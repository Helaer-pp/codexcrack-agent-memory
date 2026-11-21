# CrackV4 下一轮诊断与实验修正（2026-10-29）

基于上一轮已优化的 OpenCV 4.4.0 版本继续排查。旧版本完整保留在 `baseline/`，不覆盖上一轮项目。当前 `src/`、`build_final/Release/CrackV4.dll` 为新版本，交付SDK中DLL位于 `bin/CrackV4.dll`。

## 先看这些文件

- [决策与交付结论](reports/optimization_decision.md)
- [开发组H/CT2 失败根因](reports/diagnostics_root_causes.md)
- [完整时序回归](reports/regression_comparison.md)
- [驻留内存算法计时](reports/algorithm_benchmark.md)
- [32 个错误帧审计](registration_error_audit.csv)
- [437 个 Shadow 分歧](shadow_disagreements.csv)
- [474 例人工标注入口](review/index.html)，或 [空白人工标注表](review/annotation_template.csv)
- [实验接口、方向约定及回退](EXPERIMENTS.md)
- [构建、复现与目录说明](REPRODUCE.md)

所有人工真值为空。恢复配准/提高输出覆盖率、相对旧算法更稳定，均不能替代人工尖端和路径精度验证。默认不启用 Verified，也不采用长度单调先验。

## 使用

保留原有 `CrackV4.h/.hpp` 调用，默认结果保持兼容。要试验本轮修正，使用 `CrackV4_experiments.h` 的 `CrackV4CreateExtended`，显式 flags=244，后续仍调用原 Process / GetResultV2。`src/example_experiments.cpp` 给出完整示例；旧调用不需要重编译结构定义。

同组只初始化一次，图像为原始 `CV_8UC1`，基准点为原图坐标。按用户确认的约定，p1 在上、p2 在下时预期向右扩展。每帧有实测点就传每帧点，没有才传 nullptr 使用自动配准及有界恢复。

运行 `./build.ps1`：C++17 / x64 Release / v142，严格使用 `D:/opencv-4.4.0/build`。运行环境需要 `opencv_world440.dll` 和相应 VC++ 运行库。最终 SDK 附带 OpenCV DLL 及原许可。

计时只涵盖内存图像进入 C API 后的计算。读图、解码、绘图、保存和 JSON/CopyPath 单独处理。完整复现脚本在 `tests/`，数据目录及精确文件顺序在 `tests/datasets.json`。

## 标注包

本地双击 `review/index.html`。每例包含原分辨率局部、旧/实验/Verified 路径、尾部放大、前后 2 帧、完整原图链接和原图坐标。原始 BMP 保留在用户原 F 盘目录，包内不复制整套试验原始数据。绘制手工尖端/根部/中心线后保存并导出 JSON；JSON 与 CSV 字段都明确区分算法结果和人工真值。浏览器本地存储只作便利，请导出 JSON 留存。
