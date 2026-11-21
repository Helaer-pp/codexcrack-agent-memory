from common import *
import numpy as np,collections,shutil,difflib,platform

def truth(v):return str(v).lower() in ['true','1']
def main():
 assert read(OUT/'tables_complete.json')['full_frames']==1565
 reach=rows(OUT/'experiments/candidate_reachability.csv');group=rows(OUT/'experiments/comparison_by_group.csv');frames=rows(OUT/'experiments/B0_frame_metrics.csv');perf=rows(OUT/'experiments/performance.csv');probe=rows(OUT/'stateless_budget_x8/offline_reachability.csv')
 allsum=next(r for r in group if r['dataset_id']=='ALL' and r['split']=='all')
 sentinel={(r['dataset_id'],int(r['frame_id'])):r for r in reach if (r['dataset_id'],int(r['frame_id'])) in [('ct2',395),('group_h',78),('group_a',504),('ct3',65)]}
 assert not truth(sentinel['group_h',78]['raw_hit10'])
 incomplete=[r for r in frames if truth(r['search_incomplete'])]
 clean=next(r for r in perf if r['dataset_id']=='ALL' and r['variant']=='B0')
 release=read(OUT/'release_equivalence.json')
 release_fields=read(OUT/'release_field_summary.json')
 gates=[dict(stage='S0',status='PASS',reason='1565 frames of the explicitly scoped R02/R05D/R05E 55a0 research-build baseline, source clone and saved results are exactly equal. R01/R02 explicitly identify 1c742 as a different historical release, not an equivalent AB baseline',evidence='A0_equivalence.csv; baseline_scope.md; baseline_timings.csv'),dict(stage='HISTORICAL_RELEASE_IDENTITY',status='NOT_VERIFIED',reason=f'NOT THE SAME VERSION: full digest same {release["exact"]}/1565; formal same {release_fields["formal_exact"]}/1565. This is a documented historical version boundary, not an R05F regression or permission to deploy',evidence='release_equivalence.csv; release_field_equivalence.csv; baseline_scope.md'),dict(stage='S1',status='FAIL',reason='current evidence decoupled, but group_h78 weak ridge filtered before segment endpoint: nearest retained12.221px; 7 full-sequence segment-budget hits',evidence='experiments/candidate_reachability.csv; pixel_audit/response_to_segment_audit.json; stateless_budget_x8/offline_reachability.csv')]
 gates[1]['stage']='HISTORICAL_RELEASE_SEPARATION';gates[1]['status']='PASS'
 for stage in ['S2','S3','S4','S5','S6']:gates.append(dict(stage=stage,status='BLOCKED',reason='S1 sentinel failure; strict stage order; no later-version metric rescue or validation-only tuning',evidence='S1_gate.json; development_report.md'))
 gates.extend([dict(stage='TARGET_I7_50MS',status='NOT_VERIFIED',reason='host is Ryzen9 7950X; S1-only measured time is not complete pipeline time',evidence='experiments/performance.csv'),dict(stage='REAL_T2B',status='NOT_VERIFIED',reason='no new independent physical upstream trajectories supplied',evidence='baseline_manifest.json'),dict(stage='PRODUCTION_REPLACEMENT',status='BLOCKED',reason='no accepted stepwise/association/terminal/history implementation; original first-lock safety failure persists',evidence='tests/r03_original.csv')])
 save(OUT/'acceptance_matrix.csv',gates)
 write(OUT/'S1_gate.json',dict(status='FAIL',current_reference_independence='PASS',development_frames=1565,visible=76,raw_hits={k:int(allsum[f'raw_hit{k}']) for k in [3,5,10]},dedup_hits={k:int(allsum[f'dedup_hit{k}']) for k in [3,5,10]},sentinels=list(sentinel.values()),incomplete_frames=len(incomplete),failure='group_h78 near-tip 2/3-column ridges rejected by minimum4-column segment condition; x8 capacity does not recover candidates',later_stages='BLOCKED'))
 branches=[dict(name='A0',status='RUN',frames=1565,meaning='frozen current production baseline; profile-only clone exact',lock='A0_replay_lock.json'),dict(name='B0',status='RUN_S1_FAIL',frames=1565,meaning='current-only native small-window static coverage; no reference, step, association, terminal or trusted history',lock='B0_lock.json'),dict(name='S1_capacity_x8',status='OFFLINE_DIAGNOSTIC',frames=80,meaning='all selected DEVELOPMENT frames; stateless fixed x8 candidate/segment capacity; not online ablation and not a parameter choice',lock='stateless_budget_x8/lock.json')]
 for name in ['B1','B2','B3','B3_no_ref','B3_no_gap','B3_no_history']:branches.append(dict(name=name,status='BLOCKED',frames=0,meaning='S1 failed; no implementation/accuracy fabricated'))
 normalized_lock={k.replace('\\','/'):v for k,v in read(OUT/'B0_lock.json')['files'].items()}
 write(OUT/'experiments/ablation_manifest.json',dict(branches=branches,full_prefix_required=1565,comparison_sha=normalized_lock['research/uctt_r05f/compare.py'],dataset_roles=read(POLICY_PATH),validation_run=False,production_modified=False))
 # Existing validation records only. No validation image/annotation opened.
 val=[dict(dataset_id=r['dataset_id'],frame_id=r['frame_id'],result_hash=r['result_hash'],observed=r['observed'],tip=r['tip'],evidence_type='EXISTING_R05D_BASELINE_RECORD_NOT_NEW_EVALUATION') for r in map(json.loads,(D/'val_frames.jsonl').read_text().splitlines()) if r['dataset_id'] in VAL]
 assert len(val)==1082;save(OUT/'existing_validation_baseline_records.csv',val)
 write(OUT/'validation_status.json',dict(status='BLOCKED',reason='S1 did not pass; S5 development comparisons incomplete; do not consume validation for development',new_validation_images_opened=0,new_validation_annotations_opened=0,existing_baseline_records=len(val),previous_exposure=True,independent_test=False))
 sent_table='\n'.join(f'| {g}/{f} | {float(r["raw_nearest_px"]):.3f} | {float(r["dedup_nearest_px"]):.3f} | {"是" if truth(r["dedup_hit10"]) else "否"} | {r["A0_error_px"] or "无确认输出"} |' for (g,f),r in sentinel.items())
 group_table='\n'.join(f'| {r["dataset_id"]} | {r["visible"]} | {r["A0_observed"]} | {r["A0_hit5"]} | {r["A0_over100"]}/{r["A0_over500"]} | {r["raw_hit3"]}/{r["raw_hit5"]}/{r["raw_hit10"]} |' for r in group if r['split']=='all')
 performance_table='\n'.join(f'| {r["dataset_id"]} | {r["variant"]} | {r["n"]} | {float(r["p50_ms"]):.2f} | {float(r["p95_ms"]):.2f} | {float(r["p99_ms"]):.2f} | {float(r["max_ms"]):.2f} | {r["over50"]} |' for r in perf if r['variant'] in ['B0','A_RELEASE'])
 old=rows(E/'evaluation_B2_dev.csv');oldraw=sum(truth(r['raw_candidate10']) for r in old);oldkeep=sum(truth(r['retained_candidate10']) for r in old)
 report=f'''# R05F 开发验证：指定基线S0通过，S1弱短片段保留失败

本轮完成了隔离 C++ 当前暗线发现、开发组1565帧全前缀回放、76 VISIBLE / 4 UNCERTAIN离线对比、80帧固定容量干预及10帧29个真实访问窗口的逐像素归因。**S0 PASS、S1 FAIL，S2–S6 BLOCKED，生产未修改。** 步进、多前沿、两侧材料配准、主裂纹归属、最终终止和可信历史尚未实现/验收，不是已经完成的替换算法。

S0通过范围明确为历轮R02/R05D/R05E使用的构建DLL55a0…与当前源码克隆、R05D记录，1565帧完全一致。项目配置中的发布DLL1c742…另行核对：完整摘要0/1565相同，formal输出{release_fields['formal_exact']}/1565相同，geometry诊断{release_fields['geometry_exact']}/1565相同。**R01 dependency_audit.md第25行和R02 ab_regression_report.md第3行已明确：2026-11-06发布件是历史版本，不是当前源码的无修改A/B基线。** 因此不能因这两个历史版本不等价而判本轮克隆回归失败，也不能把55a0的精度冒充1c742发布包的精度。本轮完整量化了历史边界，并纠正中途过宽的S0失败解释。两个文件均未覆盖；S1仍只是shadow研究，不是发布候选。详见 `baseline_scope.md`。

## 关键证据

独立暗线候选 raw / 去重 / 容量后，在3/5/10原图px容差下均为 **38/56/70（分母76）**。上一轮R05E同76帧 raw10={oldraw}、retained10={oldkeep}；本轮候选覆盖提高，但候选集合和计算量不同，不能视为最终尖端正确率提升。S1没有observed生产者，研究输出均为null fallback，不写可信历史。下文A0数值专指55a0…研究构建基线，不混称配置中的发布件准确率；生产文件均未改动。

| 哨兵 | 原始最近候选px | 去重后px | ≤10px | 原A最终误差px |
|---|---:|---:|---|---:|
{sent_table}

开发组H78人工尖端附近的当前响应并未消失。在实际窗口55/56中，3px邻域最大响应3.575897，存在2个NMS脊线像素。一个2列短连通分量端点距人工尖端 **0.288046px**，另一个3列分量端点距4.383354px；两者都被 `nodes.size()<4 / x-span<4 / columns<4` 排除，无法成为候选。最终留下的端点最近12.221233px。这是 **response → segment** 的确定性失败，不是参考失败，也不是可确认物理尖端的证据。详见 `pixel_audit/`：实际小窗口的score/valid/ridge/component数组及原图映射均保留。

其余 raw10 遗漏是CT2/196、431、457，开发组H/41、115；没有将10.2346px四舍五入成命中。所有失败都在完整80帧图册中。CT3/65仍在3px内；GROUP_A/504保留10px邻域候选，但不声称恢复最终确认。

## S1 实现与预算问题

`research/uctt_r05f/current.hpp` 对96–192 × 64–128小窗口按P1/P2宽松几何覆盖；四个间距归一化尺度计算当前暗谷，随后NMS、局部连通片段、端点及对比下降候选。参考图仅在初始化保存，当前证据不读取参考像素；参考全黑/有线两种构造给出相同候选。候选按1.5px邻近、15°方向、尺度及停止类型去重，保留别名来源，不取全ROI strongest-K。此处宽度字段是滤波尺度，不是经校准的物理裂纹宽度。

这仍是 **B0静态小窗对照**，不是步进搜索。窗口/片段/候选/累计访问像素上限分别192/8192/32768/4000000；面积限制在开窗前检查，最多一个窗口的有界超量须单列，不能称绝对逐像素硬限制。50ms仅为目标，当前S1不以时间截断，否则无法完成基准覆盖。全序列有{len(incomplete)}帧命中 segment_budget，全部显式 search_incomplete，不确认终止。详细候选与片段每帧都在压缩轨迹中；CSV详细层导出全部80选帧，逐帧总体指标覆盖1565帧。

GROUP_A每帧中位去重候选6160，CT2约2127.5，开发组H523.5，CT3 168。几何去重远未形成适合下游归属的紧凑结构池。7个预算截断帧的“raw”只是已枚举下界，不能冒充未截断全池。离线预声明的 **x8容量** 对全部80开发选帧恢复完整枚举，无预算命中，仍只有70/76的raw10及dedup10，没有恢复任何遗漏；这排除了本批6个尖端遗漏的容量原因，不证明未标注帧无损失，也不把x8选作在线参数。

不能为开发组H78单独降低最短片段门槛，或通过保留全图所有短噪点来宣称成功。下一步应在S1内研究可审计的弱短片段层及共享结构关联；本轮没有按人工标注拟合阈值，也没有自动参数搜索。

## 同分母结果与计算量

以下只在76个VISIBLE人工选帧上计算准确率；其他1489帧没有本轮可评分的明确尖端GT。全1565帧只有状态、候选、预算及时间审计。4个UNCERTAIN不记零误差。路径带覆盖定义为：按约1px弧长采样完整人工路径，距实际算法脊线中心≤3/5/10px的采样点比例；不是ROI包含率或暗线填满面积率。

| 组 | VISIBLE | 原A observed | 原A≤5px | 原A>100/>500px | 新候选3/5/10px命中 |
|---|---:|---:|---:|---:|---:|
{group_table}

原A总体 observed=52/76，缺输出24，≤5px=11/76（14.47%）；确认输出误差P50={float(allsum['A0_error_p50']):.3f}px、P95={float(allsum['A0_error_p95']):.3f}px、最大{float(allsum['A0_error_max']):.3f}px，>100px=28，>500px=13。新模块是shadow，没有最终可确认输出，因此最终检测精度 **N/A**，不是以0个误确认换得“安全通过”；若强行作为替代输出，覆盖将是0/76，显然不合格。没有原始no_visible_crack真负标签，真实FPR=N/A。15/5旧内部划分保留在CSV，但不是未见外部测试。

独立计时按序调用A发布包和B0；I/O、hash、Python调试JSON导出及渲染分开。A排除4次cached reference query，B0首帧是真实当前检测且计入。

| 组 | 分支 | n | P50 ms | P95 ms | P99 ms | max ms | >50ms帧 |
|---|---|---:|---:|---:|---:|---:|---:|
{performance_table}

S1本身仍有{clean['over50']}/{clean['n']}帧超过50ms；不能外推完整S2/S3/S4链的耗时。机器为AMD Ryzen9 7950X、OpenCV4.4、4原生线程，不是目标i7，目标机结果NOT_VERIFIED。S0的localReference（扣除模板匹配）、matchTemplate、score、DP（扣除审计）、terminal审计采用互斥scope；其余主链开销未被这些局部scope覆盖，不能将它们当完整总耗时。内存峰值未做独立受控测量，NOT_VERIFIED。

## 数据、工程与版本边界

开发只使用GROUP_A/CT2/开发组H/CT3。人工标签ZIP仅由离线比较/图册/失败定位读取，原图运行器不加载标签；无训练、伪标签、拟合、文件名/试件分支。排除组X后续图像/标签读取=0。S0仅记录其既有锚点文件哈希以保护历史资产，没有使用该组数据计算。

验证组C/三点弯本轮新图像和标注读取=0，锁后验证 **BLOCKED**。仅引用既有R05D验证基线1082条记录作身份对照；不得称本轮已完成1082帧新验证，也不得用其失败反调本轮参数。所有组历史均曝光，没有独立TEST。T2-A全矩阵、真实T2-B、跨10px缺口动态恢复、候选两侧参考收益及闭环归属/终止均未验收。

生产构建DLL与发布DLL分别冻结，二进制SHA不同。前者55a0…用于原有研究基线，后者1c742…按项目配置独立重放1565帧，{release['exact']}/{release['frames']}完整非计时摘要一致（{release['status']}）。逐字段差异统计见 `release_field_summary.json`；formal差异字段为 `{release_fields['formal_difference_fields']}`，geometry差异字段为 `{release_fields['geometry_difference_fields']}`。这不是只因编译时间不同而推断的版本问题，已有实际回放差异。`release_sample_differences.json`保存每组前三帧的双方完整结果，其余全帧formal/geometry差异在CSV中；不猜测尚未定位的历史源码原因。两次运行都从每组首帧开始，未重用未来状态。

生产源码、配置、标签、原图和旧封存结果均未覆盖，也没有为消除差异直接复制DLL。S1原生源码/比较器在开跑前锁定；后续只增加离线诊断与交付脚本，`B0_lock.json`与最后快照共同记录差异。CMake后加诊断target，无B0源算法改动。

完整回放前有一次因gzip level9调试压缩过慢中止的尝试，原输出保存在 `aborted_debug_compression_attempt/`，不计入正式结果；仅改level1和JSON空白后从第一帧重跑全部1565帧，没有丢弃失败帧。调试开销不是原生算法吞吐。

## 八个问题的直接回答

1. CT2/395有7.45px候选；开发组H78有近尖端原图响应，但2/3列短脊线被片段规则过滤，仍无10px候选。两者均未获得主裂纹归属/停止证明，不能成为研究observed。
2. 未进入S2，尚无步进减少远方竞争的证据。开发组H约900px生产误差仍存在；B0不输出不能算解决。
3. S2跨10+px同帧续接及防划痕跳链未实现/未验证。静态覆盖看到后段不等于实际跨隙追踪。
4. S3未启用，两侧配准/固定与合格历史参考消融及新暗线净收益均NOT_VERIFIED；没有用旧结果假装本轮收益。
5. S4未实现，尚不能从多个合格主裂纹片段中选择最远当前可见端点；不以最大x、最强暗点或历史最大值替代。
6. B0无可信历史写入、无观察确认，异常输入返回null fallback；这仅是隔离属性。原R03 16项故障原样复现，15通过、coherent_wrong_first_lock仍失败，不能用全拒绝宣称首次锁定安全通过。
7. 生产A准确率、覆盖和大误差未变；新候选可达性提升但尚无最终检测准确率。完整1565帧和76选帧分母分开，CPU如上；验证组本轮BLOCKED。
8. **不具备生产替换条件，保留现有生产文件。** 已证实的算法障碍是弱短片段在候选前被丢弃、候选池过大和S1耗时超预算。步进、参考、归属、终止、首次锁定与验证组准入仍未完成；研究基线与历史发布件的版本边界也必须在未来部署时明确，不能混用。

## 交付导航

- `acceptance_matrix.csv`：逐门PASS/FAIL/BLOCKED/NOT_VERIFIED。
- `experiments/`：逐帧、候选、窗口、片段、参考状态、终止未决、故障与性能；`traces/B0_frames.jsonl.gz`为1565帧完整原生细节，80选帧JSON另存真实脊线polyline。
- `pixel_audit/`：失败定位的原生数组；`stateless_budget_x8/`：容量单因素干预。
- `galleries/index.html`、`galleries/images/`：全部80开发选帧真实图像；`R05F_S1_Results.mp4`：对应视频，播放速度不是检测速度。
- `source_dependency_map.md`、`design_decisions.md`、`build_and_reproduce.md`、`code_diff.patch`、`final_integrity.json`：可复核实现与版本身份。
'''
 (OUT/'development_report.md').write_text(report,encoding='utf8')
 design='''# R05F 设计决策

1. 只在隔离research目录新增C++ DLL。原生产基线只增加生成目录中的计时克隆，不覆盖生产头文件/ABI/发布件。
2. 当前暗线在小窗口内独立取多尺度暗谷；参考失败无阻断权。pixel response、局部segment、endpoint candidate及observed四种语义分开。
3. S1用静态小窗口覆盖形成B0对照，不能冒充S2局部步进。几何去重同时保留每个别名、原窗口和片段来源；无全局强度top-K。
4. 当前参数来自共享几何尺度和现有响应约定，未用标签搜索/拟合。人工图只在运行结束后对比和定位失败。诊断发现短分量过滤后，没有针对开发组H78降低阈值；保留失败版本。
5. 原始预算截断、重复访问并集、窗口边界候选均显式导出；未完成搜索不等于末端停止。S1无需导航可信历史，也不把全部fallback当成安全性成绩。
6. x8容量是事先定义的一个离线单因素干预，不是扫描后选参；恢复不了6个遗漏，说明当前优先问题不是扩大候选容量。
7. 步进+同帧缺口探索、候选驱动的两侧材料配准、独立归属与终止仍是下一阶段架构，未在S1失败后混入版本改善分数。原R03首次错锁失败没有被重命名或换seed。
8. 参考方案今后需在相同候选/窗口列表上比较无参考/单侧/双侧/固定/合格历史；UNKNOWN不得删除当前证据。此次S3未启用，不虚构此比较结论。
'''
 (OUT/'design_decisions.md').write_text(design,encoding='utf8')
 (OUT/'next_steps.md').write_text('''# 下一步：保持基线身份明确，仍在S1

R01/R02已说明config/project.json指定的1c742…是历史发布件，55a0…是历轮研究基线。当前源码完整复现55a0，不宣称复现1c742。保留两个文件和原始结果，不能用覆盖发布件“修复”等价检查；未来部署另需完整准入，不以本轮研究基线名义自动发布。

先设计与强片段分开的“未确认弱短片段”表示，保留2/3列脊线的响应、尺度、来源、方向不确定性和边界信息；在不参考标签的位置条件下，用共享的局部结构一致性减少随机纹理，而非简单降低长度门槛或增加全图top-K。对细线、模糊、断漆、纹理噪声和弱端点的正/负构造统一检查，禁止为开发组H78设分支。

随后冻结一次新S1规则，重新运行四开发组1565帧和同80帧离线比较，检查四哨兵、全部6个遗漏、候选增长、容量前后损失、路径带覆盖及native时间。不能只展示恢复开发组H78而忽略GROUP_A/CT3。

S1通过后才进入S2：不可信exploration frontier与trusted frontier分开，逐窗/多假设、10+px缺口粗细搜索、预算耗尽search_incomplete，完成完整序列及原R03错锁和正向恢复检查。之后依次实现S3同候选参考消融、S4归属与终止、S5完整消融。代码/参数/评价脚本全部锁定后，才能一次性读验证组C/三点弯验证；排除组X继续排除，标签永不训练。
''',encoding='utf8')
 commands='''# 构建与复现

工作目录：`.`。Python3 / OpenCV native4.4；MSVC v142 x64、VS17生成器，/O2 /fp:precise /utf-8、4 native threads。不存在Git commit，身份见hash清单。输入F盘只读。

```powershell
$env:PYTHONPYCACHEPREFIX='./output/pycache'
& 'D:/CMake/bin/cmake.exe' -S research/uctt_r05f -B output/build/uctt_r05f -G 'Visual Studio 17 2022' -A x64 -T v142
& 'D:/CMake/bin/cmake.exe' --build output/build/uctt_r05f --config Release -- /m:1 /nodeReuse:false
```

封存目录不可覆盖。新全程复现前将 `common.py` 中 `OUT` 改为新的 `output/runs/<unique_r05f_id>`，GEN/BUILD也建议设置新output/build子目录，并同步CMake生成源/产物目录；新目录必须为空。prepare.py主动拒绝覆盖旧OUT。算法参数仍使用已封存current.hpp，不从标注选参。再依次执行：

```powershell
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/prepare.py
# prepare生成A0插桩源后执行上面的configure/build
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/baseline.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/contracts.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/replay.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/compare.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/diagnose_budget.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/diagnose_compare.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/pixel_audit.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/benchmark_release.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/release_details.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/audit_media.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/media.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/video_qa.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/tables.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/source_map.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/report.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/postprocess_gallery.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/seal.py
```

原图回放器不接受GT输入；只读策略在读取每张图前验证。单帧失败诊断由pixel_audit.py复现实际访问窗口的native数组，明确是stateless/offline，不替代全前缀评估。独立计时期间不得同时运行其他实验/渲染。全部CSV可直接重算分母；压缩轨迹按JSONL流式读取，不能一次性解压到内存。

S0 A_FROZEN使用55a0…构建DLL；发布DLL1c742…单独完整验证，文件字节不同但行为对照另有证据。R05F研究DLL的新接口不宣称与生产ABI可直接替换。R03Original退出码2是原有错锁失败复现，不能篡改为0。
'''
 (OUT/'build_and_reproduce.md').write_text(commands,encoding='utf8')
 snapshot=OUT/'source_snapshot';snapshot.mkdir(exist_ok=True);patch=[]
 for p in sorted((ROOT/'research/uctt_r05f').glob('*.*')):
  if p.suffix not in ['.py','.cpp','.hpp','.txt']:continue
  shutil.copy2(p,snapshot/p.name);patch.extend(difflib.unified_diff([],p.read_text(encoding='utf8').splitlines(True),fromfile='/dev/null',tofile=str(p.relative_to(ROOT)).replace('\\','/')))
 (OUT/'code_diff.patch').write_text(''.join(patch),encoding='utf8')
 scope=f'''# 基线身份与历史发布边界

本轮S0的A0为 `output/build/src/cpp/a/Release/CrackV4.dll`，SHA256 55a0e7a79162da79e691ede9ff58229e59a56fdd1e0b1e3f609dc51128860402；这是R02 environment.md明确列出的候选基线，R05D/R05E继续使用。当前源码克隆与其1565帧完整非计时结果完全一致。

`output/releases/A_Win64_OpenCV440/bin/CrackV4.dll` SHA256 1c74283c53eb99479190df47daea2c4d061f7ba90bb81acd7a847b9aa3b8e21f，是R01 inventory.md明确保留的2026-11-06历史发布件。R01 dependency_audit.md:25明确说它与当前源码不是同一构建；R02 ab_regression_report.md:3明确历史发布DLL未用于该A/B。config/project.json仍指向此发布包，意味着发布包与研究候选不能混称，而非本轮应把它们的不同当成克隆失败。

本轮附加全序列量化：formal完全相同{release_fields['formal_exact']}/1565；403帧不同，其中confirmed_tip不同104帧，tip字段不同277帧，完整长度确认不同13帧。geometry全帧有三个诊断字段不同。完整摘要0/1565一致。`release_equivalence.json`中的FAIL只指对“两个文件版本相同”的附加假设检验，不是S0指定55a0源码克隆的失败，也不是R05F引入的回归。

初始交流中曾将追加差异解读为整体S0失败；查回上述历史版本说明后已纠正。保留原始数值，不隐藏差异，不将版本边界变成虚构的本轮bug。S0范围和最终准入判定以本文件和acceptance_matrix.csv为准。
'''
 (OUT/'baseline_scope.md').write_text(scope,encoding='utf8')
 print('REPORT COMPLETE; S0 scoped clone PASS / historical release distinct / S1 FAIL / S2-S6 BLOCKED',flush=True)
if __name__=='__main__':main()
