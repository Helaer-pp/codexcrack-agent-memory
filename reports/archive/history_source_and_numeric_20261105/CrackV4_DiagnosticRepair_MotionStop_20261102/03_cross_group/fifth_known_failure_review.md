# 第五组已知故障复核（非新盲测）

| frame_id | tip_confirmed | full_length | current_darkline | reference | material | risks |
|---|---|---|---|---|---|---|
| 51 | False | False | FAIL | UNKNOWN | PASS | ["BODY_EVIDENCE_LOSS", "TIP_REGION_AMBIGUOUS", "REFERENCE_NOT_EVALUABLE", "PHOTOMETRY_LIMITED"] |
| 473 | True | True | FAIL | UNKNOWN | UNKNOWN | ["BODY_EVIDENCE_LOSS", "TIP_REGION_AMBIGUOUS", "REFERENCE_NOT_EVALUABLE", "MATERIAL_MOTION_NOT_EVALUABLE", "PHOTOMETRY_LIMITED"] |

该结果不参与阈值/规则开发。第51/473帧既往已观察，不标为独立全新盲测。保留A真实输出，没有根据诊断截断或补齐长度。物理误差仍N/A。
