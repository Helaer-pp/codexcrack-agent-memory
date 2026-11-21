# 排除组X frame_id=51

PASS_IDENTITY_ONLY；这是已知故障回归，并非完全盲测。

A tip_valid=False, length_valid=False, tip=None, length_px=None。正式图/视频严格使用这些值；frame51无尖端则原图，不画候选。

固定诊断类别：PHOTOMETRY_UNRELIABLE|BODY_EVIDENCE_DISAGREEMENT。证据断点 s=233.9768288529872 px；离A尾端=680.9325660208731 px；尾窗起点=890.9093948738603 px。这个断点不是物理尖端，不产生新的测量。

成像：PHOTOMETRY_UNRELIABLE；材料高截断比例=0.23336123623124858；噪声MAD=5.146721888394612。局部材料匹配：LOCAL_MATCHES_CONDITIONALLY_AVAILABLE，有效 6/24，heldout 3；残差={"n": 6, "P50": 1.1907890034954551, "P95": 1.4098915827154057, "P99": 1.426483461368942, "Max": 1.4306314310323263}，局部绝对误差上界 UNKNOWN。可评价=False，因此不能越过质量限制推断真实路径。

[全帧原图对比](../08_media/comparison/group_x/000051.png) · [原灰度剖面](../04_path_observability/diagnostics/group_x/profile_000051.png)
