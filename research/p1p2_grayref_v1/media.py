"""Offline original-image/evidence cards and per-group videos. Never feeds GT to inference."""
from common import *
from evaluate import dense,observed,SENTINELS
import argparse,zipfile,html,subprocess,time
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20);SMALL=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16);BIG=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',29)
NAMES={'group_a':'开发组A','ct2':'CT2','group_h':'开发组H','ct3':'CT3','group_c':'验证组C','three_point_bend':'三点弯'}
def text(d,at,s,font=FONT,fill='#e7edf5'):
 for line in s.split('\n'):d.text(at,line,font=font,fill=fill);at=(at[0],at[1]+font.size+7)
def xy(p,M):return tuple((M@np.array([*p,1])).tolist())
def view(im,bounds,size=(870,300),offset=(0,0)):
 x0,y0,x1,y1=bounds;scale=min((size[0]-10)/(x1-x0),(size[1]-10)/(y1-y0));M=np.array([[scale,0,(size[0]-scale*(x1-x0))/2-scale*x0],[0,scale,(size[1]-scale*(y1-y0))/2-scale*y0]]);local=M.copy();local[:,2]+=local[:,:2]@np.array(offset);arr=cv2.warpAffine(im,local,size,flags=cv2.INTER_LINEAR,borderValue=(40,40,40));return Image.fromarray(arr).convert('RGB'),M
def overlay(base,M,meta=None,trace=None,current=None,label=None,ref=False,old=None):
 image=base.copy();d=ImageDraw.Draw(image)
 if meta:
  for p in meta['reference_points' if ref else 'current_points']:
   x,y=xy(p,M);d.line([(x-5,y),(x+5,y)],fill='#ffa74b',width=3);d.line([(x,y-5),(x,y+5)],fill='#ffa74b',width=3)
  if not ref:
   r=meta['ROI'];d.rectangle([xy([r['x_left'],r['y_top']],M),xy([r['x_right'],r['y_bottom']],M)],outline='#48cfff',width=1)
 for rr,color in [(trace,'#32f3ac'),(current,'#ffb54d')]:
  if rr:
   for i,(a,b) in enumerate(zip(rr[:-1],rr[1:])):
    solid=a['is_observed']=='True' and b['is_observed']=='True'
    if solid or i%3==0:d.line([xy([float(a['x']),float(a['selected_y'])],M),xy([float(b['x']),float(b['selected_y'])],M)],fill=color if solid else '#fb7047',width=2 if solid else 1)
   obs=observed(rr)
   if len(obs):
    x,y=xy(obs[-1],M);d.ellipse([x-5,y-5,x+5,y+5],outline=color,width=3)
 if label:
  for s in label['shapes']:
   if s['label']=='crack_path' and len(s['points'])>=2:d.line([xy(p,M) for p in s['points']],fill='#f13ed4',width=1)
   elif s['label']=='crack_tip':
    x,y=xy(s['points'][0],M);d.line([(x-8,y),(x+8,y)],fill='#f13ed4',width=3);d.line([(x,y-8),(x,y+8)],fill='#f13ed4',width=3)
 if old:
  x,y=xy(old,M);d.rectangle([x-6,y-6,x+6,y+6],outline='#79aaff',width=2)
 return image
def heat(array,low,high):
 x=np.clip((array-low)/(high-low)*255,0,255).astype(np.uint8);return cv2.cvtColor(cv2.applyColorMap(x,cv2.COLORMAP_TURBO),cv2.COLOR_BGR2RGB)
def group(g):
 suffix='dev' if g in DEV else 'validation';assert (OUT/f'evaluation_{suffix}_complete.json').exists();require(g,'comparison',uses_annotations=True);start=time.perf_counter();folder=OUT/'galleries';(folder/'images'/g).mkdir(parents=True,exist_ok=True);(folder/'video_frames'/g).mkdir(parents=True,exist_ok=True);(OUT/'videos').mkdir(exist_ok=True)
 selection=[r for r in rows(F/'selected_frames.csv') if r['dataset_id']==g];ev={(int(r['frame_id']),r['mode'],int(r['threshold'])):r for r in rows(OUT/'tables'/f'all_results_{suffix}.csv') if r['group']==g};old={int(r['frame_id']):json.loads(r['tip']) if r['tip'] else None for r in rows(OUT/'tables'/f'A55_comparison_rows_{suffix}.csv') if r['group']==g};labs={};access=[];cards=[]
 with zipfile.ZipFile(LABELS) as z:
  for row in selection:
   f=int(row['frame_id']);raw=z.read(row['selected_json']);labs[f]=json.loads(raw);access.append(dict(group=g,frame_id=f,member=row['selected_json'],sha256=hashlib.sha256(raw).hexdigest(),use='offline_visualization'))
 for row in selection:
  f=int(row['frame_id']);run=OUT/'py_runs'/g/str(f);label=labs[f];meta=read(run/'metadata.json');metric=read(run/'adapter_metrics.json');e=ev[f,'joint',10];cur=cv2.imdecode(np.frombuffer(Path(row['source_image']).read_bytes(),np.uint8),0);reference=cv2.imdecode(np.frombuffer(Path(row['reference_image']).read_bytes(),np.uint8),0);joint=rows(run/'trace_joint_T10p0.csv');current=rows(run/'trace_current_T10p0.csv');roi=meta['ROI'];points=[p for s in label['shapes'] for p in s['points']];last=[r for r in joint if r['is_observed']=='True'];xmax=max([roi['x_left']+420]+[p[0] for p in points]+[float(r['x']) for r in last]);bounds=[max(0,roi['x_left']-45),max(0,min([roi['y_top']]+[p[1] for p in points])-25),min(cur.shape[1],xmax+60),min(cur.shape[0],max([roi['y_bottom']]+[p[1] for p in points])+25)]
  with np.load(run/'evidence_arrays.npz') as z:arrays={k:z[k] for k in z.files}
  xa,ya,_,_=arrays['crop_xyxy'];canvas=Image.new('RGB',(1800,1250),'#111d2b');d=ImageDraw.Draw(canvas);text(d,(20,10),f'P1/P2 GrayRef V1 | {NAMES[g]} / {f} | {"开发" if g in DEV else "冻结验证"}',BIG);text(d,(20,52),f"joint T10 误差={e['error'] or 'N/A'} px | {e['stage'] or e['visibility']} | ROI含GT={e['roi_contains_gt'] or 'N/A'}",SMALL)
  panels=[('参考原图（参考坐标；不是材料配准）',reference,(0,0),'ref'),('当前原图 + 严格ROI + 两分支 T10',cur,(0,0),'cur'),('当前暗谷 valley：统一显示0–40',heat(arrays['valley'],0,40),(xa,ya),'field'),('新增变暗 newdark：统一显示−20–40',heat(arrays['newdark'],-20,40),(xa,ya),'field'),('有效材料mask（灰度>135且位于冻结ROI）',(arrays['valid_material']*255).astype(np.uint8),(xa,ya),'field')]
  tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];center=tips[0] if tips else [roi['x_left']+120,(roi['y_top']+roi['y_bottom'])/2];zoom=[center[0]-100,center[1]-40,center[0]+100,center[1]+40]
  panels.append(('当前尖端放大（有GT时仅用于离线裁切）',cur,(0,0),'zoom'))
  for i,(title,im,offset,kind) in enumerate(panels):
   x=20+(i%2)*890;y=100+(i//2)*365;text(d,(x,y),title,FONT);base,M=view(im,zoom if kind=='zoom' else bounds,offset=offset);base=overlay(base,M,meta,trace=None if kind=='ref' else joint,current=current if kind in ['cur','zoom'] else None,label=None if kind=='ref' else label,ref=kind=='ref',old=old.get(f) if kind in ['cur','zoom'] else None);canvas.paste(base,(x,y+34))
  text(d,(20,1200),'青绿=joint暂定像素；橙=仅当前分支；虚线=缺失；紫=人工对照；蓝方框=A55a0；不把暂定结果称为正式确认。',SMALL);path=folder/'images'/g/f'{f:06d}.jpg';canvas.save(path,quality=93);cards.append(dict(group=g,frame_id=f,path=str(path.relative_to(OUT)).replace('\\','/'),stage=e['stage'] or e['visibility'],error=e['error']))
  if (g,f) in SENTINELS:
   zoomcard=Image.new('RGB',(1800,780),'#111d2b');zd=ImageDraw.Draw(zoomcard);text(zd,(20,12),f'{NAMES[g]}/{f} 哨兵原图与灰度证据（离线GT附近）',BIG)
   for i,(title,im,offset) in enumerate([('当前原图',cur,(0,0)),('valley 0–40',heat(arrays['valley'],0,40),(xa,ya)),('newdark −20–40',heat(arrays['newdark'],-20,40),(xa,ya)),('材料 mask',(arrays['valid_material']*255).astype(np.uint8),(xa,ya))]):
    x=20+(i%2)*890;y=70+(i//2)*350;text(zd,(x,y),title);base,M=view(im,zoom,size=(870,290),offset=offset);zoomcard.paste(overlay(base,M,trace=joint,current=current,label=label),(x,y+32))
   zoomcard.save(folder/'images'/g/f'sentinel_{f}.jpg',quality=95)
  print('card',g,f,flush=True)
 sheet=Image.new('RGB',(1800,1720),'#111d2b');sd=ImageDraw.Draw(sheet);text(sd,(20,10),f'{NAMES[g]} · 全部20个既有选帧（点开HTML可查看原尺寸）',BIG)
 for i,c in enumerate(cards):
  x=(i%4)*450;y=60+(i//4)*330;thumb=Image.open(OUT/c['path']);thumb.thumbnail((445,305));sheet.paste(thumb,(x,y));text(sd,(x+6,y+306),f"帧{c['frame_id']} | {c['error'][:9] or 'UNCERTAIN'}",SMALL)
 sheet.save(folder/f'contact_{g}.jpg',quality=92);save(folder/f'cards_{g}.csv',cards);save(folder/f'annotation_access_{g}.csv',access)
 sequence=[r for r in rows(OUT/'inputs'/('manifest.csv' if g in DEV else 'validation_manifest.csv')) if r['group']==g];paths=[]
 summary=next(r for r in rows(OUT/'tables'/f'group_summary_{suffix}.csv') if r['group']==g and r['mode']=='joint' and r['threshold']=='10');intro=Image.new('RGB',(1280,600),'#111d2b');dd=ImageDraw.Draw(intro);text(dd,(45,50),f'P1/P2 GrayRef V1 · {NAMES[g]}',BIG);text(dd,(45,125),f"{'开发组' if g in DEV else '冻结后验证组'} | 全序列 {len(sequence)} 帧\n固定 joint T10：≤10px {summary['hit10']}/{summary['visible']} 可见标注\n暂定输出覆盖 {summary['provisional_coverage']}/{summary['visible']}；>100/500px {summary['over100']}/{summary['over500']}\n\n原冻结Python逐帧预览；未剔除失败帧。\n绿线为原脚本连接所选像素的预览，跨间隙连线不是观察证据。\n所有端点均为暂定候选，不是生产确认。\n本视频播放8帧/秒，不代表算法性能。\n标注仅离线比较；排除组X排除；验证结果不用于修改规则。",FONT);intro_path=folder/'video_frames'/g/'intro.jpg';intro.save(intro_path,quality=92)
 for row in sequence:
  f=int(row['frame_id']);source=OUT/'py_runs'/g/str(f)/'result_overlay.png';canvas=Image.new('RGB',(1280,600),'#111d2b');dd=ImageDraw.Draw(canvas);text(dd,(15,10),f"V1 | {NAMES[g]} / {f} | 固定 joint T10 · 暂定端点",BIG)
  if source.exists():preview=Image.open(source).convert('RGB');preview.thumbnail((1260,475));canvas.paste(preview,((1280-preview.width)//2,58))
  else:text(dd,(30,200),'本帧执行失败；保留空输出，详见日志',BIG)
  error=ev[f,'joint',10]['error'];text(dd,(15,548),f"离线误差={error[:13]+' px' if error else 'N/A（无可比较端点或无可见GT）'}；绿色预览跨缺失连线不是可见裂纹。",SMALL);path=folder/'video_frames'/g/f'{f:06d}.jpg';canvas.save(path,quality=89);paths.append(path)
 concat=OUT/'videos'/f'{g}_frames.txt';concat.write_text("file '"+str(intro_path).replace('\\','/')+"'\nduration 4\n"+''.join("file '"+str(p).replace('\\','/')+"'\nduration 0.125\n" for p in paths)+"file '"+str(paths[-1]).replace('\\','/')+"'\n",encoding='utf8');video=OUT/'videos'/f'V1_{g}.mp4';duration=4+len(paths)/8
 cmd=[str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-t',str(duration),'-vf','fps=8','-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(video)];subprocess.run(cmd,check=True)
 probe=json.loads(subprocess.check_output([str(ROOT/'third_party/ffmpeg/ffprobe.exe'),'-v','error','-show_streams','-of','json',str(video)]));count=int(probe['streams'][0]['nb_frames']);assert count==len(paths)+32;subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-v','error','-i',str(video),'-f','null','-'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 write(OUT/f'media_complete_{g}.json',dict(group=g,cards=len(cards),frames=len(paths),video=str(video.relative_to(OUT)).replace('\\','/'),encoded_frames=count,duration=duration,video_sha256=sha(video),full_decode_pass=True,render_and_encode_ms=(time.perf_counter()-start)*1000));print('MEDIA COMPLETE',g,flush=True)
def index():
 parts=[];videos=[]
 for g in VAL+DEV:
  info=read(OUT/f'media_complete_{g}.json');assert read(OUT/f'frame_comparisons_complete_{g}.json')['frames']==info['frames'];videos.append(info);parts.extend(rows(OUT/'galleries'/f'cards_{g}.csv'))
 style='<style>body{background:#111d2b;color:#e7edf5;font:18px system-ui;margin:30px}a{color:#79e7d2}img,video{width:min(100%,1800px)}article{margin:30px 0}</style>'
 page='<!doctype html><meta charset="utf-8"><title>V1跨试件冻结验证</title>'+style+'<h1>P1/P2 GrayRef V1 冻结跨试件证据</h1><p>全部结果为暂定候选。阈值未改，未按试件选择参数。验证组优先。</p><p><a href="../development_report.md">完整报告</a> · <a href="all_frames.html">全部2647帧局部对比浏览器</a></p>'
 for v in videos:
  g=v['group'];page+=f'<h2>{NAMES[g]} | {"验证" if g in VAL else "开发"}</h2><video controls preload="metadata" src="../{v["video"]}"></video><p>{v["frames"]}帧完整视频 · <a href="contact_{g}.jpg">20帧联系图</a></p>'
  for r in [p for p in parts if p['group']==g]:page+=f'<article><h3>帧{r["frame_id"]} | {html.escape(r["stage"])} | {r["error"] or "N/A"}px</h3><a href="../{r["path"]}"><img loading="lazy" src="../{r["path"]}"></a></article>'
 (OUT/'galleries/index.html').write_text(page,encoding='utf8')
 options=''.join(f'<option value="{v["group"]}">{NAMES[v["group"]]} / {v["frames"]}帧</option>' for v in videos)
 data=json.dumps({v['group']:dict(count=v['frames'],name=NAMES[v['group']],cards=[int(r['frame_id']) for r in parts if r['group']==v['group']]) for v in videos},ensure_ascii=False)
 browser='<!doctype html><meta charset="utf-8"><title>全部2647帧局部对比</title>'+style+'<h1>全部2647帧 · 冻结V1参考/当前局部对比</h1><p><a href="index.html">视频和选帧详细证据</a>。每帧均保留；原图裁切由冻结V1决定。绿色跨缺失连线不等于观测，所有端点是暂定候选。</p><select id="group">'+options+'</select> <button id="prev">上一帧</button> <input id="frame" type="number" min="1" value="1" style="width:100px"> <button id="next">下一帧</button><p id="description"></p><p><a id="full" target="_blank">打开原始尺寸PNG</a> · <a id="card" target="_blank">本帧人工标注详细对比卡</a></p><img id="preview"><script>const data='+data+''';const group=document.getElementById('group'),frame=document.getElementById('frame');function show(){const g=group.value,v=data[g],f=Math.max(1,Math.min(v.count,Number(frame.value)||1));frame.value=f;frame.max=v.count;document.getElementById('description').textContent=v.name+' / '+f+' / '+v.count+'；左右箭头切换。未标注帧不计算准确率。';document.getElementById('preview').src='comparison_frames/'+g+'/'+String(f).padStart(6,'0')+'.jpg';document.getElementById('full').href='../py_runs/'+g+'/'+f+'/result_overlay.png';const c=document.getElementById('card');c.hidden=!v.cards.includes(f);c.href='images/'+g+'/'+String(f).padStart(6,'0')+'.jpg';}group.onchange=()=>{frame.value=1;show()};frame.onchange=show;document.getElementById('prev').onclick=()=>{frame.value=Number(frame.value)-1;show()};document.getElementById('next').onclick=()=>{frame.value=Number(frame.value)+1;show()};document.onkeydown=e=>{if(e.target.tagName==='INPUT')return;if(e.key==='ArrowRight')document.getElementById('next').click();if(e.key==='ArrowLeft')document.getElementById('prev').click()};show();</script>'''
 (OUT/'galleries/all_frames.html').write_text(browser,encoding='utf8');write(OUT/'media_complete.json',dict(videos=videos,cards=len(parts),frames=sum(v['frames'] for v in videos)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--group',choices=DEV+VAL);p.add_argument('--index',action='store_true');a=p.parse_args();index() if a.index else group(a.group)
