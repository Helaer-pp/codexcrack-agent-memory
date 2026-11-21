"""Native-reference view for the dual-channel run and its independent grayscale control."""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from research.notch_identity_v34.reference_views import window,pane,font,NAMES,MODE as PRIOR_MODES
from research.v3_labelme_comparison.compare import PACKAGE,write_csv
from research.v3_labelme_comparison.infer import read_csv,current
from .domain import native_point
from .batch import ROOT,OUT,OLD,GROUPS,SELECT,read,sha
MODE={**PRIOR_MODES,'SPLIT':'有界分侧配准（含单窗或零位移回退）','LOCAL':'前向材料窗细配准','CONTOUR':'全窗零回退 · 仅粗对齐'}
NAMES={**NAMES,'group_h':'开发组H MT'}
W,H=480,238

def render(rec,meta,raw,fixed,aligned,label,score,*,include_windows=False,output_mode='full'):
    m=rec['models'][rec['stage']][output_mode];d=m['diagnostics'];i=d.get('selected');valid=m['tip'] is not None
    windows=meta['evidence']['reference_info']['fixed']['windows']
    front=m['diagnostics']['dual'].get('front')
    center=[front,windows[0]['mid']] if windows and front is not None else meta['evidence']['scene']['center']
    tip=np.rint(m['tip'] or m['root'] or center).astype(int)
    tr=d['candidates'][i]['trace'] if i is not None else {};dual=d.get('dual',{});local=dual.get('registration') or tr.get('reference') or {};coarse=d.get('coarse') or {}
    start=rec['box'][:2];info=meta['input']
    group=rec['group'];f=rec['frame'];same=info['image_sha']==info['ref_sha']
    full=rec['models'][rec['stage']]['full']['diagnostics']['dual']
    local=full.get('registration') or {}
    shift=[0,0] if same else local.get('shift') or [0,0]
    q=tip+shift
    xx,yy=np.rint(q-start).astype(int)
    pt=tip.copy() if same else native_point(q,meta,(int(info['height']),int(info['width'])),fixed.shape)
    mode='SAME' if same else 'LOCAL' if local.get('status')=='OK' else 'CONTOUR' if local.get('status')=='ZERO_FALLBACK' else 'SPLIT' if local.get('source')=='SPLIT_GRID' else 'ANCHORS' if not local.get('shift') else 'COARSE'
    ok=bool(pt is not None and 0<=xx<aligned.shape[1] and 0<=yy<len(aligned) and np.isfinite(aligned[yy,xx]))
    pixel_delta=None
    if ok and not same:
        sample=cv2.remap(fixed,np.float32([[pt[0]]]),np.float32([[pt[1]]]),cv2.INTER_LINEAR)[0,0]
        pixel_delta=abs(float(sample)-float(aligned[yy,xx]))
        assert pixel_delta<=8,(group,f,pt,pixel_delta)
    if not ok:mode='OUTSIDE';pt=None
    dxdy=np.rint(pt-tip).astype(int) if ok else (0,0)
    pts=np.asarray(m['points'] or [tip]);gt=None;manual=[];ann=[]
    if label:
        for s in label['shapes']:
            p=np.asarray(s['points'])
            if s['label']=='crack_tip':gt=p[0]
            elif s['label']=='crack_path':manual.append((p,(255,210,20),False,False))
            elif s['label']=='uncertain_region':ann.append((p,(30,220,255),False,True))
    overview=window(start,[pts,[m['root'] or tip],*[p for p,*_ in manual+ann]],220)
    detail=window(start,[[tip],*([[gt]] if gt is not None else [])],126)
    curmarks=([(tip,(40,60,247),'ring')] if valid else [])+([(gt,(255,210,20),'cross')] if gt is not None else [])
    parts=np.split(pts,np.flatnonzero(np.diff(pts[:,0])>1.7)+1)
    lines=manual+ann+[(part,(65,222,70),False,False) for part in parts] if valid else manual+ann
    im=Image.new('RGB',(1504,764),'#f6f6f3');draw=ImageDraw.Draw(im)
    def text(x,y,s,size=21,color='#18323e'):draw.text((x,y),s,font=font(size),fill=color,anchor='lt')
    title=rec["title"] if "title" in rec else NAMES[group]
    total=rec["total"] if "total" in rec else GROUPS[group]
    text(20,16,f"{title}    第 {f} / {total} 帧",30)
    status='未标注' if not score else '标注不确定' if gt is None else '无有效预测' if not valid else '尖端误差 '+f"{float(score['error_px']):.2f} px"
    if 'title' in rec and not score:status='已识别尖端' if valid else '无有效预测'
    version=rec.get("version","V6.1")
    text(990,21,f"{version} {rec['stage']} "+('完整模式' if output_mode=='full' else '纯灰度')+'   ·   '+status)
    text(20,66,'固定参考原图  ·  方框为对应点')
    text(512,66,'当前原图  ·  灰度')
    text(1004,66,'当前原图  ·  路径与尖端')
    for row,box in enumerate((overview,detail)):
        y=(99,376)[row];refbox=[box[0]+dxdy[0],box[1]+dxdy[1],box[2],box[3]]
        if ok:im.paste(pane(fixed,refbox,(0,0),marks=[(pt,(0,180,255),'bracket')]),(20,y))
        else:text(70,y+90,'无可用对应位置')
        pair=meta['current_points'] if rec['placement']=='original' else rec['geometry']['cur_points']
        marks=[(np.array(point),(0,165,250),'cross') for point in pair] if row==0 else []
        im.paste(pane(raw,box,start,marks=marks),(512,y))
        im.paste(pane(raw,box,start,lines,curmarks),(1004,y))
    text(20,347,'尖端局部放大    ·    同一行三图等倍率，参考窗口以对应点为中心平移',19)
    target='—' if pt is None else f'({pt[0]:.1f}, {pt[1]:.1f})'
    displayed=m['tip'] if valid else tip
    text(20,630,f"{'当前尖端' if valid else '无预测尖端，查看位置'} ({displayed[0]:.2f}, {displayed[1]:.2f})   →   参考原图最近像素对应 {target}    |    {MODE[mode]}",24,
         '#956018' if mode in ('COARSE','CONTOUR','ANCHORS','OUTSIDE') else '#006a58')
    win=next((w for w in windows if w['x0']<=tip[0]<w['x1']),None)
    ncc=None
    modes={'single':'单窗','side':'独立','zero':'零回退'}
    sides='对应列在分侧窗口外'
    if win:
        sides='    '.join(label+' '+modes[win[key+'_mode']]+' '+str(win[key]) for label,key in [('上','up'),('下','down')])
        ncc=win['up_ncc' if tip[1]<win['mid'] else 'down_ncc']
    text(20,678,f"固定参考   {Path(info['reference']).name}     ·     {sides}    ·    {dual.get('decision','纯灰度')}",18)
    def length(key):
        value=m[key]
        return '—' if value is None else f'{value:.2f} px'
    text(407,23,f"根点至尖端弧长 {length('path_length_px')}   ·   锚点中点投影 {length('projected_length_px')}",19)
    text(20,719,'绿线／红圈：算法路径／尖端      蓝线／十字：人工路径／尖端      原图十字：输入测量点　黄色轮廓：人工不确定区      参考图方框仅标出查找位置',18)
    row=dict(path_length_px=m['path_length_px'],projected_length_px=m['projected_length_px'],root=m['root'],group=group,frame=f,reference=Path(info['reference']).name,reference_sha=info['ref_sha'],tip=m['tip'],
        ref_xy=None if pt is None else pt.tolist(),status=mode,shift=shift,coarse=coarse.get('status'),local=local.get('status'),
        ncc=local.get('ncc'),interpolation_check=pixel_delta,state=score['state'] if score else 'UNLABELED',
        failure=bool(score and score['state']=='VISIBLE' and score['joint']!='True'),error=score['error_px'] if score else '')
    if include_windows:
        row['windows']=[overview,detail]
    return im,row
