# V3.3 裂纹尖端验证

[开发与消融报告](../../evidence/v3_3/REPORT.md) · [失败专项](../../evidence/v3_3/FAILURES_AUDIT.md)

从项目根目录导入 `research.notch_identity_v33.terminal.prepare` 与 `predict`。调用 `prep = prepare(raw_roi, hint_xy, scale, stage='v3_3')`，`predict(prep, None)` 评测当前灰度；完整模式传入与候选带同形的弱参考辅助矩阵，以及与原 ROI 同形的 fixed 对齐灰度图。未覆盖的固定参考像素用 NaN 标记。输出 root、points、tip 均为 ROI 坐标。批处理加回原图偏移后保存。

curve、tail、bidir、v3_3 四个阶段依次评估重连、全尾复核、豁免和增量排序。批量历史对照与之前封存的 V3.2 使用相同输入。用项目 Python 运行 `python -B -m research.notch_identity_v33.reports` 可从现有已封存三组预测重建两份报告和失败图册。每个失败叠图与其真实标注在输出时再次按原图摘要和评价指标校验。

冻结实验位于 `output/experiments/v33_tip_20261119_r03`，开发试验 r01/r02 位于同级目录。顺序为 probes、paired_probes、batch group_a、score group_a、batch freeze、batch three_point_bend、score three_point_bend、batch group_c、score group_c、deliver、reports。新实验须另设独立输出位置。三点弯仅作阶段对照，验证组C本轮冻结回归已执行一次。
