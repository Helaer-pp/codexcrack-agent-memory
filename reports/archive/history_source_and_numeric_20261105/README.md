# 裂纹检测项目

<!-- C_ADAPTIVE_TIP_RESEARCH_20261104 -->
2026-11-04 最新 C 自适应尖端研究已完成，结果为 **KEEP_A / C_RESEARCH_ONLY**：新受控TEST未过效果门槛，未生成或替换C DLL，生产A不变。六组真实输入均为已曝光回归/诊断，未用于C调参；排除组X继续退役、三点弯不再称未见holdout。入口：[本轮交付](CrackV4_C_AdaptiveTip_Research_20261104/run01/index.html)、[开发报告](CrackV4_C_AdaptiveTip_Research_20261104/run01/08_reports/executive_summary.md)、[含原图的视频和逐帧图](CrackV4_C_AdaptiveTip_Research_20261104/run01/07_media/index.html)。以下原记录保留其历史时间含义。


<!-- CURRENT_VALIDATION_20261104 -->
2026-11-04 当前算法仍冻结为生产 A（DLL SHA-256 `c23498fcc660469927f63244b8e98e39b1eb86d542ec9a7b069d61fcf813654b`），研究 B 未通过替换发布；本轮未修改算法、参数或 DLL。当前验证名单以 [active_validation_registry.json](active_validation_registry.json) 为准：排除组X退出现行验证名单、保留历史；三点弯作为只验证不调参的新组。三点弯 520 张图片已计算，交付入口见 [视频与逐帧对比图](CrackV4_Validation_ThreePointBend_20261104/run01/index.html)、[验证报告](CrackV4_Validation_ThreePointBend_20261104/run01/05_reports/验证报告.md)。以下为历史维护记录，不作为当前验证名单。

2026-10-30 已清理历轮结果、旧版本工作目录、重复 SDK、无用脚本和构建缓存。原始图片、基准点文件和用户开发文档保留原路径；F:、D: 的试验数据和外部依赖未删除。

- 保留原有主线与回退目录：`crack_v4_cpp/local_tip_20261030/`。
- C++ 算法、接口及示例：该目录的 `src/`。
- 当前 DLL、LIB、测试程序：该目录的 `build/Release/`。
- 必要回退实现：该目录的 `baseline/stable/` 与 `baseline/recovery/`。
- 四组数据清单、第五组独立验证记录：该目录的 `config/`。
- 研究结论：该目录的 `docs/08_release_decision.md`。最新 Hessian/重定位实验仍未通过发布验证，默认行为未因清理改变。
- 清理清单、验证记录：`maintenance/`。
- 源码回溯包：`backups/pre_cleanup_20261030.zip`，已校验 CRC 和逐文件 SHA-256。含历版源码、可用 Git 历史及必要回退二进制，不含历史视频和逐帧结果。一个旧版仓库原有 Git 引用损坏，其原始 `.git` 与工作源码已单独保存在包内，详情见 `maintenance/git_backup_status.json`。

算法核心源码和现有 DLL 未修改。清理期间仅调整测试/导出工具的目录依赖及默认构建目录，使其不再依赖删除的旧工作目录。原冻结清单记录的是清理前版本，源码回溯包保留该版本；历史报告中的结果附件已按要求删除。

在项目根目录重新编译（OpenCV 固定使用 `D:/opencv-4.4.0`）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\crack_v4_cpp\local_tip_20261030\build.ps1
```

如需重新生成四组对照结果，运行以下工具（会重新读取外部试验数据并生成较多文件，本次清理没有重新跑全量数据）：

```powershell
python .\crack_v4_cpp\local_tip_20261030\tests\replay_dev4.py --modes BASE,FULL_LOCAL --run dev4
python .\crack_v4_cpp\local_tip_20261030\tests\local_media.py
```

新生成结果统一放在 `crack_v4_cpp/local_tip_20261030/output/`，包含视频、逐帧数据、原图/检测对比图。第五组不参与开发调参；本次没有读取第五组图像或重复进行独立验证。

2026-10-30 联合路径/端点可行性研究另存于 `crack_v4_cpp/joint_path_endpoint_20261030/`，交付索引见 [开发验证结果](deliverables/joint_path_endpoint_feasibility/README.md)。结论 **NO_GO**，未替换上述主线；四组完整回放、视频、逐帧原图对比、CSV/JSONL和raw-only待标注包均单独保存。H1–H3与DEV-4准入未通过，第五组本轮未读取/运行。

2026-10-30 后续无人工真值 Frangi/参考变化/STOP 研究独立保存于 `crack_v4_cpp/zero_gt_frangi_20261030/`，结果入口为 [本轮说明](CrackV4_V5_ZeroGT_Study/00_README.md) 与 [媒体索引](CrackV4_V5_ZeroGT_Study/index.html)。结论 **RESEARCH_ONLY / NO_IMPROVEMENT**，仍保留稳定 A，未替换主线或静默更改默认 ABI。原四组实际完整回放，DEV 与独立合成 TEST 分开；按本轮任务书允许，在冻结源码、参数和渲染规则后完成第五组一次研究性失败复核，不据第五组返调。本轮真实精度均为 N/A；不要求人工标注才能运行。

2026-10-30 冻结DP的M/T/E独立研究位于 `crack_v4_cpp/frozen_dp_tip_20261030/`，交付入口为[全部视频与逐帧图](output/frozen_dp_tip_measurement_study/index.html)、[十项结果与一页消融摘要](output/frozen_dp_tip_measurement_study/09_reports/ordered_results_report.md)。四组完整五配置回放，冻结后第五组一次检测；36个MP4完整解码检查，2510张当前帧对比PNG。结论 **RESEARCH_ONLY / NOT_PROVEN / NO_IMPROVEMENT**：M未发现数值软件错误，T跨组适用性不足，E/TE在合成渐浅裂纹上误截断，排除组X473长尾未修正。选定AE本次五组完整调用实测Max62.10ms，但不因时间过关而启用精度证据未过关的研究模块。原A及现有主线源码/DLL不变。

2026-11-02 已按要求重新渲染全部视频及逐帧图，最新展示入口为[包含完整原图的视频与对比图](output/frozen_dp_tip_media_with_original_20261102/index.html)。36个视频均加入同步当前完整原图；2510张PNG为“完整原图｜A稳定版局部｜AE研究版局部”的2880×1080三栏图。另有1920×1080原图/单算法双栏视频。本次仅重渲染已保存测量结果，没有更改算法、数值CSV或重新执行第五组检测；旧版输出保留。
