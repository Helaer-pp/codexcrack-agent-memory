# GrayDetectionV2 C++ 工程

在 Visual Studio 2022 中打开 `GrayDetectionV2.sln`，选择 **Release | x64**，使用“生成解决方案”。独立工程包自带算法源码、OpenCV 4.4.0 头文件、x64 导入库与运行库。VS 安装项为“使用 C++ 的桌面开发”、v143 工具集和 Windows SDK，接口生成脚本使用 CMake 3.20 或更高版本。工程优先调用 VS 自带的 CMake，也支持 PATH 中的 cmake.exe 或 MSBuild 属性 `CMakeExe`。

## 发布编号

编辑工程中唯一的编号文件 **VERSION.txt**，保存后重新生成。格式为四段十进制整数，每段 0–65535。首版为 **2.2.0.0**，接续原 GrayDetection 的 2.1.1.0。当前检测算法为 **V6.3 S2**，二者可独立管理。

默认输出为 `output/releases/GrayDetectionV2-2.2.0.0/`，其中包含 `GrayDetectionV2.hpp`、`GrayDetectionV2.lib`、`GrayDetectionV2.dll`。编号修改后，新版本生成到对应目录。解压的独立工程使用工程内的 output，CodexCrack 中的工程使用 CodexCrack/output。

在资源管理器中查看 DLL 的“属性 → 详细信息”，文件版本和产品版本均显示发布编号。在软件中调用 `GrayDetectionV2BuildInfo()` 可同时确认算法版本、API 名称、OpenCV 版本和 DLL 编号。

## 接入宿主

包含 `GrayDetectionV2.hpp`，使用 `GrayDetectionV2` 类或同前缀的 C 函数，链接同版本的 `GrayDetectionV2.lib`。启动时，EXE 需要能加载 `GrayDetectionV2.dll`、`opencv_world440.dll` 与 x64 Visual C++ 运行库。OpenCV DLL 随独立工程放在 `third_party/opencv440/bin/`。

仓库内的解决方案直接引用 `src/cpp` 中的算法实现。独立工程包将所需源码放在工程下的相同相对目录，支持迁移到另一台开发机重新编译。
