# GROUP_A 锁后案例复核

仅描述封存结果；案例按“新增公开命中或A原合格路径”事后选取，不用于调参，不是独立验证。

| frame_id | mode | public_tip | error | public_state | pool_good | selected_trace_points | observed | inferred | nodes | promoted_nodes | containment | unvisited_budget |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 113 | A_ORIGINAL_ROI | None |  | TIP_UNCERTAIN | True | 74 | 73 | 1 | 10879 | 0 | 11 | 1907 |
| 113 | B_COMPACT_FIXED_BAND | None |  | TIP_UNCERTAIN | False | 45 | 45 | 0 | 8460 | 5700 | 42 | 1449 |
| 113 | C_DYNAMIC_CORRIDOR | None |  | TIP_UNCERTAIN | False | 40 | 40 | 0 | 9716 | 2741 | 11 | 1857 |
| 122 | A_ORIGINAL_ROI | None |  | TIP_UNCERTAIN | True | 112 | 112 | 0 | 10805 | 0 | 2 | 1791 |
| 122 | B_COMPACT_FIXED_BAND | None |  | TIP_UNCERTAIN | True | 44 | 44 | 0 | 7957 | 5206 | 118 | 1282 |
| 122 | C_DYNAMIC_CORRIDOR | None |  | TIP_UNCERTAIN | True | 44 | 44 | 0 | 9444 | 2781 | 15 | 1727 |
| 451 | A_ORIGINAL_ROI | None |  | TIP_UNCERTAIN | False | 142 | 142 | 0 | 10861 | 0 | 4 | 1872 |
| 451 | B_COMPACT_FIXED_BAND | [1356, 1161] | 0.9827600288159495 | PROVISIONAL_TIP | True | 399 | 330 | 69 | 8449 | 5543 | 575 | 883 |
| 451 | C_DYNAMIC_CORRIDOR | None |  | TIP_UNCERTAIN | False | 142 | 142 | 0 | 9630 | 2623 | 1 | 1756 |

## 原A合格路径的节点与片段存活

| frame_id | A_good_path_rank | mode | observed_nodes | outside_search | missing_retained_nodes | old_adjacent_fragment_links_split | first_split | first_missing | offline_path_good_only |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 113 | 0 | B_COMPACT_FIXED_BAND | 73 | 0 | 0 | 1 | [(997, 1143), (998, 1145)] | None | True |
| 113 | 0 | C_DYNAMIC_CORRIDOR | 73 | 0 | 0 | 1 | [(997, 1143), (998, 1145)] | None | True |
| 122 | 0 | B_COMPACT_FIXED_BAND | 112 | 0 | 0 | 1 | [(998, 1146), (999, 1149)] | None | True |
| 122 | 0 | C_DYNAMIC_CORRIDOR | 112 | 0 | 0 | 1 | [(998, 1146), (999, 1149)] | None | True |

节点都在新ROI且仍被保留，不保证原片段链接或动态规划路线保持不变。紧缩mask可以释放每列预算并引入其他已存在的局部峰，改变一对一邻接匹配；这是ROI操作通过冻结图构建器产生的效应，不是本轮修改了图规则。上表只证明实际节点/片段的首次变化，不能把所有路线损失归结为这一因素。

GROUP_A451的B原生尖端(1356,1161)误差约0.983px，停止后负证据20/24，通过原0.8门；A/C停在较早路径且后方仍有支持。GROUP_A113在B/C失去原合格路径，说明新增一张成功同时伴有候选保真退化，不能只报告1/19的收益。完整状态和损失纳入预先冻结判定。

计时说明：A/B/C固定执行顺序且共享缓存，存在并发和内存热身影响；shared_geometry_controller_ms还含边界诊断及封装开销，不能称纯走廊内核成本。速度表不替代目标硬件实时验收。
