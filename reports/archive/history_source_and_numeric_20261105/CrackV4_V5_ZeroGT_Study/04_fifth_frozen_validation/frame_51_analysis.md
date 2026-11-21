# 第五组已曝光frame_id=51：冻结后研究复核

| mode | image | tip_confirmed | full_valid | tip | length_px | path_support | tail_support | terminal | status | Process_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 5284089129.bmp | False | False | None | None | 0.5757211538461539 | 0.875 | direction_ambiguous | tracking_incomplete | 36.122099991189316 |
| A2 | 5284089129.bmp | False | False | None | None | 0.9545454545454546 | 1.0 | joint_tip_uncertain | weak_candidate | 32.14219999790657 |
| COMPAT | 5284089129.bmp | False | False | None | None | 0.5757211538461539 | 0.875 | direction_ambiguous | tracking_incomplete | 43.24800000176765 |
| D | 5284089129.bmp | False | False | None | None | 0.0 | 0.0 | no_candidate | no_new_candidate | 34.553999998024665 |

原图与各版本叠加位于frames/frame_0051_raw.png及_A/_A2/_COMPAT/_D.png。正式path、背景/停止字段见results.jsonl；A2另含failed_joint局部证据。真实尖端GT不存在，不能说未确认等于找对，也不能说正式确认等于物理正确。最终保留A与COMPAT未变，历史问题不自动视为解决；D的任何不同均记NEXT_CYCLE_FINDING，不返调本轮。

本次 A/COMPAT 均因 `direction_ambiguous` 不确认；与历史“错误路径已确认”的版本应区分。A2 候选支持率0.955仍未通过 `joint_tip_uncertain`，说明候选线局部支持高不等于确定物理尖端。D 在参考变化分支未形成新候选，正式画面只显示原图。不能把这个单帧拒绝与全组D仅6帧完整确认分开，宣称过滤有效。
