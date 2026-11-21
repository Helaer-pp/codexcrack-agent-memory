# CrackV4 FourGroups PerFrameAnchors OpenCV440

本轮为独立开发版本，保留NextRound r1冻结DLL/源码及历史结果身份。用户提供的四组1991条逐帧双点已按确认的num0参考帧映射，未裁剪、未缩放；4张参考帧+1987张当前帧。

推荐实测点候选：flags3572、Shadow1、terminal_validation1、refine1、像素接口V2。所有新行为显式选择；原Create/默认包装器仍保持flags0。尖端、根部、路径、完整长度有效性必须分别判断，禁止从(0,0)推测有效性，禁止未确认时用上一帧冒充本帧。

## 查看结果

videos内4个完整优化H264视频、4个同源帧并排对照、4个早中晚预览。15FPS为演示速度，实际源帧ID与原图分辨率逐帧显示；视频全部重新全帧解码验证。keyframes含每组至少6张关键帧及完整差异审计包。results/framewise含所有配置原始native JSONL与结构化records JSONL，CSV合并以dataset/mode/frame_id区分；参考帧is_reference=true。真实tip/length精度N/A，annotations模板待人工填写。

## 构建与复现

完整工程原件位于本文件上两级工程根目录；本目录release包含可编译src、include、build.ps1、bin、lib、tests与Python测试依赖说明。默认构建使用D:/opencv-4.4.0，VS2022 v142、x64 Release；具体工具路径见build.ps1。

在工程根目录依次运行：

```powershell
./build.ps1
python tests/anchor_inputs.py
python tests/anchor_replay.py
python tests/anchor_guard_truth.py
python tests/engineering.py --dll build_final/Release --output deliverables/results/comparisons/engineering.json
python tests/extended_engineering.py --dll build_final/Release
python tests/next_synthetic.py --dll build_final/Release
python tests/abi_smoke.py
python tests/anchor_perturbations.py --dll build_final/Release --flags 244 --output deliverables/results/comparisons/perturb_244_measured.json
python tests/anchor_perturbations.py --dll build_final/Release --flags 3572 --output deliverables/results/comparisons/perturb_3572_measured.json
python tests/anchor_photo_causality.py
python tests/anchor_analysis.py
# export_anchor_csv.mjs uses the documented bundled artifact-tool runtime.
python tests/anchor_video.py
python tests/anchor_reports.py
```

一次性freeze_*脚本只用于本轮迁移已完成消融，不要在重跑时再次执行。tests/datasets.json保留实际源图时间顺序与原路径；并非按字典序推断。迁移机器需修改数据目录与OpenCV/FFmpeg工具位置，并保留文件顺序与坐标对应关系。源图体积较大，不重复打包；单次只驻留一组，峰值内存见性能报告。

四个固定二进制源为old、latest、geometry_candidate、candidate；配置/哈希均在config/modes.json。所有数据/视频/表格指标解释在reports的五份报告中。manifest.sha256用于完整性校验。
