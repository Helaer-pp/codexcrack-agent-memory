# 本轮最终结论与原因

工程交付已完成，算法判定 **NO_GO**，不替换生产 A/V1/V2。开发尖端10px命中 2/76，联合命中 2/76；已曝光验证分别 0/35、0/35。

[2647帧图册](galleries/index.html) · [六组视频，验证组置顶](videos/index.html) · [离线人工标签对比](offline_label_overlays/index.html) · [全部模式与基线](reports/DEVELOPMENT_REPORT.md) · [完整性](run_integrity.json) · [阶段审计](stage_diagnostics/STAGE_CAUSE_REPORT.md)

## 原因定位

| group | visible | raw_coverage80 | retained_coverage80 | finite_pool_good | chosen_good | GRAPH_ROUTE_OR_RANK_BUDGET_LOSS | STOP_OR_PUBLIC_AMBIGUITY | JOINT_SUCCESS | ROI_TIP_EXCLUDED | FINAL_PATH_RANK_LOSS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | 19 | 19 | 19 | 2 | 2 | 17 | 2 |  |  |  |
| ct2 | 20 | 20 | 20 | 4 | 4 | 16 | 4 |  |  |  |
| group_h | 18 | 18 | 18 | 10 | 10 | 8 | 8 | 2 |  |  |
| ct3 | 19 | 19 | 19 | 0 | 0 | 13 |  |  | 6 |  |
| group_c | 20 | 20 | 20 | 16 | 8 | 4 | 8 |  |  | 8 |
| three_point_bend | 15 | 15 | 15 | 1 | 0 | 14 |  |  |  | 1 |

开发组主要首败层为 ('GRAPH_ROUTE_OR_RANK_BUDGET_LOSS', 54)。原始峰/保留节点靠近人工路径，只证明附近存在图像证据，不证明它们已构成正确路径。图阶段包含邻接连接、前驱选择和有限池排名；本轮不能把这些因素全部归结为单一阈值。

### 包含关系去重的进一步定位

| group | visible | preselection_good_frames | kept_good_frames | containment_loss_without_good_keeper | frames_good_budget_dropped |
| --- | --- | --- | --- | --- | --- |
| group_a | 19 | 4 | 2 | 2 | 1 |
| ct2 | 20 | 6 | 4 | 2 | 0 |
| group_h | 18 | 16 | 10 | 2 | 5 |
| ct3 | 19 | 2 | 0 | 1 | 1 |
| group_c | 20 | 20 | 16 | 0 | 19 |
| three_point_bend | 15 | 2 | 1 | 1 | 1 |

[完整候选重放证据](containment_diagnostics/CONTAINMENT_CAUSE_REPORT.md)。排序前路线被保留不等于尖端正确，不能计为新增准确率。

## 为什么有大量不确定输出

| group | frames | TIP_UNCERTAIN | PATH_AMBIGUOUS | PROVISIONAL_TIP | stops | eligible_stops | material_adequate_stops | negative_adequate_stops | frames_no_eligible_stop |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | 551 | 485 | 66 |  | 611 | 0 | 606 | 0 | 551 |
| ct2 | 468 | 449 | 11 | 8 | 557 | 8 | 515 | 11 | 460 |
| group_h | 410 | 250 | 45 | 115 | 450 | 132 | 450 | 132 | 279 |
| ct3 | 136 | 65 | 71 |  | 173 | 0 | 67 | 0 | 136 |
| group_c | 562 | 376 | 186 |  | 838 | 0 | 658 | 0 | 562 |
| three_point_bend | 520 | 453 | 67 |  | 748 | 0 | 748 | 0 | 520 |

有材料可测不等于已有可靠负证据。停止条件不足既可能来自路径提前断裂、末端后仍有线，也可能来自纹理触发；不能把这种拒绝直接解释为算法更安全。

| role | visible | public_outputs | public_over100 | public_over500 | candidate_tips | candidate_over100 | candidate_over500 | last_observed_count | last_observed_over100 | last_observed_over500 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEVELOPMENT | 76 | 3 | 1 | 1 | 5 | 3 | 2 | 76 | 45 | 3 |
| EXPOSED_REGRESSION | 35 | 0 | 0 | 0 | 0 | 0 | 0 | 35 | 20 | 6 |

最后观测点的尾误差仅作路径诊断，不计为算法尖端；单列它是为了暴露拒绝输出背后的错误路径，不能混入公开端点准确率。

## 冻结规则下的补充噪点反例

| pixel_width | spacing_px | output_state | public_tip | observed | inferred | physical_identity |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 10 | NO_EVIDENCE | None | 0 | 0 | UNVERIFIED |
| 2 | 10 | PROVISIONAL_TIP | [111, 120] | 4 | 8 | UNVERIFIED |

该检查在规则冻结后补充，只用于诊断，没有据此调参。2px点链仍能产生暂定尖端，说明有限桥接和停止证据并不认证主裂纹身份；不能把上述合成样例当作真实FPR，真实FPR仍为N/A。

## 唯一下一步建议

下一轮只检验一项：把同一条路线的不同终止跨度保留为独立假设，不再仅因片段包含关系删除弱延伸路线；固定其余证据、连接边界、排名权重与停止规则。先验证候选保真是否恢复，不承诺这一项就能改善最终尖端，也不自动放行不确定结果。 本轮不自动启动下一轮。

中值3×3在合成1px暗线上谷深保留为0，轻高斯约0.667，因此统一默认RAW。参考合格帧数表示至少一个局部窗口通过纹理检查，不代表全ROI配准可信，详见reference_group_summary.csv。

## 参考不可信的具体门条件

| group | windows | SAME_IMAGE_NO_INCREMENT | LOW_CURRENT_TEXTURE | LOW_REFERENCE_TEXTURE | INSUFFICIENT_BRIGHT_MATERIAL | TRUSTED_TEXTURE_PROXY | NCC_BELOW_FROZEN_GATE | SMALL_WINDOW | PHOTOMETRIC_OFFSET_TOO_LARGE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | 16592 | 30 | 2876 | 3860 | 1164 | 1103 | 14386 | 62 |  |
| ct2 | 33696 | 72 | 936 | 1506 | 469 | 3268 | 29889 |  |  |
| group_h | 33620 | 82 | 23534 | 31626 | 410 | 1227 | 31918 |  |  |
| ct3 | 6528 | 48 |  |  |  | 1152 | 5328 |  |  |
| group_c | 37092 | 66 |  |  |  | 20236 | 16790 |  |  |
| three_point_bend | 59280 | 114 | 1040 | 1040 | 1983 | 7682 | 49923 |  | 268 |

一个窗口可以同时违反多个条件，因此失败条件数不可直接相加当窗口数。逐窗亮度比例与扩展warp有效性由保存的完整分辨率数组补算，全部复现原始可信判断；没有改门槛或重新选择配准。

约束保持：排除组X未使用；标签只比较不训练；验证组C/三点弯未调参且不是新盲测；CT3原始TXT缺失，历史CSV与每帧P核验一致，6个ROI外可见尖端保留分母；真实阴性FPR=N/A。基线是冻结结果与完整trace的校验回放，未重跑旧检测器。

完整复现入口：`research/grayref_simplified_evidence_support/grayref_simplified_full_delivery.ps1 -RunId NEW_UNIQUE_RUN -Workers 12`。主试验源码冻结后未变；辅助脚本只做只读核查、事后报告和视频，不回写推理。
