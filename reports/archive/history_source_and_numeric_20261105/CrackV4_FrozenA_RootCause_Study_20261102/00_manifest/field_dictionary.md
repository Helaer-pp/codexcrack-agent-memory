# 字段说明与封装审计备注

本说明只澄清已冻结字段含义，不改变规则、统计、检测结果或留出测量；没有重跑第五组。

- `frame_id=0` 是参考帧；当前帧为1…N。排除组Xnum524未使用，按此前用户确认。
- `baseline.formal`、`A_tip_valid`、`A_length_valid`来自冻结DLL的正式V2结果及冻结快照；是否确认以这些布尔量为准。`baseline.native.status`是保留的内部状态字符串，可能仍显示`weak_candidate`，不能据该字符串覆盖V2确认状态。示例排除组X473正式尖端/长度均确认。
- `match_attempts.csv/search_matrix_shape`在本轮冻结源码中实际写入的是 **NCC响应网格25×25**，字段名不够准确；输入搜索图像实际为55×55、模板31×31，即±12px。此元数据命名不影响匹配或统计，原值保留以遵守冻结约束。
- `texture_eligible`仅检查有限有效模板上的std和梯度条件，不包含全部空间/材料/亮度前置排除，因此不能把四级计数误读为不加说明的同一逐级漏斗。
- `independent_validation_pass`：匹配已通过、空间上未参与拟合、训练样本平移修正后的残差≤2px。它是条件一致性样本数；并非每帧可评价数量，不代表物理运动误差已知。
- `first_failure`是原拒绝序列首个原因的归类，互斥；`secondary_reasons`可以并存。`CLIPPED_OR_LOW_DYNAMIC_RANGE`包括孔洞、非材料和编码高灰度，不能理解为ADC饱和实证。
- `legacy_photo_pass`与当前固定路径的`CASE_P1`属于不同用途；P1不授权参考差分或新增裂纹判定。P2为零也不证明没有信息损失。
- 路径影像证据减弱位置不是物理尖端。`CONTINUATION_DOMINATED_GEOMETRY`只描述两条路径的几何包含/延伸关系，不宣称较长或较短路径正确。
- `native_cpp_latency.csv`只含2510个当前帧；清单和逐帧风险表另含5张参考帧，共2515行。仪表化耗时不得并入生产性能。
- `source_and_scripts/frozen_A/CrackV4.dll`是未修改的既有冻结DLL副本，SHA256与任务指定值相同；不是本轮新发布的算法DLL。
