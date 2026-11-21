# 精度与输出一致性报告

`tip_ground_truth_available=false`。四组真实裂纹尖端MAE/P95、路径弧长误差、实际误报率/漏报率均为 **N/A（缺少独立真值）**。外部P1/P2只是逐帧几何输入，不是裂纹标注。未将冻结结果写回人工真值。

## 实测双点相对几何残差

| 数据组 | 模式 | 有效变换帧 | P50 px | P90 px | P95 px | P99 px | Max px |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | AUTO_NEW_SHADOW | 550 | 3.500 | 7.260 | 7.744 | 8.146 | 15.026 |
| 开发组A | ANCHOR_NEW_SHADOW | 550 | 2.387 | 3.345 | 3.528 | 4.790 | 5.896 |
| 开发组A | ANCHOR_OPT | 550 | 2.387 | 3.345 | 3.528 | 4.790 | 5.896 |
| 开发组A | ANCHOR_NO_REFINE | 550 | 1.945 | 3.004 | 3.243 | 3.485 | 4.449 |
| 验证组C | AUTO_NEW_SHADOW | 561 | 2.017 | 2.451 | 2.526 | 2.657 | 2.754 |
| 验证组C | ANCHOR_NEW_SHADOW | 561 | 2.431 | 3.092 | 3.203 | 3.379 | 3.601 |
| 验证组C | ANCHOR_OPT | 561 | 2.431 | 3.092 | 3.203 | 3.379 | 3.601 |
| 验证组C | ANCHOR_NO_REFINE | 561 | 1.837 | 2.306 | 2.370 | 2.486 | 2.578 |
| CT2 | AUTO_NEW_SHADOW | 467 | 6.566 | 8.582 | 9.169 | 9.782 | 20.320 |
| CT2 | ANCHOR_NEW_SHADOW | 467 | 6.106 | 8.445 | 9.145 | 9.976 | 12.932 |
| CT2 | ANCHOR_OPT | 467 | 6.106 | 8.445 | 9.145 | 9.976 | 12.932 |
| CT2 | ANCHOR_NO_REFINE | 467 | 1.654 | 3.251 | 3.527 | 3.800 | 6.798 |
| 开发组H MT | AUTO_NEW_SHADOW | 409 | 3.115 | 65.822 | 66.409 | 66.647 | 66.848 |
| 开发组H MT | ANCHOR_NEW_SHADOW | 409 | 2.703 | 3.149 | 3.406 | 4.344 | 4.811 |
| 开发组H MT | ANCHOR_OPT | 409 | 2.703 | 3.149 | 3.406 | 4.344 | 4.811 |
| 开发组H MT | ANCHOR_NO_REFINE | 409 | 0.303 | 0.694 | 0.898 | 1.687 | 1.839 |

大残差复核阈值取各组 AUTO_NEW_SHADOW 的组内P95，严格大于者入选，属于分布抽样标准而非通用合格界限。

| 数据组 | 实测点有效率 | 几何复核阈值 px | 超该阈值帧数 | 峰值点残差 px |
| --- | --- | --- | --- | --- |
| 开发组A | 100% | 7.744 | 28 | 15.026 |
| 验证组C | 100% | 2.526 | 28 | 2.754 |
| CT2 | 100% | 9.169 | 24 | 20.320 |
| 开发组H MT | 100% | 66.409 | 21 | 66.848 |

## 全时序确认覆盖

| 数据组 | 模式 | 当前帧 | 尖端确认 | 完整长度有效 | 错误 | 未确认且非错误 | 首确认 frame_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | AUTO_BASE | 550 | 501 | 497 | 0 | 49 | 33 |
| 开发组A | AUTO_NEW_SHADOW | 550 | 501 | 497 | 0 | 49 | 33 |
| 开发组A | ANCHOR_NEW_SHADOW | 550 | 497 | 496 | 0 | 53 | 49 |
| 开发组A | ANCHOR_NEW_VERIFIED | 550 | 441 | 439 | 0 | 109 | 15 |
| 开发组A | ANCHOR_OPT | 550 | 497 | 496 | 0 | 53 | 49 |
| 验证组C | AUTO_BASE | 561 | 546 | 546 | 0 | 15 | 15 |
| 验证组C | AUTO_NEW_SHADOW | 561 | 546 | 546 | 0 | 15 | 15 |
| 验证组C | ANCHOR_NEW_SHADOW | 561 | 543 | 543 | 0 | 18 | 18 |
| 验证组C | ANCHOR_NEW_VERIFIED | 561 | 482 | 482 | 0 | 79 | 14 |
| 验证组C | ANCHOR_OPT | 561 | 543 | 543 | 0 | 18 | 18 |
| CT2 | AUTO_BASE | 467 | 373 | 373 | 23 | 71 | 1 |
| CT2 | AUTO_NEW_SHADOW | 467 | 396 | 396 | 0 | 71 | 1 |
| CT2 | ANCHOR_NEW_SHADOW | 467 | 403 | 403 | 0 | 64 | 1 |
| CT2 | ANCHOR_NEW_VERIFIED | 467 | 257 | 257 | 0 | 210 | 3 |
| CT2 | ANCHOR_OPT | 467 | 403 | 403 | 0 | 64 | 1 |
| 开发组H MT | AUTO_BASE | 409 | 290 | 275 | 2 | 117 | 43 |
| 开发组H MT | AUTO_NEW_SHADOW | 409 | 292 | 276 | 0 | 117 | 43 |
| 开发组H MT | ANCHOR_NEW_SHADOW | 409 | 345 | 344 | 0 | 64 | 42 |
| 开发组H MT | ANCHOR_NEW_VERIFIED | 409 | 248 | 247 | 0 | 161 | 44 |
| 开发组H MT | ANCHOR_OPT | 409 | 345 | 344 | 0 | 64 | 42 |

分母仅为1987张当前帧，4张参考帧另存；frame_id从0开始，参考帧0。未确认包括no_seed/no_candidate/terminal_uncertain等，不等于已知漏检。Verified的历史与Shadow独立；不能用逐帧离线阈值筛选冒充闭环。

## 配对差异（共同有效帧）

| 组别 | 对照 | 尖端差P50 px | 尖端差P95 px | 尖端差Max px | 长度绝对差P95 px | 失去确认 | 新增确认 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | AUTO_NEW_SHADOW__ANCHOR_NEW_SHADOW | 0.458 | 5.204 | 31.723 | 5.651 | 5 | 1 |
| 开发组A | ANCHOR_NEW_SHADOW__ANCHOR_OPT | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 |
| 开发组A | ANCHOR_NEW_SHADOW__ANCHOR_NEW_VERIFIED | 0.000 | 0.000 | 0.000 | 0.000 | 58 | 2 |
| 开发组A | AUTO_NEW_SHADOW__AUTO_OPT | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 |
| 开发组A | ANCHOR_NO_REFINE__ANCHOR_OPT | 0.426 | 4.344 | 16.397 | 5.041 | 1 | 1 |
| 验证组C | AUTO_NEW_SHADOW__ANCHOR_NEW_SHADOW | 0.304 | 2.575 | 17.945 | 2.519 | 4 | 1 |
| 验证组C | ANCHOR_NEW_SHADOW__ANCHOR_OPT | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 |
| 验证组C | ANCHOR_NEW_SHADOW__ANCHOR_NEW_VERIFIED | 0.000 | 0.000 | 0.000 | 0.000 | 62 | 1 |
| 验证组C | AUTO_NEW_SHADOW__AUTO_OPT | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 |
| 验证组C | ANCHOR_NO_REFINE__ANCHOR_OPT | 0.500 | 23.089 | 57.404 | 21.710 | 0 | 22 |
| CT2 | AUTO_NEW_SHADOW__ANCHOR_NEW_SHADOW | 0.737 | 10.193 | 92.908 | 10.643 | 9 | 16 |
| CT2 | ANCHOR_NEW_SHADOW__ANCHOR_OPT | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 |
| CT2 | ANCHOR_NEW_SHADOW__ANCHOR_NEW_VERIFIED | 0.000 | 0.000 | 0.000 | 0.000 | 146 | 0 |
| CT2 | AUTO_NEW_SHADOW__AUTO_OPT | 0.000 | 3.323 | 11.482 | 4.852 | 0 | 1 |
| CT2 | ANCHOR_NO_REFINE__ANCHOR_OPT | 1.502 | 127.214 | 133.902 | 129.758 | 16 | 36 |
| 开发组H MT | AUTO_NEW_SHADOW__ANCHOR_NEW_SHADOW | 0.245 | 4.081 | 46.060 | 5.098 | 1 | 54 |
| 开发组H MT | ANCHOR_NEW_SHADOW__ANCHOR_OPT | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 |
| 开发组H MT | ANCHOR_NEW_SHADOW__ANCHOR_NEW_VERIFIED | 0.000 | 0.000 | 0.000 | 0.000 | 97 | 0 |
| 开发组H MT | AUTO_NEW_SHADOW__AUTO_OPT | 0.000 | 0.000 | 18.612 | 0.000 | 3 | 16 |
| 开发组H MT | ANCHOR_NO_REFINE__ANCHOR_OPT | 0.426 | 5.596 | 57.099 | 6.855 | 8 | 2 |

这些是两个自动输出间的一致性差异，不是准确率。完整有符号长度差、状态矩阵、所有重大差异及对应审计图片路径见 comparisons。

## Verified拒绝原因

### 开发组A

| 审计原因 | 帧数 |
| --- | --- |
| terminal_supported | 448 |
| no_candidate | 49 |
| possible_forward_continuation | 47 |
| weak_terminal_support | 6 |

### 验证组C

| 审计原因 | 帧数 |
| --- | --- |
| terminal_supported | 483 |
| possible_forward_continuation | 61 |
| no_candidate | 15 |
| weak_terminal_support | 2 |

### CT2

| 审计原因 | 帧数 |
| --- | --- |
| terminal_supported | 301 |
| possible_forward_continuation | 92 |
| gap_unresolved | 64 |
| weak_terminal_support | 8 |
| path_quality_uncertain | 2 |

### 开发组H MT

| 审计原因 | 帧数 |
| --- | --- |
| terminal_supported | 268 |
| possible_forward_continuation | 69 |
| no_candidate | 46 |
| gap_unresolved | 16 |
| weak_terminal_support | 10 |

## 独立合成场景

| flags | 提供当前双点 | 确认 | 合成尖端误差 px | 当前状态 |
| --- | --- | --- | --- | --- |
| 244 | False | True | 360.025 | weak_candidate |
| 1268 | False | True | 3.609 | main_segment_detected |
| 1524 | False | True | 3.609 | main_segment_detected |
| 3572 | False | True | 3.609 | main_segment_detected |
| 3572 | True | True | 3.609 | main_segment_detected |

| 合成场景 | 模式 | 确认/5 | 合成尖端误差P50 px | Max px |
| --- | --- | --- | --- | --- |
| boundary | geometry_only_shadow | 0 | N/A | N/A |
| boundary | anchor_opt_shadow | 0 | N/A | N/A |
| boundary | anchor_opt_verified | 0 | N/A | N/A |
| clean | geometry_only_shadow | 0 | N/A | N/A |
| clean | anchor_opt_shadow | 0 | N/A | N/A |
| clean | anchor_opt_verified | 0 | N/A | N/A |
| exposure_jump | geometry_only_shadow | 5 | 2.613 | 2.613 |
| exposure_jump | anchor_opt_shadow | 5 | 2.613 | 2.613 |
| exposure_jump | anchor_opt_verified | 5 | 2.613 | 2.613 |
| fast_growth_repeat_skip | geometry_only_shadow | 5 | 2.666 | 3.359 |
| fast_growth_repeat_skip | anchor_opt_shadow | 5 | 2.666 | 3.359 |
| fast_growth_repeat_skip | anchor_opt_verified | 5 | 2.666 | 3.359 |
| missing_evidence | geometry_only_shadow | 0 | N/A | N/A |
| missing_evidence | anchor_opt_shadow | 0 | N/A | N/A |
| missing_evidence | anchor_opt_verified | 0 | N/A | N/A |
| occluded_tail | geometry_only_shadow | 5 | 50.508 | 50.508 |
| occluded_tail | anchor_opt_shadow | 0 | N/A | N/A |
| occluded_tail | anchor_opt_verified | 0 | N/A | N/A |
| occlusion_restore | geometry_only_shadow | 5 | 2.613 | 50.508 |
| occlusion_restore | anchor_opt_shadow | 3 | 2.613 | 2.613 |
| occlusion_restore | anchor_opt_verified | 3 | 2.613 | 2.613 |
| opening | geometry_only_shadow | 5 | 2.613 | 2.613 |
| opening | anchor_opt_shadow | 5 | 2.613 | 2.613 |
| opening | anchor_opt_verified | 5 | 2.613 | 2.613 |
| partial_texture_erasure | geometry_only_shadow | 5 | 2.663 | 2.663 |
| partial_texture_erasure | anchor_opt_shadow | 5 | 2.663 | 2.663 |
| partial_texture_erasure | anchor_opt_verified | 5 | 2.663 | 2.663 |
| precracked | geometry_only_shadow | 5 | 3.480 | 3.480 |
| precracked | anchor_opt_shadow | 5 | 3.480 | 3.480 |
| precracked | anchor_opt_verified | 5 | 3.480 | 3.480 |
| rotation | geometry_only_shadow | 5 | 2.601 | 2.601 |
| rotation | anchor_opt_shadow | 5 | 2.601 | 2.601 |
| rotation | anchor_opt_verified | 5 | 2.601 | 2.601 |
| shadow_entrance | geometry_only_shadow | 5 | 2.626 | 2.626 |
| shadow_entrance | anchor_opt_shadow | 5 | 2.626 | 2.626 |
| shadow_entrance | anchor_opt_verified | 5 | 2.626 | 2.626 |
| shadow_middle | geometry_only_shadow | 5 | 2.801 | 2.801 |
| shadow_middle | anchor_opt_shadow | 5 | 2.801 | 2.801 |
| shadow_middle | anchor_opt_verified | 5 | 2.801 | 2.801 |
| shadow_tail | geometry_only_shadow | 5 | 2.662 | 2.662 |
| shadow_tail | anchor_opt_shadow | 5 | 2.662 | 2.662 |
| shadow_tail | anchor_opt_verified | 5 | 2.662 | 2.662 |
| shorter_visible_crack | geometry_only_shadow | 5 | 3.662 | 3.662 |
| shorter_visible_crack | anchor_opt_shadow | 5 | 3.662 | 3.662 |
| shorter_visible_crack | anchor_opt_verified | 5 | 3.662 | 3.662 |
| strong | geometry_only_shadow | 5 | 2.613 | 2.613 |
| strong | anchor_opt_shadow | 5 | 2.613 | 2.613 |
| strong | anchor_opt_verified | 5 | 2.613 | 2.613 |
| temporary_defocus | geometry_only_shadow | 5 | 2.613 | 4.629 |
| temporary_defocus | anchor_opt_shadow | 5 | 2.613 | 4.629 |
| temporary_defocus | anchor_opt_verified | 5 | 2.613 | 4.629 |
| translation | geometry_only_shadow | 5 | 2.613 | 2.613 |
| translation | anchor_opt_shadow | 5 | 2.613 | 2.613 |
| translation | anchor_opt_verified | 5 | 2.613 | 2.613 |
| weak | geometry_only_shadow | 3 | 0.951 | 0.951 |
| weak | anchor_opt_shadow | 3 | 0.951 | 0.951 |
| weak | anchor_opt_verified | 5 | 0.951 | 0.951 |
| weak_registration_texture | geometry_only_shadow | 5 | 3.645 | 3.645 |
| weak_registration_texture | anchor_opt_shadow | 5 | 3.645 | 3.645 |
| weak_registration_texture | anchor_opt_verified | 5 | 3.645 | 3.645 |

已知遮挡被拒绝、恢复后再次确认、当前可见裂纹缩短仍允许确认；完整序列和路径误差另见 synthetic_next.json。合成随机种子42，和真实试验分布不同，不与真实精度合并。

## 实测点局部鲁棒性消融

固定种子20261028，12个真实源帧（四组各早中晚），每种配置240个局部扰动用例、每用例独立初始化并重复观测3次；flags244与3572共480个用例。尖端/长度确认或像素输出差异共0项。这是局部鲁棒性/一致性检查，不是疲劳时序检出延迟或真实精度；不与完整闭环结果混算。

CT2实测点frame_id=23在当前clean参考设置下，未扰动控制没有确认尖端，因此新的尖端代理误差留空，不能照搬旧配置约278.04px并声称本轮改善。控制路径采样中约89.9%像素原灰度>=230，中值238，加25后中值255。增益与饱和分开验证，信息丢失可由原像素直接检查。双方同时加25时仍有弱候选被形式确认，局部失效保护未覆盖所有这种情况；这些是待标注/进一步处理的失败边界，不能视为过曝已解决。详见ct2_photometric_causality.json和keyframes/ct2_exposure_information_loss.png。

## 待人工标注

共 720 个真实帧样例，787 个重大配对差异项。模板所有真实tip/root/length字段留空，review_status=pending。优先覆盖原32帧、几何分布尾部、Shadow/Verified分歧以及各组早中晚阶段。keyframes/review为对照图，人工应独立查看原图以减少检测叠加诱导。schema.json说明长度真值必须来自独立中心线；只有尖端时长度留空。
