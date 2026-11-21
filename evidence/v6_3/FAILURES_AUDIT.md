# V6.3 失败审计

开发组A 18/19，三点弯 8/15，验证组C原点 18/20，验证组C亮区 18/20，开发组H MT 8/18。开发组H目标为至少 9/18 且无超过 100 px 误差。

| 组/点位 | 帧 | 可见 | 6.1 Joint | 6.2 Joint | 6.3 Joint | Hit@5 | Hit@10 | >100 px | 恢复 | 新增失败 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | 551 | 19 | 18 | 18 | 18 | 13 | 18 | 0 | 0 | 0 |
| 三点弯 | 520 | 15 | 8 | 8 | 8 | 2 | 8 | 0 | 0 | 0 |
| 验证组C原点 | 562 | 20 | 12 | 18 | 18 | 13 | 18 | 0 | 0 | 0 |
| 验证组C亮区 | 562 | 20 | 11 | 18 | 18 | 15 | 18 | 0 | 0 | 0 |
| 开发组H MT | 410 | 18 | 9 | 3 | 8 | 6 | 8 | 2 | 5 | 0 |

## 对 V6.2 的逐帧变化

| 组 | 帧 | 6.2 Joint | 6.3 Joint | 原误差 px | 现误差 px | 终止 |
| --- | --- | --- | --- | --- | --- | --- |
| 开发组H MT | 74 | False | True | — | 7.12 | ACCEPTED_PEAK |
| 开发组H MT | 96 | False | True | — | 1.85 | ACCEPTED_PEAK |
| 开发组H MT | 169 | False | True | 19.46 | 4.61 | ACCEPTED_PEAK |
| 开发组H MT | 397 | False | True | — | 2.95 | ACCEPTED_PEAK |
| 开发组H MT | 401 | False | True | 85.13 | 7.94 | ACCEPTED_PEAK |

## 全部可见标注失败帧

| 组 | 点位 | 帧 | 误差 px | 横差 px | 帧级配准 | 终止 | 最近分支误差 px | 原因 | 图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | original | 398 | 12.10 | 11.85 | ZERO_FALLBACK | ACCEPTED_PEAK | 12.10 | 全部分支均未命中，越过尖端 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_a_original_0398.jpg) |
| three_point_bend | original | 1 | — | — | MAPPED | INSUFFICIENT_TOTAL | 2.09 | 候选路径的累计证据未达发布门槛 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/three_point_bend_original_0001.jpg) |
| three_point_bend | original | 144 | 29.71 | -26.76 | MAPPED | ACCEPTED_PEAK | 29.71 | 全部分支均未命中，提前终止 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/three_point_bend_original_0144.jpg) |
| three_point_bend | original | 178 | 35.62 | -33.41 | MAPPED | ACCEPTED_PEAK | 14.66 | 全部分支均未命中，提前终止 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/three_point_bend_original_0178.jpg) |
| three_point_bend | original | 335 | 10.32 | 10.04 | MAPPED | ACCEPTED_PEAK | 10.29 | 全部分支均未命中，越过尖端 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/three_point_bend_original_0335.jpg) |
| three_point_bend | original | 407 | 20.95 | -20.94 | MAPPED | ACCEPTED_PEAK | 20.94 | 全部分支均未命中，提前终止 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/three_point_bend_original_0407.jpg) |
| three_point_bend | original | 413 | 13.22 | 13.21 | MAPPED | ACCEPTED_PEAK | 13.22 | 全部分支均未命中，越过尖端 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/three_point_bend_original_0413.jpg) |
| three_point_bend | original | 503 | 14.58 | 14.04 | MAPPED | ACCEPTED_PEAK | 14.58 | 全部分支均未命中，越过尖端 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/three_point_bend_original_0503.jpg) |
| group_c | original | 7 | — | — | MAPPED | EMPTY | — | 回溯为空 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_c_original_0007.jpg) |
| group_c | original | 510 | 15.96 | 15.94 | MAPPED | ACCEPTED_PEAK | 15.96 | 全部分支均未命中，越过尖端 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_c_original_0510.jpg) |
| group_c | bright | 7 | — | — | MAPPED | MOUTH_DEAD_END | 21.17 | 从缺口唇缘出发的路径未通过连续性检查 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_c_bright_0007.jpg) |
| group_c | bright | 510 | 15.96 | 15.94 | MAPPED | ACCEPTED_PEAK | 15.96 | 全部分支均未命中，越过尖端 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_c_bright_0510.jpg) |
| group_h | original | 41 | — | — | MAPPED | INSUFFICIENT_TOTAL | 98.90 | 候选路径的累计证据未达发布门槛 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_h_original_0041.jpg) |
| group_h | original | 78 | — | — | MAPPED | MOUTH_DEAD_END | 149.13 | 从缺口唇缘出发的路径未通过连续性检查 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_h_original_0078.jpg) |
| group_h | original | 115 | — | — | MAPPED | INSUFFICIENT_TOTAL | 146.25 | 候选路径的累计证据未达发布门槛 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_h_original_0115.jpg) |
| group_h | original | 141 | 48.79 | -48.65 | MAPPED | ACCEPTED_PEAK | 48.79 | 全部分支均未命中，提前终止 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_h_original_0141.jpg) |
| group_h | original | 216 | 116.75 | -116.74 | MAPPED | ACCEPTED_PEAK | 116.75 | 全部分支均未命中，提前终止 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_h_original_0216.jpg) |
| group_h | original | 221 | 117.37 | -117.33 | MAPPED | ACCEPTED_PEAK | 117.37 | 全部分支均未命中，提前终止 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_h_original_0221.jpg) |
| group_h | original | 252 | 37.68 | -37.68 | MAPPED | ACCEPTED_PEAK | 37.68 | 全部分支均未命中，提前终止 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_h_original_0252.jpg) |
| group_h | original | 317 | — | — | MAPPED | INSUFFICIENT_TOTAL | 239.52 | 候选路径的累计证据未达发布门槛 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_h_original_0317.jpg) |
| group_h | original | 340 | 40.28 | -40.26 | ZERO_FALLBACK | ACCEPTED_PEAK | 40.28 | 全部分支均未命中，提前终止 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_h_original_0340.jpg) |
| group_h | original | 377 | 11.46 | -11.19 | ZERO_FALLBACK | ACCEPTED_PEAK | 11.46 | 全部分支均未命中，提前终止 | [单帧与分支曲线](../../output/experiments/v63_white_primer_r01/audit_views/group_h_original_0377.jpg) |

## 开发组H的定位、配准与终止

| 实移 px | 帧 | 材料带相同 | 参考顶点相同 | 当前顶点相同 | 状态相同 | 全路径相同 | 两次均有尖端 | 最大尖端漂移 px | 左移后参考 x |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| -150 | 410 | 410 | 410 | 410 | 410 | 410 | 329 | 0.00 | 2643 |
| -350 | 410 | 410 | 410 | 410 | 410 | 410 | 329 | 0.00 | 2643 |

| 窗 | 尝试 | 上下文不足 | 低纹理 | 进入 NCC | 峰不明确 | 低相关 | 采用 | 采用非零位移 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| up | 7380 | 410 | 6734 | 236 | 0 | 0 | 236 | 236 |
| down | 7380 | 410 | 6290 | 680 | 424 | 31 | 225 | 224 |
| single | 7227 | 410 | 6339 | 478 | 351 | 39 | 88 | 87 |

| 离线回放 | 216 误差 px | 221 误差 px | 252 误差 px | 317 误差 px |
| --- | --- | --- | --- | --- |
| V6.2 | — | — | 102.70 | — |
| 仅换材料带与缺口精修 | — | 117.37 | 37.68 | — |
| 再换配准掩膜与 NCC 数值处理 | 116.75 | 117.37 | 37.68 | — |
| 完整 V6.3，加入两项终端复核 | 116.75 | 117.37 | 37.68 | — |

第 252 帧的误差由 102.70 降至 37.68 px，仅替换几何组件就出现同样改善。第 216 帧在采用新配准后从拒绝变为提前 116.75 px；第 221 帧在仅替换几何时已提前 117.37 px。两帧各有一个已发布分支，连续双证据分别为 13、24 列。预测端点处上下窗均采用分侧配准，但两个标注尖端所在的上下窗均回退为零位移。第 317 帧因证据累计不足而漏检。下一轮宜检查这几帧从已发布端点到标注端点之间的原灰度窄脊、差分和逐窗配准状态，重点区分路径是否可达以及何处停止。

[第 78 帧原图定位对照](../../output/experiments/v63_white_primer_r01/group_h_0078_geometry.png) · [全序列两档位移与坐标](../../output/experiments/v63_white_primer_r01/group_h_shift.csv) · [逐窗拒绝或采用](../../output/experiments/v63_white_primer_r01/group_h_ncc_windows.csv) · [逐帧计数](../../output/experiments/v63_white_primer_r01/group_h_ncc_frames.csv) · [开发组H分步回放](../../output/experiments/v63_white_primer_r01/group_h_stages.csv) · [开发组H视频](../../output/experiments/v63_white_primer_r01/difference_views/group_h.mp4)

## 成对合成回归

负样本误报 0/468。P4_open 和 weak_material_bridge 分别通过 36/36、36/36。936 个正样本逐例比对原通过判据，新增失败 0，新增通过 0。

旧误报 mouth_glare_arc_only（倍率 1.0，噪声 1，种子 31，曝光 nominal）配准为 MAPPED，最大连续双证据 8 列，触发短分支拒绝 True，实际发布尖端 False。

| 工况 | 试次 | 6.2 通过 | 6.3 通过 | 6.3 误报 |
| --- | --- | --- | --- | --- |
| P1_lower | 36 | 34 | 34 | 0 |
| P1_upper | 36 | 33 | 33 | 0 |
| P1_weak_gap | 216 | 168 | 168 | 0 |
| P2_fade | 36 | 17 | 17 | 0 |
| P2_isolated | 36 | 36 | 36 | 0 |
| P3_oblique | 36 | 36 | 36 | 0 |
| P3_parallel | 36 | 36 | 36 | 0 |
| P4_open | 36 | 36 | 36 | 0 |
| P4_ring | 36 | 36 | 36 | 0 |
| P5_isolated | 36 | 36 | 36 | 0 |
| P5_plastic_zone | 36 | 24 | 24 | 0 |
| P5_plastic_zone_negative | 36 | 36 | 36 | 0 |
| P6_deformed_scratch | 36 | 6 | 6 | 0 |
| P6_deformed_scratch_negative | 36 | 36 | 36 | 0 |
| P6_isolated | 36 | 4 | 4 | 0 |
| active_fork | 36 | 36 | 36 | 0 |
| control_glare | 36 | 36 | 36 | 0 |
| control_noise_blank | 36 | 36 | 36 | 0 |
| control_preexisting | 36 | 36 | 36 | 0 |
| control_same_blank | 36 | 36 | 36 | 0 |
| control_texture_tail | 36 | 36 | 36 | 0 |
| dipole_edge | 36 | 36 | 36 | 0 |
| dipole_with_crack | 36 | 36 | 36 | 0 |
| material_edge_glare | 36 | 36 | 36 | 0 |
| mouth_blob_branch | 36 | 36 | 36 | 0 |
| mouth_blob_competing | 36 | 27 | 27 | 0 |
| mouth_blob_only | 36 | 36 | 36 | 0 |
| mouth_glare_arc_branch | 36 | 36 | 36 | 0 |
| mouth_glare_arc_only | 36 | 35 | 36 | 0 |
| mouth_thick_valley | 36 | 36 | 36 | 0 |
| two_rise_bridge | 36 | 36 | 36 | 0 |
| weak_material_bridge | 36 | 36 | 36 | 0 |
| weak_tail_attached | 36 | 36 | 36 | 0 |
| weak_tail_blank | 36 | 36 | 36 | 0 |

冻结后另设白底漆对照，裂纹长度取 8–22 px。均匀白底上，零回退单极复核新增放行 4 条已知新增的合成短线（10–13 px）；该规则在正式实帧中没有新增选中分支。模拟旧线侧移 3 px 时，两种缺口灰度合计出现 22/30 误报，V6.2 为 18/30，新增 4 次均经过 MAPPED 路由。这组额外压力试验说明，正式矩阵的 0/468 不能外推到所有红蓝偶极。

| 缺口灰度 | 额外白底漆工况 | 长度试次 | 6.2 发布 | 6.3 发布 | 单极放行 |
| --- | --- | --- | --- | --- | --- |
| 0 | 新增暗线 | 15 | 9 | 13 | 4 |
| 0 | 旧线侧移 3 px | 15 | 9 | 9 | 0 |
| 0 | 无变化 | 15 | 0 | 0 | 0 |
| 22 | 新增暗线 | 15 | 9 | 13 | 0 |
| 22 | 旧线侧移 3 px | 15 | 9 | 13 | 0 |
| 22 | 无变化 | 15 | 0 | 0 | 0 |

[90 个冻结后白底漆对照](../../output/experiments/v63_white_primer_r01/primer_controls.csv)
