# 消融结论

A0/B0/B1/B2/B3/B4/B5_GATE3_KEEP_A正式输出相同。B0加入参考几何诊断；B1加入独立材料残差分区；B2加入整路径暗谷序列；B3只生成H_A/H_SHORT；B4只描述条件SUPPORTED/UNKNOWN；B5被门禁禁用。这是旁路结构消融，不是六个不同的生产检测器，不可把零变化说成准确率提高。

DEV 240当前帧，H_SHORT候选 0；TEST720当前帧，H_SHORT候选 0。该有限DEV并未激活预定持续弱支持停止候选，不能据此证明能修复真实长尾。诊断候选单独保存在JSONL。H_ALT没有真实竞争分支分数来源，H_EXTEND没有独立证据，均未实现决策。

COMMON_TRANSFORM：B2/B3/B4使用同一条A路径和同一A原生矩阵；B1另存两点刚体矩阵作几何诊断。A原生系统与点刚体不是相同内部映射。H_SHORT_DIAGNOSTIC_NOT_SELECTED是预声明的强行候选替换对照，不进入正式输出，也不重新选TEST赢家。


B4仅原型，缺少独立光度有效性合同；不能将其SUPPORTED字段当成已验证D/G证据，详见08_reports/B4_photometry_contract_limit.md。B5保持禁用。
