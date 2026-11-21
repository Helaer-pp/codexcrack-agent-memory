# CrackV4 四组恢复评估候选（2026-10-30）

这是待人工复核候选，未替换原生产版本。算法源提交：872510984a16658284ce7e6457bfdd366a5ec37b。
当前DLL SHA256：52ae56280a38122fea7ac267de7a6758f7b379eb820d58dbe6adcbe1bb0f8ba1。OpenCV 4.4.0，Windows x64，MSVC v142 /MD Release。

## 选择正确模式

本轮评估：CrackV4CreateExtended + flags=32244 + Shadow1 + terminal_validation=1 + refine_anchor_motion=1。
旧正式对照：flags=3572；撤回v3只作诊断对照：flags=15860。
默认CrackV4Create和原CrackV4Detector.initialize并不会启用32244。三个旧EXE用于ABI兼容演示，保留其原来配置，不作为本轮候选的运行入口。

## 最小调用顺序

```cpp
#include "CrackV4_experiments.h"
// 每个试验保存一个handle，不要每帧创建局部检测器。
CrackV4SetNumThreads(4);
CrackV4Config config{}; CrackV4DefaultConfig(&config);
config.reference_mode = 2; // Auto；Clean=0，Cracked=1
config.refine_anchor_motion = 1;
config.mm_per_pixel = calibrated_mm_per_pixel; // 未标定时用1，只按像素解释
CrackV4ExperimentOptions experiments{}; CrackV4DefaultExperimentOptions(&experiments);
experiments.flags = 32244; experiments.max_debug_images = 0;
CrackV4Image ref{reference.data, reference.cols, reference.rows,
                 static_cast<int64_t>(reference.step)}; // CV_8UC1原图
CrackV4Point referencePoints[2] = {{refP1.x, refP1.y}, {refP2.x, refP2.y}};
CrackV4Handle handle = nullptr; char error[4096]{}; double initMs = 0;
int rc = CrackV4CreateExtended(&ref, referencePoints, &config, &experiments,
                               &handle, &initMs, error, sizeof(error));
// rc非0：记录error，不进入Process。
CrackV4OptionsV2 options{}; CrackV4DefaultOptionsV2(&options);
options.decision_policy = CV4_SHADOW; options.terminal_validation = 1;
rc = CrackV4SetOptionsV2(handle, &options); // 初始化后设一次；每次修改会清空时序状态

// 随后每帧按时间顺序执行：
CrackV4Image im{current.data, current.cols, current.rows,
                static_cast<int64_t>(current.step)};
CrackV4Point currentPoints[2] = {{curP1.x, curP1.y}, {curP2.x, curP2.y}};
CrackV4Result result{}; result.struct_size = sizeof(result);
rc = CrackV4Process(handle, &im, currentPoints, &result);
// 先检查rc，再按有效位读取：
// result.tip_confirmed -> result.tip（当前原图像素坐标）
// result.length_confirmed -> result.length_px / result.length_mm
// result.detector_ms -> 单帧内核耗时
// 无效时可把UI值设0，但数据中必须保留tip_confirmed/length_confirmed。
// 不用p1/p2中心到尖端的直线距离冒充裂纹路径弧长。
CrackV4ResultV2 pixel{}; pixel.struct_size=sizeof(pixel); pixel.api_version=2;
CrackV4GetResultV2(handle, &pixel); // root_to_tip_length_px只在complete_length_valid为1时有效
// 最后：CrackV4Destroy(handle);
```

参考/当前图传入原图与对应原图坐标，不需要手工裁剪。两点保持物理对应与顺序，p1上p2下时预期向右。初始化参考图只用一次，之后使用逐帧实测点。相同实例不可并发Process。只读查询不推进时序。输入图必须CV_8UC1且尺寸与参考一致；保留cv::Mat在调用期间有效。调用方需要检查每个返回码。

CopyPath在启用4096后返回受支撑可见路径；该路径可能没有物理尖端，不能无条件当完整裂纹。完整确认路径、候选及支撑路径在LastJson/LastPathAuditJson中分开保存。库返回JSON指针需及时复制；不要跨下一次调用持有指针。

## 编译和回退

include/头文件，bin/CrackV4.lib，运行时bin/CrackV4.dll与opencv_world440.dll。调用程序使用兼容的x64 /MD Release运行库；不把调试版opencv_world440d.dll混入。
源码src/与本轮锁定源码逐字节一致。运行powershell -File build.ps1 -BuildDir build_reproduce，使用D:/opencv-4.4.0/build与MSVC v142重新编译；编译环境路径可在构建脚本中调整，不能把另一OpenCV版本冒充本轮验证版本。
rollback/保留原发布及撤回v3二进制。旧模式3572和15860逐帧兼容结果均为0差异；原C与PixelV2结构尺寸保持不变。回退时同时选择原二进制和原配置，先结束当前handle再初始化。

## 结果边界

原336回退中恢复311，仍有25，另外新增6回退。四组最慢开发组H49.86ms，1987张当前图均未超过66.67ms；这个计时不含图像读盘/编码/显示。
合成低对比depth6和新出现的独立暗线干扰仍未通过正例保留检查。真实试验没有人工GT，不能把覆盖数当成真实精度。
第五组锁定后完整确认213/523，路径截断198，最慢71.50ms（1帧超预算）；它仍未通过普适性与全帧15Hz要求。本候选不因这些结果反向调整参数。
