"""Bright-zone evidence cards, native difference PNGs and full-sequence video."""
import html,json,subprocess
from zipfile import ZipFile,ZIP_STORED
import cv2
import numpy as np
from PIL import Image,ImageDraw
from research.notch_identity_v34.reference_views import font
from research.notch_identity_v34.difference_views import rgb_delta
from research.notch_identity_v58.optics import remap
from .run import OUT,OLD,ROOT,N,GROUP,base,read,read_csv,sha
from .evaluate import annotations,load_truth

W,H=468,196
BG='#f5f5f0'
GREEN='#b0ef62'
BLUE='#00a7ec'


def panel(im,origin,box,shapes):
    x,y,w,h=box
    source=Image.fromarray(im)
    tile=source.crop((x-origin[0],y-origin[1],x+w-origin[0],y+h-origin[1])).convert('RGB').resize((W,H),Image.Resampling.BILINEAR)
    d=ImageDraw.Draw(tile)
    def xy(p):return ((p[0]-x+.5)*W/w,(p[1]-y+.5)*H/h)
    for kind,ps,color in shapes:
        coords=[xy(p) for p in ps]
        if kind=='box':d.rectangle((coords[0],coords[1]),outline=color,width=2)
        elif kind=='line' and len(coords)>1:d.line(coords,fill=color,width=2)
        else:
            for a,b in coords:
                if kind=='cross':
                    d.line((a-5,b,a+5,b),fill=color,width=2);d.line((a,b-5,a,b+5),fill=color,width=2)
                elif kind=='tip':d.ellipse((a-5,b-5,a+5,b+5),outline=color,width=3)
                elif kind=='ref_tip':d.rectangle((a-5,b-5,a+5,b+5),outline=color,width=2)
                elif kind in ('P1','P2'):
                    d.ellipse((a-3,b-3,a+3,b+3),fill=color,outline='black')
                    d.text((a+5,b-9),kind,fill=color,font=font(15),stroke_width=1,stroke_fill='black')
    return tile


def aspect(x,y,width):
    width=int(np.ceil(width));height=int(np.ceil(width*H/W))
    return [int(round(x-width/2)),int(round(y-height/2)),width,height]


def card(record,gt,paths,score,out=OUT,revision="r06",mode="full"):
    i=record['frame'];geo=record['geometry'];models=record['models']['bright'];m=models[mode]
    meta=read(OLD/'evidence'/GROUP/str(i)/'metadata.json');info=meta['input'];off=meta['evidence']['scene']['bounds'][:2]
    with np.load(OLD/'evidence'/GROUP/str(i)/'arrays.npz') as z:raw=z['raw']
    fixed=base.read_fixed(info['reference'],info['ref_sha']);cfg=read(out/'freeze.json')
    l,t,r,b=geo['box'] if geo else cfg['reference_box']
    boxshape=('box',[(l,t),(r-1,b-1)],GREEN)
    refmarks=[boxshape];curmarks=[boxshape]
    if geo:
        for marks,key in [(refmarks,'ref'),(curmarks,'cur')]:
            marks.append(('cross',geo['original_'+key],'#df87ef'))
            marks.extend((n,[p],'#ffcc3f') for n,p in zip(('P1','P2'),geo[key+'_points']))
    d=models['full']['diagnostics']['dual'];mapping=d.get('material_map')
    dx,dy=d.get('local_shift',[0,0])
    same=info['image_sha']==info['ref_sha']
    refxy=None
    actual=raw[t-off[1]:b-off[1],l-off[0]:r-off[0]]
    yy,xx=np.indices(actual.shape)
    delta=np.full(actual.shape,np.nan,np.float32)
    if same:
        delta[:]=0.
        refxy=m['tip']
    elif mapping:
        aligned=remap(fixed[t:b,l:r],mapping)
        yf=yy+dy;xf=xx+dx
        shifts=np.array(mapping['offsets'])
        mx=xf+np.interp(yf,mapping['rows'],shifts[:,0]);my=yf+np.interp(yf,mapping['rows'],shifts[:,1])
        # Render the physical reference position even when the correspondence
        # falls just outside the detector's cropped reference at the band edge.
        valid=(mx+l>=0)&(mx+l<fixed.shape[1]-1)&(my+t>=0)&(my+t<fixed.shape[0]-1)
        # Remap a small native reference window to avoid copying the full sensor image.
        x0=max(0,int(np.floor(mx.min()+l)));y0=max(0,int(np.floor(my.min()+t)))
        x1=min(fixed.shape[1],int(np.ceil(mx.max()+l))+2);y1=min(fixed.shape[0],int(np.ceil(my.max()+t))+2)
        mapped=cv2.remap(fixed[y0:y1,x0:x1].astype('float32'),(mx+l-x0).astype('float32'),
                         (my+t-y0).astype('float32'),cv2.INTER_LINEAR)
        delta[valid]=mapped[valid]-actual[valid]
        if m['tip']:
            x,y=m['tip'];ix=x-l;iy=y-t
            if valid[iy,ix]:refxy=[float(mx[iy,ix]+l),float(my[iy,ix]+t)]
        # Cross-check interior pixels against the frozen detector's registered crop.
        interior=valid&(xf>=0)&(xf<r-l)&(yf>=0)&(yf<b-t)&(mx>=0)&(mx<r-l-1)&(my>=0)&(my<b-t-1)
        sy,sx=np.where(interior & (xx%17==0)&(yy%19==0))
        if len(sy):
            recovered=aligned[yf[sy,sx],xf[sy,sx]]
            assert np.max(np.abs(recovered-actual[sy,sx]-delta[sy,sx]))<=8
    if refxy:refmarks.append(('ref_tip',[refxy],'#ffad00'))
    resultmarks=[('line',p,BLUE) for p in paths]
    if gt is not None:resultmarks.append(('cross',[gt],BLUE))
    if m['points']:resultmarks.extend([('line',m['points'],'#31e76b'),('tip',[m['tip']],'#fc4540')])
    delta_rgb=rgb_delta(delta)
    overview=aspect((l+r)/2,(t+b)/2,max(r-l+56,(b-t+68)*W/H))
    focus=[p for p in (m['tip'],gt) if p is not None] or [[(l+r)/2,(t+b)/2]]
    lo=np.min(focus,axis=0);hi=np.max(focus,axis=0)
    zoom=aspect(*((hi+lo)/2),max(138,hi[0]-lo[0]+46,(hi[1]-lo[1]+38)*W/H))
    im=Image.new('RGB',(1936,660),BG);draw=ImageDraw.Draw(im)
    def text(x,y,v,size=19,fill='#173340'):draw.text((x,y),v,font=font(size),fill=fill)
    text(16,6,f'验证组C   第 {i} / {N} 帧',29)
    text(540,12,f"V5.8 {revision}   亮材料带验证  {mode}",23)
    state='无人工标注' if score is None else ('无有效尖端' if not m['tip'] else '尖端误差 %.2f px'%float(score['error_px']))
    text(1490,12,state,22)
    for j,title in enumerate(['固定参考原图与对应点','当前灰度与亮区基准点','裂纹路径与尖端','配准差分（参考减当前）']):
        text(16+j*480,55,title,20)
    for j,(crop,ypos) in enumerate([(overview,86),(zoom,343)]):
        shift=[0,0] if refxy is None or not m['tip'] else np.rint(np.array(refxy)-m['tip']).astype(int)
        refbox=[crop[0]+shift[0],crop[1]+shift[1],*crop[2:]] if j else crop
        tiles=[panel(fixed,[0,0],refbox,refmarks if not j else [a for a in refmarks if a[0]=='ref_tip']),
               panel(raw,off,crop,curmarks if not j else []),
               panel(raw,off,crop,resultmarks),
               panel(delta_rgb,[l,t],crop,[])]
        for k,pic in enumerate(tiles):im.paste(pic,(16+480*k,ypos))
    text(16,300,'尖端局部放大',21)
    text(276,300,'绿框：本帧可用范围　 黄点：亮区 P1/P2　 紫十字：原点位　 橙框：尖端在固定参考图的对应位置',18)
    text(16,554,'算法路径／尖端：绿线／红圈　　人工标注：蓝线／十字　　差分：红色变暗，蓝色变亮，统一 ±32 灰度级。',19)
    length=m['path_length_px'];projected=m['projected_length_px']
    text(16,589,'折线弧长 '+('—' if length is None else f'{length:.2f} px')+'     新点中点投影 '+('—' if projected is None else f'{projected:.2f} px')+
        f'     当前尖端 {m["tip"]}     原图有效框 [{l}, {t}, {r}, {b})',19)
    text(16,622,'参考对应 '+('不可用' if refxy is None else str(tuple(round(float(p),2) for p in refxy)))+
         '　配准 '+('同一原图' if same else 'NCC '+str(round(d['registration']['ncc'],3)) if (d.get('registration') or {}).get('ncc') is not None else '不可用'),17)
    return im,Image.fromarray(delta_rgb),dict(frame=i,roi=[l,t,r,b],reference_tip=refxy,tip=m['tip'],valid_diff_pixels=int(np.isfinite(delta).sum()))


def main(out=OUT,revision="r06"):
    from research.v3_labelme_comparison.compare import write_csv
    assert sha(out/'group_c.jsonl')==read(out/'seal.json')['predictions']
    scores={int(r['frame']):r for r in read_csv(out/'scores.csv') if r['mode']=='full' and r['stage']=='bright'}
    roster=annotations();rows=[];failures=[]
    dest=out/'visuals';frames=dest/'frames';diffs=dest/'differences'
    frames.mkdir(exist_ok=True,parents=True);diffs.mkdir(exist_ok=True)
    for line in (out/'group_c.jsonl').open():
        rec=json.loads(line);i=rec['frame'];gt,paths=load_truth(roster[i]) if i in roster else (None,[])
        pic,diff,row=card(rec,gt,paths,scores.get(i),out,revision);key=f'{i:04d}'
        pic.save(frames/(key+'.jpg'),quality=91,subsampling=0);diff.save(diffs/(key+'.png'),compress_level=3)
        row['failure']=i in scores and scores[i]['joint']=='False';row['manual']=i in scores
        if row['failure']:failures.append(i)
        rows.append(row)
    write_csv(dest/'coordinates.csv',rows)
    video=dest/'group_c.mp4'
    subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-v','error','-y','-framerate','10','-start_number','1',
        '-i',str(frames/'%04d.jpg'),'-frames:v',str(N),'-c:v','libx264','-threads','3','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
    cap=cv2.VideoCapture(str(video))
    for i in range(1,N+1):
        ok,im=cap.read();assert ok and im.shape[:2]==(660,1936)
        for p in (frames/f'{i:04d}.jpg',diffs/f'{i:04d}.png'):
            with Image.open(p) as file:file.verify()
    assert not cap.read()[0];cap.release()
    with ZipFile(dest/'failure_views.zip','w',ZIP_STORED) as z:
        for i in failures:
            for p in (frames/f'{i:04d}.jpg',diffs/f'{i:04d}.png'):z.write(p,p.relative_to(dest))
    page="""<!doctype html><html lang="zh"><meta charset="utf-8"><title>验证组C亮区验证</title><style>body{font:18px system-ui;margin:2vw}img{width:100%}select,button{font:inherit;margin:.4em}a{margin-right:1em;color:#065e62}</style><h1>验证组C · 亮材料带</h1><p><a href="group_c.mp4">完整视频</a><a href="failure_views.zip">失败帧图包</a><a href="../crack_lengths.csv">逐帧长度</a><a href="../anchor_audit.csv">基准点记录</a></p><select id="filter"><option>全部帧</option><option>标注帧</option><option>联合失败帧</option></select><button id="prev">上一帧</button><select id="sel"></select><button id="next">下一帧</button><a id="diff">独立差分 PNG</a><p id="status"></p><a id="full"><img id="pic"></a><script>const all=DATA,$=id=>document.getElementById(id);function show(){let i=$('sel').value;if(!i){$('pic').removeAttribute('src');$('status').textContent='此筛选没有帧';return}let k=i.padStart(4,'0');$('pic').src=$('full').href='frames/'+k+'.jpg';$('diff').href='differences/'+k+'.png';$('status').textContent='第 '+i+' 帧'}function fill(){let mode=$('filter').selectedIndex;let a=all.filter(r=>!mode||(mode===1?r.manual:r.failure));$('sel').replaceChildren(...a.map(r=>new Option(r.frame,r.frame)));show()}$('prev').onclick=()=>{$('sel').selectedIndex=Math.max(0,$('sel').selectedIndex-1);show()};$('next').onclick=()=>{$('sel').selectedIndex=Math.min($('sel').length-1,$('sel').selectedIndex+1);show()};$('filter').onchange=fill;$('sel').onchange=show;fill();$('sel').value='221';show()</script></html>"""
    (dest/'index.html').write_text(page.replace('DATA',json.dumps([{k:r[k] for k in ('frame','failure','manual')} for r in rows])),'utf8')
    print('Verified video and pairs:',N,'failures:',failures)


if __name__=='__main__':main()
