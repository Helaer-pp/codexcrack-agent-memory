# V3.1 原灰度弱裂纹追踪

[研发报告](../../evidence/v3_1/REPORT.md) · [逐帧结果和视频](../../output/experiments/v31_weak_crack_20261119_r04/index.html)

从项目根目录使用 research.notch_identity_v31.terminal 导入 prepare(raw, hint, scale, stage) 与 predict(prepared, bonus)。stage 取 gap、taper、weak_ref 或 v3_1；v3_1 是本轮完整版。输入为 uint8 灰度 ROI、ROI 内缺口提示坐标、原图锚距。原灰度对照使用与 prepared[3] 同形的零矩阵，或传 None。完整模式传入已有配准置信掩膜约束、固定参考与实际前一帧构造的辅助差分矩阵，见 batch.run_one。prepared 为 None 时 predict 返回空尖端。输出的 root、points、tip 和诊断坐标相对于输入 ROI；批处理加回 ROI 原点后交付原图像素坐标。原 V3 接口仍用于冻结对照，新预设从本版本的模块导入。

公共回归自检：`python -m research.notch_identity_v3.check_public`。本轮复现顺序为 probes、batch group_a、score group_a、batch freeze、batch three_point_bend、score three_point_bend、batch group_c、score group_c、deliver、gap_audit、report、verify。除公共自检外，模块均以 python -m research.notch_identity_v31.<模块> 调用。新实验应在独立项目副本配置新输出目录；本轮的冻结回归已经执行。score 只读取相应组的封存预测和标注文件。

开发组A为唯一真实开发组，三点弯为阶段对照，验证组C在冻结后统一回归一次。仅在选定 60 帧运行所有消融；最终版在三组 1,633 帧均保留 full/raw_only 和正式路径。各组 JSONL 的 models.v3_1 保存完整候选、终止门、首个失去支持的位置及重连次数。每帧没有人工标注时，准确性字段留空。
