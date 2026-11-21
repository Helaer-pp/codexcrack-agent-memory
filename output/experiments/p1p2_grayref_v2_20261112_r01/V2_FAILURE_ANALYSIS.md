# 六组失败分析

阶段标签是事后证据分类，不是互斥物理因果真值。先记录ROI排除、输出不确定/缺失，再记录首观测距人工路径>10、过延伸或未解决。没有用这些标签反调规则。

| 组 | 阶段 | 可见帧数 |
|---|---|---|
| group_a | UNCERTAIN_ORIGIN_OR_SUPPORT | 13 |
| group_a | WRONG_INITIAL_OBSERVATION | 6 |
| ct2 | WRONG_INITIAL_OBSERVATION | 20 |
| ct3 | OVEREXTENSION | 1 |
| ct3 | ROI_GEOMETRY_EXCLUSION | 6 |
| ct3 | TIP_WITHIN10_PATH_SEPARATE | 4 |
| ct3 | UNCERTAIN_ORIGIN_OR_SUPPORT | 7 |
| ct3 | WRONG_INITIAL_OBSERVATION | 1 |
| group_h | UNCERTAIN_ORIGIN_OR_SUPPORT | 18 |
| three_point_bend | UNCERTAIN_ORIGIN_OR_SUPPORT | 15 |
| group_c | TIP_WITHIN10_PATH_SEPARATE | 4 |
| group_c | UNCERTAIN_ORIGIN_OR_SUPPORT | 14 |
| group_c | WRONG_INITIAL_OBSERVATION | 2 |


完整6模式分层见failure_stage_counts.csv，逐帧原始数值见offline_evaluation_dev/validation.csv。origin_failure_audit.csv区分“人工路径在起源区外”“路径附近当前证据不足”“候选被NMS/预算/短程连接过滤”“进入假设仍未选中”。hypothesis_overlap_audit.csv记录不同初始x/y假设的实际计算轨迹重合，避免把同一条计算路径的多个起点当独立物理分叉。

已确认局限：固定valley/材料阈值与原ROI限制保留；二维候选仍局限于P点附近，不能保证找到正确缺口连接；原joint在M1-only仍可否决真实候选；M2不把未知参考当负证据，但也没有独立识别旧划痕；短程支持分数会奖励错误长暗线；简单纵向去重可能制造重复路径歧义；TERMINAL只比较当前所选路径，无法挽救错主路径。单向+x和±.2方向限制未覆盖所有真实分叉/大弯折。所有输出均暂定，不是FORMAL_OBSERVED。

下一版应先在开发数据/合成物理控制中验证起源与重合路径身份的独立证据，再讨论更大候选预算或更宽ROI；这只是建议，本轮未实施新版本。验证组C和三点弯结果只作已曝光回归，不能据此挑阈值、挑模式或宣称新盲测显著性。
