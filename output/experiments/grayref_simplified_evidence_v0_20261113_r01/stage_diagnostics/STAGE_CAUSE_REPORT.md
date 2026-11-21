# 额外逐层失效定位（离线，只读冻结输出）

| group | visible | raw_coverage80 | retained_coverage80 | finite_pool_good | chosen_good | GRAPH_ROUTE_OR_RANK_BUDGET_LOSS | STOP_OR_PUBLIC_AMBIGUITY | JOINT_SUCCESS | ROI_TIP_EXCLUDED | FINAL_PATH_RANK_LOSS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | 19 | 19 | 19 | 2 | 2 | 17 | 2 |  |  |  |
| ct2 | 20 | 20 | 20 | 4 | 4 | 16 | 4 |  |  |  |
| group_h | 18 | 18 | 18 | 10 | 10 | 8 | 8 | 2 |  |  |
| ct3 | 19 | 19 | 19 | 0 | 0 | 13 |  |  | 6 |  |
| group_c | 20 | 20 | 20 | 16 | 8 | 4 | 8 |  |  | 8 |
| three_point_bend | 15 | 15 | 15 | 1 | 0 | 14 |  |  |  | 1 |

原始局部峰与保留节点覆盖率只是GT附近存在证据，不是正确整条主裂纹。图阶段包含邻接匹配、桥接、单前驱动态规划及六路径预算，不能仅凭终态确定是哪一个子项造成损失。此报告不会回写推理或调参。

开发组主要首败：[('GRAPH_ROUTE_OR_RANK_BUDGET_LOSS', 54)]。

唯一建议：固定现有暗谷候选与分数，单独检查片段邻接/前驱保留/路径预算导致的路径保真损失，先用现有原图证据逐项定位；不要通过增加末端门或降低不确定门掩盖路径池缺失。这里只提出诊断，不自动改算法。

- [group_a/308](../galleries/group_a/308/index.html)：原始峰覆盖1.000，保留节点1.000，有限路径池并集0.691；GRAPH_ROUTE_OR_RANK_BUDGET_LOSS。

- [group_a/398](../galleries/group_a/398/index.html)：原始峰覆盖1.000，保留节点1.000，有限路径池并集0.764；GRAPH_ROUTE_OR_RANK_BUDGET_LOSS。

- [ct2/271](../galleries/ct2/271/index.html)：原始峰覆盖0.966，保留节点0.966，有限路径池并集0.122；GRAPH_ROUTE_OR_RANK_BUDGET_LOSS。

- [ct2/157](../galleries/ct2/157/index.html)：原始峰覆盖1.000，保留节点1.000，有限路径池并集0.557；GRAPH_ROUTE_OR_RANK_BUDGET_LOSS。

- [group_h/317](../galleries/group_h/317/index.html)：原始峰覆盖1.000，保留节点1.000，有限路径池并集0.000；GRAPH_ROUTE_OR_RANK_BUDGET_LOSS。

- [group_h/78](../galleries/group_h/78/index.html)：原始峰覆盖1.000，保留节点1.000，有限路径池并集0.075；GRAPH_ROUTE_OR_RANK_BUDGET_LOSS。

- [ct3/20](../galleries/ct3/20/index.html)：原始峰覆盖1.000，保留节点1.000，有限路径池并集0.000；GRAPH_ROUTE_OR_RANK_BUDGET_LOSS。

- [ct3/23](../galleries/ct3/23/index.html)：原始峰覆盖1.000，保留节点1.000，有限路径池并集0.000；GRAPH_ROUTE_OR_RANK_BUDGET_LOSS。

- [group_c/38](../galleries/group_c/38/index.html)：原始峰覆盖1.000，保留节点1.000，有限路径池并集0.000；GRAPH_ROUTE_OR_RANK_BUDGET_LOSS。

- [group_c/95](../galleries/group_c/95/index.html)：原始峰覆盖1.000，保留节点1.000，有限路径池并集0.000；GRAPH_ROUTE_OR_RANK_BUDGET_LOSS。

- [three_point_bend/306](../galleries/three_point_bend/306/index.html)：原始峰覆盖1.000，保留节点1.000，有限路径池并集0.326；GRAPH_ROUTE_OR_RANK_BUDGET_LOSS。

- [three_point_bend/503](../galleries/three_point_bend/503/index.html)：原始峰覆盖1.000，保留节点1.000，有限路径池并集0.387；GRAPH_ROUTE_OR_RANK_BUDGET_LOSS。
