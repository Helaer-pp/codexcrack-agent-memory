# ROI 因果结论

GEOMETRY_HARMFUL / NO_GO；不替换A/V1/V2或上一轮简化原型。

| group | mode | visible | outputs | no_public | hit3 | hit5 | hit10 | hit20 | joint | over100 | over500 | any_candidate_path_good | GT_EXCLUDED |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | A_ORIGINAL_ROI | 19 | 0 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| group_a | B_COMPACT_FIXED_BAND | 19 | 1 | 18 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 2 | 0 |
| group_a | C_DYNAMIC_CORRIDOR | 19 | 0 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| group_c | A_ORIGINAL_ROI | 20 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |
| group_c | B_COMPACT_FIXED_BAND | 20 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 18 | 0 |
| group_c | C_DYNAMIC_CORRIDOR | 20 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |
| three_point_bend | A_ORIGINAL_ROI | 15 | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| three_point_bend | B_COMPACT_FIXED_BAND | 15 | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| three_point_bend | C_DYNAMIC_CORRIDOR | 15 | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

只改变候选可访问的像素集合；特征、配准、归一化、桥接、去重、路径预算、分数和停止背景完全冻结。新增ROI_LIMITED是搜索边界的显式拒绝，不是新的停止识别成功。

| group | mode | visible | hit10_gained | hit10_lost | joint_gained | joint_lost | new_over100 | new_over500 | new_GT_EXCLUDED | pool_good_lost | pool_good_gained |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | B_COMPACT_FIXED_BAND | 19 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 1 |
| group_a | C_DYNAMIC_CORRIDOR | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| group_c | B_COMPACT_FIXED_BAND | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| group_c | C_DYNAMIC_CORRIDOR | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| three_point_bend | B_COMPACT_FIXED_BAND | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| three_point_bend | C_DYNAMIC_CORRIDOR | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |

- 缩ROI但候选仍不改善：[group_a/67](frames/group_a/67/index.html)，B_COMPACT_FIXED_BAND，EVIDENCE_OR_GRAPH_REACHABILITY，公开误差N/A。
- 正确候选被裁剪：本轮可见标签中无案例。
- 错误路线仍胜出：本轮可见标签中无案例。
- 末端无可靠停止：[group_a/122](frames/group_a/122/index.html)，A_ORIGINAL_ROI，STOPPING_OR_AMBIGUITY，公开误差N/A。
- 图路径仍未到达：[group_a/67](frames/group_a/67/index.html)，A_ORIGINAL_ROI，EVIDENCE_OR_GRAPH_REACHABILITY，公开误差N/A。
- 搜索边界限制：[group_c/1](frames/group_c/1/index.html)，C_DYNAMIC_CORRIDOR，PATH_RANKING，公开误差N/A。
- 参考不可用：[group_a/1](frames/group_a/1/index.html)，A_ORIGINAL_ROI，UNKNOWN，公开误差N/A。

ROI面积下降不自动说明排除了错误暗线；候选数量、池中合格路径、实际公开尖端与拒绝率必须同时看。路径局部峰仍存在但未形成完整路径时，不能归咎于ROI面积本身。

唯一后续建议：保留本轮失败，不继续调整ROI宽度；只在原A固定候选池上单独检验不同终止跨度的包含关系保留，其他模块保持冻结。本轮未实施该改动，也不承诺能恢复尖端。

[完整报告](REPORT.md) · [1633帧图册](galleries/index.html) · [逐帧胜负](paired_frame_comparison.csv) · [候选血缘索引](candidate_lineage.csv)
