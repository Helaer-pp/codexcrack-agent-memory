"""Compare sealed V3 outputs with live LabelMe files in original BMP coordinates."""
import csv
import html
import json
import zipfile
from collections import Counter
from pathlib import Path
import cv2
import numpy as np
from scipy.spatial import cKDTree
from .infer import ROOT, OUT, NAMES, SELECT, POLICY, current, read_csv, read_json, save, digest
from research.raw_notch_trace_v2b.evaluate import dense

PACKAGE=ROOT/'output/runs/uctt_r05_prelabel_difference_20261111_r01/R05_LabelMe_Annotation_Package'
ARCHIVE=ROOT/'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip'
MODES=('full','raw_only')

def write_csv(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def evaluate(result,paths,gt):
    pts=np.asarray(result['points'],float)
    tip=result['tip']
    delta=np.asarray(tip)-gt if gt is not None and tip is not None else None
    err=float(np.linalg.norm(delta)) if delta is not None else None
    coverage=precision=None
    if gt is not None:
        line=np.vstack([dense(p) for p in paths])
        coverage=float((cKDTree(pts).query(line)[0]<=10).mean()) if len(pts) else 0.
        precision=float((cKDTree(line).query(pts)[0]<=10).mean()) if len(pts) else 0.
    hit=None if gt is None else err is not None and err<=10.
    joint=None if gt is None else hit and min(coverage,precision)>=.8
    return dict(status=result['status'],pred_x=tip[0] if tip else None,pred_y=tip[1] if tip else None,
                dx=float(delta[0]) if delta is not None else None,dy=float(delta[1]) if delta is not None else None,
                error_px=err,coverage=coverage,precision=precision,hit10=hit,joint=joint,
                severe=None if gt is None else err is not None and err>100)

def panel(canvas,raw,box,offset,size,pathsets,marks):
    x0,y0,x1,y1=box
    pane=raw[y0:y1,x0:x1]
    target_w,target_h=size
    scale=min(target_w/pane.shape[1],target_h/pane.shape[0])
    dw=max(1,round(pane.shape[1]*scale)); dh=max(1,round(pane.shape[0]*scale))
    img=cv2.cvtColor(cv2.resize(pane,(dw,dh),interpolation=cv2.INTER_AREA if scale<1 else cv2.INTER_LINEAR),cv2.COLOR_GRAY2BGR)
    def xy(arr):
        return np.rint((np.asarray(arr)-[x0,y0]+.5)*[dw/pane.shape[1],dh/pane.shape[0]]-.5).astype(np.int32).reshape(-1,2)
    for path,color,closed,observed in pathsets:
        if len(path):
            parts=np.split(path,np.flatnonzero(np.diff(np.asarray(path)[:,0])!=1)+1) if observed else [path]
            for part in parts:
                line=xy(part)
                if len(line)>1:cv2.polylines(img,[line],closed,color,1,cv2.LINE_AA)
                else:cv2.circle(img,tuple(line[0]),1,color,-1)
    for pt,color,cross in marks:
        if pt is None:continue
        p=tuple(xy(pt)[0])
        if cross:cv2.drawMarker(img,p,color,cv2.MARKER_CROSS,15,2)
        else:cv2.circle(img,p,7,color,2,cv2.LINE_AA)
    x,y=offset
    canvas[y:y+dh,x:x+dw]=img

def crop(raw,cloud,margin):
    pts=np.vstack(cloud); h,w=raw.shape
    lo=np.maximum(0,np.floor(pts.min(0)-margin).astype(int))
    hi=np.minimum([w,h],np.ceil(pts.max(0)+margin+1).astype(int))
    return (*lo,*hi)

def draw(raw,rec,paths,gt,uncertain,row):
    manual=(255,204,25); pred=(65,225,90); tip_color=(50,65,255)
    official=rec['full']
    lines=[(p,manual,False,False) for p in paths]+[(p,(20,184,255),True,False) for p in uncertain]
    predicted=[(official['points'],pred,False,True)]
    marks_gt=[(gt,manual,True)]
    marks_pred=[(official['tip'],tip_color,False)]
    bounds=[np.asarray(rec['hint']).reshape(1,2)]+paths+uncertain
    if official['points']:bounds.append(np.asarray(official['points']))
    if gt is not None:bounds.append(np.asarray(gt).reshape(1,2))
    extent=crop(raw,bounds,35)
    focus=gt if gt is not None else np.mean(np.vstack(uncertain),axis=0)
    detail=crop(raw,[np.asarray(focus).reshape(1,2)],55)
    canvas=np.full((580,1440,3),25,np.uint8)
    def title(text,xy,font=.55):
        cv2.putText(canvas,text,xy,cv2.FONT_HERSHEY_SIMPLEX,font,(235,235,235),1,cv2.LINE_AA)
    title(f"{rec['group']}    frame {rec['frame']}     {row['state']}     {row['status']}",(12,25),.65)
    e='N/A' if row['error_px'] is None else f"{row['error_px']:.2f} px"
    title(f"tip error {e}    |    top: full trace region    |    bottom: manual tip / uncertain region detail",(12,52))
    for j,(name,draws,marks) in enumerate([('Raw',[],[]),('Manual: cyan + / uncertain polygon',lines,marks_gt),('V3: green path, red tip / manual: cyan',lines+predicted,marks_gt+marks_pred)]):
        x=480*j+8;title(name,(x,84))
        panel(canvas,raw,extent,(x,98),(464,222),draws,marks)
        panel(canvas,raw,detail,(x,349),(464,220),draws,marks)
    return canvas

def summary(rs):
    vis=[r for r in rs if r['state']=='VISIBLE']
    valid=[r for r in vis if r['error_px'] is not None]
    return dict(total=len(rs),visible=len(vis),uncertain=len(rs)-len(vis),valid=len(valid),hit10=sum(r['hit10'] for r in vis),
                joint=sum(r['joint'] for r in vis),severe=sum(r['severe'] for r in vis),
                median_error_px=float(np.median([r['error_px'] for r in valid])) if valid else None,
                max_error_px=max((r['error_px'] for r in valid),default=None),
                uncertain_valid=sum(r['pred_x'] is not None for r in rs if r['state']=='UNCERTAIN'))

def table(headers,values):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers)]+['| '+' | '.join(str(v) for v in r)+' |' for r in values])

def compare(out=OUT):
    path=out/'predictions.jsonl'
    seal=read_json(out/'seal.json');assert digest(path)==seal['predictions_sha']
    groups=read_json(POLICY)['groups']
    selected={(r['dataset_id'],int(r['frame_id'])):r for r in read_csv(SELECT) if groups[r['dataset_id']]!='EXCLUDED'}
    records=list(map(json.loads,path.read_text().splitlines()))
    assert set(selected)=={(r['group'],r['frame']) for r in records}
    details=[];rollup=[];cards=[];same=0
    target=out/'images';target.mkdir(exist_ok=True)
    with zipfile.ZipFile(ARCHIVE) as archive:
        for rec in records:
            g=rec['group'];f=rec['frame'];item=selected[g,f];member=item['selected_json']
            labfile=PACKAGE/member;label=read_json(labfile)
            same+=int(labfile.read_bytes()==archive.read(member))
            assert rec['source_sha']==item['sha256'] and Path(label['imagePath']).name==Path(item['selected_image']).name
            raw=current(item['source_image'],rec['source_sha'])
            assert raw.shape==(label['imageHeight'],label['imageWidth'])
            shapes=label['shapes']
            paths=[np.asarray(s['points'],float) for s in shapes if s['label']=='crack_path']
            tips=[s['points'][0] for s in shapes if s['label']=='crack_tip']
            uncertain=[np.asarray(s['points'],float) for s in shapes if s['label']=='uncertain_region']
            assert (len(tips)==1 and paths and not uncertain) or (not tips and not paths and uncertain)
            gt=tips[0] if tips else None
            png=f'images/{g}_{f}.png'
            for mode in MODES:
                row=dict(group=g,role=groups[g],frame=f,mode=mode,state='VISIBLE' if gt else 'UNCERTAIN',
                         gt_x=gt[0] if gt else None,gt_y=gt[1] if gt else None,
                         **evaluate(rec[mode],paths,gt),image=png,annotation_sha=digest(labfile))
                details.append(row)
                if mode=='full':
                    img=draw(raw,rec,paths,gt,uncertain,row)
                    assert cv2.imwrite(str(out/png),img) and cv2.imread(str(out/png)).shape==img.shape
                    cards.append(row)
    for mode in MODES:
        subset=[r for r in details if r['mode']==mode]
        for scope in [*NAMES,'DEVELOPMENT','VALIDATION_ONLY','ALL']:
            rs=[r for r in subset if scope in ('ALL',r['role'],r['group'])]
            rollup.append(dict(scope=scope,mode=mode,**summary(rs)))
    write_csv(out/'per_frame.csv',details)
    write_csv(out/'group_summary.csv',rollup)
    full=[r for r in rollup if r['mode']=='full']
    totals=full[-1]
    report=['# V3 与人工裂纹标注逐帧对比',
            f"本次重新推理 {totals['total']} 张原始 BMP，{totals['visible']} 张人工标出可见尖端，{totals['uncertain']} 张圈为不确定。完整模式尖端命中 **{totals['hit10']}/{totals['visible']}**，路径与尖端联合命中 **{totals['joint']}/{totals['visible']}**。可见帧中有 {totals['valid']} 张输出尖端，{totals['severe']} 张尖端误差超过 100 px。",
            '[逐帧对比图册](index.html) · [逐帧坐标与两种模式评分](per_frame.csv) · [分组汇总](group_summary.csv) · [完整原图路径与候选诊断](predictions.jsonl)',
            table(['组别','可见','给出尖端','Hit@10','Joint','误差 >100','有效预测中位误差 px','不确定帧输出 / 张数'],[
                [NAMES.get(r['scope'],{'ALL':'合计','DEVELOPMENT':'开发组小计','VALIDATION_ONLY':'保留验证组小计'}.get(r['scope'])),r['visible'],r['valid'],r['hit10'],r['joint'],r['severe'],
                 '—' if r['median_error_px'] is None else f"{r['median_error_px']:.2f}",f"{r['uncertain_valid']}/{r['uncertain']}"] for r in full]),
            'Hit@10 为正式尖端与人工尖端的二维欧氏距离 ≤10 个原图像素。Joint 还要求在 10 px 内，人工路径被预测覆盖和预测点贴合人工路径的比例均 ≥80%。空预测计入可见分母且未命中，误差中位数只统计有输出的可见帧。不确定区域只展示，不作为正确、错误或无裂纹真值。']
    for g in NAMES:
        cnt=Counter(r['full']['status'] for r in records if r['group']==g)
        group_rows=[r for r in cards if r['group']==g]
        bad=sorted((r for r in group_rows if r['error_px'] is not None),key=lambda x:-x['error_px'])
        example=f"；误差最大的是[第 {bad[0]['frame']} 帧]({bad[0]['image']})，{bad[0]['error_px']:.2f} px" if bad else ''
        report.append(f"{NAMES[g]} 的 20 张标注图输出状态为 "+'、'.join(f'{k} {v} 张' for k,v in cnt.items())+example+'。')
    report.extend(['## 复算与数据来源',
        f"V3 s3t 检测源码与冻结记录一致。按清单核对原始 BMP、固定参考及实际前一帧的 SHA256，从当前 P1/P2 重建 ROI 和辅助差分，预测封存后读取当前 LabelMe 标注。当前包与验收快照逐字节相同 {same}/120。与上次三组重叠 {seal['overlap_frames']} 帧，两种模式的状态、起点、完整路径和尖端共有 {len(seal['overlap_differences'])} 项差异。",
        '使用长期分组，排除组X排除，验证组C和三点弯为已曝光的保留验证组。CT3 按输入清单使用既有坐标 CSV；其余组使用原始锚点 TXT 映射。这次仅执行固定版本，无训练或阈值调整。',
        '开发组H 20 张 ROI 超过旧 60Q 图搜索的 350 万像素预算。本次直接调用 V3 所需的原尺度几何与配准函数，跳过旧图搜索预计算。预测状态 NO_NOTCH_BODY 表示 V3 未定位到可用缺口本体；NO_ELIGIBLE_ROOT_TRACE 表示已有起点但没有通过认证的轨迹。'])
    (out/'REPORT.md').write_text('\n\n'.join(report)+'\n',encoding='utf-8')
    options=''.join(f'<option value="{g}">{name}</option>' for g,name in NAMES.items())
    page="""<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V3 人工标注对比</title><style>body{background:#17191c;color:#eee;font:16px system-ui;margin:2vw}a{color:#94d9ff}button,select{font:inherit;margin:.3em}img{width:min(100%,1440px);display:block}p{line-height:1.5}</style><h1>V3 与人工标注逐帧对比</h1><p>左为原图，中为人工标注，右为算法与人工叠图。青色十字为人工尖端，绿线和红圈为算法路径与尖端，黄色框线为人工不确定区。下排放大人工尖端或不确定区。</p><label>实验组 <select id="g">OPTIONS</select></label><label>显示 <select id="filter"><option value="all">全部标注帧</option><option value="miss">未联合命中</option><option value="joint">联合命中</option><option value="unc">人工不确定</option></select></label><button id="prev">上一张</button><select aria-label="选择原序列帧号" id="pick"></select><button id="next">下一张</button><p id="score"></p><img id="pic" alt="原图、人工路径和算法识别叠图"><p><a id="link">原尺寸对比图</a> · <a href="per_frame.csv">逐帧数据</a> · <a href="REPORT.md">报告</a></p><script>const data=DATA;const el=x=>document.getElementById(x);let list=[];function show(){let i=el('pick').selectedIndex,r=list[i];el('prev').disabled=i<=0;el('next').disabled=i<0||i>=list.length-1;el('pic').hidden=!r;el('link').hidden=!r;if(!r){el('pic').removeAttribute('src');el('score').textContent='此筛选下没有样本';return}el('pic').src=el('link').href=r.image;let p=v=>v==null?'—':v.toFixed(2);el('score').textContent='帧 '+r.frame+'　'+(r.state==='UNCERTAIN'?'人工不确定':r.joint?'联合命中':r.hit10?'端点命中，路径未达标':'端点未命中')+'　检测状态 '+r.status+'　端点误差 '+p(r.error_px)+' px　路径覆盖 '+p(r.coverage)+'　路径精度 '+p(r.precision)}function fill(){let v=el('filter').value;list=data.filter(r=>r.group===el('g').value&&(v==='all'||v==='unc'&&r.state==='UNCERTAIN'||v==='miss'&&r.joint===false||v==='joint'&&r.joint===true));el('pick').replaceChildren(...list.map(r=>new Option('第 '+r.frame+' 帧')));show()}el('g').onchange=el('filter').onchange=fill;el('pick').onchange=show;el('prev').onclick=()=>{el('pick').selectedIndex--;show()};el('next').onclick=()=>{el('pick').selectedIndex++;show()};fill()</script></html>"""
    (out/'index.html').write_text(page.replace('OPTIONS',options).replace('DATA',json.dumps(cards)),encoding='utf-8')
    save(out/'comparison_check.json',dict(png_count=len(cards),visible=totals['visible'],uncertain=totals['uncertain'],live_matches_snapshot=same,
                                         prediction_sha=digest(path),per_frame_sha=digest(out/'per_frame.csv')))
    assert len(cards)==120 and len(details)==240 and len(list(target.glob('*.png')))==120
    print(json.dumps(full,ensure_ascii=False))

if __name__=='__main__':
    compare()

