# CrackV4：可靠性修订版 / OpenCV 4.4.0 / x64

原算法已另存快照，未覆盖原SDK或原DLL。本版本保留V4检测路径，修复状态问题，新增像素V2接口和默认旁路诊断，并删除未使用的tile复制。

**默认仍输出旧策略尖端与长度。新终端检查尚未标注验收，保持Shadow；不要把新检查通过当作真实物理尖端的保证。**

## 交付位置

- `bin/CrackV4.dll`、`lib/CrackV4.lib`：OpenCV4.4动态库；bin含所需runtime。
- `include/CrackV4.hpp`：保留原C++调用方式，另有`resultV2()`。
- `include/CrackV4_v2.h`：像素结果、新状态与开关；旧`CrackV4.h`布局保持。
- `src`：完整C++17源码、CMake和示例；DLL运行不依赖Python或神经网络。
- `tests`：工程回归、四组序列、固定种子扰动、合成真值、计时和抽样图工具。
- `results`：各阶段逐帧记录及单帧耗时；`reports`：基线、优化结果与抽样图。
- `history.bundle`：独立开发仓库的阶段提交，便于审查/回退。
- `baseline_location.json`：原版快照路径；原图不打包，`tests/datasets.json`保留原图路径和排序。

## C++接入

仍需链接CrackV4.lib及你软件使用的OpenCV4.4。头文件、lib、DLL使用同一份版本；x64 Release。每个图像序列保留同一个对象，不要每帧重建。

```cpp
#include "CrackV4.hpp"

CrackV4Detector detector; // 放在软件类成员中，跨帧保持

// 仅开始一组新试验时执行。输入完整CV_8UC1原图，不必手动裁剪。
detector.initialize(referenceGray, referenceP1, referenceP2,
                    CrackV4Detector::ReferenceMode::Clean, 1.0);
// 若不确定参考是否已有裂纹，用Auto；确认已有裂纹可以用Cracked。
// 1.0仅为兼容旧初始化参数，新V2结果全是像素，不使用length_mm。

// 每帧按时序调用；这两个点是当前图中与参考点对应的追踪点。
CrackV4Result legacy{};
detector.getCrackTipPointCirculate(currentGray, currentP1, currentP2, &legacy);
const CrackV4ResultV2 r = detector.resultV2();

cv::Point2d tip = r.tip_confirmed
    ? cv::Point2d(r.tip_px.x, r.tip_px.y) : cv::Point2d(0, 0);
double lengthPx = r.complete_length_valid ? r.root_to_tip_length_px : 0.0;
double computeMs = r.detector_ms;
// r.tracking_endpoint_px 可用于显示候选轨迹；不等于已确认尖端。
// r.terminal_verified / r.shadow_tip_confirmed 用于旁路诊断。
```

异常时清空本帧显示，记录错误；不要沿用上帧尖端。`tip_confirmed=false`时禁止用(0,0)与标距中心求距离充当裂纹长度。
长度由路径弧长计算；“标距中心到尖端直线距离”不等同于裂纹弧长。完整长度有效需尖端和根部有效。

## 功能开关

```cpp
CrackV4OptionsV2 options{};
CrackV4DefaultOptionsV2(&options); // Shadow + terminal_validation=1
detector.setOptionsV2(options);

// 完全关闭新审计的快速兼容路径（依然保留A阶段状态修复）：
options.decision_policy = CV4_LEGACY;
options.terminal_validation = 0;
detector.setOptionsV2(options);
```

更换选项时会清空时序历史，需在帧间操作。相同选项重复设置不清空历史。
`CV4_VERIFIED_EXPERIMENTAL`会按新证据改变输出，默认关闭，未通过四组人工标注验收，不建议生产使用。
需要丢弃当前序列历史但保留参考缓存时调用`detector.resetTemporal()`；更换试件/参考图调用`initialize()`。

## 编译

```powershell
& 'D:/CMake/bin/cmake.exe' -S src -B build -G 'Visual Studio 17 2022' -A x64 -T v142 '-DOpenCV_DIR=D:/opencv-4.4.0/build' '-DCRACK_V4_OPENCV_VERSION=4.4.0' '-DCRACK_V4_PROFILE=OFF'
& 'D:/CMake/bin/cmake.exe' --build build --config Release --parallel 1 -- /nr:false
```

固定4线程用于本次测量，`CrackV4SetNumThreads(4)`是进程级OpenCV设置，不在Create中偷偷更改。多相机部署需重新衡量线程数与CPU争用。

## 复现测试

测试工具需要Python、numpy和cv2；本次环境Python3.12.7、numpy1.26.4、Python cv2 4.12.0。**DLL仍使用OpenCV4.4.0**，不要混淆Python图像生成/解码与DLL依赖。无运行时模型。

以下从SDK根目录执行：

```powershell
python tests/engineering.py --dll bin --output results/recheck_engineering.json
python tests/sequence.py --dll bin --output results/recheck_sequence --expected results/final
python tests/perturbations.py --dll bin --output results/recheck_perturbations.json
```

工程测试自带生成场景，不依赖四组原图。全序列/扰动测试需原图存在；路径或排序变化先更新`tests/datasets.json`。
`sequence.py`在每组第1帧读取参考缓存，后续按原自动配准模式处理，记录每帧核心/API/磁盘读图耗时。前10帧warm-up和错误帧剔除规则见报告。
若使用逐帧实测基准点，应调用C++/C API传入两点；当前真实测试数据没有这类文件，不伪造输入。

`tests/paired_benchmark.py`需要本开发仓库的baseline、B、C三个阶段构建目录；它是驻留图微基准，不是相机实时测试。可用history.bundle回到相应提交重新编译。
`tests/analyze_results.py`重算报告需要保留打包的results和baseline_location.json；本地路径被保留用于回溯，不代表对外机器也能直接读取原图。

## 验证结果与限制

15项工程检查通过，四组共1991帧的默认尖端、长度、路径和状态与原版一致。新增审计保持旁路；仍有32帧原自动配准错误。
开发组HMT本机纯检测P95=46.03ms、max=52.63ms；磁盘读图+API P95=103.79ms。真实相机/显示链路未测，不能承诺软件整体15Hz。
局部阴影、大曝光变化、遮挡尾端仍有失败例。没有人工真值，不能宣称误报漏报或跨材料泛化得到改善。

详细数据：[优化报告](reports/optimization_results.md)、[V4基线](reports/v4_baseline.md)、[像素API](API.md)、[变更表](CHANGELOG.md)。
