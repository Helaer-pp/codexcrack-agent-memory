# C2研究复现

本目录是独立研究输出。生产A不变，无C2 DLL。检测输入仅参考/当前灰度图、两帧P1/P2、冻结A合法当前结果。GT只在生成器和评估器读取。

当前 run01 已执行过 DEV和TEST；不要覆盖。TEST脚本有一次执行标志；复现实验应复制源码到新run目录，并保持相同依赖及原始输入，生成新的审计标识，不将复现误记为新的独立TEST。

在 `D:/ProgramData/anaconda3/python.exe` 执行（均为绝对路径的02_source脚本）：audit.py → replay_A.py → setup2.py → tests/test_contracts.py → replay_and_evaluate.py DEV → metrics2.py DEV → freeze2.py → replay_and_evaluate.py TEST → metrics2.py TEST → replay_exposed2.py → replay_real2.py。DEV版本迭代记录在09_dev_archive；最终被冻结源只对应最后DEV和一次TEST，不隐瞒先前失败。

10_delivery_tools/diagnostics2.py、media2.py TEST/DEV/real、report2.py、finalize2.py仅处理锁定输出，允许重新渲染，不重新运行检测。视频15FPS仅播放速率。原始F盘图片或D盘依赖缺失会报MISSING_SOURCE/依赖错误，不能从媒体重建同等原始输入。

环境与外部依赖见00_protocol/reproduction_environment.json；源/协议/输入的SHA见00_protocol/freeze_manifest.json、03_new_gt/input_gt_hashes.csv，最终交付见all_files.sha256。A峰值RSS包含整组预解码，不是流式内存。输入图像、基准点文件继续保留原位置，zip未打入数千张外部BMP。
