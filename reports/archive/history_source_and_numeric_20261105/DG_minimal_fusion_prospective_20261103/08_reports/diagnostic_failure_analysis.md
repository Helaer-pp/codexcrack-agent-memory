# 因果与历史异常分析

| family | frame_side_n | F_adds_support | C_adds_pixels | C_merges_components |
|---|---|---|---|---|
| gap | 360 | 268 | 258 | 213 |
| curve_static_tail | 360 | 306 | 240 | 189 |
| hole_motion | 360 | 262 | 168 | 69 |
| twin_true | 360 | 279 | 245 | 221 |
| twin_false | 360 | 279 | 245 | 221 |

C 的每个新增桥像素（ROI采样坐标）、前后组件数与端点均在 D_G_F_C_causal.csv；预注册首重复的中间矩阵保存在03_results/TEST/layers。第一处可证实的变化应按 DG→DFG→DFGC 的响应/组件/端点逐层核对，而不是笼统归因闭运算。D_pixels 是未经阈值化的非零差分面积，DG_pixels 是阈值+材料域后的面积，两者不应用作同阈值面积比较。

| group | frame_id | A_confirmed | A_arc_px | DG_evaluable | DG_confirmed | DG_arc_px | divergence_type | state | reason |
|---|---|---|---|---|---|---|---|---|---|
| ct2 | 6 | True | 441.9247651663204 | UNKNOWN | False | 318.39696961967 | INCONCLUSIVE | ABSTAIN | A_PATH_OUTSIDE_INDEPENDENT_ROI |
| ct2 | 18 | True | 440.34000473303627 | UNKNOWN | False | 317.15432893255075 | INCONCLUSIVE | ABSTAIN | A_PATH_OUTSIDE_INDEPENDENT_ROI |
| ct2 | 84 | True | 440.5734916806588 | UNKNOWN | False | 330.4680374315355 | INCONCLUSIVE | ABSTAIN | A_PATH_OUTSIDE_INDEPENDENT_ROI |
| group_x | 51 | False | N/A | UNKNOWN | False | N/A | INCONCLUSIVE | ABSTAIN | NO_INDEPENDENT_EVIDENCE |
| group_x | 473 | True | 1084.127439843421 | UNKNOWN | False | N/A | INCONCLUSIVE | ABSTAIN | A_PATH_OUTSIDE_INDEPENDENT_ROI |

排除组X473：沿 A 的原始路径逐点记录 reference/current 灰度、新变暗差和材料支持，见 key_A_path_evidence.csv。DG 若 UNKNOWN 或路径超出独立ROI，只能 ABSTAIN；不能由更短路径推出真实尖端。旧 F-WIDE 已覆盖 A 尾部但仍停在约310.255px，是已曝光历史证据，不能当本轮独立真值。无人工/物理GT，真实尖端仍 NOT_IDENTIFIABLE。排除组X51的 A 候选只画在研究材料，正式 A 视频无确认时仅原图。

CT2 6/18/84：保留原 refine-on 配置，不重定义127.21px配置差为真实误差；先前配置因果链只作为已曝光来源。本轮保存原图坐标/参考坐标证据、根部及独立配准状态，不用未知差分强行归责 A。

hole_motion 中锚点偏移是程序已知干预，参考边缘差分、Frangi增强及材料根部选择分别可通过 alignment.csv、causal.csv 和层矩阵复核。门控未通过时，不能因 F 响应较强就确认物理裂纹。
