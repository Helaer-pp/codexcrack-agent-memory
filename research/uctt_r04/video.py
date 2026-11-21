"""Render the requested result video from real originals and frozen run records."""
import json,csv,subprocess,math,html
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
from common import *
W,H,FPS=1600,900,15
BG=(14,21,34);FG=(234,241,250);MUTED=(166,181,203);RED=(255,105,105);GREEN=(100,231,156);YELLOW=(255,202,94);CYAN=(91,204,231)
FONT='C:/Windows/Fonts/msyh.ttc';BOLD='C:/Windows/Fonts/msyhbd.ttc'
def font(size,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)
def text(draw,xy,t,size=25,color=FG,bold=False):draw.text(xy,t,font=font(size,bold),fill=color)
def wrap(s,maxlen=47):
 out=[]
 for line in s.split('\n'):
  while len(line)>maxlen:out.append(line[:maxlen]);line=line[maxlen:]
  out.append(line)
 return out
NAMES={'ct2':'CT2','group_h':'开发组H','group_c':'验证组C','group_x':'排除组X（曝光历史）','ct3':'CT3','three_point_bend':'三点弯','group_a':'GROUP_A（确认不足）'}
REASON={'RAW_STRUCTURE_UNSUPPORTED':'原图截面证据不足','NO_ROOT_SUPPORTED_PREFIX':'缺少已支持的后向路径','PREFIX_STRUCTURE_UNSUPPORTED':'后向路径原图支持不足','DISCONNECTED_FROM_PREFIX':'与后向路径不连通','PREFIX_DIRECTION_CONFLICT':'连接方向冲突','UNSUPPORTED_GAP':'间隙缺少证据','PREFIX_CONNECTED_PROXY':'通过连接代理，非物理真值','ROI_EDGE':'端点靠近 ROI 边界','NO_CANDIDATE':'没有当前候选','INVALID_PATH':'候选坐标无效'}
def main():
 summary=json.loads((OUT/'result_summary.json').read_text());records={}
 with (OUT/'candidate_paths.jsonl').open(encoding='utf8') as f:
  for r in map(json.loads,f):
   if r['selected_for_review']:records[r['dataset_id'],r['variant_id'],r['frame_id']]=r
 faults=list(csv.DictReader((OUT/'lock_injection_results.csv').open(encoding='utf-8-sig')))
 perf=list(csv.DictReader((OUT/'performance_summary.csv').open(encoding='utf-8-sig')))
 coverage=list(csv.DictReader((OUT/'metric_summary.csv').open(encoding='utf-8-sig')))
 (OUT/'images').mkdir(exist_ok=True)
 ffmpeg=ROOT/'third_party/ffmpeg/ffmpeg.exe';err=(OUT/'video_encode.log').open('wb')
 proc=subprocess.Popen([str(ffmpeg),'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-threads','4','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'R04_results.mp4')],stdin=subprocess.PIPE,stderr=err)
 index=[];counter=0;gallery=[]
 def emit(im,count,meta):
  nonlocal counter
  payload=np.asarray(im,dtype=np.uint8).tobytes()
  for _ in range(count):proc.stdin.write(payload)
  index.append(dict(start_video_frame=counter,display_frames=count,start_seconds=counter/FPS,end_seconds=(counter+count)/FPS,**meta));counter+=count
 def card(title,lines,seconds=5,badge='R04 / 受控实验'):
  im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im);d.rounded_rectangle((65,65,430,115),12,fill=(34,49,68));text(d,(82,72),badge,24,CYAN)
  text(d,(70,160),title,48,FG,True);y=260
  for sentence in lines:
   for s in wrap(sentence,43):text(d,(80,y),s,29,MUTED);y+=52
   y+=14
  text(d,(80,825),'生产源码 / DLL 未替换 · 无动态 ROI 闭环 · 真实物理 GT 未提供',24,YELLOW)
  emit(im,seconds*FPS,dict(kind='result_card',title=title))
 card('本轮结果：PARTIAL，不建议替换生产算法',[
  '已完成原生旁路、路径归属对照、故障注入与真实图像回放。',
  f"{summary['N_cases']} 个初始化/帧案例：基线复现与旁路输出差异均为 0。",
  f"视觉确认：B0 {summary['N_base_observed']} → 截面 D1 {summary['N_D1_observed']} → 前缀连接 D2 {summary['N_D2_observed']}。",
  '覆盖明显下降；E2 因果交换、E3 新终止审计和 B5 优化未启用。',
  '以下包含成功、拒绝与失败；未确认帧不会被计成 0 像素误差。'],6)
 card('怎样看这份视频',[
  '红色：原算法当前路径与尖端；青色：独立主路径代理（非真值）。',
  '绿色：D2 实验确认；黄色叉：历史预测；灰色叉：无证据回退。',
  '预测与回退 valid=false，不更新确认历史，也不参与配对距离。',
  '同一原图使用共同裁剪区域。右栏为扰动初始化；无扰动时为方法对照。',
  '慢放 3 张原图/秒，关键帧停留；播放速度不是算法实时性能。'],6)
 # Explicitly separate synthetic construction from actual specimen images.
 for case in ['coherent_wrong_first_lock','weak_true_strong_artifact','connected_false_branch']:
  p=OUT/'synthetic'/f'{case}.png';im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
  text(d,(55,40),'构造注入 / 非真实试件准确率',38,YELLOW,True);text(d,(55,105),case,30)
  art=Image.open(p).convert('RGB').resize((960,640),Image.Resampling.NEAREST);im.paste(art,(40,190));d=ImageDraw.Draw(im)
  rr=[r for r in faults if r['case_id']==case]
  y=210
  for r in rr:
   label='真实构造路径' if r['label']=='construct_true' else '构造干扰路径'
   text(d,(1030,y),f"D{r['method']} / {label}",23,CYAN);y+=42
   text(d,(1030,y),'接受并写历史' if r['observed']=='1' else '拒绝，不写历史',26,GREEN if r['observed']=='1' and r['expected_observed']=='1' else RED if r['observed']!=r['expected_observed'] else MUTED);y+=62
  text(d,(55,850),'标签来自实际绘制；运行时不读取标签。相连伪影仍能误锁，并可压制真实路径。',22,YELLOW)
  fn=f'injection_{case}.png';im.save(OUT/'images'/fn);gallery.append((fn,'synthetic_injection',case));emit(im,6*FPS,dict(kind='synthetic_injection',case_id=case,image_sha256=sha(p)))
 # Fixed sequence order and windows were saved before results were observed.
 order=['ct2','group_h','group_c','ct3','three_point_bend','group_a','group_x']
 critical={'ct2':{8},'group_h':{5,78},'group_c':{38,69},'ct3':{20},'three_point_bend':{20},'group_a':{241},'group_x':{1}}
 for g in order:
  selected_frames=sorted(k[2] for k in records if k[:2]==(g,'measured'));variant=VARIANTS.get(g,'measured')
  cov=next(r for r in coverage if r['dataset_id']==g and r['variant_id']=='measured' and r['version']=='B2_D2_PREFIX' and r['subset']=='chronological_prefix')
  card(NAMES[g]+' / 预先选定的真实窗口',[
   f"控制窗口执行 {cov['N_total']} 帧：B0 确认 {cov['N_observed_base']}，D2 确认 {cov['N_observed_new']}。",
   '显示原图帧：'+', '.join(f'{a}–{b}' for a,b in WINDOWS[g])+'；检测器先按时间顺序处理此前所有帧。',
   '初始化对照：'+variant,
   '人工真实尖端标签：0。距离是输出差异，不是物理定位误差。'],4)
  boxes=[records[g,v,i]['roi'] for v in ['measured',variant] for i in selected_frames]
  sample=records[g,'measured',selected_frames[0]];iw=sample['image_w'];ih=sample['image_h']
  x0=max(0,min(b[0] for b in boxes)-40);y0=max(0,min(b[1] for b in boxes)-40);x1=min(iw,max(b[0]+b[2] for b in boxes)+40);y1=min(ih,max(b[1]+b[3] for b in boxes)+40)
  for i in selected_frames:
   left=records[g,'measured',i];right=records[g,variant,i];raw=api.read(left['input']['image_path']);frame=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(frame)
   text(d,(28,22),f'{NAMES[g]}  |  原图帧 {i}  |  原生检测结果对照',32,FG,True)
   text(d,(28,72),'GT 不可用；所有窗口预先选择；B2 只在旁路运行，生产输出未改动。',22,MUTED)
   for pane,(r,label) in enumerate([(left,'控制初始化 / B0 原始输出'),(right,('扰动初始化 '+variant if variant!='measured' else '相同初始化 / D2 实验输出'))]):
    px=20+pane*795;py=140;pw=765;ph=500
    crop=Image.fromarray(raw[y0:y1,x0:x1]).convert('RGB');scale=min(pw/crop.width,ph/crop.height);nw,nh=round(crop.width*scale),round(crop.height*scale);crop=crop.resize((nw,nh),Image.Resampling.LANCZOS);ox=px+(pw-nw)//2;oy=py+(ph-nh)//2;frame.paste(crop,(ox,oy));d=ImageDraw.Draw(frame)
    def pt(p):return (ox+(p[0]-x0)*scale,oy+(p[1]-y0)*scale)
    def path(p,color,width=2):
     if len(p)>1:d.line([pt(q) for q in p],fill=color,width=width)
    def mark(p,color,cross=False):
     x,y=pt(p)
     if cross:d.line((x-7,y-7,x+7,y+7),fill=color,width=3);d.line((x-7,y+7,x+7,y-7),fill=color,width=3)
     else:d.ellipse((x-6,y-6,x+6,y+6),outline=color,width=3)
    q=r['roi'];d.rectangle([pt(q[:2]),pt([q[0]+q[2]-1,q[1]+q[3]-1])],outline=(180,138,247),width=2)
    for b in r['sidecar']['branches']:path(b['path'],(152,152,160),1)
    path(r['sidecar']['prefix'],CYAN,2);path(r['raw']['observed_original_px'],RED,3)
    if r['raw']['tip_confirmed']:mark(r['raw']['measurement']['tip_original_xy'],RED)
    state=r['sidecar']['states'][1]
    if pane==1:
     if state['valid']:path(r['raw']['observed_original_px'],GREEN,3)
     mark(state['output'],GREEN if state['valid'] else YELLOW if state['source']=='predicted' else (170,170,170),not state['valid'])
    text(d,(px,111),label,21,CYAN)
    # Photo overview inset retains context of the original full image.
    overview=Image.fromarray(raw).convert('RGB');overview.thumbnail((155,100));frame.paste(overview,(px+pw-overview.width,py+ph-overview.height));d=ImageDraw.Draw(frame)
    text(d,(px,655),f"B0 当前确认：{'是' if r['raw']['tip_confirmed'] else '否'}    D2 当前确认：{'是' if state['valid'] else '否'}",23)
    text(d,(px,693),f"D2 来源 {state['source']} / valid={str(bool(state['valid'])).lower()}",23,GREEN if state['valid'] else YELLOW)
    reason=REASON.get(r['sidecar']['audit']['reason'],r['sidecar']['audit']['reason']);text(d,(px,731),reason,23,MUTED)
    a=r['sidecar']['audit'];text(d,(px,769),f"原图支持 {a['support']:.2f} / 前缀支持 {a['prefix_support']:.2f} / 重合 {a['overlap_fraction']:.2f}",20,MUTED)
   if variant=='measured':pair='同一初始化的方法对照：该窗口未做初始点扰动，不计算初始化配对距离'
   elif left['raw']['tip_confirmed'] and right['raw']['tip_confirmed']:
    delta=np.linalg.norm(np.array(left['raw']['measurement']['tip_original_xy'])-right['raw']['measurement']['tip_original_xy']);pair=f'B0 初始化配对差：{delta:.2f} px（非 GT 误差）'
   else:pair='共同视觉确认不足：不计算配对距离'
   text(d,(25,821),pair,25,YELLOW);text(d,(25,861),'原图 SHA256 '+left['image_sha256'],18,MUTED)
   hold=30 if i in critical.get(g,set()) else 5
   if i in critical.get(g,set()):
    fn=f'{g}_{i}.jpg';frame.save(OUT/'images'/fn,quality=93);gallery.append((fn,'real_original',f'{g} frame {i}; SHA256 {left["image_sha256"]}'))
   emit(frame,hold,dict(kind='real_original',dataset_id=g,frame_id=i,control_variant='measured',comparison_variant=variant,image_sha256=left['image_sha256'],image_path=left['input']['image_path'],initialization_only=True))
  print('video completed',g,flush=True)
 card('性能：真实原生 API 测量，50 ms 未达标',[
  '计时从内存图像进入 DLL 到返回，排除读图、压缩、绘图和本视频编码。',
  *[f"{NAMES[g]}：B0 P95 {float(next(r['P95'] for r in perf if r['kind']=='dataset' and r['name']==g and r['version']=='B0_R02_A0')):.2f} ms" for g in ['ct2','group_h','ct3']],
  '测试机 Ryzen 9 7950X；OpenCV 4.4；4 个原生线程。',
  'B1 还包含诊断拷贝与两种审计；不能将它当作已优化的部署版本。'],6)
 card('结论：不合入；失败证据完整保留',[
  '原 R03 平移干扰注入已被原图证据拦住，原候选仍被保留（非物理真值）。',
  'D2 构造正例保留 10/11，干扰误接纳 1/8；相连伪影仍未解决。',
  f"真实回放确认 {summary['N_base_observed']} → {summary['N_D2_observed']} / {summary['N_cases']}，覆盖下降 {abs(summary['D2_coverage_delta_pp']):.2f} 个百分点。",
  'E2 / E3 / B3–B5 因门槛失败未启用；没有宣称精度或解耦通过。',
  '下一步先补人工复核标签与可用的路径归属证据，再做因果交换。'],8)
 proc.stdin.close();rc=proc.wait();err.close();assert rc==0,(OUT/'video_encode.log').read_text(errors='replace')[-2000:]
 save('video_frame_index.csv',index)
 probe=subprocess.run([str(ROOT/'third_party/ffmpeg/ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(OUT/'R04_results.mp4')],capture_output=True,text=True);assert probe.returncode==0;write('video_probe.json',json.loads(probe.stdout))
 write('video_manifest.json',dict(path='R04_results.mp4',sha256=sha(OUT/'R04_results.mp4'),frames=counter,fps=FPS,duration_seconds=counter/FPS,resolution=[W,H],real_original_frames=sum(x['kind']=='real_original' for x in index),real_review_cases=len(records),slow_replay=True,contains_synthetic_sections=True,audio=False))
 gallery_html='<!doctype html><meta charset="utf-8"><title>R04 诊断视频与图集</title><style>body{background:#101827;color:#eaf0f8;font:18px sans-serif;max-width:1600px;margin:auto}img,video{max-width:100%}figure{margin:35px 0}</style><h1>R04：PARTIAL，生产算法未替换</h1><p>真实原图与构造注入分开标注。预测/回退无效，不能当作测量。E2/E3阻断。</p><video controls src="R04_results.mp4"></video>'
 for file,kind,caption in gallery:gallery_html+=f'<figure><img src="images/{file}"><figcaption>{html.escape(kind+" | "+caption)}</figcaption></figure>'
 (OUT/'failure_gallery.html').write_text(gallery_html,encoding='utf8')
 print('Video',counter,'frames',counter/FPS,'seconds',flush=True)
if __name__=='__main__':main()
