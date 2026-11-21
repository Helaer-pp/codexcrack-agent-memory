# V6.1 失败帧与因果复核

开发组A 18/19、三点弯 8/15、验证组C原点 12/20、验证组C亮区 11/20。按亮区点位合计 37/54，按原点位合计 38/54，目标为 45/54。上述三组严重错误 0。开发组H单列，18 张可见标注联合命中 9 张，严重错误 2 张。候选未达替换条件，日常默认继续使用 V5.15 S2。

## 相对 V6.0 S2 的实帧变化

| 组 | 帧 | 旧 Joint | 新 Joint | 旧路由 | 新路由 | 新误差 px |
| --- | --- | --- | --- | --- | --- | --- |
| 开发组A | 504 | False | True | JOINT | JOINT | 7.12 |
| 验证组C原点 | 38 | True | False | JOINT | PREEXISTING_CHECK | 18.15 |
| 验证组C原点 | 54 | True | False | JOINT | PREEXISTING_CHECK | 29.89 |
| 验证组C原点 | 121 | True | False | JOINT | PREEXISTING_CHECK | 12.62 |
| 验证组C原点 | 195 | True | False | JOINT | PREEXISTING_CHECK | 11.00 |
| 验证组C原点 | 345 | True | False | JOINT | PREEXISTING_CHECK | 20.10 |
| 验证组C原点 | 363 | True | False | JOINT | PREEXISTING_CHECK | 14.03 |
| 验证组C亮区 | 38 | True | False | JOINT | PREEXISTING_CHECK | 18.15 |
| 验证组C亮区 | 54 | True | False | JOINT | PREEXISTING_CHECK | 29.89 |
| 验证组C亮区 | 121 | True | False | JOINT | PREEXISTING_CHECK | 12.62 |
| 验证组C亮区 | 195 | True | False | JOINT | PREEXISTING_CHECK | 11.00 |
| 验证组C亮区 | 232 | True | False | JOINT | PREEXISTING_CHECK | 17.01 |
| 验证组C亮区 | 345 | True | False | JOINT | PREEXISTING_CHECK | 20.10 |
| 验证组C亮区 | 363 | True | False | JOINT | PREEXISTING_CHECK | 14.03 |

## 全部失败标注帧

| 组 | 点位 | 帧 | 误差 px | 横向偏差 px | 配准 | 路由 | 失效表现 | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | original | 398 | 12.10 | 11.85 | ZERO_FALLBACK | JOINT | 全部回溯分支未命中，输出越过人工尖端 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_a_original_0398.jpg) |
| three_point_bend | original | 1 | — | — | MAPPED | PREEXISTING_CHECK | 未发布尖端，INSUFFICIENT_TOTAL | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/three_point_bend_original_0001.jpg) |
| three_point_bend | original | 144 | 29.71 | -26.76 | MAPPED | JOINT | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/three_point_bend_original_0144.jpg) |
| three_point_bend | original | 178 | 35.62 | -33.41 | MAPPED | JOINT | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/three_point_bend_original_0178.jpg) |
| three_point_bend | original | 335 | 10.32 | 10.04 | MAPPED | JOINT | 全部回溯分支未命中，输出越过人工尖端 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/three_point_bend_original_0335.jpg) |
| three_point_bend | original | 407 | 20.95 | -20.94 | MAPPED | JOINT | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/three_point_bend_original_0407.jpg) |
| three_point_bend | original | 413 | 13.22 | 13.21 | MAPPED | JOINT | 全部回溯分支未命中，输出越过人工尖端 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/three_point_bend_original_0413.jpg) |
| three_point_bend | original | 503 | 14.58 | 14.04 | MAPPED | JOINT | 全部回溯分支未命中，输出越过人工尖端 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/three_point_bend_original_0503.jpg) |
| group_c | original | 7 | — | — | MAPPED | JOINT | 未发布尖端，EMPTY | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_original_0007.jpg) |
| group_c | original | 38 | 18.15 | -16.46 | MAPPED | PREEXISTING_CHECK | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_original_0038.jpg) |
| group_c | original | 54 | 29.89 | -28.49 | MAPPED | PREEXISTING_CHECK | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_original_0054.jpg) |
| group_c | original | 121 | 12.62 | -12.62 | MAPPED | PREEXISTING_CHECK | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_original_0121.jpg) |
| group_c | original | 195 | 11.00 | -10.26 | MAPPED | PREEXISTING_CHECK | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_original_0195.jpg) |
| group_c | original | 345 | 20.10 | 12.49 | MAPPED | PREEXISTING_CHECK | 全部回溯分支未命中，输出越过人工尖端 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_original_0345.jpg) |
| group_c | original | 363 | 14.03 | -14.03 | MAPPED | PREEXISTING_CHECK | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_original_0363.jpg) |
| group_c | original | 510 | 15.96 | 15.94 | MAPPED | JOINT | 全部回溯分支未命中，输出越过人工尖端 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_original_0510.jpg) |
| group_c | bright | 7 | — | — | MAPPED | JOINT | 未发布尖端，MOUTH_DEAD_END | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_bright_0007.jpg) |
| group_c | bright | 38 | 18.15 | -16.46 | MAPPED | PREEXISTING_CHECK | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_bright_0038.jpg) |
| group_c | bright | 54 | 29.89 | -28.49 | MAPPED | PREEXISTING_CHECK | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_bright_0054.jpg) |
| group_c | bright | 121 | 12.62 | -12.62 | MAPPED | PREEXISTING_CHECK | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_bright_0121.jpg) |
| group_c | bright | 195 | 11.00 | -10.26 | MAPPED | PREEXISTING_CHECK | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_bright_0195.jpg) |
| group_c | bright | 232 | 17.01 | -17.00 | MAPPED | PREEXISTING_CHECK | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_bright_0232.jpg) |
| group_c | bright | 345 | 20.10 | 12.49 | MAPPED | PREEXISTING_CHECK | 全部回溯分支未命中，输出越过人工尖端 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_bright_0345.jpg) |
| group_c | bright | 363 | 14.03 | -14.03 | MAPPED | PREEXISTING_CHECK | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_bright_0363.jpg) |
| group_c | bright | 510 | 15.96 | 15.94 | MAPPED | JOINT | 全部回溯分支未命中，输出越过人工尖端 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_c_bright_0510.jpg) |
| group_h | original | 41 | 80.80 | -80.80 | ZERO_FALLBACK | JOINT | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0041.jpg) |
| group_h | original | 78 | — | — | ZERO_FALLBACK | PREEXISTING_CHECK | 未发布尖端，NO_CONFIRMED_PREEXISTING | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0078.jpg) |
| group_h | original | 115 | — | — | ZERO_FALLBACK | PREEXISTING_CHECK | 未发布尖端，NO_CONFIRMED_PREEXISTING | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0115.jpg) |
| group_h | original | 141 | 48.79 | -48.65 | ZERO_FALLBACK | JOINT | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0141.jpg) |
| group_h | original | 216 | 116.75 | -116.74 | ZERO_FALLBACK | JOINT | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0216.jpg) |
| group_h | original | 221 | 117.37 | -117.33 | ZERO_FALLBACK | JOINT | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0221.jpg) |
| group_h | original | 252 | 37.68 | -37.68 | ZERO_FALLBACK | JOINT | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0252.jpg) |
| group_h | original | 340 | 40.28 | -40.26 | ZERO_FALLBACK | JOINT | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0340.jpg) |
| group_h | original | 377 | 11.46 | -11.19 | ZERO_FALLBACK | JOINT | 全部回溯分支未命中，输出提前终止 | [图与曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0377.jpg) |

## 同像素窗口与门限对照

验证组C第 7 帧两点位的尺度从 375 变为 287.5 px，口门统计窗同步缩小。残差从 4.492 升至 5.145，仍超过新门限 5.0。只改门限、固定旧窗口才会得到预期静态判定。诊断中仅切换为既有暗线分支，两套点位均恢复至 0.845 px。另有 13 个相对 V6.0 S2 退化的验证组C点位帧次走了相反的错误路由，切回联合分支后 13/13 恢复 Joint。上述诊断输出不计入正式成绩。三点弯第 1 帧的参考与当前相同，残差为 0，最终仍因累计分不足而无尖端。

| 组 | 点位 | 帧 | 尺度 px | 门限版本 | 残差 | 门限 | 静态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| group_c | original | 7 | 375.00 | 6.0 | 4.49 | 4.00 | False |
| group_c | original | 7 | 375.00 | 6.1 | 4.49 | 5.00 | True |
| group_c | original | 7 | 287.50 | 6.0 | 5.15 | 4.00 | False |
| group_c | original | 7 | 287.50 | 6.1 | 5.15 | 5.00 | False |
| group_c | bright | 7 | 375.00 | 6.0 | 4.49 | 4.00 | False |
| group_c | bright | 7 | 375.00 | 6.1 | 4.49 | 5.00 | True |
| group_c | bright | 7 | 287.50 | 6.0 | 5.15 | 4.00 | False |
| group_c | bright | 7 | 287.50 | 6.1 | 5.15 | 5.00 | False |
| three_point_bend | original | 1 | 384.00 | 6.0 | 0.00 | 6.71 | True |
| three_point_bend | original | 1 | 384.00 | 6.1 | 0.00 | 8.05 | True |
| three_point_bend | original | 1 | 368.00 | 6.0 | 0.00 | 6.71 | True |
| three_point_bend | original | 1 | 368.00 | 6.1 | 0.00 | 8.05 | True |
| group_h | original | 78 | 384.00 | 6.0 | 5.64 | 6.29 | True |
| group_h | original | 78 | 384.00 | 6.1 | 5.64 | 7.54 | True |
| group_h | original | 78 | 322.00 | 6.0 | 6.92 | 6.29 | False |
| group_h | original | 78 | 322.00 | 6.1 | 6.92 | 7.54 | True |

## 冻结路径的路由反事实

| 组 | 点位 | 帧 | 正式路由 | 诊断路由 | 正式误差 px | 诊断误差 px | 诊断 Joint |
| --- | --- | --- | --- | --- | --- | --- | --- |
| group_c | original | 7 | JOINT | PREEXISTING_CHECK | — | 0.84 | True |
| group_c | bright | 7 | JOINT | PREEXISTING_CHECK | — | 0.84 | True |
| group_c | original | 38 | PREEXISTING_CHECK | JOINT | 18.15 | 0.58 | True |
| group_c | bright | 38 | PREEXISTING_CHECK | JOINT | 18.15 | 0.58 | True |
| group_c | original | 54 | PREEXISTING_CHECK | JOINT | 29.89 | 1.51 | True |
| group_c | bright | 54 | PREEXISTING_CHECK | JOINT | 29.89 | 1.51 | True |
| group_c | original | 121 | PREEXISTING_CHECK | JOINT | 12.62 | 2.62 | True |
| group_c | bright | 121 | PREEXISTING_CHECK | JOINT | 12.62 | 2.62 | True |
| group_c | original | 195 | PREEXISTING_CHECK | JOINT | 11.00 | 1.74 | True |
| group_c | bright | 195 | PREEXISTING_CHECK | JOINT | 11.00 | 2.93 | True |
| group_c | bright | 232 | PREEXISTING_CHECK | JOINT | 17.01 | 0.71 | True |
| group_c | original | 345 | PREEXISTING_CHECK | JOINT | 20.10 | 3.50 | True |
| group_c | bright | 345 | PREEXISTING_CHECK | JOINT | 20.10 | 3.50 | True |
| group_c | original | 363 | PREEXISTING_CHECK | JOINT | 14.03 | 5.10 | True |
| group_c | bright | 363 | PREEXISTING_CHECK | JOINT | 14.03 | 5.03 | True |
| group_h | original | 78 | PREEXISTING_CHECK | JOINT | — | — | False |
| group_h | original | 115 | PREEXISTING_CHECK | JOINT | — | 140.29 | False |

## 合成反例

弱材料桥 36/36。P3_parallel、P3_oblique 误报均已归零。P4_open 仍有 8 次误报，全部是零回退 JOINT，候选的连续双证据列可达到 11–17。另有 1 次口门反光弧误报具有 NCC 支持，因此不触发零回退门。总误报 9/468，上轮为 18/468。

| 反例 | 倍率 | 噪声 | 种子 | 曝光 | 路由 | 配准 | 候选最大连续双证据列 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P4_open | 1.0 | 5 | 17 | nominal | JOINT | ZERO_FALLBACK | 11 |
| P4_open | 1.0 | 5 | 17 | bright | JOINT | ZERO_FALLBACK | 11 |
| P4_open | 1.0 | 5 | 31 | nominal | JOINT | ZERO_FALLBACK | 11 |
| P4_open | 1.0 | 5 | 31 | bright | JOINT | ZERO_FALLBACK | 11 |
| P4_open | 2.0 | 5 | 17 | nominal | JOINT | ZERO_FALLBACK | 16 |
| P4_open | 2.0 | 5 | 17 | bright | JOINT | ZERO_FALLBACK | 16 |
| P4_open | 2.0 | 5 | 31 | nominal | JOINT | ZERO_FALLBACK | 17 |
| P4_open | 2.0 | 5 | 31 | bright | JOINT | ZERO_FALLBACK | 17 |
| mouth_glare_arc_only | 1.0 | 1 | 31 | nominal | JOINT | MAPPED | 8 |

左移包含重裁与重新定位，每组 20 个抽检帧，含重复共 26 个配对。开发组H 26 次左移后均无可用缺口体，无法计算尖端漂移。20 个独立测试帧的参考窗口右界均缩至 x=2603（不含），原参考顶点 x=2643 已在窗外。三点弯第 120 帧最大漂移 48.21 px。验证组C亮区实际只能移动 −17 至 −14 px，第 95 帧漂移 22.80 px。
