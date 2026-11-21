# CT2：GEOMETRY_SENSITIVITY_CHARACTERIZED

使用 auto 参考模式，on/off分别独立初始化并按同一帧序运行。两条468帧（含参考）仪表化时序均与对应生产 DLL 输出的状态、尖端、长度、全部双精度 CopyPath 零差异。未修改任何搜索、评分、停止、确认阈值。

原14帧运动替换复现，14/14 swap_off 路径与原 off路径一致；同历史 on/off 正对照64/64 精确通过。原14帧中11帧改变运动后路径改变，属于已建立因果链的复核，不是新的精度发现。

union(原14,原19)固定32帧，每帧38个独立初始化干预，共1216。每次通过值复制历史previous、observation队列、frame_index和最后确认状态；on/off历史对称替换。平移±x/±y幅度0.25/0.5/1/2/4/8px；旋转±0.02/0.05/0.1/0.2/0.4度，中心是on映射后的参考锚点中点。y向下，正旋转视觉顺时针；Q左乘on映射。幅度0复用positive_on实测记录，非新增试验。干预幅度不等于实际配准误差。

原C++ ridge深重建 337 个tile，gain和supported逐项完全一致。关键终止：

| frame | refine | last_tile_index | gain | supported | tile_action |
|---|---|---|---|---|---|
| 6 | on | 8 | 0.329378604888916 | 1 | STOP_SUPPORTED_OR_GAIN |
| 6 | off | 11 | 3.3567023277282715 | 2 | STOP_SUPPORTED_OR_GAIN |
| 18 | on | 8 | 0.9584131240844727 | 1 | STOP_SUPPORTED_OR_GAIN |
| 18 | off | 11 | 0.7194323539733887 | 1 | STOP_SUPPORTED_OR_GAIN |
| 84 | on | 8 | 1.073150634765625 | 1 | STOP_SUPPORTED_OR_GAIN |
| 84 | off | 12 | 0.2205524444580078 | 1 | STOP_SUPPORTED_OR_GAIN |

保留原 supported<3 或 gain<4 条件。tile_index为0起始；停止tile与成功延伸数量不同。逐tile表含take、blocked与最终stop。扩展tile数量仅统计进入了支持评估的tile；seed提前失败时为0，不能误读为进行了0次图像采样。

## 干预响应

| 类别 | 次数 |
|---|---|
| NO_EFFECT | 70 |
| INDETERMINATE | 329 |
| REJOIN | 54 |
| SEED_OR_ROI_CHANGE | 239 |
| GEOMETRY_ONLY_SHIFT | 492 |
| CONTINUATION_DOMINATED | 32 |

NO_EFFECT只表示路径逐点相同，状态另列；GEOMETRY_ONLY_SHIFT是在各自映射逆变换回参考后Hausdorff≤3px的工程分类；SEED_OR_ROI_CHANGE依据根部/seed材料位置差>3px；CONTINUATION_DOMINATED要求短到长P95≤3px且弧长差>30px；REJOIN要求分离后持续12px汇合。没有满足严格 TRUE_GEOMETRIC_BRANCH_DIVERGENCE 的新增介入案例，不强行补足类别。所有标签均不是物理真实性。

32张输入敏感曲线和32张原图/on/off对比在06_media/diagnostics，固定全案例展示。sensitivity_output_ranges给出本次干预集合内确认尖端x/y范围、确认缺失和tile范围；adjacent_amplitude_tile_changes逐条列离散幅度间tile跳变。它们是输出敏感区间，既不是正确尖端可信区间，也不是误差上界。首次持续分歧同时用1/3/5px容差并保留共同前缀、再汇合、原图文件名/输入hash/P1P2。

运动→tile map→current/score→seed/reward→ridge→支持与gain→最终停止的首次变量差异在first_internal_difference.csv。深trace的端点最佳/次佳分差不是K-best完整路径后验。若早期根部/seed改变，只能归因为输入传播链，不能把较短路径自动判成修复。

原19个未解释帧仍单独保留，19/19的物理原因和正确性未解决，详见独立复核表。新增受控类别不将其未解释数降为0。半合成已知运动360条另外提供材料探针运动误差和合成尖端误差，物理裂纹误差全部N/A。

**Gate 2：PASS_DIAGNOSTIC_ONLY。** 可复现运动介入对采样、延伸和停止的传播；不选on/off胜者，不修改生产A，不声称修复裂纹精度。
