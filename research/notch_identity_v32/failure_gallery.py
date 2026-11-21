"""Offline failure cards for the sealed V3.2 evaluation, in original pixel coordinates."""
from collections import Counter
import html
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .batch import OUT, ROOT, SELECT, GROUPS, read, sha
from research.v3_labelme_comparison.compare import PACKAGE, crop, panel, evaluate
from research.v3_labelme_comparison.infer import read_csv, current

DEST = ROOT / 'output/diagnostics/v32_failed_frames_20261119'
NAMES = {'three_point_bend':'三点弯', 'group_c':'验证组C', 'group_a':'开发组A'}
FONT = 'C:/Windows/Fonts/msyh.ttc'
FONTS = {size:ImageFont.truetype(FONT,size) for size in (18,20,22,25,34)}
MANUAL=(255,190,0)
PRED=(70,205,50)
TIP=(50,45,245)

# These statements refer to the actual selected and rejected branches of this frozen run.
NOTES = {
    'group_a': {
        366:'原版误差 1.15 px。单改背景和单改渐弱终止门都使误差超过 10 px。最终远端亮隙规则在 x=1302 截断，尖端停在 x=1301；主干仍贴合。',
        504:'单改背景仍命中；单改尾端规则使误差升到 19.02 px。最终候选在 x=1367 触发弱隙折转检查，公开尖端停在前一列。参考图锚区纹理不足。'},
    'three_point_bend': {
        1:'从 V3.1 到最终版均从上侧起追，尖端保持在 (1554,2709)。按 10 px 距离匹配，整条预测与人工路径的覆盖和精度均为零。偏差已出现在路径选择阶段。',
        144:'换支后尖端误差由 59.29 降至 9.92 px，但人工路径覆盖降至 27.4%。终点进入容差掩盖了近缺口段的大面积错位。',
        178:'尾端规则先将预测收至 x=1562，已比人工点靠右 22.59 px。最后换支又降低了路径覆盖；该次换支没有改变尖端。',
        215:'换支前后尖端完全相同，误差仅 2.08 px。两侧路径在后段靠拢，最终覆盖与精度却从各 100% 降至 64.9% 和 60.0%。',
        248:'远端亮隙规则先把尖端拉回 10 px 容差内。最后换支保留了这个尖端，却丢失近缺口路径。',
        271:'上下候选在尾端给出同一坐标，误差仅 5.02 px。换支丢失下唇一段，覆盖和精度均跌破 80%。',
        306:'尖端距人工点仅 2.49 px。最终改选上唇后，覆盖从 100% 降至 72.5%；误差集中在起点到汇合前的路径。',
        335:'换支前尖端已过冲，二维误差 10.55 px；换支后尖端相同，路径覆盖另降至 73.0%。两项失败发生在不同阶段。',
        347:'从另一侧出发仍收敛到相同尖端，误差 2.52 px，但覆盖和精度从各 100% 降至 74.5% 和 74.4%。',
        381:'尖端稍早停止，误差 8.18 px，仍在容差内。换支使原本合格的路径覆盖与精度分别跌至 78.2% 和 76.0%。',
        407:'换支之前尖端已提前约 19 px。换支未改变终点，却把路径覆盖从 96.8% 拉到 79.7%，略低于 80% 门槛。',
        413:'背景与尾门联合时误差 7.24 px；加入远端检查后所选尖端变到 x=1756，误差升至 13.22 px。最后换支又降低路径质量。',
        435:'终止门已消除历史过冲，尖端误差仅 1.71 px。最后换支时端点保持，近缺口错位使覆盖、精度均低于 80%。',
        503:'换支后尖端从 (1795,2723) 移到 (1797,2725)，误差从 8.58 升至 11.22 px。长主干占比高，覆盖和精度仍通过。'},
    'group_c': {
        38:'最终所选候选在 x=2273 触发谷底后回升判据，公开尖端停在 x=2272；背景和尾门联合阶段已出现相同结果。提前停止伴随人工路径覆盖不足。',
        54:'背景与尾门联合阶段已在 x=2273 的谷底处截短。最终同唇门在同一列拒绝重接，端点没有恢复；预测点均贴线，但只覆盖 47.1% 人工路径。',
        69:'V3.1 过冲。远端检查在 x=2310 判定折转，随后谷底截断提前到 x=2276；最终改选的候选在 x=2275 拒绝重接。局部配准峰不唯一，尖端转为提前。',
        195:'各主要阶段均停在 x=2400，强信号门认证了人工尖端以右的延伸；远端亮隙到 x=2401 才触发。路径覆盖 100%，失分集中在终点。',
        335:'路径在人工尖端附近转向右上暗线。亮隙检查在 x=2505 才触发，晚于已认证端点 x=2494；强门接受该尾段，未触发局部参考复核。该暗线的物理身份待确认。',
        363:'末端相对人工点向上偏 17.85 px，纵向误差大于横向；强门仍放行该段，远端亮隙到 x=2497 才触发。固定参考局部纹理不足，未能裁剪。',
        456:'远端检查把尖端从 x=2506 收到 x=2504，仍向右偏 10.09 px；路径覆盖、精度均 100%。参考配准峰不唯一，最终以约 0.10 px 超出二维容差。',
        510:'收紧尾门后尖端仍由强门认证到 x=2507，比人工点靠右 16.94 px；亮隙规则到下一列才截断。主干覆盖 100%，所选尾段未触发参考复核。'}}
STAGES=(('v3_1','V3.1'),('paired','背景＋尾门'),('distal','加远端检查'),('reference','加参考复核'),('v3_2','V3.2 最终'))


def draw_text(draw,xy,text,size=20,color='#202f39'):
    draw.text(xy,text,font=FONTS[size],fill=color,anchor='lt')


def wrapped(draw,text,width,size=22):
    lines=[];line=''
    for char in text:
        if line and draw.textlength(line+char,font=FONTS[size])>width:
            lines.append(line);line=''
        line+=char
    return lines+[line]


def render(raw,paths,gt,result,row,history,reason,branch,category):
    pts=np.asarray(result['points']);tip=np.asarray(result['tip'])
    manual=[(p,MANUAL,False,False) for p in paths]
    observed=[(pts,PRED,False,True)]
    gm=[(gt,MANUAL,True)];pm=[(tip,TIP,False)]
    allbox=crop(raw,[*paths,pts,gt[None,:]],15)
    base=np.vstack([p[np.argmin(p[:,0])] for p in paths])
    rootbox=crop(raw,[base,np.array(result['root']).reshape(1,2)],29)
    tipbox=crop(raw,[gt[None,:],tip[None,:]],28)
    im=Image.new('RGB',(1560,910),'#f3f5f4');draw=ImageDraw.Draw(im)
    draw_text(draw,(28,22),f"{NAMES[row['group']]}  ·  第 {row['frame']} 帧",34)
    draw_text(draw,(810,28),category+'    /    V3.2 完整模式',25,'#a53522')
    error=float(row['error_px']);cx=float(row['coverage']);pr=float(row['precision'])
    draw_text(draw,(30,82),f"尖端误差 {error:.2f} px       横向 Δx {float(row['dx']):+.2f} px       纵向 Δy {float(row['dy']):+.2f} px       覆盖率 {cx:.1%}       路径精度 {pr:.1%}",22)
    def brick(x,y,label,box,lines,marks):
        draw_text(draw,(x,y),label,22)
        w,h=490,190
        tile=np.full((h,w,3),40,np.uint8)
        x0,y0,x1,y1=box
        z=min(w/(x1-x0),h/(y1-y0))
        offset=((w-round((x1-x0)*z))//2,(h-round((y1-y0)*z))//2)
        panel(tile,raw,box,offset,(w,h),lines,marks)
        im.paste(Image.fromarray(cv2.cvtColor(tile,cv2.COLOR_BGR2RGB)),(x,y+33))
    brick(30,139,'原始灰度',allbox,[],[])
    brick(535,139,'人工路径与尖端',allbox,manual,gm)
    brick(1040,139,'算法路径与尖端',allbox,observed,pm)
    brick(30,388,'缺口放大  ·  双路径叠加',rootbox,manual+observed,gm+pm)
    brick(535,388,'尖端放大  ·  双路径叠加',tipbox,manual+observed,gm+pm)
    draw_text(draw,(1040,388),'分阶段对照',22)
    draw_text(draw,(1040,426),'阶段',18);draw_text(draw,(1224,426),'误差 px',18);draw_text(draw,(1334,426),'覆盖率',18);draw_text(draw,(1440,426),'精度',18)
    for j,(s,label) in enumerate(STAGES):
        r=history[s];y=455+29*j
        for x,t in zip((1040,1224,1334,1440),(label,f"{float(r['error_px']):.2f}",f"{float(r['coverage']):.1%}",f"{float(r['precision']):.1%}")):
            draw_text(draw,(x,y),t,18)
    draw_text(draw,(30,638),'蓝色线与十字为人工标注，绿线和红圈为算法结果。上排三图裁剪与比例相同。下排分别放大缺口和尖端。',20)
    y=700
    for line in wrapped(draw,reason,1490):
        draw_text(draw,(30,y),line,22);y+=33
    if branch:
        for line in wrapped(draw,branch,1490,20):
            draw_text(draw,(30,y+8),line,20,'#344e68');y+=30
    assert y<875
    return im


def main():
    counts=Counter(); rows=[]; digest_list=[]
    roster={(r['dataset_id'],int(r['frame_id'])):r for r in read_csv(SELECT) if r['dataset_id'] in GROUPS}
    for g in GROUPS:
        source=OUT/(g+'.jsonl')
        assert sha(source)==read(OUT/(g+'_seal.json'))['predictions']
        scores={(int(r['frame']),r['stage']):r for r in read_csv(OUT/(g+'_scores.csv')) if r['mode']=='full'}
        needed={i for (i,s),r in scores.items() if s=='v3_2' and r['state']=='VISIBLE' and r['joint']=='False'}
        assert needed==set(NOTES[g])
        folder=DEST/g;folder.mkdir(parents=True,exist_ok=True)
        for line in source.open():
            rec=json.loads(line);i=rec['frame']
            if i not in needed:continue
            m=rec['models']['v3_2'];result=m['full']
            assert all(result[k]==m['raw_only'][k] for k in ('tip','root','points'))
            item=roster[g,i];assert rec['source_sha']==item['sha256']
            raw=current(item['source_image'],rec['source_sha'])
            lab=read(PACKAGE/item['selected_json'])
            assert raw.shape==(lab['imageHeight'],lab['imageWidth'])
            paths=[np.asarray(s['points']) for s in lab['shapes'] if s['label']=='crack_path']
            gt,=[np.asarray(s['points'][0]) for s in lab['shapes'] if s['label']=='crack_tip']
            row=scores[i,'v3_2'];scores_now=evaluate(result,paths,gt)
            assert not scores_now['joint'] and all(np.isclose(scores_now[k],float(row[k])) for k in ('dx','dy','coverage','precision','error_px'))
            path_ok=min(scores_now['coverage'],scores_now['precision'])>=.8
            category='仅路径不合格' if scores_now['hit10'] else '仅尖端超差' if path_ok else '尖端和路径均未通过'
            counts[category]+=1
            reason=NOTES[g][i];branch=''
            before=rec['models']['reference']['full']
            if g=='three_point_bend' and before['root']!=result['root']:
                candidate,=[c for c in result['diagnostics']['candidates'] if c['start']==before['root']]
                tr=candidate['trace']
                event,=[e for e in tr['events'] if not e[-1]]
                branch=(f'原下唇候选在 x={event[0]} 拒绝重接，切向外推残差 {event[3]:.2f} px，谷宽比 {event[4]:.2f}。'
                        f'起点由 {tuple(before["root"])} 切换至上唇 {tuple(result["root"])}。')
            hist={s:scores[i,s] for s,_ in STAGES}
            im=render(raw,paths,gt,result,row,hist,reason,branch,category)
            rel=f'{g}/{i:04d}.png';im.save(DEST/rel)
            with Image.open(DEST/rel) as check:check.load();assert check.size==im.size
            digest_list.append(sha(DEST/rel))
            rows.append(dict(group=g,frame=i,error=float(row['error_px']),category=category,path=rel,reason=reason,branch=branch))
    assert len(rows)==len(set(digest_list))==24
    title='V3.2 失败帧专项复核'
    intro='54 张人工尖端可见帧中，24 帧未达到联合标准。尖端容差为 10 原图像素，人工路径覆盖率和预测路径精度均须达到 80%。6 张不确定标注及 1,573 张未标注帧未纳入失败统计。同一失败帧两种模式输出一致，每帧绘制一张。'
    nav='　'.join(f'<a href="#{g}">{NAMES[g]}（{sum(r["group"]==g for r in rows)}）</a>' for g in GROUPS)
    content=[f'<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>body{{font:17px/1.6 system-ui,sans-serif;color:#233546;max-width:1200px;margin:2em auto;padding:0 16px}}img{{max-width:100%;height:auto;display:block}}a{{color:#075a73}}article{{margin-bottom:3em}}h3{{margin-bottom:.5em}}@media print{{article{{break-inside:avoid}}}}</style><h1>{title}</h1><p>{intro}</p><nav>{nav}</nav>']
    report=[f'# {title}',intro,'单项尖端超差、单项路径不合格、两项均失败各 8 帧。三点弯 14 个失败中，13 个在最终同唇规则启用后由下唇切至上唇；其中 8 个在上一阶段联合命中。验证组C 69 截短过多，335 和 363 的末端向上偏，开发组A的两个失败保留了超过 98% 的人工路径。表中结论来自同帧封存对照；暗线的开裂或划痕物理身份未经独立测量。']
    for g in GROUPS:
        sub=[r for r in rows if r['group']==g]
        content.append(f'<h2 id="{g}">{NAMES[g]} · {len(sub)} 帧</h2>')
        report.extend([f'## {NAMES[g]} · {len(sub)} 帧','| 帧 | 未通过项 | 尖端误差 px | 逐帧原因 |\n|---:|---|---:|---|'])
        entries=[]
        for r in sub:
            note=html.escape(r['reason']+r['branch'])
            label=f"{NAMES[g]}第 {r['frame']} 帧"
            content.append(f'<article><h3>{label}　{r["category"]}　{r["error"]:.2f} px</h3><a href="{r["path"]}"><img loading="lazy" width="1560" height="910" alt="{label}人工和预测路径对照" src="{r["path"]}"></a><p>{note}</p></article>')
            entries.append(f'| [{r["frame"]}]({r["path"]}) | {r["category"]} | {r["error"]:.2f} | {r["reason"]}{r["branch"]} |')
        report[-1]+='\n'+'\n'.join(entries)
    assert sorted(counts.values())==[8,8,8]
    (DEST/'index.html').write_text('\n'.join(content)+'</html>',encoding='utf-8')
    (DEST/'REPORT.md').write_text('\n\n'.join(report)+'\n',encoding='utf-8')
    with ZipFile(DEST/'v32_failure_review.zip','w',ZIP_DEFLATED) as z:
        for rel in ['index.html','REPORT.md',*[r['path'] for r in rows]]:z.write(DEST/rel,rel)
    with ZipFile(DEST/'v32_failure_review.zip') as z:assert z.testzip() is None and len(z.namelist())==26
    print(len(rows),dict(counts))

if __name__=='__main__':
    main()

