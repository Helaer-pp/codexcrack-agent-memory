# V5.8 r05 三项桥接护栏修正与开发组复验

r04 已按冻结顺序各验证一次。其前向桥接除占比、桥接场净分和参考静态排除，还继承了首四列至少一次命中、最后一列也须命中以及最短尾段。这会拒绝已达任务书三项要求的候选。r05 删除这三项附加判定；候选仍从已有联合证据的固定前缀出发，有新增像素才能定义净分。被参考强暗线解释的差分细脊在桥接表中直接屏蔽。每步保留转向和步长代价。完整算法和校验哈希已单独冻结。

开发组A联合命中 17/19，全 551 帧选用桥接 16 次。全合成矩阵 1296 例，432 个阴性误报 0，弱带严格通过 216/216。全部同步扰动的有效端点最大漂移 0.00 px。三点弯、验证组C没有在 r05 重跑，因此 r04 的验证结果不能用于判定此修正版的验证精度。

[r05 核心源码](../../../research/notch_identity_v58_strict/terminal.py) · [冻结记录](freeze.json) · [开发组A四栏图与视频](difference_views/index.html) · [逐帧长度](crack_lengths.csv) · [合成矩阵](paired_probes.csv) · [同步扰动](jitter_summary.csv)

## 开发组A失败帧

图像链接为完整模式，曲线按所列模式读取。

| 帧 | 模式 | 尖端误差 px | 覆盖率 | 精度 | 输出端点 | 曲线 |
|---|---|---|---|---|---|---|
| [299](difference_views/frames/group_a/0299.jpg) | full | 19.84 | 0.96 | 1.00 | [1228, 1162] | [分支得分](curves/group_a/0299_full.png) |
| [398](difference_views/frames/group_a/0398.jpg) | full | 12.10 | 1.00 | 0.99 | [1337, 1164] | [分支得分](curves/group_a/0398_full.png) |
| [398](difference_views/frames/group_a/0398.jpg) | raw_only | 12.10 | 1.00 | 0.99 | [1337, 1164] | [分支得分](curves/group_a/0398_raw_only.png) |
| [504](difference_views/frames/group_a/0504.jpg) | raw_only | 20.97 | 0.97 | 1.00 | [1359, 1159] | [分支得分](curves/group_a/0504_raw_only.png) |
