# H2 与 Oracle

真实图六类对照的缺失记录逐帧保存在 data/oracle_real_GT_missing.jsonl；没有实际人工GT时不把冻结基线路径伪装成Oracle。生成图的真实路径、候选与GT端点召回见 tests/synthetic_v4/graph_truth.json 和 tests/synthetic_truth_and_metrics.json。

K=2/3只在满足至少6个重叠列相距4px时视为不同候选，端点抖动或同一路径的不同截断不计分支。此为局部tile几何去重，不代表物理裂纹分支。当前序列K1/2/3采用同一评分最优路径，额外候选仅增加候选可检查性，不能虚称自动恢复了正确分支。合成fork中正确终点是否在K集合内见逐案例记录；若不在，末端细化无法弥补。
