# Python / C++ 数值与结构一致性

PY_CPP_PARITY_PASSED: YES

119669项层级检查，0项超容差或结构差异。每层分母包括2647全帧和136额外输入，共2783输入；每输入全部5个V2模式。完整逐输入记录在parity/，首个差异在numeric_first_divergences.csv，原生完整结果在native/。

| 层 | 分母 | 完全相同 | 容差内相同 | 数组最大差 |
|---|---|---|---|---|
| V2_COMBINED/outputs | 2783 | 2783 | 2783 | 0.0 |
| V2_COMBINED/paths | 2783 | 2783 | 2783 | 0.0 |
| V2_COMBINED/reference_status_counts | 2783 | 2783 | 2783 | 0.0 |
| V2_COMBINED/seeds | 2783 | 2783 | 2783 | 0.0 |
| V2_COMBINED/terminal_candidates | 2783 | 2783 | 2783 | 0.0 |
| V2_COMBINED/trace | 2783 | 2783 | 2783 | 0.0 |
| V2_NUMERIC_CONTROL/outputs | 2783 | 2783 | 2783 | 0.0 |
| V2_NUMERIC_CONTROL/paths | 2783 | 2783 | 2783 | 0.0 |
| V2_NUMERIC_CONTROL/reference_status_counts | 2783 | 2783 | 2783 | 0.0 |
| V2_NUMERIC_CONTROL/seeds | 2783 | 2783 | 2783 | 0.0 |
| V2_NUMERIC_CONTROL/terminal_candidates | 2783 | 2783 | 2783 | 0.0 |
| V2_NUMERIC_CONTROL/trace | 2783 | 2783 | 2783 | 0.0 |
| V2_ORIGIN_ONLY/outputs | 2783 | 2783 | 2783 | 0.0 |
| V2_ORIGIN_ONLY/paths | 2783 | 2783 | 2783 | 0.0 |
| V2_ORIGIN_ONLY/reference_status_counts | 2783 | 2783 | 2783 | 0.0 |
| V2_ORIGIN_ONLY/seeds | 2783 | 2783 | 2783 | 0.0 |
| V2_ORIGIN_ONLY/terminal_candidates | 2783 | 2783 | 2783 | 0.0 |
| V2_ORIGIN_ONLY/trace | 2783 | 2783 | 2783 | 0.0 |
| V2_REF_ONLY/outputs | 2783 | 2783 | 2783 | 0.0 |
| V2_REF_ONLY/paths | 2783 | 2783 | 2783 | 0.0 |
| V2_REF_ONLY/reference_status_counts | 2783 | 2783 | 2783 | 0.0 |
| V2_REF_ONLY/seeds | 2783 | 2783 | 2783 | 0.0 |
| V2_REF_ONLY/terminal_candidates | 2783 | 2783 | 2783 | 0.0 |
| V2_REF_ONLY/trace | 2783 | 2783 | 2783 | 0.0 |
| V2_TERMINAL/outputs | 2783 | 2783 | 2783 | 0.0 |
| V2_TERMINAL/paths | 2783 | 2783 | 2783 | 0.0 |
| V2_TERMINAL/reference_status_counts | 2783 | 2783 | 2783 | 0.0 |
| V2_TERMINAL/seeds | 2783 | 2783 | 2783 | 0.0 |
| V2_TERMINAL/terminal_candidates | 2783 | 2783 | 2783 | 0.0 |
| V2_TERMINAL/trace | 2783 | 2783 | 2783 | 0.0 |
| array_csm | 2783 | 2783 | 2783 | 0.0 |
| array_flank_low | 2783 | 2783 | 2783 | 0.0 |
| array_newdark | 2783 | 2783 | 2783 | 0.0 |
| array_reference_aligned | 2783 | 2783 | 2783 | 0.0 |
| array_rsm | 2783 | 2783 | 2783 | 0.0 |
| array_score | 2783 | 2783 | 2783 | 0.0 |
| array_valid_material | 2783 | 2783 | 2783 | 0.0 |
| array_valley | 2783 | 2783 | 2783 | 0.0 |
| current_points | 2783 | 2783 | 2783 | 0.0 |
| reference_points | 2783 | 2783 | 2783 | 0.0 |
| reference_quality | 2783 | 2783 | 2783 | 0.0 |
| roi | 2783 | 2783 | 2783 | 0.0 |
| status | 2783 | 2783 | 2783 | 0.0 |


整数观测的最近12点以整数和计算斜率，预测按1/1024px量化；有符号四舍五入和floor/ceil整数边界共用契约。无SVD微小浮动进入搜索边界。排序微分数1e-6、稳定x/y/ID tie-breaking；不是对验证帧添加epsilon。Python20004个数值边界检查及原生NumericSelfTest实际执行。连续数值容差分别1e-6和数组1e-5；离散选择、状态、点、列表长度/顺序必须严格相同。


首次原生全量回放发现三点弯512帧的csm/valley/newdark/flank_low四层有1个float32 ULP（1.52587890625e-5）的差异，超过运行前数组容差1e-5；所有离散路径、状态和端点仍相同。失败源码、DLL、全部原生结果、逐层表和日志保存在native_port_attempt1/，未删除或覆盖。

7×7原始像素局部复算把差异定位于对称高斯滤波加法顺序：原移植从近邻到远邻累加，冻结SciPy按远邻到近邻；仅改顺序就使该像素由202.1948699951172恢复到202.19488525390625。详见native_port_rounding_isolation.json四个控制。新C++全局按同一顺序实现，并固定sigma=.7由SciPy公式产生的binary64系数；核系数由参数确定，无图像拟合。独立合成算术核验见numeric_kernel_audit.json。此修正只实现冻结Python数值规范，不改Python算法、默认模式、任何检测阈值或容差，不是根据验证准确率修订模型。全2783输入、五模式重新回放，最终状态以本报告表格为准。第二次构建/回放日志为logs/build_port02.log和logs/native_parity_port02.log。


冻结V1没有反向修复，其旧current移植差异事实仍保留。新NUMERIC_CONTROL独立揭示新契约影响；本轮不能凭V2 parity通过宣称旧V1全域parity通过。构建日志logs/build.log，DLL与源码身份native_port_identity.json。新库不包装Python结果，不调用旧V1或生产DLL。
