# V5.12 失败帧与性能审计

以冻结 V5.11 r02 为基座。S4 可见帧 Joint 为 45/54，V5.11 为 41/54，V5.10 为 46/54。验证组C两种点位使用同一批图像，在总数中仅计一次。共运行 1,633 张原图。开发组A用于开发，三点弯和验证组C均在配置冻结后顺序运行，均为已接触的验证数据。排除组X排除。人工标注仅作封存后的评分与误差诊断。

## S1–S4 消融复核

每组抽取 20 个标注帧，合计 54 帧有可见尖端。真实帧误差为原图欧氏距离。Hit@5/10 按像素判定，Joint 同时要求 10 px 邻域路径覆盖率、精确率均 ≥80%，Severe 为有定位且误差 >100 px。无预测计入可见分母。消融速度为相同 20 帧的调用数除以算法累计时间；下表另列完整序列速度，含 ROI 准备、局部配准及检测，不含读盘、原始上游参考图构建、评分或视频编码。

| 阶段 | 数据及点位 | 可见 | Hit@5 | Hit@10 | Joint | Severe | 20 帧 full FPS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | 开发组A | 19 | 12 | 18 | 18 | 0 | 16.78 |
| S1 | 三点弯 | 15 | 6 | 11 | 9 | 0 | 5.36 |
| S1 | 验证组C 原点 | 20 | 16 | 18 | 18 | 0 | 33.16 |
| S1 | 验证组C 亮区 | 20 | 16 | 18 | 18 | 0 | 33.99 |
| S2 | 开发组A | 19 | 12 | 18 | 18 | 0 | 17.16 |
| S2 | 三点弯 | 15 | 4 | 9 | 9 | 1 | 5.41 |
| S2 | 验证组C 原点 | 20 | 16 | 18 | 18 | 0 | 33.83 |
| S2 | 验证组C 亮区 | 20 | 16 | 18 | 18 | 0 | 34.23 |
| S3 | 开发组A | 19 | 12 | 18 | 18 | 0 | 17.07 |
| S3 | 三点弯 | 15 | 4 | 9 | 9 | 1 | 5.41 |
| S3 | 验证组C 原点 | 20 | 16 | 18 | 18 | 0 | 34.24 |
| S3 | 验证组C 亮区 | 20 | 16 | 18 | 18 | 0 | 34.24 |
| S4 | 开发组A | 19 | 12 | 18 | 18 | 0 | 17.53 |
| S4 | 三点弯 | 15 | 4 | 9 | 9 | 1 | 5.65 |
| S4 | 验证组C 原点 | 20 | 16 | 18 | 18 | 0 | 35.38 |
| S4 | 验证组C 亮区 | 20 | 16 | 18 | 18 | 0 | 34.41 |

| 组别 | 序列帧 | full FPS | raw_only FPS |
| --- | --- | --- | --- |
| 开发组A | 551 | 15.89 | 63.52 |
| 三点弯 | 520 | 5.43 | 23.75 |
| 验证组C 原点 | 562 | 32.36 | 96.22 |
| 验证组C 亮区 | 562 | 33.59 | 96.37 |

## 合成与基准点扰动

| 阶段 | 合成类别 | 样本 | Hit@5 | Hit@10 | Joint | Severe | 场景验收通过 | 误报 | FPS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | 全部阳性 | 936 | 803 | 825 | 810 | 0 | 823 | — | 18.03 |
| S1 | P1_weak_gap | 216 | 216 | 216 | 216 | 0 | 216 | — | 25.29 |
| S1 | weak_material_bridge | 36 | 36 | 36 | 36 | 0 | 36 | — | 30.44 |
| S1 | active_fork | 36 | 30 | 30 | 30 | 0 | 30 | — | 25.14 |
| S1 | P6_isolated | 36 | 0 | 0 | 0 | 0 | 0 | — | 23.87 |
| S1 | P6_deformed_scratch | 36 | 0 | 3 | 3 | 0 | 3 | — | 22.55 |
| S1 | 全部阴性 | 468 | — | — | — | — | 468 | 0 | 30.19 |
| S2 | 全部阳性 | 936 | 840 | 882 | 867 | 0 | 880 | — | 25.78 |
| S2 | P1_weak_gap | 216 | 216 | 216 | 216 | 0 | 216 | — | 26.02 |
| S2 | weak_material_bridge | 36 | 36 | 36 | 36 | 0 | 36 | — | 29.90 |
| S2 | active_fork | 36 | 30 | 30 | 30 | 0 | 30 | — | 25.62 |
| S2 | P6_isolated | 36 | 36 | 36 | 36 | 0 | 36 | — | 24.27 |
| S2 | P6_deformed_scratch | 36 | 1 | 24 | 24 | 0 | 24 | — | 23.70 |
| S2 | 全部阴性 | 468 | — | — | — | — | 468 | 0 | 30.09 |
| S3 | 全部阳性 | 936 | 840 | 882 | 867 | 0 | 880 | — | 25.50 |
| S3 | P1_weak_gap | 216 | 216 | 216 | 216 | 0 | 216 | — | 25.28 |
| S3 | weak_material_bridge | 36 | 36 | 36 | 36 | 0 | 36 | — | 29.27 |
| S3 | active_fork | 36 | 30 | 30 | 30 | 0 | 30 | — | 24.28 |
| S3 | P6_isolated | 36 | 36 | 36 | 36 | 0 | 36 | — | 24.68 |
| S3 | P6_deformed_scratch | 36 | 1 | 24 | 24 | 0 | 24 | — | 22.64 |
| S3 | 全部阴性 | 468 | — | — | — | — | 468 | 0 | 30.90 |
| S4 | 全部阳性 | 936 | 840 | 882 | 867 | 0 | 880 | — | 26.28 |
| S4 | P1_weak_gap | 216 | 216 | 216 | 216 | 0 | 216 | — | 26.04 |
| S4 | weak_material_bridge | 36 | 36 | 36 | 36 | 0 | 36 | — | 30.95 |
| S4 | active_fork | 36 | 30 | 30 | 30 | 0 | 30 | — | 24.96 |
| S4 | P6_isolated | 36 | 36 | 36 | 36 | 0 | 36 | — | 25.91 |
| S4 | P6_deformed_scratch | 36 | 1 | 24 | 24 | 0 | 24 | — | 23.59 |
| S4 | 全部阴性 | 468 | — | — | — | — | 468 | 0 | 31.66 |

| 组别 | 输入 | 扰动数 | 双端点可比 | 状态/有无变化 | 最大漂移 px | 对应帧 | 可见帧最大 px |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | 固定配准 | 200 | 190 | 0 | 0.00 | 67 | 0.00 |
| 开发组A | 重裁剪重配准 | 200 | 190 | 0 | 7.00 | 204 | 7.00 |
| 三点弯 | 固定配准 | 200 | 200 | 0 | 0.00 | 1 | 0.00 |
| 三点弯 | 重裁剪重配准 | 200 | 200 | 0 | 119.34 | 248 | 119.34 |
| 验证组C | 固定配准 | 200 | 200 | 0 | 0.00 | 1 | 0.00 |
| 验证组C | 重裁剪重配准 | 200 | 200 | 0 | 4.00 | 324 | 4.00 |

封存预测中，验证组C原点/亮区两套点位有 20/20 个标注帧及 558/562 个全序列帧给出相同端点（含同时无输出）。主评测继承 V5.11 S3 的上游参考缓存，验证组C两套点位共用该缓存。在重配准试验中，每次使用实际点对重新生成上游映射。下表检查零扰动原图重算与主评测的一致性。

| 数据 | 零扰动与封存端点相同 | 比较帧 | 最大差异 px | 零扰动 Hit@10 |
| --- | --- | --- | --- | --- |
| 开发组A | 20 | 20 | 0.00 | 18 |
| 三点弯 | 20 | 20 | 0.00 | 9 |
| 验证组C | 12 | 20 | 6.08 | 18 |

## S3 与 S4 一致性

12 组合成输入的 S3/S4 逐像素证据场、种子、配准记录及门控统计完全一致。纯算子等价检查覆盖全部标注帧与点位。S3 和 S4 的状态、整条折线、端点和局部配准记录在 80/80 个组合一致。合成矩阵中，尖端、路径评分和验收状态在 1404/1404 个配对样本一致。

## 目标帧证据

验证组C亮区 232、324、335、345 恢复 Joint。第 54 帧保持 0.49 px。第 38 帧的旧分支有 10 列位于蓝带，但候选未形成从缺口到红脊的合格连接，第 0 分支总分不足，仍由第 2 分支输出。第 510 帧经缺口局部配准后，初始累计峰与最终尖端都是 [2505, 2346]，横向多追 14.94 px，桥接没有执行。限制下游峰无法纠正已经偏远的初始峰。三点弯 215 的候选延伸有连续 17 个双证据列，同时存在 29 列空档；248 的 115 列延伸中有 86 列双证据，最长连续 85 列、最长空档 28 列。空白跨度锁拦截两条延伸，S2 又因根部连接条件排除了保送分支。第 248 帧最终提前约 111 px，构成严重错误。冻结后回放复现了上述端点与完整路径。 全部真实帧与点位共有 3 个候选走过 S3 新增叉根通道，最终获选 0 次。

| 组别 | 帧 | 点位 | V5.11 误差 | S1 | S2 | S3 | S4 | S4 Δx | S4 分支 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | 299 | original | 0.44 | 0.44 | 0.44 | 0.44 | 0.44 | 0.30 | BRANCH_0 |
| 三点弯 | 215 | original | 6.03 | 0.43 | 85.76 | 85.76 | 85.76 | -85.00 | BRANCH_2 |
| 三点弯 | 248 | original | 2.20 | 3.20 | 111.20 | 111.20 | 111.20 | -110.92 | BRANCH_2 |
| 三点弯 | 306 | original | 2.49 | 2.49 | 2.49 | 2.49 | 2.49 | 2.48 | BRANCH_2 |
| 三点弯 | 413 | original | 6.43 | 6.43 | 6.43 | 6.43 | 6.43 | 6.21 | BRANCH_2 |
| 三点弯 | 435 | original | 5.49 | 5.49 | 5.49 | 5.49 | 5.49 | 5.40 | BRANCH_2 |
| 验证组C | 1 | original | 1.26 | 1.26 | 1.26 | 1.26 | 1.26 | -1.18 | BRANCH_2 |
| 验证组C | 1 | bright | 1.26 | 1.26 | 1.26 | 1.26 | 1.26 | -1.18 | BRANCH_2 |
| 验证组C | 7 | original | 0.84 | 0.84 | 0.84 | 0.84 | 0.84 | -0.03 | BRANCH_2 |
| 验证组C | 7 | bright | 2.14 | 0.84 | 0.84 | 0.84 | 0.84 | -0.03 | BRANCH_2 |
| 验证组C | 38 | original | 18.15 | 18.15 | 18.15 | 18.15 | 18.15 | -16.46 | BRANCH_2 |
| 验证组C | 38 | bright | 18.15 | 18.15 | 18.15 | 18.15 | 18.15 | -16.46 | BRANCH_2 |
| 验证组C | 54 | original | 1.51 | 0.49 | 0.49 | 0.49 | 0.49 | -0.49 | BRANCH_2 |
| 验证组C | 54 | bright | 0.49 | 0.49 | 0.49 | 0.49 | 0.49 | -0.49 | BRANCH_2 |
| 验证组C | 232 | original | 0.71 | 0.71 | 0.71 | 0.71 | 0.71 | 0.00 | BRANCH_1 |
| 验证组C | 232 | bright | 40.17 | 0.71 | 0.71 | 0.71 | 0.71 | 0.00 | BRANCH_1 |
| 验证组C | 324 | original | 7.37 | 7.37 | 7.37 | 7.37 | 7.37 | 7.28 | BRANCH_1 |
| 验证组C | 324 | bright | 166.55 | 7.37 | 7.37 | 7.37 | 7.37 | 7.28 | BRANCH_1 |
| 验证组C | 335 | original | 1.85 | 1.85 | 1.85 | 1.85 | 1.85 | 1.84 | BRANCH_1 |
| 验证组C | 335 | bright | 151.11 | 1.85 | 1.85 | 1.85 | 1.85 | 1.84 | BRANCH_1 |
| 验证组C | 345 | original | 0.55 | 0.55 | 0.55 | 0.55 | 0.55 | 0.49 | BRANCH_1 |
| 验证组C | 345 | bright | 157.75 | 0.55 | 0.55 | 0.55 | 0.55 | 0.49 | BRANCH_1 |
| 验证组C | 510 | original | 14.96 | 14.95 | 14.95 | 14.95 | 14.95 | 14.94 | BRANCH_1 |
| 验证组C | 510 | bright | 15.96 | 14.95 | 14.95 | 14.95 | 14.95 | 14.94 | BRANCH_1 |

| 组 | 帧 | 分支 S1/S2/S3/S4 | 误差 px | 覆盖率 | 精确率 | Joint | 初始峰 | 最终尖端 | 桥接判据 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 三点弯 | 215 | 1 / 2 / 2 / 2 | 85.76 | 0.31 | 0.91 | False | [1520, 2730] | [1520, 2730] | SHORT_OR_UNATTACHED |
| 三点弯 | 248 | 1 / 2 / 2 / 2 | 111.20 | 0.25 | 0.91 | False | [1519, 2733] | [1519, 2733] | SHORT_OR_UNATTACHED |
| 验证组C | 38 | 2 / 2 / 2 / 2 | 18.15 | 0.49 | 0.77 | False | [2273, 2339] | [2273, 2339] | NO_SUPPORTED_TERMINUS |
| 验证组C | 54 | 2 / 2 / 2 / 2 | 0.49 | 1.00 | 1.00 | True | [2274, 2340] | [2301, 2331] | DUAL_RUN |
| 验证组C | 232 | 1 / 1 / 1 / 1 | 0.71 | 1.00 | 1.00 | True | [2420, 2345] | [2420, 2345] | SHORT_OR_UNATTACHED |
| 验证组C | 324 | 1 / 1 / 1 / 1 | 7.37 | 1.00 | 1.00 | True | [2471, 2345] | [2471, 2345] | SHORT_OR_UNATTACHED |
| 验证组C | 335 | 1 / 1 / 1 / 1 | 1.85 | 1.00 | 1.00 | True | [2472, 2345] | [2472, 2345] | SHORT_OR_UNATTACHED |
| 验证组C | 345 | 1 / 1 / 1 / 1 | 0.55 | 1.00 | 1.00 | True | [2474, 2346] | [2474, 2346] | SHORT_OR_UNATTACHED |
| 验证组C | 510 | 1 / 1 / 1 / 1 | 14.95 | 1.00 | 0.98 | False | [2505, 2346] | [2505, 2346] | SHORT_OR_UNATTACHED |

| 组 | 帧 | 阶段 | 最终分支 | 分支编号、门控和得分 |
| --- | --- | --- | --- | --- |
| 三点弯 | 215 | S1 | BRANCH_1 | 0 MOUTH_DEAD_END，初分 34.62，排名分 42.72 / 1 VALID，初分 9.04，排名分 234.61 / 2 VALID，初分 55.73，排名分 96.23 |
| 三点弯 | 215 | S2 | BRANCH_2 | 0 MOUTH_DEAD_END，初分 34.62，排名分 42.72 / 1 DETACHED_RESCUE，初分 9.04，排名分 234.61 / 2 VALID，初分 55.73，排名分 96.23 |
| 三点弯 | 215 | S3 | BRANCH_2 | 0 MOUTH_DEAD_END，初分 34.62，排名分 42.72 / 1 DETACHED_RESCUE，初分 9.04，排名分 234.61 / 2 VALID，初分 55.73，排名分 96.23 |
| 三点弯 | 215 | S4 | BRANCH_2 | 0 MOUTH_DEAD_END，初分 34.62，排名分 42.72 / 1 DETACHED_RESCUE，初分 9.04，排名分 234.61 / 2 VALID，初分 55.73，排名分 96.23 |
| 三点弯 | 248 | S1 | BRANCH_1 | 0 MOUTH_DEAD_END，初分 32.87，排名分 40.97 / 1 VALID，初分 8.60，排名分 312.51 / 2 VALID，初分 55.92，排名分 95.07 |
| 三点弯 | 248 | S2 | BRANCH_2 | 0 MOUTH_DEAD_END，初分 32.87，排名分 40.97 / 1 DETACHED_RESCUE，初分 8.60，排名分 312.51 / 2 VALID，初分 55.92，排名分 95.07 |
| 三点弯 | 248 | S3 | BRANCH_2 | 0 MOUTH_DEAD_END，初分 32.87，排名分 40.97 / 1 DETACHED_RESCUE，初分 8.60，排名分 312.51 / 2 VALID，初分 55.92，排名分 95.07 |
| 三点弯 | 248 | S4 | BRANCH_2 | 0 MOUTH_DEAD_END，初分 32.87，排名分 40.97 / 1 DETACHED_RESCUE，初分 8.60，排名分 312.51 / 2 VALID，初分 55.92，排名分 95.07 |
| 验证组C | 38 | S1 | BRANCH_2 | 0 INSUFFICIENT_TOTAL，初分 0.28，排名分 0.28 / 2 VALID，初分 21.78，排名分 21.78 |
| 验证组C | 38 | S2 | BRANCH_2 | 0 INSUFFICIENT_TOTAL，初分 0.28，排名分 0.28 / 2 VALID，初分 21.78，排名分 21.78 |
| 验证组C | 38 | S3 | BRANCH_2 | 0 INSUFFICIENT_TOTAL，初分 0.28，排名分 0.28 / 2 VALID，初分 21.78，排名分 21.78 |
| 验证组C | 38 | S4 | BRANCH_2 | 0 INSUFFICIENT_TOTAL，初分 0.28，排名分 0.28 / 2 VALID，初分 21.78，排名分 21.78 |
| 验证组C | 510 | S1 | BRANCH_1 | 0 MOUTH_DEAD_END，初分 11.64，排名分 23.59 / 1 VALID，初分 324.87，排名分 673.82 / 2 INSUFFICIENT_TOTAL，初分 7.06，排名分 7.06 |
| 验证组C | 510 | S2 | BRANCH_1 | 0 MOUTH_DEAD_END，初分 11.64，排名分 23.59 / 1 VALID，初分 324.87，排名分 673.82 / 2 INSUFFICIENT_TOTAL，初分 7.06，排名分 7.06 |
| 验证组C | 510 | S3 | BRANCH_1 | 0 MOUTH_DEAD_END，初分 11.64，排名分 23.59 / 1 VALID，初分 324.87，排名分 673.82 / 2 INSUFFICIENT_TOTAL，初分 7.06，排名分 7.06 |
| 验证组C | 510 | S4 | BRANCH_1 | 0 MOUTH_DEAD_END，初分 11.64，排名分 23.59 / 1 VALID，初分 324.87，排名分 673.82 / 2 INSUFFICIENT_TOTAL，初分 7.06，排名分 7.06 |

| 组 | 点位 | 锁下游峰 | 锁桥接空白 | 静态延伸撤销 | 保送被拒 | 新叉根候选 | 新叉根最终获选 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | original | 0 | 0 | 3 | 0 | 0 | 0 |
| 三点弯 | original | 49 | 2 | 13 | 259 | 0 | 0 |
| 验证组C | original | 23 | 0 | 4 | 49 | 2 | 0 |
| 验证组C | bright | 24 | 0 | 4 | 44 | 1 | 0 |

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
| 验证组C | 38 | original | S4 | 16 | 16 | 15 | 16 | 15 | 13 |
| 验证组C | 38 | bright | V5.10 | 16 | 16 | 15 | 16 | 6 | 4 |
| 验证组C | 38 | bright | S1 | 16 | 16 | 15 | 16 | 15 | 13 |
| 验证组C | 38 | bright | S2 | 16 | 16 | 15 | 16 | 15 | 13 |
| 验证组C | 38 | bright | S3 | 16 | 16 | 15 | 16 | 15 | 13 |
| 验证组C | 38 | bright | S4 | 16 | 16 | 15 | 16 | 15 | 13 |
| 验证组C | 54 | original | V5.10 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | original | S1 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | original | S2 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | original | S3 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | original | S4 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | bright | V5.10 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | bright | S1 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | bright | S2 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | bright | S3 | 12 | 12 | 12 | 12 | 12 | 12 |
| 验证组C | 54 | bright | S4 | 12 | 12 | 12 | 12 | 12 | 12 |

按同一 V5.10 端点后人工标注路径取样，纵向容差 ±2 px。通过列表示该列五个像素内至少一个满足对应条件，各条件可能来自不同像素。保留列要求同一像素同时具备红色差分并通过静态与偶极子筛选。

## 三点弯模块计时

同组 20 个原始输入，预热后逐帧配对，同一进程、单 OpenCV 线程，单位为平均毫秒。嵌套调用按独占时间归属；S3 和 S4 使用同一封存的上游映射。此项用于定位耗时，全序列 FPS 见前表。

| 模块 | V5.12 S3 | V5.12 S4 | 变化 ms |
| --- | --- | --- | --- |
| 缺口与 ROI 准备 | 10.56 | 10.91 | 0.36 |
| 局部配准 | 27.02 | 27.43 | 0.41 |
| 证据场（扣除局部配准） | 123.10 | 104.12 | -18.98 |
| 差分形态与偶极子邻域 | 41.07 | 30.30 | -10.77 |
| 动态规划 | 3.73 | 3.77 | 0.04 |
| 下游峰（旧峰搜索） | 9.30 | 3.56 | -5.74 |
| 桥接（候选生成） | 0.33 | 0.34 | 0.01 |
| 其余检测与门控 | 4.64 | 4.55 | -0.09 |
| 单帧合计 | 219.76 | 184.98 | -34.78 |

采用同一进程对三点弯 20 个相同帧作预热后配对计时，单位为 ms/帧。各模块扣除已单列子调用。全序列主表为单工作进程逐帧统计；V5.11 历史主表为四进程，跨轮速度同时受并发度影响。

| 固定四工作进程、交错先后顺序 | 520 帧 full FPS | 复现封存尖端及状态 |
| --- | --- | --- |
| V5.11 | 4.02 | 520 |
| V5.12 | 3.43 | 520 |

另外从三点弯的 520 张原始 BMP 逐帧重建裁框与上游映射，使用各帧已提供的测量点。含上游映射和检测的速度为 2.88 FPS，其中 520/520 帧与封存结果的状态、路径和尖端相同。计时包含首次调用，排除读盘、点跟踪与渲染。[520 帧耗时](../../output/experiments/v512_stabilize_r01/uncached_tpb_seconds.csv)

## 全部可见失败帧

每个 full 与 raw_only 失败分别列出，涵盖验证组C两套点位。通过率为通过列数除以可评列数，偶极放行表示该列搜索带存在通过偶极筛选的像素。raw_only 的差分指标来自同点位配套参考，是诊断对照。无可信差分配准时按零局部位移重放，证据不能解释为运行时采用。[逐列原始标志](../../output/experiments/v512_stabilize_r01/individual_columns.csv)

### 开发组A · original · full

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 398 | 12.10 | 1.00/0.99 | 多追预测段 1326–1337 | 12 | 67% / 92% / 67% / 100% / 58% | 4 | BRANCH_0；0 VALID 总分 391.99→391.99，排名分 896.14 | 分支 0。端点相对标注横向 +11.8、纵向 +2.4 px。终点由本分支累计得分峰给出。 初始峰 [1337, 1164]，最终 [1337, 1164]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_a/original/full/0398.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_a/original/full/0398.png) |

### 开发组A · original · raw_only

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 398 | 12.10 | 1.00/0.99 | 多追预测段 1326–1337 | 12 | 67% / 92% / 67% / 100% / 58% | 4 | BRANCH_0；0 VALID 总分 —→272.39，排名分 513.54 | 分支 0。端点相对标注横向 +11.8、纵向 +2.4 px。终点由本分支累计得分峰给出。 初始峰 [1337, 1164]，最终 [1337, 1164]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_a/original/raw_only/0398.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_a/original/raw_only/0398.png) |
| 504 | 20.97 | 0.97/1.00 | 漏追人工段 1360–1379 | 20 | 55% / 15% / 55% / 100% / 15% | 3 | BRANCH_0；0 VALID 总分 —→295.23，排名分 551.98 | 分支 0。端点相对标注横向 -21.0、纵向 +0.4 px。终点由本分支累计得分峰给出。 初始峰 [1359, 1159]，最终 [1359, 1159]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_a/original/raw_only/0504.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_a/original/raw_only/0504.png) |

### 三点弯 · original · raw_only

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 96.62 | 0.00/0.00 | 多追预测段 1493–1562 | 70 | 0% / 0% / 94% / 100% / 0% | 0 | BRANCH_0；0 VALID 总分 —→16.95，排名分 55.95；2 VALID 总分 —→12.46，排名分 23.51 | 分支 0。端点相对标注横向 +69.9、纵向 -66.8 px。终点由本分支累计得分峰给出。 初始峰 [1562, 2665]，最终 [1562, 2665]。 [图](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0001.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0001.png) |
| 144 | 19.40 | 0.67/0.63 | 多追预测段 1532–1551 | 20 | 5% / 0% / 100% / 100% / 0% | 0 | BRANCH_2；0 VALID 总分 —→18.33，排名分 58.63；2 VALID 总分 —→23.96，排名分 61.01 | 分支 2。端点相对标注横向 +19.2、纵向 -2.5 px。终点由本分支累计得分峰给出。 初始峰 [1551, 2711]，最终 [1551, 2711]。 [图](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0144.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0144.png) |
| 178 | 20.94 | 0.78/0.68 | 多追预测段 1540–1558 | 19 | 53% / 47% / 100% / 100% / 47% | 9 | BRANCH_2；0 VALID 总分 —→17.41，排名分 58.36；2 VALID 总分 —→25.74，排名分 71.24 | 分支 2。端点相对标注横向 +18.6、纵向 -9.6 px。终点由本分支累计得分峰给出。 初始峰 [1558, 2708]，最终 [1558, 2708]。 [图](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0178.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0178.png) |
| 271 | 22.48 | 0.94/0.98 | 漏追人工段 1641–1661 | 21 | 95% / 100% / 95% / 100% / 95% | 20 | BRANCH_1；0 VALID 总分 —→28.58，排名分 75.38；1 VALID 总分 —→68.86，排名分 167.01 | 分支 1。端点相对标注横向 -22.2、纵向 +3.5 px。终点由本分支累计得分峰给出。 初始峰 [1640, 2724]，最终 [1640, 2724]。 [图](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0271.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0271.png) |
| 347 | 14.43 | 0.93/0.93 | 漏追人工段 1698–1711 | 14 | 100% / 100% / 100% / 100% / 100% | 14 | BRANCH_2；0 VALID 总分 —→82.30，排名分 206.45；2 VALID 总分 —→103.31，排名分 237.86 | 分支 2。端点相对标注横向 -14.3、纵向 -1.9 px。终点由本分支累计得分峰给出。 初始峰 [1697, 2719]，最终 [1697, 2719]。 [图](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0347.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0347.png) |
| 381 | 14.18 | 0.94/0.94 | 漏追人工段 1728–1741 | 14 | 100% / 50% / 86% / 100% / 50% | 6 | BRANCH_2；0 VALID 总分 —→91.66，排名分 232.06；2 VALID 总分 —→111.97，排名分 262.77 | 分支 2。端点相对标注横向 -14.2、纵向 -0.2 px。终点由本分支累计得分峰给出。 初始峰 [1727, 2721]，最终 [1727, 2721]。 [图](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0381.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0381.png) |
| 407 | 27.98 | 0.88/0.91 | 漏追人工段 1738–1764 | 27 | 78% / 41% / 81% / 100% / 41% | 11 | BRANCH_2；0 VALID 总分 —→102.86，排名分 252.36；2 VALID 总分 —→123.00，排名分 281.60 | 分支 2。端点相对标注横向 -27.9、纵向 +1.5 px。终点由本分支累计得分峰给出。 初始峰 [1737, 2721]，最终 [1737, 2721]。 [图](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0407.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0407.png) |
| 476 | 18.54 | 0.94/0.94 | 漏追人工段 1764–1781 | 18 | 100% / 100% / 100% / 100% / 100% | 18 | BRANCH_2；0 VALID 总分 —→122.77，排名分 292.42；2 VALID 总分 —→142.56，排名分 318.71 | 分支 2。端点相对标注横向 -18.4、纵向 +2.0 px。终点由本分支累计得分峰给出。 初始峰 [1763, 2722]，最终 [1763, 2722]。 [图](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0476.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/raw_only/0476.png) |

### 三点弯 · original · full

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 144 | 29.55 | 0.60/1.00 | 漏追人工段 1507–1531 | 25 | 36% / 28% / 96% / 100% / 24% | 6 | BRANCH_2；0 VALID 总分 25.69→25.69，排名分 9.94，独有红/蓝 2/0；1 INSUFFICIENT_TOTAL 总分 10.54→10.54，排名分 15.94；2 VALID 总分 49.59→49.59，排名分 202.88，独有红/蓝 29/0 | 分支 2。端点相对标注横向 -25.8、纵向 +14.5 px。终点由本分支累计得分峰给出。 初始峰 [1506, 2728]，最终 [1506, 2728]。 [图](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/full/0144.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/full/0144.png) |
| 178 | 25.38 | 0.60/0.94 | 漏追人工段 1521–1539 | 19 | 37% / 21% / 100% / 100% / 16% | 2 | BRANCH_2；0 MOUTH_DEAD_END 总分 32.33→32.33，排名分 41.78；1 INSUFFICIENT_TOTAL 总分 6.78→6.78，排名分 18.93；2 VALID 总分 54.08→54.08，排名分 91.88 | 分支 2。端点相对标注横向 -19.4、纵向 +16.4 px。终点由本分支累计得分峰给出。 初始峰 [1520, 2734]，最终 [1520, 2734]。 [图](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/full/0178.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/full/0178.png) |
| 215 | 85.76 | 0.31/0.91 | 漏追人工段 1521–1603 | 83 | 82% / 67% / 98% / 100% / 67% | 55 | BRANCH_2；0 MOUTH_DEAD_END 总分 34.62→34.62，排名分 42.72；1 DETACHED_RESCUE 总分 9.04→102.46，排名分 234.61，保送；2 VALID 总分 55.73→55.73，排名分 96.23 | 分支 2。端点相对标注横向 -85.0、纵向 +11.4 px。终点由本分支累计得分峰给出。 初始峰 [1520, 2730]，最终 [1520, 2730]。 [图](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/full/0215.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/full/0215.png) |
| 248 | 111.20 | 0.25/0.91 | 漏追人工段 1520–1629 | 110 | 90% / 80% / 99% / 100% / 78% | 58 | BRANCH_2；0 MOUTH_DEAD_END 总分 32.87→32.87，排名分 40.97；1 DETACHED_RESCUE 总分 8.60→145.81，排名分 312.51，保送；2 VALID 总分 55.92→55.92，排名分 95.07 | 分支 2。端点相对标注横向 -110.9、纵向 +7.8 px。终点由本分支累计得分峰给出。 初始峰 [1519, 2733]，最终 [1519, 2733]。 [图](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/full/0248.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/full/0248.png) |
| 407 | 18.28 | 0.97/0.97 | 漏追人工段 1748–1764 | 17 | 65% / 6% / 71% / 100% / 6% | 1 | BRANCH_2；0 VALID 总分 30.17→30.17，排名分 10.56，独有红/蓝 0/0；1 VALID 总分 130.44→130.44，排名分 538.03，独有红/蓝 27/0；2 VALID 总分 154.97→154.97，排名分 704.81，独有红/蓝 57/2 | 分支 2。端点相对标注横向 -17.9、纵向 +3.5 px。终点由本分支累计得分峰给出。 初始峰 [1747, 2723]，最终 [1747, 2723]。 [图](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/full/0407.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/full/0407.png) |
| 503 | 14.91 | 1.00/0.95 | 多追预测段 1787–1801 | 15 | 100% / 100% / 100% / 100% / 100% | 15 | BRANCH_1；0 VALID 总分 160.75→160.75，排名分 493.50，独有红/蓝 26/0；1 VALID 总分 198.80→198.80，排名分 617.25，独有红/蓝 90/0 | 分支 1。端点相对标注横向 +14.0、纵向 +5.0 px。终点由本分支累计得分峰给出。 初始峰 [1801, 2725]，最终 [1801, 2725]。 [图](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/full/0503.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/three_point_bend/original/full/0503.png) |

### 验证组C · original · full

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 38 | 18.15 | 0.49/0.77 | 漏追人工段 2274–2289 | 16 | 100% / 94% / 100% / 100% / 94% | 13 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 0.28→0.28，排名分 0.28；2 VALID 总分 21.78→21.78，排名分 21.78 | 分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/original/full/0038.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/original/full/0038.png) |
| 510 | 14.95 | 1.00/0.98 | 多追预测段 2491–2505 | 15 | 100% / 100% / 100% / 100% / 100% | 15 | BRANCH_1；0 MOUTH_DEAD_END 总分 5.30→5.30，排名分 15.30；1 VALID 总分 324.88→324.88，排名分 673.83；2 INSUFFICIENT_TOTAL 总分 7.06→7.06，排名分 7.06 | 分支 1。端点相对标注横向 +14.9、纵向 +0.4 px。终点由本分支累计得分峰给出。 初始峰 [2505, 2346]，最终 [2505, 2346]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/original/full/0510.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/original/full/0510.png) |

### 验证组C · original · raw_only

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 38 | 18.15 | 0.49/0.77 | 漏追人工段 2274–2289 | 16 | 100% / 94% / 100% / 100% / 94% | 13 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.28，排名分 0.93；2 VALID 总分 —→17.94，排名分 34.19 | 分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0038.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0038.png) |
| 54 | 28.94 | 0.44/0.93 | 漏追人工段 2275–2301 | 27 | 100% / 100% / 100% / 100% / 100% | 27 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.52，排名分 1.82；1 INSUFFICIENT_TOTAL 总分 —→2.02，排名分 6.57；2 VALID 总分 —→17.86，排名分 33.46 | 分支 2。端点相对标注横向 -27.5、纵向 +9.0 px。终点由本分支累计得分峰给出。 初始峰 [2274, 2340]，最终 [2274, 2340]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0054.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0054.png) |
| 69 | 13.62 | 0.94/0.93 | 漏追人工段 2291–2303 | 13 | 100% / 100% / 100% / 100% / 100% | 13 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→1.05，排名分 2.35；1 INSUFFICIENT_TOTAL 总分 —→1.59，排名分 6.14；2 VALID 总分 —→18.12，排名分 41.52 | 分支 2。端点相对标注横向 -13.6、纵向 +0.6 px。终点由本分支累计得分峰给出。 初始峰 [2290, 2332]，最终 [2290, 2332]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0069.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0069.png) |
| 95 | 25.25 | 0.81/0.96 | 漏追人工段 2304–2327 | 24 | 92% / 96% / 100% / 100% / 88% | 18 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.37，排名分 1.02；1 VALID 总分 —→19.94，排名分 48.54；2 VALID 总分 —→21.48，排名分 49.43 | 分支 2。端点相对标注横向 -24.6、纵向 -5.6 px。终点由本分支累计得分峰给出。 初始峰 [2303, 2331]，最终 [2303, 2331]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0095.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0095.png) |
| 232 | 12.02 | 0.99/1.00 | 漏追人工段 2409–2420 | 12 | 92% / 83% / 100% / 100% / 75% | 7 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.19，排名分 0.84；1 VALID 总分 —→114.10，排名分 214.85；2 INSUFFICIENT_TOTAL 总分 —→9.20，排名分 19.60 | 分支 1。端点相对标注横向 -12.0、纵向 +0.7 px。终点由本分支累计得分峰给出。 初始峰 [2408, 2345]，最终 [2408, 2345]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0232.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0232.png) |
| 324 | 27.53 | 1.00/0.93 | 多追预测段 2464–2486 | 23 | 87% / 57% / 96% / 100% / 57% | 7 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.45，排名分 1.75；1 VALID 总分 —→167.13，排名分 316.63；2 INSUFFICIENT_TOTAL 总分 —→8.65，排名分 19.05 | 分支 1。端点相对标注横向 +22.3、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0324.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0324.png) |
| 335 | 23.40 | 1.00/0.94 | 多追预测段 2471–2487 | 17 | 65% / 35% / 94% / 100% / 35% | 6 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.93，排名分 2.88；1 VALID 总分 —→171.10，排名分 322.55；2 INSUFFICIENT_TOTAL 总分 —→9.14，排名分 20.19 | 分支 1。端点相对标注横向 +16.8、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2487, 2329]，最终 [2487, 2329]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0335.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0335.png) |
| 345 | 20.10 | 1.00/0.95 | 多追预测段 2474–2486 | 13 | 69% / 38% / 100% / 100% / 38% | 5 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.29，排名分 1.59；1 VALID 总分 —→171.57，排名分 322.37；2 INSUFFICIENT_TOTAL 总分 —→8.34，排名分 18.74 | 分支 1。端点相对标注横向 +12.5、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0345.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0345.png) |
| 363 | 16.12 | 0.99/0.96 | 多追预测段 2484–2486 | 3 | 100% / 33% / 100% / 100% / 33% | 1 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.37，排名分 1.02；1 INSUFFICIENT_TOTAL 总分 —→1.63，排名分 6.83；2 VALID 总分 —→172.26，排名分 324.36 | 分支 2。端点相对标注横向 +3.0、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0363.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/original/raw_only/0363.png) |

### 验证组C · bright · full

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 38 | 18.15 | 0.49/0.77 | 漏追人工段 2274–2289 | 16 | 100% / 94% / 100% / 100% / 94% | 13 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 0.28→0.28，排名分 0.28；2 VALID 总分 21.78→21.78，排名分 21.78 | 分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/full/0038.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/full/0038.png) |
| 510 | 14.95 | 1.00/0.98 | 多追预测段 2491–2505 | 15 | 100% / 100% / 100% / 100% / 100% | 15 | BRANCH_1；0 MOUTH_DEAD_END 总分 11.64→11.64，排名分 23.59；1 VALID 总分 324.87→324.87，排名分 673.82；2 INSUFFICIENT_TOTAL 总分 7.06→7.06，排名分 7.06 | 分支 1。端点相对标注横向 +14.9、纵向 +0.4 px。终点由本分支累计得分峰给出。 初始峰 [2505, 2346]，最终 [2505, 2346]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/full/0510.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/full/0510.png) |

### 验证组C · bright · raw_only

| 帧 | 误差 px | 覆盖/精确 | 审计区段 | 列数 | 红/细脊/暗谷/偶极放行/保留 | 最长 | 选择与候选 | 终止原因和图 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 38 | 18.15 | 0.49/0.77 | 漏追人工段 2274–2289 | 16 | 100% / 94% / 100% / 100% / 94% | 13 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.28，排名分 0.93；2 VALID 总分 —→17.94，排名分 34.19 | 分支 2。端点相对标注横向 -16.5、纵向 +7.6 px。终点由本分支累计得分峰给出。 初始峰 [2273, 2339]，最终 [2273, 2339]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0038.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0038.png) |
| 54 | 28.94 | 0.44/0.93 | 漏追人工段 2275–2301 | 27 | 100% / 100% / 100% / 100% / 100% | 27 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.52，排名分 1.82；1 INSUFFICIENT_TOTAL 总分 —→2.02，排名分 6.57；2 VALID 总分 —→17.86，排名分 33.46 | 分支 2。端点相对标注横向 -27.5、纵向 +9.0 px。终点由本分支累计得分峰给出。 初始峰 [2274, 2340]，最终 [2274, 2340]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0054.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0054.png) |
| 69 | 13.62 | 0.94/0.93 | 漏追人工段 2291–2303 | 13 | 100% / 100% / 100% / 100% / 100% | 13 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→1.05，排名分 2.35；1 INSUFFICIENT_TOTAL 总分 —→1.59，排名分 6.14；2 VALID 总分 —→18.12，排名分 41.52 | 分支 2。端点相对标注横向 -13.6、纵向 +0.6 px。终点由本分支累计得分峰给出。 初始峰 [2290, 2332]，最终 [2290, 2332]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0069.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0069.png) |
| 95 | 25.25 | 0.81/0.96 | 漏追人工段 2304–2327 | 24 | 92% / 96% / 100% / 100% / 88% | 18 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.37，排名分 1.02；1 VALID 总分 —→19.94，排名分 48.54；2 VALID 总分 —→21.48，排名分 49.43 | 分支 2。端点相对标注横向 -24.6、纵向 -5.6 px。终点由本分支累计得分峰给出。 初始峰 [2303, 2331]，最终 [2303, 2331]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0095.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0095.png) |
| 232 | 12.02 | 0.99/1.00 | 漏追人工段 2409–2420 | 12 | 92% / 83% / 100% / 100% / 75% | 7 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.19，排名分 0.84；1 VALID 总分 —→114.10，排名分 214.85；2 INSUFFICIENT_TOTAL 总分 —→9.20，排名分 19.60 | 分支 1。端点相对标注横向 -12.0、纵向 +0.7 px。终点由本分支累计得分峰给出。 初始峰 [2408, 2345]，最终 [2408, 2345]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0232.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0232.png) |
| 324 | 27.53 | 1.00/0.93 | 多追预测段 2464–2486 | 23 | 87% / 57% / 96% / 100% / 57% | 7 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.45，排名分 1.75；1 VALID 总分 —→167.13，排名分 316.63；2 INSUFFICIENT_TOTAL 总分 —→8.65，排名分 19.05 | 分支 1。端点相对标注横向 +22.3、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0324.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0324.png) |
| 335 | 23.40 | 1.00/0.94 | 多追预测段 2471–2487 | 17 | 65% / 35% / 94% / 100% / 35% | 6 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.93，排名分 2.88；1 VALID 总分 —→171.10，排名分 322.55；2 INSUFFICIENT_TOTAL 总分 —→9.14，排名分 20.19 | 分支 1。端点相对标注横向 +16.8、纵向 -16.2 px。终点由本分支累计得分峰给出。 初始峰 [2487, 2329]，最终 [2487, 2329]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0335.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0335.png) |
| 345 | 20.10 | 1.00/0.95 | 多追预测段 2474–2486 | 13 | 69% / 38% / 100% / 100% / 38% | 5 | BRANCH_1；0 INSUFFICIENT_TOTAL 总分 —→0.29，排名分 1.59；1 VALID 总分 —→171.57，排名分 322.37；2 INSUFFICIENT_TOTAL 总分 —→8.34，排名分 18.74 | 分支 1。端点相对标注横向 +12.5、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0345.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0345.png) |
| 363 | 16.12 | 0.99/0.96 | 多追预测段 2484–2486 | 3 | 100% / 33% / 100% / 100% / 33% | 1 | BRANCH_2；0 INSUFFICIENT_TOTAL 总分 —→0.37，排名分 1.02；1 INSUFFICIENT_TOTAL 总分 —→1.63，排名分 6.83；2 VALID 总分 —→172.26，排名分 324.36 | 分支 2。端点相对标注横向 +3.0、纵向 -15.8 px。终点由本分支累计得分峰给出。 初始峰 [2486, 2330]，最终 [2486, 2330]。 [图](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0363.jpg) [曲线](../../output/experiments/v512_stabilize_r01/failures/group_c/bright/raw_only/0363.png) |

## 验收决定

V5.12 暂不替换 V5.10。主点位 Joint 从 V5.11 的 41/54 回升到 45/54，仍低于 V5.10 的 46/54；三点弯有 1 帧误差超过 100 px。开发组A 299 的十种扰动保持 0 px；三组固定配准扰动均为 0 px。重建参考后，开发组A全组最大 7.00 px，三点弯在 248 帧达到 119.34 px，验证组C亮区最大 4.00 px。合成孤立划痕 36/36、变形划痕 24/36、弱材料桥接 36/36、弱缺口 216/216、活跃分叉 30/36、负样本误报 0/468。下一轮宜在开发材料构造同长度空白、不同下游支撑强度的配对样本，先验证能否区分真实漏追与跳入背景，再考虑调整空白锁。 三点弯复用上游映射的单工作进程主测为 5.43 FPS；相同四进程负载下，520 帧配对的 V5.11、V5.12 分别为 4.02、3.43 FPS。四进程下 V5.12 未达到 4 FPS，不能根据单工作进程主测认定跨负载提速。

[逐帧四联图与差分 PNG](../../output/experiments/v512_stabilize_r01/difference_views/index.html) · [开发组A视频](../../output/experiments/v512_stabilize_r01/difference_views/group_a.mp4) · [三点弯视频](../../output/experiments/v512_stabilize_r01/difference_views/three_point_bend.mp4) · [验证组C视频](../../output/experiments/v512_stabilize_r01/difference_views/group_c.mp4) · [逐帧裂纹长度（px）](../../output/experiments/v512_stabilize_r01/crack_lengths.csv) · [主点位失败帧图包](../../output/experiments/v512_stabilize_r01/difference_views/failure_views.zip) · [失败审计](FAILURES_AUDIT.md)
