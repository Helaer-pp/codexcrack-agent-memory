# Pre-Registered Ablation Protocol (`UCTIP-60Q-v1.0`)

All ablation arms share identical hyper-parameters, budgets, and evaluation denominators ($N$).

## 1. Single-Arm Ablations

| Arm Name | Disabled Component | Control Conditions |
|---|---|---|
| `FULL` | None | Default primary algorithm |
| `-FIXED_REF` | Fixed reference difference evidence | `fixed_diff_weight = 0.0`. Reference geometric initialization remains active. |
| `-PREV_REF` | Preceding actual frame difference evidence | `prev_diff_weight = 0.0`. Sequential tracking history remains active. |
| `-TRACKING` | Temporal history & track hysteresis | `history_hysteresis_bonus = 0.0`, `max_lost_frames = 0`. |
| `-GAP` | Inferred gap bridging | `max_inferred_gap_px = 0.0`. Only direct contiguous segments are linked. |
| `-DYNAMIC_ROI` | Forward scout & segmented ROI expansion | `max_expansions_per_frame = 0`. Static initial working ROI. |
| `-MULTITRACK` | Multi-branch concurrent management | `max_candidate_paths = 1`, `branch_split_dist_min_px = 9999.0`. |
| `-OPENING` | P1/P2 opening proxy reinforcement | Opening bonus disabled in scoring. Anchor geometry remains active. |

## 2. Pre-Registered Combinational Ablations

| Arm Name | Combined Components | Research Rationale |
|---|---|---|
| `-FIXED_REF -PREV_REF` | Both reference difference channels disabled | Isolates pure single-image RAW dark valley capability. |
| `-TRACKING -MULTITRACK` | Temporal hysteresis and multi-branch tracking disabled | Evaluates single-frame, single-hypothesis tracking stability. |
| `-GAP -DYNAMIC_ROI` | Gap bridging and ROI expansion disabled | Evaluates spatial search space and fracture connectivity constraints. |
