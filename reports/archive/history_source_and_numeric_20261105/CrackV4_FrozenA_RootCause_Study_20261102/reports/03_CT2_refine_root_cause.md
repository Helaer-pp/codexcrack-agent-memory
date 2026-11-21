# CT2 refine 源码级因果追踪

参考模式实际为 auto，不是 clean。最初研究预跑误设 clean 已停止且归档 INVALID_mode0；未通过输出等价性验收，不用于结论。两条正式对照都从相同 auto 参考和相同逐帧输入初始化独立 Detector，只有 refine 不同。配置、输入图像 SHA 和 P1/P2 见输入清单，两个 Detector 的输入序列相同，但其输出派生历史可以自然不同，不能假称内部历史始终相同。

双配置均确认尖端的分母 367；尖端版本分歧 {"n": 367, "P50": 1.5020652449210923, "P95": 127.21387823793437, "P99": 131.9824279267895, "Max": 133.90231215330087} px。该数值不是物理尖端误差。研究编译对两配置全量逐帧的 native状态和双精度 CopyPath 均与正式DLL零差异，见 instrumentation_identity.json。

## 首个不同量及传播链

- `void Detector::motion`：冻结源第 762 行。
- `void Detector::refineRoot`：冻结源第 1015 行。
- `Tile Detector::tile`：冻结源第 1047 行。
- `bool Detector::seed`：冻结源第 1200 行。
- `Result Detector::process`：冻结源第 1587 行。
- `std::pair<Path, double> ridge`：冻结源第 359 行。

`motion`先由两点方向和中心生成刚体初值，开关两侧初值逐帧相同；refine开启时对参考背景patch运行phaseCorrelate。接受的patch经过位移中位数离群筛选，再视数量/空间跨度用SVD拟合刚体，角度<8度且中位残差<2px时采用，否则平移修正。关闭refine且已给锚点时跳过这些patch修正。首个结构性差异发生在运动精修支路，实际每帧修正值、支路和patch响应保存在 trace_all.jsonl。

变换经 transformed(tile.xy) 改变当前图的实际采样坐标；refineRoot也在变换后的根部窗口匹配。因此原参考网格相同不保证当前灰度、score、starts、reward和回溯父状态相同。根部/seed的差异与DP扩展差异分开归类，不能把所有大分歧称为DP跳支。

全量初步归类 {"INDETERMINATE": 19, "SEED_OR_ROI_CHANGE": 359, "COORDINATE_SHIFT": 33, "BRANCH_SWITCH": 56}；运动支路 {"rigid_SVD_refinement": 321, "translation_fallback": 117, "no_phase_patch_accepted": 29}。归类是固定几何定义的诊断标签，不是物理拓扑真值。首个>5px帧 1，首个>30px帧 6，最大差异帧 84。路径先统一到原图坐标，再在1/3/5px容差下记录持续12px的首次分歧与重汇合。

## 同历史运动替换反事实

| frame_id | 类型 | 尖端分歧 px | 根部材料位移 px | 变换场最大差 px | 替换运动后路径改变 | 替换后与 off 完全相同 |
|---|---|---|---|---|---|---|
| 1 | INDETERMINATE | 7.31 | 0.59 | 0.70 | True | True |
| 2 | SEED_OR_ROI_CHANGE | 0.06 | 6.33 | 7.30 | True | True |
| 3 | SEED_OR_ROI_CHANGE | N/A | 4.34 | 5.49 | True | True |
| 4 | SEED_OR_ROI_CHANGE | 2.01 | 4.11 | 4.10 | True | True |
| 5 | SEED_OR_ROI_CHANGE | 0.14 | 6.18 | 7.20 | True | True |
| 6 | SEED_OR_ROI_CHANGE | 130.06 | 5.34 | 5.80 | True | True |
| 7 | SEED_OR_ROI_CHANGE | 1.21 | 6.72 | 8.02 | True | True |
| 17 | SEED_OR_ROI_CHANGE | 0.95 | 6.57 | 7.49 | True | True |
| 18 | SEED_OR_ROI_CHANGE | 127.58 | 4.63 | 5.57 | True | True |
| 19 | COORDINATE_SHIFT | 0.00 | 0.00 | 0.00 | False | True |
| 58 | COORDINATE_SHIFT | 0.00 | 0.00 | 0.00 | False | True |
| 83 | SEED_OR_ROI_CHANGE | 0.37 | 5.64 | 7.40 | True | True |
| 84 | SEED_OR_ROI_CHANGE | 133.90 | 4.75 | 6.05 | True | True |
| 85 | COORDINATE_SHIFT | 0.00 | 0.00 | 0.00 | False | True |

预选 14 帧：同一 frozen-on 的 previous 与 observation deque 输入下，替回 on 变换的正对照全部精确复现 on；只替换为 off 的 R/T，11 帧路径改变，14 帧与原 off 路径完全相同。该对照确认这些案例中几何映射对下游输出的因果作用，未证明哪一种运动更接近真实材料，也不把配置自身称为软件错误。

深度数据保存tile当前/参考/score/mask、seed的field/reward/penalty/starts、原DP父状态与每列累积分数。每列最优/次优端点状态与ridge最优列边际不等于两条完整路径的K-best分差；近似平局只能作为条件敏感性证据，不能据此选物理真支路。未解释帧 19/467 必须保留 UNEXPLAINED，不用相关性填补因果链。

[全量追踪](../03_CT2_refine/ct2_refine_trace_all.csv) · [关键案例](../03_CT2_refine/ct2_root_cause_cases.csv) · [首次持续分歧](../03_CT2_refine/ct2_path_first_divergence.csv) · [研究源码差异](../source_and_scripts/instrumentation.diff)


## 结论边界与补充证据

统一等级：运动替换使11个预选输出变化为 `CONFIRMED_CAUSAL`，范围只限这些案例的运动映射因果作用；另3帧对同一介入无路径效应，`REFUTED`仅指这些帧的该命题。其他配置的物理正确性为 `NOT_IDENTIFIABLE`，实际曝光收益为 `NOT_TESTED`。

359帧 SEED_OR_ROI_CHANGE 是按根部材料坐标差>3px或seed状态不同定义的几何标签；它不是359次检测错误。预选6/18/84帧的大尖端差不能全归结为一次DP主体跳支，路径逐块延伸和停止位置也发生改变。列边际不是整条备选路径分差。

首次内部差异从 motion 的 refine 支路传递至 R/T、当前采样坐标、灰度/score、seed、后续ridge与停止位置。[逐变量首个差异](../03_CT2_refine/first_internal_differences.csv)、[深度矩阵数值差](../03_CT2_refine/deep_matrix_differences.csv)、[DP每列状态边际](../03_CT2_refine/DP_column_state_margins.csv)提供预选案例逐项证据。首个>30px帧为frame_id=6，选取及图像SHA均由DEV锁定。未额外对比原四组中除CT2外的refine配置，其他组同类机制为 NOT_TESTED。

## 大分歧的关键补充：继续延伸与主体分叉不同

| frame_id | 短路径配置 | 短弧长px | 长弧长px | 短到长P95距离px | 长路径首次离开短路径s(px) |
|---|---|---|---|---|---|
| 6 | on | 441.92 | 574.40 | 0.72 | 445.53 |
| 18 | on | 440.34 | 572.59 | 1.01 | 445.68 |
| 84 | on | 440.57 | 578.55 | 0.53 | 445.65 |

按固定定义，短路径到长路径距离P95<=3px且两者弧长相差>30px记 CONTINUATION_DOMINATED_GEOMETRY；双配置都确认的367帧中 40 帧满足。该规则只描述几何关系，不判断物理真尖端。对第6/18/84帧，不能用约127px的尖端差直接宣称主体跳支。

直接用保存矩阵调用同一冻结C++ ridge函数，对 286 个预选tile的原始DP终止列和gain与日志精确相等，见 [停止条件重建](../03_CT2_refine/tile_stop_reconstruction.csv) 及验证JSON。第84帧on在第8号延伸tile（从0计）只剩1个受支持样本、gain=1.07315，触发原process的 supported<3 或 gain<4 停止；off继续若干块，到第12号tile只剩1个支持、gain=0.22055才停止。两者最终原stop均为 evidence_ended。这是评分经逐块延伸影响停止位置的明确证据，不是新停止逻辑。

[主体/继续延伸全量几何](../03_CT2_refine/continuation_vs_body_geometry.csv) · [预选停止链](../03_CT2_refine/continuation_cases.csv)。同历史替换运动可精确复现off路径，因果作用已隔离；运动物理正确性和真实裂纹末端仍不可识别。
