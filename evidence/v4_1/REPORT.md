# V4.1 裂纹尖端追踪提纯融合验证报告

**冻结版未通过验收。** 开发组A、三点弯、验证组C联合命中分别为 19/19、1/15、8/20，共 28/54。V3.6 为 42/54，V4.0 为 37/54。三点弯出现 11 帧尖端误差超过 100 px，继续使用原有基线。

以 V3.6 灰度主干、近缺口重连与参考复核为基座。将完整模式的种子限制到物理前缘起向右 0.10s 以内，再用 V4.0 窄带有符号增量及 ±0.025s 参考预抑制判别候选。纯灰度模式保留独立基线行为。

人工标注仅用于结果对比，排除组X已排除。先运行合成探针，然后运行开发组A。两验证组历史上均已暴露。P5/P6 保留旧版复合探针，同时增加等长、恒定深度、无末端散点的裂纹对照，分别单独施加宽域变暗和错位静态划痕。

## 实现和数据流

① 限制起点与补种范围。② 增量轨需同时有当前图凹陷，渐隐末端用局部衰减和实际观测列认证；检查参考图相容偏移的连续暗谷以制止划痕延伸。③ 强增量根可用直至嘴沿的单极连续暗化代替原图连通；闭环仅由增量掩膜中的封闭区域判定。弱证据保留原灰度主干。阶段表逐项累加。

渐隐拟合仅用于分辨率下的细暗线。有可分辨宽度的主干沿用 V3.6 的几何端点，只在局部增量衰减至侧方背景噪声时，回到最后连续观测窗的中心。颈部拒绝跨唇跳变。重复灰度候选和相同路径的参考回剪评审按帧缓存。

terminal.py 共 264 行非空、非纯注释代码。共用 V3.6 原语、评测与渲染未计入。

evidence.py 共 63 行非空、非纯注释代码。共用 V3.6 原语、评测与渲染未计入。

backbone.py 共 131 行非空、非纯注释代码。共用 V3.6 原语、评测与渲染未计入。

## 合成压力矩阵

各格为 V4.0 → V4.1 通过数/分母。顺序为三档缩放，每档内标准、暗、亮。独立扰动控制在 V4.0 没有同场记录。阳性按原始尺度尖端误差 ≤10 px，P1 还要求路径全覆盖，P6 还要求路径精度 ≥95%。

| 探针 | 0.5× 标准 | 0.5× 暗 | 0.5× 亮 | 1× 标准 | 1× 暗 | 1× 亮 | 2× 标准 | 2× 暗 | 2× 亮 |
|---|---|---|---|---|---|---|---|---|---|
| P1_upper | 3/4 → 4/4 | 3/4 → 4/4 | 3/4 → 4/4 | 4/4 → 3/4 | 4/4 → 4/4 | 4/4 → 2/4 | 4/4 → 4/4 | 3/4 → 4/4 | 4/4 → 4/4 |
| P1_lower | 3/4 → 4/4 | 3/4 → 4/4 | 3/4 → 4/4 | 3/4 → 3/4 | 3/4 → 4/4 | 3/4 → 2/4 | 4/4 → 4/4 | 4/4 → 3/4 | 4/4 → 4/4 |
| P2_fade | 0/4 → 3/4 | 0/4 → 3/4 | 0/4 → 3/4 | 2/4 → 4/4 | 2/4 → 4/4 | 2/4 → 4/4 | 1/4 → 4/4 | 2/4 → 4/4 | 0/4 → 4/4 |
| P3_parallel | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| P3_oblique | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| P4_ring | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| P4_open | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| P5_plastic_zone | 0/4 → 3/4 | 0/4 → 3/4 | 0/4 → 3/4 | 1/4 → 4/4 | 1/4 → 4/4 | 1/4 → 4/4 | 1/4 → 4/4 | 2/4 → 4/4 | 0/4 → 4/4 |
| P5_plastic_zone_negative | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| P6_deformed_scratch | 0/4 → 2/4 | 0/4 → 2/4 | 0/4 → 1/4 | 0/4 → 4/4 | 0/4 → 4/4 | 0/4 → 4/4 | 2/4 → 4/4 | 2/4 → 4/4 | 1/4 → 3/4 |
| P6_deformed_scratch_negative | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| P2_isolated | — → 4/4 | — → 4/4 | — → 4/4 | — → 4/4 | — → 4/4 | — → 4/4 | — → 3/4 | — → 3/4 | — → 3/4 |
| P5_isolated | — → 4/4 | — → 4/4 | — → 4/4 | — → 4/4 | — → 4/4 | — → 4/4 | — → 3/4 | — → 4/4 | — → 4/4 |
| P6_isolated | — → 4/4 | — → 4/4 | — → 4/4 | — → 4/4 | — → 4/4 | — → 4/4 | — → 4/4 | — → 4/4 | — → 4/4 |
| P1_weak_gap | 10/24 → 6/24 | 10/24 → 6/24 | 10/24 → 6/24 | 14/24 → 10/24 | 15/24 → 13/24 | 14/24 → 6/24 | 20/24 → 13/24 | 20/24 → 11/24 | 20/24 → 14/24 |

nominal 阴性误报 0/72；已发布弱带重连 39 次，错接 0 次。

dim 阴性误报 0/72；已发布弱带重连 38 次，错接 0 次。

bright 阴性误报 0/72；已发布弱带重连 37 次，错接 0 次。

P2_fade 按原始尺度统计水平偏差超过 10 px 的正例。V4.0 → V4.1 为 15 提前、10 过冲、0 无预测 → 3 提前、0 过冲、0 无预测。

P5_plastic_zone 按原始尺度统计水平偏差超过 10 px 的正例。V4.0 → V4.1 为 19 提前、9 过冲、0 无预测 → 3 提前、0 过冲、0 无预测。

P6_deformed_scratch 按原始尺度统计水平偏差超过 10 px 的正例。V4.0 → V4.1 为 19 提前、12 过冲、0 无预测 → 8 提前、0 过冲、0 无预测。

每档曝光的 72 个阴性样例含独立纹理、闭环、开口边缘及仅有塑性暗化或形变划痕的背景。事件统计审查发布路径中的实际缺列及获准重连，邻近重复事件合并；与 V4.0 的内部事件口径有所不同。低采样弱裂纹的局部原图暗谷可能只有单像素，因此半倍尺度的失败仍需单列。

[逐例合成结果](../../output/experiments/v41_fusion_20261119_r07/paired_probes.csv) · [弱带事件](../../output/experiments/v41_fusion_20261119_r07/weak_events.csv)

## 实测消融

Joint 要求尖端 ≤10 px 且 10 px 容差内的路径覆盖和精度均 ≥80%。Severe 为误差 >100 px。无预测计入命中分母，误差分布仅包含有效坐标。

### 开发组A

| 阶段 | 有效 / 可见 | Hit@5 | Hit@10 | Joint | Severe | 中位 px | 最大 px |
|---|---|---|---|---|---|---|---|
| r02 | 19/19 | 10 | 16 | 16 | 0 | 4.92 | 92.06 |
| V3 | 19/19 | 10 | 14 | 14 | 0 | 4.93 | 41.34 |
| V3.6 | 19/19 | 13 | 19 | 19 | 0 | 2.95 | 9.85 |
| V4.0 | 19/19 | 13 | 19 | 19 | 0 | 3.20 | 9.85 |
| ① 前缘 + 窄带 | 19/19 | 12 | 18 | 18 | 0 | 3.13 | 12.10 |
| ② 加原图底线 | 19/19 | 14 | 19 | 19 | 0 | 2.54 | 9.85 |
| ③ 加增量根与闭环判据 | 19/19 | 14 | 19 | 19 | 0 | 2.54 | 9.85 |

### 三点弯

| 阶段 | 有效 / 可见 | Hit@5 | Hit@10 | Joint | Severe | 中位 px | 最大 px |
|---|---|---|---|---|---|---|---|
| r02 | 15/15 | 4 | 10 | 1 | 0 | 8.63 | 65.91 |
| V3 | 15/15 | 5 | 10 | 1 | 0 | 8.18 | 65.91 |
| V3.6 | 15/15 | 5 | 10 | 10 | 0 | 8.18 | 65.91 |
| V4.0 | 15/15 | 4 | 9 | 9 | 0 | 8.63 | 65.91 |
| ① 前缘 + 窄带 | 15/15 | 5 | 10 | 10 | 0 | 8.18 | 65.91 |
| ② 加原图底线 | 15/15 | 0 | 1 | 1 | 11 | 181.84 | 285.10 |
| ③ 加增量根与闭环判据 | 15/15 | 0 | 1 | 1 | 11 | 181.84 | 285.10 |

### 验证组C

| 阶段 | 有效 / 可见 | Hit@5 | Hit@10 | Joint | Severe | 中位 px | 最大 px |
|---|---|---|---|---|---|---|---|
| r02 | 20/20 | 4 | 6 | 6 | 0 | 14.52 | 39.42 |
| V3 | 20/20 | 9 | 13 | 13 | 0 | 5.86 | 30.64 |
| V3.6 | 20/20 | 8 | 13 | 13 | 0 | 8.80 | 30.57 |
| V4.0 | 20/20 | 6 | 9 | 9 | 0 | 10.47 | 54.72 |
| ① 前缘 + 窄带 | 19/20 | 6 | 10 | 10 | 0 | 9.71 | 42.30 |
| ② 加原图底线 | 19/20 | 5 | 8 | 8 | 0 | 10.46 | 56.69 |
| ③ 加增量根与闭环判据 | 19/20 | 5 | 8 | 8 | 0 | 10.46 | 56.69 |

## 指定帧对照

三列坐标与误差均按 V3.6、V4.0、V4.1 排列。验证组C 347 无标注，仅供定性检查。

### 开发组A

| 帧 | V3.6 | V4.0 | V4.1 | 误差 px | 路径来源 | 末端判定 |
|---|---|---|---|---|---|---|
| 67 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_a/0067.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_a/0067.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_a/0067.jpg) | (1005.00, 1142.00) | (1005.00, 1142.00) | (1005.00, 1142.00) | 9.85 / 9.85 / 9.85 | ANCHORED_V36 | BASE_TERMINAL |
| 366 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_a/0366.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_a/0366.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_a/0366.jpg) | (1314.00, 1159.00) | (1313.00, 1160.00) | (1313.00, 1160.00) | 1.15 / 2.15 / 2.15 | ANCHORED_V36 | RESOLVED_INCREMENT_END |
| 398 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_a/0398.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_a/0398.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_a/0398.jpg) | (1327.00, 1162.00) | (1328.00, 1163.00) | (1334.00, 1164.00) | 1.90 / 3.20 / 9.18 | ANCHORED_V36 | RESOLVED_INCREMENT_END |
| 504 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_a/0504.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_a/0504.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_a/0504.jpg) | (1381.00, 1158.00) | (1374.00, 1160.00) | (1379.00, 1159.00) | 1.17 / 6.14 / 1.07 | ANCHORED_V36 | RESOLVED_INCREMENT_END |

### 三点弯

| 帧 | V3.6 | V4.0 | V4.1 | 误差 px | 路径来源 | 末端判定 |
|---|---|---|---|---|---|---|
| 1 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/three_point_bend/0001.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/three_point_bend/0001.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/three_point_bend/0001.jpg) | (1554.00, 2709.00) | (1554.00, 2709.00) | (1530.00, 2702.00) | 65.91 / 65.91 / 48.15 | ANCHORED_V36 | CROSS_LIP_BREAK |
| 144 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/three_point_bend/0144.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/three_point_bend/0144.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/three_point_bend/0144.jpg) | (1502.00, 2729.00) | (1591.00, 2716.00) | (1502.00, 2729.00) | 33.55 / 59.29 / 33.55 | ANCHORED_V36 | BASE_TERMINAL |
| 178 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/three_point_bend/0178.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/three_point_bend/0178.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/three_point_bend/0178.jpg) | (1562.00, 2710.00) | (1562.00, 2710.00) | (1503.00, 2729.00) | 23.85 / 23.85 / 38.14 | ANCHORED_V36 | RESOLVED_INCREMENT_END |
| 335 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/three_point_bend/0335.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/three_point_bend/0335.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/three_point_bend/0335.jpg) | (1711.00, 2719.00) | (1711.00, 2719.00) | (1504.00, 2728.00) | 10.55 / 10.55 / 197.04 | ANCHORED_V36 | CROSS_LIP_BREAK |
| 407 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/three_point_bend/0407.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/three_point_bend/0407.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/three_point_bend/0407.jpg) | (1746.00, 2722.00) | (1746.00, 2722.00) | (1503.00, 2729.00) | 19.10 / 19.10 / 262.11 | ANCHORED_V36 | RESOLVED_INCREMENT_END |

### 验证组C

| 帧 | V3.6 | V4.0 | V4.1 | 误差 px | 路径来源 | 末端判定 |
|---|---|---|---|---|---|---|
| 38 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_c/0038.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_c/0038.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_c/0038.jpg) | (2299.00, 2330.00) | (2271.00, 2295.00) | (2272.00, 2338.00) | 9.64 / 40.77 / 18.68 | ANCHORED_V36 | CROSS_LIP_BREAK |
| 54 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_c/0054.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_c/0054.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_c/0054.jpg) | (2272.00, 2339.00) | (2272.00, 2339.00) | (2272.00, 2339.00) | 30.57 / 30.57 / 30.57 | ANCHORED_V36 | BASE_TERMINAL |
| 69 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_c/0069.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_c/0069.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_c/0069.jpg) | (2274.00, 2338.00) | (2327.00, 2330.00) | (2343.00, 2316.00) | 30.34 / 23.43 / 42.30 | ANCHORED_V36 | BASE_TERMINAL |
| 195 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_c/0195.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_c/0195.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_c/0195.jpg) | (2400.00, 2345.00) | (2396.00, 2345.06) | (2398.00, 2345.00) | 15.87 / 11.93 / 13.89 | ANCHORED_V36 | RESOLVED_INCREMENT_END |
| 335 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_c/0335.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_c/0335.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_c/0335.jpg) | (2468.00, 2345.00) | (2478.00, 2345.00) | (2468.00, 2345.00) | 2.18 / 7.84 / 2.18 | ANCHORED_V36 | BASE_TERMINAL |
| 347 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_c/0347.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_c/0347.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_c/0347.jpg) | (2504.00, 2319.00) | (2479.00, 2345.00) | (2470.00, 2345.00) | — / — / — | ANCHORED_V36 | BASE_TERMINAL |
| 363 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_c/0363.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_c/0363.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_c/0363.jpg) | (2470.00, 2346.00) | (2483.00, 2345.01) | (2470.00, 2346.00) | 13.03 / 0.84 / 13.03 | ANCHORED_V36 | BASE_TERMINAL |
| 456 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_c/0456.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_c/0456.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_c/0456.jpg) | (2504.00, 2344.00) | (2505.02, 2344.98) | (2504.00, 2344.00) | 10.10 / 11.19 / 10.10 | ANCHORED_V36 | BASE_TERMINAL |
| 469 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_c/0469.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_c/0469.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_c/0469.jpg) | (2503.00, 2345.00) | (2548.00, 2347.00) | (2503.00, 2345.00) | 9.71 / 54.72 / 9.71 | ANCHORED_V36 | BASE_TERMINAL |
| 510 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_c/0510.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_c/0510.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_c/0510.jpg) | (2506.00, 2346.00) | (2507.00, 2346.02) | (2506.00, 2346.00) | 15.95 / 16.95 / 15.95 | ANCHORED_V36 | BASE_TERMINAL |
| 528 [3.6](../../output/experiments/v36_patch_20261119_r02/difference_views/frames/group_c/0528.jpg) [4.0](../../output/experiments/v40_decoupled_20261119_r06/difference_views/frames/group_c/0528.jpg) [4.1](../../output/experiments/v41_fusion_20261119_r07/difference_views/frames/group_c/0528.jpg) | (2524.00, 2346.00) | (2524.00, 2346.05) | (2524.00, 2346.00) | 10.46 / 10.47 / 10.46 | ANCHORED_V36 | BASE_TERMINAL |

## 冻结失效的定位

三点弯①阶段仍有 10/15 联合命中，②阶段降至 1/15，③没有恢复。13 张有可比封存基座路径的可见标注帧触发近口跨唇判据。第 503 帧基座走到 x=1795，跨唇检查在 x=1516 首次截断，后续末端认证留下 x=1502，最终误差 285.10 px。重复截在同一处，说明这段带缺列的弯曲路径被当成了跨唇重连。记录中的最后停止原因不足以解释首次损失。[近口截断逐帧数据](../../output/experiments/v41_fusion_20261119_r07/near_mouth_gaps.csv)

验证组C 469 恢复到 9.71 px，335 为 2.18 px；363 未保住 V4.0 的 0.84 px，最终为 13.03 px。54 和 69 均有 3 个候选未通过颈部连续性检查、1 个未形成足够长的增量，新的原图门豁免没有得到可发布候选。69 的基座结果在前缘阶段已偏至 42.29 px。

下一轮可在独立合成图中并列生成“弯曲但同唇、观测缺列”和“平行两唇之间的真实跳接”。记录断前、断后切向以及参考图对应纹理，先验证能否区分这两个情形，再决定是否对已由灰度主干验证的路径执行截断。

## 效率与验收

各版本冻结全序列单帧推理算术均值，排除读图、标注评分和渲染；不同运行时 CPU 并发与系统负载会影响对比。视频播放帧率与推理速度独立。

| 组 | 版本 | 帧 | 毫秒/帧 | FPS |
|---|---|---|---|---|
| 开发组A | v3_6 | 551 | 219.82 | 4.55 |
| 开发组A | v4_0 | 551 | 171.58 | 5.83 |
| 开发组A | v4_1 | 551 | 278.82 | 3.59 |
| 三点弯 | v3_6 | 520 | 307.92 | 3.25 |
| 三点弯 | v4_0 | 520 | 593.20 | 1.69 |
| 三点弯 | v4_1 | 520 | 798.75 | 1.25 |
| 验证组C | v3_6 | 562 | 144.89 | 6.90 |
| 验证组C | v4_0 | 562 | 281.69 | 3.55 |
| 验证组C | v4_1 | 562 | 393.67 | 2.54 |

开发组A的尖端与路径验收通过。

三点弯的尖端与路径验收未通过。

验证组C的尖端与路径验收未通过。

开发组A 联合命中 V3.6、V4.0、V4.1 依次为 19、19、19。

三点弯 联合命中 V3.6、V4.0、V4.1 依次为 10、9、1。

验证组C 联合命中 V3.6、V4.0、V4.1 依次为 13、9、8。

复核全部已保存的主选根、候选起点和增量种子，共 20125 个坐标记录，越出前缘带 0 个。相同坐标在不同记录中可能重复。

同源核验逐帧检查了纯灰度状态、根点、尖端和路径；标注帧的两个冻结版本均与历史推理结果一致。真实序列只有人工可见标注帧可计算尖端误差。

[逐帧图册与视频](../../output/experiments/v41_fusion_20261119_r07/difference_views/index.html) · [失败与退化帧](../../output/experiments/v41_fusion_20261119_r07/FAILURES_AUDIT.md) · [逐帧裁决](../../output/experiments/v41_fusion_20261119_r07/tracks.csv)

本轮未在全部三个组取得达到 V3.6 的全序列速度。

P1 弱带的错接和覆盖是两项独立指标；回退或截断也会使错接数下降。应同时检查矩阵中的覆盖验收通过率。
