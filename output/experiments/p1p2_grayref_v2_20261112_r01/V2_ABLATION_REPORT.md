# 严格消融结果与解释

所有模式使用同样原图、逐帧点、V1 ROI/预处理。原V1是不可变原生Python，六档继续保留。下表核心M1/M2需相对NUMERIC_CONTROL共同底座解释；该底座相对原V1的确定性数值规则和输出安全过滤已经单独列出，不能隐藏进M1增益。

| 组/用途 | 模式 | 可见分母 | 输出 | ≤3 | ≤5 | ≤10 | >100 | >500 | 不确定 | 无端点 | 端点+路径联合 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DEVELOPMENT | V1_LOCKED | 76 | 50 | 6 | 8 | 12 | 31 | 18 | 0 | 26 | 11 |
| DEVELOPMENT | V2_NUMERIC_CONTROL | 76 | 43 | 6 | 8 | 12 | 24 | 17 | 7 | 26 | 11 |
| DEVELOPMENT | V2_ORIGIN_ONLY | 76 | 55 | 6 | 8 | 11 | 38 | 19 | 21 | 0 | 10 |
| DEVELOPMENT | V2_REF_ONLY | 76 | 59 | 4 | 5 | 8 | 40 | 21 | 0 | 17 | 6 |
| DEVELOPMENT | V2_COMBINED | 76 | 37 | 2 | 2 | 4 | 26 | 19 | 39 | 0 | 4 |
| DEVELOPMENT | V2_TERMINAL | 76 | 37 | 2 | 3 | 5 | 26 | 19 | 39 | 0 | 5 |
| EXPOSED_VALIDATION | V1_LOCKED | 35 | 20 | 0 | 2 | 5 | 4 | 0 | 0 | 15 | 5 |
| EXPOSED_VALIDATION | V2_NUMERIC_CONTROL | 35 | 14 | 0 | 2 | 5 | 0 | 0 | 6 | 15 | 5 |
| EXPOSED_VALIDATION | V2_ORIGIN_ONLY | 35 | 11 | 6 | 6 | 9 | 0 | 0 | 24 | 0 | 1 |
| EXPOSED_VALIDATION | V2_REF_ONLY | 35 | 35 | 6 | 6 | 13 | 2 | 0 | 0 | 0 | 13 |
| EXPOSED_VALIDATION | V2_COMBINED | 35 | 6 | 2 | 2 | 4 | 0 | 0 | 29 | 0 | 3 |
| EXPOSED_VALIDATION | V2_TERMINAL | 35 | 6 | 4 | 4 | 5 | 0 | 0 | 29 | 0 | 4 |


NUMERIC_CONTROL开发命中仍12，公开>100从31降至24，但原候选>100仍31：主要是短路径状态过滤，不是新增正确路径。M1-only短程多候选没有获得两个非CT3组命中，且错误尾部扩大。M2-only使已有/不可靠参考下当前暗谷可推进，但长纹理身份无法仅靠正增量辅助区分。组合歧义拒绝进一步损失命中；没有使用“各组最佳模式”作为默认。

TERMINAL是额外模块，与COMBINED的seeds/paths完整相同，区别仅在所选路径上的停止候选排序与最终截断。开发命中5对4只是这项额外规则的结果，不计入M1/M2因果收益。独立材料NCC仅输出审计，不替换remap；没有隐含M3或时间增强。

精确开关和阈值见config_v2_locked.json，规则锁定时间与源码SHA固定。没有开发r02或验证后改参。所有端点/状态/原候选严重尾部见group_summary.csv，不只展示成功者。
