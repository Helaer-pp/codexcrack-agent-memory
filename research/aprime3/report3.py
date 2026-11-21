from common3 import *
import html,zipfile
def table(rr,keys=None):
 if not rr:return '无记录。'
 keys=keys or list(rr[0]);s='| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'
 for r in rr:s+='| '+' | '.join(str(r.get(k,'')).replace('|','/').replace('\n',' ') for k in keys)+' |\n'
 return s
def execute():
 old=json.loads((RUN/'03_exposed_regression/evaluation_summary.json').read_text());new=json.loads((RUN/'04_NEW_DEV/evaluation_summary.json').read_text());controls=json.loads((RUN/'01_diagnosis/known_motion_summary.json').read_text())
 real=rows(RUN/'03_exposed_regression/real_summary.csv');endpoint=json.loads((RUN/'03_exposed_regression/same_endpoint_reference_summary.json').read_text());fail=rows(RUN/'03_exposed_regression/A_prime2_failure_recheck.csv');native_summary=json.loads((RUN/'06_native_performance/latency_summary_by_group.json').read_text())
 oldmetrics=rows(RUN/'03_exposed_regression/ablation_metrics.csv');newmetrics=rows(RUN/'04_NEW_DEV/ablation_metrics.csv');newfam=rows(RUN/'04_NEW_DEV/family_metrics.csv');oldfam=rows(RUN/'03_exposed_regression/family_metrics.csv')
 budget=[];ep=rows(RUN/'03_exposed_regression/same_endpoint_reference_compare.csv')
 for g in dict.fromkeys(r['group'] for r in ep):
  q=[json.loads(r['funnel']) for r in ep if r['group']==g and r['method']=='AP3_ENDPOINT'];rejections=collections.Counter()
  for f in q:rejections.update(f['rejections'])
  budget.append(dict(group=g,mean_within_radius=float(np.mean([f['within_query_radius'] for f in q])),mean_prebudget_eligible=float(np.mean([f['prebudget_eligible'] for f in q])),mean_selected=float(np.mean([f['selected_for_matching'] for f in q])),scan_exhausted=sum(f['scan_budget_exhausted'] for f in q),rejected=dict(rejections)))
 csvout(RUN/'03_exposed_regression/real_reference_budget_summary.csv',budget)
 gateB=new['new_coverage']>new['old_coverage'] and controls[1]['false_accept']<=controls[0]['false_accept'];decision=dict(production='KEEP_A',research='PARTIAL_CANDIDATE_RECALL_IMPROVEMENT_ONLY',gate_A=new['gate_A'],gate_B=gateB,gate_activation=new['gate_activation'],gate_C=new['gate_C'],independent_TEST='NOT_RUN',full_native_15Hz='NOT_TESTED',real_physical_accuracy='N/A',production_changed=False)
 save(RUN/'08_reports/decision.json',decision)
 write(RUN/'05_NEW_TEST/NOT_RUN_REASON.md',f'''# 独立 TEST 未执行
NEW_DEV 前置判定：候选 Gate A={new['gate_A']}；挑战激活={new['gate_activation']}；参考 Gate B={gateB}；最终判决 Gate C={new['gate_C']}。
最终正确数仍为 A 的 {new['A_correct']}，平均路径可观察覆盖 {new['old_coverage']:.8f}→{new['new_coverage']:.8f} 未提高。
没有生成、读取或评估新的 TEST，也不存在 TEST 冻结后调参。独立 TEST 的正确数、错改、FP、损失和 bootstrap 均为 N/A，不能用本轮 DEV 数值代替。
''')
 write(RUN/'06_native_performance/cpp_build_and_test.md','''# C++ 实际完成范围
新增研究专用 CrackV4AP3Observer.dll，只增加 seed 门槛和 tile 观察；不包含 A′3 Python 候选、选块及联合判决。
使用项目内 OpenCV 4.4.0 SDK（来自用户 D:/opencv-4.4.0）、MSVC v142 编译；见 configure.log/build_observer.log。
AP3 observer 在 3035 帧真实图和 540 帧曝光 DEV 上对照原生结果，状态、坐标、弧长、float64 路径完全一致。
隔离媒体/DEV负载的双原生计时是 A 与原 AP2 tile observer；AP3 seed observer 运行时与研究计算并发，不能把它当独立性能测试。
完整 A′3 原生15Hz：NOT_TESTED。联合研究 Gate 不足，未移植发布全算法 DLL。所有 DLL 仅在 output/build/Release，冻结生产 DLL 不变。
''')
 trows=[]
 for r in native_summary:
  for mode in ['A','shadow_observer']:trows.append(dict(group=r['group'],mode=mode,**r[mode]))
 csvout(RUN/'06_native_performance/latency_summary_by_group.csv',trows)
 stage=[]
 for st in dict.fromkeys(f['old_stage'] for f in fail):
  q=[f for f in fail if f['old_stage']==st];stage.append(dict(stage=st,n=len(q),new_candidate_within8=sum(f['new_candidate_correct']=='True' for f in q),new_final_correct=sum(f['new_final_correct']=='True' for f in q)))
 no=[r for r in fail if r['A_stop']=='no_seed'];candidate=[r for r in fail if r['old_stage']=='CANDIDATE_OMISSION_ON_REACHABLE_PATH'];causes=collections.Counter(r['cause'] for r in candidate)
 summary=f'''# A′3 开发结果

结论：**KEEP_A**。候选召回改进成立，但最终尖端判决没有改善，参考泛化门槛未通过，不能替换生产算法。

- 曝光 DEV：候选正确覆盖 379→404/432；新 DEV：583→621/648，旧正确候选损失0，K≤12。
- 新 DEV 的实际正确输出仍为553/648，与 A 相同；阴性误确认105/216，未改善；正确 A 错改0只是回退结果，不能当作新模块安全性证据。
- 18独立真假尾pair、3种新背景、54配对帧实际激活。新DEV918帧，非独立TEST。
- 参考可观察覆盖63.0069%→62.9512%，Gate B失败；132项已知运动对照中新旧>1px误接受均0。
- 新观察器真实3035帧完全等价。隔离计时 A 开发组HP95 46.47ms、Max50.38ms；完整A′3原生15Hz未测试。
- 输出8个视频、4493张逐帧原图对照，另有关键候选诊断图；入口 ../index.html。真实物理精度N/A。
'''
 write(RUN/'08_reports/executive_summary.md',summary)
 report=summary+f'''
## 本轮实际改动

research/aprime3/candidate3.py 保留全部旧候选与原始 double A 尖端，再加入未确认 DP 末端事件，以及多窗口支持下降局部极值、有限平台中心细化。候选来自事件，非等距密铺；上限12。旧池已占满时不强行挤掉旧候选，因此仍存在预算饱和。

reference3.py 在 GFTT/匹配预算前做完整 patch 的坏像素比例和纹理方差筛选，当前裂纹带和越界位置先排除后补位。最多480缓存、192扫描、48模板/查询、3查询。NCC≥0.65、峰间隔≥0.015、FIT≥6、HOLDOUT≥4、P90≤1px、候选±16px被holdout包围、光度验证均未放松。覆盖是沿A路径的局部可比性，不能当作物理裂纹归属。

decision3.py 显式区分 SUPPORTED_NEW、SUPPORTED_STATIC、UNKNOWN_REFERENCE_DARKENING、UNKNOWN；旧裂纹加深与表面线加深不可仅凭灰度变化区分。保留 A 回退，研究确认另列 research_valid。selected_output_tip 可为 A 输出，但不是经研究验证的真尖端。历史只使用过去双方均通过局部几何/光度的端点，作为诊断日志，不参与单调扩展或最终确认。

新增 C++ seed observer 记录未改动分支的拒绝门槛；源文件和重建脚本可查。旧 A′2封存输出、冻结生产源码/DLL未改动。初次接线错误、消融统一、历史日志及NCC计数更正在00_protocol/implementation_corrections.md说明。

## 37 / 16 / 11 / 3 逐阶段结果

{table(stage)}

37候选遗漏的主因：{dict(causes)}。21帧受官方valid与末端窗口限制；11帧近GT事件被较远强事件合并；5帧阈值前就未产生合格事件。本轮37帧中25帧进入≤8px候选，但最终未独立确认。旧67失败仍然失败；另有此前旧判决修复的6帧在歧义保护后回退到错误A，所以曝光正确数由前轮365回到359。不能只公布候选增长掩盖这一退步。

16 no_seed全部是STARTUP_FRACTION_OR_PEAK_REJECT：峰值 {min(float(r['startup_peak']) for r in no):.6f}～{max(float(r['startup_peak']) for r in no):.6f}<6；起始支持比例≥{min(float(r['startup_fraction']) for r in no):.6f}，其他种子数量/连续性/累计增益门槛已过。这里不是时序确认导致，而是seed内固定起始峰值门槛。不能据此证明所有图像可可靠辨识；只能证明A已经构造了弱种子却被规则拒绝。本轮未实现新局部seed提议，16帧明确未恢复，不以修改A阈值来制造改进。

11停/继续失败和3稳定性拒绝都来自受控假尾：GT候选已在池中。对最近GT候选逐个核验，11帧的静态占比低于0.85，其中5帧还出现“静态之后又有新信号”的继续证据；它们不是因为前缀样本或争议段覆盖不足而拒绝。另3帧形态门槛已过，但小几何/光度扰动改变了停止模式，故未稳定确认。逐帧数值见01_diagnosis/stop_continue_14_exact_reasons.csv。这里是证据分类和稳定性问题，不能因为程序GT标为假尾就取消保护。真长/交叉/55°/75°/S形在新DEV各54帧保持原A正确；这是保留能力，尚不是新增确认能力。

## 新 DEV 与公平消融

306案例×3帧=918帧。材料过程为乘法多尺度随机场、随机站点Voronoi、随机曲线磨痕；相对于前轮生成器做机制更换，随机种子和输入SHA单独封存。推理清单不含family/GT/M_GT，评测器是独立进程。无真实人工标注。

{table(newfam,['family','A_correct','full_correct','old_oracle','new_oracle','endpoint_only_oracle','multiscale_only_oracle','FP'])}

新DEV新增38个正确候选：弱裂纹+32主要来自未确认末端保留，强假尾+6来自多尺度局部事件/细化。端点仅候选，不自动确认；旧候选损失0。事件窗口没有靠GT调阈值。

{table(newmetrics,['mode','correct','FP','changed','A_correct_changed_wrong','catastrophic','penalized_loss'])}

交叉消融统一用同一A′3判决；另列AP2_LEGACY_RULE和LEGACY_PATTERN_WITH_NEW_EVIDENCE。旧模式新DEV可输出565个正确，改12帧；新证据配旧模式558个正确，改7帧。最终FULL553：说明不仅需要处理物理歧义，新的候选/查询选择也未将覆盖收益转化为有效停止证据。不能以旧参考某个转折或当前暗谷更深直接认证物理尖端。

惩罚损失：可观察正例 min(error,64)，无有效输出32；阴性输出有效尖端32，否则0；不可观察正例不纳入损失。该值是预定工程损失口径，不是mm精度。程序负控中的STATIC_DARKENING_NEGATIVE与PREEXISTING_DARKENING有54对完全相同参考/当前/锚点、但不同物理故事，专为证明不可辨识边界；不应当成可由像素算法同时完美分类的普通样本。其54阴性误确认与静态线51帧误确认分开列出。

## 参考覆盖与真实失败帧

新DEV平均可观察路径覆盖 {new['old_coverage']:.8f}→{new['new_coverage']:.8f}，没有提高。几何已支持查询1980次，已知变换局部核验>1px误接受0；另外132独立已知运动控制结果：

{table(controls)}

控制包括初始偏移0.5/1/3/5px、非刚性模型不匹配、光度、重复纹理、遮挡、压缩、饱和、既有暗线。仿射真变换只进入评估；matcher输入仍为锚点刚体近似，不把GT变换作为正确初值。0误接受只针对这些控制，不能当真实配准保证。

真实6组当前帧的多查询支持结果：

{table(real)}

同末端/同A变换/仅选块差异的严格对照：

{table(endpoint,['group','method','n','cached','geometry','joint','reasons'])}

严格同末端对照并没有证明参考匹配改善：验证组C196→194，三点弯181→181，其余四组仍为0。多查询验证组C380是不同查询覆盖口径，不能归因为选块修复、更不能当作同端点精度提高。六组缓存数在新旧策略下相同；开发组H只有6个缓存块，不足独立FIT6+HOLDOUT4；开发组A152、CT2 480、排除组X47个缓存块也未满足查询局部的成功匹配数量/空间验证。具体NCC与路径带等拒绝次数见same_endpoint_reference_summary.json与real_patch_evidence.csv。亮度/纹理门槛、匹配失败和独立验证不足必须分开，不把未通过验证解释为图中没有裂纹。排除组X51/473和CT2 6/18/84有单独逐帧表及原图对照。

{table(budget)}

例如 CT2 同末端匹配累计21611块因LOW_NCC拒绝，仅733块接受，分散在467帧中仍不足独立FIT/HOLDOUT。排除组X285次纹理歧义拒绝、仅119次块接受；开发组H局部实际无可用匹配块。GROUP_A接受率本身并不低，但选到的局部块数量太少，应优先分析参考有效纹理的空间覆盖，不能笼统归为NCC低。

所有真实组均已曝光。排除组X退役历史追因，三点弯验证-only；均未用于调参或新独立验证。真实误差、真实长度准确性N/A。

## 反事实、性能与停止条件

306个中间帧实际执行正常/倒序候选/换参考/屏蔽参考/空间块剔除/几何+0.5/光度+2%/参考ROI平移，共2448次。候选顺序不改结果，屏蔽参考不得产生可信匹配。反事实的回退同A不能证明模块有效。固定A路径的参考ROI实验确实重选块，但实际改变搜索ROI后重跑路径NOT_TESTED：冻结公开ABI没有ROI参数。本轮没有用mask模拟搜索重跑。

{table([r for r in trows if r['mode']=='A'],['group','n','P50','P95','P99','Max','over_budget'])}

计时单位ms；3029变形帧，初始化、读图和媒体编码不计；A Process、V2、路径复制计入。本轮隔离DEV/媒体，开发组H没有超66.67ms，但这只证明本机本批A运行结果。完整A′3候选/参考/决策仍为Python，不能据旁路声称15Hz。新增seed观察器未改变3035结果；不发布A′3生产替换DLL。

Gate A PASS，激活PASS；Gate B FAIL，Gate C FAIL，独立TEST未生成，整体原生Gate NOT_TESTED。独立TEST的正确/错改/FP/损失/Bootstrap全部N/A。当前证据支持候选修复与失败机制定位，不支持算法上线替换。

## 文件入口

- 01_diagnosis/candidate_trace_raw.csv、candidate_filter_audit.csv：完整事件过滤轨迹，GT距离字段明确EVAL_ONLY。
- 03_exposed_regression/A_prime2_failure_recheck.csv：旧67帧逐一新旧结果；remaining_failures.csv：本轮所有曝光正例失败。
- 04_NEW_DEV/per_frame_predictions.csv、per_candidate_evidence.csv、interval_evidence.csv、patch_evidence.csv、evaluated_per_frame_all_modes.csv、counterfactuals.csv。
- 03_exposed_regression/real_per_frame.csv、real_per_candidate_evidence.csv、same_endpoint_reference_compare.csv。
- 07_media：8视频、4493原图逐帧对照；key_cases另外展示候选与有效域，非确认输出。
- 06_native_performance：单帧原生耗时、分组分位数、构建日志。reproduce.md：运行命令。

项目继续只在CodexCrack内开发与输出。未改外部原图、用户锚点与冻结A。
'''
 write(RUN/'08_reports/development_report.md',report)
 roots='# 失败根因与完整ID\n\n'+table(stage)+'\n\n'+table(fail,['case_id','frame_id','old_stage','cause','seed_stage','startup_peak','old_final_reason','new_final_reason','new_candidate_correct','new_final_correct'])
 roots+='\n\n## 新DEV仍失败的全部可观察正例\n\n'+table(rows(RUN/'04_NEW_DEV/remaining_failures.csv'),['case_id','frame_id','family','A_stop','old_oracle_error','full_oracle_error','error','reason'])
 write(RUN/'08_reports/failure_root_causes.md',roots)
 write(RUN/'08_reports/what_improved_and_what_did_not.md',summary+'\n候选已提高；完整长度/物理尖端准确性未证明；参考泛化未通过；weak/no_seed未修复；零错改来自回退；静态暗线误确认未解决。\n')
 # The report is an ordinary project artifact, not a cloud document.
 allvid=[]
 for kind in ['real','exposed','new']:allvid+=rows(RUN/f'07_media/{kind}_video_inventory.csv')
 links=''.join(f'<section><h2>{html.escape(v["group"])} · {v["frames"]} 帧</h2><video controls preload="metadata" src="{v["video"]}"></video><p><a href="07_media/per_frame/{v["group"]}/">逐帧对比图目录</a></p></section>' for v in allvid)
 page=f'''<!doctype html><html lang="zh"><meta charset="utf-8"><title>A′3研究交付</title><style>body{{background:#101b26;color:#e9eef3;font:17px sans-serif;margin:30px;line-height:1.65}}a{{color:#62d6ed}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}}video{{width:100%}}section{{background:#1a2b3b;padding:18px}}h1{{color:#ffdc63}}</style><h1>A′3 · KEEP_A</h1><p>候选召回改善，最终尖端判决未改善；参考泛化未通过。没有独立TEST，没有完整原生15Hz发布。</p><p><a href="08_reports/development_report.md">开发报告</a> · <a href="08_reports/failure_root_causes.md">全部失败帧根因</a> · <a href="04_NEW_DEV/per_frame_predictions.csv">新DEV逐帧结果</a> · <a href="03_exposed_regression/real_per_frame.csv">真实组逐帧结果</a> · <a href="07_media/key_cases/">关键诊断图</a> · <a href="reproduce.md">复现命令</a></p><p>新DEV候选583→621；最终仍553。视频显示原图、冻结A、最终回退/确认输出；疑似候选只在key_cases诊断图中。真实精度N/A，15FPS只是播放速度。</p><div class="grid">{links}</div></html>'''
 write(RUN/'index.html',page);write(RUN/'07_media/index.html','<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=../index.html"><a href="../index.html">交付入口</a>')
 print('REPORT DONE',decision,flush=True)
if __name__=='__main__':execute()
