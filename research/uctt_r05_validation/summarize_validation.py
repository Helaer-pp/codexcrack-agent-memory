"""Score frozen outputs; no score is fed back into any detector or threshold."""
import html
from validate_annotations import *

def average(rr,key):
 values=[float(r[key]) for r in rr if r.get(key) not in ('',None)]
 return float(np.mean(values)) if values else None
def main():
 cov=rows(OUT/'path_coverage.csv');met=rows(OUT/'difference_label_comparison.csv');status=rows(OUT/'annotation_status.csv');summary=[]
 scopes=[('dataset',g) for g in sorted({r['dataset_id'] for r in status})]+[('role',r) for r in ['DEVELOPMENT','VALIDATION_ONLY']]
 for kind,name in scopes:
  group=[r for r in cov if r['dataset_id']==name] if kind=='dataset' else [r for r in cov if r['group_role']==name]
  for split in ['ALL','development','holdout']:
   rr=[r for r in group if split=='ALL' or r['original_split']==split];keys={(r['dataset_id'],r['frame_id']) for r in rr};visible=[r for r in rr if r['annotation_state']=='VISIBLE'];paired=[r for r in visible if r['paired_registration_valid']=='True']
   record=dict(scope=kind,name=name,original_split=split,group_role=rr[0]['group_role'],frames=len(rr),visible=len(visible),uncertain=sum(r['annotation_state']=='UNCERTAIN' for r in rr),paired_visible=len(paired),full_path_roi_coverage_mean=average(visible,'path_in_roi_fraction'),full_path_common_coverage_all_mean=average(visible,'path_common_fraction'),full_path_common_coverage_paired_mean=average(paired,'path_common_fraction'),transition_path_fraction_mean=average(visible,'path_transition_fraction'),tip_common_valid=sum(r['tip_common_valid']=='True' for r in visible))
   for comparison in ['PRIMARY_E1_E2','FOUR_ARM_ABLATION']:
    for tol in [3,5,10]:
     for arm in ARMS if comparison=='FOUR_ARM_ABLATION' else ARMS[:2]:
      values=[r for r in met if (r['dataset_id'],r['frame_id']) in keys and r['arm']==arm and r['comparison']==comparison and int(r['tolerance_original_px'])==tol]
      prefix=f'{comparison}_{arm}_tol{tol}';record[prefix+'_n']=sum(bool(r['path_difference_support']) for r in values);record[prefix+'_support_mean']=average(values,'path_difference_support');record[prefix+'_off_path_density_mean']=average(values,'off_path_activation_density')
   summary.append(record)
 save(OUT/'difference_group_summary.csv',summary)
 # Point scoring is separate from difference-source scoring.
 pred=rows(OUT/'production_selected_predictions.csv');plook={(r['dataset_id'],r['frame_id']):r for r in pred};manifest=rows(OUT/'active_selection_manifest.csv');pointrows=[]
 with zipfile.ZipFile(OUT/'human_annotations_six_groups_snapshot.zip') as archive:
  for r in manifest:
   require(r['dataset_id'],'comparison',uses_annotations=True);d=json.loads(archive.read(r['selected_json']));state=classify(d);p=plook[r['dataset_id'],r['frame_id']];observed=p['observed']=='True';tips=[s['points'][0] for s in d['shapes'] if s['label']=='crack_tip'];error=None
   if state=='VISIBLE' and observed:assert len(tips)==1;error=float(np.linalg.norm(np.array(tips[0])-np.array([float(p['tip_x']),float(p['tip_y'])])))
   pointrows.append(dict(dataset_id=r['dataset_id'],frame_id=int(r['frame_id']),group_role=role(r['dataset_id']),original_split=r['split'],annotation_state=state,observed=observed,predicted_x=p['tip_x'] if observed else None,predicted_y=p['tip_y'] if observed else None,human_tip_x=tips[0][0] if len(tips)==1 else None,human_tip_y=tips[0][1] if len(tips)==1 else None,error_original_px=error,within3=error<=3 if error is not None else None,within5=error<=5 if error is not None else None,within10=error<=10 if error is not None else None,score_status='OBSERVED_AND_HUMAN_VISIBLE' if error is not None else 'UNCERTAIN_EXCLUDED' if state=='UNCERTAIN' else 'NO_OBSERVED_TIP',terminal_reason=p['terminal_reason']))
 save(OUT/'production_tip_comparison.csv',pointrows);ps=[]
 for kind,name in scopes:
  group=[r for r in pointrows if r['dataset_id']==name] if kind=='dataset' else [r for r in pointrows if r['group_role']==name]
  for split in ['ALL','development','holdout']:
   rr=[r for r in group if split=='ALL' or r['original_split']==split];visible=[r for r in rr if r['annotation_state']=='VISIBLE'];scored=[r for r in visible if r['error_original_px'] is not None];errors=np.array([r['error_original_px'] for r in scored]);n=len(scored)
   ps.append(dict(scope=kind,name=name,original_split=split,group_role=rr[0]['group_role'],frames=len(rr),human_visible=len(visible),human_uncertain=sum(r['annotation_state']=='UNCERTAIN' for r in rr),observed_scored=n,missing_observed=len(visible)-n,observation_coverage=n/len(visible) if visible else None,p50_error_px=float(np.median(errors)) if n else None,p95_error_px=float(np.percentile(errors,95)) if n else None,max_error_px=float(errors.max()) if n else None,**{f'within{t}_count':int(np.sum(errors<=t)) for t in [3,5,10]},**{f'within{t}_of_observed':float(np.mean(errors<=t)) if n else None for t in [3,5,10]},**{f'within{t}_of_all_visible':int(np.sum(errors<=t))/len(visible) if visible else None for t in [3,5,10]}))
 save(OUT/'production_tip_group_summary.csv',ps)
 # Cases ordered by original sequence, not cherry-picked visual quality.
 cards=[]
 for r in manifest:
  name=f"{r['dataset_id']}__frame_{int(r['frame_id']):06d}";cards.append(f'<section><h2>{r["dataset_id"]} / {r["frame_id"]} / {role(r["dataset_id"])}</h2><img loading="lazy" src="diagnostics/{name}.jpg"></section>')
 (OUT/'R05_Human_Annotation_Comparison.html').write_text('<!doctype html><meta charset="utf-8"><title>R05 人工标注对照验证</title><style>body{font:16px system-ui;background:#e8edf1;margin:24px}img{width:100%;max-width:1600px}section{background:white;padding:12px;margin:18px 0}</style><h1>六组人工标注与冻结差分结果对比</h1><p>排除组X排除；验证组C与三点弯仅验证。绿色人工路径、红色人工尖端、黄色不确定区域，紫色为无效差分区域。所有标签仅用于对比，未训练或拟合参数。</p><p><a href="validation_report.md">完整报告与生产A尖端误差</a></p>'+''.join(cards),encoding='utf8')
 def pct(x):return 'N/A' if x is None else f'{x*100:.2f}%'
 def number(x):return 'N/A' if x is None else f'{x:.2f}'
 table=['| 数据组/角色 | 可见/不确定 | 有效配对 | 完整路径有效覆盖（仅配对帧均值） | E1/E2路径差分支持（5px） |','|---|---:|---:|---:|---:|']
 for r in summary:
  if r['scope']!='dataset' or r['original_split']!='ALL':continue
  table.append(f"| {r['name']} / {r['group_role']} | {r['visible']}/{r['uncertain']} | {r['paired_visible']} | {pct(r['full_path_common_coverage_paired_mean'])} | {pct(r['PRIMARY_E1_E2_E1_FIXED_REF_tol5_support_mean'])} / {pct(r['PRIMARY_E1_E2_E2_MATCHED_HISTORY_tol5_support_mean'])} |")
 pt=['| 数据组/角色 | 可见GT | 有观测输出 | 缺输出 | P50/P95/max误差 px | ≤5px数量（全体可见分母） |','|---|---:|---:|---:|---|---:|']
 for r in ps:
  if r['scope']!='dataset' or r['original_split']!='ALL':continue
  pt.append(f"| {r['name']} / {r['group_role']} | {r['human_visible']} | {r['observed_scored']} | {r['missing_observed']} | {number(r['p50_error_px'])}/{number(r['p95_error_px'])}/{number(r['max_error_px'])} | {r['within5_count']}/{r['human_visible']} |")
 total_rows=[r for r in ps if r['scope']=='dataset' and r['original_split']=='ALL']
 totals={k:sum(r[k] for r in total_rows) for k in ['human_visible','observed_scored','missing_observed','within5_count']}
 baseline_overview=f"总计{totals['human_visible']}张人工明确可见帧，{totals['observed_scored']}张生产A确认输出、{totals['missing_observed']}张缺输出；≤5px为{totals['within5_count']}/{totals['human_visible']}（全体可见帧分母）。这不是可接受精度已经得到证明的结果。CT2与开发组H存在数百像素偏差，三点弯缺输出较多；不能只用CT3相对较低的中位误差概括所有组。"
 report='''# R05 当前人工标注：六组受控验证

## 数据约束已生效

用户2026-11-11最新准则已写入config/dataset_usage_policy.json、AGENTS.md和数据读取检查。开发组为GROUP_A、CT2、开发组H、CT3；验证组C和三点弯整组为VALIDATION_ONLY；排除组X从本轮及未来开发/验证完全排除，旧文件仅保留，不删除。旧清单里验证组C、三点弯的development子集不授予开发或调参权限。

人工标注仅供QC和结果对比，没有训练、伪标签训练、参数拟合、自动阈值搜索或基于标签的参考选择。两个验证组只读评估，规则锁定后未根据它们改算法。全部试验此前已曝光，当前分组约束是前瞻性用途限制，不把已曝光组重新称作独立未见TEST。

## 输入、冻结与评分范围

排除排除组X20张后，6组120张：111张明确路径/尖端，9张不确定。全部当前JSON和图像映射通过QC，原图哈希未变。排除组X的双尖端及路径衔接争议不再阻塞本轮，因为其图像/标签在进入本轮读取前已排除。

冻结的E1固定参考/E2匹配历史/C0最近帧/C1开口排序结果来自R05-PRE真实产物。当前标签既不改变warp/mask，也不改变历史候选、配准门和差分阈值25。完整规则、文件哈希、策略、3/5/10原图像素容差在pre_evaluation_lock.json中先锁定后评分。生产A另用冻结DLL、flags3572/SHADOW1/terminal1/refine=true/4线程按原始序列回放；同组只初始化一次，首帧GetBaseline为缓存查询。回放只读原图和原始P1/P2，不打开标注JSON，之后比较器才读取快照标签。

每组20张原有15 development/5 holdout子划分保留作分层统计；对于验证组C和三点弯，两种子划分全部仍是验证数据。9张uncertain均排除确定尖端/路径误差，单独统计，不能按负样本或0误差计入。原标注者已要求按当前标签继续，本轮不自动修正弱可见末端。人工粗标注本身存在容差，不把点坐标当作无限精度真值。

## 差分证据验证

'''+ '\n'.join(table)+'''

覆盖分母是人工标注的完整原图路径弧长，按0.5原图像素间隔均匀采样并按弧长加权；落在ROI外的路径仍计入总长度，避免裁掉路径后虚增覆盖。路径容差带按缩放ROI像素中心映射到原图坐标，解析计算到人工线段的距离，统一使用3/5/10原图像素。E1/E2只在同帧同mask交集上比较；C0/C1消融另使用四臂共同mask，完整分母见CSV。

关键发现：图像能够通过双侧配准，并不意味着真实裂纹都落入可用差分区。CT2、验证组C、三点弯的人工路径都存在明显掩膜覆盖损失；GROUP_A、开发组H、CT3没有可评分的E1/E2配对。多数路径实际在ROI内，主要损失与中央过渡带、有效像素掩膜和配准不可用有关；这里只是位置归因，尚未通过放开掩膜消融证明可以安全恢复。

E2在人工路径附近的变化响应普遍低于E1，三点弯在5px容差带的配对样本上为零。历史图本身可能已经包含裂纹，低差分可由共同裂纹抵消造成；该结果不能解释为“当前无裂纹”，也不能把E1更多变化直接当成裂纹新生长度。因此当前证据不支持把E2作为主要可见裂纹/尖端判据，亦不能从本轮推出历史差分在新增变化检测上必然无价值。

off_path_activation_density仅为人工主路径带外的强变化密度，不是真实误报率；没有人工interference区域或no_visible_crack样本，干扰激活率与无裂纹误报率均N/A。静态几何条带与人工路径的重叠量也已导出，避免未经标注核验就认定整条带完全静态。

## 冻结生产A与人工尖端的直接对比

'''+ '\n'.join(pt)+'\n\n'+baseline_overview+'''

误差为原图像素欧氏距离，仅“人工明确可见+生产confirmed observed输出”进入P50/P95/max分母。缺输出单列，不填零；同时报告≤3/5/10px占已观测输出及全部人工可见帧的两个分母，防止确认覆盖下降被误判为精度提升。生产A只有一个冻结版本，本轮不能声称算法优化前后提升。E1/E2不生成尖端预测，因此没有其尖端定位准确率；上述点误差只属于生产A基线。

## 决策与下一步

- LABEL_QC_SIX_GROUPS = PASS：120张合法，111 visible / 9 uncertain。
- DATA_USAGE_POLICY = ENFORCED：排除组X不参与，验证组C/三点弯只验证，标签只对比。
- MODEL_TRAINING / PARAMETER_FITTING = NOT_PERFORMED。
- FIXED_VS_HISTORY_FEASIBILITY = INCONCLUSIVE_FOR_CHANGE_DETECTION。
- HISTORY_DIFFERENCE_AS_PRIMARY_VISIBLE_CRACK_EVIDENCE = UNSUPPORTED。
- R05_FORMAL_DEVELOPMENT_READY = NO：当前掩膜覆盖和有效组别不足，未证明历史差分安全增益。
- PRODUCTION_ALGORITHM_UPDATED = NO；基线尖端误差已实测，不等于新版本通过。

后续如继续研究，只能在四个开发组原图上处理配准可用性、中央过渡区域的证据表达，并保持当前图像可见结构验证；不能依赖人工点训练或拟合，不得依据验证组C/三点弯分数选参数。验证组待新规则锁定后再次评估；已经看过的验证结果不能包装成未见泛化。

性能记录为本机原生API分项计时与独立I/O计时，没有宣称目标i7端到端50ms达标。差分渲染和人工评价也不是在线算法耗时。

## 产物

- [原图ROI、人工标签与冻结差分图册](R05_Human_Annotation_Comparison.html)
- [生产A与人工尖端逐帧对照图册](Production_A_Tip_Comparison.html)、[全部120选帧结果视频](R05_Annotation_Validation.mp4)
- [逐帧路径覆盖](path_coverage.csv)、[路径带差分比较](difference_label_comparison.csv)、[按组/用途/原split汇总](difference_group_summary.csv)
- [生产A逐帧人工尖端误差](production_tip_comparison.csv)、[生产A分组与分母汇总](production_tip_group_summary.csv)
- [120张人工JSON快照](human_annotations_six_groups_snapshot.zip)、[先验锁定](pre_evaluation_lock.json)、[用途与坐标合同测试](validation_contract_tests.json)、[输入与生产完整性](integrity_check.json)

复现入口为research/uctt_r05_validation/README.md。历史R05-PRE和两轮标注审计产物均未覆盖；config/datasets.json角色调整是用户明确要求的元数据变更，旧版本已备份在policy_before，生产C++源码与DLL哈希保持不变。
'''
 (OUT/'validation_report.md').write_text(report,encoding='utf8')
 write(OUT/'final_decision.json',dict(active_groups=6,annotation_frames=120,visible=111,uncertain=9,excluded_group_x=20,development_groups=['group_a','ct2','group_h','ct3'],validation_only_groups=['group_c','three_point_bend'],annotations_for_training=False,parameter_fitting=False,production_updated=False,tip_accuracy='EVALUATED_FROZEN_PRODUCTION_A_ONLY',difference_tip_accuracy=None,formal_development_ready=False,history_difference_as_primary_visible_crack_evidence='UNSUPPORTED',change_detection_feasibility='INCONCLUSIVE'))
 write(OUT/'production_tip_overall_summary.json',totals)
 print('REPORTS AND BASELINE POINT SCORING COMPLETE')
if __name__=='__main__':main()
