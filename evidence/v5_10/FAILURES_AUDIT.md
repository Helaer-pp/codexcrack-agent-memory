# V5.10 失败与退化帧专项分析

共 38 条可见帧失败记录，含两种模式及验证组C两种点位。三组主结果 full 去除重复点位后，失败为开发组A 398，三点弯 144、178、215、407、503，验证组C 38、54。其余无明确人工尖端的帧单列在逐帧计分中。四栏图从左至右为固定参考、当前图、识别及人工路径叠图、有符号差分。每个曲线图画出各入口在每个横坐标上的最大累计 DP 得分，峰值纵坐标可能来自不同路径。

## 三帧的失败环节

验证组C 38 的低位暗线在固定参考中已存在，当前图上方有新增红色弯线。最终唯一合格候选停在 (2273, 2339)，距标注 18.15 px。另一路累计分不足。验证组C 54 仍只有一路合格，其他入口分别因总分不足及缺口死端被拒绝。预测路径起段先走下侧旧线，后折向上方新线，但仍提前约 12.5 px。两帧均在排序前失去独立的新分支；继续放大红脊排序权重无法改变此次输出。

三点弯 215 仅下入口合格，S1 谷后峰到达 (1566, 2708)，保住了相邻第 248 帧的远峰。第 215 帧的中段桥接搜索未找到正累计净收益的延伸，停止于原端点，横向少追 39.0 px、纵向少追 10.6 px。下表为独立的事后检查：从预测端点后一列沿人工折线直到标注路径最后一列，在上下各 2 px 的窗口计数。窗口里有红色像素，仍可能缺少由预测端点出发、连续且净得分为正的同一条轨迹。三点弯最后两列人工尖端与路径的横坐标略有差别，故实际扫描 37 列。

| 组别 | 帧 | 原图 x 范围 | 列数 | D>T | 形态细脊 | 剔除静态与偶极后 | 最长连续 | 原图暗谷 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 三点弯 | 215 | 1567–1603 | 37 | 37 | 37 | 16 | 11 | 37 |
| 验证组C | 38 | 2274–2289 | 16 | 16 | 15 | 6 | 4 | 16 |
| 验证组C | 54 | 2290–2301 | 12 | 12 | 12 | 12 | 12 | 12 |

三点弯 306、413、435 的最终误差依次为 2.49、6.43、5.49 px，均未发布短延伸。503 的两个有效候选已经汇合在 (1801, 2725)，基座即已超过人工尖端，完整版本维持 14.91 px。开发组A 398 的初始峰与发布尖端同为 (1337, 1164)，预测越过标注 11.85 px，路径整体仍能覆盖标注。两者的误差都发生在初始峰选择环节。

## 每条失败记录

### 开发组A 398 · original · full

尖端误差 12.10 px，S1 基座 12.10 px。路径覆盖率 1.00，精确率 0.99。分支 0。端点相对标注横向 +11.8、纵向 +2.4 px。终点由本分支累计得分峰给出。 初始峰 [1337, 1164]，最终 [1337, 1164]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 12.10 px。

分支编号、端点、门控与择优分依次为 0→[1337, 1164]，VALID，896.14。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：391.99 / 387.45。桥接诊断 SHORT_RIDGE。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_a/original/full/0398.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_a/original/full/0398.png)

### 开发组A 398 · original · raw_only

尖端误差 12.10 px，S1 基座 12.10 px。路径覆盖率 1.00，精确率 0.99。分支 0。端点相对标注横向 +11.8、纵向 +2.4 px。终点由本分支累计得分峰给出。 初始峰 [1337, 1164]，最终 [1337, 1164]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 12.10 px。

分支编号、端点、门控与择优分依次为 0→[1337, 1164]，VALID，513.54。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：272.39 / 271.36。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_a/original/raw_only/0398.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_a/original/raw_only/0398.png)

### 开发组A 504 · original · raw_only

尖端误差 20.97 px，S1 基座 20.97 px。路径覆盖率 0.97，精确率 1.00。分支 0。端点相对标注横向 -21.0、纵向 +0.4 px。终点由本分支累计得分峰给出。 初始峰 [1359, 1159]，最终 [1359, 1159]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 20.97 px。

分支编号、端点、门控与择优分依次为 0→[1359, 1159]，VALID，551.98。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：295.23 / 287.45。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_a/original/raw_only/0504.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_a/original/raw_only/0504.png)

### 三点弯 1 · original · raw_only

尖端误差 96.62 px，S1 基座 96.62 px。路径覆盖率 0.00，精确率 0.00。分支 0。端点相对标注横向 +69.9、纵向 -66.8 px。终点由本分支累计得分峰给出。 初始峰 [1562, 2665]，最终 [1562, 2665]。 存在 10 px 内的合格端点，排序选择失误。 最接近标注的合格端点误差 2.76 px。

分支编号、端点、门控与择优分依次为 0→[1562, 2665]，VALID，55.95；2→[1492, 2729]，VALID，23.51。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：16.95 / 6.21；1：0.00 / 不可达；2：12.46 / 12.46。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0001.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0001.png)

### 三点弯 144 · original · raw_only

尖端误差 19.40 px，S1 基座 19.40 px。路径覆盖率 0.67，精确率 0.63。分支 2。端点相对标注横向 +19.2、纵向 -2.5 px。终点由本分支累计得分峰给出。 初始峰 [1551, 2711]，最终 [1551, 2711]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 19.40 px。

分支编号、端点、门控与择优分依次为 0→[1561, 2668]，VALID，58.63；2→[1551, 2711]，VALID，61.01。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：18.33 / 14.28；1：0.00 / 不可达；2：23.96 / 23.87。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0144.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0144.png)

### 三点弯 178 · original · raw_only

尖端误差 20.94 px，S1 基座 20.94 px。路径覆盖率 0.78，精确率 0.68。分支 2。端点相对标注横向 +18.6、纵向 -9.6 px。终点由本分支累计得分峰给出。 初始峰 [1558, 2708]，最终 [1558, 2708]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 20.94 px。

分支编号、端点、门控与择优分依次为 0→[1561, 2668]，VALID，58.36；2→[1558, 2708]，VALID，71.24。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：17.41 / 12.52；1：0.00 / 不可达；2：25.74 / 20.85。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0178.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0178.png)

### 三点弯 271 · original · raw_only

尖端误差 22.48 px，S1 基座 22.48 px。路径覆盖率 0.94，精确率 0.98。分支 1。端点相对标注横向 -22.2、纵向 +3.5 px。终点由本分支累计得分峰给出。 初始峰 [1640, 2724]，最终 [1640, 2724]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 22.48 px。

分支编号、端点、门控与择优分依次为 0→[1566, 2708]，VALID，75.38；1→[1640, 2724]，VALID，167.01。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：28.58 / 16.41；1：68.86 / 62.78。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0271.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0271.png)

### 三点弯 347 · original · raw_only

尖端误差 14.43 px，S1 基座 14.43 px。路径覆盖率 0.93，精确率 0.93。分支 2。端点相对标注横向 -14.3、纵向 -1.9 px。终点由本分支累计得分峰给出。 初始峰 [1697, 2719]，最终 [1697, 2719]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 14.43 px。

分支编号、端点、门控与择优分依次为 0→[1697, 2719]，VALID，206.45；2→[1697, 2719]，VALID，237.86。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：82.30 / 79.69；1：0.00 / 不可达；2：103.31 / 100.70。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0347.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0347.png)

### 三点弯 381 · original · raw_only

尖端误差 14.18 px，S1 基座 14.18 px。路径覆盖率 0.94，精确率 0.94。分支 2。端点相对标注横向 -14.2、纵向 -0.2 px。终点由本分支累计得分峰给出。 初始峰 [1727, 2721]，最终 [1727, 2721]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 14.18 px。

分支编号、端点、门控与择优分依次为 0→[1727, 2721]，VALID，232.06；2→[1727, 2721]，VALID，262.77。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：91.66 / 85.37；1：0.00 / 不可达；2：111.97 / 105.68。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0381.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0381.png)

### 三点弯 407 · original · raw_only

尖端误差 27.98 px，S1 基座 27.98 px。路径覆盖率 0.88，精确率 0.91。分支 2。端点相对标注横向 -27.9、纵向 +1.5 px。终点由本分支累计得分峰给出。 初始峰 [1737, 2721]，最终 [1737, 2721]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 27.98 px。

分支编号、端点、门控与择优分依次为 0→[1737, 2721]，VALID，252.36；2→[1737, 2721]，VALID，281.60。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：102.86 / 90.13；1：0.00 / 不可达；2：123.00 / 110.27。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0407.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0407.png)

### 三点弯 476 · original · raw_only

尖端误差 18.54 px，S1 基座 18.54 px。路径覆盖率 0.94，精确率 0.94。分支 2。端点相对标注横向 -18.4、纵向 +2.0 px。终点由本分支累计得分峰给出。 初始峰 [1763, 2722]，最终 [1763, 2722]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 18.54 px。

分支编号、端点、门控与择优分依次为 0→[1763, 2722]，VALID，292.42；2→[1763, 2722]，VALID，318.71。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：122.77 / 122.34；1：0.00 / 不可达；2：142.56 / 142.12。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0476.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/raw_only/0476.png)

### 三点弯 144 · original · full

尖端误差 29.55 px，S1 基座 29.55 px。路径覆盖率 0.60，精确率 1.00。分支 2。端点相对标注横向 -25.8、纵向 +14.5 px。终点由本分支累计得分峰给出。 初始峰 [1506, 2728]，最终 [1506, 2728]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 29.55 px。

分支编号、端点、门控与择优分依次为 0→[1501, 2696]，VALID，9.94；1→[1524, 2705]，INSUFFICIENT_TOTAL，15.94；2→[1506, 2728]，VALID，132.19。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：25.69 / 14.39；1：10.54 / 3.27；2：49.59 / 39.64。桥接诊断 SHORT_RIDGE。

[四栏图](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/full/0144.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/full/0144.png)

### 三点弯 178 · original · full

尖端误差 25.12 px，S1 基座 25.12 px。路径覆盖率 0.78，精确率 0.65。分支 2。端点相对标注横向 +23.6、纵向 -8.6 px。采用下游局部峰。 初始峰 [1520, 2734]，最终 [1563, 2709]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 25.12 px。

分支编号、端点、门控与择优分依次为 0→[1502, 2697]，MOUTH_DEAD_END，41.78；1→[1524, 2705]，INSUFFICIENT_TOTAL，18.93；2→[1563, 2709]，VALID，70.41。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：32.33 / 6.50；1：6.78 / -8.68；2：54.08 / 35.01。桥接诊断 SHORT_RIDGE。

[四栏图](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/full/0178.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/full/0178.png)

### 三点弯 215 · original · full

尖端误差 40.41 px，S1 基座 40.41 px。路径覆盖率 0.68，精确率 0.82。分支 2。端点相对标注横向 -39.0、纵向 -10.6 px。采用下游局部峰。 初始峰 [1520, 2730]，最终 [1566, 2708]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 40.41 px。

分支编号、端点、门控与择优分依次为 0→[1503, 2697]，MOUTH_DEAD_END，42.72；1→[1524, 2705]，INSUFFICIENT_TOTAL，19.84；2→[1566, 2708]，VALID，85.11。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：34.62 / 不可达；1：9.04 / 不可达；2：55.73 / 13.11。桥接诊断 SHORT_RIDGE。

[四栏图](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/full/0215.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/full/0215.png)

### 三点弯 407 · original · full

尖端误差 18.28 px，S1 基座 18.28 px。路径覆盖率 0.97，精确率 0.97。分支 2。端点相对标注横向 -17.9、纵向 +3.5 px。终点由本分支累计得分峰给出。 初始峰 [1747, 2723]，最终 [1747, 2723]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 18.28 px。

分支编号、端点、门控与择优分依次为 0→[1501, 2696]，VALID，10.56；1→[1747, 2723]，VALID，152.44；2→[1747, 2723]，VALID，554.65。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：30.17 / 不可达；1：130.44 / 123.93；2：154.97 / 148.47。桥接诊断 SHORT_RIDGE。

[四栏图](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/full/0407.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/full/0407.png)

### 三点弯 503 · original · full

尖端误差 14.91 px，S1 基座 14.91 px。路径覆盖率 1.00，精确率 0.95。分支 1。端点相对标注横向 +14.0、纵向 +5.0 px。终点由本分支累计得分峰给出。 初始峰 [1801, 2725]，最终 [1801, 2725]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 14.91 px。

分支编号、端点、门控与择优分依次为 0→[1801, 2725]，VALID，493.50；1→[1801, 2725]，VALID，617.25。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：160.75 / 157.70；1：198.80 / 195.75。桥接诊断 SHORT_RIDGE。

[四栏图](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/full/0503.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/three_point_bend/original/full/0503.png)

### 验证组C 38 · original · full

尖端误差 18.15 px，S1 基座 18.15 px。路径覆盖率 0.49，精确率 0.77。分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 18.15 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2293]，INSUFFICIENT_TOTAL，0.28；2→[2273, 2339]，VALID，21.78。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.28 / -20.57；1：0.00 / -18.72；2：21.78 / 18.30。桥接诊断 NO_ATTACHED_SUPPORT。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/original/full/0038.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/original/full/0038.png)

### 验证组C 54 · original · full

尖端误差 12.53 px，S1 基座 12.53 px。路径覆盖率 0.96，精确率 1.00。分支 2。端点相对标注横向 -12.5、纵向 +1.0 px。采用下游局部峰。 初始峰 [2274, 2340]，最终 [2289, 2332]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 12.53 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2294]，INSUFFICIENT_TOTAL，0.52；1→[2267, 2303]，MOUTH_DEAD_END，2.30；2→[2289, 2332]，VALID，35.53。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.52 / -29.31；1：2.30 / -22.62；2：22.05 / 21.13。桥接诊断 NO_ATTACHED_SUPPORT。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/original/full/0054.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/original/full/0054.png)

### 验证组C 38 · original · raw_only

尖端误差 18.15 px，S1 基座 18.15 px。路径覆盖率 0.49，精确率 0.77。分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 18.15 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2293]，INSUFFICIENT_TOTAL，0.93；2→[2273, 2339]，VALID，34.19。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.28 / 不可达；1：0.00 / 不可达；2：17.94 / 14.90。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0038.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0038.png)

### 验证组C 54 · original · raw_only

尖端误差 28.94 px，S1 基座 28.94 px。路径覆盖率 0.44，精确率 0.93。分支 2。端点相对标注横向 -27.5、纵向 +9.0 px。终点由本分支累计得分峰给出。 初始峰 [2274, 2340]，最终 [2274, 2340]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 28.94 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2294]，INSUFFICIENT_TOTAL，1.82；1→[2267, 2304]，INSUFFICIENT_TOTAL，6.57；2→[2274, 2340]，VALID，33.46。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.52 / 不可达；1：2.02 / 不可达；2：17.86 / 13.21。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0054.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0054.png)

### 验证组C 69 · original · raw_only

尖端误差 13.62 px，S1 基座 13.62 px。路径覆盖率 0.94，精确率 0.93。分支 2。端点相对标注横向 -13.6、纵向 +0.6 px。终点由本分支累计得分峰给出。 初始峰 [2290, 2332]，最终 [2290, 2332]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 13.62 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2294]，INSUFFICIENT_TOTAL，2.35；1→[2267, 2304]，INSUFFICIENT_TOTAL，6.14；2→[2290, 2332]，VALID，41.52。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：1.05 / 不可达；1：1.59 / 不可达；2：18.12 / 17.31。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0069.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0069.png)

### 验证组C 95 · original · raw_only

尖端误差 25.25 px，S1 基座 25.25 px。路径覆盖率 0.81，精确率 0.96。分支 2。端点相对标注横向 -24.6、纵向 -5.6 px。终点由本分支累计得分峰给出。 初始峰 [2303, 2331]，最终 [2303, 2331]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 25.25 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2294]，INSUFFICIENT_TOTAL，1.02；1→[2303, 2331]，VALID，48.54；2→[2303, 2331]，VALID，49.43。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.37 / 不可达；1：19.94 / 13.31；2：21.48 / 14.85。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0095.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0095.png)

### 验证组C 232 · original · raw_only

尖端误差 12.02 px，S1 基座 12.02 px。路径覆盖率 0.99，精确率 1.00。分支 1。端点相对标注横向 -12.0、纵向 +0.7 px。终点由本分支累计得分峰给出。 初始峰 [2408, 2345]，最终 [2408, 2345]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 12.02 px。

分支编号、端点、门控与择优分依次为 0→[2249, 2296]，INSUFFICIENT_TOTAL，0.84；1→[2408, 2345]，VALID，214.85；2→[2274, 2342]，INSUFFICIENT_TOTAL，19.60。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.19 / 不可达；1：114.10 / 111.24；2：9.20 / 不可达。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0232.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0232.png)

### 验证组C 324 · original · raw_only

尖端误差 27.53 px，S1 基座 27.53 px。路径覆盖率 1.00，精确率 0.93。分支 1。端点相对标注横向 +22.3、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 27.53 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2296]，INSUFFICIENT_TOTAL，1.75；1→[2486, 2330]，VALID，316.63；2→[2274, 2343]，INSUFFICIENT_TOTAL，19.05。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.45 / 不可达；1：167.13 / 164.29；2：8.65 / 不可达。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0324.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0324.png)

### 验证组C 335 · original · raw_only

尖端误差 23.40 px，S1 基座 23.40 px。路径覆盖率 1.00，精确率 0.94。分支 1。端点相对标注横向 +16.8、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2487, 2329]，最终 [2487, 2329]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 23.40 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2296]，INSUFFICIENT_TOTAL，2.88；1→[2487, 2329]，VALID，322.55；2→[2274, 2343]，INSUFFICIENT_TOTAL，20.19。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.93 / 不可达；1：171.10 / 168.42；2：9.14 / 不可达。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0335.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0335.png)

### 验证组C 345 · original · raw_only

尖端误差 20.10 px，S1 基座 20.10 px。路径覆盖率 1.00，精确率 0.95。分支 1。端点相对标注横向 +12.5、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 20.10 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2297]，INSUFFICIENT_TOTAL，1.59；1→[2486, 2330]，VALID，322.37；2→[2274, 2343]，INSUFFICIENT_TOTAL，18.74。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.29 / 不可达；1：171.57 / 169.41；2：8.34 / 不可达。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0345.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0345.png)

### 验证组C 363 · original · raw_only

尖端误差 16.12 px，S1 基座 16.12 px。路径覆盖率 0.99，精确率 0.96。分支 2。端点相对标注横向 +3.0、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 16.12 px。

分支编号、端点、门控与择优分依次为 0→[2249, 2298]，INSUFFICIENT_TOTAL，1.02；1→[2267, 2307]，INSUFFICIENT_TOTAL，6.83；2→[2486, 2330]，VALID，324.36。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.37 / 不可达；1：1.63 / 不可达；2：172.26 / 170.62。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0363.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/original/raw_only/0363.png)

### 验证组C 38 · bright · full

尖端误差 18.15 px，S1 基座 18.15 px。路径覆盖率 0.49，精确率 0.77。分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 18.15 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2293]，INSUFFICIENT_TOTAL，0.28；2→[2273, 2339]，VALID，21.78。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.28 / -20.57；1：0.00 / -18.72；2：21.78 / 18.30。桥接诊断 NO_ATTACHED_SUPPORT。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/bright/full/0038.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/bright/full/0038.png)

### 验证组C 54 · bright · full

尖端误差 12.53 px，S1 基座 12.53 px。路径覆盖率 0.96，精确率 1.00。分支 2。端点相对标注横向 -12.5、纵向 +1.0 px。采用下游局部峰。 初始峰 [2274, 2340]，最终 [2289, 2332]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 12.53 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2294]，INSUFFICIENT_TOTAL，0.52；1→[2267, 2303]，MOUTH_DEAD_END，2.30；2→[2289, 2332]，VALID，35.53。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.52 / -29.31；1：2.30 / -22.62；2：22.05 / 21.13。桥接诊断 NO_ATTACHED_SUPPORT。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/bright/full/0054.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/bright/full/0054.png)

### 验证组C 38 · bright · raw_only

尖端误差 18.15 px，S1 基座 18.15 px。路径覆盖率 0.49，精确率 0.77。分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 18.15 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2293]，INSUFFICIENT_TOTAL，0.93；2→[2273, 2339]，VALID，34.19。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.28 / 不可达；1：0.00 / 不可达；2：17.94 / 14.90。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0038.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0038.png)

### 验证组C 54 · bright · raw_only

尖端误差 28.94 px，S1 基座 28.94 px。路径覆盖率 0.44，精确率 0.93。分支 2。端点相对标注横向 -27.5、纵向 +9.0 px。终点由本分支累计得分峰给出。 初始峰 [2274, 2340]，最终 [2274, 2340]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 28.94 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2294]，INSUFFICIENT_TOTAL，1.82；1→[2267, 2304]，INSUFFICIENT_TOTAL，6.57；2→[2274, 2340]，VALID，33.46。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.52 / 不可达；1：2.02 / 不可达；2：17.86 / 13.21。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0054.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0054.png)

### 验证组C 69 · bright · raw_only

尖端误差 13.62 px，S1 基座 13.62 px。路径覆盖率 0.94，精确率 0.93。分支 2。端点相对标注横向 -13.6、纵向 +0.6 px。终点由本分支累计得分峰给出。 初始峰 [2290, 2332]，最终 [2290, 2332]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 13.62 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2294]，INSUFFICIENT_TOTAL，2.35；1→[2267, 2304]，INSUFFICIENT_TOTAL，6.14；2→[2290, 2332]，VALID，41.52。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：1.05 / 不可达；1：1.59 / 不可达；2：18.12 / 17.31。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0069.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0069.png)

### 验证组C 95 · bright · raw_only

尖端误差 25.25 px，S1 基座 25.25 px。路径覆盖率 0.81，精确率 0.96。分支 2。端点相对标注横向 -24.6、纵向 -5.6 px。终点由本分支累计得分峰给出。 初始峰 [2303, 2331]，最终 [2303, 2331]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 25.25 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2294]，INSUFFICIENT_TOTAL，1.02；1→[2303, 2331]，VALID，48.54；2→[2303, 2331]，VALID，49.43。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.37 / 不可达；1：19.94 / 13.31；2：21.48 / 14.85。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0095.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0095.png)

### 验证组C 232 · bright · raw_only

尖端误差 12.02 px，S1 基座 12.02 px。路径覆盖率 0.99，精确率 1.00。分支 1。端点相对标注横向 -12.0、纵向 +0.7 px。终点由本分支累计得分峰给出。 初始峰 [2408, 2345]，最终 [2408, 2345]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 12.02 px。

分支编号、端点、门控与择优分依次为 0→[2249, 2296]，INSUFFICIENT_TOTAL，0.84；1→[2408, 2345]，VALID，214.85；2→[2274, 2342]，INSUFFICIENT_TOTAL，19.60。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.19 / 不可达；1：114.10 / 111.24；2：9.20 / 不可达。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0232.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0232.png)

### 验证组C 324 · bright · raw_only

尖端误差 27.53 px，S1 基座 27.53 px。路径覆盖率 1.00，精确率 0.93。分支 1。端点相对标注横向 +22.3、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 27.53 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2296]，INSUFFICIENT_TOTAL，1.75；1→[2486, 2330]，VALID，316.63；2→[2274, 2343]，INSUFFICIENT_TOTAL，19.05。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.45 / 不可达；1：167.13 / 164.29；2：8.65 / 不可达。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0324.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0324.png)

### 验证组C 335 · bright · raw_only

尖端误差 23.40 px，S1 基座 23.40 px。路径覆盖率 1.00，精确率 0.94。分支 1。端点相对标注横向 +16.8、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2487, 2329]，最终 [2487, 2329]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 23.40 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2296]，INSUFFICIENT_TOTAL，2.88；1→[2487, 2329]，VALID，322.55；2→[2274, 2343]，INSUFFICIENT_TOTAL，20.19。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.93 / 不可达；1：171.10 / 168.42；2：9.14 / 不可达。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0335.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0335.png)

### 验证组C 345 · bright · raw_only

尖端误差 20.10 px，S1 基座 20.10 px。路径覆盖率 1.00，精确率 0.95。分支 1。端点相对标注横向 +12.5、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 20.10 px。

分支编号、端点、门控与择优分依次为 0→[2250, 2297]，INSUFFICIENT_TOTAL，1.59；1→[2486, 2330]，VALID，322.37；2→[2274, 2343]，INSUFFICIENT_TOTAL，18.74。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.29 / 不可达；1：171.57 / 169.41；2：8.34 / 不可达。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0345.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0345.png)

### 验证组C 363 · bright · raw_only

尖端误差 16.12 px，S1 基座 16.12 px。路径覆盖率 0.99，精确率 0.96。分支 2。端点相对标注横向 +3.0、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 所有合格分支端点均在 10 px 外。 最接近标注的合格端点误差 16.12 px。

分支编号、端点、门控与择优分依次为 0→[2249, 2298]，INSUFFICIENT_TOTAL，1.02；1→[2267, 2307]，INSUFFICIENT_TOTAL，6.83；2→[2486, 2330]，VALID，324.36。各分支曲线的全局峰值 / 人工尖端所在列最大值为 0：0.37 / 不可达；1：1.63 / 不可达；2：172.26 / 170.62。桥接诊断 无差分桥接。

[四栏图](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0363.jpg) · [分支累计得分曲线](../../output/experiments/v510_vertex_r02/failures/group_c/bright/raw_only/0363.png)

## 下一轮可验证的假设

在合成图或开发组A中构造同一入口内部分叉，并检查截断前能否同时生成两个不同端点。对弱中段记录从当前峰到下游峰的可达曲面、掩膜断点和累计分首次转负的位置。用已有短尾与材料边界阴性探针同时回归，保留当前验证组作冻结后的测评。
