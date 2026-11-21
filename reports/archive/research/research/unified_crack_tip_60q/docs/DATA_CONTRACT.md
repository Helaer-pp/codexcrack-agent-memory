# 本轮数据合同

仅 GROUP_A551、三点弯520 DEV；验证组C562 LOCKED；总1633。历史三点弯验证角色在最新明确任务中被改为本轮 DEV，不改全局政策、不训练标注。验证组C曾曝光，不是新盲测。本轮冻结前不读其图片、实际P坐标或GT。

原始输入来自 metadata 清单与原始 TXT，按 tracking_num 连续顺序。frame_id=tracking_num+1 仅用于 IO。P1/P2 为缺口两侧材料点，不是尖端/根部，P连线不是前进方向。排序只规范P标签；初始+x、最终最大x保持原图语义。当前P不可用时接口可退到历史/初始几何并标记降级；批量数据必须验证当前P合法，若发现缺失立即记录阻塞，不悄悄跳过。

固定参考为原始初始帧；prev 为实际紧邻原始帧，绝不取最后成功帧。首帧prev为None、差分NaN、valid=False。两路单独P粗对齐、材料上下窗口NCC/配准后交错子集一致性检查和局部精配准。无效区域的诊断 signed 可保留估计值，但有效性False；特征仅消费有效掩膜，unavailable不是零或负证据。实际 unavailable 存NaN。差分定义 reference_aligned-current；signed 与 masks 永久成对保存。

每帧输入文件 SHA256、原图 uint8/二维尺寸、TXT SHA256、P、参考配对写入metadata。数组NPZ不做float16压缩。原始ROI为uint8；valley、signed、confidence、段/图特征数值原样保存。生成内容只在output；F盘及原始点位只读。

GT仅独立评价进程在无GT推理seal验证后读取；按源图SHA/压缩包member绑定，确认visible19/15/20。没有尖端的已标注图为UNKNOWN，未标注帧为UNLABELED；二者均非真实阴性，真实FPR=N/A。

注意：原生字段 `holdout_ncc` 命名不严谨。交错像素子集已参与整块模板匹配，因此这里只是拟合后的子集一致性，不是未参与拟合的独立留出验证；不可据此声称无过拟合或物理配准已验证。字段为保留原生结果不改名，语义在报告中更正。
