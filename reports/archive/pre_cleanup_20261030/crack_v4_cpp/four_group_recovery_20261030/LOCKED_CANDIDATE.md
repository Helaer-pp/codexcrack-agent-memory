# 四组恢复候选锁定

算法源码提交：872510984a16658284ce7e6457bfdd366a5ec37b。
锁定时刻：2026-10-30T02:11:36.312539+00:00。
DLL SHA256：52ae56280a38122fea7ac267de7a6758f7b379eb820d58dbe6adcbe1bb0f8ba1。

flags=32244，Shadow1，terminal_validation=1，refine_anchor_motion=1，OpenCV4.4.0四线程。
参数与源码文件哈希详见deliverables/config/algorithm_lock.json；锁定副本在locked/。
src/和build.ps1在独立验证开始后不可修改；第五组结果不得反馈调参。后续报告、绘图与打包脚本修正不改变算法或参数，最终交付再次逐文件核验。

本轮选择范围仅开发组A、验证组C、CT2、开发组H及合成数据。首次引用第五组输入是在tests/locked_external.py校验上述锁定后。该组在以前的轮次已经观察，不能宣传为全新盲测。

已知未解决：原336中25帧仍回退，另有6帧新增回退；两项合成正例失败。第五组完整长度确认213/523、截断198，最慢71.50ms（1帧超66.67ms）；不以少确认冒充精度改善。真实图像无人工GT。

本轮保留原生产版本，不自动替换；新模式必须显式使用CreateExtended和32244。默认C++适配器和原EXE不会自动切换到候选配置。交付sdk/README_调用与版本.md包含调用顺序。

复核入口：deliverables/index.html。每帧原图/检测对比图：deliverables/review/per_frame/{dataset}/；每组PNG打包ZIP与全部视频见deliverables/。
原四组回放在results/candidate/，原发布与撤回v3对照在results/trial1/，第五组在results/locked_external/，均指deliverables下的路径。
