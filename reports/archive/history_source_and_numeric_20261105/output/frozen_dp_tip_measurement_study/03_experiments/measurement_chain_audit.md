# M：NO_CHANGE

Stage0已先完整冻结四组A，随后才执行本审计。真实数据没有尖端GT；下列结论仅针对软件数学合同。

1. baseline/src/CrackV4.cpp::motion：单位化P1→P2方向建立旋转，双点中点建立平移；是刚体模型，不使用标距变化作整体缩放。输入原图x右y下，P1/P2身份固定。刚体模型不能描述全部局部材料变形，但不等于坐标软件bug，M不把刚体替换成相似/非刚体模型。
2. Detector::current及序列化transform_reference_to_current互相对应；当前路径逆映射/还原数学不变量见measurement_chain_per_frame.csv。anchor残差只是配准敏感性，不是尖端精度。
3. r.total=pyround(arc(full))、CopyPath直接返回d.last.path；V2返回0.01px取整数值，CopyPath保留双精度。全序列tip端点差≤0.0072px、弧长差≤0.0051px。此量化是既有接口合同，没有证据将其判为检测错误或篡改A。
4. 路径的smooth(path,3)发生在A的检测测量前；它属于冻结算法路径定义，不是显示裁剪操作，M不删除、不改变其端点。视频变换仅用于显示，长度重新核对原图点列弧长，禁止显示倍率进入测量。
5. 已生成15组已知坐标旋转/缩放/亚像素平移测试，独立验证正逆变换与弧长缩放。纯数学GT不是裂纹物理GT；后续旁路C++还会执行原生采样/前缀测试。
6. 正式有效性使用GetResultV2的tip&&complete_length_valid，不能按weak_candidate描述词删除正式有效结果。参考/当前缺失、饱和、遮挡和NaN属于质量或输入问题，不能由M凭空恢复。

没有发现应修改A坐标或弧长的软件错误，因此A+M严格NO_CHANGE。新增M只记录审计量，不改变DP、原路径或API数值。
