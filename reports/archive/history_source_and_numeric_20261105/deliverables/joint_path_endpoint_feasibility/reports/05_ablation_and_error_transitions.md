# 完整时序消融与误伤

确认数仅为覆盖，不是精度。

| group | mode | current | tip | full | errors | real_precision |
| --- | --- | --- | --- | --- | --- | --- |
| group_a | M0_BASE_STABLE | 550 | 497 | 496 | 0 | N/A |
| group_a | M1_BASE_FAILED_RESEARCH | 550 | 497 | 496 | 0 | N/A |
| group_a | OFF_COMPAT | 550 | 497 | 496 | 0 | N/A |
| group_a | V3_REJECTED | 550 | 428 | 427 | 0 | N/A |
| group_a | M2_EVIDENCE_ONLY | 550 | 497 | 496 | 0 | N/A |
| group_a | M3_LLR_BG | 550 | 497 | 496 | 0 | N/A |
| group_a | M4_JOINT_K1 | 550 | 124 | 123 | 0 | N/A |
| group_a | M5_JOINT_K2 | 550 | 124 | 123 | 0 | N/A |
| group_a | M5_JOINT_K3 | 550 | 124 | 123 | 0 | N/A |
| group_a | ANCHOR_NO_REFINE | 550 | 497 | 497 | 0 | N/A |
| group_c | M0_BASE_STABLE | 561 | 543 | 543 | 0 | N/A |
| group_c | M1_BASE_FAILED_RESEARCH | 561 | 543 | 543 | 0 | N/A |
| group_c | OFF_COMPAT | 561 | 543 | 543 | 0 | N/A |
| group_c | V3_REJECTED | 561 | 448 | 448 | 0 | N/A |
| group_c | M2_EVIDENCE_ONLY | 561 | 543 | 543 | 0 | N/A |
| group_c | M3_LLR_BG | 561 | 541 | 541 | 0 | N/A |
| group_c | M4_JOINT_K1 | 561 | 360 | 360 | 0 | N/A |
| group_c | M5_JOINT_K2 | 561 | 360 | 360 | 0 | N/A |
| group_c | M5_JOINT_K3 | 561 | 360 | 360 | 0 | N/A |
| group_c | ANCHOR_NO_REFINE | 561 | 521 | 521 | 0 | N/A |
| ct2 | M0_BASE_STABLE | 467 | 403 | 403 | 0 | N/A |
| ct2 | M1_BASE_FAILED_RESEARCH | 467 | 456 | 456 | 0 | N/A |
| ct2 | OFF_COMPAT | 467 | 403 | 403 | 0 | N/A |
| ct2 | V3_REJECTED | 467 | 281 | 281 | 0 | N/A |
| ct2 | M2_EVIDENCE_ONLY | 467 | 403 | 403 | 0 | N/A |
| ct2 | M3_LLR_BG | 467 | 450 | 450 | 0 | N/A |
| ct2 | M4_JOINT_K1 | 467 | 284 | 284 | 0 | N/A |
| ct2 | M5_JOINT_K2 | 467 | 284 | 284 | 0 | N/A |
| ct2 | M5_JOINT_K3 | 467 | 284 | 284 | 0 | N/A |
| ct2 | ANCHOR_NO_REFINE | 467 | 383 | 383 | 0 | N/A |
| group_h | M0_BASE_STABLE | 409 | 345 | 344 | 0 | N/A |
| group_h | M1_BASE_FAILED_RESEARCH | 409 | 345 | 344 | 0 | N/A |
| group_h | OFF_COMPAT | 409 | 345 | 344 | 0 | N/A |
| group_h | V3_REJECTED | 409 | 295 | 294 | 0 | N/A |
| group_h | M2_EVIDENCE_ONLY | 409 | 345 | 344 | 0 | N/A |
| group_h | M3_LLR_BG | 409 | 361 | 356 | 0 | N/A |
| group_h | M4_JOINT_K1 | 409 | 0 | 0 | 0 | N/A |
| group_h | M5_JOINT_K2 | 409 | 0 | 0 | 0 | N/A |
| group_h | M5_JOINT_K3 | 409 | 0 | 0 | 0 | N/A |
| group_h | ANCHOR_NO_REFINE | 409 | 351 | 351 | 0 | N/A |

成对增减（GT类别一律N/A）：

| group | stable_full | joint_full | lost | gained | retained | lost_GT_correct | lost_GT_wrong | gain_GT_correct | gain_GT_wrong |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | 496 | 123 | 373 | 0 | 123 | N/A | N/A | N/A | N/A |
| group_c | 543 | 360 | 183 | 0 | 360 | N/A | N/A | N/A | N/A |
| ct2 | 403 | 284 | 150 | 31 | 253 | N/A | N/A | N/A | N/A |
| group_h | 344 | 0 | 344 | 0 | 0 | N/A | N/A | N/A | N/A |

新旧每帧差异见 data/error_transitions.csv；不能把lost称正确拒绝、gain称正确识别。合成真值病例：

| mode | cases | positive_correct_cases | wrong_confirmed_cases | positive_missed_cases |
| --- | --- | --- | --- | --- |
| M0_BASE_STABLE | 22 | 15 | 0 | 4 |
| M1_BASE_FAILED_RESEARCH | 22 | 18 | 0 | 1 |
| M3_LLR_BG | 22 | 15 | 0 | 4 |
| M4_JOINT_K1 | 22 | 12 | 1 | 7 |
| M5_JOINT_K2 | 22 | 12 | 1 | 7 |
| M5_JOINT_K3 | 22 | 12 | 1 | 7 |

H1–H3尚未通过：联合停止仍在gap12产生错误早停，并误拒绝某些原本可检的弯曲/已有参考裂纹。故依任务书顺序，M6分歧恢复、M7亚像素、M8新时序不进入本轮消融，不通过继续堆叠模块掩盖H3失败。两个未准入标志在API中明确拒绝，非静默空实现。
