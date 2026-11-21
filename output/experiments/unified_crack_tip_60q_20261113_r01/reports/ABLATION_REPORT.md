# 开发组预注册消融

11模式×1071帧，正式主结果固定FULL。两组合计34张可见GT，按组19/15固定分母，不以拒绝率降低冒称准确率提高。所有模式同一配置和预算，历史状态独立，公共图像证据只读。

| group | arm | visible | valid | hit10 | over100 | oracle_hit10 | full_sequence_budget |
|---|---|---|---|---|---|---|---|
| group_a | FULL | 19 | 0 | 0 | 0 | 7 | 551 |
| group_a | NO_FIXED | 19 | 0 | 0 | 0 | 7 | 551 |
| group_a | NO_PREV | 19 | 0 | 0 | 0 | 7 | 551 |
| group_a | NO_TRACKING | 19 | 0 | 0 | 0 | 8 | 546 |
| group_a | NO_GAP | 19 | 0 | 0 | 0 | 3 | 550 |
| group_a | NO_DYNAMIC_ROI | 19 | 0 | 0 | 0 | 7 | 551 |
| group_a | NO_MULTITRACK | 19 | 0 | 0 | 0 | 9 | 549 |
| group_a | NO_OPENING | 19 | 0 | 0 | 0 | 7 | 551 |
| group_a | NO_BOTH_REF | 19 | 0 | 0 | 0 | 7 | 551 |
| group_a | NO_TRACK_MULTI | 19 | 0 | 0 | 0 | 8 | 546 |
| group_a | NO_GAP_ROI | 19 | 0 | 0 | 0 | 3 | 550 |
| three_point_bend | FULL | 15 | 11 | 3 | 2 | 14 | 93 |
| three_point_bend | NO_FIXED | 15 | 13 | 3 | 2 | 14 | 4 |
| three_point_bend | NO_PREV | 15 | 12 | 3 | 2 | 14 | 69 |
| three_point_bend | NO_TRACKING | 15 | 14 | 3 | 0 | 14 | 0 |
| three_point_bend | NO_GAP | 15 | 1 | 0 | 0 | 14 | 509 |
| three_point_bend | NO_DYNAMIC_ROI | 15 | 11 | 3 | 2 | 14 | 93 |
| three_point_bend | NO_MULTITRACK | 15 | 15 | 0 | 11 | 14 | 0 |
| three_point_bend | NO_OPENING | 15 | 11 | 3 | 2 | 14 | 93 |
| three_point_bend | NO_BOTH_REF | 15 | 14 | 4 | 0 | 14 | 0 |
| three_point_bend | NO_TRACK_MULTI | 15 | 15 | 0 | 11 | 14 | 0 |
| three_point_bend | NO_GAP_ROI | 15 | 1 | 0 | 0 | 14 | 509 |


| group | arm | FULL_minus_arm_hit10 | FULL_minus_arm_valid | FULL_minus_arm_over100 | full_only_frames | arm_only_frames |
|---|---|---|---|---|---|---|
| group_a | NO_FIXED | 0 | 0 | 0 |  |  |
| group_a | NO_PREV | 0 | 0 | 0 |  |  |
| group_a | NO_TRACKING | 0 | 0 | 0 |  |  |
| group_a | NO_GAP | 0 | 0 | 0 |  |  |
| group_a | NO_DYNAMIC_ROI | 0 | 0 | 0 |  |  |
| group_a | NO_MULTITRACK | 0 | 0 | 0 |  |  |
| group_a | NO_OPENING | 0 | 0 | 0 |  |  |
| group_a | NO_BOTH_REF | 0 | 0 | 0 |  |  |
| group_a | NO_TRACK_MULTI | 0 | 0 | 0 |  |  |
| group_a | NO_GAP_ROI | 0 | 0 | 0 |  |  |
| three_point_bend | NO_FIXED | 0 | -2 | 0 |  |  |
| three_point_bend | NO_PREV | 0 | -1 | 0 |  |  |
| three_point_bend | NO_TRACKING | 0 | -3 | 2 |  |  |
| three_point_bend | NO_GAP | 3 | 10 | 2 | 347,381,435 |  |
| three_point_bend | NO_DYNAMIC_ROI | 0 | 0 | 0 |  |  |
| three_point_bend | NO_MULTITRACK | 3 | -4 | -9 | 347,381,435 |  |
| three_point_bend | NO_OPENING | 0 | 0 | 0 |  |  |
| three_point_bend | NO_BOTH_REF | -1 | -3 | 2 |  | 306 |
| three_point_bend | NO_TRACK_MULTI | 3 | -4 | -9 | 347,381,435 |  |
| three_point_bend | NO_GAP_ROI | 3 | 10 | 2 | 347,381,435 |  |

固定参考关闭仅移除变化证据，初始缺口几何保留；NO_TRACKING仍使用实际前一帧；NO_MULTITRACK确实损失其他分支覆盖。开口仅用于不确定候选的弱平局信息，因此正式指标零变化不证明开口物理信息无效，只说明当前集成不能贡献正式结果。动态工作ROI不减少完整安全区RAW scout成本。共享预计算耗时应与每arm引擎耗时分列，不能把缓存复用当算法提速。

同帧差异只能归因于该条件开关与其时序反馈整体，不证明唯一物理机制；S5是反馈而非严格流水阶段，Oracle不能替代正式tip。组合不是验证后选优。另见[预标注轨迹预算定位](PRELABEL_TRACK_BUDGET_FINDING.md)，其中三点弯FULL的93次预算失败全部来自轨迹上限；不能把它们归咎于RAW或图边预算。
