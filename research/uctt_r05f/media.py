"""Offline display of actual native traces. Label overlays never enter runtime."""
from common import *
import numpy as np,zipfile,html,subprocess
from PIL import Image,ImageDraw,ImageFont

FONT='C:/Windows/Fonts/msyh.ttc'
def text(draw,xy,s,size=21,color='#dce8f8'):draw.text(xy,str(s),font=ImageFont.truetype(FONT,size),fill=color)
def view(im,box,t,pp,label,a,size,windows=False,segments=False,candidates=False,gt=False):
 x0,y0,x1,y1=box;part=im.crop(box);scale=min(size[0]/part.width,size[1]/part.height)
 part=part.resize((max(1,round(part.width*scale)),max(1,round(part.height*scale))),Image.Resampling.LANCZOS);d=ImageDraw.Draw(part)
 def xy(p):return ((p[0]-x0)*scale,(p[1]-y0)*scale)
 def near(p,margin=5):return x0-margin<=p[0]<=x1+margin and y0-margin<=p[1]<=y1+margin
 if windows:
  for w in t['windows']:d.line([xy(p) for p in w['polygon']+[w['polygon'][0]]],fill='#407c95',width=1)
  # S1 has no stepwise origin-band seeding. Show only the actual anchor midpoint.
  ox,oy=xy(t['origin']);d.line((ox-5,oy,ox+5,oy),fill='#00d7ff',width=2);d.line((ox,oy-5,ox,oy+5),fill='#00d7ff',width=2)
 if segments:
  for seg in t['segments']:
   path=seg['points']
   if len(path)>1 and any(near(p) for p in [path[0],path[-1]]):d.line([xy(p) for p in path],fill='#ffe063',width=2)
 if candidates:
  for c in t['candidates']:
   if not near(c['xy']):continue
   x,y=xy(c['xy']);kept=c['id']==c['canonical_id'];radius=2 if kept else 1;d.ellipse((x-radius,y-radius,x+radius,y+radius),outline='#35f5b1' if kept else '#9c8f86',width=1)
 for index,p in enumerate(pp):
  x,y=xy(p);d.ellipse((x-4,y-4,x+4,y+4),outline='#00d7ff',width=2);text(d,(x+5,y),f'P{index+1}',13,'#00d7ff')
 if a.get('confirmed_tip') and a.get('tip'):
  x,y=xy(a['tip']);d.ellipse((x-6,y-6,x+6,y+6),outline='#ff582e',width=3)
 if gt:
  for s in label['shapes']:
   if s['label']=='crack_path':d.line([xy(p) for p in s['points']],fill='#fa55f2',width=2)
   if s['label']=='crack_tip':
    x,y=xy(s['points'][0]);d.line((x-8,y,x+8,y),fill='#fa55f2',width=3);d.line((x,y-8,x,y+8),fill='#fa55f2',width=3)
 canvas=Image.new('RGB',size,'#131f2d');canvas.paste(part,((size[0]-part.width)//2,(size[1]-part.height)//2));return canvas

def main():
 records={(r['dataset_id'],int(r['frame_id'])):r for r in rows(OUT/'experiments/B0_candidate_reachability.csv')}
 base={(r['dataset_id'],r['frame_id']):r['formal'] for r in map(json.loads,(OUT/'A0_frames.jsonl').read_text().splitlines())}
 cards=[];manifest=[];movie=[];selected=filter_rows(rows(OUT/'selected_frames.csv'),'development')
 with zipfile.ZipFile(R05/'human_annotations_six_groups_snapshot.zip') as z:
  for index,s in enumerate(selected):
   g=s['dataset_id'];f=int(s['frame_id']);require(g,'comparison',uses_annotations=True);key=f'{g}_{f}';t=read(OUT/'traces'/f'B0_{key}.json');metric=records[g,f];label=json.loads(z.read(s['selected_json']));pp=json.loads(s['points']);a=base[g,f]
   path=PRE/'R05_LabelMe_Annotation_Package'/s['selected_image'];assert sha(path)==s['source_sha256'];im=Image.open(path).convert('RGB')
   im.save(OUT/'galleries/images'/f'{key}_raw.jpg',quality=93)
   out=Image.new('RGB',(1800,1080),'#0b1423');d=ImageDraw.Draw(out)
   text(d,(25,15),f'R05F / S1 当前暗线审计    {g} / {f}    DEVELOPMENT / {s["split"]}',28)
   text(d,(25,61),f'原始候选 {metric["raw_count"]} → 几何去重 {metric["dedup_count"]} | 近人工尖端 {metric["dedup_nearest_px"] or "N/A"} px',21)
   text(d,(25,99),'黄：实际暗线片段  绿：未确认候选  灰：去重别名  紫：人工对比  橙圈：冻结研究 A  青：P1/P2',20)
   full=(0,0,im.width,im.height)
   text(d,(25,140),'原图 / 冻结研究 A 与人工对比（不叠加研究片段）',18);out.paste(view(im,full,t,pp,label,a,(850,345),gt=True),(25,170))
   polygons=[p for w in t['windows'] for p in w['polygon']];arr=np.array(polygons) if polygons else np.array([[0,0],[im.width,im.height]])
   lo=np.maximum(0,np.floor(arr.min(axis=0)-10));hi=np.minimum([im.width,im.height],np.ceil(arr.max(axis=0)+10));box=tuple(map(int,[*lo,*hi]))
   text(d,(920,140),'全部实际访问窗口 / 暗线片段 / 未确认端点',18);out.paste(view(im,box,t,pp,label,a,(850,345),windows=True,segments=True,candidates=True,gt=True),(920,170))
   tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];center=np.array(tips[0] if tips else t['origin']);lo=np.maximum(0,np.floor(center-[125,90]));hi=np.minimum([im.width,im.height],np.ceil(center+[126,91]));zoom=tuple(map(int,[*lo,*hi]))
   text(d,(25,535),'人工尖端附近原图（仅离线展示裁图）',18);out.paste(view(im,zoom,t,pp,label,a,(850,330),gt=True),(25,565))
   text(d,(920,535),'同一区域：实际片段、候选和窗口边界',18);out.paste(view(im,zoom,t,pp,label,a,(850,330),windows=True,segments=True,candidates=True,gt=True),(920,565))
   text(d,(25,915),f'研究输出：fallback / tip=null；observed=false；可信历史写入=false。{t["reason"]}',22)
   text(d,(25,951),f'窗口 {len(t["windows"])}；访问像素累计 {t["window_pixels_sum"]} / 并集 {t["unique_source_pixels"]}；原生 {t["api_ms"]:.2f}ms',20)
   text(d,(25,985),'起源带步进/跨隙/可信前沿/两侧材料匹配：尚未实现，不绘制虚构结果。当前候选不等于主裂纹。',20)
   text(d,(25,1020),'本视频为选帧审计展示；播放速度与原生性能无关。验证组C/三点弯未进行本轮图像/标签验证；排除组X排除。',19)
   dest=OUT/'galleries/images'/f'{key}.jpg';out.save(dest,quality=91);movie.append(dest)
   failure='uncertain' if metric['visibility']=='UNCERTAIN' else 'near_candidate' if metric['dedup_hit10']=='True' else 'missing_candidate'
   cards.append(f'<article data-group="{g}" data-kind="{failure}"><h2>{g} / {f} — {failure}</h2><a href="images/{key}_raw.jpg">未叠加的原图展示副本</a><a href="../traces/B0_{key}.json">原生完整轨迹 JSON</a><img loading="lazy" src="images/{key}.jpg" alt="{g} {f} 实际候选与人工对比"></article>')
   manifest.append(dict(dataset_id=g,frame_id=f,source_sha256=s['source_sha256'],panel=str(dest.relative_to(OUT)),raw=f'galleries/images/{key}_raw.jpg',classification=failure,windows=len(t['windows']),segments=len(t['segments']),candidates=len(t['candidates'])))
   if index%10==0:print('gallery',index+1,'/',len(selected),flush=True)
 save(OUT/'galleries/media_manifest.csv',manifest)
 page='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>R05F S1 原生暗线候选审计</title><style>body{background:#101a28;color:#e4edf7;font:17px system-ui;max-width:1800px;margin:auto;padding:24px}img{width:100%}a{color:#6edfcc;margin-right:20px}article{border-top:1px solid #527;padding:12px 0}select{padding:8px;margin:8px}</style><h1>R05F S1：开发组全部 80 张选帧</h1><p>76 VISIBLE / 4 UNCERTAIN。黄色算法暗线与紫色人工路径严格分开。候选为 shadow，不能当作确认尖端。本页面包含真实本地图片资源。验证组40张选帧因阶段门未完成而未读图、未计分；不是漏选的开发样本。</p><p><a href="../development_report.md">开发报告</a><a href="../R05F_S1_Results.mp4">结果视频</a></p><label>组<select id="group"><option value="all">全部</option><option>group_a</option><option>ct2</option><option>group_h</option><option>ct3</option></select></label><label>类型<select id="kind"><option value="all">全部</option><option>near_candidate</option><option>missing_candidate</option><option>uncertain</option></select></label>'''+''.join(cards)+'''<script>function filter(){document.querySelectorAll('article').forEach(a=>a.hidden=!((group.value==='all'||a.dataset.group===group.value)&&(kind.value==='all'||a.dataset.kind===kind.value)))}group.onchange=kind.onchange=filter;</script></html>'''
 (OUT/'galleries/index.html').write_text(page,encoding='utf8')
 summary=Image.new('RGB',(1800,1080),'#0b1423');d=ImageDraw.Draw(summary)
 text(d,(65,65),'R05F 本轮最终状态：指定基线 S0 PASS / S1 FAIL',44,'#ffb777')
 for y,s in [(200,'R02/R05D研究基线 A 与源码克隆：1565 帧等价。'),(275,'历史发布件是不同版本；403/1565帧正式输出不同，不能混用指标。'),(350,'R01/R02已明确此历史边界；本轮未覆盖任何发布文件。'),(470,'S1 候选10px命中70/76；开发组H78弱短脊线被至少4列门槛过滤。'),(545,'容量增大8倍仍未恢复遗漏，不能以放大候选池或全拒绝声称成功。'),(660,'S1 P50 85.53ms / P95 105.03ms；1429/1565帧超过50ms。'),(765,'S2–S6 BLOCKED：步进、参考、归属、终止与锁后验证未完成。'),(860,'验证组C/三点弯不用于开发；排除组X排除；标签仅离线对比、从不训练。')]:text(d,(65,y),s,32)
 summary_path=OUT/'galleries/images/final_status.jpg';summary.save(summary_path,quality=94)
 audit=Image.open(OUT/'galleries/images/group_h78_response_segment_failure.jpg').convert('RGB');audit.thumbnail((1700,900));audit_card=Image.new('RGB',(1800,1080),'#0b1423');audit_card.paste(audit,((1800-audit.width)//2,(1080-audit.height)//2));audit_path=OUT/'galleries/images/failure_video_card.jpg';audit_card.save(audit_path,quality=94)
 concat=OUT/'galleries/video_concat.txt';concat.write_text(''.join(f"file '{p.as_posix()}'\nduration 2\n" for p in movie)+f"file '{audit_path.as_posix()}'\nduration 4\nfile '{summary_path.as_posix()}'\nduration 8\nfile '{summary_path.as_posix()}'\n",encoding='utf8')
 with (OUT/'logs/ffmpeg.log').open('w',encoding='utf8') as log:
  subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-y','-f','concat','-safe','0','-i',str(concat),'-vf','fps=24,scale=1600:960','-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'R05F_S1_Results.mp4')],stdout=log,stderr=log,check=True)
 write(OUT/'galleries/media_complete.json',dict(panels=len(movie),raw_copies=len(movie),summary_cards=2,video='R05F_S1_Results.mp4',no_validation_images_opened=True,gt_for_display_only=True))
 print('MEDIA COMPLETE',len(movie),flush=True)
if __name__=='__main__':main()
