"""Render comparison-only evidence after frozen prediction scoring is complete."""
import subprocess
import html
from validate_annotations import *

SIZE=(1600,980)
FONT='C:/Windows/Fonts/msyh.ttc'
def font(n): return ImageFont.truetype(FONT,n)
def text(draw,xy,value,size=24,color='#e8edf5'):
 draw.text(xy,str(value),font=font(size),fill=color)

def slide(lines):
 im=Image.new('RGB',SIZE,'#101b2b');d=ImageDraw.Draw(im)
 for i,line in enumerate(lines):text(d,(65,70+i*85),line,36 if i==0 else 27)
 return im

def panel(r,p,label):
 require(r['dataset_id'],'comparison',uses_annotations=True)
 source=PACKAGE/r['selected_image'];assert sha(source)==r['source_sha256']
 with Image.open(source) as opened: original=opened.convert('RGB')
 pts=[xy for s in label['shapes'] for xy in s['points']]
 observed=p['observed']=='True'
 if observed:pts.append([float(p['predicted_x']),float(p['predicted_y'])])
 if not pts:pts=[[original.width/2,original.height/2]]
 pts=np.array(pts);lo=pts.min(axis=0);hi=pts.max(axis=0);center=(lo+hi)/2;span=np.maximum(hi-lo+160,400)
 box=(max(0,int(center[0]-span[0]/2)),max(0,int(center[1]-span[1]/2)),min(original.width,int(center[0]+span[0]/2)),min(original.height,int(center[1]+span[1]/2)))
 crop=original.crop(box);scale=min(740/crop.width,725/crop.height);size=tuple(max(1,round(v*scale)) for v in crop.size)
 raw=crop.resize(size,Image.Resampling.LANCZOS);marked=raw.copy();md=ImageDraw.Draw(marked)
 def xy(point):return ((point[0]-box[0])*scale,(point[1]-box[1])*scale)
 for s in label['shapes']:
  pp=[xy(v) for v in s['points']]
  if s['label'] in ['crack_path','branch_path']:md.line(pp,fill='#5dff70',width=3)
  elif s['label']=='uncertain_region':md.line(pp+[pp[0]],fill='#ffdc54',width=3)
  elif s['label']=='crack_tip':
   x,y=pp[0];md.ellipse((x-9,y-9,x+9,y+9),outline='#ff5263',width=4)
 if observed:
  x,y=xy([float(p['predicted_x']),float(p['predicted_y'])]);md.line((x-12,y,x+12,y),fill='#25e3ff',width=4);md.line((x,y-12,x,y+12),fill='#25e3ff',width=4)
 out=Image.new('RGB',SIZE,'#101b2b');d=ImageDraw.Draw(out)
 text(d,(30,18),f"{r['dataset_id']} / frame {r['frame_id']} / {role(r['dataset_id'])}",30)
 err=p['error_original_px'];error=f'{float(err):.2f} 原图像素' if err else 'N/A（不确定标签或无确认输出）'
 text(d,(30,66),'冻结生产 A 尖端误差：'+error,27)
 text(d,(30,108),'左：原图裁剪；右：绿色人工路径、红圈人工尖端、青色十字算法尖端',25)
 out.paste(raw,(30+(740-size[0])//2,158+(725-size[1])//2));out.paste(marked,(830+(740-size[0])//2,158+(725-size[1])//2))
 text(d,(30,896),f"人工状态 {p['annotation_state']} | 算法 {'有确认输出' if observed else '无确认输出'} | {p['terminal_reason']}",24)
 text(d,(30,939),'仅对比：无训练、无调参；排除组X排除；验证组C/三点弯只验证。播放速度不代表算法吞吐。',22)
 return out

def main():
 manifest=rows(OUT/'active_selection_manifest.csv');pred={(p['dataset_id'],p['frame_id']):p for p in rows(OUT/'production_tip_comparison.csv')}
 summary=[p for p in rows(OUT/'production_tip_group_summary.csv') if p['scope']=='dataset' and p['original_split']=='ALL']
 intro=slide(['R05 当前人工标注：冻结生产 A 对照验证','开发：GROUP_A、CT2、开发组H、CT3','仅验证：验证组C、三点弯；排除组X完全排除','120 张标注：111 张明确可见，9 张不确定','标注只作对比和 QC；没有模型训练、参数拟合','连续回放后独立评分；算法未更新','后续画面按原始清单顺序展示全部 120 张选帧','路径差分 E1/E2 的独立图册及覆盖分析见报告'])
 ending=['冻结生产 A：逐组结果（误差为原图像素）']
 for r in summary:
  ending.append(f"{r['name']}  有输出 {r['observed_scored']}/{r['human_visible']}  P50 {float(r['p50_error_px']):.2f}px  ≤5px {r['within5_count']}/{r['human_visible']}" if r['p50_error_px'] else f"{r['name']}  有输出 0/{r['human_visible']}  误差 N/A")
 ending+=['历史差分作为主要可见裂纹证据：不支持；正式开发门槛未通过','所有组已历史曝光，不称独立未见测试；未发布新算法']
 end=slide(ending);folder=OUT/'production_tip_panels';folder.mkdir(exist_ok=True)
 intro.save(OUT/'video_intro.jpg');end.save(OUT/'video_summary.jpg')
 video=OUT/'R05_Annotation_Validation.mp4';ffmpeg=ROOT/'third_party/ffmpeg/ffmpeg.exe';fps=5
 cmd=[str(ffmpeg),'-y','-hide_banner','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1600x980','-framerate',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(video)]
 cards=[];frame_count=0
 with (OUT/'video_encode.log').open('w') as log:
  process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
  try:
   def push(im,seconds):
    nonlocal frame_count
    raw=im.tobytes()
    for _ in range(seconds*fps):process.stdin.write(raw);frame_count+=1
   push(intro,6)
   with zipfile.ZipFile(OUT/'human_annotations_six_groups_snapshot.zip') as archive:
    for r in manifest:
     p=pred[r['dataset_id'],r['frame_id']];im=panel(r,p,json.loads(archive.read(r['selected_json'])));name=f"{r['dataset_id']}__frame_{int(r['frame_id']):06d}.jpg";im.save(folder/name,quality=92);push(im,2)
     cards.append(f'<section><img loading="lazy" src="production_tip_panels/{html.escape(name)}"></section>')
   push(end,10)
  finally:process.stdin.close()
  assert process.wait()==0
 qa=subprocess.run([str(ffmpeg),'-v','error','-i',str(video),'-f','null','NUL'],capture_output=True,text=True)
 assert qa.returncode==0 and not qa.stderr,qa.stderr
 probe=json.loads(subprocess.check_output([str(ffmpeg.with_name('ffprobe.exe')),'-v','error','-show_entries','stream=codec_name,width,height,nb_frames:format=duration','-of','json',str(video)],text=True))
 assert int(probe['streams'][0]['nb_frames'])==frame_count
 write(OUT/'video_qa.json',dict(full_decode='PASS',frames=frame_count,cases=len(manifest),seconds=frame_count/fps,probe=probe,sha256=sha(video)))
 (OUT/'Production_A_Tip_Comparison.html').write_text('<!doctype html><meta charset="utf-8"><title>冻结生产A尖端对照</title><style>body{background:#101b2b;color:white;font:18px system-ui}img{width:100%;max-width:1600px}section{margin:20px}</style><h1>全部120选帧：人工标签与冻结生产A</h1><p>红圈人工尖端，青色十字算法确认尖端；不确定标签不评分。标签仅对比，无训练或调参。</p>'+''.join(cards),encoding='utf8')
 print('VIDEO AND 120 BASELINE COMPARISON PANELS COMPLETE',flush=True)
if __name__=='__main__':main()
