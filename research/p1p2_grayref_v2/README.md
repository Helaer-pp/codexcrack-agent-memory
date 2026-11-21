# P1/P2–GrayRef V2 r01

独立研究实现；不替换生产A或冻结V1。Python与C++只接收参考/当前uint8灰度图和各自P1/P2原图坐标，无文件名、组名、帧号、GT或历史上下文推理参数。

完整新运行（新目录必须在项目output内）：

```powershell
Set-Location .
& ./research/p1p2_grayref_v2/reproduce.ps1 -Output './output/experiments/p1p2_grayref_v2_replay01'
```

仅构建独立C++ DLL：

```powershell
& ./research/p1p2_grayref_v2/build.ps1 -Output './output/build/grayref_v2_separate'
```

单对Python CLI：用`cli.py --reference <BMP> --current <BMP> --p1-ref x,y --p2-ref x,y --p1-cur x,y --p2-cur x,y --output <全新output子目录>`。必须提供真实当帧点，不用验证组C黄金点套到其他实验。

模式：V1_LOCKED为不可变源的真实对照；V2_ORIGIN_ONLY、V2_REF_ONLY、V2_COMBINED为核心消融；V2_NUMERIC_CONTROL隔离新数值/安全合同；V2_TERMINAL为额外停止模块。默认COMBINED，不按组挑模式。参考remap/ROI保持V1，不扩CT3边界。TEMPORAL_ON与新参考配准M3未实现。

V2只提供暂定像素路径与端点。开发默认COMBINED命中4/76（V1为12/76），没有跨组精度通过；合成旧划痕仍有错误输出，不可生产使用。完整报告与六组视频/每帧图像位于`output/experiments/p1p2_grayref_v2_20261112_r01/`。

数据角色固定：开发GROUP_A/CT2/开发组H/CT3；验证组C/三点弯为已曝光验证回归，不调参；排除组X排除。标签仅完整推理后的离线对比，绝不训练/拟合/初始化。CT3使用明确帧名/坐标编号历史CSV，独立原始TXT缺失限制保留。

独立原生API见GrayRefV2.h。图像内存借用至Process返回，返回JSON/数组指针在下次Process或Destroy前有效；调用方需自行复制。每对象单调用线程，OpenCV设置1线程；多对象并行实测由不同进程执行，不声明同一对象线程安全。输出状态不可等同FORMAL_OBSERVED；candidate_tip只是审计字段，UNCERTAIN不计准确率命中。

C++测试通过完整复现入口调用`parity.py`，实际加载新DLL并运行内置`GrayRefV2NumericSelfTest`、6个合成输入和全2647帧+136个固定案例，五模式逐层比较。交付快照的测试驱动位于相邻`python_v2/parity.py`和`python_v2/native_v2.py`，C++数值自检位于`runtime.cpp`。不要对已封存输出重跑覆盖；使用新输出路径的一键复现。原生API本轮每次计算五个模式，计时并非单模式性能。
