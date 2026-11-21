# A′3 预登记（首次NEW_DEV评估之前）
生产A零修改；flags3572/SHADOW1/terminal1/refine/4线程。K≤12，最多4096路径采样，事件提议而非等距候选。
Gate A：NEW_DEV observable候选正确数相对旧候选器至少增加5帧；强假尾增加>=1、弱裂纹增加>=1；A已确认端点100%保留；不损失任何旧oracle正确帧作为研究目标；无GT输入运行时。
Gate B：与旧v3参考对照，NEW_DEV可信争议覆盖平均严格提高，独立已知运动>1px误接受不增加；分开统计完整争议段与any query。若仍不能跨材料支持，NOT_GENERALIZED。
激活：至少12独立pair/3背景过程，假尾A>32px且真长A<=8px，当前图与锚点完全相同。
Gate C前置DEV：实际正确数严格增加、惩罚损失降低、阴性FP不增加、A_correct_changed_wrong=0，灾难性>160px错改=0，真长/交叉/既有裂纹变暗负控。
旧数据只做曝光诊断；NEW_TEST须全部前置Gate满足且生成前冻结一次。缺完整原生实现即Gate D NOT_TESTED；生产保持A。
无真实物理GT，真实MAE=N/A。单调先验关闭，无未来帧，PHASE_UNKNOWN。
