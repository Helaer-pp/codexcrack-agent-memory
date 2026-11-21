"""Native-reference view for the dual-channel run and its independent grayscale control."""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from research.notch_identity_v34.reference_views import window,pane,font,native_point,NAMES,MODE as PRIOR_MODES
from research.v3_labelme_comparison.compare import PACKAGE,write_csv
from research.v3_labelme_comparison.infer import read_csv,current
from .batch import ROOT,OUT,OLD,GROUPS,SELECT,read,sha
MODE={**PRIOR_MODES,'LOCAL':'前向材料窗细配准','CONTOUR':'缺口轮廓保底 · 近似位置'}
W,H=480,238

def render(rec,meta,raw,fixed,aligned,label,score,*,include_windows=False,output_mode='full'):
    m=rec['models']['S4'][output_mode];d=m['diagnostics'];i=d.get('selected');valid=m['tip'] is not None
    tip=np.rint(m['tip'] or m['root'] or meta['evidence']['scene']['center']).astype(int)
    tr=d['candidates'][i]['trace'] if i is not None else {};dual=d.get('dual',{});local=dual.get('registration') or tr.get('reference') or {};coarse=d.get('coarse') or {}
    start=rec['box'][:2];info=meta['input']
    group=rec['group'];f=rec['frame'];same=info['image_sha']==info['ref_sha']
    full=rec['models']['S4']['full']['diagnostics']['dual']
    local=full.get('registration') or {}
    shift=[0,0] if same else local.get('shift') or [0,0]
    q=tip+shift
    xx,yy=np.rint(q-start).astype(int)
    pt=tip.copy() if same else native_point(q,meta,(int(info['height']),int(info['width'])),fixed.shape)
    warp=full.get('sensor_warp')
    if warp and not same:
        a=np.clip((yy-warp['center_y']+warp['half'])/(2*warp['half']),0,1)
        moves=np.asarray(warp['offsets'])
        pt=q-((1-a)*moves[0]+a*moves[1])
    mode='SAME' if same else 'LOCAL' if local.get('status')=='OK' else 'ANCHORS' if not local.get('shift') else 'COARSE'
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
    text(20,16,f"{NAMES[group]}    第 {f} / {GROUPS[group]} 帧",30)
    status='未标注' if not score else '标注不确定' if gt is None else '无有效预测' if not valid else '尖端误差 '+f"{float(score['error_px']):.2f} px"
    text(990,21,'V5.11 '+('完整模式' if output_mode=='full' else '纯灰度')+'   ·   '+status)
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
    text(20,630,f"{'当前尖端' if valid else '无预测尖端，定位窗口中心'} ({tip[0]:.2f}, {tip[1]:.2f})   →   参考原图 {target}    |    {MODE[mode]}",24,
         '#956018' if mode in ('COARSE','CONTOUR','ANCHORS','OUTSIDE') else '#006a58')
    ncc=local.get('ncc');ncc='—' if ncc is None else f'{ncc:.3f}'
    text(20,678,f"固定参考   {Path(info['reference']).name}     ·     前向配准 {local.get('status','—')}    NCC {ncc}     ·     裁决 {dual.get('decision','纯灰度')}",18)
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
