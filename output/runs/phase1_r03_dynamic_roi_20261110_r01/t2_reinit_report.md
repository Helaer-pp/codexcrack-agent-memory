# T2-A: safety-gated pilot, INCOMPLETE

Seven measured continuous R02 windows: GROUP_A252, group_c80, CT2/group_h/group_x120 each, three-point-bend160, CT3 full136. Four R02 failing initial variants replayed independently (group_c single P1 +5% x; CT2 common +2% x; group_h/group_x common +10% y). Initial points are copied exactly from R02 t2_variants.csv; each variant gets its own detector and state, reference image and current anchor trajectory unchanged. 988 distinct group-frames, 1428 initialization/frame cases. All are exposed evidence; group_x historical-only and three-point-bend validation-only, no tuning.

The full 16-variant matrix, added symmetric 5% sweep and non-control pairwise matrix are NOT COMPLETE. Gate2 failed before A3/A4 creation. This CSV explicitly says T2_A_PILOT_INCOMPLETE; it must not be used as full acceptance. T2-B-real is BLOCKED by missing real external tracker trajectories. No synthetic anchor sequence is relabeled real.

Statistics compare valid observed pairs only; predicted/fallback never shrink reported jitter. C0/Cv/Cpair and state mismatches are separate from complete-length mismatches. GROUP_A one observed control frame is INSUFFICIENT_OBSERVED_SUPPORT. Partial A2 coverage reduction is not an improvement.

| group | dataset_id | variant_id | N | C0 | Cv | Cpair | P95 | max | tip_state_mismatches | length_state_mismatches |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A0_R02 | group_c | p1_plus_5pct_x | 80 | 50 | 50 | 50 | 0.0000 | 6.0828 | 0 | 27 |
| A1_SHADOW | group_c | p1_plus_5pct_x | 80 | 50 | 50 | 50 | 0.0000 | 6.0828 | 0 | 27 |
| A2_STATE_ONLY | group_c | p1_plus_5pct_x | 80 | 1 | 1 | 1 | 0.0000 | 0.0000 | 0 | 27 |
| A0_R02 | ct2 | shift_x_plus_2pct | 120 | 110 | 107 | 106 | 112.7636 | 190.9188 | 5 | 4 |
| A1_SHADOW | ct2 | shift_x_plus_2pct | 120 | 110 | 107 | 106 | 112.7636 | 190.9188 | 5 | 4 |
| A2_STATE_ONLY | ct2 | shift_x_plus_2pct | 120 | 16 | 17 | 14 | 0.0000 | 0.0000 | 5 | 4 |
| A0_R02 | group_h | shift_y_plus_10pct | 120 | 114 | 63 | 58 | 1194.0617 | 1347.0935 | 61 | 2 |
| A1_SHADOW | group_h | shift_y_plus_10pct | 120 | 114 | 63 | 58 | 1194.0617 | 1347.0935 | 61 | 2 |
| A2_STATE_ONLY | group_h | shift_y_plus_10pct | 120 | 72 | 3 | 3 | 626.0966 | 626.0966 | 69 | 2 |
| A0_R02 | group_x | shift_y_plus_10pct | 120 | 120 | 120 | 120 | 296.0017 | 298.7189 | 0 | 0 |
| A1_SHADOW | group_x | shift_y_plus_10pct | 120 | 120 | 120 | 120 | 296.0017 | 298.7189 | 0 | 0 |
| A2_STATE_ONLY | group_x | shift_y_plus_10pct | 120 | 120 | 120 | 120 | 296.0017 | 298.7189 | 0 | 0 |