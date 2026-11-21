# 勘误与执行边界

文档三点弯possible_forward_continuation“已确认118帧”：原始status_counts.csv为全部118帧，其中确认尖端117帧，1帧未确认。总确认带其他shadow提示138帧可复核。历史排除组X/CT2原生tile数、gain、前缀时序等数值先引用已归档原始审计，后续只读回归，不以其选C参数。

无新真实试件和GT（用户已确认），REAL_HOLDOUT_NOT_AVAILABLE / REAL_TIP_GT_NOT_AVAILABLE。排除组X仍退出当前验证名单；本任务文档明确允许历史诊断，因此只读回放，不恢复其验证角色。三点弯已曝光，固定no-tuning。生产视频/CSV与已有研究档案均不覆盖。


最终勘误：最初data_split_manifest.json保留24族草稿及disjoint措辞，实际最终26族、独立抽样但部分支持重叠，见actual_data_split_manifest.json。共享渲染pair聚类、强假尾按独立案例另计，见post_TEST_errata.md。TEST未重测/调参。
