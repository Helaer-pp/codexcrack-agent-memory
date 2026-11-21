# CrackV4 PerFrameAnchors OpenCV440 SDK

x64 Release /MD，OpenCV4.4.0，D:/opencv-4.4.0构建。bin含CrackV4.dll、3个已编译示例、原有预编译LegacyExample及运行库；include含C ABI/Pixel V2/实验接口和C++包装器，lib含导入库，src/build.ps1可重编译。

推荐本轮显式配置：CreateExtended flags3572 =244+AnchorPositive256+GuardedRegistration1024+RejectErasedTerminal2048，refine_anchor_motion=1；policy=1 Shadow、terminal_validation=1。Auto方向不加256/512，负法向使用512替代256，二者互斥。默认兼容接口仍flags0；不能从默认C++包装器调用推断已启用这些扩展。

初始化只做一次：原始CV_8UC1参考图+参考双点+reference_mode（0无裂纹、1已有裂纹、2自动）。每帧Process传当前图+本帧追踪的同物理双点；保留同一个handle。原图坐标x右y下，不裁剪/不缩放。GetResultV2读取像素尖端、完整长度与各自有效性；CopyPath读取路径。未确认时不使用上一帧或中点到尖端距离代替测量。

LastGeometryJson只读返回配准状态和当前输入点有效性，LastQualityJson提供路径/末端/历史独立审计。GetBaseline只读，不推进时序；开始新试验销毁重建，或按需ResetTemporal。本轮不更改C结构尺寸与旧导出函数。

命令行示例（参数均原图像素）：

```
bin/CrackV4ExperimentExample.exe reference.bmp current.bmp refX1 refY1 refX2 refY2 curX1 curY1 curX2 curY2
```

完整逐帧回放/对照/视频/标注源码在validation_source.zip；源图仍在原F盘目录，未重复打包。将其解压到本SDK根目录（与bin、src同级），保留SDK已有的运行库，再运行validate_perframe.ps1。归档保留四份实际坐标记录、时间顺序映射、三个冻结二进制与当前候选构建配置。迁移机器需修改数据目录和本机工具路径后复现；Python/OpenCV只用于测试读图，DLL本身不依赖Python。CSV导出依赖当前Codex捆绑的artifact运行时，未安装时可用-SkipCsv保留JSONL。

默认接口数值兼容不代表真实精度保证。真实裂纹人工标注缺失，实际尖端/长度误差N/A；15Hz结果仅对应报告中的本机内存输入Process计时。过曝、遮挡、实测点错误、多个背景块一致误配仍可能失败，详见交付reports。
