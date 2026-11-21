"""Offline data-driven visual evidence; labels only control display/comparison."""
from common import *
from compare import original,local
import numpy as np,cv2,zipfile,html,subprocess,re
from PIL import Image,ImageDraw,ImageFont
FONT='C:/Windows/Fonts/msyh.ttc'
def text(d,xy,s,size=20,color='#e4ebf5'):d.text(xy,str(s),fill=color,font=ImageFont.truetype(FONT,size))
def fitted(image,size):
 out=Image.new('RGB',size,'#142034');image=image.copy();image.thumbnail(size,Image.Resampling.LANCZOS);out.paste(image,((size[0]-image.width)//2,(size[1]-image.height)//2));return out
def imageview(im,box,t,label,with_candidates=False):
 x0,y0,x1,y1=box;crop=im.crop(box);w,h=850,350;scale=min(w/crop.width,h/crop.height);crop=crop.resize((max(1,round(crop.width*scale)),max(1,round(crop.height*scale))));d=ImageDraw.Draw(crop)
 def xy(p):return ((p[0]-x0)*scale,(p[1]-y0)*scale)
 for s in label['shapes']:
  if s['label']=='crack_path':d.line([xy(p) for p in s['points']],fill='#ff4d69',width=2)
  if s['label']=='crack_tip':
   x,y=xy(s['points'][0]);d.line((x-7,y,x+7,y),fill='#ff4d69',width=3);d.line((x,y-7,x,y+7),fill='#ff4d69',width=3)
 roi=t['roi'];x,y=xy(roi[:2]);xx,yy=xy([roi[0]+roi[2]-1,roi[1]+roi[3]-1])
 if roi[2]>0 and roi[3]>0:d.rectangle((x,y,xx,yy),outline='#ffe174',width=2)
 if t['formal']['tip'] is not None:
  x,y=xy(t['formal']['tip']);d.ellipse((x-6,y-6,x+6,y+6),outline='#28e1ee',width=3)
 if t['selected_original']:d.line([xy(p) for p in t['selected_original']],fill='#28e1ee',width=2)
 if with_candidates:
  for c,p in zip(t['evidence']['candidates'],original([c['xy'] for c in t['evidence']['candidates']],t)):
   x,y=xy(p);kept=c['retained_id']>=0 and not c['reason'].startswith('directional_duplicate');color='#58ef83' if kept else '#eea43e';r=3 if kept else 1;d.ellipse((x-r,y-r,x+r,y+r),outline=color,width=1)
  for s in label['shapes']:
   if s['label']=='crack_tip':
    x,y=xy(s['points'][0]);d.line((x-7,y,x+7,y),fill='#ff4d69',width=3);d.line((x,y-7,x,y+7),fill='#ff4d69',width=3)
 return fitted(crop,(w,h))
def mapview(array,t,label,key):
 a=np.array(array,copy=True);finite=np.isfinite(a)
 if key=='referenceQuality':rgb=np.zeros((*a.shape,3),np.uint8);rgb[a>0]=[50,190,140];rgb[~(a>0)]=[86,55,103]
 elif key=='reasonMask':
  v=np.nan_to_num(a).astype(np.int32);rgb=np.zeros((*a.shape,3),np.uint8);rgb[(v&4)!=0]=[90,54,116];rgb[(v&64)!=0]=[35,214,173];rgb[(v&2)!=0]=[120,91,48]
 else:
  low,high=(-20,20) if key=='referenceChange' else (0,30);v=np.clip((np.nan_to_num(a,nan=low)-low)/(high-low)*255,0,255).astype(np.uint8);rgb=cv2.cvtColor(cv2.applyColorMap(v,cv2.COLORMAP_TURBO),cv2.COLOR_BGR2RGB);rgb[~finite]=[88,54,110]
 out=Image.fromarray(rgb);d=ImageDraw.Draw(out)
 tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];p=local([tips[0]],t)[0] if tips else np.array([out.width/2,out.height/2])
 if tips:d.ellipse((p[0]-5,p[1]-5,p[0]+5,p[1]+5),outline='white',width=2)
 box=[max(0,int(p[0])-100),max(0,int(p[1])-100),min(out.width,int(p[0])+101),min(out.height,int(p[1])+101)]
 if box[2]>box[0] and box[3]>box[1]:out=out.crop(box)
 return fitted(out,(275,300)),box
def panel(r,t,label,metric):
 path=PRE/'R05_LabelMe_Annotation_Package'/r['selected_image'];assert sha(path)==r['source_sha256'];im=Image.open(path).convert('RGB')
 out=Image.new('RGB',(1800,1080),'#0b1424');d=ImageDraw.Draw(out);mode=metric['mode'];e=t['evidence'];err=f"{float(metric['error_px']):.3f}" if metric['error_px'] else 'N/A'
 text(d,(30,18),f"{r['dataset_id']} / {r['frame_id']}   {role(r['dataset_id'])}   {mode} 旁路审计",29)
 text(d,(30,66),f"原 A 输出误差 {err} px | GT {metric['gt_visibility']} | raw {e['raw_count']} → retained {e['retained_count']} | 首失效 {metric['first_failure_stage']}",23)
 text(d,(30,104),'红：人工对比路径/尖端  青：原 A 输出  黄：实际尖端 ROI  橙：未保留候选  绿：保留候选',21)
 roi=t['roi'];tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];x,y,w,h=roi
 if w>0 and h>0:box=(max(0,x-30),max(0,y-30),min(im.width,x+w+30),min(im.height,y+h+30))
 else:box=(0,0,im.width,im.height)
 text(d,(30,153),'原图全貌；原始像素坐标',18);out.paste(imageview(im,(0,0,im.width,im.height),t,label),(30,182))
 text(d,(920,153),f'实际 ROI {roi}；候选来自原生快照',18);out.paste(imageview(im,box,t,label,True),(920,182))
 names=[('legacy','旧 legacyScore'),('currentEvidence','独立 currentEvidence'),('referenceChange','referenceChange / UNKNOWN紫'),('referenceQuality','referenceQuality 有效/未知'),('reasonMask','reasonMask 恢复绿/未知紫'),('referenceEvidence','参考暗线 referenceEvidence')]
 with np.load(OUT/'maps'/f"{r['dataset_id']}__{int(r['frame_id']):06d}.npz") as maps:
  for i,(key,title) in enumerate(names):
   left=30+i*295;text(d,(left,560),title,15)
   if key in maps:
    pic,cropbox=mapview(maps[key],t,label,key);out.paste(pic,(left,590));text(d,(left,900),f'局部 [{cropbox[0]},{cropbox[1]}]',15)
   else:text(d,(left,700),'NOT COMPUTED',18)
 text(d,(30,946),'下排白圈为人工尖端，仅用于裁图对比；响应色标0–30，变化色标−20–20。GT 未进入运行时或预算规则。',20)
 text(d,(30,985),'B3 归属 / B4 终止：BLOCKED；绿色候选不是已确认尖端。实际安全门失败时不升级生产。',22,'#ffd17a')
 text(d,(30,1025),'暗线证据方案；没有宣称亮线支持。未知参考不等于负证据；本图不证明真实误报率。',18)
 return out
def main():
 mode='B2' if (OUT/'B2_dev_complete.json').exists() else 'B1';metrics={}
 for phase in ['dev','val']:
  for r in rows(OUT/f'evaluation_{mode}_{phase}.csv'):metrics[r['dataset_id'],r['frame_id']]=r
 selection=rows(OUT/'selected_frames.csv');sections=[];files=[]
 with zipfile.ZipFile(R05/'human_annotations_six_groups_snapshot.zip') as z:
  for r in selection:
   g,f=r['dataset_id'],r['frame_id'];require(g,'comparison',uses_annotations=True);name=f'{g}__{int(f):06d}';t=read(OUT/'traces'/f'{mode}_{name}.json');label=json.loads(z.read(r['selected_json']));metric=metrics[g,f]
   img=panel(r,t,label,metric);file=OUT/'images'/f'{name}.jpg';img.save(file,quality=90);files.append(file)
   title=f"{g}/{f} · {metric['first_failure_stage']} · raw10={metric['raw_candidate10']} retained10={metric['retained_candidate10']}"
   sections.append(f'<section><h2>{html.escape(title)}</h2><a href="images/{name}.jpg"><img loading="lazy" src="images/{name}.jpg"></a><p><a href="traces/{mode}_{name}.json">原生完整快照</a></p></section>')
 body='<!doctype html><html lang="zh"><meta charset="utf-8"><title>R05E 故障与证据恢复图册</title><style>body{background:#0b1424;color:#e3ebf7;font:18px system-ui;max-width:1800px;margin:30px auto}a{color:#72daf2}img{width:100%}section{margin:40px 0;border-top:1px solid #526070}</style><h1>R05E：证据恢复不等于尖端检测成功</h1><p>全部120标注选帧；开发80，冻结后验证40。排除组X排除。标注仅离线对比。B3/B4状态以 gate_matrix.csv 为准；本图集不宣称误锁已修复。</p><p><a href="development_report.md">开发报告</a> · <a href="gate_matrix.csv">验收门</a> · <a href="candidate_lineage.csv">逐帧候选链</a></p>'+''.join(sections)+'</html>'
 (OUT/'R05E_Failure_And_Improvement_Gallery.html').write_text(body,encoding='utf8')
 for link in re.findall(r'(?:href|src)="([^"]+)"',body):assert (OUT/link).exists(),link
 # Every selected frame appears for 2 seconds. Playback speed is not inference FPS.
 ffmpeg=ROOT/'third_party/ffmpeg/ffmpeg.exe';video=OUT/'R05E_Validation_Results.mp4'
 with (OUT/'logs/video.log').open('w') as log:
  process=subprocess.Popen([str(ffmpeg),'-y','-hide_banner','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1800x1080','-framerate','5','-i','-','-an','-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],stdin=subprocess.PIPE,stderr=log)
  for file in files:
   data=Image.open(file).convert('RGB').tobytes()
   for _ in range(10):process.stdin.write(data)
  process.stdin.close();assert process.wait()==0
 decoded=subprocess.run([str(ffmpeg),'-v','error','-i',str(video),'-f','null','NUL'],capture_output=True,text=True);assert decoded.returncode==0 and not decoded.stderr
 write(OUT/'media_qa.json',dict(images=len(files),video_frames=len(files)*10,seconds=len(files)*2,full_decode='PASS',relative_links='PASS',video_sha=sha(video)))
 print('MEDIA',len(files),'images / video full decode PASS',flush=True)
if __name__=='__main__':main()
