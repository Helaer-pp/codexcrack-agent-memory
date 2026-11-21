# 失败原因分层

| group | visible | EVIDENCE_OR_GRAPH_REACHABILITY | STOPPING_OR_AMBIGUITY | PATH_COMPLETENESS_OR_CONTAMINATION | any_candidate_path_good | any_candidate_joint | JOINT_HIT | ROI_GEOMETRY_EXCLUSION | PATH_RANKING |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | 19 | 12 | 1 | 6 | 2 | 0 |  |  |  |
| ct2 | 20 | 20 |  |  | 4 | 0 |  |  |  |
| group_h | 18 | 13 | 3 |  | 10 | 2 | 2 |  |  |
| ct3 | 19 | 13 |  |  | 0 | 0 |  | 6 |  |
| group_c | 20 | 5 | 8 |  | 16 | 0 |  |  | 7 |
| three_point_bend | 15 | 11 |  | 3 | 1 | 0 |  |  | 1 |

分层规则只在离线使用GT：ROI排除→候选未到达尖端→路径完整性/污染→正确候选错排→停止或歧义。该诊断是有限候选池的定位证据，并非全部物理原因已证明。

1. GROUP_A/CT2：不再复用connection<0.5门，完整ROI扫描；但每列12峰与图的有限前驱仍会截断证据。候选数量、实际正确路径和联合命中须分开看。
2. 开发组H：不设旧96px起源带，几何上可访问全部ROI；自动暗连通分量只是NOTCH_HYPOTHESIS。可达不等于主裂纹身份正确。
3. CT3：6个历史GT尖端在严格ROI外，保留分母；本轮未根据GT扩ROI。
4. 验证组C/三点弯：分别检查候选池正确路径、排名和停止，曝光验证不用于改参数。

## 实际失败图例

- [group_h / 317](../galleries/group_h/317/index.html)：公开端点误差 565.36px；EVIDENCE_OR_GRAPH_REACHABILITY；路径覆盖/精度 0.0/0.0。
- [group_h / 96](../galleries/group_h/96/index.html)：公开端点误差 9.12px；JOINT_HIT；路径覆盖/精度 1.0/1.0。
- [group_h / 377](../galleries/group_h/377/index.html)：公开端点误差 1.55px；JOINT_HIT；路径覆盖/精度 1.0/1.0。

## 断续桥接

默认模式全帧选中路径桥接数/缺失像素总数：633/2331。桥接仅用于假设，不计观察长度。

| group | frame_id | missing_pixels | distance_max | off_annotated_path10_fraction | physical_wrong_bridge |
| --- | --- | --- | --- | --- | --- |
| ct3 | 101 | 2 | 15.703857392609692 | 1.0 | UNDETERMINED_WITH_PARTIAL_GT |
| ct3 | 135 | 2 | 15.037597357637983 | 1.0 | UNDETERMINED_WITH_PARTIAL_GT |
| group_c | 1 | 1 | 1875.7523792018785 | 1.0 | UNDETERMINED_WITH_PARTIAL_GT |
| group_c | 1 | 1 | 1879.6722304603695 | 1.0 | UNDETERMINED_WITH_PARTIAL_GT |
| group_c | 1 | 1 | 1883.6316789136347 | 1.0 | UNDETERMINED_WITH_PARTIAL_GT |
| group_c | 1 | 3 | 1889.5904753549366 | 1.0 | UNDETERMINED_WITH_PARTIAL_GT |
| group_c | 1 | 3 | 1895.550059296033 | 1.0 | UNDETERMINED_WITH_PARTIAL_GT |
| group_c | 1 | 1 | 1906.472167469646 | 1.0 | UNDETERMINED_WITH_PARTIAL_GT |

偏离人工可见段不必然等于物理错误：标签可能只覆盖部分可见段。图例可以证明当前桥接缺乏已标注路径支持，不能伪称已认证真实连接。合成测试报告长间隙/冲突拒绝、平行/交叉歧义；真实细纹理仍可能产生错误候选。
