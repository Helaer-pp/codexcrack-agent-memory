# Controlled ablation / STOP after Gate 2

A0_R02: same production source rebuilt. A1_SHADOW: same source plus read-only observer and state proposals. A2_STATE_ONLY: independent state instance consumes the same A1 frame; output semantics are evaluated offline/native-sidecar, no ROI feedback. A3_DYNAMIC_ROI and A4_DYNAMIC_ROI_RECOVERY: BLOCKED, neither compiled nor run. No dynamic-ROI improvement is established.

1428 case-frames: baseline mismatch 0, raw shadow mismatch 0, raw mutation 0, independent-state difference 0. Raw JSON comparisons include paths/coordinates/status/length and exclude only clocks. Gate0 comparison against R02 checks stored confirmed tip and raw status, not an unavailable complete R02 path archive.

First-output and first-substantive divergences are in first_divergence_r03.csv. Adjacent real frames and complete paths/transforms are in first_divergence/. Geometry/ROI diverges from initialization; same image SHA and current anchors are held fixed. Different reference templates, baseline masks, tip transforms and search windows may co-vary. This is an initialization intervention, NOT an isolated proof that ROI clipping alone causes the error. No ROI-swap/motion-swap counterfactual was performed. Stale main-path audit scores are not independent ROI-path quality measurements.

Fault safety: 15/16 pass; failure coherent_wrong_first_lock. Fault evidence is injected after candidate detection, not an image-level synthetic accuracy benchmark. The known distractor label stays in the harness; runtime sees shifted self-consistent path/terminal flags and accepts. This proves a missing guard in this candidate protocol, not the physical identity of any real-image tip. The next closed-loop step is prohibited by the requested Gate2 rule.

| dataset_id | variant_id | N | A0_confirmed | A2_confirmed | Cpair | removed_confirmation | observed_coordinate_changes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | measured | 252 | 1 | 1 | 1 | 0 | 0 |
| group_c | measured | 80 | 50 | 1 | 1 | 49 | 0 |
| group_c | p1_plus_5pct_x | 80 | 50 | 1 | 1 | 49 | 0 |
| ct2 | measured | 120 | 110 | 16 | 16 | 94 | 0 |
| ct2 | shift_x_plus_2pct | 120 | 107 | 17 | 17 | 90 | 0 |
| group_h | measured | 120 | 114 | 72 | 72 | 42 | 0 |
| group_h | shift_y_plus_10pct | 120 | 63 | 3 | 3 | 60 | 0 |
| group_x | measured | 120 | 120 | 120 | 120 | 0 | 0 |
| group_x | shift_y_plus_10pct | 120 | 120 | 120 | 120 | 0 | 0 |
| three_point_bend | measured | 160 | 160 | 160 | 160 | 0 | 0 |
| ct3 | measured | 136 | 124 | 117 | 117 | 7 | 0 |