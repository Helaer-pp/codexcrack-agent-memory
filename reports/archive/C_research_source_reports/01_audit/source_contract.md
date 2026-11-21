# 冻结源码合同（实读）

文件 `D:/workspace\crack_v4_cpp\frozen_dp_tip_20261030\baseline\src\CrackV4.cpp`，SHA-256 `4a774d93d9d1df19429bd4981e22b799d01b7e0a8826ffb006b13bf2378e143d`。以下行号取当前冻结文件，不修改该文件。

| 项目 | 函数 / 行号 | 实现事实 |
|---|---|---|
| 坐标与初窗 | Detector::Detector 493–542 | origin为两点均值，forward=(across.y,-across.x)；亮度双侧140判歧义，实验方向合同保留排序右侧；seed_u0=-round(d/6),width=max(48,d),half=max(12,d/4) |
| 根部 | locateRoot 944–1020 | Otsu阈值限制45…120，开运算3×3，按左侧相连暗域宽度/中心跨越选择；不是任意真实物理裂纹根部真值 |
| 几何配准 | choosePatches 661 / motion 762 / refineRoot 1021 | 两点与材料匹配配准、可选refine；根部模板NCC门槛.6；两种映射差值不是物理位移真值 |
| 特征与噪声 | tile 1047–1186 | 法向blackhat核5/9/13；reference>140选offset；material>165选噪声；ref<110屏蔽；old rl>25；当前/参考暗谷差与灰差取min；MAD、95分位、cfg.score=2.5上取大后平移评分 |
| DP | ridge 359–423 / seed 1198–1435 | continuation前驱±2且1.2*d²惩罚；seed有另一起始/重启/历史项，不能用continuation公式冒充完整seed |
| 分块 | process 1590–1708 | tile96/advance48/maxgap10；half=clip(.18d,20,40)；路径尾向量反向dot<-.7触发direction_ambiguous；支持点<3或gain<4触发evidence_ended |
| 停止/确认 | process 1709–1735 / measure 1490–1588 | evidence_ended使legacy endpoint可用；measure强证据或前缀约30点时序命中>=3才接受，参考absolute另需root；length=tip&&root |
| 终端旁路 | terminalAudit 1777–1887 | 新采样前方与尾质量、endpoint history；policy1只记shadow，policy2才替换；reg ambiguity/visibility实验有单独保护 |
| 输出耦合 | measure 1550–1588 / GetResultV2 2145–2176 | 原root-to-tip弧长只有tip&&root输出；tip已允许某些root缺失；路径CopyPath 2116返回double列表，不重新取整 |
| 内存/热点 | tile/ridge/constructor | 初始reference tile缓存；当前remap、3尺度blackhat、mask/score矩阵，DP parent分配；本轮C以局部窗口/候选上限限制开销，Python耗时不是原生实时证明 |

审计结论：A内部ROI/响应不能不改A而无损注入C；新增C系统模块消融以C_BASE为参照。C保留A路径主候选，另加有界种子DP、独立当前剖面和前方审计。图像验证证据仍相关，不宣称统计独立或校准置信度。
