# V5.11 失败帧与性能审计

以冻结 V5.10 r02 为基座。S4 可见帧 Joint 为 41/54，基线为 46/54。验证组C两种点位使用同一批图像，在总数中仅计一次。共运行 1,633 张原图。开发组A用于开发，三点弯和验证组C均在配置冻结后顺序运行，均为已接触的验证数据。排除组X排除。人工标注仅作封存后的评分与误差诊断。

## S1–S4 消融复核

每组抽取 20 个标注帧，合计 54 帧有可见尖端。真实帧误差为原图欧氏距离。Hit@5/10 按像素判定，Joint 同时要求 10 px 邻域路径覆盖率、精确率均 ≥80%，Severe 为有定位且误差 >100 px。无预测计入可见分母。消融速度为相同 20 帧的调用数除以算法累计时间；下表另列完整序列速度，均不含读盘、评分或视频编码。

| 阶段 | 数据及点位 | 可见 | Hit@5 | Hit@10 | Joint | Severe | 20 帧 full FPS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | 开发组A | 19 | 12 | 18 | 18 | 0 | 13.16 |
| S1 | 三点弯 | 15 | 5 | 10 | 10 | 0 | 2.40 |
| S1 | 验证组C 原点 | 20 | 15 | 18 | 18 | 0 | 25.35 |
| S1 | 验证组C 亮区 | 20 | 15 | 18 | 18 | 0 | 25.76 |
| S2 | 开发组A | 19 | 12 | 18 | 18 | 0 | 13.35 |
| S2 | 三点弯 | 15 | 6 | 11 | 9 | 0 | 2.47 |
| S2 | 验证组C 原点 | 20 | 16 | 19 | 19 | 0 | 25.81 |
| S2 | 验证组C 亮区 | 20 | 16 | 19 | 19 | 0 | 25.19 |
| S3 | 开发组A | 19 | 12 | 18 | 18 | 0 | 13.02 |
| S3 | 三点弯 | 15 | 6 | 11 | 9 | 0 | 2.55 |
| S3 | 验证组C 原点 | 20 | 16 | 18 | 18 | 0 | 21.49 |
| S3 | 验证组C 亮区 | 20 | 16 | 18 | 18 | 0 | 21.59 |
| S4 | 开发组A | 19 | 13 | 18 | 18 | 0 | 13.58 |
| S4 | 三点弯 | 15 | 5 | 11 | 9 | 0 | 3.89 |
| S4 | 验证组C 原点 | 20 | 15 | 18 | 18 | 0 | 21.44 |
| S4 | 验证组C 亮区 | 20 | 12 | 14 | 14 | 3 | 12.18 |

| 组别 | 序列帧 | full FPS | raw_only FPS |
| --- | --- | --- | --- |
| 开发组A | 551 | 11.71 | 51.99 |
| 三点弯 | 520 | 3.62 | 14.81 |
| 验证组C 原点 | 562 | 20.47 | 61.63 |
| 验证组C 亮区 | 562 | 17.51 | 60.97 |

## 合成与基准点扰动

| 阶段 | 合成类别 | 样本 | Hit@5 | Hit@10 | Joint | Severe | 场景验收通过 | 误报 | FPS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | 全部阳性 | 936 | 823 | 866 | 832 | 0 | 862 | — | 19.86 |
| S1 | P1_weak_gap | 216 | 216 | 216 | 216 | 0 | 216 | — | 30.62 |
| S1 | weak_material_bridge | 36 | 0 | 0 | 0 | 0 | 0 | — | 76.23 |
| S1 | active_fork | 36 | 30 | 30 | 30 | 0 | 30 | — | 31.38 |
| S1 | 全部阴性 | 468 | — | — | — | — | 468 | 0 | 33.05 |
| S2 | 全部阳性 | 936 | 786 | 809 | 775 | 0 | 805 | — | 28.57 |
| S2 | P1_weak_gap | 216 | 216 | 216 | 216 | 0 | 216 | — | 30.16 |
| S2 | weak_material_bridge | 36 | 0 | 0 | 0 | 0 | 0 | — | 75.77 |
| S2 | active_fork | 36 | 30 | 30 | 30 | 0 | 30 | — | 30.75 |
| S2 | 全部阴性 | 468 | — | — | — | — | 468 | 0 | 32.82 |
| S3 | 全部阳性 | 936 | 822 | 845 | 811 | 0 | 841 | — | 28.11 |
| S3 | P1_weak_gap | 216 | 216 | 216 | 216 | 0 | 216 | — | 30.64 |
| S3 | weak_material_bridge | 36 | 36 | 36 | 36 | 0 | 36 | — | 35.62 |
| S3 | active_fork | 36 | 30 | 30 | 30 | 0 | 30 | — | 30.64 |
| S3 | 全部阴性 | 468 | — | — | — | — | 468 | 0 | 32.41 |
| S4 | 全部阳性 | 936 | 822 | 845 | 811 | 0 | 841 | — | 27.26 |
| S4 | P1_weak_gap | 216 | 216 | 216 | 216 | 0 | 216 | — | 31.33 |
| S4 | weak_material_bridge | 36 | 36 | 36 | 36 | 0 | 36 | — | 37.43 |
| S4 | active_fork | 36 | 30 | 30 | 30 | 0 | 30 | — | 31.85 |
| S4 | 全部阴性 | 468 | — | — | — | — | 468 | 0 | 34.03 |

| 组别 | 输入 | 扰动数 | 双端点可比 | 状态/有无变化 | 最大漂移 px | 对应帧 | 可见帧最大 px |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | 固定配准 | 200 | 190 | 0 | 0.00 | 67 | 0.00 |
| 开发组A | 重裁剪重配准 | 200 | 190 | 0 | 0.00 | 67 | 0.00 |
| 三点弯 | 固定配准 | 200 | 200 | 0 | 0.00 | 1 | 0.00 |
| 三点弯 | 重裁剪重配准 | 200 | 200 | 0 | 13.60 | 120 | 0.00 |
| 验证组C | 固定配准 | 200 | 200 | 0 | 0.00 | 1 | 0.00 |
| 验证组C | 重裁剪重配准 | 200 | 200 | 0 | 215.13 | 221 | 215.13 |

## 冻结后参考映射对照

封存后固定 S4 检测代码、当前帧、裁框、点位和参数，仅替换上游配准参考，80/80 组帧与点位复现了 S3 的端点（含无输出）。下表列出验证组C亮区新增错误。[全部对照](../../output/experiments/v511_diff_unblock_r02/reference_intervention.csv)

| 验证组C亮区帧 | S3 尖端 | S4 尖端 | 仅换回原参考映射的 S4 |
| --- | --- | --- | --- |
| 232 | [2420, 2345] | [2452, 2320] | [2420, 2345] |
| 324 | [2471, 2345] | [2622, 2398] | [2471, 2345] |
| 335 | [2472, 2345] | [2611, 2400] | [2472, 2345] |
| 345 | [2474, 2346] | [2622, 2399] | [2474, 2346] |

## 目标帧证据

验证组C 54 在 S2 首次命中。验证组C 38 的原点历史末段在 S1 已恢复 15/16 列，但 S4 亮区仍只有第 2 分支有效，第 0 分支没有通过总分门槛。支持列存在不保证入口至尖端的整条分支能晋级。三点弯 215 在 S1 已恢复 37/37 列，S2 首次命中尖端；S4 覆盖率 77.7%、精确率 79.3%。三点弯 248 从 S2 起失去 Joint，S4 尖端误差 2.20 px，路径覆盖率 60.8%、精确率 63.2%。306、413、435 的 S4 均保持 Joint，末端横向偏差分别为 +2.48、+6.21、+5.40 px。验证组C 510 在 S3 首次失去 Joint。215 和 248 从 S2 起均选中保送的第 1 分支，原第 2 分支仍合格。两帧在 S4 的第 1/2 分支排名分分别为 338.3/313.5 与 426.5/372.6。合成 P6_isolated 的场景通过数从 S1 的 36/36 降至 S2 的 0/36，P6_deformed_scratch 从 23/36 降至 2/36；S3、S4 仍保留这两项退化。

| 组别 | 帧 | 点位 | V5.10 误差 | S1 | S2 | S3 | S4 | S4 Δx | S4 分支 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | 299 | original | 0.44 | 0.44 | 0.44 | 0.44 | 0.44 | 0.30 | BRANCH_0 |
| 三点弯 | 215 | original | 40.41 | 40.41 | 0.43 | 0.43 | 6.03 | 6.00 | BRANCH_1 |
| 三点弯 | 248 | original | 4.63 | 4.63 | 3.20 | 3.20 | 2.20 | 0.08 | BRANCH_1 |
| 三点弯 | 306 | original | 2.49 | 2.49 | 2.49 | 2.49 | 2.49 | 2.48 | BRANCH_2 |
| 三点弯 | 413 | original | 6.43 | 6.43 | 6.43 | 6.43 | 6.43 | 6.21 | BRANCH_2 |
| 三点弯 | 435 | original | 5.49 | 5.49 | 5.49 | 5.49 | 5.49 | 5.40 | BRANCH_2 |
| 验证组C | 1 | original | 1.26 | 1.26 | 1.26 | 1.26 | 1.26 | -1.18 | BRANCH_2 |
| 验证组C | 1 | bright | 1.26 | 1.26 | 1.26 | 1.26 | 1.26 | -1.18 | BRANCH_2 |
| 验证组C | 7 | original | 0.84 | 0.84 | 0.84 | 0.84 | 0.84 | -0.03 | BRANCH_2 |
| 验证组C | 7 | bright | 0.84 | 0.84 | 0.84 | 0.84 | 2.14 | 1.97 | BRANCH_2 |
| 验证组C | 38 | original | 18.15 | 18.15 | 18.15 | 18.15 | 18.15 | -16.46 | BRANCH_2 |
| 验证组C | 38 | bright | 18.15 | 18.15 | 18.15 | 18.15 | 18.15 | -16.46 | BRANCH_2 |
| 验证组C | 54 | original | 12.53 | 18.51 | 0.49 | 0.49 | 1.51 | 1.51 | BRANCH_2 |
| 验证组C | 54 | bright | 12.53 | 18.51 | 0.49 | 0.49 | 0.49 | -0.49 | BRANCH_2 |

| 组别 | 帧 | 点位 | 阶段 | 区段列数 | 红差分 | 细脊 | 暗谷 | 保留列 | 最长连续 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 三点弯 | 215 | original | V5.10 | 37 | 37 | 37 | 37 | 16 | 11 |
| 三点弯 | 215 | original | S1 | 37 | 37 | 37 | 37 | 37 | 37 |
| 三点弯 | 215 | original | S2 | 37 | 37 | 37 | 37 | 37 | 37 |
| 三点弯 | 215 | original | S3 | 37 | 37 | 37 | 37 | 37 | 37 |
| 三点弯 | 215 | original | S4 | 37 | 37 | 37 | 37 | 37 | 37 |
| 验证组C | 38 | original | V5.10 | 16 | 16 | 15 | 16 | 6 | 4 |
| 验证组C | 38 | original | S1 | 16 | 16 | 15 | 16 | 15 | 13 |
| 验证组C | 38 | original | S2 | 16 | 16 | 15 | 16 | 15 | 13 |
| 验证组C | 38 | original | S3 | 16 | 16 | 15 | 16 | 15 | 13 |
| 验证组C | 38 | original | S4 | 16 | 16 | 16 | 16 | 16 | 16 |
| 验证组C | 38 | bright | V5.10 | 16 | 16 | 15 | 16 | 6 | 4 |
| 验证组C | 38 | bright | S1 | 16 | 16 | 15 | 16 | 15 | 13 |
| 验证组C | 38 | bright | S2 | 16 | 16 | 15 | 16 | 15 | 13 |
| 验证组C | 38 | bright | S3 | 16 | 16 | 15 | 16 | 15 | 13 |
| 验证组C | 38 | bright | S4 | 16 | 16 | 16 | 16 | 16 | 16 |
| 验证组C | 54 | original | V5.10 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | original | S1 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | original | S2 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | original | S3 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | original | S4 | 12 | 11 | 12 | 12 | 11 | 9 |
| 验证组C | 54 | bright | V5.10 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | bright | S1 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | bright | S2 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | bright | S3 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | bright | S4 | 12 | 12 | 12 | 12 | 12 | 12 |

按同一 V5.10 端点后人工标注路径取样，纵向容差 ±2 px。通过列表示该列五个像素内至少一个满足对应条件，各条件可能来自不同像素。保留列要求同一像素同时具备红色差分并通过静态与偶极子筛选。

## 三点弯模块计时

同组 20 个原始输入，预热后逐帧配对，同一进程、单 OpenCV 线程，单位为平均毫秒。嵌套调用按独占时间归属；V5.10 直接读缓存的上游映射。此项用于定位耗时，全序列 FPS 见前表。

| 模块 | V5.10 ms/帧 | S4 ms/帧 | 变化 ms |
| --- | --- | --- | --- |
| 缺口与 ROI 准备 | 10.23 | 10.34 | 0.11 |
| 材料坐标参考重映射 | 0.00 | 12.84 | 12.84 |
| 证据场及局部配准 | 145.16 | 115.94 | -29.22 |
| 差分形态及偶极子邻域 | 74.65 | 16.65 | -58.00 |
| 动态规划内核 | 3.35 | 2.63 | -0.72 |
| 下游峰 | 8.90 | 1.17 | -7.73 |
| 桥接 | 0.15 | 0.27 | 0.12 |
| 其余 | 6.03 | 3.47 | -2.56 |
| 单帧合计 | 248.46 | 163.31 | -85.15 |

单独配对计时中，V5.10 为 248.46 ms/帧、S4 为 163.31 ms/帧，S4 折合 6.12 FPS。全序列批量评测使用四个工作进程，以单次调用耗时汇总，实测 3.62 FPS。两次测量的处理器竞争与样本范围不同，验收采用全序列结果。

## 全部可见失败帧

每个 full 与 raw_only 失败分别列出，涵盖验证组C两套点位。表内为通过列数/可评列数，偶极放行表示该列搜索带存在通过偶极筛选的像素。raw_only 的差分指标来自同点位配套参考，是诊断对照。无可信差分配准时按零局部位移重放，证据不能解释为运行时采用。[逐列原始标志](../../output/experiments/v511_diff_unblock_r02/individual_columns.csv)

### 开发组A · original · full

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 398 | 12.10 | 1.00/0.99 | 多追预测段 1326–1337 | 12 | 8/11/8/12/7 | 4 | BRANCH_0；0 VALID 总分 391.93→391.93，排名分 896.08 | 分支 0。端点相对标注横向 +11.8、纵向 +2.4 px。终点由本分支累计得分峰给出。 初始峰 [1337, 1164]，最终 [1337, 1164]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_a/original/full/0398.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_a/original/full/0398.png) |

### 开发组A · original · raw_only

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 398 | 12.10 | 1.00/0.99 | 多追预测段 1326–1337 | 12 | 8/11/8/12/7 | 4 | BRANCH_0；0 VALID 总分 —→272.39，排名分 513.54 | 分支 0。端点相对标注横向 +11.8、纵向 +2.4 px。终点由本分支累计得分峰给出。 初始峰 [1337, 1164]，最终 [1337, 1164]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_a/original/raw_only/0398.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_a/original/raw_only/0398.png) |
| 504 | 20.97 | 0.97/1.00 | 漏追人工段 1360–1379 | 20 | 11/3/11/20/3 | 3 | BRANCH_0；0 VALID 总分 —→295.23，排名分 551.98 | 分支 0。端点相对标注横向 -21.0、纵向 +0.4 px。终点由本分支累计得分峰给出。 初始峰 [1359, 1159]，最终 [1359, 1159]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_a/original/raw_only/0504.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_a/original/raw_only/0504.png) |

### 三点弯 · original · raw_only

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 96.62 | 0.00/0.00 | 多追预测段 1493–1562 | 70 | 0/0/66/70/0 | 0 | BRANCH_0；0 VALID 总分 —→16.95，排名分 55.95；2 VALID 总分 —→12.46，排名分 23.51 | 分支 0。端点相对标注横向 +69.9、纵向 -66.8 px。终点由本分支累计得分峰给出。 初始峰 [1562, 2665]，最终 [1562, 2665]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0001.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0001.png) |
| 144 | 19.40 | 0.67/0.63 | 多追预测段 1532–1551 | 20 | 1/0/20/20/0 | 0 | BRANCH_2；0 VALID 总分 —→18.33，排名分 58.63；2 VALID 总分 —→23.96，排名分 61.01 | 分支 2。端点相对标注横向 +19.2、纵向 -2.5 px。终点由本分支累计得分峰给出。 初始峰 [1551, 2711]，最终 [1551, 2711]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0144.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0144.png) |
| 178 | 20.94 | 0.78/0.68 | 多追预测段 1540–1558 | 19 | 10/9/19/19/9 | 9 | BRANCH_2；0 VALID 总分 —→17.41，排名分 58.36；2 VALID 总分 —→25.74，排名分 71.24 | 分支 2。端点相对标注横向 +18.6、纵向 -9.6 px。终点由本分支累计得分峰给出。 初始峰 [1558, 2708]，最终 [1558, 2708]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0178.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0178.png) |
| 271 | 22.48 | 0.94/0.98 | 漏追人工段 1641–1661 | 21 | 20/21/20/21/20 | 20 | BRANCH_1；0 VALID 总分 —→28.58，排名分 75.38；1 VALID 总分 —→68.86，排名分 167.01 | 分支 1。端点相对标注横向 -22.2、纵向 +3.5 px。终点由本分支累计得分峰给出。 初始峰 [1640, 2724]，最终 [1640, 2724]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0271.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0271.png) |
| 347 | 14.43 | 0.93/0.93 | 漏追人工段 1698–1711 | 14 | 14/14/14/14/14 | 14 | BRANCH_2；0 VALID 总分 —→82.30，排名分 206.45；2 VALID 总分 —→103.31，排名分 237.86 | 分支 2。端点相对标注横向 -14.3、纵向 -1.9 px。终点由本分支累计得分峰给出。 初始峰 [1697, 2719]，最终 [1697, 2719]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0347.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0347.png) |
| 381 | 14.18 | 0.94/0.94 | 漏追人工段 1728–1741 | 14 | 14/7/12/14/7 | 6 | BRANCH_2；0 VALID 总分 —→91.66，排名分 232.06；2 VALID 总分 —→111.97，排名分 262.77 | 分支 2。端点相对标注横向 -14.2、纵向 -0.2 px。终点由本分支累计得分峰给出。 初始峰 [1727, 2721]，最终 [1727, 2721]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0381.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0381.png) |
| 407 | 27.98 | 0.88/0.91 | 漏追人工段 1738–1764 | 27 | 21/11/22/27/11 | 11 | BRANCH_2；0 VALID 总分 —→102.86，排名分 252.36；2 VALID 总分 —→123.00，排名分 281.60 | 分支 2。端点相对标注横向 -27.9、纵向 +1.5 px。终点由本分支累计得分峰给出。 初始峰 [1737, 2721]，最终 [1737, 2721]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0407.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0407.png) |
| 476 | 18.54 | 0.94/0.94 | 漏追人工段 1764–1781 | 18 | 18/18/18/18/18 | 18 | BRANCH_2；0 VALID 总分 —→122.77，排名分 292.42；2 VALID 总分 —→142.56，排名分 318.71 | 分支 2。端点相对标注横向 -18.4、纵向 +2.0 px。终点由本分支累计得分峰给出。 初始峰 [1763, 2722]，最终 [1763, 2722]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0476.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/raw_only/0476.png) |

### 三点弯 · original · full

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 144 | 29.55 | 0.60/1.00 | 漏追人工段 1507–1531 | 25 | 9/7/24/25/6 | 6 | BRANCH_2；0 MOUTH_DEAD_END 总分 26.45→26.45，排名分 34.55；1 INSUFFICIENT_TOTAL 总分 10.55→10.55，排名分 18.65；2 VALID 总分 49.68→49.68，排名分 90.18 | 分支 2。端点相对标注横向 -25.8、纵向 +14.5 px。终点由本分支累计得分峰给出。 初始峰 [1506, 2728]，最终 [1506, 2728]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/full/0144.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/full/0144.png) |
| 178 | 25.12 | 0.78/0.65 | 多追预测段 1540–1563 | 24 | 18/15/23/24/14 | 14 | BRANCH_2；0 MOUTH_DEAD_END 总分 32.33→32.33，排名分 41.78；1 INSUFFICIENT_TOTAL 总分 6.78→6.78，排名分 18.93；2 VALID 总分 54.08→17.06，排名分 70.36 | 分支 2。端点相对标注横向 +23.6、纵向 -8.6 px。采用下游局部峰。 初始峰 [1520, 2734]，最终 [1563, 2709]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/full/0178.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/full/0178.png) |
| 215 | 6.03 | 0.78/0.79 | 端点命中但路径未通过，人工全段 1475–1603 | 129 | 126/120/124/129/115 | 64 | BRANCH_1；0 VALID 总分 31.58→31.58，排名分 11.05，独有红/蓝 0/0；1 VALID 总分 6.83→105.40，排名分 338.31，保送，独有红/蓝 27/2；2 VALID 总分 55.25→24.61，排名分 313.54，独有红/蓝 38/2 | 分支 1。端点相对标注横向 +6.0、纵向 -0.6 px。终点由本分支累计得分峰给出。 初始峰 [1611, 2718]，最终 [1611, 2718]。 尖端已命中，失败来自路径重合度。 [图](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/full/0215.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/full/0215.png) |
| 248 | 2.20 | 0.61/0.63 | 端点命中但路径未通过，人工全段 1473–1629 | 157 | 154/151/156/157/149 | 58 | BRANCH_1；0 VALID 总分 30.11→30.11，排名分 10.54，独有红/蓝 0/0；1 VALID 总分 6.24→135.94，排名分 426.52，保送，独有红/蓝 37/0；2 VALID 总分 55.69→43.95，排名分 372.64，独有红/蓝 45/1 | 分支 1。端点相对标注横向 +0.1、纵向 -2.2 px。终点由本分支累计得分峰给出。 初始峰 [1630, 2723]，最终 [1630, 2723]。 尖端已命中，失败来自路径重合度。 [图](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/full/0248.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/full/0248.png) |
| 407 | 18.28 | 0.97/0.97 | 漏追人工段 1748–1764 | 17 | 11/1/12/17/1 | 1 | BRANCH_2；0 VALID 总分 30.00→30.00，排名分 10.50，独有红/蓝 0/0；1 VALID 总分 130.43→130.43，排名分 533.87，独有红/蓝 26/0；2 VALID 总分 155.24→155.24，排名分 705.48，独有红/蓝 57/2 | 分支 2。端点相对标注横向 -17.9、纵向 +3.5 px。终点由本分支累计得分峰给出。 初始峰 [1747, 2723]，最终 [1747, 2723]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/full/0407.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/full/0407.png) |
| 503 | 14.91 | 1.00/0.95 | 多追预测段 1787–1801 | 15 | 15/15/15/15/15 | 15 | BRANCH_1；0 VALID 总分 161.05→161.05，排名分 493.80，独有红/蓝 26/0；1 VALID 总分 199.28→199.28，排名分 617.73，独有红/蓝 91/0 | 分支 1。端点相对标注横向 +14.0、纵向 +5.0 px。终点由本分支累计得分峰给出。 初始峰 [1801, 2725]，最终 [1801, 2725]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/full/0503.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/three_point_bend/original/full/0503.png) |

### 验证组C · original · full

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 38 | 18.15 | 0.49/0.77 | 漏追人工段 2274–2289 | 16 | 16/16/16/16/16 | 16 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 0.28→0.28，排名分 0.28；2 VALID 总分 21.77→21.77，排名分 21.77 | 分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/full/0038.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/full/0038.png) |
| 510 | 14.96 | 1.00/0.98 | 多追预测段 2491–2505 | 15 | 15/15/15/15/15 | 15 | BRANCH_1；0 MOUTH_DEAD_END 总分 4.65→4.65，排名分 14.65；1 VALID 总分 324.75→324.75，排名分 673.70，独有红/蓝 63/0；2 VALID 总分 233.33→233.33，排名分 505.28，独有红/蓝 10/2 | 分支 1。端点相对标注横向 +14.9、纵向 -0.6 px。终点由本分支累计得分峰给出。 初始峰 [2505, 2345]，最终 [2505, 2345]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/full/0510.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/full/0510.png) |

### 验证组C · original · raw_only

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 38 | 18.15 | 0.49/0.77 | 漏追人工段 2274–2289 | 16 | 16/16/16/16/16 | 16 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.28，排名分 0.93；2 VALID 总分 —→17.94，排名分 34.19 | 分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0038.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0038.png) |
| 54 | 28.94 | 0.44/0.93 | 漏追人工段 2275–2301 | 27 | 26/27/27/27/26 | 17 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.52，排名分 1.82；1 INSUFFICIENT_TOTAL 总分 —→2.02，排名分 6.57；2 VALID 总分 —→17.86，排名分 33.46 | 分支 2。端点相对标注横向 -27.5、纵向 +9.0 px。终点由本分支累计得分峰给出。 初始峰 [2274, 2340]，最终 [2274, 2340]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0054.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0054.png) |
| 69 | 13.62 | 0.94/0.93 | 漏追人工段 2291–2303 | 13 | 13/13/13/13/13 | 13 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→1.05，排名分 2.35；1 INSUFFICIENT_TOTAL 总分 —→1.59，排名分 6.14；2 VALID 总分 —→18.12，排名分 41.52 | 分支 2。端点相对标注横向 -13.6、纵向 +0.6 px。终点由本分支累计得分峰给出。 初始峰 [2290, 2332]，最终 [2290, 2332]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0069.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0069.png) |
| 95 | 25.25 | 0.81/0.96 | 漏追人工段 2304–2327 | 24 | 22/23/24/24/21 | 17 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.37，排名分 1.02；1 VALID 总分 —→19.94，排名分 48.54；2 VALID 总分 —→21.48，排名分 49.43 | 分支 2。端点相对标注横向 -24.6、纵向 -5.6 px。终点由本分支累计得分峰给出。 初始峰 [2303, 2331]，最终 [2303, 2331]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0095.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0095.png) |
| 232 | 12.02 | 0.99/1.00 | 漏追人工段 2409–2420 | 12 | 12/10/12/12/10 | 10 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.19，排名分 0.84；1 VALID 总分 —→114.10，排名分 214.85；2 INSUFFICIENT_TOTAL 总分 —→9.20，排名分 19.60 | 分支 1。端点相对标注横向 -12.0、纵向 +0.7 px。终点由本分支累计得分峰给出。 初始峰 [2408, 2345]，最终 [2408, 2345]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0232.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0232.png) |
| 324 | 27.53 | 1.00/0.93 | 多追预测段 2464–2486 | 23 | 16/11/22/23/11 | 6 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.45，排名分 1.75；1 VALID 总分 —→167.13，排名分 316.63；2 INSUFFICIENT_TOTAL 总分 —→8.65，排名分 19.05 | 分支 1。端点相对标注横向 +22.3、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0324.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0324.png) |
| 335 | 23.40 | 1.00/0.94 | 多追预测段 2471–2487 | 17 | 9/5/16/17/5 | 5 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.93，排名分 2.88；1 VALID 总分 —→171.10，排名分 322.55；2 INSUFFICIENT_TOTAL 总分 —→9.14，排名分 20.19 | 分支 1。端点相对标注横向 +16.8、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2487, 2329]，最终 [2487, 2329]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0335.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0335.png) |
| 345 | 20.10 | 1.00/0.95 | 多追预测段 2474–2486 | 13 | 6/4/13/13/3 | 3 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.29，排名分 1.59；1 VALID 总分 —→171.57，排名分 322.37；2 INSUFFICIENT_TOTAL 总分 —→8.34，排名分 18.74 | 分支 1。端点相对标注横向 +12.5、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0345.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0345.png) |
| 363 | 16.12 | 0.99/0.96 | 多追预测段 2484–2486 | 3 | 2/0/3/3/0 | 0 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.37，排名分 1.02；1 INSUFFICIENT_TOTAL 总分 —→1.63，排名分 6.83；2 VALID 总分 —→172.26，排名分 324.36 | 分支 2。端点相对标注横向 +3.0、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0363.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/original/raw_only/0363.png) |

### 验证组C · bright · full

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 38 | 18.15 | 0.49/0.77 | 漏追人工段 2274–2289 | 16 | 16/16/16/16/16 | 16 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 0.28→0.28，排名分 0.28；2 VALID 总分 21.80→21.80，排名分 21.80 | 分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/full/0038.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/full/0038.png) |
| 232 | 40.17 | 1.00/0.89 | 多追预测段 2421–2452 | 32 | 10/6/21/32/6 | 6 | BRANCH_1；0 MOUTH_DEAD_END 总分 20.16→20.16，排名分 38.11；1 VALID 总分 209.42→199.95，排名分 436.20；2 INSUFFICIENT_TOTAL 总分 11.15→11.15，排名分 13.85 | 分支 1。端点相对标注横向 +32.0、纵向 -24.3 px。采用下游局部峰。 初始峰 [2418, 2345]，最终 [2452, 2320]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/full/0232.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/full/0232.png) |
| 324 | 166.55 | 1.00/0.60 | 多追预测段 2464–2622 | 159 | 70/26/98/159/26 | 8 | BRANCH_1；0 MOUTH_DEAD_END 总分 15.42→15.42，排名分 31.42；1 VALID 总分 278.40→223.68，排名分 546.98，独有红/蓝 65/0；2 VALID 总分 191.22→136.50，排名分 391.60，独有红/蓝 15/2 | 分支 1。端点相对标注横向 +158.3、纵向 +51.8 px。采用下游局部峰。 初始峰 [2486, 2330]，最终 [2622, 2398]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/full/0324.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/full/0324.png) |
| 335 | 151.11 | 1.00/0.63 | 多追预测段 2471–2611 | 141 | 53/23/73/141/20 | 6 | BRANCH_1；0 MOUTH_DEAD_END 总分 17.40→17.40，排名分 32.65；1 VALID 总分 286.06→228.60，排名分 554.50，独有红/蓝 74/0；2 VALID 总分 196.17→138.70，排名分 395.10，独有红/蓝 23/7 | 分支 1。端点相对标注横向 +140.8、纵向 +54.8 px。采用下游局部峰。 初始峰 [2487, 2329]，最终 [2611, 2400]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/full/0335.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/full/0335.png) |
| 345 | 157.75 | 1.00/0.61 | 多追预测段 2474–2622 | 149 | 59/33/80/149/30 | 8 | BRANCH_1；0 MOUTH_DEAD_END 总分 12.71→12.71，排名分 23.96；1 VALID 总分 287.45→237.17，排名分 582.07；2 INSUFFICIENT_TOTAL 总分 8.34→8.34，排名分 8.34 | 分支 1。端点相对标注横向 +148.5、纵向 +53.2 px。采用下游局部峰。 初始峰 [2486, 2330]，最终 [2622, 2399]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/full/0345.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/full/0345.png) |
| 510 | 15.96 | 1.00/0.97 | 多追预测段 2491–2506 | 16 | 16/16/16/16/16 | 16 | BRANCH_1；0 MOUTH_DEAD_END 总分 15.52→15.52，排名分 29.42；1 VALID 总分 326.92→326.92，排名分 675.12，独有红/蓝 64/0；2 VALID 总分 240.92→240.92，排名分 525.67，独有红/蓝 18/1 | 分支 1。端点相对标注横向 +15.9、纵向 -0.6 px。终点由本分支累计得分峰给出。 初始峰 [2506, 2345]，最终 [2506, 2345]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/full/0510.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/full/0510.png) |

### 验证组C · bright · raw_only

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 38 | 18.15 | 0.49/0.77 | 漏追人工段 2274–2289 | 16 | 16/16/16/16/16 | 16 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.28，排名分 0.93；2 VALID 总分 —→17.94，排名分 34.19 | 分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0038.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0038.png) |
| 54 | 28.94 | 0.44/0.93 | 漏追人工段 2275–2301 | 27 | 27/27/27/27/27 | 27 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.52，排名分 1.82；1 INSUFFICIENT_TOTAL 总分 —→2.02，排名分 6.57；2 VALID 总分 —→17.86，排名分 33.46 | 分支 2。端点相对标注横向 -27.5、纵向 +9.0 px。终点由本分支累计得分峰给出。 初始峰 [2274, 2340]，最终 [2274, 2340]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0054.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0054.png) |
| 69 | 13.62 | 0.94/0.93 | 漏追人工段 2291–2303 | 13 | 13/13/13/13/13 | 13 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→1.05，排名分 2.35；1 INSUFFICIENT_TOTAL 总分 —→1.59，排名分 6.14；2 VALID 总分 —→18.12，排名分 41.52 | 分支 2。端点相对标注横向 -13.6、纵向 +0.6 px。终点由本分支累计得分峰给出。 初始峰 [2290, 2332]，最终 [2290, 2332]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0069.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0069.png) |
| 95 | 25.25 | 0.81/0.96 | 漏追人工段 2304–2327 | 24 | 22/22/24/24/19 | 14 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.37，排名分 1.02；1 VALID 总分 —→19.94，排名分 48.54；2 VALID 总分 —→21.48，排名分 49.43 | 分支 2。端点相对标注横向 -24.6、纵向 -5.6 px。终点由本分支累计得分峰给出。 初始峰 [2303, 2331]，最终 [2303, 2331]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0095.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0095.png) |
| 232 | 12.02 | 0.99/1.00 | 漏追人工段 2409–2420 | 12 | 12/10/12/12/10 | 10 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.19，排名分 0.84；1 VALID 总分 —→114.10，排名分 214.85；2 INSUFFICIENT_TOTAL 总分 —→9.20，排名分 19.60 | 分支 1。端点相对标注横向 -12.0、纵向 +0.7 px。终点由本分支累计得分峰给出。 初始峰 [2408, 2345]，最终 [2408, 2345]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0232.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0232.png) |
| 324 | 27.53 | 1.00/0.93 | 多追预测段 2464–2486 | 23 | 13/6/22/23/6 | 6 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.45，排名分 1.75；1 VALID 总分 —→167.13，排名分 316.63；2 INSUFFICIENT_TOTAL 总分 —→8.65，排名分 19.05 | 分支 1。端点相对标注横向 +22.3、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0324.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0324.png) |
| 335 | 23.40 | 1.00/0.94 | 多追预测段 2471–2487 | 17 | 10/6/16/17/6 | 6 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.93，排名分 2.88；1 VALID 总分 —→171.10，排名分 322.55；2 INSUFFICIENT_TOTAL 总分 —→9.14，排名分 20.19 | 分支 1。端点相对标注横向 +16.8、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2487, 2329]，最终 [2487, 2329]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0335.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0335.png) |
| 345 | 20.10 | 1.00/0.95 | 多追预测段 2474–2486 | 13 | 10/10/13/13/8 | 7 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.29，排名分 1.59；1 VALID 总分 —→171.57，排名分 322.37；2 INSUFFICIENT_TOTAL 总分 —→8.34，排名分 18.74 | 分支 1。端点相对标注横向 +12.5、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0345.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0345.png) |
| 363 | 16.12 | 0.99/0.96 | 多追预测段 2484–2486 | 3 | 3/0/3/3/0 | 0 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.37，排名分 1.02；1 INSUFFICIENT_TOTAL 总分 —→1.63，排名分 6.83；2 VALID 总分 —→172.26，排名分 324.36 | 分支 2。端点相对标注横向 +3.0、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 [图](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0363.jpg) [曲线](../../output/experiments/v511_diff_unblock_r02/failures/group_c/bright/raw_only/0363.png) |

## 验收决定

本轮未通过整体验收，继续以 V5.10 作为比较基线。验证组C亮区与原点的结果分离，亮区 324、335、345 产生严重错误。开发组A 299 的十种重配准扰动全部归零，验证组C亮区重配准最大漂移达 215.13 px。三点弯全序列速度仍低于 4 FPS。下一轮宜先在开发材料上构造能复现点对位移梯度变化的对照，验证参考映射引起的远端证据偏移；再用带路径标注的合成分叉区分“尖端命中”和“连接到正确裂纹”。性能优化优先复测证据场和局部配准。

[逐帧四联图与差分 PNG](../../output/experiments/v511_diff_unblock_r02/difference_views/index.html) · [开发组A视频](../../output/experiments/v511_diff_unblock_r02/difference_views/group_a.mp4) · [三点弯视频](../../output/experiments/v511_diff_unblock_r02/difference_views/three_point_bend.mp4) · [验证组C视频](../../output/experiments/v511_diff_unblock_r02/difference_views/group_c.mp4) · [逐帧裂纹长度（px）](../../output/experiments/v511_diff_unblock_r02/crack_lengths.csv) · [主点位失败帧图包](../../output/experiments/v511_diff_unblock_r02/difference_views/failure_views.zip) · [失败审计](FAILURES_AUDIT.md)
