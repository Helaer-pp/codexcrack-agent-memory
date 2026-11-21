# V5.9 失败与退化帧专项分析

真实图像纳入可见标注里尖端超出 10 px 或路径联合失败的每一帧，逐一列出完整与纯灰度模式。曲线记录各入口的累计得分，虚线标出人工尖端横坐标。没有可达入口时保留空图并注明原因。

## 开发组A

| 位置 | 模式 | 帧 | 误差 px | 覆盖 | 精度 | 失效证据 | 图像 / 曲线 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| original | full | 398 | 12.10 | 1.00 | 0.99 | 分支 0。端点相对标注横向 +11.8、纵向 +2.4 px。终点由本分支累计得分峰给出。 初始峰 [1337, 1164]，最终 [1337, 1164]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_a/original/full/0398.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_a/original/full/0398.png) |
| original | raw_only | 398 | 12.10 | 1.00 | 0.99 | 分支 0。端点相对标注横向 +11.8、纵向 +2.4 px。终点由本分支累计得分峰给出。 初始峰 [1337, 1164]，最终 [1337, 1164]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_a/original/raw_only/0398.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_a/original/raw_only/0398.png) |
| original | raw_only | 504 | 20.97 | 0.97 | 1.00 | 分支 0。端点相对标注横向 -21.0、纵向 +0.4 px。终点由本分支累计得分峰给出。 初始峰 [1359, 1159]，最终 [1359, 1159]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_a/original/raw_only/0504.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_a/original/raw_only/0504.png) |

## 三点弯

| 位置 | 模式 | 帧 | 误差 px | 覆盖 | 精度 | 失效证据 | 图像 / 曲线 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| original | full | 1 | 95.90 | 0.00 | 0.00 | 分支 0。端点相对标注横向 +68.9、纵向 -66.8 px。终点由本分支累计得分峰给出。 初始峰 [1561, 2665]，最终 [1561, 2665]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0001.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0001.png) |
| original | full | 144 | 29.55 | 0.60 | 1.00 | 分支 2。端点相对标注横向 -25.8、纵向 +14.5 px。终点由本分支累计得分峰给出。 初始峰 [1506, 2728]，最终 [1506, 2728]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0144.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0144.png) |
| original | full | 178 | 25.38 | 0.60 | 0.94 | 分支 2。端点相对标注横向 -19.4、纵向 +16.4 px。终点由本分支累计得分峰给出。 初始峰 [1520, 2734]，最终 [1520, 2734]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0178.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0178.png) |
| original | full | 215 | 85.76 | 0.32 | 0.91 | 分支 2。端点相对标注横向 -85.0、纵向 +11.4 px。终点由本分支累计得分峰给出。 初始峰 [1520, 2730]，最终 [1520, 2730]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0215.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0215.png) |
| original | full | 248 | 124.95 | 0.25 | 1.00 | 分支 2。端点相对标注横向 -124.9、纵向 +2.8 px。终点由本分支累计得分峰给出。 初始峰 [1505, 2728]，最终 [1505, 2728]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0248.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0248.png) |
| original | full | 306 | 11.51 | 0.93 | 0.89 | 分支 2。端点相对标注横向 +11.5、纵向 +0.8 px。采用 9 列前向桥接，细脊占 56%。 初始峰 [1687, 2718]，最终 [1696, 2719]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0306.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0306.png) |
| original | full | 335 | 12.47 | 0.92 | 0.90 | 分支 2。端点相对标注横向 +12.0、纵向 -3.2 px。终点由本分支累计得分峰给出。 初始峰 [1713, 2719]，最终 [1713, 2719]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0335.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0335.png) |
| original | full | 407 | 19.99 | 0.91 | 0.92 | 分支 2。端点相对标注横向 -19.9、纵向 +1.5 px。终点由本分支累计得分峰给出。 初始峰 [1745, 2721]，最终 [1745, 2721]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0407.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0407.png) |
| original | full | 413 | 14.21 | 1.00 | 0.97 | 分支 2。端点相对标注横向 +14.2、纵向 +0.3 px。采用 4 列前向桥接，细脊占 100%。 初始峰 [1753, 2721]，最终 [1757, 2723]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0413.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0413.png) |
| original | full | 435 | 12.76 | 0.94 | 0.92 | 分支 2。端点相对标注横向 +12.4、纵向 -3.0 px。采用 7 列前向桥接，细脊占 86%。 初始峰 [1763, 2722]，最终 [1770, 2720]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0435.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0435.png) |
| original | full | 503 | 17.50 | 0.95 | 0.92 | 分支 2。端点相对标注横向 +16.0、纵向 +7.0 px。采用 3 列前向桥接，细脊占 100%。 初始峰 [1800, 2725]，最终 [1803, 2727]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0503.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/full/0503.png) |
| original | raw_only | 1 | 96.62 | 0.00 | 0.00 | 分支 0。端点相对标注横向 +69.9、纵向 -66.8 px。终点由本分支累计得分峰给出。 初始峰 [1562, 2665]，最终 [1562, 2665]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/raw_only/0001.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/raw_only/0001.png) |
| original | raw_only | 144 | 19.40 | 0.67 | 0.63 | 分支 2。端点相对标注横向 +19.2、纵向 -2.5 px。终点由本分支累计得分峰给出。 初始峰 [1551, 2711]，最终 [1551, 2711]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/raw_only/0144.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/raw_only/0144.png) |
| original | raw_only | 178 | 20.94 | 0.78 | 0.68 | 分支 2。端点相对标注横向 +18.6、纵向 -9.6 px。终点由本分支累计得分峰给出。 初始峰 [1558, 2708]，最终 [1558, 2708]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/raw_only/0178.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/raw_only/0178.png) |
| original | raw_only | 271 | 22.48 | 0.86 | 0.88 | 分支 2。端点相对标注横向 -22.2、纵向 +3.5 px。终点由本分支累计得分峰给出。 初始峰 [1640, 2724]，最终 [1640, 2724]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/raw_only/0271.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/raw_only/0271.png) |
| original | raw_only | 347 | 14.43 | 0.93 | 0.93 | 分支 2。端点相对标注横向 -14.3、纵向 -1.9 px。终点由本分支累计得分峰给出。 初始峰 [1697, 2719]，最终 [1697, 2719]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/raw_only/0347.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/raw_only/0347.png) |
| original | raw_only | 381 | 14.18 | 0.94 | 0.94 | 分支 2。端点相对标注横向 -14.2、纵向 -0.2 px。终点由本分支累计得分峰给出。 初始峰 [1727, 2721]，最终 [1727, 2721]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/raw_only/0381.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/raw_only/0381.png) |
| original | raw_only | 407 | 27.98 | 0.88 | 0.91 | 分支 2。端点相对标注横向 -27.9、纵向 +1.5 px。终点由本分支累计得分峰给出。 初始峰 [1737, 2721]，最终 [1737, 2721]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/raw_only/0407.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/three_point_bend/original/raw_only/0407.png) |

## 验证组C

| 位置 | 模式 | 帧 | 误差 px | 覆盖 | 精度 | 失效证据 | 图像 / 曲线 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| original | full | 38 | 18.15 | 0.49 | 0.77 | 分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/original/full/0038.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/original/full/0038.png) |
| original | full | 54 | 28.94 | 0.44 | 0.93 | 分支 2。端点相对标注横向 -27.5、纵向 +9.0 px。终点由本分支累计得分峰给出。 初始峰 [2274, 2340]，最终 [2274, 2340]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/original/full/0054.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/original/full/0054.png) |
| original | full | 510 | 15.96 | 1.00 | 0.97 | 分支 1。端点相对标注横向 +15.9、纵向 -0.6 px。终点由本分支累计得分峰给出。 初始峰 [2506, 2345]，最终 [2506, 2345]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/original/full/0510.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/original/full/0510.png) |
| original | raw_only | 38 | 18.15 | 0.49 | 0.77 | 分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0038.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0038.png) |
| original | raw_only | 54 | 28.94 | 0.44 | 0.93 | 分支 2。端点相对标注横向 -27.5、纵向 +9.0 px。终点由本分支累计得分峰给出。 初始峰 [2274, 2340]，最终 [2274, 2340]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0054.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0054.png) |
| original | raw_only | 69 | 13.62 | 0.94 | 0.93 | 分支 2。端点相对标注横向 -13.6、纵向 +0.6 px。终点由本分支累计得分峰给出。 初始峰 [2290, 2332]，最终 [2290, 2332]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0069.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0069.png) |
| original | raw_only | 95 | 25.25 | 0.81 | 0.96 | 分支 2。端点相对标注横向 -24.6、纵向 -5.6 px。终点由本分支累计得分峰给出。 初始峰 [2303, 2331]，最终 [2303, 2331]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0095.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0095.png) |
| original | raw_only | 232 | 12.02 | 0.99 | 1.00 | 分支 1。端点相对标注横向 -12.0、纵向 +0.7 px。终点由本分支累计得分峰给出。 初始峰 [2408, 2345]，最终 [2408, 2345]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0232.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0232.png) |
| original | raw_only | 324 | 27.53 | 1.00 | 0.93 | 分支 1。端点相对标注横向 +22.3、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0324.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0324.png) |
| original | raw_only | 335 | 23.40 | 1.00 | 0.94 | 分支 1。端点相对标注横向 +16.8、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2487, 2329]，最终 [2487, 2329]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0335.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0335.png) |
| original | raw_only | 345 | 20.10 | 1.00 | 0.95 | 分支 1。端点相对标注横向 +12.5、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0345.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0345.png) |
| original | raw_only | 363 | 16.12 | 0.99 | 0.96 | 分支 2。端点相对标注横向 +3.0、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0363.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/original/raw_only/0363.png) |
| bright | full | 38 | 18.15 | 0.49 | 0.77 | 分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/bright/full/0038.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/bright/full/0038.png) |
| bright | full | 54 | 28.94 | 0.44 | 0.93 | 分支 2。端点相对标注横向 -27.5、纵向 +9.0 px。终点由本分支累计得分峰给出。 初始峰 [2274, 2340]，最终 [2274, 2340]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/bright/full/0054.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/bright/full/0054.png) |
| bright | full | 510 | 15.96 | 1.00 | 0.97 | 分支 1。端点相对标注横向 +15.9、纵向 -0.6 px。终点由本分支累计得分峰给出。 初始峰 [2506, 2345]，最终 [2506, 2345]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/bright/full/0510.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/bright/full/0510.png) |
| bright | raw_only | 38 | 18.15 | 0.49 | 0.77 | 分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0038.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0038.png) |
| bright | raw_only | 54 | 28.94 | 0.44 | 0.93 | 分支 2。端点相对标注横向 -27.5、纵向 +9.0 px。终点由本分支累计得分峰给出。 初始峰 [2274, 2340]，最终 [2274, 2340]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0054.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0054.png) |
| bright | raw_only | 69 | 13.62 | 0.94 | 0.93 | 分支 2。端点相对标注横向 -13.6、纵向 +0.6 px。终点由本分支累计得分峰给出。 初始峰 [2290, 2332]，最终 [2290, 2332]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0069.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0069.png) |
| bright | raw_only | 95 | 25.25 | 0.81 | 0.96 | 分支 2。端点相对标注横向 -24.6、纵向 -5.6 px。终点由本分支累计得分峰给出。 初始峰 [2303, 2331]，最终 [2303, 2331]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0095.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0095.png) |
| bright | raw_only | 232 | 12.02 | 0.99 | 1.00 | 分支 1。端点相对标注横向 -12.0、纵向 +0.7 px。终点由本分支累计得分峰给出。 初始峰 [2408, 2345]，最终 [2408, 2345]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0232.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0232.png) |
| bright | raw_only | 324 | 27.53 | 1.00 | 0.93 | 分支 1。端点相对标注横向 +22.3、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0324.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0324.png) |
| bright | raw_only | 335 | 23.40 | 1.00 | 0.94 | 分支 1。端点相对标注横向 +16.8、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2487, 2329]，最终 [2487, 2329]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0335.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0335.png) |
| bright | raw_only | 345 | 20.10 | 1.00 | 0.95 | 分支 1。端点相对标注横向 +12.5、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0345.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0345.png) |
| bright | raw_only | 363 | 16.12 | 0.99 | 0.96 | 分支 2。端点相对标注横向 +3.0、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 | [四栏图](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0363.jpg) · [分支曲线](../../output/experiments/v59_converged_r04/failures/group_c/bright/raw_only/0363.png) |

## 重点退化发生在哪一步

开发组A 398 的已发布路径到达人工尖端附近却继续延长，误差 12.10 px。验证组C两种点位的失败集中在同三帧：38、54 帧在标注前停止，510 帧越过标注。三点弯 215、248 均从下唇缘分支出发，在完整模式的原始峰停止，没有批准远峰或桥接。仅顶点吸附模式在相同帧可到达更远位置。

下表统计完整模式失败帧在人工尖端所在 x 列是否仍有可达 DP 路径，以及所有分支的最近候选端点误差。该列可达只说明横向搜索范围覆盖该位置，无法证明路径与真实裂纹重合。

| 组 | 点位 | 帧 | 候选分支数 | 最近候选误差 px | 到达人工 x 列的分支数 | 该列最高累计分 |
| --- | --- | --- | --- | --- | --- | --- |
| 开发组A | original | 398 | 1 | 12.10 | 1 | 387.65 |
| 三点弯 | original | 1 | 2 | 2.98 | 2 | 11.84 |
| 三点弯 | original | 144 | 3 | 11.53 | 3 | 40.12 |
| 三点弯 | original | 178 | 3 | 19.94 | 3 | 36.01 |
| 三点弯 | original | 215 | 3 | 82.13 | 1 | 13.81 |
| 三点弯 | original | 248 | 3 | 100.96 | 1 | 46.77 |
| 三点弯 | original | 306 | 3 | 11.51 | 1 | 103.58 |
| 三点弯 | original | 335 | 3 | 12.47 | 1 | 116.33 |
| 三点弯 | original | 407 | 3 | 19.99 | 2 | 146.94 |
| 三点弯 | original | 413 | 3 | 10.34 | 2 | 155.70 |
| 三点弯 | original | 435 | 3 | 5.49 | 2 | 169.00 |
| 三点弯 | original | 503 | 2 | 13.97 | 2 | 195.17 |
| 验证组C | original | 38 | 2 | 18.15 | 3 | 18.20 |
| 验证组C | original | 54 | 3 | 28.94 | 2 | 20.05 |
| 验证组C | original | 510 | 2 | 15.96 | 1 | 271.26 |
| 验证组C | bright | 38 | 2 | 18.15 | 3 | 18.20 |
| 验证组C | bright | 54 | 3 | 28.94 | 2 | 20.05 |
| 验证组C | bright | 510 | 3 | 15.96 | 1 | 270.95 |
