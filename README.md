# CodexCrack · 裂纹路径与尖端检测

当前研究版本为原图灰度 V3（s3t），生产验收未通过。下一位 agent 从 [V3 接手规范](docs/V3_AGENT_SPEC.md) 开始，随后查看[分阶段开发报告](evidence/v3/REPORT.md)、[最新指标](evidence/latest_metrics.json)和[逐帧预测](evidence/v3/predictions.jsonl.gz)。

1. 先读 [接手规则](AGENTS.md) 和 [阶段记录](docs/HISTORY.md)。
2. 用 Python 3.12 安装依赖并运行合成检查。首轮会编译 Numba 函数。
3. 对照 [方法和评价约定](docs/SPEC.md)、[未解决问题](docs/OPEN_PROBLEMS.md) 和[冻结指标](evidence/latest_metrics.json)设计新版本。

```bash
python -m pip install -r requirements.txt
python research/raw_notch_trace_v2b/check.py
python -m unittest research.unified_crack_tip_60q.tests
```

| 入口 | 用途 |
|---|---|
| research/notch_identity_v3 | 当前研究核心、终止门、结构负例和可复跑探针 |
| research/raw_notch_trace_v2b | 冻结双唇起点研究对照 r02 与合成样例 |
| research/raw_notch_trace_v2 | 单起点对照 r01 |
| research/unified_crack_tip_60q | 上一代多尺度灰度、双参考、图搜索、多轨迹与合成检查 |
| research/p1p2_grayref_v2/algorithm.py | 单帧参考差分与候选对照实现 |
| src/cpp/a | 历史 A 的 C++17 核心、头文件和示例。构建需要 Windows、MSVC 和外部 OpenCV 4.4.0 SDK，通过 OPENCV_ROOT 指定 |

公开快照通过合成图运行。实验原图、缓存、人工标注、视频和 DLL 保存在原工作区。完整序列复验需要获得该工作区的数据访问权限。版本与预测摘要哈希见 [provenance.json](evidence/provenance.json)。
