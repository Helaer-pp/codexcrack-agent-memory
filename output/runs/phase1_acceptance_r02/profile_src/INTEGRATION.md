# A 裂纹检测 · Windows x64 集成

本包以图像 ROI 内独立观测到的暗线末端确定尖端。参考帧的 P1/P2 只用于一次性建立固定裂纹坐标系；后续帧的 P1/P2 只提供粗刚体定位，固定参考纹理负责残余配准。尖端 ROI 的中心、方向、确认状态和结果坐标由细化后的参考几何确定。路径允许从 ROI 内任一段受支持的线开始。原根部追踪仅参与完整长度的确认。输入为原始 CV_8UC1 图像及原图像素坐标；P1/P2 必须对应同类物理位置、顺序正确，参考点还必须覆盖裂纹搜索区域。构建为 MSVC v142 x64 Release、OpenCV 4.4.0。本轮回放为 CT3 的八组选点，见 verification。旧版七组等价性及性能结论适用于上版 DLL。

## 在 Visual Studio 中切换

1. 头文件搜索路径指向本包的 `include` 和 `D:\opencv-4.4.0\build\include`，代码继续包含 `CrackV4.hpp`。
2. 链接本包 `lib/CrackV4.lib` 及 OpenCV 的 `opencv_world440.lib`。
3. 退出软件，将本包 `bin/CrackV4.dll` 和 `bin/opencv_world440.dll` 放在 EXE 旁，再启动软件。原先链接冻结 A 的软件可沿用原调用；原先链接 `CrackV4Adaptive.lib` 的软件改为 `CrackV4.lib` 并重新链接。要使用新增的分段读点接口，请同时更新头文件与导入库。

## 每组试验的调用顺序

```cpp
// 软件类成员，在整组试验期间保留
CrackV4Detector detector;

// 第一帧，只初始化一次。实际标定比例单位 mm/pixel
detector.initialize(referenceGray, refP1, refP2,
                    CrackV4Detector::ReferenceMode::Auto, mmPerPixel);
CrackV4Result first = detector.referenceResult();

// 从第二帧起，顺序传入当前帧和当前 P1/P2
CrackV4Result result{};
cv::Point2d tip = detector.getCrackTipPointCirculate(currentGray, curP1, curP2, &result);
const auto segments = detector.pathSegments();
if (result.tip_confirmed) {
    // tip 为当前原图像素坐标。对 segments 中每一段分别绘制折线。
}
double fullLengthMm = result.length_confirmed ? result.length_mm : 0.;
double computeMs = result.detector_ms;
```

确认尖端和确认完整长度是两个独立状态。断点之后证据充分时会给出尖端和可见路径，完整长度仍由 `length_confirmed` 单独判断。未确认尖端时显示 (0,0)，分段路径为空。`rawPath()` 为兼容保留，依次列出各段采样点；绘图使用 `pathSegments()`，避免在断点间画线。段内坐标均为双精度原图像素。每个采集流使用一个检测器实例，一帧的查询与绘制在处理下一帧前完成。

`detector_ms` 包含配准、基础追踪、触发的续追与尖端确认。`api_ms` 是 DLL 内处理调用耗时。两者均不含图像读盘、解码、路径复制和界面绘制。`initialize()` 单独返回初始化耗时。

本包 `example/main.cpp` 是可编译的命令行调用示例。用包内 CMakeLists.txt 配置 x64 Release 生成 CrackV4Example，依次传入参考模式（0 clean、1 cracked、2 auto）、标定比例和各帧的“文件路径 P1x P1y P2x P2y”。示例开头为参考帧，随后为变形帧。

上一版正式 A 备份为 `A_before_roi_tip.zip`。回退时退出软件，用备份中 `output/releases/A_Win64_OpenCV440/` 的 SDK 替换当前 SDK。更早的冻结 A 另有独立备份。
