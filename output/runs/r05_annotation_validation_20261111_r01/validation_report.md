# R05 当前人工标注：六组受控验证

## 数据约束已生效

用户2026-11-11最新准则已写入config/dataset_usage_policy.json、AGENTS.md和数据读取检查。开发组为GROUP_A、CT2、开发组H、CT3；验证组C和三点弯整组为VALIDATION_ONLY；排除组X从本轮及未来开发/验证完全排除，旧文件仅保留，不删除。旧清单里验证组C、三点弯的development子集不授予开发或调参权限。

人工标注仅供QC和结果对比，没有训练、伪标签训练、参数拟合、自动阈值搜索或基于标签的参考选择。两个验证组只读评估，规则锁定后未根据它们改算法。全部试验此前已曝光，当前分组约束是前瞻性用途限制，不把已曝光组重新称作独立未见TEST。

## 输入、冻结与评分范围

排除排除组X20张后，6组120张：111张明确路径/尖端，9张不确定。全部当前JSON和图像映射通过QC，原图哈希未变。排除组X的双尖端及路径衔接争议不再阻塞本轮，因为其图像/标签在进入本轮读取前已排除。

冻结的E1固定参考/E2匹配历史/C0最近帧/C1开口排序结果来自R05-PRE真实产物。当前标签既不改变warp/mask，也不改变历史候选、配准门和差分阈值25。完整规则、文件哈希、策略、3/5/10原图像素容差在pre_evaluation_lock.json中先锁定后评分。生产A另用冻结DLL、flags3572/SHADOW1/terminal1/refine=true/4线程按原始序列回放；同组只初始化一次，首帧GetBaseline为缓存查询。回放只读原图和原始P1/P2，不打开标注JSON，之后比较器才读取快照标签。

每组20张原有15 development/5 holdout子划分保留作分层统计；对于验证组C和三点弯，两种子划分全部仍是验证数据。9张uncertain均排除确定尖端/路径误差，单独统计，不能按负样本或0误差计入。原标注者已要求按当前标签继续，本轮不自动修正弱可见末端。人工粗标注本身存在容差，不把点坐标当作无限精度真值。

## 差分证据验证

| 数据组/角色 | 可见/不确定 | 有效配对 | 完整路径有效覆盖（仅配对帧均值） | E1/E2路径差分支持（5px） |
|---|---:|---:|---:|---:|
| group_a / DEVELOPMENT | 19/1 | 0 | N/A | N/A / N/A |
| ct2 / DEVELOPMENT | 20/0 | 16 | 33.11% | 24.46% / 6.97% |
| ct3 / DEVELOPMENT | 19/1 | 0 | N/A | N/A / N/A |
| group_h / DEVELOPMENT | 18/2 | 0 | N/A | N/A / N/A |
| three_point_bend / VALIDATION_ONLY | 15/5 | 14 | 52.47% | 35.69% / 0.00% |
| group_c / VALIDATION_ONLY | 20/0 | 19 | 77.77% | 24.64% / 0.75% |

覆盖分母是人工标注的完整原图路径弧长，按0.5原图像素间隔均匀采样并按弧长加权；落在ROI外的路径仍计入总长度，避免裁掉路径后虚增覆盖。路径容差带按缩放ROI像素中心映射到原图坐标，解析计算到人工线段的距离，统一使用3/5/10原图像素。E1/E2只在同帧同mask交集上比较；C0/C1消融另使用四臂共同mask，完整分母见CSV。

关键发现：图像能够通过双侧配准，并不意味着真实裂纹都落入可用差分区。CT2、验证组C、三点弯的人工路径都存在明显掩膜覆盖损失；GROUP_A、开发组H、CT3没有可评分的E1/E2配对。多数路径实际在ROI内，主要损失与中央过渡带、有效像素掩膜和配准不可用有关；这里只是位置归因，尚未通过放开掩膜消融证明可以安全恢复。

E2在人工路径附近的变化响应普遍低于E1，三点弯在5px容差带的配对样本上为零。历史图本身可能已经包含裂纹，低差分可由共同裂纹抵消造成；该结果不能解释为“当前无裂纹”，也不能把E1更多变化直接当成裂纹新生长度。因此当前证据不支持把E2作为主要可见裂纹/尖端判据，亦不能从本轮推出历史差分在新增变化检测上必然无价值。

off_path_activation_density仅为人工主路径带外的强变化密度，不是真实误报率；没有人工interference区域或no_visible_crack样本，干扰激活率与无裂纹误报率均N/A。静态几何条带与人工路径的重叠量也已导出，避免未经标注核验就认定整条带完全静态。

## 冻结生产A与人工尖端的直接对比

| 数据组/角色 | 可见GT | 有观测输出 | 缺输出 | P50/P95/max误差 px | ≤5px数量（全体可见分母） |
|---|---:|---:|---:|---|---:|
| group_a / DEVELOPMENT | 19 | 4 | 15 | 3.49/20.48/23.21 | 2/19 |
| ct2 / DEVELOPMENT | 20 | 14 | 6 | 310.13/854.41/928.94 | 0/20 |
| ct3 / DEVELOPMENT | 19 | 18 | 1 | 4.49/11.80/12.51 | 9/19 |
| group_h / DEVELOPMENT | 18 | 16 | 2 | 628.41/922.68/951.92 | 0/18 |
| three_point_bend / VALIDATION_ONLY | 15 | 3 | 12 | 20.12/37.40/39.32 | 0/15 |
| group_c / VALIDATION_ONLY | 20 | 18 | 2 | 27.69/134.84/150.69 | 6/20 |

总计111张人工明确可见帧，73张生产A确认输出、38张缺输出；≤5px为17/111（全体可见帧分母）。这不是可接受精度已经得到证明的结果。CT2与开发组H存在数百像素偏差，三点弯缺输出较多；不能只用CT3相对较低的中位误差概括所有组。

误差为原图像素欧氏距离，仅“人工明确可见+生产confirmed observed输出”进入P50/P95/max分母。缺输出单列，不填零；同时报告≤3/5/10px占已观测输出及全部人工可见帧的两个分母，防止确认覆盖下降被误判为精度提升。生产A只有一个冻结版本，本轮不能声称算法优化前后提升。E1/E2不生成尖端预测，因此没有其尖端定位准确率；上述点误差只属于生产A基线。

## 决策与下一步

- LABEL_QC_SIX_GROUPS = PASS：120张合法，111 visible / 9 uncertain。
- DATA_USAGE_POLICY = ENFORCED：排除组X不参与，验证组C/三点弯只验证，标签只对比。
- MODEL_TRAINING / PARAMETER_FITTING = NOT_PERFORMED。
- FIXED_VS_HISTORY_FEASIBILITY = INCONCLUSIVE_FOR_CHANGE_DETECTION。
- HISTORY_DIFFERENCE_AS_PRIMARY_VISIBLE_CRACK_EVIDENCE = UNSUPPORTED。
- R05_FORMAL_DEVELOPMENT_READY = NO：当前掩膜覆盖和有效组别不足，未证明历史差分安全增益。
- PRODUCTION_ALGORITHM_UPDATED = NO；基线尖端误差已实测，不等于新版本通过。

后续如继续研究，只能在四个开发组原图上处理配准可用性、中央过渡区域的证据表达，并保持当前图像可见结构验证；不能依赖人工点训练或拟合，不得依据验证组C/三点弯分数选参数。验证组待新规则锁定后再次评估；已经看过的验证结果不能包装成未见泛化。

性能记录为本机原生API分项计时与独立I/O计时，没有宣称目标i7端到端50ms达标。差分渲染和人工评价也不是在线算法耗时。

## 产物

- [原图ROI、人工标签与冻结差分图册](R05_Human_Annotation_Comparison.html)
- [生产A与人工尖端逐帧对照图册](Production_A_Tip_Comparison.html)、[全部120选帧结果视频](R05_Annotation_Validation.mp4)
- [逐帧路径覆盖](path_coverage.csv)、[路径带差分比较](difference_label_comparison.csv)、[按组/用途/原split汇总](difference_group_summary.csv)
- [生产A逐帧人工尖端误差](production_tip_comparison.csv)、[生产A分组与分母汇总](production_tip_group_summary.csv)
- [120张人工JSON快照](human_annotations_six_groups_snapshot.zip)、[先验锁定](pre_evaluation_lock.json)、[用途与坐标合同测试](validation_contract_tests.json)、[输入与生产完整性](integrity_check.json)

复现入口为research/uctt_r05_validation/README.md。历史R05-PRE和两轮标注审计产物均未覆盖；config/datasets.json角色调整是用户明确要求的元数据变更，旧版本已备份在policy_before，生产C++源码与DLL哈希保持不变。
