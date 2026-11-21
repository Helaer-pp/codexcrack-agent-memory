from common import *
from evaluate import SENTINELS
import numpy as np,difflib,shutil,collections
def table(headers,rr):
 def fmt(v):
  if v is None or v=='':return 'N/A'
  if isinstance(v,float):return f'{v:.3f}'
  return str(v).replace('|','/')
 return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(fmt(v) for v in r)+' |\n' for r in rr)+'\n'
def main():
 summary=rows(OUT/'experiments/comparison_by_group.csv');lookup={(r['variant'],r['dataset_id']):r for r in summary};perf=rows(OUT/'performance_breakdown.csv');cost=rows(OUT/'experiments/search_cost_comparison.csv');ev=rows(OUT/'experiments/selected_visible_eval.csv');el={(r['variant'],r['dataset_id'],int(r['frame_id'])):r for r in ev};failure=rows(OUT/'failure_first_divergence.csv');fl={(r['variant'],r['dataset_id'],int(r['frame_id'])):r for r in failure};safety=read(OUT/'tests/safety_summary.json');traceaudit=read(OUT/'tests/native_trace_contracts_summary.json');assert traceaudit['status']=='PASS'
 p=lambda tag,g='ALL':next(r for r in perf if r['variant']==tag and r['dataset_id']==g and r['scope']=='time_total_native_ms')
 old=rows(F/'experiments/B0_candidate_reachability.csv');aerr=[float(r['A0_error_px']) for r in old if r['visibility']=='VISIBLE' and r['A0_error_px']];oldhits=[sum(r[f'raw_hit{tol}']=='True' for r in old) for tol in [3,5,10]]
 gates=[dict(gate='G0',status='PASS',evidence='31 protected identities +468 sealed R05F artifacts; B0 stateless80 exact. Prior1565 A/B full records preserved; no fresh full A/B rerun.'),dict(gate='G1',status='PASS',evidence=f'Compiled native dependent cross-sections;640 detailed traces audited,{traceaudit["dependent_scans"]} dependent scans. Legal seeded real trajectories in all4 groups. Mechanism only.'),dict(gate='G2',status='FAIL',evidence='Bounded beam/gaps/2-3pixel weak observations implemented; synthetic12/24/40px gaps recover. Real overrun and parallel-scratch misassociation prevent acceptance.'),dict(gate='G3',status='FAIL',evidence='Diagnostic/AUTO separated; coherent wrong first-lock proposal and original R03 failure remain. All observed disabled is NOT a safety pass.'),dict(gate='G4',status='NOT_IMPLEMENTED',evidence='reference_off; no same-material motion alignment or independent reference gain claimed.'),dict(gate='G5',status='PASS',evidence='EXECUTION_AND_EVIDENCE_ONLY: full1565 x4 automatic variants,80 diagnostic cases,76visible+4uncertain scoring,all-frame images and video; accuracy/deployment NOT passed.'),dict(gate='VALIDATION_ONLY',status='BLOCKED',evidence='G2/G3 failed; group_c and three-point-bend new image/label reads0.'),dict(gate='PRODUCTION',status='NOT_AUTHORIZED',evidence='Production sources/ABI/DLL/package/config untouched; current research cannot be deployed.')]
 save(OUT/'acceptance_matrix.csv',gates)
 versions=read(OUT/'baseline_manifest.json')['protected'];beam=lookup['E1_BEAM','ALL'];seedbeam=lookup['E0_BEAM','ALL'];greedy=lookup['E0_GREEDY','ALL'];native=p('E1_BEAM')
 report='# R05G 方向横截面逐步追踪：开发与可证伪验证\n\n'
 report+='本轮**真正编译并运行了方向约束的横截面逐步前进**：后一个截面由前一个当前观测/显式缺失状态决定，不是预设大 ROI 静态铺窗。已完成四开发组1565帧、4个自动变体共6260次原生调用，以及80帧独立短起点对照。**结论：G1机制通过；G2多假设的实际归属/终止效果失败，G3首次锁定安全失败；不替换生产，不进入验证组。**\n\n'
 report+='[全部1565帧局部对比](galleries/all_frames.html) · [80选帧详细图册](galleries/index.html) · [完整序列视频](R05G_All_Development_Frames.mp4) · [80选帧慢速审阅视频](R05G_Selected_Evidence.mp4) · [逐帧图像打包](R05G_Local_Comparisons.zip)\n\n'
 report+='## 阶段门与身份\n\n'+table(['Gate','状态','证据'],[[r['gate'],r['status'],r['evidence']] for r in gates])
 report+=f'研究 A55a0：`{versions["output/build/src/cpp/a/Release/CrackV4.dll"]}`，用于原R02/R05D/R05E同版本比较。历史发布A1c742：`{versions["output/releases/A_Win64_OpenCV440/bin/CrackV4.dll"]}`，仅身份保护，不混入本轮精度。两者既有403帧正式输出差异不是本轮回归。新R05G DLL：`{sha(BUILD/"Release/R05G.dll")}`。\n\n'
 report+='G0重放R05F B0的80个选帧，非计时输出80/80完全一致；原468件封存产物校验通过。原A与R05F的1565帧全回放沿用已封存结果并核对SHA，**没有把沿用记录描述为本轮再次完整跑A/B**。详见[基线审计](G0_check.json)。\n\n'
 report+='## 数据与干预边界\n\n'
 report+='开发：GROUP_A551、CT2 468、开发组H410、CT3 136，共1565帧。评分沿用同一76 VISIBLE（19/20/18/19）和4 UNCERTAIN；其余1485帧无本轮人工选帧标注。全部1565帧中其余1489帧不进入可见端点精度分母。验证组C562与三点弯520为验证专用，本轮未准入；排除组X不读原图/标签。LabelMe只在原生规则冻结后用于离线评分、归因和展示，无训练、参数拟合、阈值搜索或在线读取。\n\n'
 report+='E0使用单独冻结的80个“点+切向”，由当前原图起始短段/物理缺口先验人工读图选择，干预量80点+80角度，不给完整路径、尖端或中途修正。9个读图不确定起点保留 `NOTCH_PRIOR_UNCERTAIN`；不是已认证的正确起点上限。离线审计后76可见帧中71个种子满足距人工路径≤5px、切向差≤25°，该条件只形成诊断子集，未用于重选种子或参数。E1入口不接收种子文件。证据见[种子来源](seeds/provenance_lock.json)、[种子坐标](seeds/diagnostic_seeds.json)、[有利起点审计](experiments/favorable_start_comparison.csv)。\n\n'
 report+='## 实现和边界\n\n'
 report+='`tracker.hpp`实现当前灰度双线性采样、法向多尺度暗谷、每截面最多3个极值、最近最多9个真实观测点的局部PCA方向拟合和限幅、显式缺失及重捕获、有限束合并/裁剪和局部前后终止探测。方向由P1/P2右法向和当前中心轨迹决定，不是全局+x。暗谷阈值3、强观测8、两侧灰度75；半宽8–24px，步长1–3px；缺失预算24–64px，均为四组共同规则。根种子没有自动冒充当前可见点；推断点不改变观测方向，也不能成为正式尖端。\n\n'
 report+='在线预算：4096截面、24000节点、50万唯一访问像素、400万双线性样本、50ms，纵向上限clamp(4.5×P1P2距离,256,2048)px。达到任何限制输出 `search_incomplete`，不宣布终止。高容量诊断只提高容量/关闭时间截断，**仍保留2048px纵向上限，因此不是无界搜索**。reference、独立身份认证、可信历史导航尚未实现；正式 `observed=false, predicted=false, tip=null`，这里fallback为空研究输出，不是偷偷输出A的尖端。`tracking_tip`与 `proposed_observed`均为未经身份认证的诊断字段。\n\n'
 report+='AUTO贪心有一个需明确的实现边界：起源阶段最多给3个起点，首轮并行展开后才收敛至宽1，所以其 `max_active_beam`可为3；E0单种子贪心才是严格全程宽1。有限束上限4实测成立。追加完整压缩trace审计后，1565帧三组自动消融的起点列表逐字段完全一致（4695对）；所有实际选中链也核对了前后依赖。无跨历史回环身份审计，只有当前方向约束、同层合并和预算限额。\n\n'
 report+='与R05F有算子差异：R05F用局部2D重采样/平滑再按列成段；本轮沿切向±0.8px做三点采样，沿法向[1,2,1]平滑，取消至少4列成段门。共享暗谷思路和最低对比约束，但**B0→G1不是仅搜索组织变化的严格单因素A/B**。E0的束宽比较、E1的无GAP/强观测比较则使用同一冻结原生算子；同起点完整核对见[记录](experiments/full_automatic_seed_pairing_audit.csv)。\n\n'
 report+='## 同分母结果：真实确认与暂定端点分别计数\n\n'
 report+=f'旧研究A在76帧中确认{len(aerr)}，≤3/5/10px分别{sum(e<=3 for e in aerr)}/{sum(e<=5 for e in aerr)}/{sum(e<=10 for e in aerr)}；>100/500px分别{sum(e>100 for e in aerr)}/{sum(e>500 for e in aerr)}。R05F B0候选≤3/5/10px为{oldhits[0]}/{oldhits[1]}/{oldhits[2]}，没有正式确认输出。\n\n'
 report+='**R05G所有变体正式确认均0/76；正式≤3/5/10均0/76，拒绝76、预测0；确认子集P50/P95/max为N/A。正式>100/500错误确认数虽为0，原因是身份功能未通过而被禁用，绝不能据此声称安全通过。** 下表完全是未确认轨迹诊断：\n\n'
 tags=['E1_GREEDY','E1_BEAM','E1_NO_GAP','E1_STRONG','E0_GREEDY','E0_BEAM','E0_CAPACITY_GREEDY','E0_CAPACITY_BEAM']
 report+=table(['变体','暂定端点数/76','≤3/5/10px /76','>100/500px','候选≤10 /76','路径覆盖10均值','路径精度10均值','路径+端点共同支持 /76','不完整/76'],[[tag,lookup[tag,'ALL']['tentative_tips'],'/'.join(lookup[tag,'ALL'][f'tentative_hit{k}'] for k in [3,5,10]),lookup[tag,'ALL']['tentative_over100']+'/'+lookup[tag,'ALL']['tentative_over500'],lookup[tag,'ALL']['candidate_hit10'],float(lookup[tag,'ALL']['mean_full_path_coverage10']),float(lookup[tag,'ALL']['mean_visible_path_precision10']),lookup[tag,'ALL']['path_and_endpoint_supported10'],lookup[tag,'ALL']['incomplete']] for tag in tags])
 report+='路径覆盖为约1px采样的人工路径被实际可见轨迹10px带覆盖比例；路径精度为实际可见轨迹中落在人工路径10px带内的比例，均不将推断缺口画成可见线。共同支持要求种子后覆盖≥90%、可见路径精度≥90%且暂定端点≤10px。路径精度仅对有轨迹者求均值，不能作为全部76的准确率。初次评测后补加了路径精度与更严格合取，原覆盖+端点指标原样保留，未改原生参数，见[追加指标审计](experiments/additional_metric_scope.json)。随机空间密度对照已逐帧记录，它是实际访问条带外接框内1000个均匀点的候选邻近率，不是实际无裂纹FPR。\n\n'
 report+='E0虽几乎覆盖整条标注路径，随后大量延伸到无关纹理，故不能将98.6%路径覆盖叫“98.6%识别准确率”。E1_STRONG端点诊断29/76优于E1_BEAM的9/76，但开发组H78弱末端丢失且CT3仍无起点；不能按这一列把强阈值变体升级生产。所有失败帧保留。\n\n'
 report+=table(['E0_BEAM组','可见分母','暂定≤10','路径覆盖10','路径精度10','共同支持'],[[g,lookup['E0_BEAM',g]['visible'],lookup['E0_BEAM',g]['tentative_hit10'],float(lookup['E0_BEAM',g]['mean_full_path_coverage10']),float(lookup['E0_BEAM',g]['mean_visible_path_precision10']),lookup['E0_BEAM',g]['path_and_endpoint_supported10']] for g in DEV])
 report+='4 UNCERTAIN全部单列输出；它们既不是准确率样本，也不是已知无裂纹负例。真实无裂纹FPR=N/A。全1565的AUTO束搜索原始几何确认建议280次，其中可见选帧13次，6次误差>100px、3次>500px，独立身份认证缺失具有实际危险，不能只看最终守卫拒绝了全部建议。\n\n'
 report+='## 九个指定案例与首失效\n\n'+table(['案例','AUTO贪心误差','AUTO束误差','诊断贪心误差','诊断束误差','AUTO束首失效（步）'],[[f'{g}/{f}']+[float(el[tag,g,f]['tracking_error_px']) if el[tag,g,f]['tracking_error_px'] else None for tag in ['E1_GREEDY','E1_BEAM','E0_GREEDY','E0_BEAM']]+[fl['E1_BEAM',g,f]['stage']+' ('+fl['E1_BEAM',g,f].get('step','')+')'] for g,f in SENTINELS])
 report+='GROUP_A504自动束在真末端后转向边缘纹理，贪心未这样偏移。CT2/196、431、457均以过度延伸为主要可定位现象，不能继续归因于R05F最短片段门。开发组H41存在提前丢失/重捕获差异，115在有缺失与弱观测的束路径中恢复到10px内。CT3/65原A约8.408px的正回归守卫未通过：AUTO无起点，诊断则越过真实末端继续追背景。\n\n'
 report+='CT3全部136帧AUTO无起点。20选帧起源审计显示最多2个连续合格截面，达不到3；法向、宽度尺度与强度门均有拒绝，不能笼统称为“没有暗线”。[起源逐候选拒绝审计](experiments/origin_candidate_audit.csv)保留实际阈值、坐标和拒绝原因，本轮没有看标签后放宽这些门。\n\n'
 report+='首失效表保存所有选帧与各变体的原生step/scan/node链接。`DIRECTION_OR_CURRENT_RESPONSE`、`GAP_REACQUISITION_OR_EARLY_STOP`是证据不足的复合归因，不冒充唯一已证实根因；`IDENTITY_UNVERIFIED`表示轨迹暂定端点已在容差内但仍不能确认。另见[首失效明细](failure_first_divergence.csv)、[截面灰度与响应曲线](experiments/profile_plot_index.csv)。\n\n'
 report+='### 开发组H78的两列/三列证据\n\n'
 report+='原R05F窗口55/56的两列端点(2797.906748,755.659093)距GT0.288px，本轮E1_BEAM在实际第123、124步选中其3px邻域的当前观测，三列片段在第118/119/120/123步附近接入；原像素双线性支持地址交集、原生响应与子节点保留信息已写入[完整审计](tests/group_h78_short_fragment_audit.json)。E1_GREEDY两列对应第121/122步。禁用GAP或仅强观测未接入这一末段。\n\n'
 report+='这修复了原先“有短响应但无法进入任何轨迹”的局部问题；AUTO束最终暂定端点仍有6.22px误差，并有末端噪点误接可能，不能称主裂纹身份/可信终止已解决。低对比原像素和仅供显示的[249,255]线性拉伸一起交付，拉伸不进入算法。[原像素放大图](galleries/images/group_h78_raw_pixels.png) · [四变体放大](galleries/images/sentinel_group_h_78.jpg) · [实际截面响应](galleries/images/profile_group_h_78.png)。\n\n'
 report+='## 计算与安全压力测试\n\n'+table(['AUTO变体','P50 ms','P95 ms','P99 ms','max ms','>50ms','全帧不完整'],[[tag]+[float(p(tag)[k]) for k in ['p50','p95','p99','max']]+[p(tag)['over50'],p(tag)['incomplete']] for tag in ['E1_GREEDY','E1_BEAM','E1_NO_GAP','E1_STRONG']])
 report+='环境为Ryzen9 7950X、MSVC v142 /O2 /fp:precise、OpenCV4.4线程设置4；当前采样追踪主体是标量实现，不宣称4线程并行加速。全帧包含冷启动，未丢弃warm-up；原生时间包含追踪审计结构维护，80选帧额外保留完整profile。I/O解码哈希、JSON导出、Python壁钟、原生分项分别在[性能表](performance_breakdown.csv)，视频10fps是播放速度。当前完整调试JSON导出P95约69.19ms、文件读取解码哈希P95约183.55ms；process内核时间绝不是当前Python/调试API端到端延迟。目标i7和内存峰值均NOT_VERIFIED。\n\n'
 report+='E1_BEAM P95约17.33ms，较旧B0约105.03ms降低，但353/1565搜索不完整，且CT3 136帧根本未初始化；**不据此宣布满足完整检测50ms目标**。\n\n'+table(['组','B0候选中位数','新观测子节点中位数','选中可见中心中位数','截面中位数','唯一原像素中位数','新/旧访问比中位数','不完整'],[[r['dataset_id']]+[float(r[k]) for k in ['median_B0_retained_candidates','median_observation_children','median_selected_visible_centers','median_scanlines','median_unique_pixels','median_visit_ratio_to_B0']]+[r['incomplete']] for r in cost if r['variant']=='E1_BEAM' and r['dataset_id']!='ALL'])
 report+='B0候选与新观测状态是不同单位，不能把相减称为误检减少。CT2中位观测子节点2326.5还多于B0候选2127.5；束搜索重复采样很高。新唯一像素为实际四邻双线性地址去重，旧B0为原静态采样足迹估计，访问比只作方向性参考。全图bitset用于访问计数，不是读取全图灰度/第二路径器；没有静态ROI暗线撒点回退。\n\n'
 report+=f'合成压力测试{ safety["synthetic_cases"]}项中{ safety["passed"]}项通过；失败/未实现项为：'+', '.join(safety['failed'])+'。12/24/40px缺口的贪心和束均恢复，无GAP对照停在缺口前；2/3列弱响应进入候选。平行划痕构造中束错误走到(651.12,255.61)，正确合成末端为(420,250)，贪心未犯同样错误。恒灰、低纹理、阴影反光、开闭合、异常P1/P2、分辨率变更、边界、重复帧、丢帧/跳变均有实际调用记录；双侧参考错位测试只是reference_off对照，不是已实现对齐的验证。原R03原样16项中 `coherent_wrong_first_lock`仍失败（退出码2）。\n\n'
 report+='[合成矩阵](tests/synthetic_matrix.csv) · [原R03矩阵](tests/R03_original_fault_matrix.csv) · [640份原生逐步不变量审计](tests/native_trace_contracts_summary.json)。\n\n'
 report+='## 必须直接回答的九个问题\n\n'
 trace=read(OUT/'traces/E1_BEAM_group_h_78.json');examples=[]
 for node in [n for n in trace['selected_path'] if n['visible']][3:8]:
  scan=trace['scans'][node['scan']];parent=trace['nodes'][node['parent']];examples.append([node['step'],parent['xy'],scan['predicted_point'],node['xy'],node['strength']])
 report+='1. **真正逐步推进了吗？** 是。640份完整trace的全部追踪截面均核对了 `pred-parent = positive_step × parent_tangent`，最大步长≤3px；不是全ROI枚举。以下为开发组H78连续实际步号，完整窗口多边形、法向profile、候选、children、裁剪原因均在trace：\n\n'+table(['step','前一中心','预测中心','所选当前中心','原生强度'],examples)
 report+=f'2. **有利起点能走到当前可见末端吗？** 只能部分做到。E0贪心/束的全部76帧端点10px为{greedy["tentative_hit10"]}/{seedbeam["tentative_hit10"]}；已离线核对的71个有利起点子集中仍仅12/14正确，分别约16.90%/19.72%。CT2、CT3均无端点10px成功；路径经过GT后继续延伸是主要问题。各帧第一次离轨和未定根因不删除，见首失效CSV。\n\n'
 report+='3. **开发组H78两列是否接入？** 是，在AUTO束123/124步进入实际选中链；但端点误差6.22px且身份未验证，只能说弱片段可追踪性改善，不能说最终可信尖端通过。\n\n'
 seeded=rows(OUT/'experiments/seeded_frame_summary.csv');timing={tag:np.percentile([float(r['time_total_native_ms']) for r in seeded if r['variant']==tag],[50,95]).tolist() for tag in ['E0_GREEDY','E0_BEAM']}
 report+=f'4. **同种子贪心与束有什么净差异？** E0候选10px72→75、暂定端点10px12→14，>100px51→52、>500px24→27；原生P50/P95分别{timing["E0_GREEDY"][0]:.3f}/{timing["E0_GREEDY"][1]:.3f}ms与{timing["E0_BEAM"][0]:.3f}/{timing["E0_BEAM"][1]:.3f}ms。合成跨隙都可恢复，束另有平行划痕错误；因此不认定束整体通过。提高容量端点成绩仍12/14，不能解决核心错误。±2px/±5°种子扰动的全部80帧结果原样记录，未挑最好种子。\n\n'
 report+='5. **自动首次误锁解决了吗？** 没有。真实AUTO 192/1565无起点，CT3全部136无起点；连贯旧划痕仍得到 `proposed_observed=true`，原R03仍失败。正式observed全部关闭是缺少身份功能的隔离守卫，不是“全拒绝解决安全”。\n\n'
 report+='6. **计算/状态数量减少多少，有隐藏大ROI吗？** 上表逐组报告。实际访问面积显著收缩，束仍大量重叠采样；CT2状态数没有降低。CT3的低成本来自失败初始化，不能记为同任务加速。只有近起源有界扫描和前沿按需截面，没有全ROI静态候选池。\n\n'
 report+='7. **76帧实际observed、准确率和拒绝是多少？** 正式observed0、≤3/5/10全0、拒绝76、预测0；确认误差分位数N/A，0个错误确认没有安全证明意义。AUTO束13/76搜索不完整；全1565不完整353。未确认暂定误差和候选召回严格另列，未用其代替正式精度。\n\n'
 report+='8. **参考是否真的启用？** NOT_IMPLEMENTED，reference_attempts=0。初始化只保存图像尺寸；没有同材料匹配、两侧运动对齐、增量参考评分或参考收益声明。历史导航同样NOT_IMPLEMENTED/NOT_EXERCISED。E1按序回放，但除图像尺寸与帧计数器外实际上逐帧独立，没有声称因果历史带来收益。\n\n'
 report+='9. **下一步主要瓶颈是什么？** 优先是“经过真实端点后仍将别的暗点接成长链”的归属与停止判断，以及CT3起源门失效/错误首次身份。短弱片段本轮已有实际接入证据，单纯放宽它会加重噪点误接。建议保留当前冻结E0作为机制对照，下一轮先明确保留较早的可信停止候选与后续探索支路之间的身份竞争，再对自动起源建立独立可证伪证据；不要扩大束/预算、从GT拟合阈值或用历史最长端点兜底。参考对齐仍属未验证后续研究，不能提前宣称可解决划痕。\n'
 (OUT/'development_report.md').write_text(report,encoding='utf8')
 limitations='''# 明确限制

- G2/G3 FAIL；全拒绝不是安全成功；所有tracking_tip仅为暂定轨迹端点。
- G1仅验证当前暗谷的前后依赖步进；复杂归属、真正独立终止认证、可信历史导航、参考运动对齐均未通过/未实现。
- AUTO贪心首轮可有3个起源候选，之后才是宽1；严格单种子宽1对照为E0。
- CT3全部136帧自动初始化失败；不能因其很快就认定性能达标。
- AUTO束353/1565搜索不完整，静态B0覆盖与逐步追踪覆盖不同；速度与正确完整检测不可混同。
- 高容量诊断仍有纵向2048px上限；不能称真正无界对照。
- 只对76可见帧评分，4不确定不当负例；无可靠真实无裂纹集，FPR=N/A。
- 种子是当前原图近起源的一点+切向，不是用户认证的正确路径。71/76满足离线有利起点审计，未据此剔除其他帧。
- R05F对照算子与新法向采样算子有差异，搜索组织净收益存在算子混杂。
- 新像素访问计数精确，旧B0足迹估计不同；访问比不能冒充严格同口径比值。
- 标量采样实现，OpenCV线程设置4；i7性能/内存峰值NOT_VERIFIED。
- 相同原图中连贯划痕与裂纹可有不可观测歧义；未实现独立身份证据。
- 合成双侧运动测试只证明关闭参考不产生该依赖，不证明运动估计可用。
- 首失效复合原因明确保留未定项；没有为每帧编造唯一根因。
- 验证组C、三点弯BLOCKED；排除组X排除；标签不训练、不调参、不进入运行时。
''';(OUT/'limitations.md').write_text(limitations,encoding='utf8')
 (OUT/'design_decisions.md').write_text('''# 设计与受控决定

先G1贪心原生编译和真实逐步证据，再启用G2编译开关；G1构建分别保存在g1_build/和g1_final_build/。初次AUTO CT3门失败保留在G1_auto_initial_gate.json；使用文档允许的独立短起点证明基本追踪机制，没有通过调参把自动初始化失败改成成功。

原生规则在E1_pre_run_lock.json中冻结后再读LabelMe。E0、AUTO分别调用不同C ABI；AUTO无seed形参。seeded模式永不写正式历史。原始种子不是当前观测，必须由后续截面生成当前响应；根节点visible=false。

beam=4保留至多3个当前极值和缺失选项；合并条件使用同源、中心距离<2px、切向点积>.985及相同可见状态。分数是最近质量EMA和可见比例，缺失按距离惩罚，不按累计总亮暗积分无条件奖励长线。终点暂按可见前进最远选择，所以当前独立归属/停止仍失败，不能确认。

原生trace只导出真实访问的profile和坐标。GT不参与横截面中心、方向、候选、束分数或预算。完整1565帧起源列表核对4695对完全相同；无历史消融因功能未实现标NOT_EXERCISED，不重复一个空操作变体冒充实验。

增加可见轨迹精度是离线指标的补充审计（首次评分后），不改变检测器、种子或原覆盖指标。没有按这一指标选择新配置。
''',encoding='utf8')
 (OUT/'source_dependency_map.md').write_text('''# 源码依赖与证据责任

```mermaid
flowchart TD
 A[原图 + 当前P1/P2] --> R[replay.py: AUTO全前缀]
 A --> E[seeded_replay.py: 隔离E0/E2]
 S[独立短起点文件] --> E
 R --> C[runtime.cpp C ABI]
 E --> C
 C --> T[tracker.hpp 局部采样/方向/beam/gap/终止提议]
 T --> L[真实逐截面日志与未确认轨迹]
 L --> V[evaluate.py 离线比较]
 GT[LabelMe只读开发成员] --> V
 V --> M[media.py 原图对比/视频]
 L --> M
```

生产src/cpp/a/CrackV4.cpp与roi_tip.inc：旧参考门/局部DP/最终确认；本轮未改。R05F research/uctt_r05f/current.hpp：静态窗口暗谷、4列短分量门；仅通过原研究runtime做80选帧重放。历史发布DLL1c742与研究55a0分别冻结，A0_frames.jsonl仅来自55a0。

新tracker.hpp::crossSection只读当前灰度；originSeeds做有界近起源搜索；track做真实前后依赖扩展；fittedDirection只用visible节点；terminalAudit只给局部停止与几何建议，无独立身份认证。runtime.cpp永不把建议写observed。reference图只用于初始化尺寸。

native.py是无标签ctypes桥；replay.py没有种子或LabelMe入口；seeded_replay.py只读独立短种子；evaluate.py/weak_audit.py/origin_audit.py/profile_plots.py/media.py负责离线证据。原图读取先执行dataset_policy。所有编译、日志、图片与视频均在output/。
''',encoding='utf8')
 commands='''# 编译与复现

工作目录：`.`。Python为`D:/ProgramData/anaconda3/python.exe`，CMake为`D:/CMake/bin/cmake.exe`。OpenCV使用项目third_party/opencv440，VS2022生成器、x64、v142、Release /O2 /fp:precise /utf-8。

本run已封存，**不要覆盖它**。完整复现先将research/uctt_r05g/common.py的OUT改为output/runs/下一个未存在的新run目录；仅输出位置变化，原生参数不变。原图F盘只读。

```powershell
$env:PYTHONPYCACHEPREFIX='./output/pycache'
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/prepare.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/baseline_check.py
& D:/CMake/bin/cmake.exe -S research/uctt_r05g -B output/build/uctt_r05g -G 'Visual Studio 17 2022' -A x64 -T v142 -DR05G_ENABLE_BEAM=OFF
& D:/CMake/bin/cmake.exe --build output/build/uctt_r05g --config Release -- /m:1 /nr:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/g1_check.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/seed_sheets.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/diagnostic_seeds.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/g1_seeded.py
# 必须检查G1_gate机制PASS后才启用beam；保持原诊断种子、不要重新择优。
& D:/CMake/bin/cmake.exe -S research/uctt_r05g -B output/build/uctt_r05g -DR05G_ENABLE_BEAM=ON
& D:/CMake/bin/cmake.exe --build output/build/uctt_r05g --config Release -- /m:1 /nr:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/replay.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/seeded_replay.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/contracts.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/evaluate.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/tables.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/evidence_audit.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/full_trace_metrics.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/origin_audit.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/weak_audit.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/profile_plots.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/media.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/weak_display.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/report.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/delivery.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/seal.py
```

R03Original对既有fault_seed.txt退出码2是预期复现的已知失败，不应修改原矩阵令它通过。完整原生参数见冻结tracker.hpp，代码新增清单及diff见code_diff.patch。修改后再复现时记录新SHA与新输出目录，不冒充同一冻结实验。
'''
 for name in ['build_and_reproduce.md','reproduction_commands.md']:(OUT/name).write_text(commands,encoding='utf8')
 write(OUT/'dataset_access_audit.json',dict(development_unique_original_frames=1565,development_groups=dict(group_a=551,ct2=468,group_h=410,ct3=136),automatic_native_calls=6260,diagnostic_selected_frames=80,diagnostic_variant_calls=640,selected_label_members=80,visible=76,uncertain=4,validation_new_images=0,validation_label_members=0,excluded_new_images=0,excluded_label_members=0,whole_zip_hashing='identity-only bytes; validation members never parsed',label_use='offline comparison/QC/plots only',training=False,parameter_fitting=False,source_manifest='image_access_log.csv',annotation_manifest='annotation_access_log.csv',seed_provenance='seeds/provenance_lock.json',runtime_entry='AUTO has no diagnostic seed / filename / label input',reference='NOT_IMPLEMENTED',history_navigation='NOT_IMPLEMENTED / NOT_EXERCISED'))
 print('REPORT COMPLETE',flush=True)
if __name__=='__main__':main()
