# ROI几何单因素：最终交付报告

结论：B、C均为GEOMETRY_HARMFUL / NO_GO。工程完成，算法不通过，不替换生产。默认C事前冻结，未事后按组选择B。

| item | result |
| --- | --- |
| ENGINEERING_COMPLETE | PASS |
| INPUT_COVERAGE | PASS |
| PROTOCOL_FROZEN | PASS |
| GT_LEAKAGE_CHECK | PASS |
| BASELINE_PARITY | PASS |
| ALGORITHM_ACCEPTED | FAIL |
| PRODUCTION_APPROVED | FAIL |

实查GROUP_A551开发、验证组C562/三点弯520曝光回归，共1633帧×3模式=4899份真实推理结果。排除组0；人工标签仅封存后独立进程比较，不训练或调参。原A完整原生结果/图1633帧一致；30帧原BMP/P重算差分最大误差0，30次检测重复一致。8165张逐帧PNG、1633套数值引用、1637个HTML页面、三段视频共1633帧通过核验和完整解码。

[原因与反例](ROI_CAUSAL_FINDINGS.md) · [完整图册](../galleries/index.html) · [原始自动报告](../REPORT.md) · [完整性](../run_integrity.json) · [冻结源码](../source_hashes.json) · [可执行复现](../README.md)

## 实际输出：可见分母固定

| group | mode | visible | outputs | no_public | hit3 | hit5 | hit10 | hit20 | joint | over100 | over500 | any_candidate_path_good | GT_EXCLUDED |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | A_ORIGINAL_ROI | 19 | 0 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| group_a | B_COMPACT_FIXED_BAND | 19 | 1 | 18 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 2 | 0 |
| group_a | C_DYNAMIC_CORRIDOR | 19 | 0 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| group_c | A_ORIGINAL_ROI | 20 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |
| group_c | B_COMPACT_FIXED_BAND | 20 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 18 | 0 |
| group_c | C_DYNAMIC_CORRIDOR | 20 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |
| three_point_bend | A_ORIGINAL_ROI | 15 | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| three_point_bend | B_COMPACT_FIXED_BAND | 15 | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| three_point_bend | C_DYNAMIC_CORRIDOR | 15 | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

no_public包含不确定/歧义/ROI限制，仍计入可见分母。joint同时要求尖端≤10px及原观测路径覆盖/精度均≥0.8。GT_EXCLUDED此处仅指人工尖端点不在mask，不等价于完整路径没有被裁剪。验证组C266的B/C均产生(2448,2345)暂定尖端，该帧无标签，不能计正确或错误，也不能从54张可见表的零严重错误推断真实FPR=0。真实FPR=N/A。

## 路径与被隐藏的误差尾部

| group | mode | path_coverage10 | path_precision10 | candidate_over100 | candidate_over500 | last_observed_over100 | last_observed_over500 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | A_ORIGINAL_ROI | 0.36888960816197214 | 1.0 | 0 | 0 | 15 | 0 |
| group_a | B_COMPACT_FIXED_BAND | 0.2820993989016009 | 0.9933363451547322 | 0 | 0 | 14 | 0 |
| group_a | C_DYNAMIC_CORRIDOR | 0.2707905108298749 | 1.0 | 0 | 0 | 15 | 0 |
| group_c | A_ORIGINAL_ROI | 0.4784358578469732 | 0.6455230882357319 | 0 | 0 | 10 | 6 |
| group_c | B_COMPACT_FIXED_BAND | 0.6791747562507855 | 0.9664383667834647 | 0 | 0 | 5 | 0 |
| group_c | C_DYNAMIC_CORRIDOR | 0.572444715627157 | 0.8408946785348584 | 0 | 0 | 8 | 2 |
| three_point_bend | A_ORIGINAL_ROI | 0.20131073579376213 | 0.34571973128247124 | 0 | 0 | 10 | 0 |
| three_point_bend | B_COMPACT_FIXED_BAND | 0.2205105424020654 | 0.3911562804914766 | 0 | 0 | 10 | 0 |
| three_point_bend | C_DYNAMIC_CORRIDOR | 0.20423305856902604 | 0.34328725762245377 | 0 | 0 | 10 | 0 |

候选端点与最后观测点单独列出；无端点不填零误差。最后观测点不是已确认尖端，尾部仅用于路径诊断。

## 几何与成本

| group | mode | area_remaining_pct | nodes_remaining_pct | edges_total | unvisited_budget | containment_deleted | ROI_LIMITED | path_P50_ms | path_P95_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | A_ORIGINAL_ROI | 100.0 | 100.0 | 2074907 | 1020376 | 2050 | 0 | 701.02 | 768.22 |
| group_a | B_COMPACT_FIXED_BAND | 30.45 | 76.26 | 2082990 | 746266 | 44893 | 1 | 288.98 | 322.66 |
| group_a | C_DYNAMIC_CORRIDOR | 51.6 | 86.92 | 2194953 | 956350 | 5731 | 1 | 491.66 | 550.26 |
| group_c | A_ORIGINAL_ROI | 100.0 | 100.0 | 6171737 | 2568057 | 7386 | 0 | 1767.49 | 1838.62 |
| group_c | B_COMPACT_FIXED_BAND | 30.62 | 63.65 | 4530447 | 1393328 | 90118 | 1 | 580.68 | 616.8 |
| group_c | C_DYNAMIC_CORRIDOR | 29.4 | 60.64 | 3903125 | 1394734 | 29406 | 50 | 558.47 | 616.6 |
| three_point_bend | A_ORIGINAL_ROI | 100.0 | 100.0 | 5967386 | 3197103 | 2884 | 0 | 3624.9 | 3811.51 |
| three_point_bend | B_COMPACT_FIXED_BAND | 30.48 | 92.27 | 11838323 | 3755488 | 19655 | 0 | 1967.63 | 2094.12 |
| three_point_bend | C_DYNAMIC_CORRIDOR | 63.05 | 98.44 | 9397642 | 4015740 | 9386 | 4 | 3217.77 | 3395.39 |

面积是相对A的实际mask像素均值，非包围矩形面积。B保留原完整x范围，只缩y。C真实多分支非矩形mask完整存盘。缩区会释放原每列候选容量，因此节点和邻接边不必按面积同比减少。unvisited_budget是达到6条保留路线后尚未访问的排序尾部，不能声称其中每条都能通过去重。

| group | frames | shared_evidence_cache_load_verify_ms_P50 | shared_evidence_cache_load_verify_ms_P95 | shared_geometry_controller_ms_P50 | shared_geometry_controller_ms_P95 | lineage_audit_ms_P50 | lineage_audit_ms_P95 | render_ms_P50 | render_ms_P95 | max_worker_peak_MiB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | 551 | 89.62 | 100.25 | 269.79 | 314.23 | 1029.32 | 1121.82 | 3013.85 | 3325.63 | 126.43 |
| group_c | 562 | 115.62 | 129.63 | 228.7 | 258.79 | 1879.22 | 1964.73 | 8502.71 | 11016.51 | 214.76 |
| three_point_bend | 520 | 185.89 | 200.43 | 1373.41 | 1526.35 | 6353.13 | 6646.57 | 10388.53 | 11089.21 | 423.99 |

A/B/C计时仅缓存证据上的路径引擎，执行顺序固定且有并发/热缓存影响；未宣称全流程等比例加速。共享geometry项还含边界检查与封装，不是纯C内核时间。RAM为单工作进程截至该帧的峰值，不是整机峰值。绘图单列，未混入推理性能。旧特征缓存经SHA核验复用，非本轮新提取特征成绩。

## 逐帧成对得失

| group | mode | visible | hit10_gained | hit10_lost | joint_gained | joint_lost | new_over100 | new_over500 | new_GT_EXCLUDED | pool_good_lost | pool_good_gained |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | B_COMPACT_FIXED_BAND | 19 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 1 |
| group_a | C_DYNAMIC_CORRIDOR | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| group_c | B_COMPACT_FIXED_BAND | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| group_c | C_DYNAMIC_CORRIDOR | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| three_point_bend | B_COMPACT_FIXED_BAND | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| three_point_bend | C_DYNAMIC_CORRIDOR | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |

完整状态分布和首败阶段见[离线开发汇总](../evaluation_complete_group_a.json)与[回归汇总](../evaluation_complete_exposed.json)。GROUP_A未知1、三点弯未知5，单独保留；未标注帧不作阴性。两验证组已曝光，不是新盲测；GROUP_A仅19可见样本，不作显著性结论。

## 使用与复现

从项目根目录按[源码README](../../../../research/grayref_roi_geometry_ablation/README.md)执行run_group_a.ps1，再执行run_regression.ps1，使用全新RunId；后者完成回归、图像、核验及视频。原图/点只读，数值缓存引用需保留上一轮简化运行目录。

视频：[验证组C](../videos/group_c.mp4) · [三点弯](../videos/three_point_bend.mp4) · [GROUP_A](../videos/group_a.mp4)。6FPS是播放速率，不是算法速度。
