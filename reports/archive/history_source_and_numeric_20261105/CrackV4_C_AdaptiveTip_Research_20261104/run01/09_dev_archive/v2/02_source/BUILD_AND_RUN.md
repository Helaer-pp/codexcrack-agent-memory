# 复现

Windows Python: D:/ProgramData/anaconda3/python.exe；numpy/cv2/Pillow；冻结A依赖D:/opencv-4.4.0/build/x64/vc15/bin。C是独立Python研究V3，未替换生产DLL。

新建不存在的run目录后复制02_source；setup_protocol.py一次性锁输入合同。tests/test_contracts.py → evaluate.py DEV → freeze_test.py（锁源码并生成一次TEST）→ evaluate.py TEST → replay_real.py → media.py → summarize.py。已有run不得覆盖TEST/协议；脚本会拒绝覆盖已有执行标记。可直接导入research_c.run(ref,current,ref_points,current_points,A_result)，不传入试件名/帧号/GT。关闭C用enabled=False并由集成方使用原A结果。

若效果Gate4未过，不执行新C++/DLL融合，结论保留A。原生A基准使用现存a_bench.exe，C Python旁路耗时单列。
