# 本轮执行差异与勘误
1. Gate1按预注册的跨场景覆盖条件失败，未推进正式停止候选、共同证据排序、新TEST和新C++DLL，依据任务书顺序门槛。216帧工程DEV用于机制与失败审查，不作为独立TEST。
2. 所有当前A尖端由原生V2精确保留；参考比较使用LastJson已提供的实际矩阵，没有修改A以导出矩阵。额外flags3573只在独立诊断运行，992帧状态与double路径完全一致。
3. 真实误配准率没有GT，仅报告状态/留出残差。原图参考邻域的严格mask与后续模板<=3%规则存在保守程度不一致，后锁定诊断只计数，不反馈预测。
4. key-case媒体二维warp最初遇到OpenCV remap单行长度上限；仅在post-lock工具改用二维map修复，不涉及测量源码/数据。所有冻结运行源码hash仍不变。
5. 内部逐组研究JSON保留native root_confirmed但root字段最初未导出；public_contract.jsonl序列化导出从已有native measurement关联root坐标，无尖端/路径/证据更改，原始研究记录保留。正式公共合同使用six_groups_public_contract.jsonl；root来自native JSON的0.01px序列化，不表示物理精度。
6. 本轮没有C++ A′算法产物，aprime_cpp/NOT_BUILT.md明确说明。新性能/TEST缺失字段写NOT_TESTED/NOT_EXECUTED，不伪造空实验结果。
