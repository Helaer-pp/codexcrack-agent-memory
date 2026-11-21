# 预注册消融与比较

全局配置见config.py和configs/unified_global.json。所有11个arm在两组DEV全部1071帧运行，单组按时序独立状态。共享只读、无历史、无GT的原始特征与候选连接图；各arm自己构造搜索/验证/历史，不能共享未来状态。来源hash一致。

FULL；NO_FIXED；NO_PREV；NO_TRACKING；NO_GAP；NO_DYNAMIC_ROI；NO_MULTITRACK；NO_OPENING；预注册组合NO_BOTH_REF、NO_TRACK_MULTI、NO_GAP_ROI。各开关定义由config.ARMS冻结。

NO_FIXED仅禁用变化证据，初始图的缺口几何仍可用，不能叫完全无初始图。NO_PREV不读其证据但共享缓存仍包含原始独立注册诊断；有效channels字段表示实际消费状态。NO_TRACKING清除历史关联/ROI提示/位移复查，仍保留实际前一帧差分。NO_GAP只允许观测接壤连接。NO_DYNAMIC_ROI搜索完整安全区域。NO_MULTITRACK限制为起源/RAW最强当前轨，损失分支覆盖明确披露。NO_OPENING移除固定轴开口投影的preferred uncertain平局信息；本实现开口不决定正式tip，预期可能零正式效果，不得夸大。

主结果始终FULL，不能事后挑最优arm代替。各组分别正式Hit3/5/10/20、VALID/null、>100/500、误差n与分位、预算、两路有效参考比例、候选与轨迹、运算时间；Oracle与preferred各列独立。S1/S2/S3/S4覆盖为离线诊断，S5是反馈ROI而非单向严格阶段；最早可观测丢失不是机制因果。仅同帧配对消融可对具体开关的条件影响做陈述，不把组合差异解释为唯一根因。

开发期间先合成测试与预声明中间两帧无标签smoke；r01不做GT参数搜索。DEV结果不论通过与否均保留。开发完整推理/消融/图册/评价/重放后冻结，才允许验证组C一次正式FULL验证；验证组C无消融、无参数选择。历史算法只做冻结保护和语义标注的旧结果对照，不能叫新实测基线。
