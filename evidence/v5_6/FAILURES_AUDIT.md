# V5.6 失败与退化帧专项分析

完整模式四栏图对应本版发布结果。统计相对对照版的尖端误差增加、路径覆盖/精度下降，以及缺失有效结果。

## 开发组A

### 67 · raw_only · 联合失败

人工 [995.2169076751946, 1143.1590656284761]，预测 —，误差 — px（v5_4 0.27，v5_5 0.27）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

入口已产生候选，全部被拒绝。{'LOW_SUPPORT': 2}。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_a/0067_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_a/0067.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_a/0067.jpg)

### 122 · full · 命中但局部指标退化

人工 [1066.4310954063603, 1156.1413427561838]，预测 (1067.00, 1158.00)，误差 1.94 px（v5_4 0.45，v5_5 0.45）。dx/dy 0.57 / 1.86；路径覆盖 / 精度 1.00 / 1.00。v5_4/尖端误差, v5_5/尖端误差。

选中入口 0，有效支撑 109 列、全路双通道一致比例 0.83。 实际起追 [958, 1146]，与人工路径最左点相距 5.96 px。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_a/0122_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_a/0122.jpg)

### 241 · full · 命中但局部指标退化

人工 [1182.590570719603, 1160.0496277915631]，预测 (1178.00, 1158.00)，误差 5.03 px（v5_4 4.13，v5_5 4.13）。dx/dy -4.59 / -2.05；路径覆盖 / 精度 1.00 / 1.00。v5_4/尖端误差, v5_5/尖端误差。

选中入口 0，有效支撑 216 列、全路双通道一致比例 0.92。 实际起追 [960, 1146]，与人工路径最左点相距 3.63 px。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_a/0241_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_a/0241.jpg)

### 299 · full · 联合失败

人工 [1247.703180212014, 1159.6749116607773]，预测 (1229.00, 1162.00)，误差 18.85 px（v5_4 0.44，v5_5 0.44）。dx/dy -18.70 / 2.33；路径覆盖 / 精度 0.97 / 1.00。v5_4/尖端误差, v5_4/覆盖, v5_5/尖端误差, v5_5/覆盖。

选中入口 0，有效支撑 269 列、全路双通道一致比例 0.94。全部入口的最终候选中最近者仍离人工端点 18.85 px，误差已出现在分支内选峰或支撑构造阶段。 实际起追 [960, 1150]，与人工路径最左点相距 3.33 px。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_a/0299_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_a/0299.jpg)

### 299 · raw_only · 联合失败

人工 [1247.703180212014, 1159.6749116607773]，预测 (1239.00, 1165.00)，误差 10.20 px（v5_4 5.25，v5_5 5.25）。dx/dy -8.70 / 5.33；路径覆盖 / 精度 1.00 / 1.00。v5_4/尖端误差, v5_4/覆盖, v5_5/尖端误差, v5_5/覆盖。

选中入口 0，有效支撑 275 列、全路双通道一致比例 0.00。全部入口的最终候选中最近者仍离人工端点 10.20 px，误差已出现在分支内选峰或支撑构造阶段。 实际起追 [960, 1147]，与人工路径最左点相距 3.20 px。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_a/0299_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_a/0299.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_a/0299.jpg)

### 308 · raw_only · 命中但局部指标退化

人工 [1252.6785714285716, 1158.0238095238094]，预测 (1249.00, 1160.00)，误差 4.18 px（v5_4 0.68，v5_5 0.68）。dx/dy -3.68 / 1.98；路径覆盖 / 精度 1.00 / 1.00。v5_4/尖端误差, v5_5/尖端误差。

选中入口 0，有效支撑 289 列、全路双通道一致比例 0.00。 实际起追 [960, 1148]，与人工路径最左点相距 3.85 px。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_a/0308_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_a/0308.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_a/0308.jpg)

### 366 · full · 命中但局部指标退化

人工 [1315.0724637681158, 1159.4202898550725]，预测 (1313.00, 1160.00)，误差 2.15 px（v5_4 1.15，v5_5 1.15）。dx/dy -2.07 / 0.58；路径覆盖 / 精度 1.00 / 1.00。v5_4/尖端误差, v5_5/尖端误差。

选中入口 0，有效支撑 335 列、全路双通道一致比例 0.91。 实际起追 [963, 1149]，与人工路径最左点相距 2.36 px。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_a/0366_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_a/0366.jpg)

### 398 · full · 联合失败

人工 [1325.1507352941178, 1161.5514705882351]，预测 (1337.00, 1164.00)，误差 12.10 px（v5_4 12.10，v5_5 12.10）。dx/dy 11.85 / 2.45；路径覆盖 / 精度 1.00 / 0.99。。

选中入口 0，有效支撑 325 列、全路双通道一致比例 0.84。全部入口的最终候选中最近者仍离人工端点 12.10 px，误差已出现在分支内选峰或支撑构造阶段。 实际起追 [961, 1151]，与人工路径最左点相距 1.47 px。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_a/0398_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_a/0398.jpg)

### 398 · raw_only · 联合失败

人工 [1325.1507352941178, 1161.5514705882351]，预测 (1337.00, 1164.00)，误差 12.10 px（v5_4 12.10，v5_5 12.10）。dx/dy 11.85 / 2.45；路径覆盖 / 精度 1.00 / 0.99。。

选中入口 0，有效支撑 371 列、全路双通道一致比例 0.00。全部入口的最终候选中最近者仍离人工端点 12.10 px，误差已出现在分支内选峰或支撑构造阶段。 实际起追 [961, 1151]，与人工路径最左点相距 1.47 px。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_a/0398_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_a/0398.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_a/0398.jpg)

### 504 · raw_only · 联合失败

人工 [1379.9691833590139, 1158.5516178736518]，预测 (1359.00, 1159.00)，误差 20.97 px（v5_4 20.97，v5_5 20.97）。dx/dy -20.97 / 0.45；路径覆盖 / 精度 0.97 / 1.00。。

选中入口 0，有效支撑 397 列、全路双通道一致比例 0.00。全部入口的最终候选中最近者仍离人工端点 20.97 px，误差已出现在分支内选峰或支撑构造阶段。 实际起追 [963, 1149]，与人工路径最左点相距 0.78 px。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_a/0504_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_a/0504.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_a/0504.jpg)

## 三点弯

### 1 · full · 联合失败

人工 [1492.142857142857, 2731.7532467532465]，预测 —，误差 — px（v5_4 64.04，v5_5 64.04）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/失去端点, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0001_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0001.jpg)

### 1 · raw_only · 联合失败

人工 [1492.142857142857, 2731.7532467532465]，预测 —，误差 — px（v5_4 64.04，v5_5 64.04）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/失去端点, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0001_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0001.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0001.jpg)

### 144 · full · 联合失败

人工 [1531.764705882353, 2713.529411764706]，预测 —，误差 — px（v5_4 22.75，v5_5 22.75）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0144_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0144.jpg)

### 144 · raw_only · 联合失败

人工 [1531.764705882353, 2713.529411764706]，预测 —，误差 — px（v5_4 18.57，v5_5 18.57）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0144_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0144.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0144.jpg)

### 178 · full · 联合失败

人工 [1539.4117647058824, 2717.6470588235293]，预测 —，误差 — px（v5_4 25.48，v5_5 25.48）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0178_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0178.jpg)

### 178 · raw_only · 联合失败

人工 [1539.4117647058824, 2717.6470588235293]，预测 —，误差 — px（v5_4 20.94，v5_5 20.94）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0178_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0178.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0178.jpg)

### 215 · full · 联合失败

人工 [1604.9999999999998, 2718.5714285714284]，预测 —，误差 — px（v5_4 40.41，v5_5 40.41）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0215_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0215.jpg)

### 215 · raw_only · 联合失败

人工 [1604.9999999999998, 2718.5714285714284]，预测 —，误差 — px（v5_4 7.02，v5_5 7.02）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0215_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0215.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0215.jpg)

### 248 · full · 联合失败

人工 [1629.9212598425197, 2725.196850393701]，预测 —，误差 — px（v5_4 7.41，v5_5 7.41）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0248_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0248.jpg)

### 248 · raw_only · 联合失败

人工 [1629.9212598425197, 2725.196850393701]，预测 —，误差 — px（v5_4 9.86，v5_5 9.86）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0248_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0248.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0248.jpg)

### 271 · full · 联合失败

人工 [1662.2047244094488, 2720.472440944882]，预测 —，误差 — px（v5_4 3.25，v5_5 3.25）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0271_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0271.jpg)

### 271 · raw_only · 联合失败

人工 [1662.2047244094488, 2720.472440944882]，预测 —，误差 — px（v5_4 22.48，v5_5 22.48）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0271_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0271.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0271.jpg)

### 306 · full · 联合失败

人工 [1684.5192307692307, 2718.1730769230767]，预测 —，误差 — px（v5_4 2.49，v5_5 2.49）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0306_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0306.jpg)

### 306 · raw_only · 联合失败

人工 [1684.5192307692307, 2718.1730769230767]，预测 —，误差 — px（v5_4 9.69，v5_5 9.69）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0306_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0306.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0306.jpg)

### 335 · full · 联合失败

人工 [1700.9574468085107, 2722.2340425531916]，预测 —，误差 — px（v5_4 8.67，v5_5 8.67）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0335_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0335.jpg)

### 335 · raw_only · 联合失败

人工 [1700.9574468085107, 2722.2340425531916]，预测 —，误差 — px（v5_4 9.52，v5_5 9.52）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0335_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0335.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0335.jpg)

### 347 · full · 联合失败

人工 [1711.3043478260868, 2720.869565217391]，预测 —，误差 — px（v5_4 2.52，v5_5 2.52）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0347_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0347.jpg)

### 347 · raw_only · 联合失败

人工 [1711.3043478260868, 2720.869565217391]，预测 —，误差 — px（v5_4 14.43，v5_5 14.43）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0347_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0347.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0347.jpg)

### 381 · full · 联合失败

人工 [1741.1764705882354, 2721.1764705882356]，预测 —，误差 — px（v5_4 11.18，v5_5 11.18）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0381_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0381.jpg)

### 381 · raw_only · 联合失败

人工 [1741.1764705882354, 2721.1764705882356]，预测 —，误差 — px（v5_4 18.18，v5_5 18.18）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0381_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0381.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0381.jpg)

### 407 · full · 联合失败

人工 [1764.935064935065, 2719.4805194805194]，预测 —，误差 — px（v5_4 23.07，v5_5 23.07）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0407_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0407.jpg)

### 407 · raw_only · 联合失败

人工 [1764.935064935065, 2719.4805194805194]，预测 —，误差 — px（v5_4 27.98，v5_5 27.98）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0407_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0407.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0407.jpg)

### 413 · full · 联合失败

人工 [1742.7922077922078, 2722.6623376623374]，预测 (1756.00, 2722.00)，误差 13.22 px（v5_4 6.43，v5_5 6.43）。dx/dy 13.21 / -0.66；路径覆盖 / 精度 0.77 / 0.76。v5_4/尖端误差, v5_4/路径精度, v5_4/覆盖, v5_5/尖端误差, v5_5/路径精度, v5_5/覆盖。

选中入口 1，有效支撑 277 列、全路双通道一致比例 0.70。全部入口的最终候选中最近者仍离人工端点 13.22 px，误差已出现在分支内选峰或支撑构造阶段。 实际起追 [1474, 2686]，与人工路径最左点相距 43.16 px。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0413_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0413.jpg)

### 413 · raw_only · 联合失败

人工 [1742.7922077922078, 2722.6623376623374]，预测 (1744.00, 2722.00)，误差 1.38 px（v5_4 9.93，v5_5 9.93）。dx/dy 1.21 / -0.66；路径覆盖 / 精度 0.79 / 0.80。。

选中入口 1，有效支撑 256 列、全路双通道一致比例 0.00。另一个入口 0 的端点已进入容差，状态 VALID，其择优分 244.12，获胜分 308.56。 实际起追 [1474, 2687]，与人工路径最左点相距 42.16 px。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0413_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0413.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0413.jpg)

### 435 · full · 联合失败

人工 [1757.5961538461538, 2722.980769230769]，预测 —，误差 — px（v5_4 5.49，v5_5 5.49）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0435_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0435.jpg)

### 435 · raw_only · 联合失败

人工 [1757.5961538461538, 2722.980769230769]，预测 —，误差 — px（v5_4 4.70，v5_5 4.70）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0435_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0435.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0435.jpg)

### 476 · full · 联合失败

人工 [1781.4285714285713, 2719.9999999999995]，预测 (1789.00, 2719.00)，误差 7.64 px（v5_4 8.63，v5_5 8.63）。dx/dy 7.57 / -1.00；路径覆盖 / 精度 0.77 / 0.79。v5_4/路径精度, v5_4/覆盖, v5_5/路径精度, v5_5/覆盖。

选中入口 0，有效支撑 310 列、全路双通道一致比例 0.75。端点已命中，但覆盖或路径精度低于 80%。 实际起追 [1473, 2684]，与人工路径最左点相距 45.29 px。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0476_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0476.jpg)

### 476 · raw_only · 联合失败

人工 [1781.4285714285713, 2719.9999999999995]，预测 (1782.00, 2720.00)，误差 0.57 px（v5_4 18.54，v5_5 18.54）。dx/dy 0.57 / 0.00；路径覆盖 / 精度 0.80 / 0.79。。

选中入口 0，有效支撑 293 列、全路双通道一致比例 0.00。端点已命中，但覆盖或路径精度低于 80%。 实际起追 [1474, 2687]，与人工路径最左点相距 42.30 px。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0476_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0476.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0476.jpg)

### 503 · full · 联合失败

人工 [1786.9565217391303, 2719.9999999999995]，预测 —，误差 — px（v5_4 14.91，v5_5 14.91）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0503_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0503.jpg)

### 503 · raw_only · 联合失败

人工 [1786.9565217391303, 2719.9999999999995]，预测 —，误差 — px（v5_4 4.04，v5_5 4.04）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/three_point_bend/0503_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/three_point_bend/0503.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0503.jpg)

## 验证组C

### 1 · full · 联合失败

人工 [2276.176470588235, 2337.450980392157]，预测 —，误差 — px（v5_4 1.26，v5_5 1.26）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0001_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0001.jpg)

### 1 · raw_only · 联合失败

人工 [2276.176470588235, 2337.450980392157]，预测 —，误差 — px（v5_4 1.26，v5_5 1.26）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0001_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0001.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0001.jpg)

### 7 · full · 联合失败

人工 [2273.0289532293987, 2339.844097995546]，预测 —，误差 — px（v5_4 1.29，v5_5 1.29）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0007_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0007.jpg)

### 7 · raw_only · 联合失败

人工 [2273.0289532293987, 2339.844097995546]，预测 —，误差 — px（v5_4 1.29，v5_5 1.29）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0007_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0007.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0007.jpg)

### 38 · full · 联合失败

人工 [2289.459459459459, 2331.3513513513512]，预测 —，误差 — px（v5_4 0.58，v5_5 0.58）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0038_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0038.jpg)

### 38 · raw_only · 联合失败

人工 [2289.459459459459, 2331.3513513513512]，预测 —，误差 — px（v5_4 1.58，v5_5 1.58）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0038_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0038.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0038.jpg)

### 54 · full · 联合失败

人工 [2301.4880952380954, 2330.952380952381]，预测 —，误差 — px（v5_4 1.51，v5_5 1.51）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0054_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0054.jpg)

### 54 · raw_only · 联合失败

人工 [2301.4880952380954, 2330.952380952381]，预测 —，误差 — px（v5_4 1.51，v5_5 1.51）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0054_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0054.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0054.jpg)

### 69 · full · 联合失败

人工 [2303.610108303249, 2331.407942238267]，预测 —，误差 — px（v5_4 2.42，v5_5 2.42）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0069_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0069.jpg)

### 69 · raw_only · 联合失败

人工 [2303.610108303249, 2331.407942238267]，预测 —，误差 — px（v5_4 2.42，v5_5 2.42）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0069_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0069.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0069.jpg)

### 95 · full · 联合失败

人工 [2327.6339285714284, 2336.5625]，预测 —，误差 — px（v5_4 0.77，v5_5 0.77）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0095_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0095.jpg)

### 95 · raw_only · 联合失败

人工 [2327.6339285714284, 2336.5625]，预测 —，误差 — px（v5_4 0.77，v5_5 0.77）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0095_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0095.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0095.jpg)

### 121 · full · 联合失败

人工 [2344.621513944223, 2337.051792828685]，预测 —，误差 — px（v5_4 3.08，v5_5 3.08）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0121_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0121.jpg)

### 121 · raw_only · 联合失败

人工 [2344.621513944223, 2337.051792828685]，预测 —，误差 — px（v5_4 1.22，v5_5 1.22）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0121_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0121.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0121.jpg)

### 171 · full · 联合失败

人工 [2376.8896321070233, 2338.76254180602]，预测 —，误差 — px（v5_4 0.26，v5_5 0.26）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0171_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0171.jpg)

### 171 · raw_only · 联合失败

人工 [2376.8896321070233, 2338.76254180602]，预测 —，误差 — px（v5_4 2.04，v5_5 2.04）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0171_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0171.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0171.jpg)

### 195 · full · 联合失败

人工 [2384.262295081967, 2342.950819672131]，预测 —，误差 — px（v5_4 1.20，v5_5 1.20）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0195_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0195.jpg)

### 195 · raw_only · 联合失败

人工 [2384.262295081967, 2342.950819672131]，预测 —，误差 — px（v5_4 106.02，v5_5 106.02）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0195_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0195.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0195.jpg)

### 221 · full · 联合失败

人工 [2405.6140350877195, 2344.2105263157896]，预测 —，误差 — px（v5_4 7.43，v5_5 12.39）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0221_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0221.jpg)

### 221 · raw_only · 联合失败

人工 [2405.6140350877195, 2344.2105263157896]，预测 —，误差 — px（v5_4 87.67，v5_5 87.67）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0221_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0221.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0221.jpg)

### 232 · full · 联合失败

人工 [2420.0, 2344.285714285714]，预测 —，误差 — px（v5_4 1.23，v5_5 1.23）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0232_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0232.jpg)

### 232 · raw_only · 联合失败

人工 [2420.0, 2344.285714285714]，预测 —，误差 — px（v5_4 74.44，v5_5 74.44）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0232_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0232.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0232.jpg)

### 324 · full · 联合失败

人工 [2463.723404255319, 2346.170212765958]，预测 —，误差 — px（v5_4 13.33，v5_5 13.33）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0324_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0324.jpg)

### 324 · raw_only · 联合失败

人工 [2463.723404255319, 2346.170212765958]，预测 —，误差 — px（v5_4 33.34，v5_5 33.34）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0324_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0324.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0324.jpg)

### 335 · full · 联合失败

人工 [2470.1639344262294, 2345.245901639344]，预测 —，误差 — px（v5_4 8.15，v5_5 8.15）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0335_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0335.jpg)

### 335 · raw_only · 联合失败

人工 [2470.1639344262294, 2345.245901639344]，预测 —，误差 — px（v5_4 28.46，v5_5 28.46）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0335_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0335.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0335.jpg)

### 345 · full · 联合失败

人工 [2473.511029411765, 2345.7536764705883]，预测 —，误差 — px（v5_4 6.53，v5_5 6.53）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0345_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0345.jpg)

### 345 · raw_only · 联合失败

人工 [2473.511029411765, 2345.7536764705883]，预测 —，误差 — px（v5_4 24.92，v5_5 24.92）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0345_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0345.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0345.jpg)

### 363 · full · 联合失败

人工 [2483.032490974729, 2345.8483754512636]，预测 —，误差 — px（v5_4 2.20，v5_5 2.20）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0363_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0363.jpg)

### 363 · raw_only · 联合失败

人工 [2483.032490974729, 2345.8483754512636]，预测 —，误差 — px（v5_4 19.55，v5_5 19.55）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0363_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0363.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0363.jpg)

### 456 · full · 联合失败

人工 [2493.906882591093, 2343.7044534412958]，预测 —，误差 — px（v5_4 10.10，v5_5 10.10）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0456_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0456.jpg)

### 456 · raw_only · 联合失败

人工 [2493.906882591093, 2343.7044534412958]，预测 —，误差 — px（v5_4 8.20，v5_5 8.20）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0456_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0456.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0456.jpg)

### 469 · full · 联合失败

人工 [2493.2995951417006, 2345.5263157894738]，预测 —，误差 — px（v5_4 8.72，v5_5 8.72）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0469_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0469.jpg)

### 469 · raw_only · 联合失败

人工 [2493.2995951417006, 2345.5263157894738]，预测 —，误差 — px（v5_4 6.72，v5_5 6.72）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0469_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0469.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0469.jpg)

### 480 · full · 联合失败

人工 [2494.9772382397573, 2345.0531107739002]，预测 —，误差 — px（v5_4 8.02，v5_5 8.02）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0480_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0480.jpg)

### 480 · raw_only · 联合失败

人工 [2494.9772382397573, 2345.0531107739002]，预测 —，误差 — px（v5_4 7.02，v5_5 7.02）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0480_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0480.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0480.jpg)

### 510 · full · 联合失败

人工 [2490.0551470588234, 2345.5698529411766]，预测 —，误差 — px（v5_4 16.95，v5_5 16.95）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0510_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0510.jpg)

### 510 · raw_only · 联合失败

人工 [2490.0551470588234, 2345.5698529411766]，预测 —，误差 — px（v5_4 15.95，v5_5 15.95）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0510_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0510.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0510.jpg)

### 528 · full · 联合失败

人工 [2513.644646924829, 2344.510250569476]，预测 —，误差 — px（v5_4 0.82，v5_5 0.62）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0528_full.png) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0528.jpg)

### 528 · raw_only · 联合失败

人工 [2513.644646924829, 2344.510250569476]，预测 —，误差 — px（v5_4 0.82，v5_5 0.82）。dx/dy — / —；路径覆盖 / 精度 0.00 / 0.00。v5_4/路径精度, v5_4/覆盖, v5_4/失去端点, v5_5/路径精度, v5_5/覆盖, v5_5/失去端点。

未形成可竞争分支；终止状态 OPEN_FORK。口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。 [独立累计分曲线](../../output/experiments/v56_decoupled_20261120_r04/curves/group_c/0528_raw_only.png) [纯灰度四栏图](../../output/experiments/v56_decoupled_20261120_r04/raw_failures/group_c/0528.jpg) [完整模式四栏图](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0528.jpg)

## 基准标记是否进入裂纹判别

在冻结预测后，按正式算法的灰度阈值和四个截面重建暗区。用同一裁剪图的八连通标签核对暗带是否包含 P1/P2 中心。图中黄圈是实测点，粉红线是与标记中心同连通体的计数暗带，绿线是其余暗带。连通体号 0 表示该中心像素在此阈值下属于背景。

| 实验 | 原图与截面 | 图像根部 | 估计厚度 px | P1/P2 连通体号 | 标记暗段数 | 正式赞成票/4 | 事后去标记票数/4 |
|---|---|---|---|---|---|---|---|
| 三点弯 | [144](../../output/experiments/v56_decoupled_20261120_r04/marker_audit/0144.png) | [1474, 2684] | 47.0 | [0, 7] | 4 | 3 | 0 |
| 三点弯 | [178](../../output/experiments/v56_decoupled_20261120_r04/marker_audit/0178.png) | [1475, 2706] | 63.6 | [0, 7] | 4 | 2 | 0 |
| 三点弯 | [215](../../output/experiments/v56_decoupled_20261120_r04/marker_audit/0215.png) | [1474, 2706] | 64.8 | [0, 6] | 4 | 3 | 0 |
| 验证组C | [221](../../output/experiments/v56_decoupled_20261120_r04/marker_audit/0221.png) | [2248, 2342] | 37.8 | [1, 0] | 10 | 4 | 1 |
| 验证组C | [324](../../output/experiments/v56_decoupled_20261120_r04/marker_audit/0324.png) | [2248, 2343] | 38.4 | [1, 0] | 11 | 4 | 0 |
| 验证组C | [456](../../output/experiments/v56_decoupled_20261120_r04/marker_audit/0456.png) | [2248, 2342] | 37.8 | [1, 0] | 10 | 4 | 1 |
| 验证组C | [510](../../output/experiments/v56_decoupled_20261120_r04/marker_audit/0510.png) | [2247, 2345] | 38.4 | [1, 0] | 12 | 4 | 0 |

达到两票即触发 OPEN_FORK。最后一列仅重算拓扑判据，没有重新运行检测或计入验证命中。该实验表明，输入坐标平移稳定，仍可能把图像中的实体基准标记当作缺口几何。下一轮应在合成及开发图像里加入独立深色标记，只让属于缺口本体的壁面参与拓扑计票，并保留无坐标提示的标记对照。 [逐列连通体记录](../../output/experiments/v56_decoupled_20261120_r04/marker_audit/cross_sections.csv)

三点弯 520 帧中 477 帧触发 OPEN_FORK。在 15 帧可见标注中仅 2 帧输出有效尖端。上述 P2 连通体归因已逐帧复核 144、178、215，验证组C全部 562 帧触发该门。验证组C 221、324、456、510 的正式票数均为 4，事后去掉接触 P1 中心的连通体后分别为 1、0、1、0。此操作也可能同时去掉与标记相连的试件暗部，不能直接当作修复方法。其他触发帧仅统计停止原因。三个新阶段共享口门定位与拓扑门，S1 同时变更配准、尺度与入口构造，因此不能将相对 V5.4 的全部变化归因于多分支 DP。

## 指定帧独立分支比较

| 组 | 帧 | 人工尖端 | V5.4误差 | V5.5误差 | S1误差 | S2误差 | V5.6误差 | 输出尖端 | 覆盖 | 精度 | 弧长 px | 选择 | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 开发组A | [1](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_a/0001.jpg) | 不确定 | — | — | — | — | — | None | — | — | — | NONE | NO_LEGAL_BRANCH |
| 开发组A | [398](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_a/0398.jpg) | [1325.1507352941178, 1161.5514705882351] | 12.10 | 12.10 | 12.10 | 12.10 | 12.10 | [1337, 1164] | 1.00 | 0.99 | 416.55 | BRANCH_0 | ACCEPTED_PEAK |
| 三点弯 | [144](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0144.jpg) | [1531.764705882353, 2713.529411764706] | 22.75 | 22.75 | — | — | — | None | 0.00 | 0.00 | — | NONE | OPEN_FORK |
| 三点弯 | [178](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0178.jpg) | [1539.4117647058824, 2717.6470588235293] | 25.48 | 25.48 | — | — | — | None | 0.00 | 0.00 | — | NONE | OPEN_FORK |
| 三点弯 | [215](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/three_point_bend/0215.jpg) | [1604.9999999999998, 2718.5714285714284] | 40.41 | 40.41 | — | — | — | None | 0.00 | 0.00 | — | NONE | OPEN_FORK |
| 验证组C | [221](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0221.jpg) | [2405.6140350877195, 2344.2105263157896] | 7.43 | 12.39 | — | — | — | None | 0.00 | 0.00 | — | NONE | OPEN_FORK |
| 验证组C | [324](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0324.jpg) | [2463.723404255319, 2346.170212765958] | 13.33 | 13.33 | — | — | — | None | 0.00 | 0.00 | — | NONE | OPEN_FORK |
| 验证组C | [456](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0456.jpg) | [2493.906882591093, 2343.7044534412958] | 10.10 | 10.10 | — | — | — | None | 0.00 | 0.00 | — | NONE | OPEN_FORK |
| 验证组C | [510](../../output/experiments/v56_decoupled_20261120_r04/difference_views/frames/group_c/0510.jpg) | [2490.0551470588234, 2345.5698529411766] | 16.95 | 16.95 | — | — | — | None | 0.00 | 0.00 | — | NONE | OPEN_FORK |

| 组 | 帧 | 分支 | 实际根部 | 候选尖端 | 累计分 | 择优分 | 有效列 | 一致比例 | 条件 |
|---|---|---|---|---|---|---|---|---|---|
| 开发组A | 1 | 0 | [957, 1143] | [964, 1143] | 7.42 | 17.71 | 8 | 0.00 | LOW_SUPPORT |
| 开发组A | 1 | 1 | [957, 1144] | [965, 1144] | 7.90 | 18.67 | 9 | 0.00 | LOW_SUPPORT |
| 开发组A | 398 | 0 | [961, 1151] | [1337, 1164] | 331.39 | 735.88 | 325 | 0.84 | VALID |
