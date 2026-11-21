from v2common import *
from frozen_adapter import decode
from PIL import Image,ImageDraw,ImageFont
import numpy as np,subprocess,html,concurrent.futures,argparse
FONT='C:/Windows/Fonts/msyh.ttc'
COLORS={'V1_LOCKED':'#22dd73','V2_NUMERIC_CONTROL':'#ffc04d','V2_ORIGIN_ONLY':'#26d6ff','V2_REF_ONLY':'#ec77ff','V2_COMBINED':'#40f18b','V2_TERMINAL':'#ff594f'}
def panel(canvas,rect,image,bounds,title,result=None,label=None):
 x,y,w,h=rect;draw=ImageDraw.Draw(canvas);font=ImageFont.truetype(FONT,18);small=ImageFont.truetype(FONT,14);draw.text((x+8,y+3),title,font=font,fill='white');x0,y0,x1,y1=bounds;im=Image.fromarray(image[y0:y1,x0:x1]).convert('RGB');scale=min((w-16)/im.width,(h-65)/im.height);im=im.resize((max(1,int(im.width*scale)),max(1,int(im.height*scale))));ox=x+(w-im.width)//2;oy=y+33+(h-65-im.height)//2;canvas.paste(im,(ox,oy));draw=ImageDraw.Draw(canvas)
 def pos(p):return (ox+(p[0]-x0+.5)*scale,oy+(p[1]-y0+.5)*scale)
 if result:
  g=result.get('roi')
  if g:
   for yy in [g['upper'],g['lower']]:draw.line([pos((x0,yy)),pos((x1,yy))],fill='#009ab5',width=1)
  trace=result['trace'];color=COLORS[result['mode']]
  for i,r in enumerate(trace):
   p=pos(r[:2]);visible=r[2]
   if visible:
    if i and trace[i-1][2] and r[0]==trace[i-1][0]+1:draw.line([pos(trace[i-1][:2]),p],fill=color,width=2)
    else:draw.ellipse((p[0]-1,p[1]-1,p[0]+1,p[1]+1),fill=color)
   else:
    q=pos((r[0],r[4]/1024));draw.point(q,fill='#ff9d41')
  for s in result.get('seeds',[]):
   if s.get('reason') in ['PATH_HYPOTHESIS','SINGLE_COLUMN']:
    p=pos((s['x'],s['y']));draw.rectangle((p[0]-3,p[1]-3,p[0]+3,p[1]+3),outline='#00aaff',width=1)
  tip=result['tip']
  if tip:
   p=pos(tip);draw.line((p[0]-5,p[1]-5,p[0]+5,p[1]+5),fill='red',width=2);draw.line((p[0]-5,p[1]+5,p[0]+5,p[1]-5),fill='red',width=2)
  draw.text((x+8,y+h-28),f"{result['output_state']}  tip={tip}  {result.get('stop_reason','')}",font=small,fill='#f5d08c')
 if label:
  for s in label['shapes']:
   if s['label']=='crack_path' and len(s['points'])>1:draw.line([pos(p) for p in s['points']],fill='#e800ff',width=1)
   elif s['label']=='crack_tip':
    p=pos(s['points'][0]);draw.line((p[0]-6,p[1],p[0]+6,p[1]),fill='#e800ff',width=2);draw.line((p[0],p[1]-6,p[0],p[1]+6),fill='#e800ff',width=2)
def card(data,R,C,title,label=None,bounds=None):
 g=data['roi'];results=[data['baseline']]+data['results'];tips=[r.get('candidate_tip') for r in results if r.get('candidate_tip')];gt=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'] if label else []
 if bounds is None:bounds=[max(0,g['xleft']-45),max(0,g['upper']-24),min(C.shape[1],max(g['xleft']+420,*[p[0]+60 for p in tips+gt])),min(C.shape[0],g['lower']+24)]
 bounds=list(map(int,bounds));canvas=Image.new('RGB',(1600,1320),'#142232');d=ImageDraw.Draw(canvas);d.text((18,8),title,font=ImageFont.truetype(FONT,24),fill='white');d.text((18,42),'全局统一规则 | 紫=推理后人工对照 | 橙点=缺失预测 | 框=起源假设 | 暂定端点不等于物理认证',font=ImageFont.truetype(FONT,18),fill='#c4d0dc')
 items=[('原始参考（未配准）',R,None),('原始当前',C,None)]+[(r['mode'],C,r) for r in results]
 for i,(name,im,r) in enumerate(items):panel(canvas,((i%2)*800,80+(i//2)*310,800,305),im,bounds,name,r,label if i else None)
 return canvas
def render_group(group):
 from evaluate_v2 import getlabels
 labels,_=getlabels([group]);folder=OUT/'galleries'/group;folder.mkdir(parents=True,exist_ok=True);ref=None;entries=[]
 for fid in range(1,COUNTS[group]+1):
  data=unpack(OUT/'frames'/group/str(fid)/'result.json.gz');R=ref if ref is not None else decode(data['input']['reference']);ref=R;C=decode(data['input']['current']);label=labels.get((group,fid));im=card(data,R,C,f'{group} / {fid}   单帧无历史 · V1与独立V2消融',label);p=folder/f'{fid:06}.jpg';im.save(p,quality=88)
  if label:
   tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip']
   if tips:
    x,y=tips[0];bounds=[max(0,int(x)-210),max(0,int(y)-100),min(C.shape[1],int(x)+110),min(C.shape[0],int(y)+100)];card(data,R,C,f'{group}/{fid} 仅显示阶段按GT局部放大，不进入推理',label,bounds).save(folder/f'{fid:06}_detail.jpg',quality=92)
  entries.append(f'<figure><a href="{group}/{fid:06}.jpg"><img loading="lazy" src="{group}/{fid:06}.jpg"></a><figcaption>{group}/{fid} · <a href="../frames/{group}/{fid}/result.json.gz">完整候选与轨迹</a></figcaption></figure>')
  if fid%100==0:print('MEDIA',group,fid,flush=True)
 video=OUT/'galleries'/f'{group}_V1_V2.mp4';cmd=[str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-y','-v','error','-framerate','8','-start_number','1','-i',str(folder/'%06d.jpg'),'-frames:v',str(COUNTS[group]),'-vf','scale=1280:1056','-c:v','libx264','-threads','2','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(video)];r=subprocess.run(cmd,capture_output=True,text=True);(OUT/'logs'/f'video_{group}.log').write_text(r.stderr,encoding='utf8');assert r.returncode==0;check=subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True);assert check.returncode==0;write(OUT/'galleries'/f'{group}_video_qa.json',dict(frames=COUNTS[group],fps=8,full_decode=True,sha=sha(video),not_algorithm_fps=True))
 page='<meta charset="utf-8"><style>body{font:18px system-ui;background:#eef2f5}img{width:min(100%,1200px)}figure{margin:20px 0}video{width:min(100%,1200px)}</style><h1>'+group+' 全帧结果</h1><p>8fps仅播放速度；全部失败/无端点保留。紫色标签仅离线对比。<a href="index.html">返回六组导航</a></p><video controls src="'+video.name+'"></video>'+''.join(entries);(OUT/'galleries'/f'{group}.html').write_text(page,encoding='utf8');print('MEDIA COMPLETE',group,flush=True)
def main():
 assert (OUT/'validation_evaluation_complete.json').exists();(OUT/'logs').mkdir(exist_ok=True);(OUT/'galleries').mkdir(exist_ok=True)
 with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
  for _ in pool.map(render_group,VAL+DEV):pass
 cards=[];from evaluate_v2 import getlabels
 labels,_=getlabels(VAL+DEV)
 for case in read(OUT/'perturbation_plan.json')['cases']:
  if case['kind'] not in ['same_BMP_ABCD','predefined_sentinel']:continue
  folder=OUT/'sentinels'/case['name'];data=unpack(folder/'result.json.gz');R=decode(data['input']['reference']);C=decode(data['input']['current']);target=OUT/'galleries/sentinels'/f"{case['name']}.jpg";target.parent.mkdir(exist_ok=True);label=labels.get((case['row']['group'],case['row']['frame_id']));card(data,R,C,case['name']+' 预定义案例：全部模式、失败保留',label).save(target,quality=92);cards.append(f'<h2>{case["name"]}</h2><img src="sentinels/{case["name"]}.jpg"><p><a href="../sentinels/{case["name"]}/result.json.gz">逐列候选/假设</a></p>')
 (OUT/'galleries/same_bmp_ABCD_v1_v2.html').write_text('<meta charset="utf-8"><style>img{width:min(100%,1400px)}body{font:18px system-ui}</style><h1>ABCD及预定义哨兵</h1><p>第237帧没有精确LabelMe真值；近似回归锚点未进入检测。</p><a href="../D_two_origins_audit.csv">D两个首列起源生成审计</a> · <a href="../first_divergence_vs_v1.csv">全帧第一处决策分歧</a>'+''.join(cards),encoding='utf8')
 index='<meta charset="utf-8"><style>body{font:20px system-ui;max-width:1100px;margin:40px auto}li{margin:16px}video{max-width:100%}</style><h1>V1 / V2 六组全帧证据</h1><p>开发和已曝光回归分别报告。不是新盲测；不代表生产批准。<a href="../V2_DEVELOPMENT_REPORT.md">中文报告</a> · <a href="same_bmp_ABCD_v1_v2.html">ABCD/哨兵</a></p><ul>'
 for g in VAL+DEV:index+=f'<li>{g}：<a href="{g}.html">{COUNTS[g]}帧局部对比图</a> · <a href="{g}_V1_V2.mp4">完整视频</a></li>'
 index+='</ul>';(OUT/'galleries/index.html').write_text(index,encoding='utf8');write(OUT/'media_complete.json',dict(full_frame_comparisons=2647,videos=6,decoded=True,utc=utc()));print('MEDIA ALL COMPLETE',flush=True)
if __name__=='__main__':main()
