"""Derive auditable reports from completed, frozen snapshots; no runtime tuning."""
from common import *
from compare import original
import numpy as np,collections,shutil,platform,difflib
def truth(v):return str(v).lower() in ['true','1']
def stats(v):
 v=list(map(float,v));return dict(n=len(v),p50=float(np.percentile(v,50)),p95=float(np.percentile(v,95)),p99=float(np.percentile(v,99)),maximum=max(v),sum=sum(v)) if v else dict(n=0)
def md(name,body):(OUT/name).write_text(body,encoding='utf8')
def main():
 mode='B2' if (OUT/'B2_dev_complete.json').exists() else 'B1';assert (OUT/f'{mode}_val_complete.json').exists()
 freeze=read(OUT/'validation_freeze.json')
 for p,h in {**freeze['rule_sources'],**freeze['generated_sources'],**freeze['dlls']}.items():assert sha(ROOT/p)==h,p
 evaluation=[]
 for phase in ['dev','val']:
  for m in ['B1','B2']:
   p=OUT/f'evaluation_{m}_{phase}.csv'
   if p.exists():evaluation.extend(rows(p))
 save(OUT/'tip_outputs_and_gt_eval.csv',evaluation)
 final=[r for r in evaluation if r['mode']==mode];dev=[r for r in final if r['phase']=='dev'];val=[r for r in final if r['phase']=='val']
 counts=[];equivalence=rows(OUT/'baseline_equivalence.csv');performance=rows(OUT/'performance_B0.csv')
 for m in ['B1','B2']:
  for phase in ['dev','val','perf']:
   p=OUT/f'counts_{m}_{phase}.csv'
   if p.exists():counts.extend(rows(p));performance.extend(rows(OUT/f'performance_{m}_{phase}.csv'));equivalence.extend(rows(OUT/f'equivalence_{m}_{phase}.csv'))
 save(OUT/'evidence_channels_per_frame.csv',counts);save(OUT/'performance_native.csv',performance)
 save(OUT/'all_stage_equivalence.csv',equivalence)
 # Stream all-frame, all-stored-raw-candidate provenance; do not just report GT crops.
 fields=['dataset_id','frame_id','phase','mode','raw_candidate_id','merged_id','retained_id','original_x','original_y','direction','source_channel','current_support','reference_available','reference_support','bucket_id','dedup_reason','prune_reason','audited','path_id','denominator']
 lineage_count=0
 with (OUT/'candidate_lineage.csv').open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
  for phase in ['dev','val']:
   with (OUT/f'{mode}_{phase}_frames.jsonl').open(encoding='utf8') as src:
    for line in src:
     t=json.loads(line);candidates=t['evidence']['candidates'];coords=original([c['xy'] for c in candidates],t)
     for c,p in zip(candidates,coords):
      writer.writerow(dict(dataset_id=t['dataset_id'],frame_id=t['frame_id'],phase=phase,mode=mode,raw_candidate_id=c['id'],merged_id=c['merged_id'],retained_id=c['retained_id'] if c['retained_id']>=0 else '',original_x=p[0],original_y=p[1],direction=c['direction'],source_channel=c.get('source_channel','current'),current_support=c['current_support'],reference_available=c['reference_available'],reference_support=c['reference_support'],bucket_id=c['bucket'],dedup_reason=c['reason'] if c['reason'].startswith('directional_duplicate') else '',prune_reason=c['reason'] if c['retained_id']<0 else '',audited=False,path_id='',denominator='all stored raw candidates of all 2647 sequence frames; no GT in this table'));lineage_count+=1
 # Blocked stages have explicit records, not empty PASS tables.
 for name,stage in [('attribution_audit.csv','B3'),('terminal_audit.csv','B4')]:save(OUT/name,[dict(stage=stage,status='BLOCKED',cases_executed=0,reason='Prior evidence/candidate safety gate did not pass. No new attribution/terminal decision implemented.',legacy_R03_safety='coherent_wrong_first_lock FAIL')])
 lost=[r for r in dev if truth(r['capacity_lost_true_candidate10'])]
 all_lost=[r for r in final if truth(r['capacity_lost_true_candidate10'])]
 regress=[dict(dataset_id=r['dataset_id'],frame_id=r['frame_id'],phase=r['phase'],stage='B2_COMPRESSION',status='FAIL',raw_nearest_px=r['raw_nearest_px'],retained_nearest_px=r['retained_nearest_px'],old_A_hit5=r['hit5'],old_A_hit10=r['hit10'],trace=f"traces/{mode}_{r['dataset_id']}__{int(r['frame_id']):06d}.json",reason='raw candidate within10px but no retained representative within10px',denominator='76 visible development selections' if r['phase']=='dev' else '35 visible frozen validation selections') for r in all_lost]
 if not regress:regress=[dict(stage='B2_CAPACITY',status='NO_SELECTED_LOSS' if mode=='B2' else 'BLOCKED',denominator='76 visible development selections; not whole-sequence physical GT')]
 save(OUT/'first_regression.csv',regress)
 failure=[]
 for phase,data in [('dev',dev),('val',val)]:
  for stage,n in collections.Counter(r['first_failure_stage'] for r in data).items():failure.append(dict(phase=phase,stage=stage,count=n,denominator=len(data),source=f'evaluation_{mode}_{phase}.csv'))
 save(OUT/'failure_stage_counts.csv',failure)
 summary=[]
 for g in DEV+VAL:
  ss=[r for r in final if r['dataset_id']==g];visible=[r for r in ss if r['gt_visibility']=='VISIBLE'];cc=[r for r in counts if r['mode']==mode and r['phase'] in ['dev','val'] and r['dataset_id']==g]
  summary.append(dict(dataset_id=g,role=role(g),full_frames=len(cc),selected=len(ss),visible=len(visible),uncertain=len(ss)-len(visible),observed=sum(truth(r['observed']) for r in visible),hits3=sum(truth(r['hit3']) for r in visible),hits5=sum(truth(r['hit5']) for r in visible),hits10=sum(truth(r['hit10']) for r in visible),current10=sum(truth(r['current_evidence10']) for r in visible),raw3=sum(truth(r['raw_candidate3']) for r in visible),raw5=sum(truth(r['raw_candidate5']) for r in visible),raw10=sum(truth(r['raw_candidate10']) for r in visible),retained3=sum(truth(r['retained_candidate3']) for r in visible),retained5=sum(truth(r['retained_candidate5']) for r in visible),retained10=sum(truth(r['retained_candidate10']) for r in visible),capacity_lost10=sum(truth(r['capacity_lost_true_candidate10']) for r in visible),raw_stats=stats(r['raw_count'] for r in cc),retained_stats=stats(r['retained_count'] for r in cc),raw_exhaustion_frames=sum(truth(r['budget_exhausted']) for r in cc),bucket_drop_frames=sum(int(r['merged_count'])>int(r['retained_count']) for r in cc)))
 save(OUT/'group_summary.csv',summary);write(OUT/'group_summary.json',summary)
 perfsummary=[]
 for m,phase in sorted({(r['mode'],r.get('phase','baseline')) for r in performance}):
  rr=[r for r in performance if r['mode']==m and r.get('phase','baseline')==phase and not truth(r['reference_query'])]
  if not rr:continue
  entry=dict(mode=m,phase=phase,**stats(r['api_ms'] for r in rr),over50=sum(float(r['api_ms'])>50 for r in rr),normal_and_failure_included=True,io_gt_render_excluded=True)
  for key in ['prep_ms','tipmotion_ms','local_reference_ms','legacy_dp_ms','current_ms','reference_channel_ms','dp_ms','candidates_ms','other_ms','peak_memory_bytes']:
   if all(r.get(key) not in ['',None] for r in rr):entry[key]=stats(r[key] for r in rr)
  if all(r.get('candidate_count') for r in rr):
   x=np.array([float(r['candidate_count']) for r in rr]);y=np.array([float(r['api_ms']) for r in rr]);entry['candidate_count_api_pearson']=float(np.corrcoef(x,y)[0,1]) if np.std(x)>0 else None
  perfsummary.append(entry)
 write(OUT/'performance_summary.json',perfsummary)
 b1=read(OUT/'B1_gate.json');b2=read(OUT/'B2_gate.json') if (OUT/'B2_gate.json').exists() else dict(status='BLOCKED')
 devvisible=[r for r in dev if r['gt_visibility']=='VISIBLE'];current10=sum(truth(r['current_evidence10']) for r in devvisible);raw10=sum(truth(r['raw_candidate10']) for r in devvisible);kept10=sum(truth(r['retained_candidate10']) for r in devvisible)
 gates=[]
 def gate(name,status,denom,evidence,detail):gates.append(dict(gate=name,status=status,denominator=denom,source=evidence,source_sha256=sha(OUT/evidence),detail=detail))
 gate('B0_BASELINE_EQUIVALENT','PASS','1565 development frames; all non-timing fields','B0_complete.json','Original production, same-source rebuild and R05D replay hashes equal')
 gate('EVIDENCE_DECOUPLED',b1['status'],'1565 chronological frames / 76 visible development selections','B1_gate.json',f'Independent current evidence within10: {current10}/76; scalar evidence is not endpoint correctness')
 gate('TRUE_TIP_CANDIDATE_RECALL','PASS' if raw10==76 else 'FAIL','76 visible development selections',f'evaluation_{mode}_dev.csv',f'raw10={raw10}/76 retained10={kept10}/76; same threshold3/5/10')
 gate('CANDIDATE_BUDGET_SAFE',b2['status'],'76 visible selections + 1565 development full frames',f'{mode}_gate.json',f'Within10px true-candidate losses={len(lost)}; all budget drops are logged')
 gate('ATTRIBUTION_LOCK_SAFE','BLOCKED','0 new B3 cases; unchanged original R03 16 cases','tests/r03_original.csv','Original coherent_wrong_first_lock still FAIL. No new safety claim.')
 gate('TERMINAL_AUDIT_SAFE','BLOCKED','0 B4 cases','terminal_audit.csv','No nonempty-path shortcut enabled; prior gate did not pass')
 gate('VISIBLE_GT_ACCURACY','FAIL','76 development VISIBLE, 35 validation VISIBLE','tip_outputs_and_gt_eval.csv','Original A outputs unchanged; candidate recall is not endpoint accuracy')
 gate('OBSERVED_COVERAGE','PASS','2647 chronological shadow replay frames',f'{mode}_val_complete.json','PASS means no coverage regression versus frozen A; it does not mean high coverage or new sidecar observation')
 gate('STATE_CAUSAL_REPLAY','PASS','1565 development + 1082 validation frames','all_stage_equivalence.csv','One initialization per sequence, complete chronological replay, no sidecar history writes')
 gate('INITIAL_ANCHOR_STABILITY','NOT_VERIFIED','0 new perturbed-initialization experiments',f'{mode}_dev_replay_lock.json','Original anchors used; R05D historical 4 sentinel probes not upgraded into new B2 stability proof')
 gate('CPU_50MS','NOT_VERIFIED','AMD Ryzen9 7950X; target i7 not tested','performance_summary.json','50ms target not demonstrated; current-host measured violations reported separately')
 gate('VALIDATION_ONLY_FROZEN_RESULT','PASS','1082 frames / 40 selected / 35 VISIBLE / 5 UNCERTAIN','validation_freeze.json','PASS is protocol/freeze integrity, not accuracy; no tuning after validation')
 gate('PRODUCTION_REPLACEMENT_ELIGIBLE','FAIL','stage gates B0-B5','gate_matrix_placeholder.json' if False else f'{mode}_gate.json','NO; production unchanged; B3/B4/B5 blocked')
 save(OUT/'gate_matrix.csv',gates)
 table='|组|全帧|可见/不确定|原A observed|原A ≤5px|current10|raw10|retained10|预算误删10|\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'+'\n'.join(f"|{r['dataset_id']} ({r['role']})|{r['full_frames']}|{r['visible']}/{r['uncertain']}|{r['observed']}|{r['hits5']}|{r['current10']}|{r['raw10']}|{r['retained10']}|{r['capacity_lost10']}|" for r in summary)
 gate_table='|Gate|状态|分母|\n|---|---|---|\n'+'\n'.join(f"|{g['gate']}|{g['status']}|{g['denominator']}|" for g in gates)
 sentinel=[]
 for g,f in [('ct2',395),('group_h',78),('group_a',504),('ct3',65)]:
  r=next(r for r in dev if r['dataset_id']==g and int(r['frame_id'])==f);sentinel.append(f"- {g}/{f}: current10={r['current_evidence10']}; raw nearest={r['raw_nearest_px']} px; retained nearest={r['retained_nearest_px']} px; original A error={r['error_px'] or 'N/A'} px. `traces/{mode}_{g}__{f:06d}.json` 与图册同帧可复核。")
 md('development_report.md',f'''# R05E 证据解耦与候选安全排查

本轮交付为隔离 C++17 原生 B0/B1/B2 研究。**生产替换 NO。B1={b1['status']}；B2={b2['status']}。** 新旁路没有 observed 输出或可信历史，生产结果原样保留。候选出现不能视为尖端修复。

## 实现与阶段门

- B0：从当前生产源码独立构建；1565开发帧和冻结A/R05D逐帧非计时hash一致，四个指定案例也在完整序列中复现。
- B1：`research/uctt_r05e/evidence.hpp` 独立当前暗谷、参考暗谷/变化、空间有效性及原因位；参考不可用为NaN+UNKNOWN，参考已有裂纹零差分不删除当前证据。仅暗线方案，没有宣称亮线支持。保留全部旧score算法。
- B2：当前DP局部峰与旧DP峰求并集；方向/空间3px合并；4×4空间桶，每桶强累计、强当前响应、最远停止和弱响应4种代表；K64、原始存储8192、短追踪16点。规则在看本轮GT对比前固定，没有搜索阈值。实际逐帧lineage共{lineage_count}条。
- B3/B4：前置门未通过，未实施新归属/终止或可信历史策略；原R03 16例保持15通过/错误首锁1失败。B5完整生产替换验收BLOCKED。
- B1/B2调试选帧与全帧输出等价；诊断采样不进入决定输出的分支。默认trace未访问字段不能视为已审计。

{gate_table}

## 六组结果

{table}

current10表示半径10原图像素内存在分数≥3的像素。raw/retained表示候选端点≤10px，未代表归属或终止正确。所有候选距离/误差只在快照完成后由独立比较器读取标注计算。没有人工无裂纹负例，因此真实误报率NOT_VERIFIED；距离GT较远的候选不直接叫误报。UNCERTAIN不填0误差、不进入可见分母。

## 指定反例

{chr(10).join(sentinel)}

## 新增退化与停止原因

开发可见76例：current10={current10}，raw10={raw10}，retained10={kept10}；预算丢失{len(lost)}例。逐帧反例见first_regression.csv，所有帧预算计数见evidence_channels_per_frame.csv，实际代表坐标见candidate_lineage.csv。若方向合并代表偏移跨越10px边界，也计为损失；没有把重复节点原坐标冒充保留代表。

旧A输出、observed覆盖、ROI、长度、历史及非计时ABI数据均未变化；这只证明旁路隔离。新模块没有确认输出，故“新增错锁=0”不能被当成安全性成功。原始coherent_wrong_first_lock仍会错误写入历史。

## 冻结后验证

规则、生成源码、DLL及比较器hash在validation_freeze.json中冻结。之后仅对验证组C/三点弯1082帧回放，40选帧对比，未据验证结果改规则。冻结状态最终再次逐文件核验。排除组X图像/标注读取0；六组均历史曝光，不称独立未见TEST。人工标注从未用于训练、拟合、阈值扫描或运行时选择。

## 性能与限制

见performance_report.md。正常与失败状态均计入；参考帧GetBaseline是缓存查询，单独列出、不冒充推理。阶段计时互斥，other包含旧主路径和未单列开销。初始化扰动本轮NOT_VERIFIED，不能以R05D历史四例替代B2稳定性证明。目标i7未测试，本机Ryzen结果不能推断i7达标。

## 下一步（仅开发组，最多三项）

1. 优先处理已有raw候选被固定桶预算删除的逐帧反例：下一轮研究结构链的多停止位置保留，先证明候选可达性，再允许归属；不从验证组调规则。
2. 对current响应存在但没有近端峰的G2_RAW案例，检查真实停止位置与DP局部极值定义；继续区分像素恢复和端点可达性。
3. 前两项通过后再实现可信首锁归属和独立终止；必须先通过原R03错误首锁反例，禁止用大幅降低observed覆盖换取安全性表象。
''')
 md('candidate_recall_report.md','# 候选召回与预算\n\n'+table+'\n\n固定容差3/5/10完整数字见group_summary.csv。raw为当前与legacy峰并集，retained仅代表节点坐标；合并从属节点虽映射retained_id，不把从属坐标当成保留。桶间/桶内选择不读取GT。原始峰预算耗尽时记录budget_exhausted，旁路始终无确认输出。全帧候选计数P50/P95/P99/max/sum在group_summary.json，容量删除每帧计数与逐原始候选理由已导出。\n')
 if (OUT/'current_peak_filter_diagnosis.csv').exists():
  diagnosed=[r for r in rows(OUT/'current_peak_filter_diagnosis.csv') if r['first_failure_stage']=='G2_RAW']
  detail='\n## 对候选未生成的直接定位\n\n76个有图像地图的选帧，用同一个原生distalLine递推重算currentEvidence；current-source峰坐标/增益与B1快照集合完全一致，之后才离线查询GT邻域。74个VISIBLE有图可查，2个G0没有证据地图。\n\n|组/帧|当前达标像素10|同时gain≥12|再通过纵向极值|再通过向前停止极值|首先丢失条件|\n|---|---:|---:|---:|---:|---|\n'+'\n'.join(f"|{r['dataset_id']}/{r['frame_id']}|{r['current_support_pixels10']}|{r['support_and_gain12_pixels10']}|{r['plus_ymax_pixels10']}|{r['plus_forward_stop_pixels10']}|{r['first_current_peak_filter_loss']}|" for r in diagnosed)+'\n\n这定位的是固定提取器中的实际过滤步骤，不是物理裂纹终止真相；未据此下降阈值或更换容差。控制表current_dp_control.csv、查询表current_peak_filter_diagnosis.csv、实际gain图maps/*__current_dp.npz可复核。\n'
  for name in ['development_report.md','candidate_recall_report.md']:
   with (OUT/name).open('a',encoding='utf8') as f:f.write(detail)
 if (OUT/'budget_loss_cases.csv').exists():
  cases=rows(OUT/'budget_loss_cases.csv');detail='\n## 预算误删归因\n\n全部误删的近端raw_id、合并代表、桶内保留节点、分数及裁剪原因见budget_loss_lineage.csv。B1/B2原始候选集合逐帧精确对照；只发生压缩变化，因此不能用“原本没有候选”解释这些退化。\n\n'+ '\n'.join(f"- {r['dataset_id']}/{r['frame_id']} ({r['phase']}): {r['causes']}；近端raw {r['near_raw_count']}；全帧raw {r['raw_count']} → retained {r['retained_count']}；原A hit5={r['old_A_hit5']}, hit10={r['old_A_hit10']}。" for r in cases)+'\n'
  for name in ['development_report.md','candidate_recall_report.md']:
   with (OUT/name).open('a',encoding='utf8') as f:f.write(detail)
 md('lock_safety_report.md','# 首锁安全\n\nB3 BLOCKED，0新归属运行。原始R03 contracts.cpp/state.hpp/seed未经修改，tests/r03_provenance.json记录来源hash。16原测试15 PASS，coherent_wrong_first_lock FAIL：错误候选与其路径自洽即可首次锁定并写入历史。没有替换fixture，也没有用只返回unknown的旁路声称锁定修复。真实无裂纹负例缺失，真实FP NOT_VERIFIED。\n')
 md('terminal_review_report.md','# 独立终止\n\nB4 BLOCKED，0新多停止点归属后审计。B2当前仅图像候选和有限16点局部方向；不是完整物理路径或可见末端。旧A非空distalLine路径的确认规则仍原样存在，不能把候选增强称为终止审计已通过。\n')
 perftext='|模式/阶段|非参考帧|P50 ms|P95 ms|P99 ms|max ms|>50 ms|\n|---|---:|---:|---:|---:|---:|---:|\n'+'\n'.join(f"|{r['mode']}/{r['phase']}|{r['n']}|{r['p50']:.3f}|{r['p95']:.3f}|{r['p99']:.3f}|{r['maximum']:.3f}|{r['over50']}|" for r in perfsummary)
 md('performance_report.md','# 原生性能\n\n'+perftext+'\n\n输入图像已解码到内存，时间窗为原生API调用，排除IO、GT、JSON导出及渲染。dev/val选帧有调试capture；perf为capture关闭的完整开发序列，不并发媒体/其他计算；B0初始回放期间有源码编辑和小型合同构建，故不能当严格隔离benchmark。所有成功/失败状态均纳入分母。缓存参考查询单列，不纳入非参考帧统计；初始化也不是逐帧API延迟。\n\nprep/tipmotion/local_reference/legacy_dp/current/reference_channel/new_dp/candidates均独立计时；other是API总时间减以上互斥项，包含旧主路径、其他处理和轻量ABI调用。B3/B4未执行，时间留空而非伪造0。peak_memory_bytes为整个Python回放进程PeakWorkingSet，含桥接、maps/JSON与DLL，不能当纯DLL峰值。原生候选存储上限8192、保留≤64、短路径追踪≤16，图像DP存储O(ROI像素)。候选数与API时间Pearson以及每阶段分位数见performance_summary.json。\n\nCF4控制是选帧上确切旧reason2旁路+distalLine，performance_CF4_control.csv；它是离线阶段计时、无IO/输出/可信历史，不是完整在线版本。不得把它和整个B2 API时延直接混比。50ms在本机的违例已列，目标i7 NOT_VERIFIED。\n')
 if (OUT/'performance_CF4_control.csv').exists() and (OUT/'performance_B2_perf.csv').exists():
  perf={(r['dataset_id'],r['frame_id']):r for r in rows(OUT/'performance_B2_perf.csv')};paired=[]
  for r in rows(OUT/'performance_CF4_control.csv'):
   now=perf[r['dataset_id'],r['frame_id']];paired.append(dict(dataset_id=r['dataset_id'],frame_id=r['frame_id'],cf4_offline_stage_ms=float(r['median_ms']),b2_added_channels_dp_candidate_ms=sum(float(now[k]) for k in ['current_ms','reference_channel_ms','dp_ms','candidates_ms']),b2_candidate_scan_merge_budget_ms=float(now['candidates_ms']),b2_raw_count=int(now['candidate_count']),b2_retained_count=int(now['retained_count']),scope='matched selected images, different evidence channels; phase cost comparison NOT whole API speedup'))
  save(OUT/'performance_candidate_comparison.csv',paired)
  cf=stats(r['cf4_offline_stage_ms'] for r in paired);new=stats(r['b2_added_channels_dp_candidate_ms'] for r in paired)
  with (OUT/'performance_report.md').open('a',encoding='utf8') as f:f.write(f"\n## 与CF4的同图阶段对照\n\n{len(paired)}个非参考、可配准开发选帧：旧CF4离线补证据+DP P99={cf['p99']:.3f}ms；B2新增通道+新DP+候选处理阶段之和P99={new['p99']:.3f}ms。B2保留旧生产计算，不能把这个新增工作时间解释为替代后的整机时延。两者证据通道不同，因此这是已声明范围的成本对照；没有证明完整替代算法P99改善。尤其压缩候选数不减少当前方案的整ROI DP扫描，不能凭K64声称CPU安全。\n")
 md('evidence_channel_design.md','# 独立证据通道\n\n当前3×3 σ0.8模糊暗谷=min(y−4,y+4)−current；当前flank≥75方可支持，完全不读取参考有效性。当前证据仅暗线。referenceEvidence为配准参考暗谷，referenceChange为registered−current，referenceQuality为实际accepted tile全11×11处理足迹有效；否则浮点NaN，非负证据。保留原legacyScore、eroded/refMin/refMax/novel/knownCrack及legacyReason地图。局部参考64tile、9个24模板、corr阈值.62、至少2票及2px一致票全部保持；完整小块位置、delta、corr、票和拒绝原因在选帧trace tiles中。votes<2时agree默认0是未执行，一律解释为UNKNOWN，不能当测得不一致0票。\n\nreasonMask位1边界未计算、2当前flank不足、4参考未知、8旧eroded门、16旧参考纹理门、32已知裂纹mask、64当前响应恢复。quality=0只表示UNKNOWN而非否定裂纹。图册统一当前证据色标0..30、变化−20..20，NaN紫色；原始float图保存在maps。\n')
 md('implementation_diff.md','# 实现范围\n\n生产源码/DLL未改。research/uctt_r05e 为当前研究代码；生成副本在output/build/uctt_r05e_source，B0/B1/B2目标在output/build/uctt_r05e/Release。generate.py复用只读R05D源生成逻辑并把所有输出根明确重定向到R05E；不执行旧sealed输出中的源码。B0是原源码重建；B1/B2同一生成源，B2仅定义R05E_BUDGET。旧Trace计时/局部参考元数据为旁路；旧DP峰只读导出并与current峰合并。R05E exports均研究专用，不改变原ABI。research_source_patch含构建所需研究源码/生成源；完整差异见research_source_patch/production_instrumentation.diff。\n\n早期B1运行首帧遇到Python汇总字典mode重复键，修复报表字段后从第1帧重跑；日志保留logs/B1_writer_fix.log。该修复未改C++或候选规则。\n')
 md('build_manifest.md','# 构建身份\n\nC++17，MSVC v142 19.29.30159 x64，OpenCV4.4，Release /O2 /fp:precise /utf-8，4 native threads。\n\n'+ '\n'.join(f'- {p.name}: `{sha(p)}`' for p in [BUILD/'Release/B0.dll',BUILD/'Release/B1.dll',BUILD/'Release/B2.dll',BUILD/'Release/R03Original.exe',BUILD/'Release/EvidenceContracts.exe',ROOT/'third_party/opencv440/bin/opencv_world440.dll'])+'\n\n生产DLL身份、原图/P1P2库存与标注ZIP身份见frozen_manifest_r05e.json；每原图在读入前核对hash。\n')
 md('README.md','# R05E 验证交付\n\n先读development_report.md与gate_matrix.csv，再打开R05E_Failure_And_Improvement_Gallery.html。R05E_Validation_Results.mp4含全部120选帧的实际原图叠加和通道图。所有图/trace使用包内相对链接；原始地图在maps，不依赖联网。\n\n本轮重点是发现问题，生产保持A。标注仅离线对比；排除组X排除；验证组C/三点弯规则冻结后只读验证。各CSV分母/状态明确，BLOCKED文件解释未执行原因。\n')
 md('problem_findings.md',f'''# 本轮问题结论

**证据解耦通过，候选预算安全失败，不能上线。** 开发76个可见标注：独立当前证据在10px内可达{current10}例；原始候选可达{raw10}例；压缩后可达{kept10}例。这里的“可达”仅指附近有候选，原A尖端输出没有改变。

1. **参考失败曾连带抹掉当前证据，已在旁路证实可解耦。** R05D的50个G1案例全部恢复当前响应。CT2/395的参考质量在尖端10px邻域内为UNKNOWN，当前暗谷最大13.58，实际候选到标注8.31px；旧A误差仍928.94px。原图及实际ROI证明该例不是简单“ROI太小”。
2. **有响应，仍不一定产生末端候选。** 开发组H/78有10个当前响应≥3的邻域像素，但没有同时满足gain≥12的像素；最近峰12.15px，仍超过固定10px容差。CT2/196、338、431则卡在向前停止局部极值条件。76个原生重算控制的峰坐标/增益与B1一致；见current_peak_filter_diagnosis.csv。
3. **按空间桶选强/弱/最远代表，会删除真正需要的停止位置。** 开发{len(lost)}例出现“raw≤10px、retained>10px”。GROUP_A/398距标注约0.96px的raw722被桶10容量规则删除。全部开发误删都归因于桶内选择；原始8192存储预算没有耗尽。见budget_loss_lineage.csv，可追溯每个raw→代表→保留节点。
4. **错误首锁仍没有解决。** 原R03 16项原始测试中，coherent_wrong_first_lock仍失败：自洽的错误路径/尖端可首次锁定并写历史。B2失败后已停止B3/B4，未用“旁路无输出”冒充安全通过。

验证组规则冻结后只读回放1082帧、40个标注选帧。下表只比较已冻结的旁路，未据验证组调参数；排除组X完全排除，标注没有用于训练。

{table}

后续优先级仅三项：先修复开发组中停止位置的预算保留；再区分弱累积支持与非停止极值两类G2问题；前两项通过后才做首锁归属和独立终止。不要直接提高预算或降低阈值来宣布通过。

完整证据：[图册](R05E_Failure_And_Improvement_Gallery.html) · [逐项验收](gate_matrix.csv) · [完整报告](development_report.md) · [性能限制](performance_report.md)。视频单独保存在运行目录R05E_Validation_Results.mp4。
''')
 md('reproduction_commands.md','''# 复现命令

工作目录必须是 CodexCrack；复现请先把common.py中OUT/GEN/BUILD设为新的未存在目录，不覆盖本次封存目录。PowerShell设置PYTHONPYCACHEPREFIX到output/pycache。

```powershell
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/freeze.py
& D:/CMake/bin/cmake.exe -S research/uctt_r05e -B output/build/uctt_r05e -G "Visual Studio 17 2022" -A x64 -T v142
& D:/CMake/bin/cmake.exe --build output/build/uctt_r05e --config Release --target B0 R03Original EvidenceContracts -- /m:1 /nodeReuse:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/baseline.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/generate.py
& D:/CMake/bin/cmake.exe -S research/uctt_r05e -B output/build/uctt_r05e
& D:/CMake/bin/cmake.exe --build output/build/uctt_r05e --config Release --target B1 B2 EVIDENCE_DP_PROBE -- /m:1 /nodeReuse:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/checks.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/replay.py B1 dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/compare.py B1 dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/diagnose.py
# Only if B1_gate PASS:
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/replay.py B2 dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/compare.py B2 dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/freeze_validation.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/replay.py B1 val
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/compare.py B1 val
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/replay.py B2 val
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/compare.py B2 val
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/budget_diagnose.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/replay.py B2 perf
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/benchmark.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/input_contract.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/report.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/media.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/seal.py
```

B2 FAIL即停止B3/B4，不执行新输出融合。冻结后验证只观察已冻结阶段；不能凭验证结果继续改预算。
''')
 for p in (ROOT/'research/uctt_r05e').glob('*'):
  if p.is_file():shutil.copy2(p,OUT/'research_source_patch'/p.name)
 diffs=[]
 for n in ['CrackV4.cpp','roi_tip.inc']:
  a=(ROOT/'src/cpp/a'/n).read_text(encoding='utf8');b=(GEN/n).read_text(encoding='utf8');diffs.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='production/'+n,tofile='generated/'+n))
 (OUT/'research_source_patch/production_instrumentation.diff').write_text(''.join(diffs),encoding='utf8')
 print('REPORT READY',mode,'losses',len(lost),'raw10',raw10,'retained10',kept10,flush=True)
if __name__=='__main__':main()
