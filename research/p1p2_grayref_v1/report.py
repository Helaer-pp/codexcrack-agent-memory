"""Read completed outputs only. No detector invocation, fitting, or parameter selection."""
from common import *
import numpy as np
import math
from collections import Counter
from preflight import source_points

NAMES=dict(group_a='GROUP_A',ct2='CT2',group_h='开发组H',ct3='CT3',group_c='验证组C',three_point_bend='三点弯',DEVELOPMENT='开发合计',VALIDATION_ONLY='验证合计')
def fmt(x):
 if x is None or x=='':return 'N/A'
 if isinstance(x,float):return f'{x:.3f}'
 return str(x).replace('|','/').replace('\n',' ')
def table(headers,records):
 return '| '+' | '.join(headers)+' |\n|'+ '|'.join(['---']*len(headers))+'|\n'+''.join('| '+' | '.join(fmt(x) for x in r)+' |\n' for r in records)+'\n'
def doc(name,text): (OUT/name).write_text(text,encoding='utf8')
def percentiles(values):
 a=np.asarray(values,float)
 return dict(n=len(a),p50=float(np.percentile(a,50)),p95=float(np.percentile(a,95)),p99=float(np.percentile(a,99)),max=float(a.max())) if len(a) else dict(n=0,p50=None,p95=None,p99=None,max=None)
def main():
 assert read(OUT/'evaluation_dev_complete.json')['frames']==1565
 assert read(OUT/'evaluation_validation_complete.json')['frames']==1082
 assert sha(FROZEN)==EXPECTED_SHA
 combined={}
 for name in ['all_frames','all_results','group_summary','failure_stages','A55_comparison_rows']:
  combined[name]=rows(OUT/'tables'/f'{name}_dev.csv')+rows(OUT/'tables'/f'{name}_validation.csv');save(OUT/'tables'/f'{name}.csv',combined[name])
 save(OUT/'inputs/labels_offline.csv',rows(OUT/'inputs/labels_offline_dev.csv')+rows(OUT/'inputs/labels_offline_validation.csv'))
 summaries=combined['group_summary'];result=combined['all_results'];primary=[r for r in summaries if r['mode']=='joint' and r['threshold']=='10']
 parity=[];pgroup=[];arrays=[]
 for g in DEV+VAL:
  rr=rows(OUT/'tables'/f'parity_{g}.csv');parity+=rr;delta=[float(r['tip_distance']) for r in rr if r['tip_distance']!=''];p=dict(group=g,frames=len(rr)//6,cases=len(rr),tip_exact=sum(r['tip_exact']=='True' for r in rr),trace_equal=sum(r['trace_structure_equal']=='True' for r in rr),status_equal=sum(r['status_equal']=='True' for r in rr),roi_equal=sum(r.get('roi_equal')=='True' for r in rr),points_equal=sum(r.get('points_equal')=='True' for r in rr),candidate_counts_equal=sum(r['candidate_counts_equal']=='True' for r in rr),endpoint_delta_p50=float(np.percentile(delta,50)) if delta else None,endpoint_delta_p95=float(np.percentile(delta,95)) if delta else None,endpoint_delta_max=max(delta) if delta else None,predicted_max_abs=max(float(r['predicted_max_abs'] or 0) for r in rr));pgroup.append(p)
  for row in [r for r in rows(F/'selected_frames.csv') if r['dataset_id']==g]:
   f=int(row['frame_id'])
   with np.load(OUT/'py_runs'/g/str(f)/'evidence_arrays.npz') as py,np.load(OUT/'cpp_runs'/g/str(f)/'evidence_arrays.npz') as cpp:
    for key in cpp.files:arrays.append(dict(group=g,frame_id=f,field=key,shape_equal=py[key].shape==cpp[key].shape,different_pixels=int(np.count_nonzero(py[key]!=cpp[key])),max_abs=float(np.max(np.abs(py[key].astype(float)-cpp[key].astype(float))))))
 save(OUT/'tables/py_cpp_parity.csv',parity);save(OUT/'tables/parity_all_groups.csv',pgroup);save(OUT/'tables/array_parity_all_selections.csv',arrays)
 divergences=[]
 for r in parity:
  if r['trace_structure_equal']=='True':continue
  py=json.loads(r['first_divergence_python']);cpp=json.loads(r['first_divergence_cpp']);meta=read(OUT/'py_runs'/r['group']/r['frame_id']/'metadata.json')['ROI']
  bounds=lambda trace:[max(meta['y_top']+3,math.floor(trace[7]-7)),min(meta['y_bottom']-3,math.ceil(trace[7]+7)+1)]
  divergences.append(dict(group=r['group'],frame_id=r['frame_id'],mode=r['mode'],threshold=r['threshold'],first_divergence_column_index=r['first_divergence'],x=py[0],python_predicted=py[7],cpp_predicted=cpp[7],first_predicted_abs=abs(py[7]-cpp[7]),python_search_y_bounds=bounds(py),cpp_search_y_bounds=bounds(cpp),search_bounds_differ=bounds(py)!=bounds(cpp),python_selected_y=py[1],cpp_selected_y=cpp[1],python_observed=py[5],cpp_observed=cpp[5],tip_exact=r['tip_exact'],tip_distance=r['tip_distance'],cause='Least-squares floating prediction crosses floor/ceil search boundary; no post-validation detector modification'))
 save(OUT/'tables/first_divergence_audit.csv',divergences)
 labels={(r['group'],r['frame_id']):r for r in rows(OUT/'inputs/labels_offline.csv') if r['visibility']=='VISIBLE'};cpp_accuracy=[]
 for g in DEV+VAL:
  for mode in ['joint','current']:
   for threshold in [8,10,12]:
    rr=[r for r in parity if r['group']==g and r['mode']==mode and r['threshold']==str(threshold) and (g,r['frame_id']) in labels];ee=[]
    for r in rr:
     tip=json.loads(r['cpp_tip']) if r['cpp_tip'] else None;label=labels[g,r['frame_id']]
     if tip is not None:ee.append(float(np.linalg.norm(np.array(tip)-[float(label['tip_x']),float(label['tip_y'])])))
    cpp_accuracy.append(dict(group=g,mode=mode,threshold=threshold,visible=len(rr),coverage=len(ee),hit3=sum(e<=3 for e in ee),hit5=sum(e<=5 for e in ee),hit10=sum(e<=10 for e in ee),over100=sum(e>100 for e in ee),over500=sum(e>500 for e in ee),**{'error_'+k:v for k,v in percentiles(ee).items()}))
 save(OUT/'tables/cpp_selected_accuracy.csv',cpp_accuracy)
 comparison=[]
 for g in DEV+['DEVELOPMENT']+VAL+['VALIDATION_ONLY']:
  groups=DEV if g=='DEVELOPMENT' else VAL if g=='VALIDATION_ONLY' else [g]
  for mode in ['A55a0','joint','current']:
   rr=[r for r in combined['A55_comparison_rows'] if r['group'] in groups] if mode=='A55a0' else [r for r in result if r['group'] in groups and r['mode']==mode and r['threshold']=='10' and r['visibility']=='VISIBLE'];ee=[float(r['error']) for r in rr if r['error']!=''];comparison.append(dict(group=g,algorithm=mode,output_kind='formal_observed' if mode=='A55a0' else 'provisional_only',visible=len(rr),output=len(ee),hit3=sum(e<=3 for e in ee),hit5=sum(e<=5 for e in ee),hit10=sum(e<=10 for e in ee),over100=sum(e>100 for e in ee),over500=sum(e>500 for e in ee),**{'error_'+k:v for k,v in percentiles(ee).items()}))
 save(OUT/'tables/A55_V1_comparison.csv',comparison)
 performance=[]
 for g in DEV+VAL:
  for kind,records,fields in [('cpp',rows(OUT/'tables'/f'cpp_timing_{g}.csv'),['native_ms','point_ms','preprocess_ms','track_ms','decode_ms','export_ms']),('python',rows(OUT/'tables'/f'python_frames_{g}.csv'),['wall_ms','decode_ms','tracking_ms','savefig_ms','staging_io_hash_ms']),('cli_sample', [r for r in rows(OUT/'tables/full_cli_timing_samples.csv') if r['group']==g],['full_cli_wall_ms'])]:
   for field in fields:
    values=[float(r[field]) for r in records if r.get(field,'')!='']
    if values:performance.append(dict(group=g,implementation=kind,scope=field,**percentiles(values)))
 save(OUT/'tables/performance.csv',performance)
 # Post-run coordinate audit reads coordinate fields only, never detector outputs.
 audit=[];cache={}
 for r in rows(F/'input_inventory_allowed.csv'):
  if r['dataset_id'] not in DEV+VAL:continue
  path=r['p1p2_source']
  if path not in cache:cache[path]=source_points(path)
  pair=cache[path].get(int(r['frame_order']));match=pair is not None and pair[0]==json.loads(r['points']) and (pair[1] is None or pair[1]==Path(r['source_image']).name)
  provenance=read(OUT/'py_runs'/r['dataset_id']/r['frame_id']/'input_provenance.json');digest=provenance.get('current_sha256',provenance.get('image_sha256'))
  audit.append(dict(group=r['dataset_id'],frame_id=r['frame_id'],point_source=path,point_mapping_equal=match,current_byte_hash_equal=digest==r['sha256'],status=provenance['status']))
 save(OUT/'tables/final_input_audit.csv',audit);assert len(audit)==2647 and all(r['point_mapping_equal'] and r['current_byte_hash_equal'] for r in audit)
 baseline=read(OUT/'preflight_status.json');protected={p:sha(ROOT/p)==digest for p,digest in baseline['protected_production'].items()};assert all(protected.values())
 gate=read(OUT/'parity_gate.json');assert all(sha(ROOT/p)==v for p,v in gate['files'].items())
 roi=[]
 for g in DEV+VAL:
  rr=[r for r in result if r['group']==g and r['mode']=='joint' and r['threshold']=='10'];v=[r for r in rr if r['visibility']=='VISIBLE'];roi.append(dict(group=g,frames=len(rr),status_ok=sum(r['status']=='OK' for r in rr),no_provisional_tip_all_frames=sum(r['coverage']=='False' for r in rr),visible=len(v),gt_tip_outside_roi=sum(r['roi_contains_gt']=='False' for r in v),gt_tip_outside_sampling_roi=sum(r['sampling_roi_contains_gt']=='False' for r in v),mean_gt_path_inside_roi=float(np.mean([float(r['gt_path_inside_roi_fraction']) for r in v])),path_recall10=float(next(r['path_recall10'] for r in primary if r['group']==g)),path_precision10=float(next(r['path_precision10'] for r in primary if r['group']==g))))
 save(OUT/'tables/roi_and_path_feasibility.csv',roi)
 failures=[r for r in combined['failure_stages'] if r['mode']=='joint' and r['threshold']=='10'];sentinels=[r for r in failures if (r['group'],int(r['frame_id'])) in [('ct2',395),('group_h',78),('group_a',504),('ct3',65)]]
 fcounts=rows(OUT/'tables/failure_counts_dev.csv')+rows(OUT/'tables/failure_counts_validation.csv')
 for i,r in enumerate(fcounts):r['split']='DEVELOPMENT' if i<13 else 'VALIDATION_ONLY'
 save(OUT/'tables/failure_counts.csv',fcounts)
 accuracy=table(['组','完整帧','VISIBLE','暂定输出','≤3/5/10px','>100/500px','误差 n / P50 / P95 / max','GT在ROI外'],[[NAMES[r['group']],r['frames'],r['visible'],r['provisional_coverage'],'/'.join(r[k] for k in ['hit3','hit5','hit10']),r['over100']+'/'+r['over500'],r['error_n']+' / '+' / '.join(fmt(float(r[k])) if r[k] else 'N/A' for k in ['error_p50','error_p95','error_max']),r['roi_gt_outside']] for r in primary])
 parity_md=table(['组','帧×模式','端点完全一致','逐列选择一致','ROI/P点一致','端点差max(px)','预测y最大浮点差'],[[NAMES[r['group']],r['cases'],r['tip_exact'],r['trace_equal'],str(r['roi_equal'])+'/'+str(r['points_equal']),r['endpoint_delta_max'],f"{r['predicted_max_abs']:.3g}"] for r in pgroup])
 comp_md=table(['组','输出','VISIBLE','覆盖','≤3/5/10px','>100/500px','P50/P95/max'],[[NAMES[r['group']],r['algorithm'],r['visible'],r['output'],f"{r['hit3']}/{r['hit5']}/{r['hit10']}",f"{r['over100']}/{r['over500']}",' / '.join(fmt(r[k]) for k in ['error_p50','error_p95','error_max'])] for r in comparison])
 modes_md=table(['组/分母','分支','T','暂定输出','≤3/5/10px','>100/500px'],[[NAMES[r['group']]+'/'+r['visible'],r['mode'],r['threshold'],r['provisional_coverage'],r['hit3']+'/'+r['hit5']+'/'+r['hit10'],r['over100']+'/'+r['over500']] for r in summaries])
 roi_md=table(['组','完整帧/运行成功','全帧无暂定端点','GT在ROI外/采样ROI外','人工路径落在ROI比例均值','10px路径覆盖/精度均值'],[[NAMES[r['group']],str(r['frames'])+'/'+str(r['status_ok']),r['no_provisional_tip_all_frames'],str(r['gt_tip_outside_roi'])+'/'+str(r['gt_tip_outside_sampling_roi']),f"{r['mean_gt_path_inside_roi']:.1%}",f"{r['path_recall10']:.1%}/{r['path_precision10']:.1%}"] for r in roi])
 failure_md=table(['数据用途','类别','计数','代表帧','直接证据'],[[r['split'],r['stage'],r['count'],r['representative'],r['evidence']] for r in fcounts])
 sentinel_md=table(['开发哨兵','joint误差/有向x误差','分类','初始中心距GT路径','最后访问x/缺失列','GT处valley/newdark/两侧灰度','GT邻域current/joint像素数'],[[r['group']+'/'+r['frame_id'],(fmt(float(r['error'])) if r['error'] else '无端点')+' / '+(fmt(float(r['signed_x_error'])) if r.get('signed_x_error') else 'N/A'),r['stage'],fmt(float(r['initial_distance_gt_path'])),r['last_visited_x']+'/'+r['last_missing_run'],' / '.join(fmt(float(r[k])) if r.get(k) else 'N/A' for k in ['gt_pixel_valley','gt_pixel_newdark','gt_pixel_flank_low']),r.get('gt_neighborhood_current_accepted','')+'/'+r.get('gt_neighborhood_joint_accepted','')] for r in sentinels])
 val=next(r for r in primary if r['group']=='VALIDATION_ONLY')
 report=f'''# P1/P2-GrayRef V1 冻结跨试件实测报告

## 实测结论

全量执行完成：开发1565帧、锁后验证1082帧，共2647帧；每帧固定 joint/current × T8/10/12，Python和独立C++各15882组结果。全部输入可读取，未删除失败或无端点帧。六档BMP黄金回归完全一致，源码SHA256保持任务书值。

默认 joint T10 开发尖端≤10px为12/76（15.8%），全部来自CT3；GROUP_A、CT2、开发组H均0命中。验证≤10px为{val['hit10']}/{val['visible']}，>100/500px为{val['over100']}/{val['over500']}。**工程链路可运行，开发移植parity通过；锁后验证暴露current分支的浮点边界放大，跨组精度与完整移植验收均未通过。保留A，不发布本研究DLL为生产版本。**

全部V1 tip是暂定候选，无独立主裂纹认证。formal_observed字段0仅表示未实现该确认合同，不是安全或低误检证明。没有NO_VISIBLE_CRACK负例；FPR=N/A。4个开发UNCERTAIN、5个验证UNCERTAIN单独保留，不能当负例。其余2527张无标签图像只用于运行/状态/一致性统计。

## 表一：冻结Python V1原生准确率（固定 joint T10）

缺端点仍计入所有VISIBLE分母，不能当零误差。分位数仅有可比较端点的n，不包含缺输出；单位全部为原始图像像素。

{accuracy}
## 表二：C++相对Python移植一致性

{parity_md}
开发锁前9390/9390端点、逐列整数坐标/缺失计数/观测位、点与ROI完全一致；80选帧×8数组全部逐像素相同。锁后验证另计6492组模式结果。合计{sum(r['cases'] for r in pgroup)}组中{sum(r['tip_exact'] for r in pgroup)}端点完全一致。120选帧×8数组共{len(arrays)}份，其中{sum(r['different_pixels']==0 for r in arrays)}份逐像素完全一致。

**锁后验证15组端点不一致，126组轨迹不一致；不能将开发parity通过延伸成全数据严格一致。** 全部端点差异在current分支；joint三阈值端点仍全部一致。首次离散分歧的预测y差均小于1e-9，却跨过floor/ceil取整边界，导致搜索范围差1像素。Python np.polyfit与C++ OpenCV SVD在最近12点线性拟合上的微差可触发离散放大。典型验证组C440/current/T8：首次x=2280，预测2343.9999999999995与2344.0，搜索下界不同，Python接受y2336而C++未接受，最终端点差209.02px。验证组C2/current/T12差16.40px；三点弯32/current/T12差45px。不能以“只是浮点微差”淡化最终端点影响。现有可见选帧上的原生3/5/10px与>100/500px计数恰好和Python相同，但不消除全序列移植失败。完整记录见[first_divergence_audit.csv](tables/first_divergence_audit.csv)，未重新推理或修补验证帧。

完整trace含前50/后50与所有中间列；候选计数另列CSV。锁定版本继续保留，未按验证差异改floor/ceil、加epsilon或改SVD。下一候选只能在新版本中研究可移植数值等价性；本次结果不得覆盖。另存[原生选帧准确率](tables/cpp_selected_accuracy.csv)，避免把Python精度表不加说明地当成全部C++精度。图像/ROI错误合同比较“均拒绝”，Python分类错误与native ERROR文案不要求相同。

## 表三：研究A55a0与V1，同一VISIBLE分母

A55复用R05D封存回放，未重新执行/选择旧A参数；A55列是formal observed，V1列是provisional，输出语义不同但端点误差可同分母对照。没有把历史发布A1c742混入表中。

{comp_md}
## 固定六模式消融

{modes_md}
joint T10开发12/76优于current T10的8/76，但增益集中于CT3，不能宣称跨材料显著优势。CT2 joint全部无端点，current也未命中。验证验证组Cjoint T10为0/20而current T10为11/20，三点弯joint为5/15、current为2/15：参考分支没有统一优势。参考首帧可能已有裂纹，current与joint共享当前图/ROI/追踪规则，差异支持“增量证据与可见裂纹不等价”，不独立证明旧裂纹或配准是哪一个原因。T8、T12保持预设对照，没有逐组/逐帧挑最佳阈值。验证表仅报告，不反向选择模式。

## P点、ROI与路径可行性

{roi_md}
每组首帧固定参考、原图坐标xy、P1上/P2下、frame_id=frame_order+1。2647条P点原记录映射与读入图像SHA逐一核对通过。CT3来源为显式原帧名和坐标num的历史坐标CSV；独立原始跟踪TXT仍缺失，不能夸大其外部可追溯性。全部帧提供当前P点；NCC回退仅黄金回归实测，不能把本批统计解释为全量NCC成功率。

ROI严格保持冻结上下边界与自动右边界，实际采样另有上2/下1像素内缩。CT3六个GT在ROI外是适用假设失败，未为GT扩ROI。路径覆盖是人工路径中距可见算法线段≤10px的比例；路径精度是反方向比例，按全部VISIBLE逐帧均值，空路径为0；不把跨缺口的预测连线当观测。5px数据同样在group_summary.csv。完整人工路径可能从P点左侧起始，ROI路径比例与尖端包含是不同指标。

## 失败类别与直接证据

{failure_md}
分类为离线、固定优先级的可观测证据归类，并非排他物理因果证明：输入→ROI排除→已命中→初始中心偏离→GT邻域材料/暗谷/差分→过冲→21列缺失早停→UNKNOWN。GT邻域为±3px，数字只用于说明已冻结结果，不能改路径。零计数只代表未归入该类，不代表该机制不存在。NOT_OBSERVABLE不据不确定标签臆断；9个UNCERTAIN另列。两点y线性位移插值不是严格两侧材料配准，REFERENCE_COMPENSATION_UNTRUSTWORTHY的独立证据仍不足。

{sentinel_md}
开发组H78的弱末端在当前灰度/差分图中可见局部响应，但实际路径远在其前方停止；不能把“GT附近有证据”写成“V1到达并正确终止”。GROUP_A504与CT2/395同样保留起始中心、最后访问列、21列缺失和近GT灰度，见哨兵放大图。CT3/65暂定误差6.66px，有效但不满足3/5px。裂纹闭合、喷漆遮挡与真实物理间隙没有单独同步物理标签，不能仅凭trace缺失给出分材料因果成功率；报告能确认的是暗谷/增量证据的数值与访问范围，物理原因仍需补证。

## 执行边界与偏差记录

冻结源码未改，source_diff.patch为空。为绕开冻结cv2.imread对中文Windows路径的限制，adapter仅按原字节复制到ASCII output/io_cache并校验SHA，不预裁剪、不重编码。实际逐帧调用原main，观察器只读取返回局部变量，包含观察开销；提供的batch_validate_V1先通过1565帧dry-run，完整回放用常驻worker以减少每帧导入开销。12个开发首/中/末帧另跑真实CLI，六行输出与常驻结果一致；不能把常驻main耗时标为含进程启动的CLI。

验证进入前已锁定算法、native DLL、adapter、评分规则与manifest。两组首次各完成Python第1帧后，provenance字段重名导致记录层中断；修正validation.py的日志键，并按validation_io_amendment.json复用这两份已完成Python输出，原始锁与初始错误日志保留。此前native验证帧数0，未读验证标签；检测规则、DLL、评估阈值均不改。恢复不是无记录地重跑首帧，也不能称所有驱动文件从未改动。40份验证标签在1082帧推理全部完成后读取；访问记录保留。各组历史已被研究曝光，含任务书明确回归图，不称外部独立盲测。

冻结源码本身对任意非空tip写stop_reason=gap_limit，即使循环到右边界也如此；保持该行为，真实终止应结合last_visited_x/missing_run判断。原overlay把非连续观测点相连，本轮视频忠实展示并注明跨缺失线不是观测；新增局部卡片以虚线区分缺失。C++只借用CrackV4Image/Point内存结构，未调用或链接A/R05G检测实现，使用独立导出GrayRef*。

## 最小V2建议（仅方案，未实施）

首先解决“当前P点几何中点附近的单列起始先验”与实际主裂纹身份/可达性不一致：在DEVELOPMENT预先固定局部起源证据规则，逐项对照V1，报告首个分歧、到达GT邻域率及严重错误；不拿人工tip作种子，不依据某组名字分支。单独研究reference-unavailable/已有裂纹的证据状态，current与增量证据不能互相当成物理真值。ROI物理假设若要放宽，应先定义独立几何依据与适用范围，不能以包含现有GT为优化目标。每次仅改一个机制，保持四组全序列、同76个可见分母、3/5/10与>100/500、路径精度和覆盖、无标签负例FPR=N/A；预注册规则后冻结，再考虑新的独立验证数据。本轮验证组不再作为这些改动的开发选型数据。需要用户明确批准V2后另开版本，不能覆写V1。

## 交付索引

- [六组视频与120张详细对比卡](galleries/index.html)，验证组优先；[2647帧局部对比](galleries/all_frames.html)。
- [原生准确率](tables/group_summary.csv)、[完整逐帧](tables/all_results.csv)、[移植parity](tables/py_cpp_parity.csv)、[A55对比](tables/A55_V1_comparison.csv)、[失败证据](tables/failure_stages.csv)。
- [环境与身份](baseline_and_versions.md)、[独立时间范围](performance_report.md)、[构建和复现](build_and_reproduce.md)、[最终完整性](final_integrity.json)。
'''
 doc('development_report.md',report)
 timing=table(['组','实现','计时范围','n','P50 ms','P95 ms','P99 ms','max ms'],[[NAMES[r['group']],r['implementation'],r['scope'],r['n'],r['p50'],r['p95'],r['p99'],r['max']] for r in performance])
 doc('performance_report.md','# 实测性能与计时范围\n\n'+timing+'''机器为AMD Ryzen 9 7950X / Windows 11，非目标i7-12700K。native OpenCV4.4四线程，开发组多进程并行；验证两个worker并发，部分期间还运行CLI计时和离线媒体渲染，未隔离系统负载。P95不是部署保证。

native_ms是一次完整六模式process（含P点、预处理、六次追踪），不含参考initialize、图片解码、JSON序列化/解析、文件写入、NPZ或渲染。point/preprocess/track是其内部子范围；decode_ms在外部，export_ms包含GrayRefRead JSON生成/解析，不含结果文件写盘。不能将不同范围或各自分位数简单相加得到端到端分位数。JSON结果保留call_wall_ms（FFI完整调用），本表native是内核内测。

Python wall_ms为常驻main加日志重定向，含decode/CSV/figure/export与return观察器；decode_ms读两张图，tracking_ms六模式追踪，savefig_ms只计savefig，不含figure构造。余量混合预处理/其他导出/绘图构造，未单独宣称纯Python计算成本；NPZ证据压缩与adapter staging/hash不计入wall，后者单列。无法从现有计时准确拆开Python预处理与CSV写盘，明确保留这个限制。full_cli_wall_ms为12个确定开发首/中/末帧的真实子进程，含导入与启动，全部六行输出与全量回放相同；不是2647帧CLI性能分布。

视频固定8fps为播放速度，不代表算法吞吐。C++为逐步严格镜像、未引入预算截断或改变规则来满足50ms。真实终端性能仍须目标机器隔离测试；即使时间通过，也不能弥补本轮跨组准确率失败。
''')
 versions=read(OUT/'freeze_manifest.json');pack=read(OUT/'package_identity.json')
 doc('baseline_and_versions.md',f'''# 基线身份与版本

完整包：`{pack['zip_path']}`，SHA256 `{pack['zip_sha256']}`。配套README、batch、六行golden均可用，package_identity.json逐件记录。preflight_status.json中缺资料状态是历史启动快照，已由package_identity与本报告解决，不能抹掉当时记录。

冻结Python SHA256 `{EXPECTED_SHA}`；所有2647帧按此源执行，source_snapshot byte-for-byte相同，source_diff.patch为空。C++候选DLL SHA256 `{sha(BUILD/'Release/P1P2GrayRefV1.dll')}`。MSVC v142 / C++17 / OpenCV4.4 / O2 / fp:strict，原生和Python不同库版本通过实际parity，不宣称因版本号相同而一致。

Python环境：`{json.dumps(versions['versions'],ensure_ascii=False)}`。包中原运行环境另见input_package/requirements_tested.txt和freeze_manifest.json；当前环境六档golden仍完全一致。

研究A：R02/R05D build55a0，历史发布：A1c742，两种身份不同，准确率只从研究A55封存dev_frames/val_frames读取。生产源码和两个DLL共{len(protected)}个保护文件的原SHA均保持；详见最终完整性。复用旧结果不是本轮重新验证旧A算法。

严格数据隔离：开发4组1565帧/80标签（76可见），验证2组1082帧/40标签（35可见），排除组X0。标签只在完成推理之后作离线对比，不作训练、伪标签、参数搜索、参考选择、ROI或路径指导。解码/移植未读取GT。验证规则锁与metadata修复amendment分别保留。
''')
 write(OUT/'report_complete.json',dict(frames=len(audit),result_rows=len(result),parity_cases=len(parity),exact_tips=sum(r['tip_exact']=='True' for r in parity),array_cases=len(arrays),exact_arrays=sum(r['different_pixels']==0 for r in arrays),protected_files_unchanged=protected,source_unchanged=True,decision='KEEP_A_V1_RESEARCH_ONLY_ACCURACY_FAIL'))
 print('REPORT COMPLETE',len(audit),len(result),flush=True)

if __name__=='__main__':main()
