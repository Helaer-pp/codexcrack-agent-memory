# V3.2 原灰度裂纹路径与尖端追踪

从项目根目录导入 `research.notch_identity_v32.terminal`。输入为当前 8 位单通道 ROI、ROI 内的缺口提示坐标 (x, y)、以原图像素计的锚距。下面给出仅用原灰度的调用。

```python
from research.notch_identity_v32.terminal import prepare, predict

prepared = prepare(raw_roi, notch_hint_xy, anchor_distance_px)
result = predict(prepared, bonus=None)
tip_xy = result["tip"]
points = result["points"]
```

完整模式调用 `predict(prepared, bonus, fixed=aligned_fixed_roi)`。bonus 的形状与 `prepared[3]` 一致，由历史配准、有效掩膜与有界弱差分构造，见 batch.run_one。fixed 与当前输入 ROI 对应，提供局部复核所需的配准固定参考，缺测区域用 NaN 表示。尖端与路径输出坐标相对于输入 ROI。若无有效尖端，tip 为 None。批处理会加回 ROI 原点，逐帧表中的坐标均为原图坐标。

`prepare` 的 stage 可取 background、taper_only、paired、distal、reference、v3_2，默认 v3_2。两个单项对照各自只对 V3.1 改动一项；后续从 paired 开始逐步叠加。非默认阶段在六十张固定抽样帧上计算。full 与 raw_only 两种最终模式均覆盖 1,633 帧。

[开发与消融报告](../../evidence/v3_2/REPORT.md) · [逐帧图像与视频](../../output/experiments/v32_precision_20261119_r03/index.html) · [冻结指纹](../../output/experiments/v32_precision_20261119_r03/freeze.json)

已有预测、冻结输入和分组结果可直接用于复核。在项目根目录运行 `python -B -m research.notch_identity_v32.report` 将从已有封存结果重建报告，并同步当前指标与项目记录。推理流程依序为 probes、batch group_a、score group_a、batch freeze、batch three_point_bend、score three_point_bend、batch group_c、score group_c、deliver。启动新研究轮次需在独立输出目录封存；本轮验证组C回归已执行一次。

诊断中 events 保留弱带起列、重获窗口首末列、外推残差、谷宽比和同唇规则的通过标志。reconnections 为原始追踪器的临时重获次数；最终路径可能在后续复核时被裁剪。geometry_cut 为首次不再允许的列，公开尖端还需通过末端认证，可能早于该列。参考图诊断保留局部 NCC、平移、裁剪坐标与裁剪前尖端。全序列的两模式差异见 mode_disagreements.csv，三点弯 215 与验证组C 69、335 的分支诊断见 focus_candidates.csv。
