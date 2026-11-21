# V3.2 裂纹尖端追踪算法高精度与普适性验证报告

[交互逐帧图册](../../output/experiments/v32_precision_20261119_r03/index.html) · [1,633 帧识别坐标、状态和图像](../../output/experiments/v32_precision_20261119_r03/frames.csv) · [开发组A视频](../../output/experiments/v32_precision_20261119_r03/group_a.mp4) · [三点弯视频](../../output/experiments/v32_precision_20261119_r03/three_point_bend.mp4) · [验证组C视频](../../output/experiments/v32_precision_20261119_r03/group_c.mp4)

## 1　执行摘要与改动

2026-11-19，冻结版本 v32_precision_20261119_r03。54 张尖端可见的人工标注帧中，完整模式命中 38/54，路径与尖端联合命中 30/54，误差超过 100 px 共 0 帧。另有 6 张标注为不确定，其余 1,573 帧提供识别图与坐标。真实数据缺少独立阴性标注，实际误报率未知。

| 相对 V3.1 r04 的变动 | 判据及保留的诊断 |
|---|---|
| 背景包络 | 分别试验旧背景、逐列 85% 分位与局部均值和全局中值的上包络。原灰度双侧暗谷始终是主证据。 |
| 渐弱终止门 | 三个连续尾窗检查衰减趋势、前方谷深相对噪声底以及主干与末段夹角；对于谷深跌至噪声后又持续回升的候选，在首个合格谷底前截断。强门独立保留。极低采样时允许单列谷底。 |
| 远端防跳接 | 对单向 DP 的临时轨迹逐列检查。在起点 0.35 倍尺度之外，连续约 0.014 倍尺度的归一化响应低于 0.85，或短弱隙两端转向超过 22°，即在候选参与竞争前截断。 |
| 固定参考局部复核 | 完整模式仅复核渐弱认证、发生重连或明显折转的候选。用路径外材料纹理做局部平移 NCC（±0.025 倍尺度）；仅在定位充分且观察到已变化主干与静态相似尾段的边界时回剪、重新认证。 |
| 同唇重连与张口负例 | 沿断带前段切向外推，要求重获窗中位纵向残差 ≤0.012 倍尺度（至少 1 像素），断带两侧谷宽比 ≤2。对短张口外缘联合检查外移方向、起点横截面宽度与开口中心偏距。 |
| 曝光及尺度 | 沿用局部 3% / 70% 分位差、归一化暗谷强度与无量纲长度排序；full 还保留 V3.1 的有界弱差分，raw_only 只使用当前灰度。 |

开发限于开发组A与独立合成图。首轮开发组A 17/19、渐弱探针 9/12。第二轮把单列谷底判据用于全部分辨率，渐弱探针达 10/12，开发组A 217、299 提前截断，联合降至 15/19。最终轮只在谷底统计窗不超过两列时启用该判据，开发组A恢复 17/19，渐弱探针保持 10/12。所有参数在三点弯与验证组C推理前冻结；验证组C执行一次。两组有历史曝光，未取得全新独立盲测集。标签仅用于预测封存后的比较。排除组X未参与。

## 2　分阶段消融

九个预设均在每组同一批 20 张标注帧上比较，V3.2 同时覆盖三组全序列。Hit@10 为原图二维尖端距离 ≤10 px；Joint 另需路径覆盖率与预测点精度均 ≥80%（匹配距离 10 px）。Severe 为误差 >100 px。误差中位与最大值限于有效可见帧。r02 是旧灰度基线，与开发轮号分开。

以 v3_1 为共同起点，background 只改背景，taper_only 只改尾端规则，paired 同时启用两项。随后依次叠加 distal 防跳接、reference 局部参考复核、v3_2 同唇与张口外缘校验。曝光和尺度规则在四格对照中保持一致。

| 组别 | 阶段 | 模式 | 可见/有效 | Hit@10 | Joint | Severe | 中位 px | 最大 px |
|---|---|---|---|---|---|---|---|---|
| 开发组A | r02 | full | 19/19 | 16 | 16 | 0 | 4.92 | 92.06 |
| 开发组A | r02 | raw_only | 19/19 | 16 | 16 | 0 | 4.92 | 92.06 |
| 开发组A | s3t | full | 19/19 | 14 | 14 | 0 | 4.93 | 41.34 |
| 开发组A | s3t | raw_only | 19/19 | 15 | 15 | 0 | 4.55 | 41.34 |
| 开发组A | v3_1 | full | 19/19 | 16 | 16 | 0 | 4.35 | 42.34 |
| 开发组A | v3_1 | raw_only | 19/19 | 16 | 16 | 0 | 4.35 | 42.34 |
| 开发组A | background | full | 19/19 | 15 | 15 | 0 | 5.18 | 42.34 |
| 开发组A | background | raw_only | 19/19 | 15 | 15 | 0 | 5.18 | 42.34 |
| 开发组A | taper_only | full | 19/19 | 15 | 15 | 0 | 4.93 | 42.34 |
| 开发组A | taper_only | raw_only | 19/19 | 15 | 15 | 0 | 4.93 | 42.34 |
| 开发组A | paired | full | 19/19 | 16 | 16 | 0 | 4.13 | 42.34 |
| 开发组A | paired | raw_only | 19/19 | 16 | 16 | 0 | 4.13 | 42.34 |
| 开发组A | distal | full | 19/19 | 17 | 17 | 0 | 4.13 | 14.31 |
| 开发组A | distal | raw_only | 19/19 | 17 | 17 | 0 | 4.13 | 14.31 |
| 开发组A | reference | full | 19/19 | 17 | 17 | 0 | 4.13 | 14.31 |
| 开发组A | reference | raw_only | 19/19 | 17 | 17 | 0 | 4.13 | 14.31 |
| 开发组A | v3_2 | full | 19/19 | 17 | 17 | 0 | 4.13 | 14.31 |
| 开发组A | v3_2 | raw_only | 19/19 | 17 | 17 | 0 | 4.13 | 14.31 |
| 三点弯 | r02 | full | 15/15 | 10 | 1 | 0 | 8.63 | 65.91 |
| 三点弯 | r02 | raw_only | 15/15 | 10 | 2 | 0 | 8.63 | 65.91 |
| 三点弯 | s3t | full | 15/15 | 10 | 1 | 0 | 8.18 | 65.91 |
| 三点弯 | s3t | raw_only | 15/15 | 10 | 1 | 0 | 8.18 | 65.91 |
| 三点弯 | v3_1 | full | 15/15 | 5 | 5 | 0 | 11.61 | 65.91 |
| 三点弯 | v3_1 | raw_only | 15/15 | 5 | 5 | 0 | 11.61 | 65.91 |
| 三点弯 | background | full | 15/15 | 5 | 5 | 0 | 11.61 | 65.91 |
| 三点弯 | background | raw_only | 15/15 | 5 | 5 | 0 | 11.61 | 65.91 |
| 三点弯 | taper_only | full | 15/15 | 8 | 8 | 0 | 8.58 | 65.91 |
| 三点弯 | taper_only | raw_only | 15/15 | 8 | 8 | 0 | 8.58 | 65.91 |
| 三点弯 | paired | full | 15/15 | 8 | 8 | 0 | 8.58 | 65.91 |
| 三点弯 | paired | raw_only | 15/15 | 8 | 8 | 0 | 8.58 | 65.91 |
| 三点弯 | distal | full | 15/15 | 9 | 9 | 0 | 8.63 | 65.91 |
| 三点弯 | distal | raw_only | 15/15 | 9 | 9 | 0 | 8.63 | 65.91 |
| 三点弯 | reference | full | 15/15 | 9 | 9 | 0 | 8.63 | 65.91 |
| 三点弯 | reference | raw_only | 15/15 | 9 | 9 | 0 | 8.63 | 65.91 |
| 三点弯 | v3_2 | full | 15/15 | 9 | 1 | 0 | 9.16 | 65.91 |
| 三点弯 | v3_2 | raw_only | 15/15 | 9 | 1 | 0 | 9.16 | 65.91 |
| 验证组C | r02 | full | 20/20 | 6 | 6 | 0 | 14.52 | 39.42 |
| 验证组C | r02 | raw_only | 20/20 | 6 | 6 | 0 | 14.52 | 39.42 |
| 验证组C | s3t | full | 20/20 | 13 | 13 | 0 | 5.86 | 30.64 |
| 验证组C | s3t | raw_only | 20/20 | 13 | 13 | 0 | 5.86 | 30.64 |
| 验证组C | v3_1 | full | 20/20 | 10 | 9 | 0 | 10.94 | 52.82 |
| 验证组C | v3_1 | raw_only | 20/20 | 10 | 9 | 0 | 10.94 | 52.82 |
| 验证组C | background | full | 20/20 | 11 | 10 | 0 | 9.64 | 42.88 |
| 验证组C | background | raw_only | 20/20 | 11 | 10 | 0 | 9.64 | 42.88 |
| 验证组C | taper_only | full | 20/20 | 11 | 11 | 0 | 8.80 | 42.88 |
| 验证组C | taper_only | raw_only | 20/20 | 11 | 11 | 0 | 8.80 | 42.88 |
| 验证组C | paired | full | 20/20 | 12 | 12 | 0 | 7.61 | 42.88 |
| 验证组C | paired | raw_only | 20/20 | 12 | 12 | 0 | 7.61 | 42.88 |
| 验证组C | distal | full | 20/20 | 12 | 12 | 0 | 8.20 | 30.64 |
| 验证组C | distal | raw_only | 20/20 | 12 | 12 | 0 | 8.20 | 30.64 |
| 验证组C | reference | full | 20/20 | 12 | 12 | 0 | 8.20 | 30.64 |
| 验证组C | reference | raw_only | 20/20 | 12 | 12 | 0 | 8.20 | 30.64 |
| 验证组C | v3_2 | full | 20/20 | 12 | 12 | 0 | 8.20 | 30.64 |
| 验证组C | v3_2 | raw_only | 20/20 | 12 | 12 | 0 | 8.20 | 30.64 |

原图摘要逐帧核对；对 60 张标注帧的三个历史基线、两种模式，360 条状态、起点、尖端和路径与封存结果逐点一致。[指标表](../../output/experiments/v32_precision_20261119_r03/ablation_metrics.csv) · [冻结清单](../../output/experiments/v32_precision_20261119_r03/freeze.json)

## 3　反例、逐帧归因与新增受损帧

下表为 full 模式二维误差（px），最终偏差是预测减人工。最后一列记录单独改变背景或尾端规则能否使旧漏检重新进入 10 px 容差；算法路径和排名也可能随规则改变。

| 帧 | v3_1 | background | taper_only | paired | distal | reference | v3_2 | 最终 dx / dy | 最终结果 | 四格对照 |
|---|---|---|---|---|---|---|---|---|---|---|
| [开发组A 366](../../output/experiments/v32_precision_20261119_r03/labels/group_a/366.png) | 1.15 | 11.37 | 13.17 | 11.37 | 14.31 | 14.31 | 14.31 | -14.07 / 2.58 | 尖端提前 | 原已命中 |
| [开发组A 451](../../output/experiments/v32_precision_20261119_r03/labels/group_a/451.png) | 3.92 | 3.92 | 3.92 | 3.92 | 3.12 | 3.12 | 3.12 | -3.10 / -0.39 | 联合命中 | 原已命中 |
| [开发组A 504](../../output/experiments/v32_precision_20261119_r03/labels/group_a/504.png) | 5.18 | 5.18 | 19.02 | 19.02 | 14.18 | 14.18 | 14.18 | -13.97 / 2.45 | 尖端提前 | 原已命中 |
| [开发组A 542](../../output/experiments/v32_precision_20261119_r03/labels/group_a/542.png) | 0.64 | 0.64 | 0.64 | 0.64 | 2.95 | 2.95 | 2.95 | -2.93 / 0.36 | 联合命中 | 原已命中 |
| [三点弯 215](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/215.png) | 7.02 | 7.02 | 2.08 | 2.08 | 2.08 | 2.08 | 2.08 | -2.00 / -0.57 | 尖端命中、路径未达标 | 原已命中 |
| [三点弯 248](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/248.png) | 10.15 | 10.15 | 10.15 | 10.15 | 9.16 | 9.16 | 9.16 | 9.08 / -1.20 | 尖端命中、路径未达标 | 两项均未恢复 |
| [三点弯 335](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/335.png) | 12.47 | 12.47 | 10.55 | 10.55 | 10.55 | 10.55 | 10.55 | 10.04 / -3.23 | 向右过冲 | 两项均未恢复 |
| [三点弯 413](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/413.png) | 16.42 | 16.42 | 7.24 | 7.24 | 13.22 | 13.22 | 13.22 | 13.21 / -0.66 | 向右过冲 | 仅尾门单改恢复 |
| [三点弯 435](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/435.png) | 12.76 | 12.76 | 1.71 | 1.71 | 1.71 | 1.71 | 1.71 | 1.40 / -0.98 | 尖端命中、路径未达标 | 仅尾门单改恢复 |
| [三点弯 476](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/476.png) | 11.61 | 11.61 | 11.61 | 11.61 | 8.63 | 8.63 | 8.63 | 8.57 / -1.00 | 联合命中 | 两项均未恢复 |
| [验证组C 69](../../output/experiments/v32_precision_20261119_r03/labels/group_c/69.png) | 42.88 | 42.88 | 42.88 | 42.88 | 30.34 | 30.34 | 30.34 | -29.61 / 6.59 | 尖端提前 | 两项均未恢复 |
| [验证组C 335](../../output/experiments/v32_precision_20261119_r03/labels/group_c/335.png) | 52.82 | 42.82 | 30.64 | 30.64 | 30.64 | 30.64 | 30.64 | 23.84 / -19.25 | 向右过冲 | 两项均未恢复 |
| [验证组C 221](../../output/experiments/v32_precision_20261119_r03/labels/group_c/221.png) | 25.54 | 25.54 | 9.39 | 9.39 | 9.39 | 9.39 | 9.39 | 9.39 / -0.21 | 联合命中 | 仅尾门单改恢复 |
| [验证组C 456](../../output/experiments/v32_precision_20261119_r03/labels/group_c/456.png) | 12.16 | 12.16 | 12.16 | 12.16 | 10.10 | 10.10 | 10.10 | 10.09 / 0.30 | 向右过冲 | 两项均未恢复 |
| [验证组C 480](../../output/experiments/v32_precision_20261119_r03/labels/group_c/480.png) | 13.02 | 13.02 | 2.02 | 1.47 | 1.47 | 1.47 | 1.47 | 1.02 / -1.05 | 联合命中 | 仅尾门单改恢复 |
| [验证组C 528](../../output/experiments/v32_precision_20261119_r03/labels/group_c/528.png) | 12.37 | 2.41 | 10.46 | 1.44 | 1.44 | 1.44 | 1.44 | 1.36 / 0.49 | 联合命中 | 仅背景单改恢复 |

**验证组C第 69 帧**　人工尖端 [2303.610108303249, 2331.407942238267]。截断列为原图 x；空值表示所选分支未发生该项截断。

| 阶段叠图 | 所选起点 | 预测尖端 | 误差 px | 几何判断 | 几何截断 | 谷底截断 | 局部复核 | NCC | 平移 | 参考截断 | 复核前尖端 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [v3_1](../../output/experiments/v32_precision_20261119_r03/stage_images/group_c/69_v3_1.png) | [2240, 2316] | [2344, 2317] | 42.88 | — | None | None | — | — | None | None | None |
| [paired](../../output/experiments/v32_precision_20261119_r03/stage_images/group_c/69_paired.png) | [2240, 2316] | [2344, 2317] | 42.88 | CLEAR | None | None | — | — | None | None | None |
| [distal](../../output/experiments/v32_precision_20261119_r03/stage_images/group_c/69_distal.png) | [2240, 2316] | [2274, 2338] | 30.34 | DISTAL_KINK | 2310 | 2276 | — | — | None | None | None |
| [reference](../../output/experiments/v32_precision_20261119_r03/stage_images/group_c/69_reference.png) | [2240, 2316] | [2274, 2338] | 30.34 | DISTAL_KINK | 2310 | 2276 | AMBIGUOUS_ALIGNMENT | 1.00 | [0, 1] | None | None |
| [v3_2](../../output/experiments/v32_precision_20261119_r03/labels/group_c/69.png) | [2247, 2344] | [2274, 2338] | 30.34 | OTHER_LIP | 2275 | None | AMBIGUOUS_ALIGNMENT | 0.99 | [0, 0] | None | None |

**验证组C第 335 帧**　人工尖端 [2470.1639344262294, 2345.245901639344]。截断列为原图 x；空值表示所选分支未发生该项截断。

| 阶段叠图 | 所选起点 | 预测尖端 | 误差 px | 几何判断 | 几何截断 | 谷底截断 | 局部复核 | NCC | 平移 | 参考截断 | 复核前尖端 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [v3_1](../../output/experiments/v32_precision_20261119_r03/stage_images/group_c/335_v3_1.png) | [2252, 2340] | [2516, 2319] | 52.82 | — | None | None | — | — | None | None | None |
| [paired](../../output/experiments/v32_precision_20261119_r03/stage_images/group_c/335_paired.png) | [2252, 2340] | [2494, 2326] | 30.64 | CLEAR | None | None | — | — | None | None | None |
| [distal](../../output/experiments/v32_precision_20261119_r03/stage_images/group_c/335_distal.png) | [2252, 2340] | [2494, 2326] | 30.64 | DISTAL_BRIGHT_GAP | 2505 | None | — | — | None | None | None |
| [reference](../../output/experiments/v32_precision_20261119_r03/stage_images/group_c/335_reference.png) | [2252, 2340] | [2494, 2326] | 30.64 | DISTAL_BRIGHT_GAP | 2505 | None | NOT_SUSPICIOUS | — | None | None | None |
| [v3_2](../../output/experiments/v32_precision_20261119_r03/labels/group_c/335.png) | [2252, 2340] | [2494, 2326] | 30.64 | DISTAL_BRIGHT_GAP | 2505 | None | NOT_SUSPICIOUS | — | None | None | None |

| 三点弯 215 | 起点 | 尖端 | 首失列 | 重获事件¹ | 覆盖 | 精度 | Joint |
|---|---|---|---|---|---|---|---|
| s3t | [1472, 2679] | [1603, 2718] | None | None | 0.57 | 0.52 | False |
| v3_1 | [1474, 2729] | [1612, 2718] | 1507 | None | 1.00 | 1.00 | True |
| paired | [1474, 2729] | [1603, 2718] | 1507 | [[1507, 1520, 1533, 8.035714285714292, 1.2222222222222223, 1]] | 1.00 | 1.00 | True |
| distal | [1474, 2729] | [1603, 2718] | 1507 | [[1507, 1520, 1533, 8.035714285714292, 1.2222222222222223, 1]] | 1.00 | 1.00 | True |
| reference | [1474, 2729] | [1603, 2718] | 1507 | [[1507, 1520, 1533, 8.035714285714292, 1.2222222222222223, 1]] | 1.00 | 1.00 | True |
| v3_2 | [1472, 2679] | [1603, 2718] | 1612 | [] | 0.65 | 0.60 | False |

¹ 事件依次为弱带起始列、重获窗首末列、纵向预测残差、谷宽比、是否通过。最终入选起点与截断可在[分阶段诊断](../../output/experiments/v32_precision_20261119_r03/stage_diagnostics.csv)核对。

| 相对 V3.1 | 模式 | 丢失 Hit | 丢失 Joint | 误差增加 | 覆盖降低 | 精度降低 |
|---|---|---|---|---|---|---|
| 开发组A | full | 366, 504 | 366, 504 | 217, 241, 366, 504, 542 | 366, 504 | 504 |
| 开发组A | raw_only | 366, 504 | 366, 504 | 217, 241, 366, 504, 542 | 366, 504 | 504 |
| 三点弯 | full | — | 215, 271, 306, 347, 381 | 381, 407 | 144, 178, 215, 248, 271, 306, 335, 347, 381, 407, 413, 435, 476, 503 | 144, 178, 215, 248, 271, 306, 335, 347, 381, 407, 413, 435, 476, 503 |
| 三点弯 | raw_only | — | 215, 271, 306, 347, 381 | 381, 407 | 144, 178, 215, 248, 271, 306, 335, 347, 381, 407, 413, 435, 476, 503 | 144, 178, 215, 248, 271, 306, 335, 347, 381, 407, 413, 435, 476, 503 |
| 验证组C | full | 38, 54 | 54 | 38, 54 | 38, 54, 69 | 38, 121 |
| 验证组C | raw_only | 38, 54 | 54 | 38, 54 | 38, 54, 69 | 38, 121 |

以下为所有可见标注中 full 最终联合未命中的帧。偏差方向、覆盖和精度说明失败类型；记录的末端认证、首失列与复核状态描述触发机制，材料纹理的物理身份仍需独立证据。

| 异常帧 | 类型 | dx / dy px | 误差 px | 覆盖 / 精度 | 尾门 / 停止条件 | 几何 / 局部复核 |
|---|---|---|---|---|---|---|
| [开发组A 366](../../output/experiments/v32_precision_20261119_r03/labels/group_a/366.png) | 尖端提前 | -14.07 / 2.58 | 14.31 | 0.99 / 1.00 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / NOT_SUSPICIOUS |
| [开发组A 504](../../output/experiments/v32_precision_20261119_r03/labels/group_a/504.png) | 尖端提前 | -13.97 / 2.45 | 14.18 | 0.98 / 1.00 | TAPER / DISTAL_WEAK | DISTAL_KINK / LOW_ANCHOR_TEXTURE |
| [三点弯 1](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/1.png) | 向右过冲 | 61.86 / -22.75 | 65.91 | 0.00 / 0.00 | STRONG / GAP_NOT_REACQUIRED | CLEAR / NOT_SUSPICIOUS |
| [三点弯 144](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/144.png) | 尖端命中、路径未达标 | -2.76 / -9.53 | 9.92 | 0.27 / 0.29 | STRONG / DISTAL_WEAK | OTHER_LIP / NO_STATIC_SUFFIX |
| [三点弯 178](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/178.png) | 向右过冲 | 22.59 / -7.65 | 23.85 | 0.33 / 0.29 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / NO_STATIC_SUFFIX |
| [三点弯 215](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/215.png) | 尖端命中、路径未达标 | -2.00 / -0.57 | 2.08 | 0.65 / 0.60 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / NOT_SUSPICIOUS |
| [三点弯 248](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/248.png) | 尖端命中、路径未达标 | 9.08 / -1.20 | 9.16 | 0.64 / 0.64 | TAPER / DISTAL_WEAK | DISTAL_BRIGHT_GAP / AMBIGUOUS_ALIGNMENT |
| [三点弯 271](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/271.png) | 尖端命中、路径未达标 | 4.80 / -1.47 | 5.02 | 0.71 / 0.68 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / NOT_SUSPICIOUS |
| [三点弯 306](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/306.png) | 尖端命中、路径未达标 | 2.48 / -0.17 | 2.49 | 0.73 / 0.72 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / NOT_SUSPICIOUS |
| [三点弯 335](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/335.png) | 向右过冲 | 10.04 / -3.23 | 10.55 | 0.73 / 0.74 | TAPER / DISTAL_WEAK | DISTAL_BRIGHT_GAP / LOW_ANCHOR_TEXTURE |
| [三点弯 347](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/347.png) | 尖端命中、路径未达标 | 1.70 / -1.87 | 2.52 | 0.75 / 0.74 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / NOT_SUSPICIOUS |
| [三点弯 381](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/381.png) | 尖端命中、路径未达标 | -8.18 / -0.18 | 8.18 | 0.78 / 0.76 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / NOT_SUSPICIOUS |
| [三点弯 407](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/407.png) | 尖端提前 | -18.94 / 2.52 | 19.10 | 0.80 / 0.82 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / NOT_SUSPICIOUS |
| [三点弯 413](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/413.png) | 向右过冲 | 13.21 / -0.66 | 13.22 | 0.78 / 0.77 | TAPER / DISTAL_WEAK | DISTAL_BRIGHT_GAP / AMBIGUOUS_ALIGNMENT |
| [三点弯 435](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/435.png) | 尖端命中、路径未达标 | 1.40 / -0.98 | 1.71 | 0.78 / 0.78 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / NOT_SUSPICIOUS |
| [三点弯 503](../../output/experiments/v32_precision_20261119_r03/labels/three_point_bend/503.png) | 向右过冲 | 10.04 / 5.00 | 11.22 | 0.84 / 0.85 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / AMBIGUOUS_ALIGNMENT |
| [验证组C 38](../../output/experiments/v32_precision_20261119_r03/labels/group_c/38.png) | 尖端提前 | -17.46 / 6.65 | 18.68 | 0.49 / 0.75 | STRONG / GAP_NOT_REACQUIRED | CLEAR / NOT_SUSPICIOUS |
| [验证组C 54](../../output/experiments/v32_precision_20261119_r03/labels/group_c/54.png) | 尖端提前 | -29.49 / 8.05 | 30.57 | 0.47 / 1.00 | STRONG / GAP_NOT_REACQUIRED | OTHER_LIP / AMBIGUOUS_ALIGNMENT |
| [验证组C 69](../../output/experiments/v32_precision_20261119_r03/labels/group_c/69.png) | 尖端提前 | -29.61 / 6.59 | 30.34 | 0.59 / 0.76 | STRONG / DISTAL_WEAK | OTHER_LIP / AMBIGUOUS_ALIGNMENT |
| [验证组C 195](../../output/experiments/v32_precision_20261119_r03/labels/group_c/195.png) | 向右过冲 | 15.74 / 2.05 | 15.87 | 1.00 / 0.95 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / NOT_SUSPICIOUS |
| [验证组C 335](../../output/experiments/v32_precision_20261119_r03/labels/group_c/335.png) | 向右过冲 | 23.84 / -19.25 | 30.64 | 1.00 / 0.91 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / NOT_SUSPICIOUS |
| [验证组C 363](../../output/experiments/v32_precision_20261119_r03/labels/group_c/363.png) | 纵向偏差主导 | 8.97 / -17.85 | 19.97 | 0.99 / 0.93 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / LOW_ANCHOR_TEXTURE |
| [验证组C 456](../../output/experiments/v32_precision_20261119_r03/labels/group_c/456.png) | 向右过冲 | 10.09 / 0.30 | 10.10 | 1.00 / 1.00 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / AMBIGUOUS_ALIGNMENT |
| [验证组C 510](../../output/experiments/v32_precision_20261119_r03/labels/group_c/510.png) | 向右过冲 | 16.94 / 0.43 | 16.95 | 1.00 / 0.97 | STRONG / DISTAL_WEAK | DISTAL_BRIGHT_GAP / NOT_SUSPICIOUS |

[两种模式的全部失败及上游阶段误差](../../output/experiments/v32_precision_20261119_r03/failures.csv) · [连续指标退化清单](../../output/experiments/v32_precision_20261119_r03/regressions.csv) · [不确定标注](../../output/experiments/v32_precision_20261119_r03/uncertain.csv)

九张历史过冲帧中，单改渐弱终止规则使三点弯 413、435 和验证组C 221、480 回到容差，单改背景只使验证组C 528 回到容差。加入远端检查后，三点弯 248、476 恢复，413 又离开容差。最终九帧恢复六帧，三点弯 335、413 和验证组C 456 仍过冲。开发组A 366 在两种单改下均退化，504 主要受尾端规则影响；451、542 仍联合命中。

验证组C 69 在 distal 阶段先遇 x=2310 折转，缩短后的有效轨迹又触发 x=2276 谷底截断，误差从过冲转为提前。最终所选起点改到 (2247,2344)，同唇校验在 x=2275 截断。局部 NCC 虽高，但峰值不唯一，两阶段均未据参考图裁剪。验证组C 335 的原灰度叠图可见算法线从人工终点转向右上暗线。新的终止规则把误差降到 30.64 px；远端首次满足连续亮隙条件在 x=2505，晚于已认证尖端 x=2494。所选尾段通过强门且未触发复核。图像支持旁侧暗线吸附，尚无法确认该线在固定参考中静止。

三点弯 215 的正确下唇从 (1474,2729) 出发。重获窗 x=1520–1533 的谷宽比为 1.22，切向外推中位残差 8.04 px，同唇门在 x=1507 拒绝该重连，下唇候选退至 x=1506。上唇候选因而胜出，尖端误差保持 2.08 px，覆盖率从 100% 降至 64.9%，路径精度从 100% 降至 60%。三点弯该阶段整体由 9/15 联合命中降至 1/15。三点弯第 1 帧路径覆盖和精度均为零，是另一类早期归属失败。[包括未入选分支的三帧记录](../../output/experiments/v32_precision_20261119_r03/focus_candidates.csv)

## 4　合成探针与弱带错连

相同的 156 个几何、噪声、弱带条件组合分别比较两个版本和三种曝光。下表为原曝光。P1 要求整条真线在 2.5 个基准像素容差内且尖端误差 ≤10，P2 仅按尖端阈值，P3/P4 为阴性。误差按倍率折回基准像素。

| 探针 | 版本 | 0.5× 通过 | 1× 通过 | 2× 通过 |
|---|---|---|---|---|
| P1_upper | v3_1 | 4/4 | 4/4 | 4/4 |
| P1_upper | v3_2 | 4/4 | 4/4 | 4/4 |
| P1_lower | v3_1 | 4/4 | 4/4 | 4/4 |
| P1_lower | v3_2 | 4/4 | 4/4 | 4/4 |
| P2_fade | v3_1 | 1/4 | 4/4 | 4/4 |
| P2_fade | v3_2 | 2/4 | 4/4 | 4/4 |
| P3_parallel | v3_1 | 4/4（FP 0/4） | 4/4（FP 0/4） | 4/4（FP 0/4） |
| P3_parallel | v3_2 | 4/4（FP 0/4） | 4/4（FP 0/4） | 4/4（FP 0/4） |
| P3_oblique | v3_1 | 4/4（FP 0/4） | 4/4（FP 0/4） | 4/4（FP 0/4） |
| P3_oblique | v3_2 | 4/4（FP 0/4） | 4/4（FP 0/4） | 4/4（FP 0/4） |
| P4_ring | v3_1 | 4/4（FP 0/4） | 4/4（FP 0/4） | 4/4（FP 0/4） |
| P4_ring | v3_2 | 4/4（FP 0/4） | 4/4（FP 0/4） | 4/4（FP 0/4） |
| P4_open | v3_1 | 4/4（FP 0/4） | 4/4（FP 0/4） | 2/4（FP 2/4） |
| P4_open | v3_2 | 4/4（FP 0/4） | 4/4（FP 0/4） | 4/4（FP 0/4） |
| P1_weak_gap | v3_1 | 6/24 | 12/24 | 13/24 |
| P1_weak_gap | v3_2 | 6/24 | 12/24 | 13/24 |

72 个弱带样本的错误重连，只对最终入选轨迹中重获窗与注入区相交的事件计数。窗内贴合真下唇的点少于 80% 计一次错连。

| 版本 | 弱带宽 | 残余对比 | 样本 | 接受 | 错连 | 同唇门拒绝 | 整路径通过 |
|---|---|---|---|---|---|---|---|
| v3_1 | 4 | 0.0 | 12 | 8 | 0 | 0 | 8/12 |
| v3_1 | 4 | 0.2 | 12 | 2 | 0 | 0 | 10/12 |
| v3_1 | 9 | 0.0 | 12 | 10 | 4 | 0 | 0/12 |
| v3_1 | 9 | 0.2 | 12 | 3 | 0 | 0 | 7/12 |
| v3_1 | 16 | 0.0 | 12 | 4 | 4 | 0 | 0/12 |
| v3_1 | 16 | 0.2 | 12 | 3 | 0 | 0 | 6/12 |
| v3_2 | 4 | 0.0 | 12 | 8 | 0 | 0 | 8/12 |
| v3_2 | 4 | 0.2 | 12 | 2 | 0 | 0 | 10/12 |
| v3_2 | 9 | 0.0 | 12 | 6 | 0 | 1 | 0/12 |
| v3_2 | 9 | 0.2 | 12 | 2 | 0 | 1 | 7/12 |
| v3_2 | 16 | 0.0 | 12 | 0 | 0 | 1 | 0/12 |
| v3_2 | 16 | 0.2 | 12 | 3 | 0 | 0 | 6/12 |

原曝光接受数从 30 降至 21，错连从 8 次降至 0 次。错连减少与保守截断同时发生。每个曝光及每个样本的路径评分见[探针原始数据](../../output/experiments/v32_precision_20261119_r03/probes.csv)。

## 5　曝光稳定性与运行时间

固定几何分别施加 nominal 原灰度、dim = 0.65I+9、bright = 1.16I+15，并裁剪为 8 位。通过状态和尖端比较均相对同一版本、同一原曝光样本。

| 版本 | 曝光 | 通过 / 总数 | 通过状态变化数 | 坐标或有效性变化数 |
|---|---|---|---|---|
| v3_1 | nominal | 110/156 | 0 | 0 |
| v3_1 | dim | 110/156 | 2 | 18 |
| v3_1 | bright | 101/156 | 17 | 4 |
| v3_2 | nominal | 113/156 | 0 | 0 |
| v3_2 | dim | 112/156 | 1 | 24 |
| v3_2 | bright | 104/156 | 15 | 17 |

六个 CPU 工作进程；每帧耗时包含 ROI 内准备、辅助矩阵与一次 full 预测，排除读盘、绘图、视频和 raw_only。FPS 为平均耗时的倒数。局部复核净耗时为所有帧（含未触发）的均值，按唯一末段缓存计时。阶段总耗时差为每组 20 帧 reference 减 distal，包含调度和候选重认证波动。

| 组 | 帧 | 平均 ms | P95 ms | 最慢 ms（帧） | FPS | 局部复核 ms/帧 | 至少一次复核帧数 | 阶段差 ms/帧 |
|---|---|---|---|---|---|---|---|---|
| 开发组A | 551 | 85.61 | 68.88 | 4294.43（11） | 11.68 | 0.21 | 371 | 1.27 |
| 三点弯 | 520 | 127.42 | 115.78 | 4193.34（9） | 7.85 | 1.96 | 462 | -3.25 |
| 验证组C | 562 | 83.53 | 70.86 | 4285.11（3） | 11.97 | 1.21 | 500 | 0.70 |

| 组 | 复核后裁剪候选数（含重复候选） | 最终入选有裁剪帧数 | full/raw 尖端不同帧数 | 公开路径或状态不同帧数 | full 无尖端帧数 |
|---|---|---|---|---|---|
| 开发组A | 1 | 0 | 0 | 0 | 0 |
| 三点弯 | 12 | 5 | 5 | 16 | 0 |
| 验证组C | 5 | 1 | 1 | 1 | 0 |

局部配准专项五例中，人为设置的静态后缀从 x=128 开始；平移估计为 (−3,+2)，首次裁剪在 x=127。整线静态、整线新增、参考缺像素及低纹理四例均保留原预测。旧公共矩阵 420 行逐项一致。新算法另由双版本的 936 条曝光与倍率观测覆盖。[配准测试](../../output/experiments/v32_precision_20261119_r03/reference_tests.json) · [计时及复核状态分布](../../output/experiments/v32_precision_20261119_r03/timing.csv) · [视频解码核验](../../output/experiments/v32_precision_20261119_r03/delivery_check.json)

两种模式在三个组的可见帧 Hit、Joint、严重误差和误差分布均持平。全序列仍有 6 帧的尖端不同，逐帧差异和人工标注状态单列。[两种模式的全部输出差异](../../output/experiments/v32_precision_20261119_r03/mode_disagreements.csv)。计时中的最慢帧位于各批启动阶段，包含新编译算子开销；阶段总耗时差可为负。局部参考与画面曝光的真实联合作用仍缺少受控实测。

## 6　生产验收与遗留边界

**PRODUCTION_NO_GO**。开发组A及原曝光合成目标通过。三点弯的尖端和路径指标、验证组C的尖端与联合指标均低于门槛。与 V3.1 相比，三个组汇总的尖端命中从 31/54 增到 38/54，联合命中均为 30/54。当前限制生产使用的首要问题是三点弯的近缺口路径归属。

| 项目 | 门槛 | 实际 | 判定 |
|---|---|---|---|
| 开发组A | Hit ≥16，Joint ≥16，严重 0 | Hit 17/19，Joint 17/19，严重 0 | 通过 |
| 三点弯 | Hit ≥10，Joint ≥8，严重 0 | Hit 9/15，Joint 1/15，严重 0 | 未通过 |
| 验证组C | Hit ≥13，Joint ≥13，严重 0 | Hit 12/20，Joint 12/20，严重 0 | 未通过 |
| 弱带错连 | 相对 8/30 减至少于 3 次 | 错连 0/21 次接受；同一批 72 个样本 | 通过事件计数，接受数减少 |
| P2_fade | 至少 10/12 | 原曝光 10/12 | 通过 |
| 阴性误报 | 0.5× / 2× 逼近零 | 原曝光 P3/P4 两个倍率均 0/16 | 通过合成负例 |
| 双模式 | full 不劣于 raw_only | 三组可见标注的指标持平 | 通过本次对照 |

| 问题 | 已有证据 | 可检验的下一步 |
|---|---|---|
| 同唇校验误拒真实弯曲下唇 | 三点弯 215 的预测残差 8.04 px，谷宽比 1.22；最终选到上唇。三点弯最后阶段丢失八个联合命中。 | 在开发组及独立合成图加入弯曲、合流、遮挡的双唇；分别消融切向与宽度，将正确拒绝和错误拒绝都列入事件统计。 |
| 末端暗线离开主裂纹，或保护规则提前截断 | 验证组C 335 的远端亮隙触发晚于误选的暗线；69 的回剪跨过人工尖端，局部配准峰不唯一。 | 在独立开发图造出带已知真实尖端的斜向划痕，区分首次偏离列、首次弱隙列、实际截断列，并检验配准峰唯一性。 |
| 弱尾及曝光边界 | 开发组A 366、504 由命中转为提前约 14 px；P2 的两个失败都在半倍率高噪声下。强曝光下合成通过数从 113 降到 104。 | 在独立采集的开发图改变倍率、曝光和噪声，验证弱尾信号分辨率及局部背景动态范围。 |
| 实际误报率及实时性缺证 | 54 张可见人工尖端和 6 张不确定标注；已有序列缺少独立阴性和相机端到端时延测量。 | 取得独立无裂纹阴性序列并测量单路采集到输出的稳态及冷启动延迟。 |
