# V3 裂纹路径与尖端交接

当前研究实现为 S3 完整版（代码参数 s3t）。生产验收未通过。先读[开发与消融报告](../evidence/v3/REPORT.md)和[未解决问题](OPEN_PROBLEMS.md)。

## 接口与复现

从仓库根目录运行。解释器依赖见 requirements.txt。以下命令用确定性的合成图比较 r02 与四种预设模式，输出 420 行，并逐字段核验发布时保存的结果。

```bash
python -m pip install -r requirements.txt
python -m research.notch_identity_v3.check_public
```

单帧入口为 research.notch_identity_v3.terminal.prepare(raw, hint, scale, 's3t') 和 predict(prepared, bonus)。raw 是 uint8 二维原始灰度 ROI，hint 是当前 ROI 坐标中的缺口提示 [x,y]，scale 是原图中两锚点的距离。未找到缺口时传入 predict(None, None)。成功准备时 raw_only 传入与 prepared[3] 同形的 float32 零矩阵。full 将固定参考与上一参考的可信正差分按各自 0.04 × clip(signed/20,0,1) 相加，在 prepared[0] 所指裁剪内构建，灰度信号 <1 的位置置零。算法随后抑制近缺口的辅助证据。

正式输出含 status、root、points、tip 和候选诊断；检测器坐标相对传入的 ROI。批处理将 ROI 左上角平移加回，公开逐帧文件的坐标均为原图像素。路径列间可有缺测，空 tip 保持 null。阶段 s1 用 detector.prepare/predict，s2、s3、s3t 用 terminal.prepare/predict。topology.py 对闭环及开口外缘作结构检查。

## 证据与边界

[1,633 行结果摘要](../evidence/v3/frames.csv)与[完整路径和候选诊断](../evidence/v3/predictions.jsonl.gz)同时保留 full 和 raw_only。解压后按 group、frame 读取 JSONL。54 张可见人工标注用于离线比较。Hit@10 取原图尖端欧氏误差 ≤10 px，Joint 再要求 10 px 内路径覆盖率与精度均 ≥80%。真实数据的 FPR 未知。

| 组 | 可见 / 全序列 | Hit@10，r02 → V3 | Joint，r02 → V3 |
|---|---:|---:|---:|
| DEV-A | 19 / 551 | 16 → 14 | 16 → 14 |
| DEV-B | 15 / 520 | 10 → 10 | 1 → 1 |
| REG-C | 20 / 562 | 6 → 13 | 6 → 13 |

下一轮优先检验 DEV-B 第 215 帧代表的下唇中断问题。该帧下唇候选只到 x=1505，上唇候选走到 x=1603，端点误差 2.08 px，路径覆盖 57.4%。先在合成双唇上引入可控弱对比断带，固定终止门与评分器，记录首次失去支持的位置和错误重接率。DEV-A 的 366、451、504、542 是提前终止的回归反例。保留每一项改动的原灰度对照及受损帧。

## 后续数据规则

长期策略要求排除指定禁用试验组，人工标签只作比较。DEV-B 与 REG-C 均属长期验证保留组。此次任务书将 DEV-B 列作阶段对照，REG-C 为历史已曝光的冻结后回归。后续默认只在获准开发组和独立合成探针上设计规则，冻结后在保留组评分。复核已知反例时标明历史曝光；需要新的独立测试来检验泛化。
