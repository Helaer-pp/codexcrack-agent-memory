# 开发组H MT · V6.2 诊断

实际左移 150 px 后，历史 26 次测试（20 张图，含重复）保持名义参考位置 0 次。全 410 帧中，原缺口在裁后材料带内 0 帧；完成两端定位并准备好搜索的有 177 帧，其中与名义参考端点相同 0 帧。其余 233 帧在准备阶段返回空。两次都发布尖端的只有 11 帧。

保留左移后的横向范围和提示点，仅在离线回放中换回名义纵向材料带，410/410 帧恢复 V6.2 名义参考端点。第 78 帧材料带下界从 y=1372 变为 731，原参考缺口 (2643,780) 被裁出。名义点位下，扩大统计范围又使暗区分割门槛升至 250.74，轮廓延伸至 (2655,782)。位移测试恢复同一参考坐标与实际尖端识别正确是两项独立指标。

[第 78 帧定位与裁带示意](../../output/experiments/v62_global_notch_r01/group_h_0078_reference_band.png) · [参考缺口对照，含仅替换纵向材料带](../../output/experiments/v62_global_notch_r01/group_h_reference_scan.csv) · [全 410 帧实际左移](../../output/experiments/v62_global_notch_r01/group_h_full_shift.csv) · [历史扰动及重复试次](../../output/experiments/v62_global_notch_r01/group_h_stress.csv) · [全部 NCC 窗、阈值与拒绝原因](../../output/experiments/v62_global_notch_r01/ncc_window_rejections.csv)

开发组H 410/410 帧全部分侧窗回退到零位移。63,960 次上侧、下侧或合并窗尝试中，63,933 次材料掩膜覆盖不足，另有 27 次窗口尺寸不足。

在尺寸合格的 63,933 次尝试中，有效材料比例最大值为 0.000%，当前窗与参考窗灰度 ≥250 的像素占比中位数分别为 99.3% 和 100.0%。配准器先剔除饱和点，并对参考支持做 11×11 腐蚀。低纹理判定、±5 px 峰值搜索和 NCC 0.84 门限均未执行。这批图像无法据此估计实际位移是否超过 5 px。

| 配准窗 | 支持率 <35% | 几何尺寸不足 | 低纹理 | 进入 NCC | 被采用 |
| --- | --- | --- | --- | --- | --- |
| up | 21311 | 9 | 0 | 0 | 0 |
| down | 21311 | 9 | 0 | 0 | 0 |
| single | 21311 | 9 | 0 | 0 | 0 |

## 18 张可见标注

| 开发组H帧 | V6.1 Joint | V6.2 Joint | 误差 px | 路由 | 终止 |
| --- | --- | --- | --- | --- | --- |
| 41 | False | False | — | JOINT | EMPTY |
| 74 | True | False | — | JOINT | INSUFFICIENT_TOTAL |
| 78 | False | False | — | JOINT | EMPTY |
| 96 | True | False | — | JOINT | INSUFFICIENT_TOTAL |
| 115 | False | False | — | JOINT | EMPTY |
| 141 | False | False | — | JOINT | CONTOUR_DUAL_RUN_SHORT |
| 169 | True | False | 19.46 | JOINT | ACCEPTED_PEAK |
| 197 | True | True | 1.87 | JOINT | ACCEPTED_PEAK |
| 216 | False | False | — | JOINT | CONTOUR_DUAL_RUN_SHORT |
| 221 | False | False | — | JOINT | CONTOUR_DUAL_RUN_SHORT |
| 252 | False | False | 102.70 | JOINT | ACCEPTED_PEAK |
| 276 | True | True | 9.67 | JOINT | ACCEPTED_PEAK |
| 304 | True | True | 4.87 | JOINT | ACCEPTED_PEAK |
| 317 | True | False | — | JOINT | NO_REACHABLE_POSITIVE |
| 340 | False | False | — | JOINT | INSUFFICIENT_TOTAL |
| 377 | False | False | — | JOINT | CONTOUR_DUAL_RUN_SHORT |
| 397 | True | False | — | JOINT | INSUFFICIENT_TOTAL |
| 401 | True | False | 85.13 | JOINT | ACCEPTED_PEAK |

开发组H第 252 帧误差 102.70 px。第 216、221 帧从严重提前变为门控拒绝，均计作漏检。 离线交叉回放只替换参考定位或门控组合（口门阈值与连续列门槛），两条对角线的状态、尖端和全路径已与各自正式输出核对。

| 参考定位 | 门控组合 | 18 帧 Joint | >100 px | 发布尖端 |
| --- | --- | --- | --- | --- |
| 6.1 | 6.1 | 9 | 2 | 16 |
| 6.1 | 6.2 | 8 | 1 | 13 |
| 6.2 | 6.1 | 3 | 1 | 6 |
| 6.2 | 6.2 | 3 | 1 | 6 |

[开发组H定位与门控逐帧交叉对照](../../output/experiments/v62_global_notch_r01/group_h_factorial_scores.csv)

开发组H应先让参考材料带覆盖原缺口，再比较局部和整带灰度统计对缺口右端的影响。对分侧配准，先在同批原图核查较远的未饱和材料区是否有稳定纹理；本次注册窗的支持率不足以评估放宽 NCC 或扩大搜索半径的收益。

[410 帧参考、结果与差分视频](../../output/experiments/v62_global_notch_r01/difference_views/group_h.mp4)
