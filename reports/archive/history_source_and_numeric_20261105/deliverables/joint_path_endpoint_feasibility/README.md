# 裂纹路径与停止点联合推断：可行性验证

**结论：NO_GO。稳定工程未替换。第五组未触达。** 无人工尖端/中心线GT，真实精度全部N/A。本次失败结论针对当前有界原型及统一参数，不表示理论路线已经被普遍否定。

- [视频与全部逐帧对比图](visuals/index.html)：四组各baseline/candidate/before_after三条完整MP4，逐帧原图/描线PNG。candidate固定M5_JOINT_K2研究版本，橙线只是候选，黄色点才为已确认尖端；GT不存在。
- [开发结论及完整表](reports/09_release_decision.md)、[代码根因](reports/01_code_level_root_cause.md)、[历史问题](reports/06_historical_failure_cases.md)、[速度与资源](reports/07_performance_and_resources.md)。
- [逐帧CSV](data/dev4_frame_results.csv)、[全部阶段JSONL](data/dev4_stage_scores.jsonl)、[超时帧](data/over_budget_frames.csv)、[原336帧清单](data/v3_lost336.csv)。CSV含10种独立闭环模式，保留参考/未确认/异常帧，不是人工修正结果。
- [raw-only标注工具](annotation/index.html)：选择同目录annotation_tasks.json加载，先看原图独立标尖端/根部/中心线/背景段，再导出human_gt.json并运行校验器；不要把算法旧路径作为GT。
- source为可编译C++17/OpenCV4.4.0与复现脚本；bin内稳定版、失败研究版、旧v3与本轮研究DLL分开保存。运行依赖D:/opencv-4.4.0/build/x64/vc15/bin的OpenCV runtime。脚本实际运行位置保留在crack_v4_cpp/joint_path_endpoint_20261030，不建议从复制目录直接改路径猜测数据。
- [版本/flags](config/baseline_identity.json)、[参数](config/flags_and_parameters.json)、[冻结身份](config/freeze_manifest.json)、[验收口径](config/acceptance_manifest.json)。冻结不代表准入通过。
- 第五组[NOT_RUN_GATED说明](reports/08_final5_frozen_validation.md)：H1–H3未通过且速度超时，遵守文档DEV-4准入门槛，没有生成假的第五结果；已曝光51/473不构成独立盲测，未来需全新第六组。

报告时间字段为实际采样，不承诺任意机器实时性。图像放大仅用于显示，不改变DLL输入与检测坐标；所有坐标和长度为原图像素，未做mm换算。

冻结源码提交：`7ac41c3ca13301ea3fea05894db4dfead972385c`；研究DLL SHA256：`a576a4f77bbac6b9364745edf972f1e3064186af82e9c1743d44e08c9c628a5f`。全部文件哈希见config/SHA256SUMS.txt。视频已解码帧数总计5973（三种视图×1991帧）。
