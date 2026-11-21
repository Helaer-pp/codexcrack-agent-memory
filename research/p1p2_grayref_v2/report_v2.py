from v2common import *
import collections,platform
def table(records,columns):
 return '| '+' | '.join(label for key,label in columns)+' |\n|'+ '|'.join('---' for _ in columns)+'|\n'+''.join('| '+' | '.join(str(r.get(key,'')) if r.get(key,'') not in [None,''] else 'N/A' for key,label in columns)+' |\n' for r in records)
def doc(name,text):(OUT/name).write_text(text,encoding='utf8')
def main():
 port_note=''
 if (OUT/'native_port_attempt1/native_parity_complete.json').exists():
  port_note='''
首次原生全量回放发现三点弯512帧的csm/valley/newdark/flank_low四层有1个float32 ULP（1.52587890625e-5）的差异，超过运行前数组容差1e-5；所有离散路径、状态和端点仍相同。失败源码、DLL、全部原生结果、逐层表和日志保存在native_port_attempt1/，未删除或覆盖。

7×7原始像素局部复算把差异定位于对称高斯滤波加法顺序：原移植从近邻到远邻累加，冻结SciPy按远邻到近邻；仅改顺序就使该像素由202.1948699951172恢复到202.19488525390625。详见native_port_rounding_isolation.json四个控制。新C++全局按同一顺序实现，并固定sigma=.7由SciPy公式产生的binary64系数；核系数由参数确定，无图像拟合。独立合成算术核验见numeric_kernel_audit.json。此修正只实现冻结Python数值规范，不改Python算法、默认模式、任何检测阈值或容差，不是根据验证准确率修订模型。全2783输入、五模式重新回放，最终状态以本报告表格为准。第二次构建/回放日志为logs/build_port02.log和logs/native_parity_port02.log。
'''
 acceptance=read(OUT/'development_acceptance.json');parity=read(OUT/'native_parity_complete.json');summary=rows(OUT/'group_summary.csv');syn=read(OUT/'gate1_complete.json');native=read(OUT/'native_port_identity.json');lock=read(OUT/'config_v2_locked.json');integrity=read(OUT/'final_integrity.json') if (OUT/'final_integrity.json').exists() else {};engineer=parity['passed'] and (OUT/'media_complete.json').exists();acc=acceptance['accepted'];columns=[('group','组/用途'),('mode','模式'),('visible','可见分母'),('output_coverage','输出'),('hit3','≤3'),('hit5','≤5'),('hit10','≤10'),('over100','>100'),('over500','>500'),('visible_UNCERTAIN','不确定'),('visible_NO_TIP','无端点'),('joint_tip_path_success','端点+路径联合')];totals=[r for r in summary if r['group'] in ['DEVELOPMENT','EXPOSED_VALIDATION']];combined=[r for r in summary if r['mode']=='V2_COMBINED'];state='YES' if engineer else 'NO';report=f'''# P1/P2–GrayRef V2 r01 实际开发与验证报告

ENGINEERING_COMPLETE: {state}  
ALGORITHM_ACCURACY_ACCEPTED: {'YES' if acc else 'NO'}  
PY_CPP_PARITY_PASSED: {'YES' if parity['passed'] else 'NO'}  
PRODUCTION_RELEASE_APPROVED: NO

## 结论

完整交付了真实CPU Python与独立C++17/OpenCV实现、四核心模式及两个额外控制、开发1565帧和已曝光验证1082帧、123组固定扰动、ABCD与9个预定义代表输入。**算法未达到预注册跨组接受条件**：默认COMBINED开发10px命中4/76，旧V1为12/76；三个非CT3开发组仍全为0。独立TERMINAL为5/76，不能据此替换默认或宣布成功。所有规则在开发完整评分前锁定；没有看验证结果反调，没有额外r02设计迭代。

COMBINED公开输出>100px由31降至26，但公开输出覆盖由50降至37；其原始候选>100px为57/76、>500px为37/76，公开>500px仍19/76（V1为18）。**拒绝错误候选不等于找到正确裂纹，严重尾部与可用召回仍未解决。** 合成“只有已有划痕”的一个阴性构造在5个V2模式中有{syn['synthetic_negative_false_outputs']}个暂定输出，说明现有起源身份分数不能独立区分长划痕与裂纹。这是合成行为，不是实际FPR估计。

## 全量实测汇总

{table(totals,columns)}

默认COMBINED逐组：

{table(combined,columns)}

所有VISIBLE包含NO_TIP/UNCERTAIN/ROI_LIMITED，分母不变。3/5/10比例、输出覆盖、仅有有效输出的误差n/P50/P95/max、各状态全帧数和5/10px路径覆盖/精度均在[group_summary.csv](group_summary.csv)。UNCERTAIN标签4开发/5验证单独统计。CT3六帧GT在原ROI外保留原分母，未扩大ROI。真实NO_VISIBLE_CRACK库不可用，FPR=N/A；NEW_BLIND_HOLDOUT=NOT_AVAILABLE。

输入来源限制：CT3使用带明确帧文件名与编号的历史坐标CSV，已核对旧V1完整回放映射；独立原始跟踪TXT仍不可用，不能声称已从原始TXT独立恢复。其余组从现有原始点记录核对。baseline_identity.json保留来源与SHA；原始点语义/物理配准真值仍UNRESOLVED。

路径指标仅用实际观测连续段，预测跨缺失不连线；无路径为0。即使状态UNCERTAIN，已有观测候选路径仍可离线比较，但不能称为物理主裂纹认证。独立联合指标要求有效端点≤10px且路径覆盖/精度10px均≥0.8。原图标签只由[独立评估器](python_v2/evaluate_v2.py)在相应整组推理完成后读取；GT字段只在offline_evaluation表中，不在推理接口。

## 机制与严格消融

M1在P点起源区域多列提取当前暗谷候选，确定性NMS后最多24个短程测试、3个路径身份假设；短程连续性、曲率和向缺口回溯连接共同评分，不按最远x取胜。M2保持V1参考remap，检查上下材料窗纹理/NCC质量，可靠正新增增量只提供最多25%辅助加分，未知/同图/无纹理/不可靠差分不硬否决当前暗谷。

NUMERIC_CONTROL单列隔离确定性整数拟合/预测量化、全零初始化拒绝与不足8观测的输出安全合同。M1-only仍使用原joint必要条件与原末观测端点；M2-only不扩首列扫描或±7后续搜索范围。核心因果分析需在共同NUMERIC_CONTROL底座做2×2，另报告相对真正V1的总变化。TERMINAL只对COMBINED同一所选路径增加停止候选竞争，未改上游候选/排序；全部合成与全量parity证据可审计。详见[V2_ABLATION_REPORT.md](V2_ABLATION_REPORT.md)及[实现审计](V2_IMPLEMENTATION_AUDIT.md)。

## 失败发现

M1-only为11/76且>100px增加到38；M2-only为8/76且>100px为40；组合仅4/76。多候选和参考解耦均没有建立可靠跨组身份。当前实现的纵向起源带去重不能识别不同起始x但后来重合的同一路径，保留了重复路径竞争；歧义拒绝可能损失原CT3命中。短程连续性也会奖励错误长暗线。该解释有[候选淘汰/GT事后审计](origin_failure_audit.csv)与[计算路径重合审计](hypothesis_overlap_audit.csv)，不能当独立物理真值。

参考局部质量检查是可审计纹理一致性代理，未提供完整材料物理变形真值/无裂纹材料mask。已有裂纹和划痕都可能表现为NO_INCREMENT；不将其等价“无裂纹”。原始P点语义仍承接前轮UNRESOLVED，不据替代NCC认定原点错误。完整[分层失败报告](V2_FAILURE_ANALYSIS.md)保留原始候选与公开输出两套严重错误计数。

## 验证组C同BMP和扰动

A/B/C/D均在固定源码/参数下真实运行，原V1 A/D六模式轨迹先与未修改CLI及旧结果逐列核对。第237帧不在20张VISIBLE中，其(2423,2344)只为历史近似回归锚点，未进入推理。

D的M2-only选择(2255,2351)，端点(2424,2344)；组合版原始候选同时包含(2255,2282)和(2255,2351)，前者被NMS合并、后者进入路径假设，但最终所选起源(2319,2340)与其他路径竞争，输出UNCERTAIN。M1-only也UNCERTAIN。**单帧修复不构成全组改进；不把拒绝错误D认作找到正确D。** [D起源明细](D_two_origins_audit.csv)和[ABCD及哨兵图册](galleries/same_bmp_ABCD_v1_v2.html)展示全部失败。

固定123组扰动覆盖4点各自x/y±2/±5、参考/当前/全点x/y±1/±3以及A→D t=0:.1:1；另4个ABCD和9个代表输入，总136次同样的六模式展示。每次同时保存原V1六档；V2共5个模式。跳变、状态变化、原始候选跳变分开记录于[perturbation_robustness.csv](perturbation_robustness.csv)，没有搜索验证组C最佳点值或对噪声分布做假设。

## 原生实现与数值一致性

独立GrayRefV2 API真实执行，不调用Python结果或旧DLL。MSVC v142/C++17/OpenCV4.4，/O2 /fp:strict，1原生线程；Python cv2环境版本见复现记录。C++证据预处理在新源码中保留V1算法，未链接/修改旧V1二进制。DLL SHA `{native['dll_sha']}`。

共2647全帧+136代表/扰动输入、每输入5模式，{parity['mode_cases']}模式比较；另6个原生合成结构/异常控制。逐层核对P/ROI、8数组、参考质量/状态、候选集/排名、全部路径逐列选择、停止候选、输出状态和坐标。结果与精度分开：[V2_NUMERIC_PARITY_REPORT.md](V2_NUMERIC_PARITY_REPORT.md)。整数离散决策必须完全相同；标量容差1e-6、数组容差1e-5并同时报告完全相同分母，不用最终端点一致冒充全链路一致。

## 性能与交付

[runtime_performance.csv](runtime_performance.csv)列六组P50/P95/P99/max；Python V2和native_ms均为同一输入全部5个V2模式合计，不能当作单模式耗时。Python V2不含解码/导出/启动，V1适配为原六模式且包括CSV导出；api_wall含创建/JSON及数组复制，不含文件解码。RSS为整个worker进程峰值，native进程仍含Python桥，不能称纯DLL峰值。测试并行负载与目标i7部署不同，不作实时部署保证。视频8fps只是播放速度。

已生成六组2647张每帧8面板局部对比、标注帧局部放大、6段完整视频和13个ABCD/代表卡片。查看[六组导航（验证组置顶）](galleries/index.html)。另提供[全帧参考证据查看器](galleries/reference_evidence.html)：逐窗参考质量/状态/原因、上下独立材料审计、来源P点变换，以及133张当前灰度/对齐参考/暗谷/带符号新增/质量分层图。完整原图不重复复制，所有结果能回链原图SHA和原始P记录。

代码、构建、运行命令见[reproduce.md](reproduce.md)，交付映射见[DELIVERABLE_INDEX.md](DELIVERABLE_INDEX.md)，完整性见[final_integrity.json](final_integrity.json)。V1、生产A、旧结果、外部原图与人工标签不修改；未发布生产版本。
''';doc('V2_DEVELOPMENT_REPORT.md',report)
 ablation='''# 严格消融结果与解释

所有模式使用同样原图、逐帧点、V1 ROI/预处理。原V1是不可变原生Python，六档继续保留。下表核心M1/M2需相对NUMERIC_CONTROL共同底座解释；该底座相对原V1的确定性数值规则和输出安全过滤已经单独列出，不能隐藏进M1增益。

'''+table(totals,columns)+'''

NUMERIC_CONTROL开发命中仍12，公开>100从31降至24，但原候选>100仍31：主要是短路径状态过滤，不是新增正确路径。M1-only短程多候选没有获得两个非CT3组命中，且错误尾部扩大。M2-only使已有/不可靠参考下当前暗谷可推进，但长纹理身份无法仅靠正增量辅助区分。组合歧义拒绝进一步损失命中；没有使用“各组最佳模式”作为默认。

TERMINAL是额外模块，与COMBINED的seeds/paths完整相同，区别仅在所选路径上的停止候选排序与最终截断。开发命中5对4只是这项额外规则的结果，不计入M1/M2因果收益。独立材料NCC仅输出审计，不替换remap；没有隐含M3或时间增强。

精确开关和阈值见config_v2_locked.json，规则锁定时间与源码SHA固定。没有开发r02或验证后改参。所有端点/状态/原候选严重尾部见group_summary.csv，不只展示成功者。
''';doc('V2_ABLATION_REPORT.md',ablation)
 stats=rows(OUT/'numeric_parity_summary.csv');doc('V2_NUMERIC_PARITY_REPORT.md',f'''# Python / C++ 数值与结构一致性

PY_CPP_PARITY_PASSED: {'YES' if parity['passed'] else 'NO'}

{parity['checks']}项层级检查，{parity['failed_layers']}项超容差或结构差异。每层分母包括2647全帧和136额外输入，共2783输入；每输入全部5个V2模式。完整逐输入记录在parity/，首个差异在numeric_first_divergences.csv，原生完整结果在native/。

{table(stats,[('layer','层'),('n','分母'),('exact','完全相同'),('within_tolerance','容差内相同'),('max_abs','数组最大差')])}

整数观测的最近12点以整数和计算斜率，预测按1/1024px量化；有符号四舍五入和floor/ceil整数边界共用契约。无SVD微小浮动进入搜索边界。排序微分数1e-6、稳定x/y/ID tie-breaking；不是对验证帧添加epsilon。Python20004个数值边界检查及原生NumericSelfTest实际执行。连续数值容差分别1e-6和数组1e-5；离散选择、状态、点、列表长度/顺序必须严格相同。

{port_note}

冻结V1没有反向修复，其旧current移植差异事实仍保留。新NUMERIC_CONTROL独立揭示新契约影响；本轮不能凭V2 parity通过宣称旧V1全域parity通过。构建日志logs/build.log，DLL与源码身份native_port_identity.json。新库不包装Python结果，不调用旧V1或生产DLL。
''')
 failures=rows(OUT/'offline_evaluation_dev.csv')+rows(OUT/'offline_evaluation_validation.csv');counts=collections.Counter((r['group'],r['mode'],r['stage']) for r in failures if r['visibility']=='VISIBLE');countrows=[dict(group=g,mode=m,stage=s,n=n) for (g,m,s),n in sorted(counts.items())];save(OUT/'failure_stage_counts.csv',countrows)
 doc('V2_FAILURE_ANALYSIS.md','''# 六组失败分析

阶段标签是事后证据分类，不是互斥物理因果真值。先记录ROI排除、输出不确定/缺失，再记录首观测距人工路径>10、过延伸或未解决。没有用这些标签反调规则。

'''+table([r for r in countrows if r['mode']=='V2_COMBINED'],[('group','组'),('stage','阶段'),('n','可见帧数')])+'''

完整6模式分层见failure_stage_counts.csv，逐帧原始数值见offline_evaluation_dev/validation.csv。origin_failure_audit.csv区分“人工路径在起源区外”“路径附近当前证据不足”“候选被NMS/预算/短程连接过滤”“进入假设仍未选中”。hypothesis_overlap_audit.csv记录不同初始x/y假设的实际计算轨迹重合，避免把同一条计算路径的多个起点当独立物理分叉。

已确认局限：固定valley/材料阈值与原ROI限制保留；二维候选仍局限于P点附近，不能保证找到正确缺口连接；原joint在M1-only仍可否决真实候选；M2不把未知参考当负证据，但也没有独立识别旧划痕；短程支持分数会奖励错误长暗线；简单纵向去重可能制造重复路径歧义；TERMINAL只比较当前所选路径，无法挽救错主路径。单向+x和±.2方向限制未覆盖所有真实分叉/大弯折。所有输出均暂定，不是FORMAL_OBSERVED。

下一版应先在开发数据/合成物理控制中验证起源与重合路径身份的独立证据，再讨论更大候选预算或更宽ROI；这只是建议，本轮未实施新版本。验证组C和三点弯结果只作已曝光回归，不能据此挑阈值、挑模式或宣称新盲测显著性。
''')
 doc('V2_IMPLEMENTATION_AUDIT.md','''# 实现与模块隔离审计

- python_v2/algorithm.py：evidence保持V1 ROI、平滑、flank和双点remap；quality计算上下独立纹理质量；Tracker.seeds实现二维当前谷候选/NMS/短程验证；Tracker.walk使用同范围逐列路径；run_mode明确M1/M2开关；terminal_candidates只被独立TERMINAL调用。
- python_v2/frozen_adapter.py：编译精确不可变V1文件；Unicode安全读图接口；6份trace/summary生成后跳过绘图。G0同图完整未修改CLI对照及全2647帧六轨迹旧回放一致。原始算法源码未改。
- cpp_v2/evidence.hpp：V2目录内保留V1预处理数学，删除旧追踪方法/调用；不链接旧DLL。v2_detector.hpp独立实现质量、起源、数值规则、逐列路径和停止，runtime.cpp导出GrayRefV2*。无Python回调或组名/帧名/GT参数。
- V2_NUMERIC_CONTROL独立记录新整数拟合与输出安全合同；core三种V2共享该底座，额外控制不可混淆原V1。NUMERIC_CONTROL与V1的所有差异保留。
- 不足8观测/歧义UNCERTAIN；无候选/无观测NO_TIP；贴右界ROI_LIMITED；非法点INPUT_ERROR；其他满足支持要求才PROVISIONAL_OBSERVED。candidate_tip是审计候选，不计有效命中。原V1状态仅反映历史暂定输出。
- M1和M2仅改变锁定机制，TERMINAL没有改变COMBINED候选/主路径选择。新配准M3与TEMPORAL_ON均NOT_IMPLEMENTED，不隐藏在核心消融。
- 原生预测精度1/1024px、分数1e-6是全局数值合同，tie由小y/小x/稳定ID确定。合成弱2/3列保留为线索但拒绝单独认证；合成旧划痕阴性仍产生误输出，已明确失败。
- reference_quality中的tile code2表示纹理可靠性；只有结合逐候选delta才区分EXISTING_DARK_OR_NO_INCREMENT与NEW_DARK_SUPPORTED。code0/1是未知/不可靠，不能用0差分伪装可靠反证。独立局部NCC另记INDEPENDENT_NCC_NOT_APPLIED，不进入推理。

本轮只有r01，未做一次可选开发设计修复；工程可运行不等于算法成功。所有新增源码位置及原始哈希见source_manifest.json/配置锁。
''')
 write(OUT/'report_complete.json',dict(utc=utc(),engineering_complete=engineer,algorithm_accuracy_accepted=acc,py_cpp_parity_passed=parity['passed'],production_release_approved=False));print('REPORT COMPLETE',state,acc,flush=True)
if __name__=='__main__':main()
