# 运行说明

Python：D:/ProgramData/anaconda3/python.exe；Windows、OpenCV Python 4.12、NumPy/SciPy/scikit-image。冻结 A 是 C++17 / OpenCV4.4 DLL，不重编译、不修改。

本次研究的源文件同时保存在 D:/workspace/crack_v4_cpp/dg_prospective_20261103 与本目录。主工作区脚本绑定独立结果目录 DG_minimal_fusion_prospective_20261103。已封存输入/输出拒绝覆盖；若另起研究，先复制脚本并更改 study.py 的 OUT、生成种子和运行ID，再从头锁定新协议。

执行顺序（每步成功后再执行下一步）：

1. prepare.py → replay_A.py（五组2515原始图，正确历史reference-mode；完整native计时需独占运行，预解码不计入核心）。
2. tests.py → gt_generator.py NEW_DEV → evaluate.py NEW_DEV DEV_k25 --noise-k 2.5 → evaluate.py NEW_DEV DEV_k35 --noise-k 3.5。
3. summarize.py select → preflight.py → freeze.py（包含本轮源码、政策、生成器和指标哈希）。
4. gt_generator.py NEW_TEST_LOCKED（先封存原图、GT及SHA）→ evaluate.py NEW_TEST_LOCKED TEST（固定策略一次性执行）。
5. history.py（已曝光五组回归，不选择参数）→ archive.py（480合成逐图重放、336索引匹配鲜明native路径）。
6. report.py → media.py history → media.py synthetic → report.py index。

脚本参数只控制实验标签/DEV的两个全局noise-k候选；Detector仅接收图像、两组点和统一policy，不接收组名、帧号、GT、A路径。D/G/Frangi消融使用共同参考刚体映射。A本身仍按其原生refine-on处理，这是系统对照，不是宣称A和DG内部映射相同。

05_regression/*.jsonl 是历史DG逐帧路径；06_performance/native/*.pathbin 是冻结A的double路径（每帧int32数量、随后连续float64 x/y）。03_results/*/predictions.jsonl 保留合成案例的A正式与候选路径、DG/对照路径。正式媒体无确认仅原图；研究橙线为候选，所有标签清晰标明。

帧级统计键：case_id + frame_id + side + algorithm；图像身份另有input_sha256。空值/N/A代表不可评价，不能填0作为精度。真值只属于程序几何；真实物理尖端 N/A。A左侧NOT_SUPPORTED，不能把左侧缺失当原单侧A漏检。

未满足前瞻证据门槛时按任务书条件跳过C++边车：NOT_TESTED_IN_CPP。Python时间和15 FPS演示视频均不能证明原生完整核心15Hz。
