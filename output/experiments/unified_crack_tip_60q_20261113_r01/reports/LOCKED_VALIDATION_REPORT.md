# 冻结验证组C验证

新算法在prevalidation_freeze.json生成后才读取验证组C原图和实际P；但通用旧A检查已在冻结前读取过该组，严格数据隔离审计FAIL，详见PROTOCOL_DEVIATION.md。只执行一轮562帧FULL正式序列；结果封存后独立读取20张可见GT。额外原图重算和首3帧确定性检查属于固定结果审计，不选参数、不产生替换成绩。该组历史已曝光，且本轮有隔离执行偏差，明确非新盲测或隔离流程完全合格的锁定验证。

| group | frames | visible | valid | null | hit3 | hit5 | hit10 | hit20 | coverage | over100 | over500 | mean_error | median_error | p95_error | max_error | oracle_hit10 | preferred_uncertain_hit10 | passes_frozen_thresholds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| group_c | 562 | 20 | 20 | 0 | 1 | 3 | 12 | 19 | 1.0 | 0 | 0 | 9.520212062433203 | 8.733486430907812 | 16.492070640888716 | 22.00093199995825 | 17 | 0 | False |

冻结后不按验证组C调整任何算法/配置/评价逻辑，不筛掉预算耗尽或错误输出帧。
