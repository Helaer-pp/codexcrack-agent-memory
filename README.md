# CodexCrack · 裂纹路径与尖端检测

这是交给下一位研究 agent 的源码与实验记录。当前研究入口是 `research/raw_notch_trace_v2b/detector.py`。它在原图灰度上寻找与缺口相连的暗线，返回原 ROI 坐标系中的观测点和尖端。最新版本在开发组 A 有 16/19 张完整路径与尖端同时达标，开发组 B 为 1/15，曝光回归组 C 为 6/20。当前决定为 **PRODUCTION_NO_GO**。

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
| research/raw_notch_trace_v2b | 当前双唇起点研究实现 r02 与合成样例 |
| research/raw_notch_trace_v2 | 单起点对照 r01 |
| research/unified_crack_tip_60q | 上一代多尺度灰度、双参考、图搜索、多轨迹与合成检查 |
| research/p1p2_grayref_v2/algorithm.py | 单帧参考差分与候选对照实现 |
| src/cpp/a | 历史 A 的 C++17 核心、头文件和示例。构建需要 Windows、MSVC 和外部 OpenCV 4.4.0 SDK，通过 OPENCV_ROOT 指定 |

公开快照通过合成图运行。实验原图、缓存、人工标注、视频和 DLL 保存在原工作区。完整序列复验需要获得该工作区的数据访问权限。版本与预测摘要哈希见 [provenance.json](evidence/provenance.json)。
