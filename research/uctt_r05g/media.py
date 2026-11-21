"""Real replay rendering only. GT is read offline after all detector runs are frozen."""
from common import *
from evaluate import SENTINELS,path_samples
import cv2,numpy as np,gzip,zipfile,html,subprocess
from PIL import Image,ImageDraw,ImageFont
FONTPATH='C:/Windows/Fonts/msyh.ttc'
FONT=ImageFont.truetype(FONTPATH,19);SMALL=ImageFont.truetype(FONTPATH,15);BIG=ImageFont.truetype(FONTPATH,29)
COLORS={'gt':'#ee39dc','visible':'#10edb6','gap':'#ff6f3c','seed':'#7777ff','scan':'#ffca41','old':'#55b7ff'}
def lines(d,at,text,font=FONT,fill='#e4edf4'):
 for line in text.split('\n'):d.text(at,line,font=font,fill=fill);at=(at[0],at[1]+font.size+6)
def bounds(t,others,label=None):
 o=np.array(t['origin']);u=np.array(t['forward']);v=np.array([-u[1],u[0]]);L=t['spacing'];points=[]
 for q in [t]+others:points.extend([p['xy'] for p in q['selected_path']])
 if label is not None:points.extend(path_samples(label).tolist())
 low=np.array([-.08*L,-.15*L]);high=np.array([1.5*L,.15*L])
 if points:
  xy=np.array(points)-o;uv=np.column_stack([xy@u,xy@v]);low=np.minimum(low,uv.min(0)-15);high=np.maximum(high,uv.max(0)+15)
 return o,u,v,low,high
def view(im,b,size):
 o,u,v,lo,hi=b;w,h=size;scale=min((w-12)/(hi[0]-lo[0]),(h-12)/(hi[1]-lo[1]));margin=(np.array(size)-scale*(hi-lo))/2
 M=np.array([[scale*u[0],scale*u[1],margin[0]-scale*(np.dot(o,u)+lo[0])],[scale*v[0],scale*v[1],margin[1]-scale*(np.dot(o,v)+lo[1])]])
 inv=cv2.invertAffineTransform(M);p=np.array([[o[0],o[1],1],[o[0]+19,o[1]+11,1]]);q=p@M.T;back=np.column_stack([q,np.ones(len(q))])@inv.T;assert np.max(np.abs(back-p[:,:2]))<1e-8
 arr=cv2.warpAffine(im,M,size,flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=48)
 return Image.fromarray(arr).convert('RGB'),M,inv
def xy(p,M):return tuple((M@np.array([*p,1.])).tolist())
def overlay(image,M,t=None,label=None,a=None,static=None,fail=None):
 image=image.copy();d=ImageDraw.Draw(image)
 if t:
  layer=Image.new('RGBA',image.size,(0,0,0,0));ld=ImageDraw.Draw(layer)
  for s in t['scans']:
   if s['phase']=='tracking':
    p=np.array(s['predicted_point']);n=np.array(s['normal']);h=s['halfwidth'];ld.line([xy(p-h*n,M),xy(p+h*n,M)],fill=(255,196,55,24),width=1)
  image=Image.alpha_composite(image.convert('RGBA'),layer).convert('RGB');d=ImageDraw.Draw(image)
  path=t['selected_path']
  for x,y in zip(path[:-1],path[1:]):
   visible=x['visible'] and y['visible'];p,q=xy(x['xy'],M),xy(y['xy'],M)
   if visible:d.line([p,q],fill=COLORS['visible'],width=2)
   elif y['step']%2==0:d.line([p,q],fill=COLORS['gap'],width=2)
  for s in t['seeds']:
   p=xy(s['xy'],M);q=xy(np.array(s['xy'])+np.array(s['tangent'])*12,M);d.line([p,q],fill=COLORS['seed'],width=3);d.rectangle([p[0]-3,p[1]-3,p[0]+3,p[1]+3],outline=COLORS['seed'],width=2)
  if t['tracking_tip']:
   x,y=xy(t['tracking_tip'],M);d.ellipse([x-5,y-5,x+5,y+5],outline=COLORS['visible'],width=2)
  if fail and fail.get('node_id') not in [None,'']:
   node=next((p for p in path if p['id']==int(fail['node_id'])),None)
   if node:
    x,y=xy(node['xy'],M);d.line([(x-7,y-7),(x+7,y+7)],fill='#ff3232',width=3);d.line([(x-7,y+7),(x+7,y-7)],fill='#ff3232',width=3)
 if static:
  for c in static['candidates']:
   if c['id']==c['canonical_id']:
    x,y=xy(c['xy'],M)
    if 0<=x<image.width and 0<=y<image.height:d.ellipse([x-1,y-1,x+1,y+1],fill='#ffbb3f')
 if a:
  if a['path']:d.line([xy(p,M) for p in a['path']],fill=COLORS['old'],width=2)
  if a['confirmed_tip'] and a['tip']:
   x,y=xy(a['tip'],M);d.ellipse([x-6,y-6,x+6,y+6],outline=COLORS['old'],width=3)
 if label:
  for s in label['shapes']:
   if s['label']=='crack_path':d.line([xy(p,M) for p in s['points']],fill=COLORS['gt'],width=1)
   elif s['label']=='crack_tip':
    x,y=xy(s['points'][0],M);d.line([(x-7,y),(x+7,y)],fill=COLORS['gt'],width=2);d.line([(x,y-7),(x,y+7)],fill=COLORS['gt'],width=2)
 return image
def panel(canvas,at,base,M,title,sub,**kw):
 x,y=at;d=ImageDraw.Draw(canvas);lines(d,(x,y),title,FONT);lines(d,(x,y+28),sub,SMALL);canvas.paste(overlay(base,M,**kw),(x,y+53))
def stream(tag):
 with gzip.open(OUT/'traces'/f'{tag}_frames.jsonl.gz','rt',encoding='utf8') as f:
  for line in f:yield json.loads(line)
def main():
 cv2.setNumThreads(1);assert read(OUT/'E1_complete.json')['frames']==1565;assert (OUT/'experiments/selected_visible_eval.csv').exists()
 inv={(r['dataset_id'],int(r['frame_id'])):r for r in rows(OUT/'input_inventory.csv')};sel={(r['dataset_id'],int(r['frame_id'])):r for r in rows(OUT/'selection.csv')};a={(r['dataset_id'],r['frame_id']):r['formal'] for r in map(json.loads,(F/'A0_frames.jsonl').read_text().splitlines())}
 failures={(r['variant'],r['dataset_id'],int(r['frame_id'])):r for r in rows(OUT/'failure_first_divergence.csv')};ev={(r['variant'],r['dataset_id'],int(r['frame_id'])):r for r in rows(OUT/'experiments/selected_visible_eval.csv')};labels={};meta=[];cards=[]
 with zipfile.ZipFile(LABELS) as z:
  for key,r in sel.items():require(key[0],'development');require(key[0],'comparison',uses_annotations=True);labels[key]=json.loads(z.read(r['selected_json']))
 for t,b in zip(stream('E1_BEAM'),stream('E1_GREEDY')):
  g,f=t['dataset_id'],t['frame_id'];assert (g,f)==(b['dataset_id'],b['frame_id']);key=g,f;r=inv[key];require(g,'development');raw=Path(r['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);label=labels.get(key);box=bounds(t,[b],label);base,M,Minv=view(im,box,(776,300));canvas=Image.new('RGB',(1600,900),'#111d2b');d=ImageDraw.Draw(canvas)
  lines(d,(20,10),f'R05G 逐帧裂纹局部对照 | {g} / {f}',BIG)
  lines(d,(20,52),'研究输出：未确认主裂纹身份，不是生产尖端。青绿=当前可见轨迹；橙色虚线=推断缺口；紫色=离线人工对照。',SMALL)
  gt_text='有离线人工标注' if key in sel else '本帧无人工 GT，不计算准确率'
  panel(canvas,(18,85),base,M,'当前原图局部',gt_text)
  panel(canvas,(812,85),base,M,'研究基线 A55a0','蓝色=A 原生路径/已确认端点；超出本局部视野的旧误检见数值报告',a=a[key],label=label)
  panel(canvas,(18,454),base,M,'自动起点 · 贪心 beam=1',f"{b['reason']} | {b['time_total_native_ms']:.2f} ms | {b['scanline_count']} 截面",t=b,label=label,fail=failures.get(('E1_GREEDY',g,f)))
  panel(canvas,(812,454),base,M,'自动起点 · 有限束 beam=4',f"{t['reason']} | {t['time_total_native_ms']:.2f} ms | {t['scanline_count']} 截面",t=t,label=label,fail=failures.get(('E1_BEAM',g,f)))
  lines(d,(20,825),f"自动 observed=false；trusted_history=0；搜索不完备={bool(t['search_incomplete'])}。黄色细线为实际访问截面；红叉为离线定位首失效。",SMALL)
  lines(d,(20,853),'画面播放速度不是算法速度。验证组C/三点弯未准入，排除组X排除。局部视图由实际轨迹/原图几何确定。',SMALL)
  folder=OUT/'galleries/local_frames'/g;folder.mkdir(exist_ok=True);path=folder/f'{f:06d}.jpg';canvas.save(path,quality=91)
  meta.append(dict(dataset_id=g,frame_id=f,path=str(path.relative_to(OUT)).replace('\\','/'),source_sha256=r['sha256'],original_to_panel=M.tolist(),panel_to_original=Minv.tolist(),matrix_roundtrip_max_error='<1e-8 original px',label='OFFLINE_SELECTED_ONLY' if label else 'NONE',observed=False))
  if key in sel:
   ts={tag:read(OUT/'traces'/f'{tag}_{g}_{f}.json') for tag in ['E1_GREEDY','E1_BEAM','E0_GREEDY','E0_BEAM']};box=bounds(t,list(ts.values()),label);base2,M2,_=view(im,box,(870,310));card=Image.new('RGB',(1800,1330),'#111d2b');cd=ImageDraw.Draw(card);lines(cd,(20,10),f'{g} / {f} | 完整选帧证据对照 | {ev["E1_BEAM",g,f]["visibility"]}',BIG)
   lines(cd,(20,53),'紫色人工路径只作离线比较；蓝色方块为起点；青绿末端均为未确认候选。所有面板使用同一原图坐标变换。',SMALL)
   panel(card,(20,90),base2,M2,'当前原图局部 + 人工对照','原图显示不由人工路径生成算法轨迹',label=label)
   old=read(F/'traces'/f'B0_{g}_{f}.json');panel(card,(910,90),base2,M2,'旧研究 A55a0 + R05F 静态 B0','蓝色=A；黄色=B0 去重候选；不是 R05G 正式输出',a=a[key],static=old,label=label)
   for j,tag in enumerate(ts):
    x=20+(j%2)*890;y=485+(j//2)*395;e=ev[tag,g,f];failure=failures[tag,g,f];sub=f"端点诊断误差={e['tracking_error_px'] or 'N/A'} px; 首失效步={failure.get('step','')}"
    panel(card,(x,y),base2,M2,tag+' | '+ts[tag]['reason'],sub,t=ts[tag],label=label,fail=failure)
   name=f'{g}_{f:06d}.jpg';card.save(OUT/'galleries/images'/name,quality=93);cards.append(f'<article data-group="{g}"><h2>{g}/{f}</h2><p>首失效：{html.escape(failures["E1_BEAM",g,f]["stage"])}；<a href="../traces/E1_BEAM_{g}_{f}.json">原生逐截面日志</a></p><a href="images/{name}"><img loading="lazy" src="images/{name}"></a></article>')
   if key in SENTINELS:
    tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];p=np.array(tips[0]);zoom=(p,np.array([1.,0]),np.array([0.,1.]),np.array([-90.,-65.]),np.array([90.,65.]));bz,mz,_=view(im,zoom,(870,620));zcard=Image.new('RGB',(1800,1500),'#111d2b');zd=ImageDraw.Draw(zcard);lines(zd,(20,10),f'{g}/{f} 尖端附近原图放大：实际轨迹是否接入',BIG)
    for j,tag in enumerate(ts):panel(zcard,(20+(j%2)*890,90+(j//2)*700),bz,mz,tag,failures[tag,g,f]['stage'],t=ts[tag],label=label,fail=failures[tag,g,f])
    zcard.save(OUT/'galleries/images'/f'sentinel_{g}_{f}.jpg',quality=95)
  if len(meta)%100==0:print('media',len(meta),flush=True)
 assert len(meta)==1565 and len(cards)==80;save(OUT/'galleries/render_manifest.csv',meta)
 style='<style>body{background:#111d2b;color:#e4edf4;font:18px system-ui;max-width:1800px;margin:auto;padding:24px}a{color:#55dabb}img{width:100%;height:auto}article{border-top:1px solid #567;margin-top:30px}select,button,input{font:inherit;padding:8px;margin:5px}</style>'
 page='<!doctype html><meta charset="utf-8"><title>R05G 完整80选帧图册</title>'+style+'<h1>R05G：80 选帧完整对照</h1><p>76 VISIBLE + 4 UNCERTAIN。逐步追踪已实现；主裂纹身份和可信尖端未通过。诊断起点成绩与自动成绩分别列出。</p><p><a href="all_frames.html">全部1565帧局部对比图</a> · <a href="../R05G_All_Development_Frames.mp4">完整序列视频</a> · <a href="../development_report.md">开发报告</a></p><p>'+''.join(f'<a href="images/sentinel_{g}_{f}.jpg">{g}/{f}放大</a> ' for g,f in SENTINELS)+'</p><label>试验组<select id="group"><option value="all">全部</option>'+''.join(f'<option>{g}</option>' for g in DEV)+'</select></label>'+''.join(cards)+"<script>group.onchange=()=>document.querySelectorAll('article').forEach(x=>x.hidden=group.value!=='all'&&x.dataset.group!==group.value)</script>";(OUT/'galleries/index.html').write_text(page,encoding='utf8')
 entries=[dict(g=r['dataset_id'],f=r['frame_id'],p=r['path'].removeprefix('galleries/')) for r in meta]
 page='<!doctype html><meta charset="utf-8"><title>1565帧裂纹局部对比</title>'+style+'<h1>完整开发序列逐帧对比</h1><p>全部1565张实际原图，未剔除失败帧；只有80张有离线标注，其他帧无GT精度。点击图像可查看原尺寸。</p><p><a href="index.html">80选帧详细图册</a> · <a href="../R05G_All_Development_Frames.mp4">视频</a></p><select id="group">'+''.join(f'<option>{g}</option>' for g in DEV)+'</select><button id="prev">上一帧</button><input id="slider" type="range" min="0" value="0"><button id="next">下一帧</button><span id="counter"></span><a id="link"><img id="frame"></a><script>const data='+json.dumps(entries)+';let filtered=[],i=0;function show(){i=Math.max(0,Math.min(i,filtered.length-1));let r=filtered[i];frame.src=r.p;link.href=r.p;counter.textContent=r.g+" / "+r.f+" ("+(i+1)+"/"+filtered.length+")";slider.value=i}function reset(){filtered=data.filter(x=>x.g===group.value);i=0;slider.max=filtered.length-1;show()}group.onchange=reset;prev.onclick=()=>{i--;show()};next.onclick=()=>{i++;show()};slider.oninput=()=>{i=+slider.value;show()};reset();</script>';(OUT/'galleries/all_frames.html').write_text(page,encoding='utf8')
 concat=OUT/'galleries/video_frames.txt';concat.write_text(''.join("file '"+str(OUT/r['path']).replace('\\','/')+"'\nduration 0.1\n" for r in meta)+"file '"+str(OUT/meta[-1]['path']).replace('\\','/')+"'\n",encoding='utf8')
 cmd=[str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-y','-hide_banner','-loglevel','warning','-f','concat','-safe','0','-i',str(concat),'-vf','fps=10','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'R05G_All_Development_Frames.mp4')]
 with (OUT/'logs/video_encode.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
 write(OUT/'media_complete.json',dict(all_frame_comparison_images=1565,selected_detailed_cards=80,sentinel_zoom_cards=9,video='R05G_All_Development_Frames.mp4',playback_fps=10,algorithm_fps_claim=False,source='actual native replay and original frames only',labels='80 selected offline only',transform_roundtrip='verified <1e-8 original pixels'))
 print('MEDIA COMPLETE',flush=True)
if __name__=='__main__':main()
