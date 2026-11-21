# 截图所列数据与关键图打包

本包按现有保存结果整理，没有重新检测、修改算法或重算坐标。

## 截图清单对应位置

- 04_results/TEST_frame_predictions.csv、TEST_candidate_tips.csv、TEST_mechanism_by_family.csv：原文件直接打包。
- 04_results/TEST_roi_counterfactual.csv：ROI放大反事实；TEST_adaptive_params_per_frame.csv为TEST逐帧参数，REAL_adaptive_params_per_frame.csv为真实六组，adaptive_params_per_frame.csv为原DEV/TEST/REAL合表。其余配对指标、区间与拒绝条件作为辅助。
- 07_media/key_cases/controlled/：强假尾、真长、弱渐浅、S弯、55°/75°急弯，共108张。保留原先展示的3背景rep00全部6帧，不按效果挑帧；controlled_key_png_index.csv列出案例、源图SHA与PNG对应关系。
- 07_media/key_cases/evidence_*.png：已有候选剖面/前方证据图3张。
- 07_media/real_changed/：六组真实试验中，A/C尖端共同有效且距离>8px，或尖端有效性变化，或路径有效性变化的原对照PNG。全部2024张；参考帧若满足条件也保留，在索引is_reference标记。不是把坐标变化宣称为真实改善。
- 07_media/key_cases/historical/：已有紧凑局部对照11张，包含CT2 num6/18/84、排除组Xnum51/473及各组末帧。原对照图同时含原图局部、冻结A、C与放大，属于诊断PNG；清理疑似标记后的新版视频仍单独保存在11_A_C_confirmed_only，本次不把视频加入包。
- 05_regression/：六组逐帧CSV和原A/C路径JSONL，供继续分析；03_new_gt/保留TEST输入索引和程序GT；00_protocol/保留冻结与测量合同；08_reports/说明本轮失败和真实精度边界。

## 完整版与轻量版

完整版包含全部2024张变化对照PNG；轻量版保留全部相同CSV/JSONL/协议及全部受控关键PNG，但真实变化图按每组共同确认位移最大的前10帧，以及每个尖端/路径有效性变化方向最早3帧取并集，共110张。两版都保留11张紧凑历史对照。

real_change_png_index.csv对2024帧全部列出archive_path与included_in_light，轻量版未包含的PNG路径只是索引，不代表文件缺失。两版MANIFEST.csv为各自实际成员，列原文件路径、SHA256、字节数。JSONL中未删诊断字段，视频显示筛选不改变原数值。

## 解读边界

所有PNG是已有研究对照图，不是人工真值；真实六组物理尖端误差仍N/A。排除组X保持退役历史诊断、三点弯为已曝光不调参回归。TEST真值是程序可观察端点，形成但不可观察的端点另列。>8px为已有研究误差尺度下的打包检索规则，不是新检测阈值，也不是对TEST重新调参。

失效坐标/长度保持空值和有效位；长度字段以原图pixel、基准线右法向投影与legacy弧长分列，不混作mm。MANIFEST与ZIP完整性/逐成员SHA复核记录见压缩包旁package_complete.json。
