# 原图灰度裂纹追踪 V3

[开发报告](../../output/experiments/notch_identity_v3_20261118_r01/REPORT.md) · [最终版逐帧图册](../../output/experiments/notch_identity_v3_20261118_r01/s3t/index.html) · [可见标注复查](../../output/experiments/notch_identity_v3_20261118_r01/visible_review/index.html)

从项目根目录用配置指定的 Python 执行模块。原生输入为已核验的 60Q 原图 ROI 缓存、点位和两类参考通道；检测函数本身不接收样本名、帧号或标签。基线、计分和视频生成复用 research/raw_notch_trace_v2b 下的活动源码。只运行指定三组，排除组X完全排除。历史回归已曝光，本轮已封存。

| 阶段参数 | 实现 |
|---|---|
| s1 | detector.py 的多起点与汇合前身份比较，沿用 r02 灰度与终止 |
| s2 | terminal.py 的尺度化滚动追踪、主干和前方材料判据 |
| s3 | 叠加差分门控、近根附着和路径直线性 |
| s3t | 完整 S3，topology.py 增加闭环、开口轮廓检查 |

本轮顺序为开发 S1、比较 r02、开发 S2 与 S3、独立结构反例、完整 S3；之后运行 probes.py、verify_dev.py，冻结四个阶段，共用一次验证组C读取事务。预测输出用原图整数像素坐标。帧诊断中 pairs 的格式为两个候选的零起始编号和汇合位置 x；候选没有 near 表示未进入获选终点所在簇的近段竞争。保存的是实际观测点，相邻记录间可有间断。相同终点不保证相同路径。

以下模块提供实验入口。数据根、运行目录和分组定义在 run.py；已存在的预测文件禁止覆盖。复现实验应在新实验副本设置空输出目录，在停止条件与配置锁定后执行回归。

```text
python -m research.notch_identity_v3.run dev s1
python -m research.notch_identity_v3.run dev s2 s3
python -m research.notch_identity_v3.run dev s3t
python -m research.notch_identity_v3.probes s1 s2 s3 s3t
python -m research.notch_identity_v3.verify_dev
python -m research.notch_identity_v3.run freeze s1 s2 s3 s3t
python -m research.notch_identity_v3.run locked s1 s2 s3 s3t
python -m research.notch_identity_v3.run deliver s3t
python -m research.notch_identity_v3.report
python -m research.notch_identity_v3.review
python -m research.notch_identity_v3.lip_audit
```

全序列正式预测见 s3t/dev.jsonl、s3t/locked.jsonl。报告、标注复查图与补充审计可从已有预测离线生成。补充候选得分仅在三点弯 15 张可见帧上回放 S1；验证组C叠图仅读取封存预测与原图，不再运行检测器。

