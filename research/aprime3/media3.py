"""Offline raster plots: exact original pixels plus measured coordinate overlays."""
from common3 import *
from media import Image,ImageDraw,FONTS,COLORS,panel
import shutil
W,H=1600,900
def render(z,label=None,diagnostic=False):
 im=read(z['input_image']);a=z['A']['formal'];p=np.asarray(a['raw_path'],float).reshape(-1,2);pp=np.asarray(z['points']);tip=a['tip']
 dec=z.get('decision_result',z.get('modes',{}).get('FULL',{}));name=z.get('group',z.get('case_id'));f=z['frame_id']
 canvas=Image.new('RGB',(W,H),COLORS['bg']);d=ImageDraw.Draw(canvas)
 d.text((18,10),f'A′3 研究对照 | {name} | 帧 {f}',font=FONTS[30],fill=COLORS['text'])
 d.text((18,52),'冻结 A 保留；回退 A 不代表物理确认。'+('受控 DEV：程序 GT 仅用于离线评价。' if label else '真实试验无人工物理 GT，准确率 N/A。'),font=FONTS[20],fill=COLORS['muted'])
 content=np.vstack([pp,p]) if len(p) else pp;pad=max(30,np.linalg.norm(pp[1]-pp[0])*.14)
 bounds=[max(0,int(content[:,0].min()-pad)),max(0,int(content[:,1].min()-pad)),min(im.shape[1],int(content[:,0].max()+pad)+1),min(im.shape[0],int(content[:,1].max()+pad)+1)]
 maps=[]
 for k,x in enumerate([15,545,1075]):
  tile,pos,fun=panel(im,(x,130,510,555),bounds);canvas.paste(tile,pos);maps.append(fun)
  d.text((x,96),['原图局部（无描线）','冻结 A 已确认输出','A′3 最终输出' if not diagnostic else 'A′3 候选诊断（非确认）'][k],font=FONTS[24],fill=COLORS['text'])
 d=ImageDraw.Draw(canvas)
 for k,valid,dt in [(1,a['confirmed_tip'],tip),(2,dec.get('valid',False),dec.get('tip'))]:
  fun=maps[k];color=COLORS['green'] if k==2 and dec.get('decision')=='RESEARCH_RELOCATED' else COLORS['yellow']
  if valid:
   path=p
   if len(p) and dt is not None:path=p[:np.argmin(np.linalg.norm(p-dt,axis=1))+1]
   if len(path)>1:d.line([fun(q) for q in path],fill=COLORS['red'],width=2)
   if dt is not None:
    x,y=fun(dt);d.ellipse((x-6,y-6,x+6,y+6),outline=color,width=2)
  for j,q in enumerate(pp):
   x,y=fun(q);d.ellipse((x-3,y-3,x+3,y+3),outline=COLORS['cyan'],width=2);d.text((x+5,y),f'P{j+1}',font=FONTS[17],fill=COLORS['cyan'])
  v0=np.asarray(fun(pp[0]));v1=np.asarray(fun(pp[1]));steps=max(1,int(np.linalg.norm(v1-v0)/9))
  for j in range(0,steps,2):d.line([tuple(v0+(v1-v0)*j/steps),tuple(v0+(v1-v0)*min(j+1,steps)/steps)],fill=COLORS['cyan'],width=1)
 if diagnostic:
  fun=maps[2]
  if len(p)>1:d.line([fun(q) for q in p],fill=COLORS['orange'],width=1)
  for c in z['pool']:
   if c['A_original_bitwise']:continue
   x,y=fun(c['xy']);d.ellipse((x-3,y-3,x+3,y+3),outline=COLORS['orange']);d.text((x+4,y-13),str(c['candidate_id']),font=FONTS[17],fill=COLORS['orange'])
  for q in z.get('queries',[]):
   if q['reg']['local_supported']:
    hull=[fun(t) for t in q['reg']['polygon']]
    if len(hull)>2:d.line(hull+[hull[0]],fill=(55,145,150),width=1)
 if label:
  gt=label.get('GT',label)
  if gt['observable']:
   for fun in maps[1:]:
    x,y=fun(gt['tip']);d.line([(x-8,y),(x+8,y)],fill=(240,100,255),width=2);d.line([(x,y-8),(x,y+8)],fill=(240,100,255),width=2)
 # Full-view thumbnail keeps context while the three principal panels use matched crops.
 tile,pos,_=panel(im,(18,704,135,170));canvas.paste(tile,pos);d=ImageDraw.Draw(canvas)
 fmt=lambda t:'null / 无有效尖端' if t is None else f'({t[0]:.2f}, {t[1]:.2f}) px'
 d.text((175,710),'A 尖端：'+fmt(tip),font=FONTS[20],fill=COLORS['yellow'])
 d.text((175,745),'研究输出：'+fmt(dec.get('tip')),font=FONTS[20],fill=COLORS['text'])
 d.text((175,780),f'状态：{dec.get("decision")}  |  参考可观察覆盖：{100*z["states"]["coverage"]:.1f}%',font=FONTS[20],fill=COLORS['text'])
 d.text((175,815),f'A 停止：{z["A"]["native"]["stop_reason"]}  |  候选 {len(z["pool"])}  |  原图 {im.shape[1]} × {im.shape[0]}',font=FONTS[17],fill=COLORS['muted'])
 d.text((175,850),'坐标为原图像素。黄圈=A；绿圈=研究改动；紫十字=程序 GT（仅受控图）。15 FPS 为播放速度。',font=FONTS[17],fill=COLORS['muted'])
 return np.asarray(canvas)
def writer(path):
 path.parent.mkdir(parents=True,exist_ok=True);log=path.with_suffix('.ffmpeg.log').open('w')
 p=subprocess.Popen([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1600x900','-r','15','-i','-','-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],stdin=subprocess.PIPE,stderr=log)
 return p,log
def execute(kind):
 root=RUN/'07_media';inventory=[];pngs=[];current=None;wr=None;log=None;count=0
 folder=RUN/('03_exposed_regression' if kind in ['real','exposed'] else '04_NEW_DEV');src=folder/('real_predictions.jsonl' if kind=='real' else 'predictions.jsonl')
 labels={} if kind=='real' else {(z['case_id'],z['frame_id']):z for z in jl(folder/'evaluator_GT.jsonl')}
 failures={(z['case_id'],int(z['frame_id'])) for z in rows(RUN/'01_diagnosis/failure_stage_audit.csv')}
 key={'group_x':{51,473},'ct2':{6,18,84},'group_a':{0,100,550},'group_c':{0,170,561},'group_h':{0,200,409},'three_point_bend':{0,100,300,519}}
 for z in jl(src):
  g=z['group'] if kind=='real' else kind;fid=z['frame_id'];cid=z.get('case_id',g);lab=labels.get((cid,fid))
  if g!=current:
   if wr:wr.stdin.close();assert wr.wait()==0;log.close();inventory.append(dict(group=current,frames=count,video=str(video.relative_to(RUN))))
   current=g;count=0;video=root/f'videos/{g}_A_AP3.mp4';wr,log=writer(video)
  frame=render(z,lab);wr.stdin.write(frame.tobytes());count+=1
  fn=root/f'per_frame/{g}/{cid}_{fid:04d}.png';fn.parent.mkdir(parents=True,exist_ok=True)
  ok,buf=cv2.imencode('.png',cv2.cvtColor(frame,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_PNG_COMPRESSION,2]);assert ok;buf.tofile(str(fn));pngs.append(dict(group=g,frame_id=fid,case_id=cid,path=str(fn.relative_to(RUN)),sha256=sha(fn)))
  iskey=fid in key.get(g,set()) if kind=='real' else ((cid,fid) in failures if kind=='exposed' else fid==2)
  if iskey:
   diag=render(z,lab,True);put(root/f'key_cases/{cid}_{fid:04d}.png',cv2.cvtColor(diag,cv2.COLOR_RGB2BGR))
  if count%100==0:print('MEDIA',kind,g,count,flush=True)
 if wr:wr.stdin.close();assert wr.wait()==0;log.close();inventory.append(dict(group=current,frames=count,video=str(video.relative_to(RUN))))
 csvout(root/f'{kind}_video_inventory.csv',inventory);csvout(root/f'{kind}_png_inventory.csv',pngs);print('MEDIA DONE',kind,len(pngs),flush=True)
if __name__=='__main__':execute(sys.argv[1] if len(sys.argv)>1 else 'real')
