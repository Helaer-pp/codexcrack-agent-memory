# 排除组X frame_id=473

PASS_IDENTITY_ONLY；这是已知故障回归，并非完全盲测。

A tip_valid=True, length_valid=True, tip=[2344.05, 2409.42], length_px=1084.13。正式图/视频严格使用这些值；frame51无尖端则原图，不画候选。

固定诊断类别：PHOTOMETRY_UNRELIABLE|REGISTRATION_UNRELIABLE|BODY_EVIDENCE_DISAGREEMENT。证据断点 s=160.8705233316044 px；离A尾端=923.2569165118165 px；尾窗起点=1048.127439843421 px。这个断点不是物理尖端，不产生新的测量。

成像：PHOTOMETRY_UNRELIABLE；材料高截断比例=0.23576991034618153；噪声MAD=5.23192433794293。局部材料匹配：REGISTRATION_UNRELIABLE，有效 6/24，heldout 3；残差={"n": 6, "P50": 4.763817833544701, "P95": 5.033976731371183, "P99": 5.058139599510815, "Max": 5.064180316545723}，局部绝对误差上界 UNKNOWN。可评价=False，因此不能越过质量限制推断真实路径。

[全帧原图对比](../08_media/comparison/group_x/000473.png) · [原灰度剖面](../04_path_observability/diagnostics/group_x/profile_000473.png)
