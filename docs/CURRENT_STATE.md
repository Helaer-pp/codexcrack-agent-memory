# 当前开发状态

当前研究版本可从固定入口运行。请编辑 [脚本顶部手动设置区](../run_crack_tip.py#L3)，启动 [CrackTipRunner.exe](../output/releases/CrackTipRunner/CrackTipRunner.exe)。[运行与渲染说明](CURRENT_CRACK_RUNNER.md)。

## V6.3 白底漆配准与材料带解耦

Windows x64 集成测试可使用GrayDetectionV2 动态库，公开类名为 GrayDetectionV2，21 个 C 函数统一使用 GrayDetectionV2 前缀。旧工程需更新调用名并重新链接。[下载 V6.3 S2 集成包](../output/releases/GrayDetectionV2-2.2.0.0.zip) · [接入说明](../src/cpp/v63/集成说明.md) · [新库链接验证](../output/verification/GrayDetectionV2_2_2_0_0/integration.json) · [V6.3 算法全量对照](../output/verification/v63_dll/REPORT.md)

V6.3 S2 是当前研究候选。开发组A 18/19、三点弯 8/15、验证组C原点和亮区各 18/20。开发组H从 3/18 恢复到 8/18，仍低于 V6.1 的 9/18，第 216、221 帧均提前超过 100 px。开发组H在 −150 和 −350 px 两档实际左移中各有 410/410 帧保持材料带、缺口坐标与全路径一致。正式矩阵误报 0/468，另行构造的旧线侧移对照仍有 22/30 误报。日常默认 V5.15 S2。

[开发报告](../evidence/v6_3/REPORT.md) · [失败审计](../evidence/v6_3/FAILURES_AUDIT.md) · [开发组H专项](../evidence/v6_3/GROUP_H_REPORT.md) · [四组视频与逐帧对比](../output/experiments/v63_white_primer_r01/difference_views/index.html)

## V6.2 全宽参考缺口与尺度门控

V6.2 S2 的冻结验证已完成。联合命中为开发组A 18/19、三点弯 8/15、验证组C原点与亮区各 18/20、开发组H 3/18。验证组C V6.1 丢失的 13 个帧次全部恢复。合成开口误报清零，总误报 1/468，弱材料桥 36/36。开发组H左移 150 px 后，全部 410 帧的纵向材料带裁出了名义缺口。名义点位的配准窗口也都在计算 NCC 前被拒绝。日常默认 V5.15 S2。

[开发报告](../evidence/v6_2/REPORT.md) · [失败审计](../evidence/v6_2/FAILURES_AUDIT.md) · [开发组H专项](../evidence/v6_2/GROUP_H_REPORT.md) · [四组视频与逐帧对比](../output/experiments/v62_global_notch_r01/difference_views/index.html)

## V6.1 中心缺口与零回退门控

研究候选为 V6.1 S2，日常默认继续使用 V5.15 S2。联合命中为开发组A 18/19、三点弯 8/15、验证组C原点 12/20、亮区 11/20。开发组H 410 帧均定位到缺口，342 帧有尖端，联合命中 9/18，严重提前 2 帧。合成误报 9/468，弱材料桥 36/36。左移 150 px 时，开发组H参考定位窗截断了原有中心缺口。

V6.1 的四联图、差分和视频已封存。[完整报告](../evidence/v6_1/REPORT.md) · [失败原因](../evidence/v6_1/FAILURES_AUDIT.md) · [开发组H专项](../evidence/v6_1/GROUP_H_REPORT.md) · [四组图册](../output/experiments/v61_center_gate_r01/difference_views/index.html)

## V6.0 上下分侧配准与物理尺度

研究展示采用 V6.0 S2，日常默认 V5.15 S2。S1 在三点弯取得 9/15 个 Joint，验证组C原点和亮区均为 19/20，但合成负样本误报 36/468。S2 的 Joint 为开发组A 17/19、三点弯 8/15、验证组C两套点位各 18/20。S3 改善了 P6 三倍率截断，合成负样本仍误报 18/468，并失去三点弯第 306 帧的 Joint。三个阶段均无 >100 px 的可见标注尖端错误。

V6.0 S2 已封存。历次封存结果可通过各版本报告查看。[开发报告](../evidence/v6_0/REPORT.md) · [失败与差分审计](../evidence/v6_0/FAILURES_AUDIT.md) · [全序列逐帧图与视频](../output/experiments/v60_split_reg_r01/difference_views/index.html)

## V5.16 精度收口验证

四阶段均已冻结并完成验证。研究交付为 V5.16 S3，日常默认继续使用 V5.15 S2。S3 的 Joint 为开发组A 17/19、三点弯 8/15、验证组C原点 18/20、验证组C亮区 18/20，严重错误 0。S3 收回三点弯 335、413、503，失去原先命中的 215、271、381 和验证组C原点 7。三点弯 520 帧四进程含映射平均每进程 8.54 FPS，最慢 52 帧为 7.38 FPS。S4 改善了三种倍率的 P6，但继承了实帧回退。验证组C 7 的强制路由仅作事后诊断。

V5.16 S3 的实际推理与渲染已封存。[开发报告](../evidence/v5_16/REPORT.md) · [失败帧与阶段对照](../evidence/v5_16/FAILURES_AUDIT.md) · [逐帧局部对比、差分与视频](../output/experiments/v516_precision_closure_r01/difference_views/index.html)

## V5.15 缺口门控与大图窄带验证

本轮交付 S2 研究结果。Joint 为开发组A 17/19、三点弯 8/15、验证组C原点 19/20、验证组C亮区 18/20。验证组C亮区第 7 帧仍因入口得分不足而无预测。P4_open 误报归零，全部负样本误报 0/468，弱材料桥保持 36/36。S3 在两类 P6 划痕的三个倍率均为 0/12。三点弯 520 帧均约 18 万证据像素，S2 四进程并发时每进程含映射 9.22 FPS，检测 12.45 FPS。

[开发与验收报告](../evidence/v5_15/REPORT.md) · [失败原因与点位对照](../evidence/v5_15/FAILURES_AUDIT.md) · [逐帧四联图、差分和视频](../output/experiments/v515_clean_fast_r02/difference_views/index.html)

## V5.14 基准点与前端 ROI 解耦

S4 的 Joint 命中数为开发组A 14/19、三点弯 7/15、验证组C原点 18/20、验证组C亮区 15/20。四个口径均无超过 100 px 的定位误差。三点弯 215、248 保住 Joint。验证组C 38 的真候选被口门弧线校验拒绝。合成孤立划痕通过 9/36、变形划痕 6/36、活动分叉 36/36、弱材料桥接 34/36，负样本误报 5/468。三点弯完整 520 帧含上游映射的单进程和四进程每进程速度为 4.46 和 3.01 FPS，按 V5.13 的仅检测口径为 5.55 和 3.70 FPS。V5.14 保留为研究实现。

[开发报告与左移压力表](../evidence/v5_14/REPORT.md) · [失败帧、候选曲线与子步骤耗时](../evidence/v5_14/FAILURES_AUDIT.md) · [全帧四联图与视频](../output/experiments/v514_roi_decouple_r01/difference_views/index.html)

## V5.13 差分净得分与基准点验证

冻结后的 S3 在开发组A、三点弯、验证组C亮区分别取得 17/19、8/15、19/20 个 Joint 命中，验证组C原点另计 19/20。三点弯 215 和 248 恢复，248 重裁剪重配准的最大漂移为 0 px。验证组C 38 的端点误差为 1.58 px。孤立划痕未通过（0/36），弱间断通过 172/216，负样本误报 1/468。维持研究版本，未通过替换验收。

[开发报告](../evidence/v5_13/REPORT.md) · [失败审计与候选曲线](../evidence/v5_13/FAILURES_AUDIT.md) · [逐帧参考、当前、路径、差分与视频](../output/experiments/v513_unified_diff_r01/difference_views/index.html)

## V5.12 原生 Win64 动态库

研究 SDK 采用最初的 CrackV4.dll 文件名、结构体和导出序号。在同一 DLL 上回放开发组A 551 帧、三点弯 520 帧、验证组C亮区 562 帧，1,633 个尖端与确认状态一致，1,590 条折线逐点一致。最大弧长差 0.408 px。验证组C冻结选区随 SDK 单独提供。生产发布目录保持原版本。

[完整 SDK](../output/releases/V5_12_CrackV4_Win64_OpenCV440.zip) · [集成说明](../src/cpp/v512/集成说明.md) · [原生回放报告](../output/verification/v512_release/REPORT.md)

## V5.12 稳健配准与分支验证

V5.12 r01 在 54 个可见标注帧上取得 45 个 Joint 命中（开发组A 18/19、三点弯 9/15、验证组C亮区 18/20），V5.11 为 41/54，V5.10 为 46/54。验证组C原点另计 18/20，亮区 324、335、345 的严重错误已消除。三点弯 248 在空白跨度锁与根部连接门控叠加后提前 111.20 px，仍有一项严重错误。固定配准扰动最大漂移 0 px，重裁剪重配准最大漂移为开发组A 7.00、三点弯 119.34、验证组C亮区 4.00 px。合成孤立划痕 36/36、变形划痕 24/36，负样本误报 0/468。V5.12 未通过替换验收。

[开发报告](../evidence/v5_12/REPORT.md) · [失败审计](../evidence/v5_12/FAILURES_AUDIT.md) · [逐帧四联图和视频](../output/experiments/v512_stabilize_r01/difference_views/index.html)

## V5.11 差分双一致与配准验证

S4 在 54 个可见标注帧中取得 41 个 Joint 命中（开发组A 18/19、三点弯 9/15、验证组C亮区 14/20）。验证组C原点另计 18/20。验证组C 54 命中，38 仍失败。亮区 324、335、345 出现严重错误。固定同一 S4 算法换回上游旧映射，80 个标注帧与点位组合都复现 S3 端点。固定配准扰动最大漂移为零，全流程开发组A 299 漂移归零，验证组C亮区最差 215.13 px。合成弱材料桥接恢复至 36/36，负样本误报 0/468。三点弯全序列 3.62 FPS，低于 4 FPS 门槛。V5.11 未通过替换验收，保留 V5.10 比较基线。

[开发报告](../evidence/v5_11/REPORT.md) · [失败审计](../evidence/v5_11/FAILURES_AUDIT.md) · [逐帧图册](../output/experiments/v511_diff_unblock_r02/difference_views/index.html)

## V5.10 Windows x64 动态库

V5.10 r02 已移植为原生 C++17 / OpenCV 4.4.0 研究 SDK。三组 1,633 帧，含纯灰度与完整模式及验证组C两套点位的 4,390 次回放中，状态和尖端全部与冻结 Python 版相同，4,282 条折线逐点相同。对 DLL 输出按人工标注重新计分，完整模式联合命中 46/54。三点弯完整模式单帧平均 346 ms。生产 A 继续独立发布。

[Win64 SDK](../output/releases/V5_10_Win64_OpenCV440.zip) · [集成说明](../src/cpp/v510/集成说明.md) · [原生回放报告](../output/verification/v510_native/REPORT.md)

## V5.10 红脊分支择优与中段桥接

冻结版 r02 在开发组A、三点弯和验证组C共 1,633 帧上验证。full 联合命中分别为 18/19、10/15、18/20，验证组C两套点位同分。三组共 46/54，严重误差为零，与 V5.9 仅顶点吸附持平。验证组C 38、54 均只有一个合格候选，三点弯 215 仍提前 40.41 px。三点弯 2.53 FPS 未达到 4 FPS 验收门。暂保留仅顶点吸附基线。

冻结检测输入时，开发组A和验证组C亮区的同步扰动最大漂移均为零。从原始帧重建裁框与配准后，最大漂移分别为 18.25 px 和 4.00 px。三点弯为 93.38 px（无可见尖端标注的第 84 帧），可见标注帧最大 3.00 px。

[开发报告](../evidence/v5_10/REPORT.md) · [失败与退化分析](../evidence/v5_10/FAILURES_AUDIT.md) · [视频及逐帧图册](../output/experiments/v510_vertex_r02/difference_views/index.html) · [裂纹长度](../output/experiments/v510_vertex_r02/crack_lengths.csv)

## V5.9 材料带内缺口吸附与基准点敏感性

r04 同一冻结版完成 1,633 帧。完整模式开发组A 18/19、三点弯 4/15、验证组C原点位及亮区点位均 17/20，总计 39/54（验证组C仅计一次）。三点弯第 248 帧误差 124.95 px，整体验收未通过。仅顶点吸附消融分别 18/19、10/15、18/20，后续应在开发样例区分参考配准、远峰选择及尾段延伸的作用。

开发组A、验证组C各 200 次标注帧受测扰动的成对尖端最大漂移均为 0 px，联合状态稳定。验证组C全 562 帧直接替换原点与亮区点时，有 4 帧端点变化，第 494 帧相差 4 px。弱间隙 216/216，新增材料边缘阴性零误报，全阴性 0/468。验证组C和三点弯继续作为验证数据。

[开发总报告](../evidence/v5_9/REPORT.md) · [失败图及分支曲线](../evidence/v5_9/FAILURES_AUDIT.md) · [三组视频与逐帧图册](../output/experiments/v59_converged_r04/difference_views/index.html) · [逐帧长度](../output/experiments/v59_converged_r04/crack_lengths.csv)

[V5.8 开发总报告（r01–r07）](../evidence/v5_8/REPORT.md) 汇总三组实验、消融、亮区点位复核与逐帧证据。r04 为三组同版本结果，r05、r06、r07 的复验范围见报告首表。

## V5.8 验证组C亮材料带与基准点复核

2026-11-20。按用户红框重新验证验证组C 562 帧。r07 同时检查参考和当前图 P1/P2 的 9×9 亮度，2248 次名义点位检查全部通过。full 在 20 个标注帧上联合通过 8 帧，严重误差 5 帧，未达 17/20、严重误差为零的验收门。第 335 帧误差 0.30 px；第 345、363、456、469、480 帧桥接至上边界附近。200 次受限扰动的最大成对尖端漂移为 278.98 px。保留 r06 行亮度误裁剪的对照。验证组C为已暴露验证组。

[开发报告](../evidence/v5_8_bright/REPORT.md) · [失败分析](../evidence/v5_8_bright/FAILURES_AUDIT.md) · [视频与图册](../output/experiments/v58_material_group_c_r07/visuals/index.html)

## V5.8 分支内谷底爬升、桥接与同步基准点验证

2026-11-20。r04 在合成与开发组A上开发并冻结，依次单次验证三点弯、验证组C。本轮未通过。开发组A联合 17/19，三点弯 9/15，验证组C 0/20，总计 26/54，对照 V5.7 为 42/54。三点弯第 248 帧误差从 111.20 降至 3.02 px，第 215、407 帧仍为 40.91、21.09 px。三点弯和验证组C分别达到 4.35 和 8.70 FPS。验证组C 20/20 可见帧误差均超过 100 px，前缘向右偏移 131–136 px。第 221 帧跟上了真裂纹上方的背景暗带。下一轮应在开发图检查前缘定位与光学尺度，继续保持验证组隔离。

r04 和桥接条件修正版 r05 的全合成阴性误报均为 0/432，弱带 216/216。各版分别完成 374 次同步坐标输入测试，包含同步平移 ±10/±20 px 和点距缩放 ±20%，所测开发样例中尖端最大漂移 0 px，联合命中维持。r04 前向桥接仍继承首末列和最短长度判定。r05 清除这三项附加判定并显式屏蔽参考静态暗线，仅运行合成与开发组A，后者联合 17/19，551 帧中发布桥接 16 次。截至 r05，两验证组仅有 r04 的结果。

[r04 全组冻结报告](../output/experiments/v58_valley_bridge_20261120_r04/REPORT.md) · [失败帧专项分析](../evidence/v5_8/FAILURES_AUDIT.md) · [r05 修正复验](../evidence/v5_8/STRICT_DEV.md) · [r04 逐帧图册与视频](../output/experiments/v58_valley_bridge_20261120_r04/difference_views/index.html) · [r04 逐帧长度](../output/experiments/v58_valley_bridge_20261120_r04/crack_lengths.csv)


## V5.7 V5.4 基座上的独立入口 DP 与法向桥接

2026-11-20。r03 在合成与开发组A上开发，冻结后依次运行三点弯、验证组C。54 个可见人工端点均有输出，尖端与路径联合命中 42/54，V5.4 为 43/54。开发组A 18/19，验证组C 17/20，三点弯 7/15。三组的前缘与参考配准状态、平移在 1,633 帧上与 V5.4 一致，实测标记中心均在右侧搜索走廊外。开发组A 299 为 0.44 px，验证组C 221 为 7.43 px。阴性误报 0/432，弱带严格通过 216/216。

三点弯 215 仍选中下方近口峰，误差 85.76 px。第 248 帧误差 111.20 px，是本轮唯一超过 100 px 的可见标注帧。三组真实序列均未选用前向桥接；三点弯另有 3 帧选用了同分支下游峰。三点弯与验证组C的全序列速度分别为 1.94 和 3.80 FPS，均低于 4 FPS。保留 V5.4 比较基线，本轮未通过验收。1,633 帧均有四栏图、差分图与视频，1,585 帧输出了有效折线弧长。

[验证报告](../evidence/v5_7/REPORT.md) · [失败帧分析](../evidence/v5_7/FAILURES_AUDIT.md) · [三组视频与逐帧图册](../output/experiments/v57_clean_20261120_r03/difference_views/index.html) · [逐帧裂纹长度](../output/experiments/v57_clean_20261120_r03/crack_lengths.csv)


## V5.6 基准点解耦与多分支独立 DP

2026-11-20。合成及开发组A开发，r04 冻结后依次单次运行三点弯、验证组C。1,633 帧完整模式中 537 帧输出有效折线长度。在 54 帧可见标注中，尖端命中 18 帧、路径与尖端联合命中 17 帧。开发组A联合 17/19，三点弯 0/15，验证组C 0/20。V5.4 同口径联合 43/54。本轮未通过验收，保留 V5.4 作为比较基线。

在开发组A 20 帧与 14 个合成样例的输入基准点扰动试验中，V5.6 的有效尖端在 ±10 和 ±20 px 下最大漂移均为 0 px。开发组A在 ±10 px 下有 6/240 次扰动改变了根部或中间路径。三点弯 477/520 帧、验证组C 562/562 帧在多分支 DP 建表前被开口拓扑门拒绝。三点弯第 144、178、215 帧的 P2 暗标记进入了壁面计票。验证组C四个重点帧中，接触 P1 中心的连通体也参与计票，单独重算该门无法验证后续尖端是否正确。下一轮应在开发数据中区分缺口本体、独立暗标记与相连暗部，再测试其对判定的影响。

[开发报告](../evidence/v5_6/REPORT.md) · [失败帧分析](../evidence/v5_6/FAILURES_AUDIT.md) · [逐帧图册及视频](../output/experiments/v56_decoupled_20261120_r04/difference_views/index.html) · [逐帧弧长与投影](../output/experiments/v56_decoupled_20261120_r04/crack_lengths.csv) · [基准点扰动](../output/experiments/v56_decoupled_20261120_r04/jitter_summary.csv)


## V5.5 细脊差分提权与同枝下游峰验证

2026-11-19。以合成和开发组A开发，r02 冻结后依次验证三点弯、验证组C。完整模式下，54 帧可见尖端中联合命中 42 帧，V5.4 为 43 帧。开发组A 18/19，三点弯 8/15，验证组C 16/20。超过 100 px 的误差为零。本轮未通过验收。

三点弯第 215 帧从旧尖端到正确候选的 37 列中心差分均强，但仅 5 列满足持续细脊、4 列实际提权，合并支撑 16/37。保留旧尖端，误差 40.41 px。验证组C第 221 帧在五列延伸中有三列融合支撑，无高置信细脊，仍通过同枝替换，误差从 7.43 增至 12.39 px。新增双段阳性 36/36，原有合成阴性误报 0/360，新增无裂纹弱尾阴性误报 0/36。全序列完成 1,633 帧预测和制图。

[验证报告](../evidence/v5_5/REPORT.md) · [失败帧分析](../evidence/v5_5/FAILURES_AUDIT.md) · [逐帧图册及视频](../output/experiments/v55_ridge_20261119_r02/difference_views/index.html) · [逐帧裂纹长度](../output/experiments/v55_ridge_20261119_r02/crack_lengths.csv)


## V5.4 谷底爬升与近口终点复核

2026-11-19。合成与开发组A开发后冻结 r03，按顺序验证三点弯、验证组C。完整模式在 54 帧可见尖端上命中 43 帧，尖端和路径联合合格从 V5.3 的 35/54 恢复至 43/54，与 V5.2 持平。开发组A 18/19、三点弯 8/15、验证组C 17/20，严重误差为零。三点弯目标为 9/15，本轮未通过。

取消 V5.3 全局红弧扣分后，三点弯原先退化的 8 帧均恢复。三点弯 520 帧有 67 帧选用远端峰。第 215 帧离人工端点 2.08 px 的候选通过各项准入，离线复核其路径也合格；累计分排序选中较短的分支，实际误差 40.41 px。第 144、178 帧仍失配。合成阴性误报 0/360，弱带 216/216、零错接，竞争唇缘端点 36/36、路径联合 27/36。1,633 帧均有四栏图与差分，1,589 帧输出有效弧长。排除组X排除，标注仅用于离线评分。

[验证报告](../evidence/v5_4/REPORT.md) · [失败与退化分析](../evidence/v5_4/FAILURES_AUDIT.md) · [各组视频与逐帧图册](../output/experiments/v54_valley_20261119_r03/difference_views/index.html) · [裂纹长度 CSV](../output/experiments/v54_valley_20261119_r03/crack_lengths.csv)


## V5.3 远端局部峰与近缺口红弧验证

2026-11-19。r03 冻结后依次验证三点弯、验证组C。完整模式共 43/54 个可见尖端在 10 px 内，路径联合命中从 V5.2 的 43/54 降到 35/54。开发组A 18/19、验证组C 17/20 联合命中均持平，三点弯从 8/15 降到 0/15。本轮未达到生产验收条件。

三点弯第 215 帧存在离标注 2.08 px 的局部峰，远段净增量和支撑比例未达门槛。只修复候选检索时，三点弯保留 8/15 联合命中。加入红弧抑制后，这 8 帧的近口路径均偏离。合成竞争唇缘的联合命中由 0/36 升至 27/36，全部合成阴性误报 0/360。完整模式在全部 1633 帧上选用远端替代峰 0 次。

[验证报告](../evidence/v5_3/REPORT.md) · [失败帧专项分析](../evidence/v5_3/FAILURES_AUDIT.md) · [逐帧图与视频](../output/experiments/v53_local_peaks_20261119_r03/difference_views/index.html) · [逐帧长度](../output/experiments/v53_local_peaks_20261119_r03/crack_lengths.csv)


## V5.2 宽团块抑制、远端裁决与逐帧长度

2026-11-19。仅使用合成和开发组A开发，r03 冻结后按顺序验证三点弯、验证组C。三组完整模式联合命中 18/19、8/15、17/20，合计 43/54；严重误差为零。三点弯未达 11/15 验收门。三个目标帧的远端候选均位于搜索区左边界，净增量不足。弱带 216/216，原有阴性 0/288 误报，新增纯团块阴性 0/36。合成竞争分支可命中远端尖端，但仍有从错误唇缘跨接的路径。

每帧 CSV、视频和四栏图均给出缺口根点至识别尖端的路径弧长，以及尖端相对当帧锚点中点的右法向投影，单位为原图 px。检测无结果时留空。长度为算法测量值，尖端命中仍需结合整条路径检查。排除组X排除，标注仅作离线对比。

[开发报告](../evidence/v5_2/REPORT.md) · [失败帧分析](../evidence/v5_2/FAILURES_AUDIT.md) · [逐帧长度 CSV](../output/experiments/v52_distal_20261119_r03/crack_lengths.csv) · [视频与逐帧对比](../output/experiments/v52_distal_20261119_r03/difference_views/index.html)


## V5.1 全局自由终点 DP 修正

2026-11-19。先在合成探针和开发组A标定，冻结 r08 后依次验证三点弯、验证组C。60 个标注帧中有 54 个可见尖端，完整模式联合命中 43/54，严重误差为零。开发组A 18/19、中位 2.95 px；三点弯 8/15、中位 8.67 px；验证组C 17/20、中位 2.31 px。三点弯门槛为 12/15，本版未通过整体生产验收。

近口强差分、可恢复负分与连续强灰度谷判别使开发组A首帧正确输出空路径，验证组C首帧保留预存裂纹（误差 1.26 px）。合成弱带 216/216、错接零，原有阴性 0/216 误报。纯灰度验证组C再无水平跨度超过 1000 px 的路径，标注第 195 帧仍有 106 px 误差。三点弯第 215 帧人工端点已可达，但净分排序仍让路径提前约 85 px。后续以合成、开发组A等开发组开展新实验，验证组仅作冻结对照。排除组X排除，人工标注只作比较。

[开发与消融报告](../evidence/v5_1/REPORT.md) · [失败帧与累计得分曲线](../evidence/v5_1/FAILURES_AUDIT.md) · [三组视频、逐帧参考与差分](../output/experiments/v51_dp_fix_20261119_r08/difference_views/index.html)


## V4.2 止血与 V5.0 全局自由终点验证

2026-11-19。两版按顺序完成。开发使用合成探针和开发组A，三点弯及验证组C各自只跑冻结版本。排除组X排除，人工标注只用于事后评分。下表为完整模式下可见尖端与路径的联合命中数。

| 版本 | 开发组A | 三点弯 | 验证组C | >100 px 严重误差 |
|---|---:|---:|---:|---:|
| V4.2 | 19/19 | 10/15 | 10/20 | 0 |
| V5.0 | 18/19 | 0/15 | 14/20 | 13 |

V4.2 恢复三点弯的弯曲下唇，仍未恢复验证组C V3.6 的 13/20。V5.0 采用带斜率状态的单遍全局动态规划，冻结前开发组A达标，三点弯的累计负分下限使后段不可达，验证组C第 1 帧在同图参考下沿原图背景过冲约 2070 px。两版均未通过整体生产验收。后续以真实弯曲下唇的局部失分、同图参考的长连通纹理为独立开发探针。实测验证组只作冻结对照。

[V4.2 报告](../evidence/v4_2/REPORT.md) · [V4.2 失败帧](../evidence/v4_2/FAILURES_AUDIT.md) · [V4.2 逐帧浏览](../output/experiments/v42_hotfix_20261119_r03/difference_views/index.html)

[V5.0 报告](../evidence/v5_0/REPORT.md) · [V5.0 失败帧与得分曲线](../evidence/v5_0/FAILURES_AUDIT.md) · [V5.0 逐帧浏览](../output/experiments/v50_global_dp_20261119_r06/difference_views/index.html)


## V4.1 提纯融合

2026-11-19。研究版完成，生产验收未通过。先在合成与开发组A验收，再冻结规则运行三点弯与验证组C。开发组A联合 19/19、中位 2.54 px；三点弯 1/15、中位 181.84 px，11 帧严重提前；验证组C 8/20、中位 10.46 px。三点弯 503 的首个损失是近口跨唇判据提前截断，最终误差 285.10 px。三种合成渐隐/塑性区/形变划痕阳性分别 33/36、33/36、28/36，全部阴性 0/216 误报。保留 V3.6 为研究对照。

[开发与消融报告](../evidence/v4_1/REPORT.md) · [失败与受损帧](../evidence/v4_1/FAILURES_AUDIT.md) · [视频、逐帧图及差分](../output/experiments/v41_fusion_20261119_r07/difference_views/index.html)。


## V4.0 双轨独立追踪与末端精修

2026-11-19。冻结研究版，生产验收未通过。开发组A、三点弯、验证组C的 Hit@5 分别为 13/19、4/15、6/20；Hit@10 和联合命中分别为 19/19、9/15、9/20，严重误差均为零。三点弯 144 的增量候选被闭环检查淘汰，验证组C 469 在增量轨认证后向右过冲 54.7 px，验证组C 363 误差降至 0.84 px。三档曝光合计 216 个合成阴性样例无误报，弱带接受的 33 次重连无错接。保留 V3.6 作为对照基线。后续视频和逐帧图继续提供固定参考对应位置、当前灰度、识别叠图和有符号差分，并单独导出差分 PNG。

[开发与消融报告](../evidence/v4_0/REPORT.md) · [失败与受损帧分析](../evidence/v4_0/FAILURES_AUDIT.md) · [逐帧图册与视频](../output/experiments/v40_decoupled_20261119_r06/difference_views/index.html)。


## V3.6 缺口补种、静态淘汰与划痕回溯

2026-11-19。PRODUCTION_NO_GO。54 张可见标注的尖端和联合命中均从 40 提升至 42，严重误差为零。开发组A 19/19，三点弯 10/15，验证组C 13/20。验证组C 38 和 335 恢复命中，验证组C 363 的提前截断略有加重。三点弯 144 静态过冲得到纠正，但新路径停得过早。三种曝光的合成弱带错接均为零，暗曝光下另有两例路径覆盖下降。[开发报告](../evidence/v3_6/REPORT.md) · [失败与受损分析](../evidence/v3_6/FAILURES_AUDIT.md) · [四栏逐帧图册与差分 PNG](../output/experiments/v36_patch_20261119_r02/difference_views/index.html)。

## V3.5 双通道追踪与形变划痕复核

2026-11-19。PRODUCTION_NO_GO。开发组A尖端和联合命中均为 19/19，三点弯 10/15，验证组C 11/20。开发组A 504 误差由 14.18 降至 1.17 px，验证组C 335 由 30.64 降至 23.40 px。三种曝光的合成弱带错接归零，三点弯和验证组C仍低于验收门。后续视频及逐帧图默认提供参考对应位置与有符号差分。[开发报告](../evidence/v3_5/REPORT.md) · [失败帧分析](../evidence/v3_5/FAILURES_AUDIT.md) · [四栏图册、视频与每帧差分](../output/experiments/v35_dual_20261119_r03/difference_views/index.html)。

## V3.4 参考图解锁与尖端验证

三组全序列共 1,633 帧可按固定参考原图、当前灰度、路径叠图和有符号差分四列复查。每帧另有原像素尺寸的裂纹局部差分 PNG，图册默认定位到验证组C第 335 帧。[参考差分图册与视频](../output/experiments/v34_reference_20261119_r03/difference_views/index.html)。

2026-11-19。PRODUCTION_NO_GO。冻结版在 54 张可见标注上尖端和联合命中均为 39/54，严重误差 0。开发组A 18/19，三点弯 10/15，验证组C 11/20。开发组A 366 和三点弯 413 恢复命中，验证组C 528 新增过冲。标准曝光下含参考模式的跨唇豁免引入 2/24 次错误重连，纯灰度仍为 0/22。下一轮优先在独立合成弱带上复查跨唇豁免，再验证已有裂纹与参考图静态背景的区分。[开发与消融报告](../evidence/v3_4/REPORT.md) · [失败与受损帧分析](../evidence/v3_4/FAILURES_AUDIT.md) · [固定参考与逐帧图册](../output/experiments/v34_reference_20261119_r03/fixed_views/index.html)。

## V3.3 尖端精度验证

2026-11-19。PRODUCTION_NO_GO。54 帧可见标注中尖端命中 38 帧、联合命中 38 帧、严重误差 0 帧。[开发报告](../evidence/v3_3/REPORT.md) · [失败帧专项](../evidence/v3_3/FAILURES_AUDIT.md)。

## V3.2 精度与普适性

2026-11-19。PRODUCTION_NO_GO。开发组A、三点弯、验证组C的尖端命中分别为 17/19、9/15、12/20，联合命中分别为 17/19、1/15、12/20。三点弯同唇门误拒正确下唇；验证组C 69 提前，335 仍转向旁侧暗线。[完整报告](../evidence/v3_2/REPORT.md) · [逐帧查看与视频](../output/experiments/v32_precision_20261119_r03/index.html)。

## V3.1 弱裂纹追踪

2026-11-19。本轮限开发组A开发、三点弯冻结规则对照、验证组C一次冻结回归。最终版在 54 张可见标注上的尖端 / 联合命中为开发组A 16 / 16（共 19）、三点弯 5 / 5（共 15）、验证组C 10 / 9（共 20），严重误差均为零。三点弯 215 跨带成功，但弱尾过冲仍造成回退。生产验收未通过。[开发报告](../evidence/v3_1/REPORT.md) · [1,633 帧图册](../output/experiments/v31_weak_crack_20261119_r04/index.html) · [复现入口](../research/notch_identity_v31/README.md)。


## 原图灰度 V3 阶段消融

2026-11-18。三组 1,633 帧已交付逐帧图与完整视频。新版在 54 张可见标注上的尖端/联合命中分别为 GROUP_A 14/14（共 19），三点弯 10/1（共 15），验证组C 13/13（共 20）。验证组C冻结回归改善，GROUP_A 四个原命中帧提前终止，三点弯 215 仍从上唇通过。生产验收未通过。合成闭合/张开轮廓负例仍有 9/24 次误报，下一步优先隔离真实下唇断带与弱尾端截断。[开发报告](../output/experiments/notch_identity_v3_20261118_r01/REPORT.md) · [逐帧图册](../output/experiments/notch_identity_v3_20261118_r01/s3t/index.html) · [源码](../research/notch_identity_v3/README.md)。


2026-11-18 · 原灰度缺口追踪 V2 r02 已完成。GROUP_A、三点弯和验证组C Hit@10 分别为16/19、10/15和6/20，路径与端点联合为16/19、1/15和6/20。三点弯仍可选错缺口唇缘，验证组C14个漏命中点均向右偏。生产验收未通过。开发采用GROUP_A和三点弯，冻结后验证组C单轮回归，标注只作离线比较。[本轮报告和图册](../output/experiments/raw_notch_trace_v2_20261118_r02/REPORT.md)。

## UCTIP-60Q完成：研究交付完整，生产验收不通过

2026-11-14，独立实现research/unified_crack_tip_60q；产物output/experiments/unified_crack_tip_60q_20261113_r01。全1633帧证据/局部对比/HTML，DEV1071帧×11模式加验证组C562帧单轮FULL，共12343条完整模式预测。三段H264视频逐帧解码通过，39项顺序重放/源图重算一致，176105个历史保护文件无改动。group_a Hit@10=0/19、有效0/19、>100px=0；three_point_bend Hit@10=3/15、有效11/15、>100px=2；group_c Hit@10=12/20、有效20/20、>100px=0。结论PRODUCTION_NO_GO，不替换旧A。

RAW覆盖好不等于路径正确。GROUP_A全551帧预算耗尽，正式null：546帧起源候选上限、545帧路径候选上限、7帧轨迹上限（有重叠），RAW/图边上限均未触发；三点弯端点候选Oracle14/15，但联合路径/端点候选只有1/15，正式端点3/15、联合0；单轨消融严重误差11/15。15项基本合成测试通过，扩展5项中静态独立暗线误输出1项失败。需隔离研究候选/轨迹膨胀与错误身份支持，不能删除多分支或直接放行Oracle。

原四模块未改；独立engine_fast批量历史查询在133真实检查点和15基本合成测试上完全一致后启用。旧结果原始来源hash保留，性能按执行后端分列。评价器无GT帧摘要读取经66原生核对；可见GT仍完整原生评价。全部源码/配置/评价器/展示规则已在验证组C新算法运行前冻结，后续不得就地修改或重新选择验证组C成绩。

本轮明确角色DEV=GROUP_A+三点弯，验证组C为冻结后已曝光固定回归；其他组不进入新算法队列，标注比较不训练，无GT参数搜索。**严格隔离失败**：预冻结误跑通用旧A检查读取验证组C图像/P（另含CT2/开发组H历史检查），新算法未据此调参但不能声称完全合规或新盲测。偏差已完整保留。Python实现，无C++；极端图邻居枚举内存保证未完成，非法P批处理入口fail-fast，物理缺口/变形真值未认证，真实阴性不足FPR=N/A。真实浏览器操作受工具URL策略阻断，只完成Node合同与图像检查。

[最终结论](../output/experiments/unified_crack_tip_60q_20261113_r01/reports/FINAL_DECISION.md) · [开发失败定位](../output/experiments/unified_crack_tip_60q_20261113_r01/reports/MEASURED_FAILURE_FINDINGS.md) · [全帧图册](../output/experiments/unified_crack_tip_60q_20261113_r01/galleries/index.html) · [三段视频/完整索引](../output/experiments/unified_crack_tip_60q_20261113_r01/DELIVERABLE_INDEX.md) · [完整性](../output/experiments/unified_crack_tip_60q_20261113_r01/reports/final_integrity.json)。所有失败/空输出保留；继续开发须新建版本，不能覆盖本轮和历史封存结果。

## 用户工具更新：P1/P2文件夹批量与三栏显示（2026-11-13）

用户明确要求改写根目录paired_p1p2_roi_easy_edit.py，已新增参考帧/文件夹/初始P1/P2配置、自然排序、中文路径、逐帧NCC和失败后继续。差分参考固定，默认以上一成功帧跟踪P点，可选固定参考匹配；单对--current兼容。每次独立run目录，三栏原图ROI/局部原图/裂纹结果、逐帧轨迹、汇总CSV及HTML翻页。参考P点低纹理拒绝；NO_TIP与ERROR不伪造路径。仅纠正到达ROI右界的stop_reason日志，检测公式不改。

4项针对性检查通过：自然排序/排除排除组X、低纹理拒绝、坏图继续与累计位移、修改前后六份轨迹逐列完全一致；run.ps1 check通过。使用原配置三点弯46.bmp→7695.bmp生成实际三栏预览，未读标签、未调参、未跑完整520帧精度验收。保留修改前源码与golden在output/tests/paired_folder_20261113_r01；旧research冻结版本/生产未改。

[用法](PAIRED_P1P2_BATCH_USAGE.md) · [实际单帧预览](../output/tests/paired_folder_20261113_r01/real_pair/run_20261113_153841_893020/index.html)。

## ROI几何单因素实验完成：工程通过，B/C均NO_GO（2026-11-13）

按GrayRef_GROUP_A_Only_ROI_Causal_Experiment_Agent_Prompt.md，只改变候选/路径搜索mask：A原ROI、B静态紧凑带、C无GT动态多走廊。GROUP_A551开发先封存评分，再对验证组C562/三点弯520锁后回归。共1633帧、4899真实预测、8165张PNG、1637个HTML页面、三段全帧视频；A原生结果/候选图1633帧完全一致，30份原BMP重算差分误差0，30次重复检测一致，源码/旧受保护文件未改。

B/C均GEOMETRY_HARMFUL，NO_GO，生产不批准。可见尖端10px与路径联合：GROUP_A A/B/C为0/1/0（分母19）；验证组C均0/20、三点弯均0/15。B的GROUP_A451误差0.983px，但GROUP_A113原合格路径丢失：73节点全保留，新增较近暗谷点改变冻结一对一连接。C另损失验证组C232（168原路径节点中裁23个）与三点弯1（原15节点及相邻连接仍在，但扩成17点片段后未进入路径预算）。验证组CB候选池16→18/20，未转成尖端输出；C16→16包含一增一失。验证组C266 B/C输出无标签，不能判正确。

B面积约剩30.5%；C在GROUP_A/验证组C/三点弯分别剩51.60%/29.40%/63.05%。三点弯邻接边与预算未访问尾部反而增加，不能称普遍减少竞争。全序列ROI_LIMITED B为1/1/0，C为1/50/4。GT_EXCLUDED全0仅指人工尖端点；根目录自动原因报告的“正确候选被裁剪无案例”标题过宽，final_delivery复核报告已明确更正，原封存文件保留不改。

代码research/grayref_roi_geometry_ablation/，只读交付辅助research/grayref_roi_geometry_support/。本轮CT2/开发组H/CT3/排除组X不进入队列；标注仅比较不训练；验证不调参，无新盲测，FPR=N/A，物理起源未认证。下一项仅建议独立研究原A不同终止跨度保留，不能自动按本轮标签调ROI宽度或发布。

[复核报告](../output/experiments/grayref_roi_geometry_group_a_only_20261113_r01/final_delivery/REPORT.md) · [原因与反例](../output/experiments/grayref_roi_geometry_group_a_only_20261113_r01/final_delivery/ROI_CAUSAL_FINDINGS.md) · [视频与全帧入口](../output/experiments/grayref_roi_geometry_group_a_only_20261113_r01/final_delivery/index.html) · [原始全帧图册](../output/experiments/grayref_roi_geometry_group_a_only_20261113_r01/galleries/index.html) · [复现](../research/grayref_roi_geometry_ablation/README.md) · [最终补充封存](../output/experiments/grayref_roi_geometry_group_a_only_20261113_r01/supplemental_delivery_seal.json)。

## GrayRef 简化原型：全量工程通过，准确率 NO_GO（2026-11-13）

用户任务书 `GrayRef_Simplified_Evidence_Path_Tip_FullFrame_Visualization_Agent_Prompt.md` 明确授权独立简化路线，取代上一轮“下一项仅连接门审计”的工作范围限制，但不推翻旧审计事实。源码 `research/grayref_simplified_evidence_v0/`，输出 `output/experiments/grayref_simplified_evidence_v0_20261113_r01/`，只读交付辅助源码 `research/grayref_simplified_evidence_support/`。九模式全2647帧真实完成，默认 C_FUSION_RAW；原始/轻滤波暗谷、可信参考、有限断续图、独立停止，无时间/试件名/帧号/GT输入。开发先封存评分，再固定规则验证；没有调参或模式挑选。

工程完整性通过：2647份原始3D曲面、有符号差分、数值及预测全部核验，50293张逐帧PNG，12份原始BMP/P随机复算灰度和差分最大误差0。故意缺图/坏NPZ能报错，隔离补图SHA一致。六组视频全部完整解码共2647帧；120张人工标签对比单独标为OFFLINE_LABEL_OVERLAY。旧V2全部39734文件、A/V1受保护工件未变。参考2232帧至少有一组两侧共同通过的纹理窗口，不能称全ROI物理可信；开发组H0，三点弯平均可信面积3.70%。参考失败条件表的186808个windows按单侧计数，开发组H1227个单侧通过不等于存在两侧共同通过的局部区块。全部单侧可信判断、2647张灰度PNG和7941张暗谷PNG已从数值精确复核。融合参考相比当前灰度没有增加10px命中。

算法 NO_GO、生产 NO：开发公开3/76，10px和联合均2/76，>100和>500均1；GROUP_A0/19、CT2 0/20、CT3 0/19、开发组H2/18。曝光验证0/35且公开0/35，不能解释为安全成功。V1命中12/76、5/35，V2_COMBINED命中4/76、4/35（联合4/76、3/35）；仅冻结结果/完整trace校验回放，未重跑旧检测器。开发组H317跟随上方圆形标记边缘，误差565.358px，仍满足停止后材料和负证据条件，说明身份归属未解决。冻结后2px噪点链反例也有暂定尖端；真实FPR=N/A。

只读逐层审计：111可见帧的原始峰/保留节点均覆盖至少80%标注路径，但不等于已构成正确路径。开发首败54图路径/预算、14停止/公开歧义、6ROI外、2联合命中。完整原生路线重放进一步证明7张开发帧的合格路径被不合格的包含关系keeper压制，最终无合格替代路径；这只是离线路径损失，未对被删路线重新认证尖端，不计为新增准确率。唯一下一步建议：只测试不同终止跨度独立保留，其余证据、连接边界、排名权重及停止规则保持固定。不得据验证改参、自动放宽拒绝或启动整套新算法。

[最终原因与结果](../output/experiments/grayref_simplified_evidence_v0_20261113_r01/FINAL_FINDINGS.md) · [2647帧图册](../output/experiments/grayref_simplified_evidence_v0_20261113_r01/galleries/index.html) · [六组视频](../output/experiments/grayref_simplified_evidence_v0_20261113_r01/videos/index.html) · [独立人工对比](../output/experiments/grayref_simplified_evidence_v0_20261113_r01/offline_label_overlays/index.html) · [完整复现](../research/grayref_simplified_evidence_support/README.md)。排除组X排除，标签仅比较不训练，验证组C/三点弯仅已曝光回归；CT3原TXT缺失、历史CSV核验及6个ROI外尖端分母保留，无新盲测。

## GrayRef V2候选Oracle审计：下一项只研究连接门保真性，不开发V3

2026-11-13，完成`GrayRef_V2_Candidate_Oracle_Stage_Audit_Agent_Prompt.md`诊断。输出`output/diagnostics/grayref_v2_candidate_oracle_audit_r01/`，审计源码在其audit_source/。仅复用2647全序列清单；150输入AUDIT_OFF/ON各五模式（111可见、9人工未知、30未标注），原输出、候选顺序、路径与八数组一致，原V2全39734文件无变化。41616条原始种子记录、1430条原完整假设，补齐真实短程及NMS keeper血缘；GT在全部候选哈希冻结后单独join。

COMBINED的GROUP_A19/19和CT2 20/20都有近GT种子、NMS keeper及可用短轨迹，但通过原短程门的近GT轨迹均0；主要首败是connection<0.5。所有原种子无GT诊断延伸中，GROUP_A14帧、CT2 7帧有被连接门拒绝但可贴近标注路径与尖端的保留种子，原最终池无联合成功替代；这些额外轨迹绝不计入原Oracle或算法准确率。GROUP_A/CT2未发现近GT NMS被删种子联合成功但keeper不成功的帧，不能把NMS_DUPLICATE数量当路径损失。

开发组H18张人工路径均在完整ROI，却距固定起源带右边51.75–57.57px；只能证明标注可见段不相交，不能证明真实物理起源错或无不可见连接段。所有18张有坐标/全几何/局部图，物理缺口与P语义保持UNRESOLVED。

原完整路径+原生尖端联合Oracle/实际：开发7/76 vs4/76，仅CT3；曝光回归13/35 vs3/35（验证组C11/3、三点弯2/0）。端点-only与联合分开。固定候选聚类主规则开发+2联合却新增9个>100px错误；严格敏感性规则仍新增1个>100px，不支持归并后放行。原短程排名公式无直接M2参考项，固定轨迹参考off/on完全相同；M2影响更早像素选择，不能伪造路径参考加分实验。

主建议分支B：仅允许下一轮隔离研究回溯连接门保真性与物理缺口连接语义；不是立即删门/降0.5、按组调参或开发整套V3。先独立确认缺口内部不可采样、不可见连接、真实断连等语义，再考虑单点修复并全开发组复测。排除组X排除、标注不训练、验证组C/三点弯不选参、无真实FPR/新盲测。

[执行报告](../output/diagnostics/grayref_v2_candidate_oracle_audit_r01/AUDIT_EXECUTIVE_REPORT.md) · [决策矩阵](../output/diagnostics/grayref_v2_candidate_oracle_audit_r01/decision_matrix.md) · [全部关键表/复现](../output/diagnostics/grayref_v2_candidate_oracle_audit_r01/DELIVERABLE_INDEX.md) · [图册](../output/diagnostics/grayref_v2_candidate_oracle_audit_r01/galleries/index.html)。

## P1/P2 GrayRef V2：全量开发与移植完成，跨组准确率不通过

2026-11-12，按`P1P2_GrayRef_V2_Strict_Development_Agent_Prompt.md`完成真实单帧Python和独立C++17/OpenCV实现。活动源码`research/p1p2_grayref_v2/`，产物`output/experiments/p1p2_grayref_v2_20261112_r01/`。M1起源多候选/M2分级参考独立开关，另设NUMERIC_CONTROL隔离数值/安全变化、TERMINAL隔离停止竞争；没有M3或时间增强。参数及Python源码在评分前锁定，只做r01，未根据已曝光验证调整算法。

四开发组1565帧、验证组1082帧完整运行；V1原六档全帧轨迹与旧结果完全一致。默认COMBINED开发命中10px=4/76（V1=12/76），三个非CT3组仍0；公开>100px=26（V1=31），但有效输出37（V1=50），原始候选>100=57、>500=37，不能把拒绝称为安全成功。ORIGIN_ONLY/REF_ONLY分别11/76、8/76且严重尾部扩大；TERMINAL5/76不可事后替换默认。合成旧划痕阴性3/5模式误输出，实际FPR=N/A。CT3原ROI外6帧保留；独立原始TXT缺失，历史坐标CSV及帧映射证据明确保留。

已曝光验证COMBINED4/35：验证组C4/20、三点弯0/15；35张中仅6有效输出，29不确定。M2-only的13/35只是固定消融记录，不作为新模式选择。D原始起源y2282和y2351均生成，默认最终UNCERTAIN；不同x起始的重合路径可能形成虚假歧义，暗线连续性仍不能认证裂纹身份。

C++全2783输入（2647全帧+136固定ABCD/哨兵/扰动）×5模式、119669项逐层检查通过。第一次移植三点弯512帧4个数组层相差1float32 ULP（1.52587890625e-5）超固定容差1e-5，但离散路径/端点全一致；失败源码、DLL、全部结果与日志在native_port_attempt1/保留。局部四控制确认高斯加法顺序原因，C++统一遵循冻结Python规范后重新全量核对；没改Python算法/阈值/容差，不是按验证精度修复模型。旧V1自身移植差异仍是历史事实，不倒推旧版本通过。

交付六段完整视频、2647张每帧8面板对比、111张可见尖端局部图、13张ABCD/哨兵卡、133张参考证据图和全帧质量查看器；无输出和失败帧未删除。原生产A、冻结V1、旧结果、标签与外部原图保持不变。排除组X排除，标注仅推理后对比，不训练/拟合；验证组C/三点弯仅曝光回归，无新盲测。工程交付不等于算法通过，生产批准NO。

[开发报告](../output/experiments/p1p2_grayref_v2_20261112_r01/V2_DEVELOPMENT_REPORT.md) · [消融](../output/experiments/p1p2_grayref_v2_20261112_r01/V2_ABLATION_REPORT.md) · [数值核对](../output/experiments/p1p2_grayref_v2_20261112_r01/V2_NUMERIC_PARITY_REPORT.md) · [六组视频及全帧图](../output/experiments/p1p2_grayref_v2_20261112_r01/galleries/index.html) · [交付索引](../output/experiments/p1p2_grayref_v2_20261112_r01/DELIVERABLE_INDEX.md) · [最终完整性](../output/experiments/p1p2_grayref_v2_20261112_r01/final_integrity.json)。

## 验证组C同一BMP：计算失效链已复现，物理与点位语义仍有证据缺口

2026-11-12，按`group_c_Same_BMP_V1_Root_Cause_Agent_Prompt.md`做冻结故障审计。源码在`research/group_c_same_bmp_v1/`，证据在`output/diagnostics/group_c_same_bmp_root_cause_v1_20261112_r01/`。原图字节与解码数组、原始TXT、frame237/tracking236及冻结源2e2e5e…baf6均核验。该BMP不是既有20张标注帧之一，(2423,2344)仅作事后近似回归锚点。

ABCD原生joint T10分别(2423,2344)/(2424,2344)/(2423,2344)/(2255,2282)，A与旧黄金、D与正式序列六模式逐列复现。D首列x2255，current偏好的y2351处valley27.3987但newdark−5.2426，被joint否决；joint唯一非零胜者y2282仅产生一次观测，随后21列缺失。69px纵向差超出局部半宽7px恢复范围。不是D全零argmax，也不是gap_limit本身解释了根因。

诊断控制：几何A/位移D仍(2423,2344)，几何D/位移A无端点，几何D/位移D复现错误首锁；不能声称仅换参考就能修好。纯AA/DD的13个数组和全部轨迹与原生精确一致。114次原生Python main、4次明确标记的反事实main，每次6模式；另4次C++辅助对照。101个预定义扰动完整保留，A→D采样插值首跳t=.7、t=.8无输出，不细搜参数。

4个额外已标注可见帧：232复现相近错首锁；38/7联合差分/排序不足无输出；1因R=C增量全零默认首候选。它们不是整组比例。独立材料6窗仅2窗NCC≥.8，局部支持D位移不一致；原始点击/点语义记录与物理配准真值缺失，保持UNRESOLVED。未改V1、生产、旧结果，未开发V2；验证组C仅故障审计，不用于选参，标注仅推理后比较，排除组X排除。

[中文报告](../output/diagnostics/group_c_same_bmp_root_cause_v1_20261112_r01/ROOT_CAUSE_REPORT.md) · [逐列查看器](../output/diagnostics/group_c_same_bmp_root_cause_v1_20261112_r01/trace_audit_A_B_C_D.html) · [证据视频](../output/diagnostics/group_c_same_bmp_root_cause_v1_20261112_r01/root_cause_walkthrough.mp4) · [最终完整性](../output/diagnostics/group_c_same_bmp_root_cause_v1_20261112_r01/final_integrity.json)。这轮交付是故障归因，不是算法修复或精度验收通过。

## P1/P2-GrayRef V1：完整回放已交付，跨组精度与全域移植一致性未通过

2026-11-12，按用户提供完整冻结包与`Agent_Development_Prompt.md`执行。独立研究代码`research/p1p2_grayref_v1/`，结果`output/runs/p1p2_grayref_v1_20261112_r01/`。Python源码SHA严格匹配2e2e5e…baf6，六档BMP完整回归一致，原检测源码diff为空。全1565开发帧与1082验证帧、joint/current×T8/10/12，Python/C++各15882结果。没有合并旧A/R05G评分或改变V1参数。

固定joint T10开发可见76：暂定覆盖50，3/5/10px=6/8/12，>100/500px=31/18；12个10px命中全来自CT3。验证35可见：覆盖20，3/5/10px=0/2/5，>100/500px=4/0；验证组C0/20、三点弯5/15命中10px。开发4/验证5个UNCERTAIN单独保留。CT3六个GT在严格ROI外；GROUP_A/开发组H多在到达GT前停止，CT2联合全序列无端点；验证组C起始位置证据不匹配，current T10为11/20但不得据验证切换默认模式。只有暂定端点，无独立正式observed，不能称全拒绝安全。

开发9390组端点和逐列选择完全一致，640个选帧数组逐像素一致，锁后才进入验证。验证新增15个current模式端点差异、126条轨迹差异；首次预测y差<1e-9跨过floor/ceil边界，最终最大差209.02px。全部960个选帧中间数组一致，joint三档所有端点一致；全模式15867/15882端点一致不能替代严格parity通过。保留锁定源码与DLL，不使用验证修补SVD/epsilon。新DLL58e073…f1与生产分开。

两验证组首帧原Python运行完成后遇日志字段重名中断，只修改记录层并复用完成输出；原锁、修复前后驱动SHA、首帧输出哈希与两套日志保留。检测参数及评分规则未变，标签均在推理完成后读取。排除组X0、标注不训练、验证不调参。六组视频全部解码检查，2647张参考/当前/轨迹三联图、120详细卡片、4哨兵放大图已生成。性能六模式native P95约10.55–219.66ms（7950X，并发负载），不是目标i7验收。

结论KEEP_A：工程可运行，但跨组质量及完整移植验收失败；V2仅提供最小研究建议，未实施。详细见[本轮报告](../output/runs/p1p2_grayref_v1_20261112_r01/development_report.md)、[首次分歧](../output/runs/p1p2_grayref_v1_20261112_r01/tables/first_divergence_audit.csv)、[视频图册](../output/runs/p1p2_grayref_v1_20261112_r01/galleries/index.html)、[完整性](../output/runs/p1p2_grayref_v1_20261112_r01/final_integrity.json)。A55a0与历史发布A1c742不混用，旧R05H结果保留。

## R05H：全流程已执行，精度与错锁安全未达标

源码 `research/uctt_r05h/`，输出 `output/runs/uctt_r05h_20261112_r01/`。四开发组1565帧×4消融、两验证组1082帧×FULL，共7342次真实C++调用。源码/规则/DLL先冻结，验证一次性只读，无标签训练、参数拟合、排除组X图像或标签读取。已接通弱起源、物理缺口身份、STOP竞争、双侧材料参考、当前末端精扫、状态输出与过去可信材料导航，非全拒绝占位。

开发76可见：正式36，3/5/10px命中1/3/7，正式>100/500px=19/0；工作命中8/12/17，>100/500px=33/1。验证35可见：正式12、正式10px4、工作10px11；验证组C4/20和10/20，三点弯0/15和1/15。UNCERTAIN开发4、验证5单独处理。CT3起点136/136恢复，CT3/65工作误差3.43px，但正式0。GROUP_A504、开发组H78、CT2 431/457保留近GT STOP却选择较早位置，不能把所有错误称为过冲。

固定参考关闭/开启：工作10px19→17，正式7→7，没有精度增益。开发历史导航VALID0，验证组C208；开发19、验证2张正式误差>100px的标注帧均写历史。原R03 coherent_wrong_first_lock仍失败；原图负例与其不同，不代表安全已解决。40px间隙可达但确认失败，2/3列弱末端最终保留失败。保留为可运行但非生产工程基线，不替换A。

六组独立视频（验证组优先）及2647张逐帧局部对比见 `galleries/index.html` / `galleries/all_frames.html`。完整指标、签名有向误差、STOP分数、注册质量、性能、故障日志、源码与原图hash在同一运行目录。上一轮2960个封存文件核对未变；研究A55a0和历史发布A1c742身份仍分别保留。

## R05G：横截面逐步机制通过，归属/终止与首次锁定仍失败

隔离实现位于 `research/uctt_r05g/`，结果 `output/runs/uctt_r05g_20261112_r01/`。真实C++/OpenCV方向横截面、最近当前观测方向拟合、最多3局部极值、有限束、显式缺失与重捕获已编译回放。G0身份/旧B0选帧复现通过，G1机制通过；G2实际归属/终止FAIL，G3首次锁定FAIL；G4参考与可信历史导航NOT_IMPLEMENTED。G5全回放/证据交付完成，不代表准确率通过或可部署。

四开发组1565帧×4自动变体=6260次调用；80选帧76 VISIBLE+4 UNCERTAIN。独立当前原图短种子E0与AUTO严格分离，标签只在冻结后离线比较。E0贪心/束暂定端点10px为12/76、14/76；束人工路径覆盖均值98.56%，但可见轨迹精度均值63.98%，大量经过真实尖端后继续追纹理。AUTO贪心/束暂定10px为10/76、9/76；强观测消融29/76但开发组H弱末端丢失，不能按这一列升级。正式observed全部0、trusted_history为空，这是功能未通过的守卫，不是全拒绝安全成功。

开发组H78原两列弱片段在AUTO束第123/124步附近接入，暂定端点误差6.22px；GROUP_A504 AUTO贪心1.73px而束523.11px；CT2/395束401.42px。CT3全136帧AUTO无起点，选帧最长合格起源连续性≤2未达3；诊断轨迹又有末端过冲，正回归守卫失败。合成34项31通过，连贯旧划痕误锁/平行划痕束误接仍在，参考辨别未实现；原R03错首锁继续失败。

AUTO束原生P50/P95=6.170/17.331ms，>50ms为0；但353/1565搜索不完整且192无起点，不能声称完整检测已达标。完整debug导出P95约69.19ms，I/O解码哈希约183.55ms，不能混成内核时间。i7/内存峰值NOT_VERIFIED。全1565帧4695对消融起源逐字段一致；640详细trace、672948个依赖截面核验通过。AUTO贪心首轮最多3起点，此后宽1；严格单种子宽1对照是E0。

交付1565张逐帧局部图、80详细卡、9哨兵放大/截面响应、原像素弱裂纹证据、完整视频与慢速证据视频、逐帧图ZIP。生产/配置/原图/标签/旧468件R05F产物未改。验证组C/三点弯本轮新图像/标注读取0，排除组X排除。下一步优先独立起源身份、保留早期停止候选与后续探索的竞争；不扩大候选/预算、不用GT选阈值或历史最长端点兜底。读development_report、failure_first_divergence、origin_candidate_audit与group_h78_short_fragment_audit后再开发。

## R05F：S0指定基线通过，S1弱短片段过滤失败，后续门未启用

本轮隔离原生代码在 `research/uctt_r05f/`，产物在 `output/runs/uctt_r05f_20261111_r01/`。S0将R02/R05D/R05E研究构建55a0与当前源码计时克隆及既有记录逐帧比较，1565帧非计时输出完全一致。新S1 B0只用当前小窗口多尺度暗谷、NMS脊线、局部片段及几何去重，无参考门抑制，无observed/可信历史写入。四开发组完整1565帧回放，80选帧中76 VISIBLE / 4 UNCERTAIN；raw/去重/预算后3/5/10px召回均38/56/70。候选改善不能当成最终尖端准确率。

S1 FAIL：开发组H78最近候选12.221px；原生实际窗口55/56的尖端邻域有当前响应，距离线标注0.288px的2列脊线及4.383px的3列脊线被“至少4列成段”过滤。CT2/395候选7.453px，GROUP_A504保留7.303px，CT3/65为2.131px。全部6个raw10遗漏保留；GROUP_A全序列7帧触发8192片段预算，显式search_incomplete。固定x8容量的80选帧stateless对照仍70/76，没有恢复遗漏；不能直接提高容量或针对开发组H改阈值。当前优先研究方向是独立的未确认弱片段层及共享结构约束，仍在S1内。

独立S1原生调用计时P50=85.529ms、P95=105.028ms、P99=118.696ms、max=193.448ms，1429/1565帧>50ms；CPU为Ryzen9 7950X，目标i7未验证。35项接口/长线构造检查通过，但未覆盖的弱短片段失败已由真实数据证实。R03原16项故障原样复现，coherent_wrong_first_lock仍失败。S2步进、S3两侧材料参考、S4归属/终止、S5消融与S6只读验证均BLOCKED；没有以全fallback伪造安全改善。

本轮验证组C/三点弯新图像/标注读取为0，只记录已有1082条基线身份；排除组X不参与任何开发或验证，标签仅离线对比。生产源码、两个DLL、配置、原图、标签和旧封存结果不改。视频包含全部80开发选帧及失败结论，不能把播放速度当算法性能。

额外版本复查：发布DLL1c742（2026-11-06）与研究DLL55a0（2026-11-10）有403/1565帧formal输出差异，104帧确认状态、277帧tip字段不同。R01 dependency_audit.md:25和R02 ab_regression_report.md:3已明确前者为历史发布件，未用于当前源码A/B；因此这是既有版本边界，不是R05F回归，也不推翻指定55a0的源码克隆等价。中途把追加差异解释成整体S0失败的判断已纠正；发布件和研究候选精度不能混称，不能复制DLL来消除差异。详见baseline_scope.md。

[开发报告](../output/runs/uctt_r05f_20261111_r01/development_report.md) · [阶段门](../output/runs/uctt_r05f_20261111_r01/acceptance_matrix.csv) · [80帧图册](../output/runs/uctt_r05f_20261111_r01/galleries/index.html) · [结果视频](../output/runs/uctt_r05f_20261111_r01/R05F_S1_Results.mp4) · [弱片段原生证据](../output/runs/uctt_r05f_20261111_r01/galleries/images/group_h78_response_segment_failure.jpg)。

## R05E：当前证据解耦通过，空间桶候选安全失败

真实隔离C++17代码`research/uctt_r05e/`，产物`output/runs/uctt_r05e_20261111_r01/`。生产源码/DLL未改。B0完整开发1565帧与冻结A/R05D非计时输出一致；B1/B2完整开发1565及冻结后验证1082帧均保持原输出/ROI/长度/状态，选帧legacyScore逐位一致。B1恢复全部50个R05D G1当前响应；开发76 VISIBLE中current10=74，raw10=67。B2固定4×4桶、每桶4个、K64压缩后retained10=55，12例近端候选被桶内容量误删，Gate FAIL；B3/B4/B5 BLOCKED，不得生产替换。

四哨兵B2最近保留候选：CT2/395 8.31px、开发组H/78 12.15px、GROUP_A/504 7.12px、CT3/65 1.64px；这些不是新的确认输出，原A大偏差仍在。GROUP_A/398原本0.96px近端raw722被桶10删除。76个原生DP重算控制与B1 current-source峰完全一致；开发组H/41、78、115当前支持像素的gain不足12，CT2/196、338、431及开发组H/304不满足向前停止极值。不要用调整10px容差或降低阈值宣布修复。

原始R03同一fixture仍15/16通过，coherent_wrong_first_lock失败；不能把旁路无输出/无历史写入称为锁定安全通过。冻结后验证组C/三点弯35 VISIBLE raw10=29、retained10=22、预算误删7；5 UNCERTAIN不评分。验证数据没有参与改规则。排除组X完全排除，人工标注仅对比/QC，不训练、不拟合。无真实阴性标签，真实FP NOT_VERIFIED。目标i7及新初始点扰动稳定性NOT_VERIFIED，完整原生计时见报告，K64不等于CPU达标。

下一轮优先研究开发组中结构链/停止位置的预算保留，随后区分弱累积支持与非停止极值两类G2；两关通过才允许新归属/终止。禁止据验证组调参。保留所有R05E失败证据和旧输出。

[问题结论](../output/runs/uctt_r05e_20261111_r01/problem_findings.md) · [完整报告](../output/runs/uctt_r05e_20261111_r01/development_report.md) · [120帧图册](../output/runs/uctt_r05e_20261111_r01/R05E_Failure_And_Improvement_Gallery.html) · [结果视频](../output/runs/uctt_r05e_20261111_r01/R05E_Validation_Results.mp4) · [验收门](../output/runs/uctt_r05e_20261111_r01/gate_matrix.csv)。

## R05D：已定位端点证据丢失及竞争路径拒绝，未替换生产

代码 `research/uctt_r05d/`，产物 `output/runs/uctt_r05d_20261111_r01/`。六组完整2647帧A0/D0非计时原生输出、状态、路径/长度严格一致；R05原120选帧指标原样复现。开发组80选帧中76 VISIBLE/4 UNCERTAIN；首次失效查询G1=50、G0=2、G2=2、G3=4、G4=1、NONE=17（10原图px粗容差）。G1中38例局部参考相关票不足、9例一致票不足、3例响应弱。G0两例是CT2/204、299端点配准不可用，不能统一称ROI太小。

CT2/395与开发组H/78人工尖端均在真实端点ROI内。前者参考块0票达到0.62，后者3票但0个一致票；`localReference`拒绝后aligned保持0，`eroded>75`使尖端邻域score保持-3，首失败G1。GROUP_A/504在7.12px附近有真实候选，但与先选路径共享点为0，`shared<4`使distalLine返回空，首失败G4。CT3/65对应参考块6票一致、score最大25.17、最近峰1.64px、最终误差8.41px；映射闭环正常。主路径ROI、独立端点ROI、R05 E1/E2掩膜已分开，不能混用归因。

302个开发组离线反事实保留全部结果：CF1固定变换扩窗，CF2固定ROI更换局部参考drift，CF3仅旁路竞争路径拒绝，CF4只给参考不可用像素补当前valley。CT2/395扩窗仍928.94px；CF4产生GT近峰但最终仍238.55px。开发组H/78 CF4仍279.61px；GROUP_A/504 CF3返回360.98px错误点，CF4恢复7.12px但候选3→448。因此不得直接上线扩窗或旁路。四重点帧另作统一初始点+2%间距x平移、完整前缀回放；这是T2-A研究，不是真实新上游轨迹。

验证组C/三点弯按冻结规则只读验收1082帧、40选帧；35 VISIBLE中G1=16、G2=1、G3=8、NONE=9、INDETERMINATE=1（验证组C首帧声明无裂纹参考，缓存结果没有端点证据）。5 UNCERTAIN不评分。它们不用于开发、干预或选参。排除组X图像/标注不读；标签不训练、不拟合。

生产A接口计时（2641非参考帧）P50=106.16ms、P95=172.65ms、max=220.04ms，2452帧>50ms；CPU AMD Ryzen9 7950X，4原生线程，不能称目标i7达标。D0单列，未含I/O、hash及渲染。下一轮只建议研究“参考不可用与当前图候选证据解耦”的一个局部分支，保留候选来源与未确认状态；不建议直接生产替换。物理全因果诊断仍PARTIAL，局部首失效与反事实已可审计。

[开发报告](../output/runs/uctt_r05d_20261111_r01/development_report.md) · [逐例根因](../output/runs/uctt_r05d_20261111_r01/root_cause_report.md) · [全120帧图册](../output/runs/uctt_r05d_20261111_r01/R05D_G0_G5_Failure_Gallery.html) · [离线完整证据包](../output/runs/uctt_r05d_20261111_r01/R05D_visual_evidence.zip) · [结果视频](../output/runs/uctt_r05d_20261111_r01/R05D_Failure_Stage_Results.mp4) · [下轮最小研究计划](../output/runs/uctt_r05d_20261111_r01/next_patch_plan.md)。旧R01–R05输出保留。

## R05 当前人工标注验证完成：用途隔离生效，算法效果未通过

2026-11-11 按用户最新要求，`config/dataset_usage_policy.json` 规定：GROUP_A、CT2、开发组H、CT3用于开发；验证组C和三点弯整组仅验证，不能用于调参或选择算法；排除组X完全排除后续开发与验证。人工标注只用于QC及结果对比，不用于模型训练、伪标签训练、参数拟合、自动阈值搜索或在线参考选择。旧development/holdout字段不覆盖组级权限；既往曝光事实保留，不能称独立未见TEST。后文七组结果、排除组X标签争议均为历史记录，不再是当前使用数据或阻塞项。

本轮位于 `research/uctt_r05_validation/`，输出 `output/runs/r05_annotation_validation_20261111_r01/`。排除排除组X后120张标签格式与映射通过：111张明确可见，9张不确定单独统计。人工文件未修改；先锁定规则、输入和生产身份，再做比较；无训练或调参。

冻结生产A按六组原始时间顺序回放2576帧，对120选帧独立评分。在111张明确可见帧中73张有确认输出、38张缺输出，17/111张误差≤5原图像素。逐组有输出/可见GT：GROUP_A4/19、CT2 14/20、开发组H16/18、CT3 18/19、验证组C18/20、三点弯3/15。仅有输出样本的尖端误差P50分别为3.49、310.13、628.41、4.49、27.69、20.12px；缺输出不计为零误差。CT2和开发组H存在明显大偏差，不能认为生产A精度通过。保留A仅表示未发布未经验证的新版本。

冻结E1/E2差分仅49张明确可见帧可公平配对；CT2、验证组C、三点弯完整人工路径共同有效覆盖均值分别33.11%、77.77%、52.47%，其他三组没有有效配对。E2路径附近响应偏弱，可能与历史已有裂纹相消有关，不能作为噪声改善或当前无裂纹证明。历史差分作为主要可见裂纹/尖端证据不获支持；新增变化检测价值仍INCONCLUSIVE，R05_FORMAL_DEVELOPMENT_READY=NO。生产C++与DLL均未改变。

[完整报告](../output/runs/r05_annotation_validation_20261111_r01/validation_report.md) · [120帧尖端叠图](../output/runs/r05_annotation_validation_20261111_r01/Production_A_Tip_Comparison.html) · [差分与路径覆盖图册](../output/runs/r05_annotation_validation_20261111_r01/R05_Human_Annotation_Comparison.html) · [4分16秒结果视频](../output/runs/r05_annotation_validation_20261111_r01/R05_Annotation_Validation.mp4)。视频为全部选帧逐张对照，不是原始序列实时检测速度。用途与原图坐标合同测试通过；`run.ps1 check`已排除排除组X，现有五组15张冒烟及历史回放通过，不假称覆盖CT3。完整性与源代码快照见该运行目录的最终清单。

## R05 人工标注第二次检查：文件与格式通过，6帧主尖端语义仍待确认

2026-11-11 16:06 检查140份人工JSON全部齐全且通过格式/坐标QC：123张单一路径+尖端、11张不确定、6张双路径/双尖端。GROUP_A1已改polygon，三点弯曲1已补保存。排除组X248/268/320/337/390/407仍未区分单主目标，其中248下方尖端移动后距路径末端13.14px，需要据原图核实衔接。其余137份JSON与首次检查相同，排除组X519/CT2 271/开发组H78的视觉建议保留。

[第二次检查报告](../output/runs/r05_annotation_audit_20261111_160646/annotation_quality_report.md) · [叠图](../output/runs/r05_annotation_audit_20261111_160646/annotation_review.html)。SCHEMA_PASS / SEMANTIC_REVIEW_REQUIRED，未修改人工标签或生产代码；单主尖端评分应暂排除6帧语义歧义。

## R05 人工标注已返回：QC部分通过，待补齐与目标澄清

2026-11-11 复核外层工作包140张原图，139份JSON已保存。122张单一路径/尖端通过格式和坐标检查，11张不确定标注（其中GROUP_A1使用circle，与约定polygon不符），6张排除组X图有双路径/双尖端；三点弯曲1缺JSON。排除组X248/268/320/337/390/407需明确主目标或多目标评价规则，不能自动删一条。排除组X519、CT2 271、开发组H78另有弱可见区域复核建议。原图哈希未变，所有134个点距最近路径端点≤1.60px，该值不是定位精度。

[标注QC报告](../output/runs/r05_annotation_audit_20261111_154722/annotation_quality_report.md) · [人工标注叠图](../output/runs/r05_annotation_audit_20261111_154722/annotation_review.html)。原始139份人工JSON已快照备份，本轮未改标注、未做调参/holdout评分。重复解压的内层同名包140份JSON全空，不能混作人工标签。ANNOTATION_QC=PARTIAL/NEEDS_REVIEW，正式算法开发仍需先处理这些问题。

## UCTT R05-PRE：140张原图包已交付，正式开发等待人工标注

2026-11-11 隔离研究位于 `research/uctt_r05_prelabel_difference/`；[标注包](../output/runs/uctt_r05_prelabel_difference_20261111_r01/R05_LabelMe_Annotation_Package.zip)、[中文标注说明](../output/runs/uctt_r05_prelabel_difference_20261111_r01/R05_LabelMe_Annotation_Package/README_标注说明.md)、[完整报告](../output/runs/uctt_r05_prelabel_difference_20261111_r01/R05_Difference_Controlled_Report.md)、[对照视频](../output/runs/uctt_r05_prelabel_difference_20261111_r01/R05_Reference_Difference_Results.mp4)。盘点7组3171原图，每组20张字节复制+空JSON，实际LabelMe5.2.1逐张加载140张通过。每组15 development/5内部holdout；全部已曝光，不能称独立测试。CT3点来源仅冻结CSV显式映射，独立原始跟踪文件缺失。

185目标帧（140标注帧+每组固定前8帧的并集），E1/E2共同有效73帧：验证组C25、CT2 22、三点弯曲26，其他组无公平配对。共同mask上稳定条带残差p95中位数E1→E2：验证组C12→7、CT2 6→6.5、三点弯曲6→5灰度级；不能当尖端准确率。全部同ROI/阈值，未来图像及P1/P2扰动测试通过；中央过渡区域排除、稳定条带未经人工确认，覆盖风险未解除。FIXED_VS_HISTORY_FEASIBILITY=INCONCLUSIVE；REAL_TIP_ACCURACY=AWAITING_MANUAL_ANNOTATION；R05_FORMAL_DEVELOPMENT_READY=NO。生产源码/DLL与此前封存证据587文件哈希不变，没有发布新算法。后续先导入用户标签并验证路径覆盖、干扰区域，禁止把空标签当负样本。

## UCTT R04：路径归属旁路失败，视频已交付，生产 A 不变

2026-11-11 的隔离代码在 `research/uctt_r04/`；[开发报告](../output/runs/uctt_r04_path_tip_20261111_r01/development_report.md)、[结果视频](../output/runs/uctt_r04_path_tip_20261111_r01/R04_results.mp4)。642个初始化/帧案例、472张组帧复现R03，B1诊断旁路与B0原始输出零差异。真实确认覆盖B0=268、原图截面D1=159、前缀连接D2=21，总分母642；D2下降38.47个百分点，不能作为稳定性改善。没有生产合入。

R03原16项故障原样复现。在同一GROUP_A图像及原R03平移候选上，R04原图支持检查拒绝了干扰、保留原候选（原候选并非物理GT）。构造反例中D2保留10/11个可见正候选、误接纳1/8个干扰；相连强伪影仍能引起错锁及真实路径拒绝。真实人工标签=0，无独立HOLDOUT，无T2-B-real。E1安全/覆盖门槛未过，因此E2交换、E3新终止候选、B3–B5和完整扰动矩阵均未启用；ROI/mask/配准各自因果贡献仍NOT_PROVEN。

视频为2分18秒、1600×900、H.264，包含预先选定的153张真实原图（235个初始化案例）及明确标记的构造注入；慢放速度不是原生吞吐。原生性能单独计时，50ms未通过。保留候选/后向路径/截面/map哈希导出与失败证据，不得把D2的低配对距离或预测输出解释为通过。

## UCTT Phase 1 R03：Gate 2 失败，保留生产 A

本轮按 R03 状态机/动态 ROI 文档执行分阶段实验，代码位于 `research/uctt_r03/`，证据位于 [R03 开发报告](../output/runs/phase1_r03_dynamic_roi_20261110_r01/development_report.md)。生产源码、R02 基线 DLL 和 R01/R02 封存证据未改动；没有发布或合入新生产算法。

七组 measured 连续窗口和四个已知失败初始化变体共 1428 个初始化/帧案例复现 R02，A1 shadow 原始输出差异为零。A2 state-only 的有限坐标明确区分 observed/predicted/fallback；预测和回退不确认、不更新历史。但路径连接门槛导致验证组C控制确认 50→1、CT2 110→16、CT3 124→117，不能称为解耦改善。

16 个候选证据注入测试通过 15 个；自洽干扰路径首次获取仍会写入历史，Gate 2 安全失败。按文档顺序禁止创建 A3/A4 闭环，因此完整16变体与新增±5%矩阵、动态ROI改善、恢复性能均未验收。真实物理GT和T2-B-real轨迹仍缺失。性能重新使用每帧计时器，按互斥scope归因；CPU为Ryzen 9 7950X，并非目标i7-12700K。完整数值、限界与验收状态见报告，不得把本轮失败实验当作正式版本。

## 基准点与结果解耦（当前实现）

生产 A 现在将当前帧 P1/P2 限定为粗刚体定位先验，不再让它们直接重定义裂纹尖端 ROI 的中心、方向、确认状态或结果坐标。参考帧一次性建立固定裂纹坐标系；每帧先以对应的当前 P1/P2 给出捕获范围，再由固定参考纹理计算残余平移/旋转，最后在配准后的固定参考 ROI 内独立测量尖端。当前 P1/P2 必须是有限、在图像内、间距非退化且对应参考帧同类物理位置的点。

`tests/check_anchor_invariance.py` 对六组冒烟序列施加整体平移、端点不等量移动、间距缩放、轻微旋转和小幅抖动；CT3 完整验证从第二帧起施加 ±20 px 平移和 0.75–1.35 倍间距变化。尖端确认状态和坐标应由纹理细化后的参考几何决定。完整根到尖端弧长仍是独立的根部/路径测量，不属于本次尖端解耦合同。该回归不覆盖错误物理对应、点序颠倒、裂纹离开视野或图像纹理不足。

当前正式 A 已切换为 ROI 内独立尖端测量。P1/P2 定位和跟踪搜索窗口，窗口内逐段判断暗线末端；完整弧长单独校验。CT3 共 136 帧、八组选点，详见 `output/runs/ct3_roi_tip_r01/验证报告.md`。集成包仍为 `output/releases/A_Win64_OpenCV440.zip`。切换前 A 的源文件和 SDK 在 `output/backups/A_before_roi_tip.zip`。下段为上一版发布记录。

上一版 A 的七组验证见 `output/runs/a_production_merge_seven_r01/`，更早的冻结 A 备份见 `output/backups/FrozenA_before_A_merge.zip`。

下文为早期 A′ 研究的封存记录。

2026-11-05 最新 A′3：**KEEP_A**。代码research/aprime3，输出output/runs/aprime3_20261105_r01/index.html。生产冻结A哈希和操作合同未变，AP2及更早封存证据不改动。

37候选遗漏定位为21末端被valid/window排除、11事件合并、5阈值前不产生合格事件。保留旧池+未确认端点+多尺度事件后，曝光候选正确379→404/432；NEW_DEV583→621/648，无旧正确候选损失，K≤12。16 no_seed是起始峰值4.989779～5.997019<6，已有支持路径而被seed门槛拒绝，本轮没有新seed恢复。11 stop/continue是静态占比<.85（5帧还出现继续证据），3帧扰动不稳定。

NEW_DEV306案例918帧，18独立pair/3背景/54配对帧实际激活。最终正确553→553，阴性FP105/216未改善，Gate C失败；曝光旧365正确在歧义保护后回退为359，不可只报候选收益。54对相同图像但不同物理归属是不可辨识反例，不是可由灰度图完美分类的普通负控。GT隔离在评测器，真实精度N/A。

参考新DEV覆盖63.0069%→62.9512%，Gate B失败。严格同端点：验证组C196→194、三点弯181→181，其余4组0；多查询验证组C380不能作为同端点提高。CT2主要LOW_NCC；GROUP_A/排除组X局部合格块不足；开发组H仅6缓存且查询附近0。已知运动132条件中新旧>1px错误接受均0，但未证明跨试件泛化。

3035帧新seed观察器与冻结A状态/尖端/旧弧长/float64路径完全等价。隔离计时开发组HA P95=46.47ms、Max=50.38ms，本批无>66.67ms；全A′3仍Python，完整原生15Hz NOT_TESTED。独立TEST未生成，所有TEST指标N/A。8视频/4493逐帧原图对照，候选只在关键诊断图显示。research_valid与selected_output_valid明确分开，回退A不等于研究确认。

以下为前轮背景，非最新结论：

2026-11-05 A′2最新一轮：KEEP_A。运行目录output/runs/aprime2_20261105_r01；研究代码research/aprime2。3035帧最终C++旁路/原A状态及float64路径一致，原图SHA逐一核对。原生旁路仅采集tile，不是A′2生产DLL。

新DEV180案例540帧、432可观察正例，12独立真假尾pair/3种材料过程实际激活36个配对帧。A正确359、候选oracle379、v2/v3决策正确365。v2改6帧均≤8px；v3改9帧，额外3帧误差约9.74–10.91px仍不正确。只有2独立pair两侧三帧全部正确，无独立TEST。弱裂纹仍7/36。

参考v2同末端口径240/3029，比旧A′337下降；多区间339是另一口径，四个零支持组仍为0。查明点mask角点排名先消耗预算、后筛patch的问题；prefilter=True前置比例筛选在同DEV覆盖20.16%→58.31%，没有增加正确尖端数。仅原四组做该修正后续诊断；排除组X历史与三点弯验证不调参。默认MaterialCache仍prefilter=False，以显式--prefilter区分v3实验，未静默推广。

H2未泛化，正式TEST未启动，完整A′2原生15Hz NOT_TESTED。原A/旁路本轮计时存在与媒体并发，开发组H少数帧超66.67ms，不能据此给生产实时保证。详细失败阶段、反事实、版本差异和未完成ROI重跑项见本轮报告。继续开发先阅读该报告；不要将DEV收益或回退A解释为真实独立准确性。

---

前轮A′封存背景：

生产：冻结A，C++17 / OpenCV4.4，正式flags3572、policy1 SHADOW、terminal1、refine=true、4线程。原DLL与核心源码哈希在 baseline/frozen_a/identity.json。项目迁移不改算法。

最近一轮A′：正式3035帧重放状态/尖端/旧弧长/double路径完全一致，992帧独立诊断trace同样一致。339/3029张变形帧局部几何通过，337张联合光度通过：验证组C137、三点弯200，其余四组0。跨场景Gate1失败，停止后续正式候选排序、新TEST及新A′DLL。

新工程DEV72案例216帧：168可观察正例，保留A的输出118帧<=8px；36阴性有12个静态线误确认；12不可观察正例0确认。强假尾激活0/12，因此未证明解决排除组X473长尾。55/75交叉保持A各12正确，S型0正确、弱裂纹4正确，不可用回退结果声称新模块改进。

关键问题：A当前线恢复分支及路径前缀历史确认可支持错误长尾。参考关系已经用于配准和响应，但末端独立归属证据不足。A′先可信材料匹配、空间FIT/HOLDOUT、局部光度与沿路径增量，再考虑尖端；不要将参考纹理转折直接升格为尖端。

开发组A/开发组H参考局部大量近饱和像素；CT2有纹理但匹配数/分布不足。选块mask“任何近饱和像素腐蚀整块”比后续模板<=3%坏像素更严格，是待改进点；不能通过降低验证门槛伪造覆盖率。下一轮先在新DEV上验证选块与图像可比性，再进入候选/决策门槛。

排除组X退役，只作曝光历史追因，禁止调参；三点弯曝光验证、禁止调参；四组开发数据也已曝光。暂无新真实试件、人工物理GT、同步载荷相位；真实准确率N/A，不采用单调先验。所有历史合成DEV/TEST均不再独立。

项目独立整理后，archive不参与运行。最新封存结果在output/aprime_20261105/run01，保持文件内容哈希；旧绝对路径只作来源，使用维护目录中的迁移映射定位。新运行仅output/runs/<id>，构建仅output/build，工具输出仅output/。
