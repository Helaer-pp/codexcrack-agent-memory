# R03 第一阶段第三轮：Gate 2 安全失败，停止闭环

1. **生产源码：未修改。** 新代码仅 research/uctt_r03；生产及 R01/R02 共 333 个文件哈希复核无变化。MSVC19.29/v142、OpenCV4.4、CPU四线程。R02 DLL SHA256=55a0e7a79162da79e691ede9ff58229e59a56fdd1e0b1e3f609dc51128860402。新 A0/A1 DLL、源码及图像清单哈希见 frozen_manifest_r03.json。不存在生产合入；隔离实验可直接弃用。

2. **R02 复现：** CT2、group_h、group_c、group_x 的四个已知失败变体与七组 measured 连续窗口共 1428 初始化/帧案例全部对齐 R02 已存尖端和原始状态，差异 0。Three-point-bend、CT3 仅 measured 回放，未独立重跑它们完整扰动矩阵；GROUP_A仅1次控制确认，证据不足。group_x仅曝光历史；其他数据也非独立TEST。不能称七组扰动全部完成。

3. **A0–A4：** A1 raw/path/length 与 A0 差异 0/1428，旁路未改原始结果。A2有限输出/预测/回退已落地为实验 sidecar，配对确认坐标不变；它会拒绝部分原确认，覆盖损失见 state_only_comparison.csv，不能解释为稳定性改善。A3/A4因首次错锁测试失败被强制阻断，未创建闭环版本。完整16变体及±5%扫描未执行，R03全证据不完整。

4. **首次分歧：** 相同原图SHA和当前点轨迹下，不同初始点改变 origin/spacing/forward、搜索ROI及参考相关状态；候选路径/尖端随后分歧。实际变换、路径、状态与相邻帧已保存。具体首帧见 first_divergence_r03.csv。尚未分离ROI、参考mask、局部配准的因果贡献；“单纯缩小ROI可修复”仍是假设。完整长度状态差异与尖端失锁分别统计，不混算。

5. **状态机：** 16个明确标记的候选证据注入用例，15通过。无候选连续8帧 SEARCHING/无TRACK ROI；已确认静止裂纹维持TRACKING；闭合首帧OCCLUDED且预测无效、历史不更新；连续3次丢失RECOVERING；运动失效fallback；尺寸变化需重置。coherent_wrong_first_lock失败：整体平移的自洽干扰路径被首次接受并写历史，说明当前终端/路径证据不足以防错锁。这不是图像级真实准确率测试；真实错锁率仍NOT_VERIFIED。

6. **性能：** 981个非参考帧完整原生API计时，50ms未达标。按状态/组/分辨率P50/P95/P99/max及超时率见 performance_report.md / performance_summary.csv。新增 localReference、终端路径和tip-motion计时；所有相加统计使用互斥scope，R02重置计时器作差错误已规避。残余时间明确保留，未虚构归因。A3/A4性能不存在。

7. **限制：** 无物理GT、无真实多初始点外部跟踪轨迹（T2-B-real BLOCKED）；当前988张独立组帧原图可读取且哈希核对，无本批缺图。完整矩阵/闭环恢复/独立新TEST均未完成；原ABI没有预测来源字段，有限占位仅在实验扩展输出。并发/真实尺寸改变未全面认证。故障注入不等于真实无裂纹/闭合数据验证。

8. **结论：** R03_EVIDENCE=PARTIAL（Gate0–2停止证据已交付，完整R03未齐）；STABLE_DECOUPLING=FAIL（基线敏感性仍在，动态ROI未验证）；WRONG_LOCK_RISK=FAIL（注入错锁已证实，真实图像安全NOT_VERIFIED）；CPU_50MS=FAIL；PHASE1_GATE=FAIL。分离验收：EVIDENCE_COMPLETE=NO，BEHAVIOR=BLOCKED，LOCK_SAFETY=FAIL，PERF=FAIL，T2_B_REAL=BLOCKED，OVERALL_PHASE1=FAIL。保留A0，不合入。

9. **下一步最小实验（最多3项）：** (1) 用有独立归属标签的真实/受控干扰图对验证首次获取证据，替换相关的terminal/path布尔值；(2) 在已保存首分歧帧上分别固定运动/参考mask后交换ROI，定位敏感性的直接来源；(3) 仅对profile确认的最大互斥耗时项做输出等价优化。状态安全通过后再恢复完整扰动矩阵和A3/A4，不能提前宣称动态ROI有效。

## 本批确认覆盖

| dataset_id | variant_id | N | A0_confirmed | A2_confirmed | Cpair | removed_confirmation |
| --- | --- | --- | --- | --- | --- | --- |
| group_a | measured | 252 | 1 | 1 | 1 | 0 |
| group_c | measured | 80 | 50 | 1 | 1 | 49 |
| group_c | p1_plus_5pct_x | 80 | 50 | 1 | 1 | 49 |
| ct2 | measured | 120 | 110 | 16 | 16 | 94 |
| ct2 | shift_x_plus_2pct | 120 | 107 | 17 | 17 | 90 |
| group_h | measured | 120 | 114 | 72 | 72 | 42 |
| group_h | shift_y_plus_10pct | 120 | 63 | 3 | 3 | 60 |
| group_x | measured | 120 | 120 | 120 | 120 | 0 |
| group_x | shift_y_plus_10pct | 120 | 120 | 120 | 120 | 0 |
| three_point_bend | measured | 160 | 160 | 160 | 160 | 0 |
| ct3 | measured | 136 | 124 | 117 | 117 | 7 |

## 本批初始化扰动差值（真实准确率N/A）

| group | dataset_id | variant_id | C0 | Cv | Cpair | P95 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A0_R02 | group_c | p1_plus_5pct_x | 50 | 50 | 50 | 0.0000 | 6.0828 |
| A1_SHADOW | group_c | p1_plus_5pct_x | 50 | 50 | 50 | 0.0000 | 6.0828 |
| A2_STATE_ONLY | group_c | p1_plus_5pct_x | 1 | 1 | 1 | 0.0000 | 0.0000 |
| A0_R02 | ct2 | shift_x_plus_2pct | 110 | 107 | 106 | 112.7636 | 190.9188 |
| A1_SHADOW | ct2 | shift_x_plus_2pct | 110 | 107 | 106 | 112.7636 | 190.9188 |
| A2_STATE_ONLY | ct2 | shift_x_plus_2pct | 16 | 17 | 14 | 0.0000 | 0.0000 |
| A0_R02 | group_h | shift_y_plus_10pct | 114 | 63 | 58 | 1194.0617 | 1347.0935 |
| A1_SHADOW | group_h | shift_y_plus_10pct | 114 | 63 | 58 | 1194.0617 | 1347.0935 |
| A2_STATE_ONLY | group_h | shift_y_plus_10pct | 72 | 3 | 3 | 626.0966 | 626.0966 |
| A0_R02 | group_x | shift_y_plus_10pct | 120 | 120 | 120 | 296.0017 | 298.7189 |
| A1_SHADOW | group_x | shift_y_plus_10pct | 120 | 120 | 120 | 296.0017 | 298.7189 |
| A2_STATE_ONLY | group_x | shift_y_plus_10pct | 120 | 120 | 120 | 296.0017 | 298.7189 |

## 原生API性能

| kind | name | N | P50 | P95 | P99 | max | over_50_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dataset | group_a | 251 | 74.8649 | 76.9099 | 78.8077 | 107.6925 | 1.0000 |
| state | SEARCHING | 262 | 74.6413 | 76.8285 | 78.2685 | 107.6925 | 0.9122 |
| resolution | 1856x2072 | 251 | 74.8649 | 76.9099 | 78.8077 | 107.6925 | 1.0000 |
| state | TRACKING | 484 | 94.6517 | 139.6867 | 144.5446 | 147.3071 | 0.7562 |
| state | OCCLUDED | 6 | 75.8872 | 132.6244 | 137.0150 | 138.1126 | 0.6667 |
| state | RECOVERING | 229 | 115.7052 | 141.0036 | 141.9599 | 143.5819 | 0.6900 |
| dataset | group_c | 79 | 45.1610 | 46.3550 | 47.4024 | 49.6171 | 0.0000 |
| resolution | 5120x5120 | 357 | 94.3170 | 118.6654 | 120.1313 | 122.4082 | 0.7787 |
| dataset | ct2 | 119 | 116.6346 | 119.5412 | 121.2128 | 122.4082 | 1.0000 |
| dataset | group_h | 119 | 139.1204 | 142.7541 | 144.4818 | 144.5511 | 1.0000 |
| resolution | 5112x1406 | 119 | 139.1204 | 142.7541 | 144.4818 | 144.5511 | 1.0000 |
| dataset | group_x | 119 | 135.0771 | 140.0375 | 146.2879 | 147.3071 | 1.0000 |
| resolution | 3036x4024 | 119 | 135.0771 | 140.0375 | 146.2879 | 147.3071 | 1.0000 |
| dataset | three_point_bend | 159 | 94.1126 | 95.6376 | 101.8400 | 103.6994 | 1.0000 |
| dataset | ct3 | 135 | 9.3089 | 10.5097 | 10.9918 | 11.0922 | 0.0000 |
| resolution | 2024x1032 | 135 | 9.3089 | 10.5097 | 10.9918 | 11.0922 | 0.0000 |