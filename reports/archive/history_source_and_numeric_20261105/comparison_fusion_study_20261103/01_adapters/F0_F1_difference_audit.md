# F0 / F1 逐项差异

- F0_original 是原 ZIP 逐文件原样解包，持续核验 SHA；源文件没有改算法、路径常量或输出 CSV。
- source_module 只执行常量、三个原函数与原逐帧计算片段。移除顶层 mkdir、硬编码读写、导出绘图/视频的副作用；不调用原 run_pipeline。
- 每组参考图及参考 ROI、专用根部/掩膜、midpoint 平移、差分、Frangi、阈值、桥接、连通域、骨架、argmax/min x 保持原算术。提取计算段原文另存 *_extracted_core.py.txt；与原 CSV 尖端/投影逐帧审计，任何差异保留不调参追平。
- F1 在专用四组只增加测量语义：整数 tip_roi → tip_ref → 当前 raw 回投；在同一骨架中选有序主路径并计算弧长；原端点和水平投影不改变。缺失 tip 与 CT2 的根部占位不当有效检测。root-gap>25 时弧长 unavailable，不补画根部连线。
- F-WIDE 是单独 ROI 实验：原 x 范围/检测参数固定，只增加高度并平移掩膜局部坐标；不能称 F0 等价。
- 验证组C没有原专用脚本；F1 是预注册通用迁移（参考图黑暗连通域 + 基准点比例），不是 F0，不含人工验证组C根部常数。
- 公共受控分支是独立的简单 D/F/G/C/S 实验，不是把原 F0 的专用流水线伪装成通用算法。缓存只在同次调用共享组件/骨架，保留独立 uncached 实现，随机固定对照及验证组C全序列逐输出相等断言均保留。
- 合成 F-NATIVE-ROI 只是预声明窄物理范围代理，原 F0 硬编码 ROI 在小画布上不适用，F0 合成 GT 对照 NOT_APPLICABLE_NATIVE_FIXED_ROI。真正原生 F0 的结果仅在对应真实四组全量报告。
- 所有长度以 px 比较，A ratio=1；没有为各组假设共同 mm/pixel。没有 Frangi C++ 移植或新生产 DLL。
