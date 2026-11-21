# 开发组H MT · V6.3 全序列

开发组A 18/19，三点弯 8/15，验证组C原点 18/20，验证组C亮区 18/20，开发组H MT 8/18。开发组H目标为至少 9/18 且无超过 100 px 误差。

## 实际基准点平移

| 实移 px | 帧 | 材料带相同 | 参考顶点相同 | 当前顶点相同 | 状态相同 | 全路径相同 | 两次均有尖端 | 最大尖端漂移 px | 左移后参考 x |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| -150 | 410 | 410 | 410 | 410 | 410 | 410 | 329 | 0.00 | 2643 |
| -350 | 410 | 410 | 410 | 410 | 410 | 410 | 329 | 0.00 | 2643 |

两档扰动均从原始图像重建输入 ROI，参考与当前 P1/P2 同步移动。表内坐标均已还原至原图。全路径相同包含两次均为空，另列同时有尖端的帧数。

## 白底漆与局部配准

放开白底漆上限后，21,987 次尝试中 1,394 次进入 NCC，实际采用 549 次。410 帧中 310 帧至少有一个采纳窗，100 帧仍全部零回退。采纳一个合并窗计一次，即使两侧共用。非零位移另列。V6.2 的 63,960 次尝试全部在 NCC 之前被拒，两版物理尺度与窗口数量不同。

| 窗 | 尝试 | 上下文不足 | 低纹理 | 进入 NCC | 峰不明确 | 低相关 | 采用 | 采用非零位移 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| up | 7380 | 410 | 6734 | 236 | 0 | 0 | 236 | 236 |
| down | 7380 | 410 | 6290 | 680 | 424 | 31 | 225 | 224 |
| single | 7227 | 410 | 6339 | 478 | 351 | 39 | 88 | 87 |

## 可见标注与逐步替换

| 按顺序替换组件 | Joint/18 | >100 px | 发布尖端 |
| --- | --- | --- | --- |
| V6.2 | 3 | 1 | 6 |
| 仅换材料带与缺口精修 | 8 | 1 | 13 |
| 再换配准掩膜与 NCC 数值处理 | 8 | 2 | 14 |
| 完整 V6.3，加入两项终端复核 | 8 | 2 | 14 |

| 离线回放 | 216 误差 px | 221 误差 px | 252 误差 px | 317 误差 px |
| --- | --- | --- | --- | --- |
| V6.2 | — | — | 102.70 | — |
| 仅换材料带与缺口精修 | — | 117.37 | 37.68 | — |
| 再换配准掩膜与 NCC 数值处理 | 116.75 | 117.37 | 37.68 | — |
| 完整 V6.3，加入两项终端复核 | 116.75 | 117.37 | 37.68 | — |

| 开发组H帧 | 6.1 Joint | 6.2 Joint | 6.3 Joint | 误差 px | 终止 | 帧级配准 | 预测处上/下窗 | 标注处上/下窗 | 最近分支误差 px |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 41 | False | False | False | — | INSUFFICIENT_TOTAL | MAPPED | — | single/side | 98.90 |
| 74 | True | False | True | 7.12 | ACCEPTED_PEAK | MAPPED | single/side | single/side | 7.12 |
| 78 | False | False | False | — | MOUTH_DEAD_END | MAPPED | — | zero/zero | 149.13 |
| 96 | True | False | True | 1.85 | ACCEPTED_PEAK | ZERO_FALLBACK | zero/zero | zero/zero | 1.85 |
| 115 | False | False | False | — | INSUFFICIENT_TOTAL | MAPPED | — | zero/zero | 146.25 |
| 141 | False | False | False | 48.79 | ACCEPTED_PEAK | MAPPED | zero/zero | zero/zero | 48.79 |
| 169 | True | False | True | 4.61 | ACCEPTED_PEAK | ZERO_FALLBACK | zero/zero | zero/zero | 4.61 |
| 197 | True | True | True | 1.83 | ACCEPTED_PEAK | MAPPED | zero/zero | zero/zero | 1.83 |
| 216 | False | False | False | 116.75 | ACCEPTED_PEAK | MAPPED | side/side | zero/zero | 116.75 |
| 221 | False | False | False | 117.37 | ACCEPTED_PEAK | MAPPED | side/side | zero/zero | 117.37 |
| 252 | False | False | False | 37.68 | ACCEPTED_PEAK | MAPPED | zero/zero | zero/zero | 37.68 |
| 276 | True | True | True | 2.89 | ACCEPTED_PEAK | ZERO_FALLBACK | zero/zero | zero/zero | 2.89 |
| 304 | True | True | True | 2.91 | ACCEPTED_PEAK | ZERO_FALLBACK | zero/zero | zero/zero | 2.91 |
| 317 | True | False | False | — | INSUFFICIENT_TOTAL | MAPPED | — | zero/zero | 239.52 |
| 340 | False | False | False | 40.28 | ACCEPTED_PEAK | ZERO_FALLBACK | zero/zero | zero/zero | 40.28 |
| 377 | False | False | False | 11.46 | ACCEPTED_PEAK | ZERO_FALLBACK | zero/zero | zero/zero | 11.46 |
| 397 | True | False | True | 2.95 | ACCEPTED_PEAK | ZERO_FALLBACK | zero/zero | zero/zero | 2.95 |
| 401 | True | False | True | 7.94 | ACCEPTED_PEAK | MAPPED | zero/zero | zero/zero | 7.94 |

第 252 帧的误差由 102.70 降至 37.68 px，仅替换几何组件就出现同样改善。第 216 帧在采用新配准后从拒绝变为提前 116.75 px；第 221 帧在仅替换几何时已提前 117.37 px。两帧各有一个已发布分支，连续双证据分别为 13、24 列。预测端点处上下窗均采用分侧配准，但两个标注尖端所在的上下窗均回退为零位移。第 317 帧因证据累计不足而漏检。下一轮宜检查这几帧从已发布端点到标注端点之间的原灰度窄脊、差分和逐窗配准状态，重点区分路径是否可达以及何处停止。

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

[第 78 帧原图定位对照](../../output/experiments/v63_white_primer_r01/group_h_0078_geometry.png) · [全序列两档位移与坐标](../../output/experiments/v63_white_primer_r01/group_h_shift.csv) · [逐窗拒绝或采用](../../output/experiments/v63_white_primer_r01/group_h_ncc_windows.csv) · [逐帧计数](../../output/experiments/v63_white_primer_r01/group_h_ncc_frames.csv) · [开发组H分步回放](../../output/experiments/v63_white_primer_r01/group_h_stages.csv) · [开发组H视频](../../output/experiments/v63_white_primer_r01/difference_views/group_h.mp4)
