"""Render and report frozen diagnostic results; never changes detection rules."""
import collections,zipfile,shutil,html,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from common import *
from analyze import original,local
FONT='C:/Windows/Fonts/msyh.ttc'
FOCUS=[('ct2',395),('group_h',78),('group_a',504),('ct3',65),('ct2',8),('ct2',457),('group_h',41),('group_h',96),('group_a',67),('group_c',528),('three_point_bend',503)]
def txt(d,xy,s,size=22,color='white'):d.text(xy,str(s),font=ImageFont.truetype(FONT,size),fill=color)
def image_panel(source,box,lines,points,polygons):
 crop=source.crop(tuple(map(int,box)));scale=min(750/crop.width,355/crop.height);size=tuple(max(1,round(v*scale)) for v in crop.size);im=crop.resize(size,Image.Resampling.LANCZOS);d=ImageDraw.Draw(im)
 def xy(p):return ((p[0]-box[0])*scale,(p[1]-box[1])*scale)
 for line,color,width in lines:
  if len(line)>1:d.line([xy(p) for p in line],fill=color,width=width)
 for poly,color in polygons:
  if poly:d.line([xy(p) for p in poly]+[xy(poly[0])],fill=color,width=2)
 for point,color in points:
  x,y=xy(point);d.ellipse((x-5,y-5,x+5,y+5),outline=color,width=3)
 out=Image.new('RGB',(750,355),'#172537');out.paste(im,((750-im.width)//2,(355-im.height)//2));return out
def roi_poly(roi):x,y,w,h=roi;return [[x,y],[x+w-1,y],[x+w-1,y+h-1],[x,y+h-1]]
def panel(r,t,label,metric):
 source=PRE/'R05_LabelMe_Annotation_Package'/r['selected_image'];assert sha(source)==r['source_sha256'];im=Image.open(source).convert('RGB')
 human=[s['points'] for s in label['shapes'] if s['label']=='crack_path'];tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];actual=t['formal']['tip'];points=[(p,'#ff4a64') for p in tips]+([(actual,'#22e5ff')] if actual else [])
 lines=[(p,'#ff4a64',2) for p in human];polygons=[(roi_poly(t['roi']),'#ffdb4d')]+[(p,'#c486ff') for p in t['main_rois']]
 extent=np.array([*roi_poly(t['roi']),*tips],float);lo=np.maximum(extent.min(axis=0)-40,0);hi=np.minimum(extent.max(axis=0)+40,[im.width,im.height]);box=[*lo,*hi]
 if box[2]<=box[0] or box[3]<=box[1]:box=[0,0,im.width,im.height]
 base=image_panel(im,box,lines,points,polygons)
 algorithm=[(t['selected_original'],'#60ff86',3)]
 candidate_points=[]
 # Actual visited production candidates only. All candidates remain in trace JSON.
 for peak in t['peaks'][:5]:
  if peak['line_local_reverse']:algorithm.append((original(peak['line_local_reverse'],t).tolist(),'#f89c57',2));candidate_points.append((original([peak['xy']],t)[0],'#f89c57'))
 candidates=image_panel(im,box,algorithm,candidate_points+points,polygons)
 tip=tips[0] if tips else t['center'];zoom=[max(0,tip[0]-150),max(0,tip[1]-150),min(im.width,tip[0]+150),min(im.height,tip[1]+150)]
 close=image_panel(im,zoom,lines+algorithm,candidate_points+points,[])
 with np.load(OUT/'maps'/f"{r['dataset_id']}__{int(r['frame_id']):06d}.npz") as a:
  evidence=Image.new('RGB',(750,355),'#172537')
  if 'score' in a:
   score=a['score'];rgb=np.stack([np.clip(score,0,20)*12]*3,axis=-1).astype(np.uint8);rgb[a['reason']<5]=[81,42,92];e=Image.fromarray(rgb);ed=ImageDraw.Draw(e)
   for line in human:ed.line([tuple(p) for p in local(line,t)],fill='#ff4a64',width=2)
   if t['selected_local']:ed.line([tuple(p) for p in t['selected_local']],fill='#60ff86',width=2)
   e.thumbnail((750,355));evidence.paste(e,((750-e.width)//2,(355-e.height)//2))
  else:txt(ImageDraw.Draw(evidence),(30,120),'NOT_COMPUTED / registration or baseline skip',23)
 out=Image.new('RGB',(1600,1000),'#101b2b');d=ImageDraw.Draw(out)
 txt(d,(30,18),f"{r['dataset_id']} / {r['frame_id']} / {role(r['dataset_id'])} | first stage: {metric['first_failure_stage']}",29)
 txt(d,(30,62),f"{metric['failure_subtype']}",20)
 txt(d,(30,100),f"observed={metric['observed']} | error={metric['error_original_px'] or 'N/A'} px | GT in ROI={metric['oracle_tip_in_roi'] or 'N/A'}",22)
 txt(d,(30,129),f"local endpoint {t['selected_local'][-1] if t['selected_local'] else 'NONE'} -> original {actual or 'NONE'} | ROI {t['roi']} | roundtrip {metric['coordinate_roundtrip_px']} px",14)
 for pos,img,title in [((30,180),base,'原图：红色人工路径/尖端，青色 A；黄色端点ROI，紫色主路径采样区域'),((820,180),evidence,'端点分支实际消费 score；紫色未通过计算条件（不是 E1/E2）'),((30,600),close,'人工尖端附近放大；红色人工，绿色实际选中，橙色真实候选'),((820,600),candidates,'绿色实际路径；橙色实际访问过的前五候选（完整列表见 trace）')]:
  txt(d,(pos[0],pos[1]-33),title,17);out.paste(img,pos)
 txt(d,(30,965),'离线核验，无训练/调参；3/5/10均为原图像素。未访问候选不能称已通过审计。',20)
 return out
def number(v):return 'N/A' if v in ['',None] else f'{float(v):.3f}'
def main():
 assert all(read(OUT/f'{p}_complete.json')['equivalence']=='PASS' for p in ['dev','val','cf'])
 # Only analysis and native diagnostic code were frozen for validation; report code may evolve.
 freeze=read(OUT/'diagnosis_frozen_before_validation.json')
 for p,h in freeze['source_hashes'].items():
  if Path(p).name in ['analyze.py','trace.hpp','exports.inc','replay.py']:assert sha(ROOT/p)==h,p
 merged={}
 for outname,stem in [('tip_reachability_per_frame','reachability'),('candidate_trace','candidate'),('terminal_audit_trace','terminal'),('registration_trace','registration'),('evidence_trace','evidence'),('a0_d0_equivalence','equivalence'),('timings','timings')]:
  merged[outname]=rows(OUT/f'{stem}_dev.csv')+rows(OUT/f'{stem}_val.csv');save(OUT/f'{outname}.csv',merged[outname])
 # Presentation only: unevaluated trace defaults must not masquerade as measured zeros.
 for c in merged['candidate_trace']:
  c['raw_trace_stage']=c['stage'];visited_path=bool(json.loads(c['path_local_reverse']))
  if not visited_path:c['hits']=None
  if not visited_path or c['stage'] in ['path_too_short','path_hits_below_72pct']:c['tail_hits']=None
  if c['shared']=='-1':c['shared']=None
 save(OUT/'candidate_trace.csv',merged['candidate_trace'])
 per=merged['tip_reachability_per_frame'];lookup={(r['dataset_id'],int(r['frame_id'])):r for r in per};summary=[]
 for g in ['group_a','ct2','group_h','ct3','group_c','three_point_bend']:
  rr=[r for r in per if r['dataset_id']==g];vis=[r for r in rr if r['annotation_state']=='VISIBLE'];counts=collections.Counter(r['first_failure_stage'] for r in vis)
  for stage,n in counts.items():summary.append(dict(dataset_id=g,role=role(g),stage=stage,count=n,visible_denominator=len(vis),all_selected=len(rr),evidence='operational trace query, not automatically causal proof'))
 save(OUT/'first_failure_summary.csv',summary)
 strata=collections.Counter((r['dataset_id'],r['group_role'],r['stratum']) for r in per);save(OUT/'stratum_summary.csv',[dict(dataset_id=g,role=role_,stratum=s,count=n) for (g,role_,s),n in strata.items()])
 cf_summary=[]
 for variant in ['CF1','CF2','CF3','CF4']:
  rr=[r for r in rows(OUT/'counterfactual_results.csv') if r['variant']==variant and r['annotation_state']=='VISIBLE']
  cf_summary.append(dict(variant=variant,visible=len(rr),baseline_observed=sum(r['baseline_observed']=='True' for r in rr),counterfactual_nonempty=sum(r['counterfactual_nonempty_path']=='True' for r in rr),**{f'baseline_within{tol}':sum(r['baseline_error_px']!='' and float(r['baseline_error_px'])<=tol for r in rr) for tol in [3,5,10]},**{f'counterfactual_within{tol}':sum(r['counterfactual_error_px']!='' and float(r['counterfactual_error_px'])<=tol for r in rr) for tol in [3,5,10]},online_accuracy_claim=False))
 save(OUT/'counterfactual_summary.csv',cf_summary)
 geometries=[]
 for phase in ['dev','val']:
  for r in map(json.loads,(OUT/f'{phase}_frames.jsonl').read_text().splitlines()):
   geometries.append(dict(dataset_id=r['dataset_id'],frame_id=r['frame_id'],roi=r['roi'],center=r['center'],tip_transform=r['tip_transform'],main_transform=r['main_transform'],valid=r['registration_valid'],motion_branch=r['motion_branch'],observed=r['observed'],tip=r['tip']))
 assert read(OUT/'geometry_completion.json')['frames']==2647
 shutil.copy2(OUT/'roi_geometry_trace_full.csv',OUT/'roi_geometry_trace.csv')
 local_votes=[]
 for p in (OUT/'traces').glob('*__local.json'):
  audit=read(p)
  for tile in audit['tiles']:local_votes.append(dict(dataset_id=audit['dataset_id'],frame_id=audit['frame_id'],tile=tile['tile'],stage=tile['stage'],correlations=tile['correlations'],votes=tile['votes'],agree=tile['agree'] if tile['votes']>=2 else None,offset=tile['offset'] if tile['votes']>=2 else None,registered_bitwise_equal=True))
 save(OUT/'local_reference_vote_trace.csv',local_votes)
 perf=[]
 for g in ['ALL','group_a','ct2','group_h','ct3','group_c','three_point_bend']:
  for variant in ['A0_FROZEN','D0_TRACE_ONLY']:
   rr=[r for r in merged['timings'] if r['reference_query']=='False' and r['variant']==variant and (g=='ALL' or r['dataset_id']==g)];v=np.array([float(r['api_wall_ms']) for r in rr]);perf.append(dict(dataset_id=g,variant=variant,n=len(v),p50=float(np.median(v)),p95=float(np.percentile(v,95)),p99=float(np.percentile(v,99)),max=float(v.max()),over50=int(np.sum(v>50))))
 save(OUT/'performance_summary.csv',perf)
 cf=rows(OUT/'counterfactual_results.csv');cflook={(r['dataset_id'],int(r['frame_id']),r['variant']):r for r in cf}
 selected=rows(OUT/'selected_frames.csv');cards=[]
 with zipfile.ZipFile(R05/'human_annotations_six_groups_snapshot.zip') as z:
  for r in selected:
   g=r['dataset_id'];f=int(r['frame_id']);require(g,'comparison',uses_annotations=True);name=f'{g}__{f:06d}';t=read(OUT/'traces'/f'{name}.json');label=json.loads(z.read(r['selected_json']));panel(r,t,label,lookup[g,f]).save(OUT/'images'/f'{name}.jpg',quality=91)
   shutil.copy2(R05/'diagnostics'/f'{g}__frame_{f:06d}.jpg',OUT/'images'/f'{name}__difference.jpg')
   met=lookup[g,f];details=html.escape(json.dumps({k:met[k] for k in ['first_failure_stage','oracle_tip_in_roi','oracle_tip_evidence_available','oracle_near_candidate','coordinate_roundtrip_px','evidence_level','missing_internal_state']},ensure_ascii=False))
   cards.append(f'<section id="{name}"><h2>{g} / {f}</h2><p>{details}</p><p>原图 SHA256: {r["source_sha256"]}</p><a href="traces/{name}.json">真实内部trace与所有候选</a> · <a href="source_dependency_map.md">源码调用链</a><img loading="lazy" src="images/{name}.jpg"><details><summary>独立 R05 E1/E2 对照（不是生产A的输入）</summary><img loading="lazy" src="images/{name}__difference.jpg"></details></section>')
 (OUT/'R05D_G0_G5_Failure_Gallery.html').write_text('<!doctype html><meta charset="utf-8"><title>R05D真实尖端可达性</title><style>body{background:#101b2b;color:#ecf3fb;font:17px system-ui;margin:24px}a{color:#72cbff}img{width:100%;max-width:1600px}section{padding:15px;border:1px solid #334;margin-bottom:24px}p{overflow-wrap:anywhere}</style><h1>R05D：全部120选帧真实证据</h1><p>开发四组 / 验证组C三点弯只验证 / 排除组X排除。红色为人工，绿色为生产实际路径，青色为生产确认尖端。</p>'+''.join(cards),encoding='utf8')
 for g,f in FOCUS:shutil.copy2(OUT/'images'/f'{g}__{f:06d}.jpg',OUT/f'key_{g}_{f}.jpg')
 # Function lines in unchanged production source are the authoritative map.
 functions={}
 for name in ['CrackV4.cpp','roi_tip.inc']:
  lines=(ROOT/'src/cpp/a'/name).read_text(encoding='utf8').splitlines()
  for i,line in enumerate(lines,1):
   if any(s in line for s in ['bool Detector::estimateTipMotion','void Detector::motion','void Detector::measureTip','Path distalLine','cv::Rect tipWindow','cv::Mat1b localReference','int CrackV4Process','r.tip=r.has=r.path_valid=r.terminal=','r.endpoint=r.tipxy=','if(shared<4)return','if(g<(absolute?55:12)']):functions[f'{name}:{i}']=line.strip()
 (OUT/'source_dependency_map.md').write_text('# 当前生产调用链\n\n初始化 choosePatches -> 固定 origin/spacing/forward -> 每帧 CrackV4Process -> Detector::process -> motion（主路径）及 estimateTipMotion（端点独立）-> 主路径 seed/tile/Frangi -> measureTip覆盖最终尖端 -> tipWindow -> localReference -> 暗线/参考score -> distalLine -> 非空路径直接确认 -> V2返回。主路径仅参与完整长度，不决定端点是否存在。\n\n端点DP是自由起点，best=0允许任意列重新起步；没有显式物理主裂纹身份验证。主路径Frangi图未导出，端点实际score/gains/back均已导出。逐tile相关值和票数由同一原生函数stateless重算，注册后float数组与D0逐位hash一致，见traces/*__local.json。主路径完整Frangi数组标NOT_EXPOSED，不用替代算法补画。\n\n'+ '\n'.join(f'- `{k}` `{v}`' for k,v in functions.items())+'\n\n原始生产源码见source_evidence/，trace为生成副本的只读采集。主路径采样ROI为变换后的网格多边形，并非端点ROI。端点尺度1、0-based整数像素中心，quarter-turn逆映射后加roi.tl。\n',encoding='utf8')
 (OUT/'source_evidence').mkdir(exist_ok=True)
 for n in ['CrackV4.cpp','roi_tip.inc']:shutil.copy2(ROOT/'src/cpp/a'/n,OUT/'source_evidence'/n)
 root=['# 可达性与根因证据\n','阶段是冻结查询合同下的直接追踪结果，不把“离GT较远”当成物理误报。只有反事实显示单变量使不可达→可达，才声称该变量有局部因果贡献。G1/G2/G3基于10px粗标注邻域；没有独立误差校准，不声称无限精度真值。\n']
 for g,f in FOCUS:
  r=lookup[g,f];t=read(OUT/'traces'/f'{g}__{f:06d}.json');root.append(f"## {g}/{f}\n\n首失效 `{r['first_failure_stage']}` / `{r['failure_subtype']}`；GT在端点ROI={r['oracle_tip_in_roi']}，ROI={r['roi']}；10px邻域score最大值={r.get('tip10px_score_max','N/A')}；最近真实峰候选距离={r['nearest_candidate_distance']}px；端点配准分支={t['motion_branch']}，inliers={t['solve_inliers']}，残差={t['solve_residual']:.6g}。局部DP真实子条件计数：{dict(collections.Counter(p['stage'] for p in t['peaks']))}。\n\n源码责任范围：{r['source_location']}；非空路径⇒terminal语义仍在roi_tip.inc:224附近。坐标往返误差={r['coordinate_roundtrip_px']}，内部路径终点与返回点差={r.get('internal_tip_to_returned_px','N/A')}。\n")
  for variant in ['CF1','CF2','CF3']:
   c=cflook.get((g,f,variant))
   if c:root.append(f"- {variant}: {c['unique_changed_variable']}; ROI内={c['counterfactual_tip_in_roi']}; 非空路径={c['counterfactual_nonempty_path']}; 误差={c['counterfactual_error_px'] or 'N/A'}px; 10px近峰数={c['near_actual_peaks']}; 远离GT的峰数={c['distant_peaks_not_true_false_positives']}（不是误报率）。\n")
  c=cflook.get((g,f,'CF4'))
  if c:root.append(f"- CF4（仅补入原本reason2被参考门排除像素的当前valley）：误差={c['counterfactual_error_px'] or 'N/A'}px；10px近峰={c['near_actual_peaks']}；候选数 {c['baseline_candidate_count']}→{c['candidate_count']}。原始score控制重算与生产DP逐点一致。\n")
  if r.get('local_reference_at_tip'):root.append(f"\n尖端所在64px参考块的真实小模板审计：`{r['local_reference_at_tip']}`。该stateless原生重算的registered浮点数组hash与D0完全一致。10px尖端邻域条件码：{r.get('tip10px_reason_counts')}。条件码2表示reference erosion≤75；代码初始化aligned为0，票数/一致性不足便continue，故当前帧可见裂纹仍可能完全失去score。\n")
  root.append(f"\n[原图拼图](key_{g}_{f}.jpg) · [真实trace](traces/{g}__{f:06d}.json)。未证明部分：参考模板匹配正确性不是几何往返正确性的推论，局部相关接受不等于物理对应正确。\n")
 (OUT/'root_cause_report.md').write_text('\n'.join(root),encoding='utf8')
 dev=[r for r in per if r['group_role']=='DEVELOPMENT' and r['annotation_state']=='VISIBLE'];val=[r for r in per if r['group_role']=='VALIDATION_ONLY' and r['annotation_state']=='VISIBLE'];dc=collections.Counter(r['first_failure_stage'] for r in dev);vc=collections.Counter(r['first_failure_stage'] for r in val)
 report=f'''# R05D 冻结生产A：真实尖端首次失效诊断

本轮只增加隔离插桩、离线反事实和评价，没有生产补丁。输出按项目AGENTS.md放在output/runs/，而非任务书的research/out；生产及R01–R05原产物只读。

## 四个优先问题的直接回答

1. CT2/395：人工尖端在真实ROI [2584,2329,1673,769] 内，首次失效G1。所在64px块9个相关值约0.13–0.21，0票达到0.62；roi_tip.inc:53跳过该块，aligned保留0，:185 eroded>75失败，尖端10px邻域314个像素均未生成score。输出2878,2706就是内部选中错误早端点，非最后映射错误。扩窗误差仍928.94px；参考门离线旁路使GT附近峰0→1，但最终误差仍238.55px，后续排序也有问题。
2. 开发组H/78：GT也在ROI内，首次G1。局部块3票达到0.62，但二维一致性票为0，:57拒绝；尖端邻域312像素score保持-3。错误区域的自由起点路径被选中，:224非空路径直接令terminal=true，故产生roi_terminal_supported。内部候选本就在错误区域；数值映射闭环正常，不能据此声称物理配准完全正确。
3. GROUP_A/504：G0/G1通过；7.12px附近真实候选已存在且通过前置尾端/材质条件，但与先前选中路径在重叠端共享不足4点，:139 shared<4使distalLine返回空路径，最终roi_terminal_unconfirmed。跳过该整帧拒绝会返回误差360.98px的旧候选，不是安全修复；当前证据旁路可得7.12px，却让峰数3→448。
4. CT3/65：参考块6票一致通过，尖端附近score最大25.17，末端后25px路径响应有支持，最近峰约1.64px，最终误差8.41px，映射误差约1e-13。它是10px粗容差内正向对照，不是零误差真值。

## 完成范围

六组完整2647帧（包含6次首帧缓存查询）A0/D0非计时原生返回、状态、路径/长度严格一致。独立同源码A0重建还通过每组前3帧对照。开发四组1565帧，80选帧，其中76 VISIBLE、4 UNCERTAIN；验证两组1082帧，40选帧，其中35 VISIBLE、5 UNCERTAIN。R05旧2576前缀回放的120选帧结果原样复现；原73/111确认、38缺失、17/111≤5px不被改写。

原主回放只保存了选帧的主路径多边形，后续另做2647帧完全等价、无标签、无新评分的几何补录，导出每帧主路径采样区域及端点裁剪前/后ROI。该补录不选规则、不用于调参。离线状态默认零值只在已执行条件中解释；未访问候选的hits/tail/shared在导出CSV中为null。

DEVELOPMENT首阶段分布（76可评分）：{dict(dc)}。
VALIDATION_ONLY首阶段分布（35可评分）：{dict(vc)}。
NONE只指≤10px对照容差，不等于生产验收通过。INDETERMINATE不计作已定位根因；所有分类均保留证据层次。

## 可确认的实现事实

独立端点ROI由固定参考origin/spacing经tip_transform放置，并不跟随当前可见裂纹长度扩展。DP可从任意列开始；真实峰列表、访问顺序、长度/支持率/尾端/前向材质/竞争路径拒绝均已导出。主路径Frangi与端点局部暗线/参考score是不同链路；R05差分另列，不用于生产归因。非空局部路径被同时置为tip/path_valid/terminal，不能视为独立物理真实性审计。

端点主变换、实际ROI、主路径采样网格多边形、参考匹配分支与局部有效mask、完整score/gains/back、真实候选以及最终原图路径均保留。额外用完全相同的原生localReference函数重算，导出逐24px模板相关值、票数、一致性及拒绝原因，并核对registered float图逐位hash相同。主路径完整Frangi数组未导出，它不决定独立端点；没有把人工路径或替代响应冒充算法路径。

## 隔离反事实

{len(cf)}个分支，限四开发组非参考选帧；顺序回放全部1565帧形成状态后才离线测量。CF1固定变换、将ROI几何宽高各扩大2倍并裁图；不接收GT。CF2固定实际ROI/方向，仅用主路径变换导出的drift替换局部参考配准先验；主路径变换不是独立真值，不能因改善就认定配准已解决。CF3仅旁路竞争不相连路径的整帧拒绝，保留其他门。每次恢复控制状态，正常D1逐帧与原D0哈希一致。CF4为74例stateless原生DP单变量探针：只将reference-eroded门无效像素(reason2)的score替为当前valley，ROI、DP和终止阈值全部不变；原始score控制输出与D0路径逐点一致。额外远离GT的候选单列，不冒充真实误报。

CF1采用标签无关通用扩窗，并在比较器事后检查是否包入GT；重点三类失败的GT原本已在ROI内，因此扩窗结果不支持“ROI太小是共同根因”。四个重点帧另作初始点统一+2%间距x平移的完整前缀回放，保存真实tip transform与ROI作T2-A敏感性对照；这不是每个新物理选点的真实上游轨迹，T2-B-real仍NOT_VERIFIED。没有模型训练、标签拟合、自动阈值搜索，验证组没有反事实。

## 去留

R05D_DIAGNOSIS=PARTIAL：实现事实、可达性查询与局部干预结果可审计；“全链路物理根因完全确认”未成立。FIRST_FAILURE_STAGES见逐帧表，不能用统一G4替代。PRODUCTION_REPLACEMENT=NO。

详见[root_cause_report.md](root_cause_report.md)、[全120帧图册](R05D_G0_G5_Failure_Gallery.html)、[逐帧可达性](tip_reachability_per_frame.csv)、[反事实](counterfactual_results.csv)、[性能](performance_report.md)、[验收矩阵](acceptance_matrix.csv)。所有六组历史曝光，不称未知外部测试。
'''
 (OUT/'development_report.md').write_text(report,encoding='utf8')
 table='|组|版本|N非参考|P50|P95|P99|max|>50ms|\n|---|---|---:|---:|---:|---:|---:|---:|\n'+'\n'.join(f"|{r['dataset_id']}|{r['variant']}|{r['n']}|{r['p50']:.2f}|{r['p95']:.2f}|{r['p99']:.2f}|{r['max']:.2f}|{r['over50']}|" for r in perf)
 (OUT/'performance_report.md').write_text('# 性能边界\n\nCPU '+read(OUT/'frozen_manifest.json')['cpu']+'，原生4线程，OpenCV4.4/MSVC v142 /O2 /fp:precise。计时仅内存图像CrackV4Process调用到返回，不含解码、SHA、JSON/map导出或渲染；首帧GetBaseline缓存查询全部排除，初始化另属创建成本。A0/D0交错顺序、D0有采集开销，不能据此推断插桩上线成本或目标i7已达标。CPU_50MS=FAIL。\n\n'+table,encoding='utf8')
 (OUT/'equivalence_report.md').write_text('# A0/D0逐帧严格等价\n\nPASS：2647/2647，同原图SHA、同初始化/当前锚点、同flags3572/SHADOW1/terminal1/refine=true。规范化只删除 *_ms 计时字段；native JSON、geometry JSON及完整formal/raw_path采用精确数值比较，不使用容差。参考查询单列，不作为推断耗时。每组一实例，完整序列无抽帧重置。D1正常输出另与开发组1565条原哈希一致。\n\nD0只读插桩未改变门；D1的CF2固定ROI改动只在R05D_OFFLINE编译分支，D0 DLL保持初次构建不变。见instrumentation_D0_initial.diff及三个replay_lock。\n',encoding='utf8')
 gates=[('R05D_EVIDENCE_COMPLETE','PASS','Required data, exact local-reference votes, candidate paths, CF, full images and logs exported; physical completeness remains bounded in development_report.md'),('A0_D0_EQUIVALENCE','PASS','2647/2647 a0_d0_equivalence.csv'),('FIRST_FAILURE_LOCALIZED','PASS','Development76 VISIBLE queried; first stage at fixed10px tolerance; G1/G4 focus causes directly traced and paired interventions recorded; root_cause_report.md'),('COORDINATE_MAPPING_VERIFIED','PASS','Four quarter turns unit-tested; internal selected/output and affine roundtrip checked; registration_trace.csv'),('NO_LABEL_LEAKAGE','PASS','Separate offline comparator; no GT native inputs; contract_tests.json'),('VALIDATION_ONLY_POLICY','PASS','Classifier locked before new VAL replay; no VAL CF; diagnosis_frozen_before_validation.json'),('CPU_50MS','FAIL','A0 non-reference calls exceed50ms; performance_report.md'),('PRODUCTION_REPLACEMENT','BLOCKED','Diagnosis-only round; no production change')]
 gates += [('Gate0_DATA_BASELINE','PASS','Frozen policy/input/source; 2647 identical outputs; frozen_manifest.json'),('Gate1_DEV_COVERAGE','PASS','80 selections,76 visible/4 uncertain; same timeline; tip_reachability_per_frame.csv'),('Gate2_ISOLATED_INTERVENTIONS','PASS','302 branches across four development groups; successes and failures retained; counterfactual_results.csv'),('Gate3_STATE_AND_50MS','FAIL','State/denominators preserved, but 2452/2641 A0 calls exceed50ms; performance_summary.csv'),('Gate4_PRODUCTION_RELEASE','BLOCKED','Only a next-round research plan; next_patch_plan.md')]
 save(OUT/'acceptance_matrix.csv',[dict(gate=g,status=s,evidence=e) for g,s,e in gates])
 (OUT/'next_patch_plan.md').write_text('# 后续只建议一个局部研究补丁\n\n当前：NO_PRODUCTION_PATCH_RECOMMENDED；不能直接上线CF1/CF3/CF4。\n\nR05-E候选：在roi_tip.inc证据生成层，将“参考不可用”与“当前图没有暗线证据”分离；只在参考无效像素保留一个独立标记的当前图候选通道，暂不赋予terminal/observed，不修改ROI和既有阈值。\n\n实证：CT2/395因0个相关票失去reference，CF4使10px附近峰从0变1；GROUP_A/504可恢复7.12px附近候选输出。反证：CT2仍误选238.55px之外位置，开发组H仍错279.61px；GROUP_A候选数3→448。故该补丁只解决一部分候选可达性，不能解决路径身份或直接确认，安全终止/候选选择仍需独立证据。\n\n风险：纹理划痕和噪点候选增加、闭合/已存在裂纹误接纳、当前CT3正确点被竞争干扰。必须回归GROUP_A/CT2/开发组H/CT3完整1565帧和全部80选帧（76可评分），保留无输出分母，检查原有3/5/10px正确案例、初始点扰动与当前点解耦。规则冻结后再一次性只读验收验证组C/三点弯完整1082帧和40选帧；不能依据验证分数选阈值。人工标签只作核验，不能训练/拟合；排除组X禁止。\n',encoding='utf8')
 (OUT/'reproduction_commands.md').write_text('''# 复现命令

在项目根运行，Python D:/ProgramData/anaconda3/python.exe。原运行已封存，复跑先在common.py将OUT/GEN/BUILD设为新唯一output目录，不覆盖本轮。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/prepare.py
& D:/CMake/bin/cmake.exe -S research/uctt_r05d -B output/build/uctt_r05d -G "Visual Studio 17 2022" -A x64 -T v142
& D:/CMake/bin/cmake.exe --build output/build/uctt_r05d --config Release -- /m:1 /nodeReuse:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/contracts.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/replay.py dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/analyze.py dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/local_audit.py dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/analyze.py dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/replay.py cf
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/evidence_probe.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/initialization_probe.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/counterfactuals.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/replay.py val
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/local_audit.py val
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/analyze.py val
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/geometry_completion.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/deliver.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/crossgroup.py
```

重点帧不能单图重置：复现所属完整组后查看traces/<group>__<frame:06d>.json。只看已有重点帧可直接打开R05D_G0_G5_Failure_Gallery.html#ct2__000395、#group_h__000078、#group_a__000504、#ct3__000065。全部候选在JSON中；NPZ原数组供进一步离线审计。
''',encoding='utf8')
 # Package actual referenced images, trace JSON and reports; maps remain in run directory.
 files=[p for p in OUT.rglob('*') if p.is_file() and (p.parent.name in ['images','source_evidence','traces'] or p.parent==OUT and p.suffix in ['.md','.html','.csv','.jpg'])]
 with zipfile.ZipFile(OUT/'R05D_visual_evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,p.relative_to(OUT).as_posix())
 write(OUT/'visual_qa.json',dict(cases=len(cards),key_montages=len(FOCUS),images=240,zip_entries=len(files),relative_images_exist=True))
 # A video of every case accompanies the complete, independently viewable gallery.
 ffmpeg=ROOT/'third_party/ffmpeg/ffmpeg.exe';video=OUT/'R05D_Failure_Stage_Results.mp4'
 with (OUT/'logs/video.log').open('w') as log:
  process=subprocess.Popen([str(ffmpeg),'-y','-hide_banner','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1600x1000','-framerate','5','-i','-','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],stdin=subprocess.PIPE,stderr=log)
  for r in selected:
   data=Image.open(OUT/'images'/f"{r['dataset_id']}__{int(r['frame_id']):06d}.jpg").convert('RGB').tobytes()
   for _ in range(10):process.stdin.write(data)
  process.stdin.close();assert process.wait()==0
 decoded=subprocess.run([str(ffmpeg),'-v','error','-i',str(video),'-f','null','NUL'],capture_output=True,text=True);assert decoded.returncode==0 and not decoded.stderr
 write(OUT/'video_qa.json',dict(full_decode='PASS',frames=1200,seconds=240,cases=120,sha256=sha(video)))
 print('DELIVERY COMPLETE',dict(dc),dict(vc),flush=True)
if __name__=='__main__':main()
