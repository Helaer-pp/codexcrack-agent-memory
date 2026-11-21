# V6.0 失败帧与分侧配准复核

研究展示采用 V6.0 S2。开发组A 17/19，三点弯 8/15，验证组C原点 18/20，验证组C亮区 18/20。S3 负样本误报 18/468，弱材料桥 36/36，相对 S2 丢失 1 个实帧 Joint。日常默认保留 V5.15 S2。

S1 的三点弯 Joint 从 8/15 升至 9/15，验证组C两套点位均达到 19/20。开发组A全部材料窗回退至零局部位移，三点弯共有 527 个分块的上下位移不同。S1 同时替换了旧映射和下游配准，准确率变化不能全部归因于分侧位移。S2 让验证组C 7 两套点位走相同的 JOINT 分支，但两处都失去尖端。S1 在两处走既有暗线分支，误差均为 0.84 px。三点弯 144 在 S2 恢复路径，端点误差 29.17 px。S3 在三点弯 306 保留了 3.49 px 的端点误差，但路径未过 Joint。

S2/S3 的 18 个负样本误报来自 P4_open 11 次、P3_parallel 4 次和 P3_oblique 3 次。这些反例全部在上、下材料窗均回退零位移时进入 JOINT 并输出尖端。优先排查失去可靠配准后联合证据的准入，以及从原生缺口变化切换路由时的短路径判定。

## 与 V5.15 S2 的实帧对照

| 组 | 阶段 | 可见帧 | Hit@10 | Hit@5 | Joint | Severe | 无尖端 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | V5.15 S2 | 19 | 17 | 12 | 17 | 0 | 0 |
| 开发组A | S1 | 19 | 17 | 12 | 17 | 0 | 0 |
| 开发组A | S2 | 19 | 17 | 12 | 17 | 0 | 0 |
| 开发组A | S3 | 19 | 17 | 12 | 17 | 0 | 0 |
| 三点弯 | V5.15 S2 | 15 | 8 | 3 | 8 | 0 | 1 |
| 三点弯 | S1 | 15 | 9 | 4 | 9 | 0 | 1 |
| 三点弯 | S2 | 15 | 8 | 2 | 8 | 0 | 1 |
| 三点弯 | S3 | 15 | 8 | 2 | 7 | 0 | 1 |
| 验证组C原点 | V5.15 S2 | 20 | 19 | 15 | 19 | 0 | 0 |
| 验证组C原点 | S1 | 20 | 19 | 15 | 19 | 0 | 0 |
| 验证组C原点 | S2 | 20 | 18 | 13 | 18 | 0 | 1 |
| 验证组C原点 | S3 | 20 | 18 | 13 | 18 | 0 | 1 |
| 验证组C亮区 | V5.15 S2 | 20 | 18 | 14 | 18 | 0 | 1 |
| 验证组C亮区 | S1 | 20 | 19 | 16 | 19 | 0 | 0 |
| 验证组C亮区 | S2 | 20 | 18 | 15 | 18 | 0 | 1 |
| 验证组C亮区 | S3 | 20 | 18 | 15 | 18 | 0 | 1 |

## 逐阶段 Joint 得失

| 组 | 点位 | 帧 | 阶段 | Joint | 误差 px | 路由 | 终止原因 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| three_point_bend | original | 1 | S2 | True → False | 2.98 → — | PREEXISTING_CHECK → PREEXISTING_CHECK | INSUFFICIENT_TOTAL |
| three_point_bend | original | 306 | S3 | True → False | 3.49 → 3.49 | JOINT → JOINT | ACCEPTED_PEAK |
| three_point_bend | original | 435 | S1 | False → True | 10.44 → 5.52 | JOINT → JOINT | ACCEPTED_PEAK |
| group_c | bright | 7 | S1 | False → True | — → 0.84 | JOINT → PREEXISTING_CHECK | ACCEPTED_PEAK |
| group_c | bright | 7 | S2 | True → False | 0.84 → — | PREEXISTING_CHECK → JOINT | MOUTH_DEAD_END |
| group_c | original | 7 | S2 | True → False | 0.84 → — | PREEXISTING_CHECK → JOINT | EMPTY |

## 逐帧失败原因

| 组 | 点位 | 帧 | 误差 px | 横向偏差 px | 覆盖率 | 精确率 | 直接观察 | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | original | 398 | 12.10 | 11.85 | 1.00 | 0.99 | 回溯分支均未命中，选中尖端在标注右侧 | [原图与候选曲线](../../output/experiments/v60_split_reg_r01/audit_views/group_a_original_0398.jpg) |
| group_a | original | 504 | 18.03 | -17.97 | 0.97 | 1.00 | 回溯分支均未命中，选中尖端提前结束 | [原图与候选曲线](../../output/experiments/v60_split_reg_r01/audit_views/group_a_original_0504.jpg) |
| three_point_bend | original | 1 | — | — | 0.00 | 0.00 | 未输出尖端，终止原因为 INSUFFICIENT_TOTAL | [原图与候选曲线](../../output/experiments/v60_split_reg_r01/audit_views/three_point_bend_original_0001.jpg) |
| three_point_bend | original | 144 | 29.17 | -25.76 | 0.63 | 1.00 | 存在 10 px 内分支，最终门控或排序选中另一支 | [原图与候选曲线](../../output/experiments/v60_split_reg_r01/audit_views/three_point_bend_original_0144.jpg) |
| three_point_bend | original | 178 | 35.62 | -33.41 | 0.56 | 1.00 | 回溯分支均未命中，选中尖端提前结束 | [原图与候选曲线](../../output/experiments/v60_split_reg_r01/audit_views/three_point_bend_original_0178.jpg) |
| three_point_bend | original | 335 | 10.32 | 10.04 | 1.00 | 1.00 | 回溯分支均未命中，选中尖端在标注右侧 | [原图与候选曲线](../../output/experiments/v60_split_reg_r01/audit_views/three_point_bend_original_0335.jpg) |
| three_point_bend | original | 407 | 20.95 | -20.94 | 0.96 | 1.00 | 回溯分支均未命中，选中尖端提前结束 | [原图与候选曲线](../../output/experiments/v60_split_reg_r01/audit_views/three_point_bend_original_0407.jpg) |
| three_point_bend | original | 413 | 13.22 | 13.21 | 1.00 | 0.99 | 回溯分支均未命中，选中尖端在标注右侧 | [原图与候选曲线](../../output/experiments/v60_split_reg_r01/audit_views/three_point_bend_original_0413.jpg) |
| three_point_bend | original | 503 | 14.58 | 14.04 | 0.97 | 0.92 | 回溯分支均未命中，选中尖端在标注右侧 | [原图与候选曲线](../../output/experiments/v60_split_reg_r01/audit_views/three_point_bend_original_0503.jpg) |
| group_c | bright | 7 | — | — | 0.00 | 0.00 | 未输出尖端，终止原因为 MOUTH_DEAD_END | [原图与候选曲线](../../output/experiments/v60_split_reg_r01/audit_views/group_c_bright_0007.jpg) |
| group_c | bright | 510 | 14.96 | 14.94 | 1.00 | 0.98 | 回溯分支均未命中，选中尖端在标注右侧 | [原图与候选曲线](../../output/experiments/v60_split_reg_r01/audit_views/group_c_bright_0510.jpg) |
| group_c | original | 7 | — | — | 0.00 | 0.00 | 未输出尖端，终止原因为 EMPTY | [原图与候选曲线](../../output/experiments/v60_split_reg_r01/audit_views/group_c_original_0007.jpg) |
| group_c | original | 510 | 15.96 | 15.94 | 1.00 | 0.97 | 回溯分支均未命中，选中尖端在标注右侧 | [原图与候选曲线](../../output/experiments/v60_split_reg_r01/audit_views/group_c_original_0510.jpg) |

## 指定帧残差

偶极计数取同列相隔 2 px、符号相反且两端绝对差均 ≥5 灰度级的材料像素对，排除裂纹中线 ±3 px。按每千有效像素对报告。该量衡量配准残差，真实开口也可能产生相反符号。 下表三阶段均取相同原图矩形、相同有效材料像素。mouth 为缺口前 80 px，distal 为随后最多 400 px。图册中的参考位置使用同一映射反算。

| 组 | 点位 | 帧 | 区段 | 公共像素对 | 基线 | S1 | S2 | 对照图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| three_point_bend | original | 144 | distal | 19767 | 50.08 | 49.43 | 48.87 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/three_point_bend_original_0144_distal.png) |
| three_point_bend | original | 144 | mouth | 3467 | 40.67 | 31.73 | 31.73 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/three_point_bend_original_0144_mouth.png) |
| three_point_bend | original | 178 | distal | 19770 | 66.51 | 68.94 | 69.50 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/three_point_bend_original_0178_distal.png) |
| three_point_bend | original | 178 | mouth | 3465 | 60.32 | 46.75 | 47.91 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/three_point_bend_original_0178_mouth.png) |
| three_point_bend | original | 215 | distal | 19782 | 67.33 | 61.82 | 62.03 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/three_point_bend_original_0215_distal.png) |
| three_point_bend | original | 215 | mouth | 3570 | 64.71 | 47.62 | 46.78 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/three_point_bend_original_0215_mouth.png) |
| three_point_bend | original | 381 | distal | 19776 | 68.97 | 60.22 | 60.38 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/three_point_bend_original_0381_distal.png) |
| three_point_bend | original | 381 | mouth | 3597 | 70.61 | 52.27 | 58.10 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/three_point_bend_original_0381_mouth.png) |
| three_point_bend | original | 407 | distal | 19778 | 49.09 | 45.40 | 45.30 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/three_point_bend_original_0407_distal.png) |
| three_point_bend | original | 407 | mouth | 3598 | 60.31 | 43.64 | 43.91 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/three_point_bend_original_0407_mouth.png) |
| group_c | bright | 7 | distal | 11002 | 61.53 | 77.44 | 77.26 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_bright_0007_distal.png) |
| group_c | bright | 7 | mouth | 3992 | 73.15 | 79.41 | 79.41 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_bright_0007_mouth.png) |
| group_c | bright | 38 | distal | 11025 | 53.24 | 48.34 | 48.34 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_bright_0038_distal.png) |
| group_c | bright | 38 | mouth | 3988 | 70.21 | 58.93 | 58.93 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_bright_0038_mouth.png) |
| group_c | bright | 54 | distal | 11940 | 46.15 | 47.15 | 47.15 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_bright_0054_distal.png) |
| group_c | bright | 54 | mouth | 3992 | 59.87 | 58.87 | 58.87 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_bright_0054_mouth.png) |
| group_c | bright | 335 | distal | 11606 | 61.95 | 75.05 | 74.88 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_bright_0335_distal.png) |
| group_c | bright | 335 | mouth | 3995 | 93.87 | 68.09 | 68.09 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_bright_0335_mouth.png) |
| group_c | bright | 510 | distal | 12113 | 49.53 | 32.77 | 32.11 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_bright_0510_distal.png) |
| group_c | bright | 510 | mouth | 3998 | 74.79 | 38.27 | 38.27 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_bright_0510_mouth.png) |
| group_c | original | 7 | distal | 11002 | 55.26 | 57.26 | 57.26 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_original_0007_distal.png) |
| group_c | original | 7 | mouth | 3992 | 66.13 | 69.14 | 69.14 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_original_0007_mouth.png) |
| group_c | original | 38 | distal | 11025 | 43.72 | 49.25 | 49.25 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_original_0038_distal.png) |
| group_c | original | 38 | mouth | 3988 | 63.44 | 63.44 | 63.44 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_original_0038_mouth.png) |
| group_c | original | 54 | distal | 11940 | 49.25 | 45.81 | 45.81 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_original_0054_distal.png) |
| group_c | original | 54 | mouth | 3992 | 77.40 | 58.87 | 58.87 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_original_0054_mouth.png) |
| group_c | original | 335 | distal | 11606 | 63.33 | 60.06 | 59.62 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_original_0335_distal.png) |
| group_c | original | 335 | mouth | 3995 | 75.34 | 63.58 | 74.34 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_original_0335_mouth.png) |
| group_c | original | 510 | distal | 12113 | 49.95 | 42.19 | 38.80 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_original_0510_distal.png) |
| group_c | original | 510 | mouth | 3998 | 69.03 | 45.02 | 45.02 | [同窗差分](../../output/experiments/v60_split_reg_r01/registration_audit/group_c_original_0510_mouth.png) |

## 验证组C点位及口门路由

| 组 | 点位 | 帧 | 基线 px | S1 px | S2 px | S3 px | 展示阶段路由 | 终止 | 原生残差 | 路由阈值 | 口门重算 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | original | 113 | 1.96 | 1.03 | 1.03 | 1.03 | JOINT | ACCEPTED_PEAK | 25.32 | 6.42 | False |
| group_a | original | 299 | 5.25 | 5.25 | 5.25 | 5.25 | JOINT | ACCEPTED_PEAK | 120.36 | 6.42 | False |
| group_a | original | 366 | 2.15 | 2.15 | 2.15 | 2.15 | JOINT | ACCEPTED_PEAK | 149.59 | 6.42 | False |
| three_point_bend | original | 144 | — | — | 29.17 | 29.17 | JOINT | ACCEPTED_PEAK | 103.00 | 6.71 | False |
| three_point_bend | original | 178 | 36.27 | 35.62 | 35.62 | 35.62 | JOINT | ACCEPTED_PEAK | 143.01 | 6.71 | False |
| three_point_bend | original | 215 | 6.04 | 5.06 | 5.06 | 5.06 | JOINT | ACCEPTED_PEAK | 104.65 | 6.71 | False |
| three_point_bend | original | 381 | 8.18 | 8.18 | 9.41 | 9.41 | JOINT | ACCEPTED_PEAK | 105.58 | 6.71 | False |
| three_point_bend | original | 407 | 17.27 | 20.01 | 20.95 | 20.95 | JOINT | ACCEPTED_PEAK | 104.44 | 6.71 | False |
| group_c | bright | 7 | — | 0.84 | — | — | JOINT | MOUTH_DEAD_END | 4.49 | 4.00 | False |
| group_c | bright | 38 | 1.58 | 0.58 | 0.58 | 0.58 | JOINT | ACCEPTED_PEAK | 4.39 | 4.00 | False |
| group_c | bright | 54 | 1.51 | 1.51 | 1.51 | 1.51 | JOINT | ACCEPTED_PEAK | 4.25 | 4.00 | False |
| group_c | bright | 335 | 2.85 | 2.85 | 2.85 | 2.85 | JOINT | ACCEPTED_PEAK | 5.50 | 4.00 | False |
| group_c | bright | 510 | 14.95 | 15.96 | 14.96 | 14.96 | JOINT | ACCEPTED_PEAK | 4.95 | 4.00 | False |
| group_c | original | 7 | 0.84 | 0.84 | — | — | JOINT | EMPTY | 4.49 | 4.00 | False |
| group_c | original | 38 | 1.58 | 0.58 | 0.58 | 0.58 | JOINT | ACCEPTED_PEAK | 4.39 | 4.00 | False |
| group_c | original | 54 | 1.51 | 1.51 | 1.51 | 1.51 | JOINT | ACCEPTED_PEAK | 4.25 | 4.00 | False |
| group_c | original | 335 | 2.85 | 2.85 | 2.85 | 2.85 | JOINT | ACCEPTED_PEAK | 5.16 | 4.42 | False |
| group_c | original | 510 | 14.96 | 15.96 | 15.96 | 15.96 | JOINT | ACCEPTED_PEAK | 6.19 | 4.42 | False |

| 阶段 | 同路由 /562 | 同状态 /562 | 双侧均有尖端 | 距离 ≤1 px |
| --- | --- | --- | --- | --- |
| S1 | 558 | 561 | 557 | 461 |
| S2 | 513 | 561 | 528 | 401 |
| S3 | 513 | 561 | 528 | 401 |

固定裁框和点对中点，将开发组A、三点弯的 P1/P2 间距缩至 0.8 倍或增至 1.2 倍，80 次比对中有 0 次路径变化、0 次路由变化。验证组C真实更换点位后，49 帧 S2 路由不同，其中 49 帧的后端尺度相同，49 帧出现固定参考轮廓顶点坐标变化，2 帧当前轮廓顶点也发生变化。第 7 帧两侧的后端尺度均为 375 px，灰度残差均为 4.49，高于门限 4.00，因而都进入 JOINT。左移检查中，验证组C亮区第 469 帧实际移动 −14.5 px，尖端漂移 10.0 px。[固定裁框间距对照](../../output/experiments/v60_split_reg_r01/spacing.csv) · [参考与当前顶点坐标](../../output/experiments/v60_split_reg_r01/native_vertices.csv)

## 合成负样本归因

| 阶段 | 反例 | 基线终止 | 新路由 | 全窗零回退 | 误报次数 |
| --- | --- | --- | --- | --- | --- |
| S1 | P4_open | CONTOUR_SHORT_DUAL_RUN | JOINT | True | 5 |
| S1 | P4_open | INSUFFICIENT_TOTAL | JOINT | True | 31 |
| S2 | P3_oblique | NO_REACHABLE_POSITIVE | JOINT | True | 3 |
| S2 | P3_parallel | NO_REACHABLE_POSITIVE | JOINT | True | 4 |
| S2 | P4_open | CONTOUR_SHORT_DUAL_RUN | JOINT | True | 1 |
| S2 | P4_open | INSUFFICIENT_TOTAL | JOINT | True | 10 |
| S3 | P3_oblique | NO_REACHABLE_POSITIVE | JOINT | True | 3 |
| S3 | P3_parallel | NO_REACHABLE_POSITIVE | JOINT | True | 4 |
| S3 | P4_open | CONTOUR_SHORT_DUAL_RUN | JOINT | True | 1 |
| S3 | P4_open | INSUFFICIENT_TOTAL | JOINT | True | 10 |

各误报与相同输入的 V5.15 S2 成对复算。全窗零回退表示仅剩粗对齐，联合分支仍可能接受口门或既有暗线。该对照定位到失效的门控路径；它不能单独证明某一位移引发了误报。[每次误报的候选证据](../../output/experiments/v60_split_reg_r01/negative_audit.csv)
