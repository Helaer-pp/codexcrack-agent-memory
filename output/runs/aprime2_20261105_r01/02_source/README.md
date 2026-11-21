# CodexCrack

Codex 裂纹算法独立开发项目，唯一开发目录为本文件所在目录。源码、研究、配置和后续输出均集中于此，旧项目不再作为运行依赖。

当前生产算法为 **冻结 A**；最新 A′2 为 **RESEARCH_ONLY / KEEP_A**，未发布替换生产的 DLL。最新交付入口：[A′2报告、视频和逐帧图](output/runs/aprime2_20261105_r01/index.html)。旧A′封存结果仍保留。

| 目录 | 用途 |
|---|---|
| `baseline/frozen_a/` | 原生产 DLL、精确源码/头文件及 SHA256 身份 |
| `src/python/crackv4/` | 独立 Python/C ABI 调用模块 |
| `src/cpp/` | 原生只读回放工具源码 |
| `research/aprime/` | 当前 A′ 参考/变形联合证据研究代码与合同测试 |
| `research/aprime2/` | 多停止候选、参考区间审查、研究决策和独立原生旁路；生产A不变 |
| `config/` | 项目和试验组配置 |
| `data/anchors/` | 用户提供的逐帧基准点原文件 |
| `data/inputs/` | 3035 帧输入清单，F盘原图只读 |
| `data/frozen_a_replay/` | 六组冻结状态、坐标、完整 float64 路径，供回归比较 |
| `data/smoke/` | 独立冒烟验证图：六组各3帧，灰度像素与原输入一致 |
| `third_party/` | 项目内 OpenCV4.4 SDK、FFmpeg 及许可证 |
| `output/` | 全部生成数据、构建产物、日志、视频和对比图 |
| `docs/` | 当前状态、规范、历史任务书和整理记录 |
| `archive/` | 旧源码/数值证据压缩归档、过去要求保留的交付包；不参与运行 |

在本目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1 check
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
```

`check` 使用项目内18张真实灰度图和原生产DLL，比较旧状态、尖端及完整double路径，并运行参考模块合同测试；无需读取F盘。Python和CMake路径可在 `config/project.json` 中修改，编译需要已安装的Visual Studio C++工具链。

完整真实序列仍按配置只读使用F盘原始图片，未复制、删除或修改原始试验数据。项目独立指代码、原生运行库、配置、基准和冒烟数据不再依赖旧工作区；不包含整套Python/编译器或全部外部原始图。新试验输入通过配置指定，所有输出限制在 `output/`。

当前完整报告/7个视频/3251张逐帧对照：[最新交付](output/aprime_20261105/run01/index.html)。历史文件中的旧绝对路径保留其出处，迁移对照见 `docs/maintenance/legacy_path_map.json`；通过本入口访问媒体不依赖旧路径。

继续开发前阅读 [当前状态](docs/CURRENT_STATE.md)、[Codex开发约定](AGENTS.md)。最新批量研究入口示例：

```powershell
.\run.ps1 research setup_round -RunId new_round_001
.\run.ps1 research replay_ap -RunId new_round_001
.\run.ps1 research real_reference_audit -RunId new_round_001
```

研究模块没有升级为生产算法。新实验必须使用新RunId，不能覆盖封存结果；旧TEST/真实数据都已曝光。

构建输出的 `CrackV4Candidate.dll` 仅为冻结 A 源码的独立重编译产物，用于确认工程可构建，不包含 A′ 研究模块，也不替换正式 DLL。生产入口始终为 `baseline/frozen_a/bin/CrackV4.dll`。
