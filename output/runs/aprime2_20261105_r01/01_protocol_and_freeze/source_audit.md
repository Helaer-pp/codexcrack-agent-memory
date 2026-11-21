# 实际源码与旁路审计

冻结源 baseline/frozen_a/src/CrackV4.cpp：motion约793–939，两点刚性与材料patch refine；tile约1017–1198，配准采样、亮度偏置、blackhat暗谷和参考差异；seed约1200–1495，入口ROI、可起点mask和DP；ridge359–417，逐列累积最佳前驱与端点；measure1496–1586，平滑、根部连接及历史前缀确认；process1589–1775，tile循环、增益/支持不足/缝隙/方向/边界停止；terminalAudit1789–1890，SHADOW不覆盖legacy；Process2055，GetBaseline2100，CopyPath2116，GetV22145。

已复用：tile增益、支持样本、方向、有效像素、现有DP局部路径和当前原图完整路径。旁路仅新增固定AP2Stop[256]和可选CopyStops导出到独立DLL；不写原DP/阈值/历史。
额外计算：ss中位数的<=96元素暂存、有效mask均值；Python法向5点/前后窗，最多4096路径采样，K<=12。参考最多480缓存/3查询×48patch，额外成本有界，但不满足原生2.77ms余量的任何证明。
缺省：竞争第二路径得分B、可比历史末端T未采集，null；未谎称已实现有限分叉DP备选。

Observer v1的invalid字段误用0/255均值，影响诊断显示不影响候选/检测。raw JSON保留；native_tile_samples.csv用(254+raw)/255恢复有效比例，最终C++修正为1-mean/255并再次3035帧原生对照验证。正式原生产DLL和检测过程未修改。

模板选择、局部几何/光度代码直接从本项目可移植A′模块导入；归档只读取失败机制而不作为运行时依赖。C2的第一个归属转折优先覆盖规则未复制。
