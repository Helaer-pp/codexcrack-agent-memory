# V5.10 原生实现

工程目标 `CrackV510` 编译 Win64 动态库，`CrackV510Example` 编译使用公开 C++ 接口的示例。CMake 从项目内的 OpenCV 4.4.0 SDK 链接，Visual Studio 2022 使用 v142 工具集。面向软件调用方的说明见 [集成说明](集成说明.md)。

```powershell
cmake -S . -B output/build/v510_native -G "Visual Studio 17 2022" -A x64 -T v142
cmake --build output/build/v510_native --config Release --target CrackV510Example
```

从项目根目录运行。主要源码按处理阶段组织。

| 文件 | 处理阶段 |
|---|---|
| registration.cpp | 原图跟踪点生成采集区域、分块参考重映射、缺口／两侧纹理和轮廓配准 |
| geometry.cpp | 参考材料带、缺口顶点吸附、入口与局部噪声估计 |
| evidence.cpp | 原图灰度与有符号差分评分、预存裂纹、细脊及静态背景过滤 |
| tracking.cpp | 分入口方向状态 DP、谷后峰、限域桥接、分支重排与回溯 |
| api.cpp | 序列句柄、固定参考、可选亮区几何、路径缓存和长度输出 |

`parity.py` 通过导出的 C ABI 读取原图进行回放，逐帧对照 `output/experiments/v510_vertex_r02` 中已封存的 Python 路径。仅开发组开发组A可在冻结前运行。冻结文件位于 `output/verification/v510_native/freeze.json`，验证组回放会检查 DLL 摘要。冻结时记录当前 DLL、开发组A完整对照 CSV 与 Python 原始预测的 SHA256。核验结果和依赖清单齐备后，`python -m src.cpp.v510.package` 生成安装目录与 ZIP。
