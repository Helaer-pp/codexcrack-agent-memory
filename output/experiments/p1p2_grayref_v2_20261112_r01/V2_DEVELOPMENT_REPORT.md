# P1/P2–GrayRef V2 r01 实际开发与验证报告

ENGINEERING_COMPLETE: YES  
ALGORITHM_ACCURACY_ACCEPTED: NO  
PY_CPP_PARITY_PASSED: YES  
PRODUCTION_RELEASE_APPROVED: NO

## 结论

完整交付了真实CPU Python与独立C++17/OpenCV实现、四核心模式及两个额外控制、开发1565帧和已曝光验证1082帧、123组固定扰动、ABCD与9个预定义代表输入。**算法未达到预注册跨组接受条件**：默认COMBINED开发10px命中4/76，旧V1为12/76；三个非CT3开发组仍全为0。独立TERMINAL为5/76，不能据此替换默认或宣布成功。所有规则在开发完整评分前锁定；没有看验证结果反调，没有额外r02设计迭代。

COMBINED公开输出>100px由31降至26，但公开输出覆盖由50降至37；其原始候选>100px为57/76、>500px为37/76，公开>500px仍19/76（V1为18）。**拒绝错误候选不等于找到正确裂纹，严重尾部与可用召回仍未解决。** 合成“只有已有划痕”的一个阴性构造在5个V2模式中有3个暂定输出，说明现有起源身份分数不能独立区分长划痕与裂纹。这是合成行为，不是实际FPR估计。

## 全量实测汇总

| 组/用途 | 模式 | 可见分母 | 输出 | ≤3 | ≤5 | ≤10 | >100 | >500 | 不确定 | 无端点 | 端点+路径联合 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DEVELOPMENT | V1_LOCKED | 76 | 50 | 6 | 8 | 12 | 31 | 18 | 0 | 26 | 11 |
| DEVELOPMENT | V2_NUMERIC_CONTROL | 76 | 43 | 6 | 8 | 12 | 24 | 17 | 7 | 26 | 11 |
| DEVELOPMENT | V2_ORIGIN_ONLY | 76 | 55 | 6 | 8 | 11 | 38 | 19 | 21 | 0 | 10 |
| DEVELOPMENT | V2_REF_ONLY | 76 | 59 | 4 | 5 | 8 | 40 | 21 | 0 | 17 | 6 |
| DEVELOPMENT | V2_COMBINED | 76 | 37 | 2 | 2 | 4 | 26 | 19 | 39 | 0 | 4 |
| DEVELOPMENT | V2_TERMINAL | 76 | 37 | 2 | 3 | 5 | 26 | 19 | 39 | 0 | 5 |
| EXPOSED_VALIDATION | V1_LOCKED | 35 | 20 | 0 | 2 | 5 | 4 | 0 | 0 | 15 | 5 |
| EXPOSED_VALIDATION | V2_NUMERIC_CONTROL | 35 | 14 | 0 | 2 | 5 | 0 | 0 | 6 | 15 | 5 |
| EXPOSED_VALIDATION | V2_ORIGIN_ONLY | 35 | 11 | 6 | 6 | 9 | 0 | 0 | 24 | 0 | 1 |
| EXPOSED_VALIDATION | V2_REF_ONLY | 35 | 35 | 6 | 6 | 13 | 2 | 0 | 0 | 0 | 13 |
| EXPOSED_VALIDATION | V2_COMBINED | 35 | 6 | 2 | 2 | 4 | 0 | 0 | 29 | 0 | 3 |
| EXPOSED_VALIDATION | V2_TERMINAL | 35 | 6 | 4 | 4 | 5 | 0 | 0 | 29 | 0 | 4 |


默认COMBINED逐组：

| 组/用途 | 模式 | 可见分母 | 输出 | ≤3 | ≤5 | ≤10 | >100 | >500 | 不确定 | 无端点 | 端点+路径联合 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| group_a | V2_COMBINED | 19 | 6 | 0 | 0 | 0 | 6 | 0 | 13 | 0 | 0 |
| ct2 | V2_COMBINED | 20 | 20 | 0 | 0 | 0 | 20 | 19 | 0 | 0 | 0 |
| group_h | V2_COMBINED | 18 | 0 | 0 | 0 | 0 | 0 | 0 | 18 | 0 | 0 |
| ct3 | V2_COMBINED | 19 | 11 | 2 | 2 | 4 | 0 | 0 | 8 | 0 | 4 |
| DEVELOPMENT | V2_COMBINED | 76 | 37 | 2 | 2 | 4 | 26 | 19 | 39 | 0 | 4 |
| group_c | V2_COMBINED | 20 | 6 | 2 | 2 | 4 | 0 | 0 | 14 | 0 | 3 |
| three_point_bend | V2_COMBINED | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 15 | 0 | 0 |
| EXPOSED_VALIDATION | V2_COMBINED | 35 | 6 | 2 | 2 | 4 | 0 | 0 | 29 | 0 | 3 |


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

独立GrayRefV2 API真实执行，不调用Python结果或旧DLL。MSVC v142/C++17/OpenCV4.4，/O2 /fp:strict，1原生线程；Python cv2环境版本见复现记录。C++证据预处理在新源码中保留V1算法，未链接/修改旧V1二进制。DLL SHA `6589f10cf869f5f2be5ba8fc7737471324a044fabf073bc4441b19b62e799ab4`。

共2647全帧+136代表/扰动输入、每输入5模式，13915模式比较；另6个原生合成结构/异常控制。逐层核对P/ROI、8数组、参考质量/状态、候选集/排名、全部路径逐列选择、停止候选、输出状态和坐标。结果与精度分开：[V2_NUMERIC_PARITY_REPORT.md](V2_NUMERIC_PARITY_REPORT.md)。整数离散决策必须完全相同；标量容差1e-6、数组容差1e-5并同时报告完全相同分母，不用最终端点一致冒充全链路一致。

## 性能与交付

[runtime_performance.csv](runtime_performance.csv)列六组P50/P95/P99/max；Python V2和native_ms均为同一输入全部5个V2模式合计，不能当作单模式耗时。Python V2不含解码/导出/启动，V1适配为原六模式且包括CSV导出；api_wall含创建/JSON及数组复制，不含文件解码。RSS为整个worker进程峰值，native进程仍含Python桥，不能称纯DLL峰值。测试并行负载与目标i7部署不同，不作实时部署保证。视频8fps只是播放速度。

已生成六组2647张每帧8面板局部对比、标注帧局部放大、6段完整视频和13个ABCD/代表卡片。查看[六组导航（验证组置顶）](galleries/index.html)。另提供[全帧参考证据查看器](galleries/reference_evidence.html)：逐窗参考质量/状态/原因、上下独立材料审计、来源P点变换，以及133张当前灰度/对齐参考/暗谷/带符号新增/质量分层图。完整原图不重复复制，所有结果能回链原图SHA和原始P记录。

代码、构建、运行命令见[reproduce.md](reproduce.md)，交付映射见[DELIVERABLE_INDEX.md](DELIVERABLE_INDEX.md)，完整性见[final_integrity.json](final_integrity.json)。V1、生产A、旧结果、外部原图与人工标签不修改；未发布生产版本。
