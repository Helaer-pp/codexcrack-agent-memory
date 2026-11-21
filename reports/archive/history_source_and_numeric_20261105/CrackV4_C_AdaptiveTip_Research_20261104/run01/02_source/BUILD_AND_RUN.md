# 运行与冻结边界

生产A不变；当前C仅Python独立研究版，无C新DLL。依赖现有同工作区历史只读研究工具/冻结runner和OpenCV4.4，不是独立可分发SDK。

环境：Windows x64；Python3 / NumPy / OpenCV Python4.12 / Pillow / matplotlib / psutil；native A runner OpenCV4.4；FFmpeg见media.py。DLL及source SHA见00_protocol/frozen_A_identity.json。

已有TEST执行marker禁止重新检测或覆盖；freeze_test.py/evaluate.py是一次性新run流程，不能在此目录重跑。更换输入/调参需新run及新TEST。本轮评价和回放均已保存。

只读重算诊断和报告：
```powershell
& 'D:/ProgramData/anaconda3/python.exe' 'D:/workspace/CrackV4_C_AdaptiveTip_Research_20261104/run01/02_source/run_entry.py' diagnose_results.py
& 'D:/ProgramData/anaconda3/python.exe' 'D:/workspace/CrackV4_C_AdaptiveTip_Research_20261104/run01/02_source/run_entry.py' summarize.py
```
只重渲染已有预测（不重新检测）：
```powershell
& 'D:/ProgramData/anaconda3/python.exe' 'D:/workspace/CrackV4_C_AdaptiveTip_Research_20261104/run01/02_source/run_entry.py' media.py
```
全部逐帧结果04_results/frame_predictions.csv包含REAL/DEV/TEST及8配置，以evaluation_split区分；原文件分别保留REAL_*/DEV_*/TEST_*。GT仅评价/渲染使用，不输入检测器。

正式集成仍使用原CrackV4Detector。C研究入口research_c.run(ref,current,reference_points,current_points,a_candidate,variant)返回独立output/adaptive/candidates/runtime；tip/length失效是null+validity，不得直接取未确认候选当测量。A路径可作为候选而非终点裁决。所有坐标是原图pixel，长度是基准线投影pixel。
