"""Scientific evidence plots and local interactive trace viewer, after all inference."""
from analyze import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
from PIL import Image,ImageDraw,ImageFont
import html
fontManager.addfont('C:/Windows/Fonts/msyh.ttc');plt.rcParams.update({'font.family':'Microsoft YaHei','axes.unicode_minus':False,'font.size':11,'figure.facecolor':'white','savefig.facecolor':'white'})
FIG=OUT/'figures'
COLORS=dict(A='#16a085',B='#2471a3',C='#8e44ad',D='#c0392b')
def finish(fig,name):fig.savefig(FIG/name,dpi=160,bbox_inches='tight');plt.close(fig)
def path(ax,name,mode='joint',color=None,limit=None,corridor=False):
 t=trace(name,mode);t=t[:limit] if limit else t;color=color or '#00a88f';chunk=[]
 for r in t:
  x=int(r['x']);y=int(r['selected_y']);observed=r['is_observed']=='True'
  if observed:chunk.append([x,y])
  else:
   if chunk:q=np.asarray(chunk);ax.plot(q[:,0],q[:,1],color=color,lw=1.6,marker='.',ms=2);chunk=[]
   ax.plot(x,y,'.',color='#d95d39',ms=1.8,alpha=.6)
 if chunk:q=np.asarray(chunk);ax.plot(q[:,0],q[:,1],color=color,lw=1.6,marker='.',ms=2)
 if corridor:
  x=np.array([int(r['x']) for r in t]);yp=np.array([float(r['predicted_y']) for r in t]);ax.fill_between(x,yp-7,yp+7,color=color,alpha=.16);ax.plot(x,yp,ls='--',lw=.8,color=color)
 observed=[r for r in t if r['is_observed']=='True']
 if observed and limit is None:ax.plot(int(observed[-1]['x']),int(observed[-1]['selected_y']),'x',color=color,ms=9,mew=2)
def raw(ax,image,bounds):
 x0,y0,x1,y1=map(int,bounds);ax.imshow(image[y0:y1,x0:x1],cmap='gray',vmin=0,vmax=255,extent=[x0-.5,x1-.5,y1-.5,y0-.5],interpolation='nearest');ax.set_xlim(x0,x1);ax.set_ylim(y1,y0);ax.set_xlabel('原图 x / px');ax.set_ylabel('原图 y / px')
def field(ax,case,key,bounds,vmin=None,vmax=None,cmap='turbo'):
 xa,ya,xb,yb=case['arrays']['crop'];im=ax.imshow(case['arrays'][key],extent=[xa-.5,xb-.5,yb-.5,ya-.5],vmin=vmin,vmax=vmax,cmap=cmap,interpolation='nearest');ax.set_xlim(bounds[0],bounds[2]);ax.set_ylim(bounds[3],bounds[1]);ax.set_title(key);return im
def overlays(C,cases):
 fig,axes=plt.subplots(2,2,figsize=(14,10),layout='constrained');bounds=[2210,2230,2505,2460]
 for name,ax in zip('ABCD',axes.flat):
  case=cases[name];raw(ax,C,bounds);path(ax,name,color=COLORS[name]);path(ax,name,'current','#e69f00');roi=case['meta']['ROI'];ax.axhline(roi['y_top'],color='deepskyblue',ls='--',lw=.8);ax.axhline(roi['y_bottom'],color='deepskyblue',ls='--',lw=.8);p=np.array(case['meta']['current_points']);ax.scatter(p[:,0],p[:,1],c='#ff8c00',marker='+',s=80);s=next(r for r in case['summary'] if r['mode']=='joint' and r['threshold']=='10.0');ax.plot(2423,2344,'+',color='magenta',ms=12);ax.set_title(f'{name} 原生V1：joint T10={tip(s)}\n彩色=joint；橙=current；紫=事后近似锚点')
 fig.suptitle('相同BMP、同一冻结Python：A/B/C/D交叉点位实测',fontsize=18);finish(fig,'same_bmp_ABCD_overlay.png')
 fig,axes=plt.subplots(2,2,figsize=(14,10),layout='constrained')
 for (g,m),ax in zip([(g,m) for g in ['A','D'] for m in ['A','D']],axes.flat):
  name=f'CF_geometry_{g}_motion_{m}';case=cases[name];raw(ax,C,bounds);path(ax,name);path(ax,name,'current','#e69f00');s=next(r for r in case['summary'] if r['mode']=='joint' and r['threshold']=='10.0');ax.set_title(f'诊断反事实：几何{g} × 位移场{m}\njoint T10={tip(s) or "NO_TIP"}');ax.plot(2423,2344,'+',color='magenta',ms=11)
 fig.suptitle('两因素隔离 · 不是原生V1性能或新算法结果',fontsize=18);finish(fig,'geometry_reference_counterfactual.png')
def candidates(cases):
 fig,axes=plt.subplots(2,4,figsize=(20,10),layout='constrained')
 for i,name in enumerate('ABCD'):
  rows_=cases[name]['init'];j=[r for r in rows_ if r['mode']=='joint'];cur=[r for r in rows_ if r['mode']=='current'];ax=axes[0,i];ax.plot([float(r['weighted_score']) for r in j],[int(r['y']) for r in j],label='joint score×prior',color=COLORS[name]);ax.plot([float(r['weighted_score']) for r in cur],[int(r['y']) for r in cur],label='current valley×prior',color='#e69f00',alpha=.7);winner=next(r for r in j if r['selected']=='True');ax.axhline(int(winner['y']),color=COLORS[name],ls='--');ax.invert_yaxis();ax.set_title(f"{name} 首列 x={winner['x']}，y0={winner['y']}");ax.set_xlabel('加权分数');ax.set_ylabel('全部候选 y');ax.legend(fontsize=8)
  top=sorted(j,key=lambda r:float(r['weighted_score']),reverse=True)[:10];ax=axes[1,i];ax.barh(range(10),[float(r['weighted_score']) for r in top],color=['#16a085' if r['accept_joint_T10']=='True' else '#aaaaaa' for r in top]);ax.set_yticks(range(10),[r['y'] for r in top]);ax.invert_yaxis();ax.set_xlabel('joint加权分数');ax.set_title('Top10：绿=满足joint T10\n灰=初始化得分非零但阈值不通过')
 fig.suptitle('首列完整排序：初始化并不先要求 valley/newdark 都≥10',fontsize=18);finish(fig,'first_column_candidates.png')
def divergence(C,cases):
 d=cases['D'];bounds=[2245,2265,2300,2370];fig,axes=plt.subplots(2,3,figsize=(17,11),layout='constrained');raw(axes[0,0],C,bounds);path(axes[0,0],'A',color=COLORS['A'],limit=30,corridor=True);path(axes[0,0],'D',color=COLORS['D'],limit=30,corridor=True);axes[0,0].set_title('头30列实际搜索走廊\nA绿 / D红；D仅执行22列')
 for ax,key,low,high,cmap in [(axes[0,1],'reference_aligned',0,255,'gray'),(axes[0,2],'newdark',-30,40,'coolwarm'),(axes[1,0],'valley',0,45,'turbo'),(axes[1,1],'valid_material',0,1,'gray'),(axes[1,2],'score',0,40,'turbo')]:
  im=field(ax,d,key,bounds,low,high,cmap);ax.axvline(2255,color='gold',ls='--',lw=.9);ax.scatter([2255,2255],[2282,2351],facecolors='none',edgecolors=['red','cyan'],s=70);fig.colorbar(im,ax=ax,shrink=.65)
 fig.suptitle('D关键首列 x=2255：红圈被选中；青圈是current首选但joint否决',fontsize=17);finish(fig,'first_divergence_panels.png')
def motion(C,cases):
 fig,axes=plt.subplots(2,3,figsize=(18,10),layout='constrained');box=[2245,2265,2300,2380]
 for ax,name in zip(axes[0,:2],['CF_geometry_D_motion_A','CF_geometry_D_motion_D']):
  im=field(ax,cases[name],'newdark',box,-30,40,'coolwarm');fig.colorbar(im,ax=ax,shrink=.7);ax.set_title('固定D几何 / '+name.rsplit('_',1)[-1]+'位移场\nnewdark，阈值10');ax.axvline(2255,color='black',ls='--',lw=.8)
 ax=axes[0,2]
 for name in ['A','D']:
  c=cases[name];y=np.arange(c['arrays']['crop'][1],c['arrays']['crop'][3]);ax.plot(c['arrays']['dy'][:,0],y,label=name+' dy',color=COLORS[name]);ax.plot(c['arrays']['dx'][:,0],y,label=name+' dx',color=COLORS[name],ls='--')
 ax.invert_yaxis();ax.set_title('两点插值位移场');ax.set_xlabel('原图位移 / px');ax.legend()
 raw(axes[1,0],C,[2520,2240,3650,2440]);rr=rows(OUT/'independent_material_motion.csv')
 from matplotlib.patches import Rectangle
 for r in rr:
  if r['motion']!='A':continue
  x0,y0,x1,y1=json.loads(r['bounds']);axes[1,0].add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,ec='#ff9300',lw=1.5));axes[1,0].text(x0,y0-3,f"NCC {float(r['template_peak_ncc']):.2f}",fontsize=8,color='red')
 axes[1,0].set_title('固定材料纹理候选窗：未认证全无裂纹')
 for i,key in enumerate(['aligned_current_ncc','zero_mean_residual_rmse'],1):
  ax=axes[1,i];names=list(dict.fromkeys(r['patch'] for r in rr));x=np.arange(len(names))
  for motion,shift in [('A',-.18),('D',.18)]:ax.bar(x+shift,[float(next(r[key] for r in rr if r['patch']==n and r['motion']==motion)) for n in names],.36,label=motion,color=COLORS[motion])
  ax.set_xticks(x,names,rotation=35,ha='right');ax.set_title(key);ax.legend()
 fig.suptitle('参考变化有直接数值证据；材料物理配准失真仍需独立证据',fontsize=18);finish(fig,'reference_motion_and_delta.png')
def sensitivity():
 rr=rows(OUT/'point_sensitivity.csv');fig,axes=plt.subplots(2,4,figsize=(21,10),layout='constrained')
 for i,base in enumerate(['A','D']):
  for j,scope in enumerate(['both','current','reference']):
   ax=axes[i,j]
   for mode,color in [('joint','#16a085'),('current','#e69f00')]:
    r=[r for r in rr if r['base']==base and r['scope']==scope and r['mode']==mode and r['threshold']=='10'];x=[float(r['dy']) for r in r];errors=[float(r['approximate_anchor_error']) if r['approximate_anchor_error'] else np.nan for r in r];ax.plot(x,errors,'o-',color=color,label=mode);missing=[float(r['dy']) for r in r if not r['tip']];ax.scatter(missing,[-15]*len(missing),marker='x',c=color,s=60)
   ax.set_title(f'{base}基点 / {scope} y平移');ax.set_xlabel('预定义 dy / px');ax.set_ylabel('离线近似锚点距离 / px；×=NO_TIP');ax.set_ylim(bottom=-25);ax.grid(alpha=.25);ax.legend()
  ax=axes[i,3];r=[r for r in rr if r['base']==base and '_p' in r['scope'] and r['mode']=='joint' and r['threshold']=='10'];names=[r['scope'].replace('reference','R').replace('current','C')+'/'+r['dy'] for r in r];errors=[float(r['approximate_anchor_error']) if r['approximate_anchor_error'] else np.nan for r in r];ax.bar(range(len(r)),errors,color=COLORS[base]);ax.set_xticks(range(len(r)),names,rotation=90,fontsize=8);ax.set_title(base+'：单点 y±2/±5，joint T10')
 fig.suptitle('预定义扰动响应：不是实际追踪误差分布，也不用于选参数',fontsize=18);finish(fig,'sensitivity_plot.png')
 fig,axes=plt.subplots(1,2,figsize=(14,5),layout='constrained');r=[r for r in rr if r['scope']=='four_point_linear_interpolation' and r['mode']=='joint' and r['threshold']=='10'];t=[float(v['t']) for v in r];errors=[float(v['approximate_anchor_error']) if v['approximate_anchor_error'] else np.nan for v in r];axes[0].plot(t,errors,'o-',color='#16a085');axes[0].scatter([float(v['t']) for v in r if not v['tip']],[-15]*sum(not v['tip'] for v in r),marker='x',c='red');axes[0].set_ylabel('近似锚点误差；×=NO_TIP');axes[1].plot(t,[int(v['y0']) for v in r],'o-');axes[1].set_ylabel('初始化 y0')
 for ax in axes:ax.set_xlabel('四点 A→D 预定插值 t');ax.grid(alpha=.25)
 fig.suptitle('首个已采样终点跃迁在t=0.7；t=0.8无输出，不细化搜最佳值',fontsize=16);finish(fig,'interpolation_transition.png')
def sentinel_figures(config):
 manifest={int(r['frame_id']):r for r in rows(OLD/'inputs/validation_manifest.csv') if r['group']=='group_c'};frames=[r['frame_id'] for r in read(OUT/'sentinel_plan.json')['additional_visible_frames']];fig,axes=plt.subplots(2,2,figsize=(15,10),layout='constrained')
 for f,ax in zip(frames,axes.flat):
  case=load_case('sentinel_'+str(f));im=cv2.imread(str(OUT/'staging'/f'current_{f}.bmp'),0);raw(ax,im,[2220,2240,2505,2460]);path(ax,case['name']);path(ax,case['name'],'current','#e69f00');label=read(case['folder']/'offline_label.json')
  for shape in label['shapes']:
   pts=np.array(shape['points'])
   if shape['label']=='crack_path':ax.plot(pts[:,0],pts[:,1],c='magenta',lw=.8)
   if shape['label']=='crack_tip':ax.plot(pts[0,0],pts[0,1],'+',c='magenta',ms=11)
  stats=[r for r in rows(OUT/'group_sentinels.csv') if int(r['frame_id'])==f];title=' / '.join(r['mode']+': '+(f"{float(r['offline_error']):.2f}px" if r['offline_error'] else 'NO_TIP') for r in stats);ax.set_title(f'验证组C{f} | {title}\n绿joint / 橙current / 紫人工离线对照')
 fig.suptitle('四个既有VISIBLE代表帧：保留无输出与远错误',fontsize=18);finish(fig,'group_sentinels.png')
 case=load_case('sentinel_1');fig,axes=plt.subplots(1,3,figsize=(16,5),layout='constrained');field(axes[0],case,'newdark',[2240,2250,2460,2445],-10,10,'coolwarm');axes[0].set_title('首帧 R=C：newdark全零')
 for mode,ax in zip(['joint','current'],axes[1:]):
  r=[r for r in case['init'] if r['mode']==mode];ax.plot([float(v['weighted_score']) for v in r],[int(v['y']) for v in r]);winner=next(v for v in r if v['selected']=='True');ax.axhline(int(winner['y']),c='red',ls='--');ax.invert_yaxis();ax.set_title(f"{mode}: y0={winner['y']}\nnp.argmax全零时选第一候选（仅joint）")
 finish(fig,'zero_initialization.png')
 R=cv2.imread(config['reference'],0);C=cv2.imread(config['current'],0);fig,axes=plt.subplots(1,2,figsize=(12,8),layout='constrained')
 for kind,im,ax in [('R',R,axes[0]),('C',C,axes[1])]:
  raw(ax,im,[2180,2210,2340,2470]);ax.set_title(('参考' if kind=='R' else '当前')+'精确点位：G绿 / S红')
  for source,color in [('G',COLORS['A']),('S',COLORS['D'])]:
   points=config['points'][kind+'_'+source]
   for i,p in enumerate(points):ax.scatter(*p,c=color,s=80,marker='+');ax.text(p[0]+2,p[1]+(-5 if source=='G' else 10),f'{source}P{i+1}',color=color,fontsize=10)
 fig.suptitle('坐标映射正确不等于两套点测量相同物理中心；原点击语义未提供',fontsize=15);finish(fig,'point_semantics.png')
def viewer(C,cases):
 bounds=[2235,2250,2485,2445];x0,y0,x1,y1=bounds;Image.fromarray(C[y0:y1,x0:x1]).save(FIG/'interactive_raw_crop.png');data={}
 for name in 'ABCD':
  data[name]={}
  for mode in ['joint','current']:
   cs=[r for r in cases[name]['candidates'] if r['mode']==mode];cols={}
   for r in cs:
    f={k:float(r[k]) for k in ['x','y','yp','valley','newdark','strength','merit','missing_run']};f.update({k:r[k]=='True' for k in ['valid_material','accept','selected','is_observed']});cols.setdefault(r['x'],[]).append(f)
   data[name][mode]=dict(columns=cols,trace=[dict(x=int(r['x']),y=int(r['selected_y']),observed=r['is_observed']=='True',yp=float(r['predicted_y'])) for r in trace(name,mode)])
 page='''<!doctype html><meta charset="utf-8"><title>验证组C同BMP逐列因果审计</title><style>body{font:17px system-ui;margin:28px;background:#f4f6f8;color:#17283a}a{color:#006d77}canvas{width:min(100%,1100px);background:white}table{border-collapse:collapse;background:white;font-size:14px}td,th{padding:5px 9px;border:1px solid #ddd}.selected{background:#ffe3a3}img{max-width:100%}select,input,button{font:inherit}</style><h1>同一BMP · 冻结V1逐列证据</h1><p><a href="ROOT_CAUSE_REPORT.md">完整中文报告</a> · <a href="initial_candidate_audit.csv">首列全部候选CSV</a> · <a href="first_causal_divergence.csv">首次分歧CSV</a> · <a href="root_cause_walkthrough.mp4">证据视频</a></p><p>这是已曝光案例故障审计，不是新算法、训练或盲测。下面只展示原生A/B/C/D的T10实际候选；紫色十字为推理完成后叠加的近似回归锚点。</p><select id="case"><option>A</option><option>B</option><option>C</option><option>D</option></select> <select id="mode"><option>joint</option><option>current</option></select> <button id="prev">上一列</button> x=<input id="x" type="number" style="width:95px"> <button id="next">下一列</button><p id="status"></p><canvas width="1000" height="780" id="plot"></canvas><table><thead><tr><th>y</th><th>valley</th><th>newdark</th><th>材料</th><th>accept</th><th>strength</th><th>merit</th><th>选中</th></tr></thead><tbody id="rows"></tbody></table>'''
 page+='<script>const DATA='+json.dumps(data,separators=(',',':'))+';const BOUNDS='+json.dumps(bounds)+''';const c=document.getElementById('case'),m=document.getElementById('mode'),x=document.getElementById('x'),canvas=document.getElementById('plot'),ctx=canvas.getContext('2d');const im=new Image();im.src='figures/interactive_raw_crop.png';function xy(a,b){return [(a-BOUNDS[0]+.5)*4,(b-BOUNDS[1]+.5)*4]}function line(a,b,color){ctx.strokeStyle=color;ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke()}function render(reset=false){const v=DATA[c.value][m.value],keys=Object.keys(v.columns).map(Number).sort((a,b)=>a-b);x.min=keys[0];x.max=keys.at(-1);if(reset||!v.columns[x.value])x.value=keys[0];const col=v.columns[x.value],sel=col.find(v=>v.selected);ctx.clearRect(0,0,1000,780);ctx.drawImage(im,0,0,1000,780);ctx.lineWidth=2;v.trace.forEach((p,i)=>{if(i&&p.observed&&v.trace[i-1].observed)line(xy(v.trace[i-1].x,v.trace[i-1].y),xy(p.x,p.y),'#00ad81');else{ctx.fillStyle=p.observed?'#00ad81':'#d35c30';ctx.fillRect(...xy(p.x,p.y),3,3)}});ctx.fillStyle='rgba(0,130,230,.18)';const a=xy(Number(x.value)-.5,col[0].y-.5),b=xy(Number(x.value)+.5,col.at(-1).y+.5);ctx.fillRect(a[0],a[1],Math.max(4,b[0]-a[0]),b[1]-a[1]);ctx.strokeStyle='red';ctx.beginPath();ctx.arc(...xy(sel.x,sel.y),6,0,7);ctx.stroke();const p=xy(2423,2344);line([p[0]-8,p[1]],[p[0]+8,p[1]],'magenta');line([p[0],p[1]-8],[p[0],p[1]+8],'magenta');document.getElementById('status').textContent=`${c.value}/${m.value}/T10：x=${x.value}，预测y=${sel.yp}，选中y=${sel.y}，观测=${sel.is_observed}，missing_run=${sel.missing_run}；蓝色=真实候选走廊。`;document.getElementById('rows').innerHTML=col.map(r=>'<tr class="'+(r.selected?'selected':'')+'"><td>'+r.y+'</td>'+['valley','newdark'].map(k=>'<td>'+r[k].toFixed(4)+'</td>').join('')+'<td>'+r.valid_material+'</td><td>'+r.accept+'</td><td>'+r.strength.toFixed(4)+'</td><td>'+r.merit.toFixed(4)+'</td><td>'+r.selected+'</td></tr>').join('')}c.onchange=m.onchange=()=>render(true);x.onchange=()=>render();document.getElementById('prev').onclick=()=>{x.value=Math.max(Number(x.min),Number(x.value)-1);render()};document.getElementById('next').onclick=()=>{x.value=Math.min(Number(x.max),Number(x.value)+1);render()};im.onload=()=>render(true);</script>'''
 for name,label in [('same_bmp_ABCD_overlay.png','原生ABCD'),('first_column_candidates.png','初始化排序'),('first_divergence_panels.png','首个路线决策'),('geometry_reference_counterfactual.png','诊断反事实，非原生输出'),('reference_motion_and_delta.png','独立材料运动检查'),('sensitivity_plot.png','预定扰动'),('interpolation_transition.png','插值跃迁'),('group_sentinels.png','其他可见帧'),('zero_initialization.png','全零argmax'),('point_semantics.png','点位语义')]:page+=f'<h2>{label}</h2><img loading="lazy" src="figures/{name}">'
 (OUT/'trace_audit_A_B_C_D.html').write_text(page,encoding='utf8')
def video():
 slides=[('same_bmp_ABCD_overlay.png','原生V1：A/B/C/D相同图像、交叉点位'),('first_column_candidates.png','原生首列完整排序：D在y=2282锁定'),('first_divergence_panels.png','采样走廊：候选间距69px，局部半宽7px'),('geometry_reference_counterfactual.png','诊断反事实：非原生V1性能结果'),('reference_motion_and_delta.png','参考差分变化≠已证明材料配准失真'),('sensitivity_plot.png','固定扰动范围：不是噪声分布，不用于调参'),('interpolation_transition.png','A→D首个已采样跃迁t=0.7；t=0.8无输出'),('group_sentinels.png','其他4张已有可见标签：失败同样保留'),('zero_initialization.png','首帧R=C：全零argmax默认首候选')];folder=OUT/'video_frames';folder.mkdir(exist_ok=True);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20);paths=[]
 for i,(name,title) in enumerate(slides):
  canvas=Image.new('RGB',(1920,1200),'#132131');d=ImageDraw.Draw(canvas);d.text((24,12),title,font=font,fill='white');im=Image.open(FIG/name).convert('RGB');im.thumbnail((1890,1090));canvas.paste(im,((1920-im.width)//2,60+(1090-im.height)//2));d.text((24,1160),'验证组C已曝光案例故障审计 | 冻结V1未改 | 暂定端点不是正式确认 | 标注仅离线对照',font=small,fill='white');p=folder/f'{i:02d}.png';canvas.save(p);paths.append(p)
 listing=OUT/'video_concat.txt';listing.write_text(''.join("file '"+str(p).replace('\\','/')+"'\nduration 6\n" for p in paths)+"file '"+str(paths[-1]).replace('\\','/')+"'\n",encoding='utf8');output=OUT/'root_cause_walkthrough.mp4';subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-t',str(6*len(paths)),'-vf','fps=12','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True);subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-v','error','-i',str(output),'-f','null','-'],check=True,capture_output=True);write(OUT/'video_qa.json',dict(duration=6*len(paths),slides=len(paths),full_decode_pass=True,sha256=sha(output)))
def main():
 assert read(OUT/'analysis_complete.json')['source_unchanged'];FIG.mkdir(exist_ok=True);config=read(OUT/'inputs.json');C=cv2.imread(config['current'],0);names=list('ABCD')+[f'CF_geometry_{g}_motion_{m}' for g in ['A','D'] for m in ['A','D']];cases={n:load_case(n) for n in names};overlays(C,cases);candidates(cases);divergence(C,cases);motion(C,cases);sensitivity();sentinel_figures(config);viewer(C,cases);video();write(OUT/'visualization_complete.json',dict(figures=len(list(FIG.glob('*.png'))),native_and_counterfactual_separated=True));print('VISUALIZATION COMPLETE',flush=True)
if __name__=='__main__':main()
