"""Saved-result renderer only; cannot call a detector or change a prediction."""
from common_ap import *
from PIL import Image,ImageDraw,ImageFont
import subprocess,html
cv2.setNumThreads(1)
FF=str(ROOT/'third_party/ffmpeg/ffmpeg.exe');M=O/'08_media';FONT='C:/Windows/Fonts/msyh.ttc'
FONTS={};TXT=[];NAMES=dict(group_a='开发组A',group_c='验证组C',ct2='CT2',group_h='开发组HMT',group_x='排除组X（退役历史诊断）',three_point_bend='三点弯')
def tx(s,xy,size=20,color=(225,235,244)):TXT.append((s,xy,size,color))
def flush(im):
 a=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB));dr=ImageDraw.Draw(a)
 for s,p,size,c in TXT:
  if size not in FONTS:FONTS[size]=ImageFont.truetype(FONT,size)
  dr.text(p,s,font=FONTS[size],fill=c)
 TXT.clear();return cv2.cvtColor(np.asarray(a),cv2.COLOR_RGB2BGR)
def box(out,im,b):
 x,y,w,h=b;ih,iw=im.shape[:2];s=min(w/iw,h/ih);size=(max(1,round(iw*s)),max(1,round(ih*s)));im=cv2.resize(im,size,interpolation=cv2.INTER_AREA if s<1 else cv2.INTER_LINEAR);ox=x+(w-size[0])//2;oy=y+(h-size[1])//2;out[oy:oy+size[1],ox:ox+size[0]]=im
def line(im,p,color=(50,70,240),width=2,shift=(0,0)):
 p=np.asarray(p,float).reshape(-1,2)-shift
 if len(p)>1:cv2.polylines(im,[np.rint(p).astype('int32')],False,color,width,cv2.LINE_AA)
def tipmark(im,p,color=(25,230,255),shift=(0,0)):
 q=tuple(np.rint(np.array(p)-shift).astype(int));cv2.circle(im,q,6,color,2,cv2.LINE_AA);cv2.drawMarker(im,q,color,cv2.MARKER_CROSS,20,1)
def anchors_draw(im,pp,shift):
 p=np.array(pp)-shift
 for k,q in enumerate(p):cv2.drawMarker(im,tuple(np.rint(q).astype(int)),(245,120,30),cv2.MARKER_CROSS,20,1);cv2.putText(im,'P'+str(k+1),tuple(np.rint(q+[7,-6]).astype(int)),cv2.FONT_HERSHEY_SIMPLEX,.5,(245,120,30),1,cv2.LINE_AA)
 for t in np.arange(0,1,.07):line(im,[p[0]+t*(p[1]-p[0]),p[0]+min(1,t+.035)*(p[1]-p[0])],(245,120,30),1)
def crop_for(im,cp,path):
 co,u,d=anchors(cp);p=[co+[-.28*d,-.7*d],co+[1.15*d,.7*d]]
 if len(path):p.extend(np.asarray(path)[::max(1,len(path)//100)])
 p=np.asarray(p);lo=np.maximum([0,0],np.floor(p.min(0)-.06*d)).astype(int);hi=np.minimum([im.shape[1],im.shape[0]],np.ceil(p.max(0)+.08*d)).astype(int)
 return [int(lo[0]),int(lo[1]),int(hi[0]),int(hi[1])]
def render(raw,z,title,gt=None):
 im=np.full((1080,1920,3),(25,19,12),np.uint8);cp=z['points'];path=z['A_path'];valid=z['A_tip_valid'];tip=z['A_tip'];crop=crop_for(raw,cp,path);x0,y0,x1,y1=crop;shift=np.array([x0,y0]);local=cv2.cvtColor(raw[y0:y1,x0:x1],cv2.COLOR_GRAY2BGR)
 tx(title+' | 原图 · 冻结 A · A′ 研究旁路',(16,9),28);tx(f"num={z['frame_id']} | {z['filename']} | 原图 {raw.shape[1]}×{raw.shape[0]} | PHASE_UNKNOWN",(16,50),19)
 overview=cv2.cvtColor(cv2.resize(raw,(max(1,round(raw.shape[1]*min(1,350/raw.shape[0]))),min(raw.shape[0],350)),interpolation=cv2.INTER_AREA),cv2.COLOR_GRAY2BGR)
 sx=overview.shape[1]/raw.shape[1];sy=overview.shape[0]/raw.shape[0];cv2.rectangle(overview,(round(x0*sx),round(y0*sy)),(round(x1*sx),round(y1*sy)),(200,150,70),1)
 X=[16,650,1284]
 for col,label in enumerate(['原图（完整视野 + 统一局部）','冻结 A：正式输出','A′：门槛未通过，保留 A']):tx(label,(X[col],88),21);box(im,overview,(X[col],125,620,245))
 panels=[local,local.copy(),local.copy()]
 for p in panels[1:]:
  anchors_draw(p,cp,shift)
  if valid:
   line(p,path,shift=shift);tipmark(p,tip,shift=shift)
  if gt and gt.get('tip'):tipmark(p,gt['tip'],(240,60,230),shift)
 for col,p in enumerate(panels):box(im,p,(X[col],395,620,495))
 tx(f"局部原图范围 x={x0}…{x1} y={y0}…{y1}",(16,914),18)
 val=f"({tip[0]:.3f}, {tip[1]:.3f}) px"if valid else'0 px（valid=0）'
 tx('A 尖端: '+val,(650,914),18);tx('A′ 尖端: '+val,(1284,914),18)
 tx(f"向右投影: {z['horizontal_length_px']:.3f} px"if valid else'向右投影: 0 px（valid=0）',(1284,944),18)
 tx('局部参考几何: '+z['reference_alignment_state']+' | 光度: '+z['photometry_state'],(16,980),18)
 tx('红线/黄十字仅显示 A 正式有效尖端对应路径；A′ 未新增确认。'+('紫色=程序合成GT。'if gt else'真实物理尖端误差 N/A。'),(16,1012),18)
 tx('15 FPS 为演示播放速度；A′ 原生完整性能 NOT_TESTED | KEEP_A_RESEARCH_FALLBACK',(16,1046),17)
 return flush(im),crop
def savepng(p,im):
 p.parent.mkdir(parents=True,exist_ok=True);ok,b=cv2.imencode('.png',im,[cv2.IMWRITE_PNG_COMPRESSION,3]);assert ok;b.tofile(str(p))
def gallery(folder,files,title,video):
 write(folder/'index.html',f'''<!doctype html><meta charset="utf-8"><title>{html.escape(title)}</title><style>body{{background:#0d1722;color:#e4edf5;font:18px sans-serif;margin:24px}}a{{color:#8fcaff}}img,video{{max-width:100%}}input{{width:65%}}</style><h1>{html.escape(title)}</h1><p>A′参考有效性研究；保留冻结A，未声称真实精度改善。15FPS为演示速度。</p><video controls preload="metadata" src="{video}"></video><p><button onclick="show(i-1)">上一帧</button><input id="r" type="range" min="0" max="{len(files)-1}" value="0" oninput="show(+this.value)"><button onclick="show(i+1)">下一帧</button><span id="n"></span><a id="a" target="_blank">打开PNG</a></p><img id="im"><script>let i=0;const f={json.dumps(files)};function show(j){{i=Math.max(0,Math.min(f.length-1,j));r.value=i;im.src=f[i];a.href=f[i];n.textContent=(i+1)+'/'+f.length+' ';}}show(0);</script>''')
def encode(folder,out):subprocess.run([FF,'-y','-v','error','-framerate','15','-i',str(folder/'%06d.png'),'-c:v','libx264','-preset','fast','-crf','18','-threads','4','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],check=True)
def real():
 mapping=[]
 for g,name in NAMES.items():
  folder=M/g;marker=folder/'complete.json'
  if marker.exists():continue
  frames=folder/'frames';files=[]
  for z in jl(O/f'06_real_regression/{g}_predictions.jsonl'):
   raw=read(z['input_image']);im,crop=render(raw,z,name);p=frames/f"{z['frame_id']:06d}.png";savepng(p,im);files.append('frames/'+p.name);mapping.append(dict(group=g,frame_id=z['frame_id'],input_sha256=z['input_sha256'],PNG=str(p),PNG_sha256=sha(p),crop=crop))
   if z['frame_id']%100==0:print('MEDIA',g,z['frame_id'],flush=True)
  out=folder/f'{g}_original_A_Aprime.mp4';encode(frames,out);gallery(folder,files,name,out.name);save(marker,dict(frames=len(files),video=str(out),video_sha256=sha(out)));csvout(folder/'frame_map.csv',[r for r in mapping if r['group']==g]);print('VIDEO_COMPLETE',g,flush=True)
def dev():
 folder=M/'engineering_DEV';frames=folder/'frames';files=[]
 for i,z in enumerate(jl(O/'04_candidate_evidence/DEV_predictions.jsonl')):
  cp=z['points'];co,u,d=anchors(cp);f=z['A']['formal'];v=f['confirmed_tip'];t=f['tip'];zz=dict(points=cp,A_path=f['raw_path'],A_tip_valid=v,A_tip=t,frame_id=i,filename=z['case_id']+' frame'+str(z['frame_id']),horizontal_length_px=float((np.array(t)-co)@u)if t else None,reference_alignment_state=z['reg']['state'],photometry_state=z['photo']['state'])
  im,_=render(read(z['input_image']),zz,'ENGINEERING DEV（非独立TEST）',z['GT']);p=frames/f'{i:06d}.png';savepng(p,im);files.append('frames/'+p.name)
 out=folder/'DEV_original_A_Aprime_GT.mp4';encode(frames,out);gallery(folder,files,'工程DEV（所有案例，含失败）',out.name);save(folder/'complete.json',dict(frames=len(files),video_sha256=sha(out)))
if __name__=='__main__':real()if sys.argv[1]=='real'else dev()
