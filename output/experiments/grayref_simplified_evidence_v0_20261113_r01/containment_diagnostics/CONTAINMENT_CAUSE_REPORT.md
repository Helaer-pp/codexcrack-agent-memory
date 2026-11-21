# 包含关系去重的只读因果定位

| group | visible | preselection_good_frames | kept_good_frames | containment_loss_without_good_keeper | frames_good_budget_dropped |
| --- | --- | --- | --- | --- | --- |
| group_a | 19 | 4 | 2 | 2 | 1 |
| ct2 | 20 | 6 | 4 | 2 | 0 |
| group_h | 18 | 16 | 10 | 2 | 5 |
| ct3 | 19 | 2 | 0 | 1 | 1 |
| group_c | 20 | 20 | 16 | 0 | 19 |
| three_point_bend | 15 | 2 | 1 | 1 | 1 |

所有111帧的原生保留路径ID、片段链、排序分数均与存量数值图精确重放一致。原始图确实曾形成的排序前路线才纳入表，不引入新图像候选、不修改连接、权重或停止。

同一路线的强前缀可能比“强前缀+弱延伸”平均分更高。当前包含关系去重把二者看作重复，从而可能保留短前缀、删除较完整路线。独立合成强弱两段已复现该机制；上表是真实可见帧的实际损失，不从合成推断真实成功率。

`containment_loss_without_good_keeper`要求：被删除路线满足离线路径覆盖/精度≥0.8，其压制者不满足，而且最终池没有其他合格路径。仅近邻点被删不计损失；若该值为0，不应归咎于去重。

排序前路径质量不是原生尖端成功；这些被删路线未在原始流程中进行停止评估，因此不得把它们当新增联合命中或已验证改进。

- [group_a/67](../galleries/group_a/67/index.html)：排序前合格6，包含关系压制1，最终池合格0。
- [group_a/165](../galleries/group_a/165/index.html)：排序前合格2，包含关系压制2，最终池合格0。
- [ct2/8](../galleries/ct2/8/index.html)：排序前合格1，包含关系压制1，最终池合格0。
- [ct2/131](../galleries/ct2/131/index.html)：排序前合格4，包含关系压制4，最终池合格0。
- [group_h/141](../galleries/group_h/141/index.html)：排序前合格6，包含关系压制6，最终池合格0。
- [group_h/252](../galleries/group_h/252/index.html)：排序前合格11，包含关系压制3，最终池合格0。
- [three_point_bend/503](../galleries/three_point_bend/503/index.html)：排序前合格7，包含关系压制7，最终池合格0。
- [ct3/114](../galleries/ct3/114/index.html)：排序前合格13，包含关系压制13，最终池合格0。
