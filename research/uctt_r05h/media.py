"""Actual original-image overlays, one video per group; annotation use is offline only."""
from evaluate import *
import cv2,subprocess,html
from PIL import Image,ImageDraw,ImageFont
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20);SMALL=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16);BIG=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',30)
NAMES={'group_c':'验证组C','three_point_bend':'三点弯','group_a':'开发组A','ct2':'CT2','group_h':'开发组H','ct3':'CT3'}
COLORS={'OBSERVED':'#25efa8','TENTATIVE':'#ffb34d','PREDICTED':'#a9a0ff','UNOBSERVED':'#eeeeee'}
def text(d,xy,s,font=FONT,fill='#e5edf5'):
 for line in s.split('\n'):d.text(xy,line,font=font,fill=fill);xy=(xy[0],xy[1]+font.size+7)
def view(im,origin,u,v,lo,hi,size=(770,300)):
 o=np.array(origin);u=np.array(u);v=np.array(v);lo=np.array(lo);hi=np.array(hi);scale=min((size[0]-16)/(hi[0]-lo[0]),(size[1]-16)/(hi[1]-lo[1]));margin=(np.array(size)-scale*(hi-lo))/2
 M=np.array([[scale*u[0],scale*u[1],margin[0]-scale*(o@u+lo[0])],[scale*v[0],scale*v[1],margin[1]-scale*(o@v+lo[1])]])
 arr=cv2.warpAffine(im,M,size,flags=cv2.INTER_LINEAR,borderValue=45);return Image.fromarray(arr).convert('RGB'),M
def xy(p,M):return tuple((M@np.array([*p,1])).tolist())
def overlay(base,M,t=None,label=None,old=None):
 im=base.copy();d=ImageDraw.Draw(im)
 if label:
  for s in label['shapes']:
   if s['label']=='crack_path' and len(s['points'])>=2:d.line([xy(p,M) for p in s['points']],fill='#ff43d1',width=2)
   elif s['label']=='crack_tip':
    x,y=xy(s['points'][0],M);d.line([(x-8,y),(x+8,y)],fill='#ff43d1',width=3);d.line([(x,y-8),(x,y+8)],fill='#ff43d1',width=3)
   elif s['label']=='uncertain_region':d.line([xy(p,M) for p in s['points']+s['points'][:1]],fill='#ff43d1',width=2)
 if old and old.get('observed') and old.get('tip'):
  x,y=xy(old['tip'],M);d.rectangle([x-5,y-5,x+5,y+5],outline='#65b8ff',width=2)
 if t:
  for p in t['visible_segments']:
   if len(p)>1:d.line([xy(x,M) for x in p],fill='#25efa8',width=2)
   elif p:
    x,y=xy(p[0],M);d.ellipse([x-1,y-1,x+1,y+1],fill='#25efa8')
  for i,p in enumerate(t['inferred_gaps']):
   if i%2==0:d.line([xy(x,M) for x in p],fill='#ff734c',width=2)
  for i,q in enumerate(t['alternative_stops'][:8]):
   x,y=xy(q['xy'],M);d.ellipse([x-3,y-3,x+3,y+3],outline='#f5df72',width=1)
  if t['working_tip']:
   x,y=xy(t['working_tip'],M);d.ellipse([x-7,y-7,x+7,y+7],outline=COLORS[t['status']],width=3)
 return im
def main():
 assert (OUT/'evaluation_complete.json').exists();cv2.setNumThreads(1);labs=labels();summary=read(OUT/'evaluation_summary.json');stats=read(OUT/'full_sequence_stats.json');ev={(r['dataset_id'],int(r['frame_id'])):r for r in rows(OUT/'experiments/selected_evaluation.csv') if r['variant']=='FULL'};inventory={(r['dataset_id'],int(r['frame_id'])):r for r in rows(OUT/'input_inventory.csv')}
 old={}
 for p in [D/'dev_frames.jsonl',D/'val_frames.jsonl']:
  for line in p.open(encoding='utf8'):
   r=json.loads(line);old[r['dataset_id'],r['frame_id']]=r
 metadata=[];videos=[]
 for g in VAL+DEV:
  require(g,'validation' if g in VAL else 'development');folder=OUT/'galleries/images'/g;folder.mkdir(exist_ok=True);s=next(r for r in summary if r['dataset_id']==g and r['variant']=='FULL');st=next(r for r in stats if r['dataset_id']==g);paths=[];role_name='验证组 · 冻结后一次性只读验证' if g in VAL else '开发组 · 同一冻结版本'
  intro=Image.new('RGB',(1600,1000),'#111d2b');d=ImageDraw.Draw(intro);text(d,(65,70),f'R05H | {NAMES[g]}',BIG);text(d,(65,140),role_name,BIG)
  text(d,(65,230),f"完整序列 {st['frames']} 帧，未剔除失败帧\n人工可见标注 {s['visible']} 帧，另有不确定标注 {s['uncertain']} 帧\n正式确认 {s['observed']}/{s['visible']}；正式尖端 10px 内 {s['observed_hit10']}/{s['visible']}\n工作端点 10px 内 {s['working_hit10']}/{s['visible']}；>100px {s['working_over100']}；>500px {s['working_over500']}\n原生耗时 P95 {st['p95']:.2f} ms；搜索不完整 {st['incomplete']}/{st['frames']}\n\n青绿实线：当前可见路径；橙色虚线：推断间隙\n圆圈：工作端点，颜色表示状态；黄色点：停止候选\n紫色：人工离线对照；蓝色方框：旧研究基线 A55a0 已确认端点\n暂定输出不代表确认结果；无标注帧不计算准确率。\n人工标注不训练；验证组不回调参数；排除组X排除。",FONT)
  intro_path=folder/'intro.jpg';intro.save(intro_path,quality=92)
  for t in stream(g):
   f=t['frame_id'];key=g,f;r=inventory[key];raw=Path(r['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);label=labs.get(key);u=np.array(t['forward']);v=np.array([-u[1],u[0]]);o=np.array(t['origin']);points=[p['xy'] for p in t['main_path']]
   if label:points.extend(p for sh in label['shapes'] for p in sh['points'])
   lo=np.array([-.08*t['spacing'],-.18*t['spacing']]);hi=np.array([max(150,t['spacing']*1.6),.18*t['spacing']])
   if points:
    q=np.array(points)-o;uv=np.column_stack([q@u,q@v]);lo=np.minimum(lo,uv.min(0)-15);hi=np.maximum(hi,uv.max(0)+15)
   base,M=view(im,o,u,v,lo,hi);tips=[sh['points'][0] for sh in (label or {}).get('shapes',[]) if sh['label']=='crack_tip'];center=tips[0] if tips else t['working_tip'] or (o+u*t['spacing']).tolist();zoom,Z=view(im,center,u,v,[-85,-35],[85,35],(770,300))
   canvas=Image.new('RGB',(1600,1000),'#111d2b');d=ImageDraw.Draw(canvas);text(d,(20,12),f"R05H | {NAMES[g]}  帧 {f} | {role_name}",BIG);text(d,(20,58),f"{t['status']}  |  {t['reason']}  |  native {t['runtime_breakdown']['total_native_ms']:.2f} ms",FONT,COLORS[t['status']])
   text(d,(20,104),'原图局部（与右图同一视野）');text(d,(810,104),'R05H 实际可见路径 / 工作端点 / 停止候选')
   canvas.paste(base,(20,137));canvas.paste(overlay(base,M,t,label,old.get(key)),(810,137))
   text(d,(20,460),'尖端附近原图放大');text(d,(810,460),'同一局部放大 + 实际输出 / 人工对照')
   canvas.paste(zoom,(20,494));canvas.paste(overlay(zoom,Z,t,label,old.get(key)),(810,494))
   e=ev.get(key,{});error=e.get('working_error','');observed_error=e.get('observed_error','');subtitle=f"离线标注={e.get('visibility','无标注')} | 工作误差={error or 'N/A'} px | 正式误差={observed_error or 'N/A'} px"
   text(d,(20,818),subtitle,FONT);text(d,(20,850),f"搜索完整={t['search_complete']} | 物理缺口={t['physical_notch']} | 停止候选={len(t['alternative_stops'])} | 本帧可信历史写入={t['history_written']}",SMALL)
   selected=t['alternative_stops'][t['selected_stop']] if t['selected_stop']>=0 else None
   text(d,(20,878),f"参考={selected['reference']['state']+' / '+selected['reference']['classification'] if selected else 'N/A'} | 放大中心={'人工尖端（仅展示裁切）' if tips else '工作端点或几何中心'}",SMALL)
   text(d,(20,910),'绿线=当前可见；橙虚线=推断间隙；紫=离线人工对照；蓝方框=A55a0；圆圈颜色=正式/暂定状态。',SMALL)
   text(d,(20,940),'研究算法未达到生产精度；完整保留失败帧。视频8帧/秒仅为播放速度。',SMALL)
   p=folder/f'{f:06d}.jpg';canvas.save(p,quality=90);paths.append(p);metadata.append(dict(dataset_id=g,frame_id=f,path=str(p.relative_to(OUT)).replace('\\','/'),original_to_panel=M.tolist(),zoom_original_to_panel=Z.tolist(),source_sha256=r['sha256'],state=t['status']))
   if len(paths)%100==0:print('images',g,len(paths),flush=True)
  video=OUT/'videos'/f'R05H_{g}.mp4';concat=OUT/'videos'/f'{g}_frames.txt';duration=4+len(paths)/8
  concat.write_text("file '"+str(intro_path).replace('\\','/')+"'\nduration 4\n"+''.join("file '"+str(p).replace('\\','/')+"'\nduration 0.125\n" for p in paths)+"file '"+str(paths[-1]).replace('\\','/')+"'\n",encoding='utf8')
  cmd=[str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-t',str(duration),'-vf','fps=8','-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(video)]
  with (OUT/'videos'/f'{g}_encode.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
  probe=json.loads(subprocess.check_output([str(ROOT/'third_party/ffmpeg/ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(video)]));count=int(probe['streams'][0]['nb_frames']);assert count==32+len(paths),(g,count,len(paths));subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-v','error','-i',str(video),'-f','null','-'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  videos.append(dict(dataset_id=g,path=str(video.relative_to(OUT)).replace('\\','/'),unique_source_frames=len(paths),encoded_frames=count,duration=duration,full_decode_pass=True,sha256=sha(video)));write(OUT/'videos/verified_videos.json',videos);print('VIDEO COMPLETE',g,flush=True)
 save(OUT/'galleries/render_manifest.csv',metadata)
 style='<style>body{background:#111d2b;color:#e5edf5;font:18px system-ui;margin:30px}a{color:#6de6d0}video,img{width:min(100%,1600px)}select,input,button{font:inherit;margin:6px}</style>'
 page='<!doctype html><meta charset="utf-8"><title>R05H 六组实验视频</title>'+style+'<h1>R05H 六组完整实验视频</h1><p>验证组优先展示。完整保留失败帧；标注只对比、不训练；验证组不调参；排除组X排除。</p><p><a href="../development_report.md">量化报告</a> · <a href="all_frames.html">全部2647帧局部对比图</a></p>'
 for v in videos:page+=f'<h2>{NAMES[v["dataset_id"]]} — {"验证组" if v["dataset_id"] in VAL else "开发组"}</h2><video controls preload="metadata" src="../{v["path"]}"></video><p><a href="../{v["path"]}">打开视频</a> · 原图 {v["unique_source_frames"]} 帧</p>'
 (OUT/'galleries/index.html').write_text(page,encoding='utf8')
 entries=[dict(g=r['dataset_id'],f=r['frame_id'],p=r['path'].removeprefix('galleries/')) for r in metadata]
 page='<!doctype html><meta charset="utf-8"><title>R05H 2647帧局部对比</title>'+style+'<h1>R05H 逐帧局部对比</h1><p><a href="index.html">六组视频</a></p><select id="group">'+''.join(f'<option value="{g}">{NAMES[g]}</option>' for g in VAL+DEV)+'</select><button id="prev">上一帧</button><input id="slider" type="range" min="0" value="0"><button id="next">下一帧</button><span id="counter"></span><br><a id="link"><img id="frame"></a><script>const data='+json.dumps(entries)+';let filtered=[],i=0;function show(){i=Math.max(0,Math.min(i,filtered.length-1));let r=filtered[i];frame.src=r.p;link.href=r.p;counter.textContent=r.g+" / "+r.f+" ("+(i+1)+"/"+filtered.length+")";slider.value=i}function reset(){filtered=data.filter(x=>x.g===group.value);i=0;slider.max=filtered.length-1;show()}group.onchange=reset;prev.onclick=()=>{i--;show()};next.onclick=()=>{i++;show()};slider.oninput=()=>{i=+slider.value;show()};reset();</script>'
 (OUT/'galleries/all_frames.html').write_text(page,encoding='utf8');write(OUT/'media_complete.json',dict(images=len(metadata),videos=len(videos),verified=True));print('MEDIA COMPLETE',flush=True)
if __name__=='__main__':main()

