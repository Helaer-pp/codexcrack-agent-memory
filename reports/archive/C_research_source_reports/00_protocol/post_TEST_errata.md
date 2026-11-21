# 冻结后工程与统计勘误（没有重新检测TEST）

1. 旧研究工具把其目录插到sys.path前，直接运行replay_real首次在导入evaluate时发生ImportError，未执行任何真实帧检测/写入marker。新增run_entry.py按绝对文件路径绑定本轮evaluate；未编辑冻结源码，也未重跑TEST。媒体/报告允许采用同一入口。
2. 冻结评价器按case_id进行bootstrap，但假长/真长控制对共享背景、运动、噪声，应作为同一render-pair cluster。新增只读diagnose_results.py生成case_bootstrap_ci.csv，按pair_id或独立case_id聚类；旧评价器、原CI、预测和标签全部保留。该统计修正不触发成功发布，也不用于改参数。
3. 冻结评价器false_tail_fixed原始合计含所有正投影过长族、按帧计数。严格强假尾修复另按strong_serial_false_tail的独立案例单列，不能把弱线过长修正当成强假尾修复。
4. TEST使用新随机种子、新背景生成过程、未出现的分辨率及独立参数抽样；线宽/运动支持区间部分重叠，并非所有潜变量空间严格互斥。不能宣称全新物理材质holdout。未对困难帧、阴性或不可观察帧做事后删改。
