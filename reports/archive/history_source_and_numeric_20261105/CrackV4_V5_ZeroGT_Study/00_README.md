# CrackV4 无人工真值研究：RESEARCH_ONLY

本轮按照 `CrackV4_ZeroGT_Frangi_StopAware_Optimization_Agent_Prompt.md` 实际修改 C++、编译并运行。结论为 **NO_IMPROVEMENT / NOT_RELEASE_READY**：正式选择保留稳定 A 行为，新 DLL 的 COMPAT 模式与 A 在完整四组数值兼容。B/C/D 仅供研究，不建议替换产品算法。

入口：本目录 `index.html`。视频是真实 MP4，逐组有 baseline、optimized、side_by_side、A_vs_D_research 和 notable_cases；**optimized 是保留 A 的兼容模式，不是声称优化成功**。四组参考帧和当前帧共 1991 张，第五组共 524 张；每张原图与正式结果对比 PNG 放在 `frames/final`，CSV 按 frame_id 与源文件名回溯。

正式图像与视频只画本帧确认且完整有效的中心线和一个末端点；无效帧只显示原图。没有 P1/P2、绿色线、虚线、候选线或历史填充。无损 PNG 的局部显示裁剪仅用于观看，与检测 ROI 不同；完整原图路径仍在数据清单和 CSV 中。第五组 51/473 另存全分辨率无损原图。

## 数值与限制

- `03_experiments/final_selected_per_frame.csv`：保留版五组每帧结果，含组名、frame_id、图片名、尖端原图 x/y、完整弧长 px 和有效标志；无效值写 0，标志可区分无效与真实零值。各组没有新提供独立标定比例，本轮统一像素长度，不把旧组比例推广到所有材料。
- `per_frame_results.csv`：四组 × 六种实际模式；`04_fifth_frozen_validation/per_frame.csv`：第五组 × 四种预先冻结模式。完整中心线为实际 CopyPath 输出，不通过离线移动尖端或平滑修改。
- 旧 V2 坐标/长度保留 0.01 px 数值取整，CopyPath 保留双精度。因此可视尖端取实际路径末点，允许 API 坐标量化差 ≤0.0072 px、弧长差 ≤0.0051 px；不等于真实亚像素精度。
- **所有真实图像尖端/长度准确度 N/A**。合成 DEV 和独立 TEST 有程序 GT，单独统计；确认数量和版本一致性不当成真实精度。第五组已知 51/473 不是严格盲测。
- 正式有效性读取 GetResultV2 的 tip/full 标志，并核对 CopyPath；不要按 `status` 描述词判断。旧 `weak_candidate` 描述也可对应时序已接受的完整有效输出，第五组473即如此；本轮没有按这个词隐藏错误长尾。
- B 在开发组H 409 当前帧全部超过 66.67 ms。D 当前 DEV 有超时且确认数下降；独立合成 TEST 有严重错误确认。本轮不把拒绝更多帧当定位改善。
- E0/E1 未运行：D 依赖层已明显失败，不继续叠加复杂度。没有虚构 E0/E1 数据。

## 工程与运行

源码工作目录：`D:/workspace\crack_v4_cpp\zero_gt_frangi_20261030`。
本交付 `01_source_and_build/source` 包含同一份源码、工具和构建脚本；`source.bundle` 保存冻结 Git 提交。
Windows x64 / C++17 / v142 / `/O2 /fp:precise /MD`，OpenCV SDK 固定 `D:\opencv-4.4.0`，运行需对应 OpenCV 4.4.0 DLL。Python 回放工具需 numpy、opencv-python、Pillow、psutil；Python OpenCV 仅负责输入与展示，实际检测在原生 OpenCV 4.4.0 DLL。

```powershell
cd D:/workspace\crack_v4_cpp\zero_gt_frangi_20261030
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
python .\tests\study_replay.py
python .\tests\study_synthetic.py --split dev
python .\tests\study_synthetic.py --split test
python .\tests\study_checks.py
```

A：冻结稳定 DLL / flags=3572。A2：上轮失败联合路径研究 DLL。COMPAT：新 DLL / flags=3572。B：增加 bit29 Frangi；C：增加 bit30 参考变化、背景与可信历史启动；D：C 再增加 bit31 STOP。接口布局和默认行为保留；新只读诊断接口不影响正式状态。具体 flags、公式、边界、采样种子在 `02_configs`。

第五组已按 `freeze_manifest.json` 冻结后执行一次；**不要在此交付目录重跑 `study_freeze_and_fifth.py`**，脚本会拒绝已有冻结文件。未来新研究必须另建目录与版本，不能覆盖本次结果。渲染脚本只读已保存正式结果，不重跑算法；重放完整第五组时序只发生一次。

## 验收与证据

`06_reports/release_decision.md` 给出结论；root_cause、frangi_utility、stop_aware_dp、no_gt_validation、generalization、regression 分别说明机制与边界。
`05_performance` 保存每帧 Process 耗时、阶段嵌套计时、最坏帧、600 帧内存观察、MP4 全量解码及渲染合同检查。初次失败回放的 DLL 与全帧输出保留在 `diagnostics/initial_failure_pass`；不删除首轮超时以美化结论。四组第二次完整计时没有并行合成或编码，预解码、每模式预热 5 帧、OpenCV 4 线程；第五组无额外输入预热。

`SHA256SUMS.txt` 覆盖实际交付文件；HTML 所有媒体链接需检查存在，MP4 需全量解码确认帧数/尺寸/15 FPS，抽查内容与输入画面一致。阶段计时仍有未独立打点的 DP/根部细分，不把残差冒充已测热点。合成样本不涵盖真实断裂全部成像机制，不保证普适准确度。

冻结后另有只读结果汇总脚本 `diagnostics/postprocess_saved_results.py`，只读取既有数值，不调用DLL或源图；补充中心线距离、MAE、路径分歧代理。`frozen_generated_challenges.py` 在冻结后补充了生成的分叉、遮挡、饱和、旋转挑战，仅评价已冻结DLL，不使用第五组像素或调参，且不混入原独立TEST指标与专用性能回放；详见 `06_reports/additional_frozen_challenges.md`。数据分析/报告文件可以在冻结后补全，冻结的算法、参数、DLL与正式渲染规则没有变化。

原冻结渲染脚本在完成25段视频及解码检查后，最后写JSON验收记录时遇到 NumPy int32 裁剪坐标序列化问题。`diagnostics/recover_render_acceptance.py` 调用完全相同的冻结渲染函数，逐张核对最终PNG像素，补写普通整数验收记录；不调用DLL、不重编码、不移动任何路径。原始失败日志保留在 `media.log`，恢复日志另存。`01_source_and_build/renderer_metadata_serialization.patch` 仅修正元数据序列化，供后续版本使用，未改写本轮冻结源代码/画图规则。
