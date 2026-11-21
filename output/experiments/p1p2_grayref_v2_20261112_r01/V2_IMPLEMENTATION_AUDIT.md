# 实现与模块隔离审计

- python_v2/algorithm.py：evidence保持V1 ROI、平滑、flank和双点remap；quality计算上下独立纹理质量；Tracker.seeds实现二维当前谷候选/NMS/短程验证；Tracker.walk使用同范围逐列路径；run_mode明确M1/M2开关；terminal_candidates只被独立TERMINAL调用。
- python_v2/frozen_adapter.py：编译精确不可变V1文件；Unicode安全读图接口；6份trace/summary生成后跳过绘图。G0同图完整未修改CLI对照及全2647帧六轨迹旧回放一致。原始算法源码未改。
- cpp_v2/evidence.hpp：V2目录内保留V1预处理数学，删除旧追踪方法/调用；不链接旧DLL。v2_detector.hpp独立实现质量、起源、数值规则、逐列路径和停止，runtime.cpp导出GrayRefV2*。无Python回调或组名/帧名/GT参数。
- V2_NUMERIC_CONTROL独立记录新整数拟合与输出安全合同；core三种V2共享该底座，额外控制不可混淆原V1。NUMERIC_CONTROL与V1的所有差异保留。
- 不足8观测/歧义UNCERTAIN；无候选/无观测NO_TIP；贴右界ROI_LIMITED；非法点INPUT_ERROR；其他满足支持要求才PROVISIONAL_OBSERVED。candidate_tip是审计候选，不计有效命中。原V1状态仅反映历史暂定输出。
- M1和M2仅改变锁定机制，TERMINAL没有改变COMBINED候选/主路径选择。新配准M3与TEMPORAL_ON均NOT_IMPLEMENTED，不隐藏在核心消融。
- 原生预测精度1/1024px、分数1e-6是全局数值合同，tie由小y/小x/稳定ID确定。合成弱2/3列保留为线索但拒绝单独认证；合成旧划痕阴性仍产生误输出，已明确失败。
- reference_quality中的tile code2表示纹理可靠性；只有结合逐候选delta才区分EXISTING_DARK_OR_NO_INCREMENT与NEW_DARK_SUPPORTED。code0/1是未知/不可靠，不能用0差分伪装可靠反证。独立局部NCC另记INDEPENDENT_NCC_NOT_APPLIED，不进入推理。

本轮只有r01，未做一次可选开发设计修复；工程可运行不等于算法成功。所有新增源码位置及原始哈希见source_manifest.json/配置锁。
