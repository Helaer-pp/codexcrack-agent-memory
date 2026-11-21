# V5.16 失败帧与原因审计

四个候选均触发交付底线，日常默认保留 V5.15 S2。本轮研究交付与逐帧展示采用 V5.16 S3。联合命中为开发组A 17/19，三点弯 8/15，验证组C原点 18/20，验证组C亮区 18/20。

相对 V5.15 S2，展示阶段新增 Joint 的帧次为 three_point_bend/original/335、three_point_bend/original/413、three_point_bend/original/503。失去 Joint 的帧次为 three_point_bend/original/215、three_point_bend/original/271、three_point_bend/original/381、group_c/original/7。

| 阶段 | 交付底线检查 |
| --- | --- |
| S1 | 验证组C原点第 7 帧失去联合命中，三点弯最慢区段低于 8 FPS |
| S2 | 验证组C原点第 7 帧失去联合命中，三点弯最慢区段低于 8 FPS |
| S3 | 三点弯第 215 帧失去联合命中，三点弯第 271 帧失去联合命中，三点弯第 381 帧失去联合命中，验证组C原点第 7 帧失去联合命中，三点弯最慢区段低于 8 FPS |
| S4 | 三点弯第 215 帧失去联合命中，三点弯第 271 帧失去联合命中，三点弯第 381 帧失去联合命中，验证组C原点第 7 帧失去联合命中 |

## 阶段对照

| 组与点位 | 阶段 | 可见 | Hit@5 | Hit@10 | Joint | Severe | 无预测 | 整序列含映射 FPS/进程¹ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | V5.15 S2 | 19 | 12 | 17 | 17 | 0 | 0 | — |
| 开发组A | S1 | 19 | 12 | 17 | 17 | 0 | 0 | 12.60 |
| 开发组A | S2 | 19 | 12 | 17 | 17 | 0 | 0 | 12.55 |
| 开发组A | S3 | 19 | 12 | 17 | 17 | 0 | 0 | 12.46 |
| 开发组A | S4 | 19 | 12 | 17 | 17 | 0 | 0 | 11.22 |
| 三点弯 | V5.15 S2 | 15 | 3 | 8 | 8 | 0 | 1 | — |
| 三点弯 | S1 | 15 | 3 | 8 | 8 | 0 | 1 | 9.75 |
| 三点弯 | S2 | 15 | 3 | 8 | 8 | 0 | 0 | 9.23 |
| 三点弯 | S3 | 15 | 5 | 8 | 8 | 0 | 1 | 9.22 |
| 三点弯 | S4 | 15 | 5 | 8 | 8 | 0 | 1 | 8.66 |
| 验证组C原点 | V5.15 S2 | 20 | 15 | 19 | 19 | 0 | 0 | — |
| 验证组C原点 | S1 | 20 | 14 | 18 | 18 | 0 | 1 | 21.35 |
| 验证组C原点 | S2 | 20 | 14 | 18 | 18 | 0 | 1 | 21.01 |
| 验证组C原点 | S3 | 20 | 15 | 18 | 18 | 0 | 1 | 20.05 |
| 验证组C原点 | S4 | 20 | 15 | 18 | 18 | 0 | 1 | 18.24 |
| 验证组C亮区 | V5.15 S2 | 20 | 14 | 18 | 18 | 0 | 1 | — |
| 验证组C亮区 | S1 | 20 | 14 | 18 | 18 | 0 | 1 | 20.07 |
| 验证组C亮区 | S2 | 20 | 14 | 18 | 18 | 0 | 1 | 20.02 |
| 验证组C亮区 | S3 | 20 | 15 | 18 | 18 | 0 | 1 | 19.53 |
| 验证组C亮区 | S4 | 20 | 15 | 18 | 18 | 0 | 1 | 17.48 |

| 阶段 | 误报 /468 | P4 /36 | 反光弧 /36 | 弱桥 /36 | 分叉 /36 | P6 孤立各 /12 | P6 变形各 /12 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | 0 | 36 | 36 | 36 | 36 | 0 / 0 / 0 | 0 / 0 / 0 |
| S2 | 0 | 36 | 36 | 36 | 36 | 0 / 0 / 0 | 0 / 0 / 0 |
| S3 | 0 | 36 | 36 | 36 | 36 | 0 / 0 / 0 | 0 / 0 / 0 |
| S4 | 0 | 36 | 36 | 36 | 36 | 5 / 8 / 5 | 6 / 6 / 3 |

## 各阶段改变状态或命中的帧

| 组 | 点位 | 帧 | 阶段 | 证据路由 | 终止原因 | Joint | 误差 px | 划痕截断列索引 | 转移代价 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_c | original | 7 | S1 | PREEXISTING_CHECK → JOINT | ACCEPTED_PEAK → EMPTY | True → False | 0.84 → — | — | — |
| three_point_bend | original | 144 | S2 | JOINT → JOINT | MOUTH_DEAD_END → ACCEPTED_PEAK | False → False | — → 30.59 | — | 0.00 |
| three_point_bend | original | 215 | S3 | JOINT → JOINT | ACCEPTED_PEAK → CLOSED_RIM | True → False | 6.04 → — | — | — |
| three_point_bend | original | 271 | S3 | JOINT → JOINT | ACCEPTED_PEAK → ACCEPTED_PEAK | True → False | 2.27 → 10.35 | — | 5.45 |
| three_point_bend | original | 335 | S3 | JOINT → JOINT | ACCEPTED_PEAK → ACCEPTED_PEAK | False → True | 12.42 → 4.58 | — | 7.30 |
| three_point_bend | original | 381 | S3 | JOINT → JOINT | ACCEPTED_PEAK → ACCEPTED_PEAK | True → False | 8.18 → 10.24 | — | 8.51 |
| three_point_bend | original | 413 | S3 | JOINT → JOINT | ACCEPTED_PEAK → ACCEPTED_PEAK | False → True | 13.22 → 3.16 | — | 9.48 |
| three_point_bend | original | 503 | S3 | JOINT → JOINT | ACCEPTED_PEAK → ACCEPTED_PEAK | False → True | 19.46 → 3.96 | — | 3.90 |

## 重点帧

| 组 | 帧 | V5.15 S2 px | S1 | S2 | S3 | S4 | 展示阶段 dx | 覆盖率 | 精确率 | 逐阶段局部图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | 113 | 1.96 | 1.96 | 1.96 | 1.96 | 1.96 | -1.67 | 1.00 | 1.00 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/group_a_original_0113.jpg) |
| 开发组A | 299 | 5.25 | 5.25 | 5.25 | 5.25 | 5.25 | -4.70 | 1.00 | 1.00 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/group_a_original_0299.jpg) |
| 开发组A | 366 | 2.15 | 2.15 | 2.15 | 2.15 | 2.15 | -2.07 | 1.00 | 1.00 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/group_a_original_0366.jpg) |
| 开发组A | 398 | 12.10 | 12.10 | 12.10 | 12.10 | 12.10 | 11.85 | 1.00 | 0.99 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/group_a_original_0398.jpg) |
| 三点弯 | 144 | — | — | 30.59 | 30.59 | 30.59 | -26.76 | 0.59 | 1.00 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/three_point_bend_original_0144.jpg) |
| 三点弯 | 215 | 6.04 | 6.04 | 6.04 | — | — | — | 0.00 | 0.00 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/three_point_bend_original_0215.jpg) |
| 三点弯 | 248 | 9.14 | 9.14 | 9.14 | 3.37 | 3.37 | 3.08 | 1.00 | 1.00 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/three_point_bend_original_0248.jpg) |
| 三点弯 | 335 | 12.42 | 12.42 | 12.42 | 4.58 | 4.58 | -2.96 | 0.93 | 0.91 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/three_point_bend_original_0335.jpg) |
| 三点弯 | 381 | 8.18 | 8.18 | 8.18 | 10.24 | 10.24 | -10.18 | 1.00 | 1.00 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/three_point_bend_original_0381.jpg) |
| 三点弯 | 413 | 13.22 | 13.22 | 13.22 | 3.16 | 3.16 | -2.79 | 1.00 | 1.00 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/three_point_bend_original_0413.jpg) |
| 三点弯 | 435 | 10.44 | 10.44 | 10.44 | 11.63 | 11.63 | -11.60 | 0.99 | 0.96 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/three_point_bend_original_0435.jpg) |
| 三点弯 | 503 | 19.46 | 19.46 | 19.46 | 3.96 | 3.96 | -3.96 | 1.00 | 1.00 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/three_point_bend_original_0503.jpg) |
| 验证组C原点 | 7 | 0.84 | — | — | — | — | — | 0.00 | 0.00 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/group_c_original_0007.jpg) |
| 验证组C原点 | 38 | 1.58 | 1.58 | 1.58 | 1.58 | 1.58 | 1.54 | 0.98 | 0.98 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/group_c_original_0038.jpg) |
| 验证组C原点 | 54 | 1.51 | 1.51 | 1.51 | 1.51 | 1.51 | 1.51 | 1.00 | 1.00 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/group_c_original_0054.jpg) |
| 验证组C原点 | 510 | 14.96 | 14.96 | 14.96 | 14.96 | 14.96 | 14.94 | 1.00 | 0.98 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/group_c_original_0510.jpg) |
| 验证组C亮区 | 7 | — | — | — | — | — | — | 0.00 | 0.00 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/group_c_bright_0007.jpg) |
| 验证组C亮区 | 38 | 1.58 | 1.58 | 1.58 | 1.58 | 1.58 | 1.54 | 0.98 | 0.93 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/group_c_bright_0038.jpg) |
| 验证组C亮区 | 54 | 1.51 | 1.51 | 1.51 | 1.51 | 1.51 | 1.51 | 0.99 | 0.96 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/group_c_bright_0054.jpg) |
| 验证组C亮区 | 510 | 14.95 | 14.95 | 14.95 | 13.96 | 13.96 | 13.94 | 1.00 | 0.98 | [四阶段图](../../output/experiments/v516_precision_closure_r01/stage_views/group_c_bright_0510.jpg) |

| 组 | 帧 | 阶段 | 路由 | 终止 | 缺口窗宽 px | 局部残差 P97 | 近端重算 | 入口分 | 连续双列 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 三点弯 | 144 | S1 | JOINT | MOUTH_DEAD_END | 64 | 129.90 | False | 35.67 | 32 |
| 三点弯 | 144 | S2 | JOINT | ACCEPTED_PEAK | 64 | 129.90 | True | 43.58 | 32 |
| 三点弯 | 144 | S3 | JOINT | ACCEPTED_PEAK | 64 | 129.90 | True | 43.58 | 32 |
| 三点弯 | 144 | S4 | JOINT | ACCEPTED_PEAK | 64 | 129.90 | True | 43.58 | 32 |
| 验证组C原点 | 7 | S1 | JOINT | EMPTY | 57 | 6.06 | False | — | — |
| 验证组C原点 | 7 | S2 | JOINT | EMPTY | 57 | 6.06 | False | — | — |
| 验证组C原点 | 7 | S3 | JOINT | EMPTY | 57 | 6.06 | False | — | — |
| 验证组C原点 | 7 | S4 | JOINT | EMPTY | 57 | 6.06 | False | — | — |
| 验证组C亮区 | 7 | S1 | JOINT | INSUFFICIENT_TOTAL | 57 | 6.19 | False | 1.48 | 6 |
| 验证组C亮区 | 7 | S2 | JOINT | INSUFFICIENT_TOTAL | 57 | 6.19 | False | 1.48 | 6 |
| 验证组C亮区 | 7 | S3 | JOINT | INSUFFICIENT_TOTAL | 57 | 6.19 | False | 1.48 | 6 |
| 验证组C亮区 | 7 | S4 | JOINT | INSUFFICIENT_TOTAL | 57 | 6.19 | False | 1.48 | 6 |

### 验证组C第 7 帧路由反事实

固定同一输入图、测点与配准实现，单独强制缺口变化检测器返回静止或变化。该试验只作事后归因。native 为实际推理。

| 点位 | 实验开关 | 物理窗残差 | 顶点前沿 x | 配准位移 | 证据源 | 端点 | 裁决 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| original | native | 6.060031433105451 | 2248 | [0, 0] | JOINT | — | EMPTY |
| original | quiet | 6.060031433105451 | 2248 | [0, 0] | PREEXISTING_CHECK | [2273, 2339] | ACCEPTED_PEAK |
| original | changed | 6.060031433105451 | 2248 | [0, 0] | JOINT | — | EMPTY |
| bright | native | 6.186265258789064 | 2248 | [1, 0] | JOINT | — | INSUFFICIENT_TOTAL |
| bright | quiet | 6.186265258789064 | 2248 | [1, 0] | PREEXISTING_CHECK | [2273, 2339] | ACCEPTED_PEAK |
| bright | changed | 6.186265258789064 | 2248 | [1, 0] | JOINT | — | INSUFFICIENT_TOTAL |

验证组C第 7 帧的两种点位都找到前沿 x=2248。原点与亮区的局部残差 P97 分别为 6.06 和 6.19，实际均走 JOINT。固定输入并强制走既有暗线分支后，两者都恢复 (2273, 2339)，与标注相差 0.84 px。该帧的错误可定位到对局部变化的判断。亮区路径累计到 6 列仍不足以同时通过原图窄谷及连续双证据要求。

## P6 剩余错误

| P6 场景 | 倍率 | 通过 /12 | 无预测 | 端点误差 >10 | 端点命中但路径精确率低 |
| --- | --- | --- | --- | --- | --- |
| P6_isolated | 0.5 | 5 | 0 | 7 | 0 |
| P6_isolated | 1.0 | 8 | 0 | 3 | 1 |
| P6_isolated | 2.0 | 5 | 0 | 6 | 1 |
| P6_deformed_scratch | 0.5 | 6 | 0 | 6 | 0 |
| P6_deformed_scratch | 1.0 | 6 | 0 | 5 | 1 |
| P6_deformed_scratch | 2.0 | 3 | 0 | 8 | 1 |

## 末端惩罚与划痕判定

| 组 | 帧 | 阶段 | 整候选受罚列 | 整候选锐度扣分 | 划痕截断索引 | 端点误差 px |
| --- | --- | --- | --- | --- | --- | --- |
| 开发组A | 113 | S3 | 0 | 0.00 | — | 1.96 |
| 开发组A | 113 | S4 | 0 | 0.00 | None | 1.96 |
| 开发组A | 299 | S3 | 0 | 0.00 | — | 5.25 |
| 开发组A | 299 | S4 | 0 | 0.00 | None | 5.25 |
| 开发组A | 366 | S3 | 0 | 0.00 | — | 2.15 |
| 开发组A | 366 | S4 | 0 | 0.00 | None | 2.15 |
| 开发组A | 398 | S3 | 0 | 0.00 | — | 12.10 |
| 开发组A | 398 | S4 | 0 | 0.00 | None | 12.10 |
| 三点弯 | 144 | S3 | 0 | 0.00 | — | 30.59 |
| 三点弯 | 144 | S4 | 0 | 0.00 | None | 30.59 |
| 三点弯 | 215 | S3 | 19 | 53.20 | — | — |
| 三点弯 | 215 | S4 | 24 | 67.20 | 49 | — |
| 三点弯 | 248 | S3 | 13 | 36.40 | — | 3.37 |
| 三点弯 | 248 | S4 | 13 | 36.40 | None | 3.37 |
| 三点弯 | 335 | S3 | 20 | 56.00 | — | 4.58 |
| 三点弯 | 335 | S4 | 19 | 53.20 | None | 4.58 |
| 三点弯 | 381 | S3 | 16 | 44.80 | — | 10.24 |
| 三点弯 | 381 | S4 | 16 | 44.80 | None | 10.24 |
| 三点弯 | 413 | S3 | 15 | 42.00 | — | 3.16 |
| 三点弯 | 413 | S4 | 15 | 42.00 | None | 3.16 |
| 三点弯 | 435 | S3 | 15 | 42.00 | — | 11.63 |
| 三点弯 | 435 | S4 | 15 | 42.00 | None | 11.63 |
| 三点弯 | 503 | S3 | 26 | 72.80 | — | 3.96 |
| 三点弯 | 503 | S4 | 26 | 72.80 | None | 3.96 |
| 验证组C原点 | 7 | S3 | 0 | 0.00 | — | — |
| 验证组C原点 | 7 | S4 | 0 | 0.00 | — | — |
| 验证组C原点 | 38 | S3 | 0 | 0.00 | — | 1.58 |
| 验证组C原点 | 38 | S4 | 0 | 0.00 | None | 1.58 |
| 验证组C原点 | 54 | S3 | 0 | 0.00 | — | 1.51 |
| 验证组C原点 | 54 | S4 | 0 | 0.00 | None | 1.51 |
| 验证组C原点 | 510 | S3 | 0 | 0.00 | — | 14.96 |
| 验证组C原点 | 510 | S4 | 0 | 0.00 | None | 14.96 |
| 验证组C亮区 | 7 | S3 | 0 | 0.00 | — | — |
| 验证组C亮区 | 7 | S4 | 0 | 0.00 | None | — |
| 验证组C亮区 | 38 | S3 | 0 | 0.00 | — | 1.58 |
| 验证组C亮区 | 38 | S4 | 0 | 0.00 | None | 1.58 |
| 验证组C亮区 | 54 | S3 | 0 | 0.00 | — | 1.51 |
| 验证组C亮区 | 54 | S4 | 0 | 0.00 | None | 1.51 |
| 验证组C亮区 | 510 | S3 | 2 | 5.60 | — | 13.96 |
| 验证组C亮区 | 510 | S4 | 2 | 5.60 | None | 13.96 |

S3 在三点弯第 215 帧对两个主要候选均累计扣 53.2 分，新的端点截短后触发 CLOSED_RIM，两条路径均遭拒绝。第 435 帧从过追约 10 px 转为提前约 12 px。开发组A第 398 帧在人工端点后仍有 12 列，1–2 px 锐度中位数为 15.5 灰度级；验证组C第 510 帧的越界段也保有窄谷。宽浅暗晕不足以解释全部过追帧。

按 S3 输出路径在原图抽样。proximal_12 为标注尖端前 12 px，beyond_gt 为标注尖端之后。灰度落差越高代表该宽度上暗谷越深。标注仅用于离线划分区间。

| 组 | 点位 | 帧 | 区域 | 列数 | 1–2 px 锐度中位 | 4–6 px 落差中位 |
| --- | --- | --- | --- | --- | --- | --- |
| group_a | original | 398 | proximal_12 | 12 | 19.75 | 24.50 |
| group_a | original | 398 | beyond_gt | 12 | 15.50 | 15.50 |
| three_point_bend | original | 335 | proximal_12 | 10 | 5.75 | 15.83 |
| three_point_bend | original | 335 | beyond_gt | 0 | — | — |
| three_point_bend | original | 413 | proximal_12 | 10 | 5.25 | 16.67 |
| three_point_bend | original | 413 | beyond_gt | 0 | — | — |
| three_point_bend | original | 435 | proximal_12 | 1 | 7.50 | 21.67 |
| three_point_bend | original | 435 | beyond_gt | 0 | — | — |
| three_point_bend | original | 503 | proximal_12 | 9 | 5.00 | 21.33 |
| three_point_bend | original | 503 | beyond_gt | 0 | — | — |
| group_c | bright | 510 | proximal_12 | 12 | 24.00 | 38.33 |
| group_c | bright | 510 | beyond_gt | 14 | 10.50 | 15.50 |
| group_c | original | 510 | proximal_12 | 12 | 24.00 | 38.33 |
| group_c | original | 510 | beyond_gt | 15 | 9.50 | 15.33 |

列数与扣分来自胜出分支的完整回溯候选，可能包含最终尖端之后的列。

## 所有可见失败

| 点位 | 帧 | 误差 | dx | dy | 诊断 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| 开发组A | 398 | 12.10 | 11.85 | 2.45 | 回溯候选均未命中，胜出路径越过标注尖端 | [图与曲线](../../output/experiments/v516_precision_closure_r01/audit_views/group_a_original_0398.jpg) |
| 开发组A | 504 | 18.03 | -17.97 | 1.45 | 回溯候选均未命中，胜出路径提前终止 | [图与曲线](../../output/experiments/v516_precision_closure_r01/audit_views/group_a_original_0504.jpg) |
| 三点弯 | 144 | 30.59 | -26.76 | 14.80 | 回溯候选均未命中，胜出路径提前终止 | [图与曲线](../../output/experiments/v516_precision_closure_r01/audit_views/three_point_bend_original_0144.jpg) |
| 三点弯 | 178 | 36.27 | -34.41 | 11.46 | 回溯候选均未命中，胜出路径提前终止 | [图与曲线](../../output/experiments/v516_precision_closure_r01/audit_views/three_point_bend_original_0178.jpg) |
| 三点弯 | 215 | — | — | — | 无尖端，最终裁决 CLOSED_RIM | [图与曲线](../../output/experiments/v516_precision_closure_r01/audit_views/three_point_bend_original_0215.jpg) |
| 三点弯 | 271 | 10.35 | -10.20 | 1.75 | 回溯候选均未命中，胜出路径提前终止 | [图与曲线](../../output/experiments/v516_precision_closure_r01/audit_views/three_point_bend_original_0271.jpg) |
| 三点弯 | 381 | 10.24 | -10.18 | -1.12 | 回溯候选均未命中，胜出路径提前终止 | [图与曲线](../../output/experiments/v516_precision_closure_r01/audit_views/three_point_bend_original_0381.jpg) |
| 三点弯 | 407 | 25.07 | -24.94 | 2.62 | 回溯候选均未命中，胜出路径提前终止 | [图与曲线](../../output/experiments/v516_precision_closure_r01/audit_views/three_point_bend_original_0407.jpg) |
| 三点弯 | 435 | 11.63 | -11.60 | -0.90 | 回溯候选均未命中，胜出路径提前终止 | [图与曲线](../../output/experiments/v516_precision_closure_r01/audit_views/three_point_bend_original_0435.jpg) |
| 验证组C原点 | 7 | — | — | — | 无尖端，最终裁决 EMPTY | [图与曲线](../../output/experiments/v516_precision_closure_r01/audit_views/group_c_original_0007.jpg) |
| 验证组C原点 | 510 | 14.96 | 14.94 | -0.57 | 回溯候选均未命中，胜出路径越过标注尖端 | [图与曲线](../../output/experiments/v516_precision_closure_r01/audit_views/group_c_original_0510.jpg) |
| 验证组C亮区 | 7 | — | — | — | 无尖端，最终裁决 INSUFFICIENT_TOTAL | [图与曲线](../../output/experiments/v516_precision_closure_r01/audit_views/group_c_bright_0007.jpg) |
| 验证组C亮区 | 510 | 13.96 | 13.94 | -0.57 | 回溯候选均未命中，胜出路径越过标注尖端 | [图与曲线](../../output/experiments/v516_precision_closure_r01/audit_views/group_c_bright_0510.jpg) |

## 速度与扰动

| 阶段 | 含映射 FPS/进程 | 检测 FPS/进程 | 整池 FPS | 最慢 52 帧 FPS/进程 | 累计证据像素中位 |
| --- | --- | --- | --- | --- | --- |
| V5.15 S2 | 9.22 | 12.45 | 25.65 | 8.63 | 179916 |
| S1 | 8.19 | 10.89 | 22.97 | 6.65 | 179916 |
| S2 | 8.92 | 11.83 | 25.00 | 7.54 | 179916 |
| S3 | 8.54 | 11.29 | 24.16 | 7.38 | 179916 |
| S4 | 8.50 | 11.13 | 24.26 | 8.14 | 179916 |

| 阶段 | 上游映射 ms | 局部配准 ms | 其余证据场 ms | 法向证据 ms | DP ms |
| --- | --- | --- | --- | --- | --- |
| V5.15 S2 | 28.12 | 5.27 | 33.09 | 9.16 | 4.06 |
| S1 | 30.35 | 5.48 | 35.88 | 11.65 | 4.21 |
| S2 | 27.59 | 5.06 | 30.29 | 10.13 | 3.89 |
| S3 | 28.51 | 5.19 | 30.98 | 10.46 | 3.96 |
| S4 | 27.81 | 5.18 | 30.09 | 10.32 | 6.25 |

| 组 | 阶段 | 配对试次 | 实际 dx（px） | 像素比中位 | 时间比中位 | 时间比 P95 | 最大漂移 px | 状态改变 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | S1 | 26 | -150.00 至 -150.00 | 1.00 | 1.01 | 1.11 | 0.00 | 0 |
| 开发组A | S2 | 26 | -150.00 至 -150.00 | 1.00 | 1.00 | 1.13 | 0.00 | 0 |
| 开发组A | S3 | 26 | -150.00 至 -150.00 | 1.00 | 1.02 | 1.09 | 0.00 | 0 |
| 开发组A | S4 | 26 | -150.00 至 -150.00 | 1.00 | 1.01 | 1.16 | 0.00 | 0 |
| 三点弯 | S1 | 26 | -150.00 至 -150.00 | 1.00 | 1.01 | 1.38 | 0.00 | 0 |
| 三点弯 | S2 | 26 | -150.00 至 -150.00 | 1.00 | 1.01 | 1.15 | 0.00 | 0 |
| 三点弯 | S3 | 26 | -150.00 至 -150.00 | 1.00 | 1.01 | 1.16 | 0.00 | 0 |
| 三点弯 | S4 | 26 | -150.00 至 -150.00 | 1.00 | 1.01 | 1.15 | 0.00 | 0 |
| 验证组C亮区 | S1 | 26 | -17.00 至 -14.00 | 1.00 | 1.01 | 1.12 | 3.16 | 0 |
| 验证组C亮区 | S2 | 26 | -17.00 至 -14.00 | 1.00 | 1.02 | 1.17 | 3.16 | 0 |
| 验证组C亮区 | S3 | 26 | -17.00 至 -14.00 | 1.00 | 1.03 | 1.21 | 3.16 | 0 |
| 验证组C亮区 | S4 | 26 | -17.00 至 -14.00 | 1.00 | 1.04 | 1.21 | 3.16 | 0 |

[逐帧四联图、差分和视频](../../output/experiments/v516_precision_closure_r01/difference_views/index.html) · [逐帧尖端与长度](../../output/experiments/v516_precision_closure_r01/crack_lengths.csv) · [合成逐次结果](../../output/experiments/v516_precision_closure_r01/paired_probes.csv) · [冻结清单](../../output/experiments/v516_precision_closure_r01/freeze.json) · [阶段准入记录](../../output/experiments/v516_precision_closure_r01/selection.json)
