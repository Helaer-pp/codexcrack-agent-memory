# 推理与标注隔离

engine/features/graph/config 不导入文件系统，不接收样本名、帧号、文件名、GT或人工路径。tests检查接口签名、拒绝gt关键字、配置拒绝未知字段；audit解析AST排除禁用运行变量。pipeline只处理源图、原始P、参考与清单；offline_evaluate从不被推理import。

序列进程每arm每组独立Engine，逐帧推进，前一图按原始metadata映射，即便前帧没有tip也不改变。并行仅用于无历史特征或不同arm/序列。缓存不含标签、预测或未来信息，禁用参考的arm不消费其特征。原始数组源图重算核对、首三帧全原生结果/状态重放保证序列可复现。

每组arm输出seal记录全部result/debug/lineage/summary hash。离线评价先后都核验seal，对GT只读并记录member SHA。LOCKED prepare与infer入口强制检查prevalidation_freeze的整个源码树hash及DEV完成seal。未生成freeze前不给验证组C像素/坐标访问入口。最终再核验历史176105文件与所有输入结果图。

这些是工程隔离与审计，不证明历史曝光数据为盲测；既有GT语义、真实裂纹身份和物理配准仍有外部证据局限。用户标注不作为模型训练。

执行中发现通用 `run.ps1 check` 绕过本轮角色入口、在冻结前实际执行了旧 A 验证组C图像/点位回放。没有新算法验证组C调用或参数变更，但不能将新入口的门控检查通过扩大为整个开发过程隔离通过。最终 DATA_ISOLATION_AUDIT=FAIL_WITH_DISCLOSED_DEVIATION，见run内协议偏差报告。原始标注仍只在封存后比较。
