"""Render native fixed-frame correspondence from sealed V3.3 observations."""
import json
import subprocess
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .batch import ROOT, OUT, OLD, GROUPS, SELECT, read, sha
from research.notch_identity_v31.report import NAMES
from research.unified_crack_tip_60q.features import ordered_points
from research.v3_labelme_comparison.compare import PACKAGE,write_csv
from research.v3_labelme_comparison.infer import read_csv,current

DEST=ROOT/'output/diagnostics/v33_fixed_reference_views_r01'
W,H=480,238
FONT='C:/Windows/Fonts/msyh.ttc'
MODE={'LOCAL':'尾段局部配准通过','COARSE':'仅缺口粗定位 · 近似位置','ANCHORS':'仅上游几何映射 · 近似位置','SAME':'同一张原图','OUTSIDE':'映射超出有效参考范围'}

@lru_cache()
def font(size):return ImageFont.truetype(FONT,size)

def native_point(q,meta,shape,refshape):
    """Evaluate the exact upstream current-grid -> native fixed-grid remap at q."""
    cp=ordered_points(meta['current_points'],shape);rp=ordered_points(meta['fixed_points'],refshape)
    if cp is None or rp is None:return None
    x,y=np.asarray(q,dtype=np.float32)
    a=np.clip((y-cp[0,1])/max(1.,cp[1,1]-cp[0,1]),0.,1.)
    point=np.array([x,y])-((1-a)*(cp-rp)[0]+a*(cp-rp)[1])
    for win in meta['evidence']['reference_info']['fixed']['windows']:
        if win['trusted'] and win['x0']<=x<win['x1']:
            top,bottom=win['sides']
            t=np.clip((y-top['bounds'][1])/max(1,bottom['bounds'][1]-top['bounds'][1]),0,1)
            point+=(1-t)*np.array(top['shift'])+t*np.array(bottom['shift'])
            break
    return point

def window(bounds,points,minimum):
    pts=np.vstack(points)
    lo,hi=pts.min(axis=0),pts.max(axis=0)
    width=int(np.ceil(max(minimum,hi[0]-lo[0]+36,(hi[1]-lo[1]+36)*W/H)))
    height=int(round(width*H/W))
    center=(lo+hi)/2
    return [int(round(center[0]-width/2)),int(round(center[1]-height/2)),width,height]

def pane(im,box,origin,lines=(),marks=()):
    x,y,w,h=box
    lx=x-origin[0];ly=y-origin[1]
    canvas=np.full((h,w),38,np.uint8)
    l=max(0,lx);r=min(im.shape[1],lx+w);t=max(0,ly);b=min(im.shape[0],ly+h)
    if l<r and t<b:canvas[t-ly:b-ly,l-lx:r-lx]=im[t:b,l:r]
    img=cv2.cvtColor(cv2.resize(canvas,(W,H),interpolation=cv2.INTER_LINEAR if w<W else cv2.INTER_AREA),cv2.COLOR_GRAY2BGR)
    def coords(pts):
        return np.rint((np.asarray(pts)-[x,y]+.5)*[W/w,H/h]-.5).astype(np.int32)
    for path,color,observed,closed in lines:
        parts=np.split(path,np.flatnonzero(np.diff(path[:,0])!=1)+1) if observed else [path]
        for part in parts:
            if len(part)>1:cv2.polylines(img,[coords(part)],closed,color,1,cv2.LINE_AA)
            elif len(part):cv2.circle(img,tuple(coords(part)[0]),1,color,-1)
    for p,color,symbol in marks:
        center=tuple(coords(p))
        if symbol=='cross':cv2.drawMarker(img,center,color,cv2.MARKER_CROSS,15,2,cv2.LINE_AA)
        elif symbol=='ring':cv2.circle(img,center,7,color,2,cv2.LINE_AA)
        else: # Corner brackets leave original background visible inside the target.
            x0,y0=center
            for sx in (-1,1):
                for sy in (-1,1):
                    corner=(x0+sx*9,y0+sy*9)
                    cv2.line(img,corner,(x0+sx*4,y0+sy*9),color,2,cv2.LINE_AA)
                    cv2.line(img,corner,(x0+sx*9,y0+sy*4),color,2,cv2.LINE_AA)
    return Image.fromarray(cv2.cvtColor(img,cv2.COLOR_BGR2RGB))

def render(rec,meta,raw,fixed,aligned,label,score):
    m=rec['models']['v3_3']['full'];d=m['diagnostics'];i=d['selected'];tip=np.array(m['tip'])
    tr=d['candidates'][i]['trace'];local=tr.get('reference',{});coarse=d.get('coarse') or {}
    start=meta['evidence']['scene']['bounds'][:2];info=meta['input']
    group=rec['group'];f=rec['frame'];same=info['image_sha']==info['ref_sha']
    near=local.get('before_tip') is None or np.linalg.norm(tip-local['before_tip'])<=meta['evidence']['scene']['scale']*.05
    if same:mode='SAME';shift=[0,0]
    elif local.get('status')=='OK' and near:mode='LOCAL';shift=local['shift']
    elif coarse.get('status')=='OK':mode='COARSE';shift=coarse['shift']
    else:mode='ANCHORS';shift=[0,0]
    q=tip+shift
    pt=tip.copy() if same else native_point(q,meta,(int(info['height']),int(info['width'])),fixed.shape)
    xx,yy=q-start
    ok=(pt is not None and 0<=pt[0]<fixed.shape[1]-1 and 0<=pt[1]<fixed.shape[0]-1 and 0<=xx<aligned.shape[1] and 0<=yy<aligned.shape[0] and np.isfinite(aligned[yy,xx]))
    pixel_delta=None
    if ok and not same:
        sample=cv2.remap(fixed,np.float32([[pt[0]]]),np.float32([[pt[1]]]),cv2.INTER_LINEAR)[0,0]
        pixel_delta=abs(float(sample)-float(aligned[yy,xx]))
        # Equivalent remaps can round either way at a 1/32-pixel interpolation boundary.
        assert pixel_delta<=8,(group,f,pt,pixel_delta)
    if not ok:mode='OUTSIDE';pt=None
    dxdy=np.rint(pt-tip).astype(int) if ok else (0,0)
    pts=np.asarray(m['points']);gt=None;manual=[];ann=[]
    if label:
        for s in label['shapes']:
            p=np.asarray(s['points'])
            if s['label']=='crack_tip':gt=p[0]
            elif s['label']=='crack_path':manual.append((p,(255,210,20),False,False))
            elif s['label']=='uncertain_region':ann.append((p,(30,220,255),False,True))
    overview=window(start,[pts,[m['root']],*[p for p,*_ in manual+ann]],220)
    detail=window(start,[[tip],*([[gt]] if gt is not None else [])],126)
    curmarks=[(tip,(40,60,247),'ring')]+([(gt,(255,210,20),'cross')] if gt is not None else [])
    lines=manual+ann+[(pts,(65,222,70),True,False)]
    im=Image.new('RGB',(1504,764),'#f6f6f3');draw=ImageDraw.Draw(im)
    def text(x,y,s,size=21,color='#18323e'):draw.text((x,y),s,font=font(size),fill=color,anchor='lt')
    text(20,16,f"{NAMES[group]}    第 {f} / {GROUPS[group]} 帧",30)
    status='未标注' if not score else '标注不确定' if gt is None else '尖端误差 '+f"{float(score['error_px']):.2f} px"
    text(990,21,'V3.3 完整模式   ·   '+status)
    text(20,66,'固定参考原图  ·  方框为对应点')
    text(512,66,'当前原图  ·  灰度')
    text(1004,66,'当前原图  ·  路径与尖端')
    for row,box in enumerate((overview,detail)):
        y=(99,376)[row];refbox=[box[0]+dxdy[0],box[1]+dxdy[1],box[2],box[3]]
        if ok:im.paste(pane(fixed,refbox,(0,0),marks=[(pt,(0,180,255),'bracket')]),(20,y))
        else:text(70,y+90,'无可用对应位置')
        im.paste(pane(raw,box,start),(512,y))
        im.paste(pane(raw,box,start,lines,curmarks),(1004,y))
    text(20,347,'尖端局部放大    ·    同一行三图等倍率，参考窗口以对应点为中心平移',19)
    target='—' if pt is None else f'({pt[0]:.1f}, {pt[1]:.1f})'
    text(20,630,f"当前尖端 ({tip[0]}, {tip[1]})   →   参考原图 {target}    |    {MODE[mode]}",24,
         '#956018' if mode in ('COARSE','ANCHORS','OUTSIDE') else '#006a58')
    ncc=local.get('ncc');ncc='—' if ncc is None else f'{ncc:.3f}'
    text(20,678,f"固定参考   {Path(info['reference']).name}     ·     尾段配准 {local.get('status','—')}    NCC {ncc}     ·     当前灰度与参考灰度使用同一显示范围",18)
    text(20,719,'绿线／红圈：算法路径／尖端      蓝线／十字：人工路径／尖端      黄色轮廓：人工不确定区      参考图方框仅标出查找位置',18)
    return im,dict(group=group,frame=f,reference=Path(info['reference']).name,reference_sha=info['ref_sha'],tip=m['tip'],
        ref_xy=None if pt is None else pt.tolist(),status=mode,shift=shift,coarse=coarse.get('status'),local=local.get('status'),
        ncc=local.get('ncc'),interpolation_check=pixel_delta,state=score['state'] if score else 'UNLABELED',
        failure=bool(score and score['hit10']=='False'),error=score['error_px'] if score else '')

def group_views(group):
    cv2.setNumThreads(1)
    pred=OUT/(group+'.jsonl')
    assert sha(pred)==read(OUT/(group+'_seal.json'))['predictions']
    scores={int(r['frame']):r for r in read_csv(OUT/(group+'_scores.csv')) if r['stage']=='v3_3' and r['mode']=='full'}
    roster={int(r['frame_id']):r for r in read_csv(SELECT) if r['dataset_id']==group}
    folder=DEST/'frames'/group;folder.mkdir(exist_ok=True,parents=True)
    annotated=DEST/'manual'/group;annotated.mkdir(exist_ok=True,parents=True)
    failures=DEST/'failures'/group;failures.mkdir(exist_ok=True,parents=True)
    records=[];reference_sha=None
    for idx,line in enumerate(pred.open(),1):
        rec=json.loads(line);assert rec['group']==group and rec['frame']==idx
        cached=OLD/'evidence'/group/str(idx);meta=read(cached/'metadata.json');info=meta['input']
        assert rec['source_sha']==info['image_sha'] and sha(cached/'arrays.npz')==meta['arrays_sha']
        if reference_sha!=info['ref_sha']:
            fixed=current(info['reference'],info['ref_sha']);reference_sha=info['ref_sha']
        label=None
        if idx in scores:
            assert roster[idx]['sha256']==rec['source_sha']
            label=read(PACKAGE/roster[idx]['selected_json'])
        with np.load(cached/'arrays.npz') as data:
            im,r=render(rec,meta,data['raw'],fixed,data['fixed__aligned'],label,scores.get(idx))
        im.save(folder/f'{idx:04d}.jpg',quality=93,subsampling=0)
        r['image']=f'frames/{group}/{idx:04d}.jpg'
        if label:
            im.save(annotated/f'{idx:04d}.png')
            r['image']=f'manual/{group}/{idx:04d}.png'
        if r['failure']:
            file=failures/f'{idx:04d}.png'
            file.write_bytes((DEST/r['image']).read_bytes())
            r['image']=f'failures/{group}/{idx:04d}.png'
        records.append(r)
    n=GROUPS[group];assert len(records)==n
    video=DEST/(group+'.mp4')
    subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-v','error','-y','-framerate','10','-start_number','1','-i',str(folder/'%04d.jpg'),'-frames:v',str(n),'-c:v','libx264','-threads','3','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
    cap=cv2.VideoCapture(str(video));count=0
    while True:
        ok,frame=cap.read()
        if not ok:break
        assert frame.shape[:2]==(764,1504);count+=1
    cap.release();assert count==n
    return records

def main():
    with ProcessPoolExecutor(3) as pool:
        groups=list(pool.map(group_views,GROUPS))
    rows=sum(groups,[]);assert len(rows)==1633
    write_csv(DEST/'correspondence.csv',rows)
    failures=[r for r in rows if r['failure']]
    assert len(failures)==16 and sum(r['state']!='UNLABELED' for r in rows)==60
    with ZipFile(DEST/'failure_comparisons.zip','w',ZIP_DEFLATED) as z:
        for r in failures:z.write(DEST/r['image'],r['image'])
    with ZipFile(DEST/'failure_comparisons.zip') as z:assert z.testzip() is None
    page="""<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V3.3 固定参考对照</title><style>body{font:17px/1.55 system-ui;color:#15333b;background:#f6f6f3;margin:2vw}a{color:#006958}select,button,input{font:inherit;margin:4px}img{display:block;width:min(100%,1504px);height:auto}p{max-width:68em}</style><h1>固定参考与当前裂纹对照</h1><p>左列显示固定参考原图。方框中心是当前预测尖端回映到参考原图的坐标。上下两行分别看整条路径和尖端邻域，当前原图在中列。可比较暗线是否已经存在、方向是否连续。</p><p>“仅缺口粗定位”和“仅上游几何映射”只给出近似位置。NCC 是尾段匹配分数；当帧上标注配准未通过时，即使分数较高也需考虑错位。“同一张原图”表示两侧来自同一图像。</p><select id="group"><option value="group_c">验证组C</option><option value="three_point_bend">三点弯</option><option value="group_a">开发组A</option></select><select id="filter"><option value="all">全部帧</option><option value="failure">仅尖端失败</option><option value="ann">全部人工标注</option></select><button id="prev">上一帧</button><select id="frame"></select><button id="next">下一帧</button>　<a id="video">整组视频</a>　<a href="failure_comparisons.zip">16 张失败图</a>　<a href="correspondence.csv">对应坐标表</a><p id="status"></p><a id="file"><img id="pic"></a><script>const data=ROWS;const $=id=>document.getElementById(id);let a=[];function show(){let i=$('frame').selectedIndex,r=a[i];$('prev').disabled=i<=0;$('next').disabled=i>=a.length-1;$('pic').src=$('file').href=r.image;$('status').textContent=r.reference+'　·　第 '+r.frame+' 帧　'+r.label+ (r.error?'　尖端误差 '+Number(r.error).toFixed(2)+' px':'');}function fill(){a=data.filter(r=>r.group===$('group').value&&($('filter').value==='all'||($('filter').value==='failure'?r.failure:r.state!=='UNLABELED')));$('frame').replaceChildren(...a.map(r=>new Option('第 '+r.frame+' 帧')));$('video').href=$('group').value+'.mp4';show()}$('prev').onclick=()=>{$('frame').selectedIndex--;show()};$('next').onclick=()=>{$('frame').selectedIndex++;show()};$('group').onchange=$('filter').onchange=fill;$('frame').onchange=show;fill()</script></html>"""
    payload=[dict(**{k:r[k] for k in ('reference','group','frame','state','failure','error','image')},label=MODE[r['status']]) for r in rows]
    (DEST/'index.html').write_text(page.replace('ROWS',json.dumps(payload,ensure_ascii=False)),encoding='utf8')
    stats={g:dict(Counter(r['status'] for r in group)) for g,group in zip(GROUPS,groups)}
    print(json.dumps(stats,ensure_ascii=False))
    print('Largest remap pixel difference',max(r['interpolation_check'] or 0 for r in rows))
if __name__=='__main__':main()

