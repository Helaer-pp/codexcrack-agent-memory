# V6.2 全局参考缺口定位与门控验证

开发组A与三点弯守住 18/19、8/15，验证组C原点与亮区均为 18/20，V6.1 退化的 13 个帧次恢复 13 个。开发组H的联合命中从 9/18 降到 3/18，左移验收失败。V6.2 S2 作为研究候选交付，日常默认 V5.15 S2。

[四组逐帧图与视频](../../output/experiments/v62_global_notch_r01/difference_views/index.html) · [全量尖端和裂纹长度（px）](../../output/experiments/v62_global_notch_r01/crack_lengths.csv) · [推理冻结清单](../../output/experiments/v62_global_notch_r01/freeze.json) · [失败审计](FAILURES_AUDIT.md) · [开发组H诊断](GROUP_H_REPORT.md)

本轮按任务书在 CodexCrack 实现。核对到的 GeminiCrack 独立项目源码仍使用局部参考搜索与固定 10 列门槛。

## 算法与评测口径

参考帧先沿用边缺口快路，失败时扫描有效材料带全宽的暗连通域；当前帧围绕参考端点加基准点平移，在局部对齐。保留 aperture × 11.5 的物理尺度，恢复静态口门门限 max(4, 0.035 × 灰度极差, 3 × 噪声)。仅有轮廓粗配准的 JOINT 分支要求双证据连续列达到 max(10, round(0.065 × 实测物理尺度))。尺度以像素计，各倍率的实际门槛见合成逐例表。

开发组A 551 帧、三点弯 520 帧、验证组C 562 帧、开发组H 410 帧，共 2,043 张图、2,605 个帧与点位组合。验证组C两套点位使用同一序列，bright 检查点及邻域处于亮区。三点弯和验证组C只作冻结回归，人工标注仅作离线比较，排除组X排除。Joint 要求尖端误差 ≤10 原图像素，且路径精确率和覆盖率均 ≥80%。无输出计为未命中。

在 run_crack_tip.py 顶部启用 use_validation_candidate，或运行 CrackTipRunner.exe --candidate。相同 EXE 抽查 9 个帧与点位组合，状态、尖端、路径和长度与冻结结果一致。

## 冻结实帧结果

| 组/点位 | 全帧 | 可见标注 | V6.0 Joint | V6.1 Joint | V6.2 Hit@5 | Hit@10 | Joint | >100 px |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | 551 | 19 | 17 | 18 | 13 | 18 | 18 | 0 |
| 三点弯 | 520 | 15 | 8 | 8 | 2 | 8 | 8 | 0 |
| 验证组C原点 | 562 | 20 | 18 | 12 | 13 | 18 | 18 | 0 |
| 验证组C亮区 | 562 | 20 | 18 | 11 | 15 | 18 | 18 | 0 |
| 开发组H MT | 410 | 18 | — | 9 | 2 | 3 | 3 | 1 |

| 组/点位 | 帧 | 参考边缘快路 | 参考全宽回退 | 有 NCC 位移 | 全窗零回退 | 发布尖端 |
| --- | --- | --- | --- | --- | --- | --- |
| 开发组A | 551 | 551 | 0 | 0 | 551 | 492 |
| 三点弯 | 520 | 520 | 0 | 520 | 0 | 452 |
| 验证组C原点 | 562 | 562 | 0 | 562 | 0 | 546 |
| 验证组C亮区 | 562 | 562 | 0 | 562 | 0 | 542 |
| 开发组H MT | 410 | 0 | 410 | 0 | 410 | 155 |

三点弯 520 帧、4 个工作进程。逐帧处理耗时合计折算 8.70 FPS，含读图、校验与进程调度的整池墙钟吞吐 11.45 FPS。4.5 FPS 门槛通过。

## 验证组C退化帧逐次对照

| 点位 | 帧 | V6.1 路由 | V6.2 路由 | 残差 | 恢复门限 | 误差 px | 恢复 Joint |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 验证组C原点 | 38 | PREEXISTING_CHECK | JOINT | 4.35 | 4.00 | 0.58 | True |
| 验证组C原点 | 54 | PREEXISTING_CHECK | JOINT | 4.20 | 4.00 | 1.51 | True |
| 验证组C原点 | 121 | PREEXISTING_CHECK | JOINT | 4.50 | 4.00 | 2.62 | True |
| 验证组C原点 | 195 | PREEXISTING_CHECK | JOINT | 5.23 | 4.42 | 1.74 | True |
| 验证组C原点 | 345 | PREEXISTING_CHECK | JOINT | 4.47 | 4.42 | 3.50 | True |
| 验证组C原点 | 363 | PREEXISTING_CHECK | JOINT | 4.88 | 4.42 | 5.10 | True |
| 验证组C亮区 | 38 | PREEXISTING_CHECK | JOINT | 4.35 | 4.00 | 0.58 | True |
| 验证组C亮区 | 54 | PREEXISTING_CHECK | JOINT | 4.20 | 4.00 | 1.51 | True |
| 验证组C亮区 | 121 | PREEXISTING_CHECK | JOINT | 4.50 | 4.00 | 2.62 | True |
| 验证组C亮区 | 195 | PREEXISTING_CHECK | JOINT | 4.59 | 4.00 | 2.93 | True |
| 验证组C亮区 | 232 | PREEXISTING_CHECK | JOINT | 4.46 | 4.00 | 0.71 | True |
| 验证组C亮区 | 345 | PREEXISTING_CHECK | JOINT | 4.58 | 4.00 | 3.50 | True |
| 验证组C亮区 | 363 | PREEXISTING_CHECK | JOINT | 4.48 | 4.00 | 5.03 | True |

## 开发组H左移与零回退

实际左移 150 px 后，历史 26 次测试（20 张图，含重复）保持名义参考位置 0 次。全 410 帧中，原缺口在裁后材料带内 0 帧；完成两端定位并准备好搜索的有 177 帧，其中与名义参考端点相同 0 帧。其余 233 帧在准备阶段返回空。两次都发布尖端的只有 11 帧。

保留左移后的横向范围和提示点，仅在离线回放中换回名义纵向材料带，410/410 帧恢复 V6.2 名义参考端点。第 78 帧材料带下界从 y=1372 变为 731，原参考缺口 (2643,780) 被裁出。名义点位下，扩大统计范围又使暗区分割门槛升至 250.74，轮廓延伸至 (2655,782)。位移测试恢复同一参考坐标与实际尖端识别正确是两项独立指标。

开发组H 410/410 帧全部分侧窗回退到零位移。63,960 次上侧、下侧或合并窗尝试中，63,933 次材料掩膜覆盖不足，另有 27 次窗口尺寸不足。

| 配准窗 | 支持率 <35% | 几何尺寸不足 | 低纹理 | 进入 NCC | 被采用 |
| --- | --- | --- | --- | --- | --- |
| up | 21311 | 9 | 0 | 0 | 0 |
| down | 21311 | 9 | 0 | 0 | 0 |
| single | 21311 | 9 | 0 | 0 | 0 |

在尺寸合格的 63,933 次尝试中，有效材料比例最大值为 0.000%，当前窗与参考窗灰度 ≥250 的像素占比中位数分别为 99.3% 和 100.0%。配准器先剔除饱和点，并对参考支持做 11×11 腐蚀。低纹理判定、±5 px 峰值搜索和 NCC 0.84 门限均未执行。这批图像无法据此估计实际位移是否超过 5 px。

开发组H第 252 帧误差 102.70 px。第 216、221 帧从严重提前变为门控拒绝，均计作漏检。 离线交叉回放只替换参考定位或门控组合（口门阈值与连续列门槛），两条对角线的状态、尖端和全路径已与各自正式输出核对。

| 参考定位 | 门控组合 | 18 帧 Joint | >100 px | 发布尖端 |
| --- | --- | --- | --- | --- |
| 6.1 | 6.1 | 9 | 2 | 16 |
| 6.1 | 6.2 | 8 | 1 | 13 |
| 6.2 | 6.1 | 3 | 1 | 6 |
| 6.2 | 6.2 | 3 | 1 | 6 |

[开发组H定位与门控逐帧交叉对照](../../output/experiments/v62_global_notch_r01/group_h_factorial_scores.csv)

[第 78 帧定位与裁带示意](../../output/experiments/v62_global_notch_r01/group_h_0078_reference_band.png) · [参考缺口对照，含仅替换纵向材料带](../../output/experiments/v62_global_notch_r01/group_h_reference_scan.csv) · [全 410 帧实际左移](../../output/experiments/v62_global_notch_r01/group_h_full_shift.csv) · [历史扰动及重复试次](../../output/experiments/v62_global_notch_r01/group_h_stress.csv) · [全部 NCC 窗、阈值与拒绝原因](../../output/experiments/v62_global_notch_r01/ncc_window_rejections.csv)

## 合成对照

负样本误报 1/468。P4_open 的原 8 次误报逐个配对，8 次转为拒绝。weak_material_bridge 通过 36/36。

| 合成工况 | 总数 | V6.1 通过 | V6.2 通过 | V6.2 误报 |
| --- | --- | --- | --- | --- |
| P1_lower | 36 | 34 | 34 | 0 |
| P1_upper | 36 | 33 | 33 | 0 |
| P1_weak_gap | 216 | 168 | 168 | 0 |
| P2_fade | 36 | 17 | 17 | 0 |
| P2_isolated | 36 | 36 | 36 | 0 |
| P3_oblique | 36 | 36 | 36 | 0 |
| P3_parallel | 36 | 36 | 36 | 0 |
| P4_open | 36 | 28 | 36 | 0 |
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
| mouth_glare_arc_only | 36 | 35 | 35 | 1 |
| mouth_thick_valley | 36 | 36 | 36 | 0 |
| two_rise_bridge | 36 | 36 | 36 | 0 |
| weak_material_bridge | 36 | 36 | 36 | 0 |
| weak_tail_attached | 36 | 36 | 36 | 0 |
| weak_tail_blank | 36 | 36 | 36 | 0 |

[1,404 次合成明细](../../output/experiments/v62_global_notch_r01/paired_probes.csv)

## 后续研发

开发组H应先让参考材料带覆盖原缺口，再比较局部和整带灰度统计对缺口右端的影响。对分侧配准，先在同批原图核查较远的未饱和材料区是否有稳定纹理；本次注册窗的支持率不足以评估放宽 NCC 或扩大搜索半径的收益。
