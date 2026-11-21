# 冻结基线对照边界

旧 A 的正式观测与 GrayRef 暂定端点、新规则VALID并非同一物理认证等级。本对照表未重新执行旧A/V1/V2，也未以其候选Oracle代替正式结果。此前误运行通用检查中的旧A少量回放另记于PROTOCOL_DEVIATION.md，不属于此全序列对照。下表只读取原封存汇总，明确是历史比较；不能当本轮公平重测或新盲测。A不提供语义匹配的新1633帧正式统计，记NOT_RERUN而非虚造指标。

| version | group | visible | valid | hit10 | over100 | semantics |
|---|---|---|---|---|---|---|
| V1 | group_a | 19 | 13 | 0 | 13 | HISTORICAL_PROVISIONAL_NOT_NEW_FORMAL_OBSERVATION |
| V1 | group_c | 20 | 6 | 0 | 4 | HISTORICAL_PROVISIONAL_NOT_NEW_FORMAL_OBSERVATION |
| V1 | three_point_bend | 15 | 14 | 5 | 0 | HISTORICAL_PROVISIONAL_NOT_NEW_FORMAL_OBSERVATION |
| V2 | group_a | 19 | 6 | 0 | 6 | HISTORICAL_PROVISIONAL_NOT_NEW_FORMAL_OBSERVATION |
| V2 | group_c | 20 | 6 | 4 | 0 | HISTORICAL_PROVISIONAL_NOT_NEW_FORMAL_OBSERVATION |
| V2 | three_point_bend | 15 | 0 | 0 | 0 | HISTORICAL_PROVISIONAL_NOT_NEW_FORMAL_OBSERVATION |

旧源码、DLL、原输出全部hash核对见final_integrity.json。
