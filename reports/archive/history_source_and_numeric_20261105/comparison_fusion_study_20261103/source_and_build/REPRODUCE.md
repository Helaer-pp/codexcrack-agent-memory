# 重放方法

Python: D:/ProgramData/anaconda3/python.exe；生产依赖 D:/opencv-4.4.0/build/x64/vc15/bin，C++17/MSVC v142。依赖与哈希见 protocol_frozen.json、environment.json 与 source_inventory.csv。研究代码的工作区布局为 D:/workspace/crack_v4_cpp/frangi_comparison_20261103，依赖 common_cmp.py 指定的既有冻结辅助模块。交付副本用于离线审阅；原工作区可直接运行。

prepare.py、原生/GT/留出脚本均有防重复锁；不要在已完成目录覆盖执行。要重现实验，先在新的研究输出目录更改 common_cmp.OUT 并重新封存来源，保留原结果不动。

顺序：prepare.py → replay_A.py → unit_tests.py → run_real.py --mode native → generate_gt.py --split DEV → run_gt.py --split DEV → metrics.py --select-dev → freeze_protocol.py → generate_gt.py --split TEST → run_gt.py --split TEST → run_real.py --mode controlled → replay_A.py --holdout → run_real.py --mode holdout → metrics.py --all → media.py --group [group]（五组）→ media.py --synthetic → publish.py。

A0 使用原 DLL 和逐帧输入TSV，由 a_bench.exe 独立整组顺序回放，未从中间帧重置历史。F0 原ZIP文件及函数摘录在01_adapters，运行封装仅移除IO副作用。无Frangi C++移植/新DLL，NOT_TESTED_IN_CPP。


## 调用勘误（优先于上面的原始流程）

排除组X A 必须用 `replay_A_holdout_historical_config.py --holdout`，恢复历史 Auto(2)。Frangi 排除组X使用 `run_real_exact_enumeration.py --mode holdout`，其中 F0 仍为原计算，只有 F-WIDE 使用等价连通域枚举。先把两个驱动中的研究源/输出路径按新的独立工作区设置，并登记新哈希；不要在本轮已封存结果目录直接重跑。主源码 bundle 保留勘误前的锁定原件，交付 source_and_build 顶层另含上述补充。旧中断/失败调用不能作为有效结果。

完成 metrics.py --all 后执行 export_measurements.py、export_dynamics.py；媒体全部生成后执行 build_galleries.py、final_execution_notes.py，最后 seal.py 检查链接/帧映射/全部文件哈希。生产算法或 Frangi 阈值均不修改。
