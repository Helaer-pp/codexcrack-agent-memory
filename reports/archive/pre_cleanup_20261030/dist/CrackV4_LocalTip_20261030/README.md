# CrackV4 LocalTip 研究验证交付

结论：未通过不可发布。新模块保留显式实验开关，默认稳定逻辑未替换。

源码提交：05b07da711712aa3b301ad0785eb40c92b9940c8
候选DLL SHA256：d63f4bdacf7f4b9646b16eba0de74fef068e34cf9cd3c46d47227e49197a776b

先看 reports/08_release_decision.md、04_ablation_and_dev4_precision.md、05_latency_and_compatibility.md。交互浏览全部视频、逐帧原图与结果：review/index.html。视频都是完整序列，15FPS为演示播放帧率，坐标/弧长单位px。真实精度N/A。

编译：Windows x64 VS2022安装v142工具链，D:/CMake/bin/cmake.exe，D:/opencv-4.4.0。执行 powershell -File build.ps1 -BuildDir build。bin含OpenCV4.4运行库。旧C ABI与V2不扩字段。公共新只读接口为CrackV4LastLocalTipJson，声明在CrackV4_experiments.h。

集成方式仍为：Detector为成员对象，参考帧初始化一次，参考/每帧当前两个点使用未裁剪原图像素坐标，按时间顺序调用Process。旧C++CrackV4Detector包装器默认不启用本轮研究模块。显式实验调用参照src/example_experiments.cpp：CrackV4CreateExtended的flags设888308诊断版或364020生产诊断关闭版；V2 Options设ShadowPolicy=1、terminal_validation=1。参数的完整固定定义见config/freeze_manifest.json。所有参数全局统一。

flags：BASE3572；RIDGE_SHADOW560628；RIDGE_CP_SHADOW626164；RIDGE_CP_GATED757236；FULL_LOCAL888308；FULL_NO_REFINE888308但refine=0；FULL_PRODUCTION364020。旧v3/4096硬拒绝不与新Hessian组合。默认不开新位。

仅tip_valid有效时读取物理尖端；complete_length_valid还要求根部与路径可靠。tracking_endpoint、visible_supported_path与change_point不是已确认物理尖端。CP变化点不能直接当真实尖端。未确认完整长度为N/A，软件如显示0必须同时保存valid标志，禁止用无效(0,0)重新计算非零长度。

可见长度下降允许，不使用单调先验。根部连接上限12px不变，24px只用于局部重定位回看。参考帧允许无裂纹/已有裂纹；图像去噪/细化、两点配准与原DP主路径保留。

回退：恢复baseline/stable/CrackV4.dll及原头文件，或在新DLL关闭32768及其依赖位即可保持原稳定输出；切换算法/样本需重新初始化。保留baseline/v3仅用于对照，不建议回退到v3。

复现开发：tests/replay_dev4.py --run dev4；完整参数、图像顺序与逐帧基准点见config/data_manifest_dev4.json。合成GT、局部测试与失败断言在tests中。原四组仅为开发集合，真实精度/误报/召回N/A。原图独立标注工具review/annotation/annotate.html，选择tasks.json开始。

第五组历史有预暴露，本轮代码和脚本锁定后仅一次检测回放，见freeze_manifest.json与holdout_access_log.json。不要重跑final5_once.py；脚本有独占日志保护。渲染读取已保存结果，不重跑检测。

数据：results/dev4/frame_results.csv包含BASE与全部消融每帧数据，路径和证据按group/frame_id关联*_native.jsonl及*_local.jsonl，diagnostic_segments.jsonl合并详细证据。结果CSV的空值表示未确认，不把无真值误差写成0。results/final5/frame_results.csv为锁定候选全部帧。ground_truth_metrics区分合成与真实N/A。SHA256SUMS校验除自身外每项文件。


## 复现位置与范围

SDK的src可独立编译，bin的局部证据测试可用同目录OpenCV运行库执行。交付tests为冻结实验脚本副本，历史比较路径与本机工作区绑定，不宣称任意解压目录零配置。

已验证实验请在原工作区 D:/workspace/crack_v4_cpp/local_tip_20261030 运行，例如：
python D:/workspace/crack_v4_cpp/local_tip_20261030/tests/replay_dev4.py --modes OFF,RIDGE_SHADOW,RIDGE_CP_SHADOW,RIDGE_CP_GATED,FULL_LOCAL,FULL_NO_REFINE,FULL_PRODUCTION --run another_dev4_run
不要重新运行第五组脚本。现有第五组锁定输出已经完整保存。

P1在上、P2在下时，右法线指向本轮约定的主裂纹扩展侧。结果不代表同时检测了左右两条裂纹或所有分叉。

额外交付：14个完整H264视频（1920×1080，15FPS演示），2515张逐帧PNG、5份逐帧PNG压缩包、4份CSV、原图独立标注包、证据曲线。视频全部解码检查通过；15个PNG/视频对应点检最小PSNR为38.17dB，仅表示编码保真，与检测精度无关。

工程环境细节：CMake4.0.2，MSVC19.29.30159.0（v142），OpenCV4.4.0。

清理记录：config/cleanup_manifest.json及post_build_cleanup.json。冻结后只追加只读复核报告、证据曲线和交付说明，未修改算法、参数、DLL或已冻结脚本，也未重跑第五组检测。
