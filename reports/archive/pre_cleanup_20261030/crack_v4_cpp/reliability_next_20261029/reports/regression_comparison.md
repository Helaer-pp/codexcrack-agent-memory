# 完整时序与准确性验证

## 默认路径等价性

每组初始化一次，按原文件顺序完整回放，保留 previous/history。最终DLL在相同输入下与冻结优化版及上一轮保存JSONL比较，4组共1991帧、1987个当前帧，状态、根部、尖端/可见终点、像素长度、路径、旧时序及审计输出**零差异**。比较不包括计时和外部文件读耗时。内存驻留回放也逐帧独立核对，不只是抽样。

这证明兼容性，不证明真实精度为零误差。默认flags0，Verified仍关闭。

## 实验flags244的正式测量覆盖

| 组别 | 当前帧 | 旧确认 | 旧完整长度 | 旧error | 实验确认 | 实验完整长度 | 实验error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A测试-1 | 550 | 501 | 500 | 0 | 501 | 500 | 0 |
| 验证组C | 561 | 545 | 545 | 0 | 545 | 545 | 0 |
| CT2 | 467 | 371 | 371 | 27 | 398 | 398 | 0 |
| 开发组HMT | 409 | 290 | 275 | 5 | 293 | 278 | 0 |

32个原错误全部通过当前图匹配恢复，其中CT2 27帧输出完整长度，开发组H2帧没有裂纹候选、3帧确认完整长度。错误数减少与覆盖率提高不能解释为人工精度提高。

以下是实验模式相对旧正式路径的逐帧测量变化，而非默认回归。错误恢复会改变检测器frame_index及少量后续历史/seed诊断；未把这些反馈差异隐藏：

| 组别 | 最终默认与保存结果差异帧 | 原非error帧测量/路径变化数 | 所有实验测量变化帧 |
| --- | --- | --- | --- |
| 开发组A测试-1 | 0 | 0 | 0 |
| 验证组C | 0 | 0 | 0 |
| CT2 | 0 | 0 | 27 |
| 开发组HMT | 0 | 0 | 5 |

完整变化列表：`results/measurement_changes.json`；所有新测量均标记未判定好坏。Root连接上限继续12px；未修改黑帽、DP、平滑、根部长度定义、旧确认时序门槛。

## Verified 真正闭环回放

下面每个实例实际启用policy2后从参考初始化并逐帧处理，previous/history接收自己的判断反馈，不是把旧路径离线改标签：

| 组别 | 旧Verified尖端 | 完整长度 | error | 实验Verified尖端 | 完整长度 | error |
| --- | --- | --- | --- | --- | --- | --- |
| 开发组A测试-1 | 439 | 436 | 0 | 439 | 436 | 0 |
| 验证组C | 493 | 493 | 0 | 493 | 493 | 0 |
| CT2 | 165 | 165 | 27 | 188 | 188 | 0 |
| 开发组HMT | 213 | 195 | 5 | 214 | 196 | 0 |

原Shadow旧接受/旁路拒绝分别65/54/206/92，总417；反向3/2/0/15，总20。全部保留437行审核表。Verified依然明显降低覆盖，CT2旧371正式确认仅165 Verified；不能称拒绝的都正确。实验层级分类没有统一放宽所有阈值，等待标注后再决定权限调整。

## 240个真实图受控扰动

种子20261028，4组×3阶段×20种scope/扰动组合。含原曝光/gamma/对比度/阴影/噪声/失焦/平移/旋转/抖点/倍率。对两侧都确认的尖端才计算坐标代理偏差，失确认单列。

| 组别 | 案例 | 旧确认 | 实验确认 | 新旧确认翻转 | 实验最大代理偏差px | 控制确认但扰动丢失 |
| --- | --- | --- | --- | --- | --- | --- |
| 开发组A测试-1 | 60 | 43 | 43 | 0 | 11.454 | 0 |
| 验证组C | 60 | 55 | 55 | 0 | 29.261 | 5 |
| CT2 | 60 | 55 | 55 | 0 | 278.044 | 5 |
| 开发组HMT | 60 | 31 | 31 | 0 | 5.307 | 9 |

只有开发组Hboth阴影中/末段两例坐标改变，均保持确认；其他组包括CT2曝光失败保持未解决。初始化方向单项的结果与组合相同。所有数据为相对控制输出的代理稳定性，不是人工真值精度。

## 已知真值合成场景

保留原10类，并加入阴影入口/中部/尾部、曝光跳变、遮挡恢复、失焦恢复、高速增长/重复/跳帧、短可见裂纹、弱/局部配准纹理，共20类×3配置×5帧=300次观察。另有6种自动配准刚体移动×4配置=24例，每例3次观察。合成物理尖端、可见终点分开记录。

| 场景 | 首次确认帧 | 确认/5 | 末帧物理尖端误差px | 长度有符号误差px | 末帧审计 |
| --- | --- | --- | --- | --- | --- |
| strong | 1 | 5 | 2.613 | 6.127 | terminal_supported |
| weak | 1 | 5 | 0.951 | 3.377 | terminal_supported |
| clean | 无 | 0 | 无确认 | 无完整长度 | no_candidate |
| shadow_entrance | 1 | 5 | 2.626 | 6.127 | terminal_supported |
| shadow_middle | 1 | 5 | 2.801 | 6.277 | terminal_supported |
| shadow_tail | 1 | 5 | 2.662 | 6.127 | terminal_supported |
| exposure_jump | 1 | 5 | 2.613 | 6.127 | terminal_supported |
| occluded_tail | 无 | 0 | 无确认 | 无完整长度 | texture_erased_or_uncertain |
| occlusion_restore | 1 | 3 | 2.613 | 6.127 | terminal_supported |
| temporary_defocus | 1 | 5 | 2.613 | 6.127 | terminal_supported |
| shorter_visible_crack | 1 | 5 | 3.662 | 6.278 | terminal_supported |
| fast_growth_repeat_skip | 1 | 5 | 2.974 | 7.127 | terminal_supported |
| weak_registration_texture | 1 | 5 | 3.645 | 7.187 | terminal_supported |
| partial_texture_erasure | 1 | 5 | 2.663 | 6.227 | terminal_supported |
| translation | 1 | 5 | 2.613 | 6.127 | terminal_supported |
| rotation | 1 | 5 | 2.601 | 6.177 | terminal_supported |
| opening | 1 | 5 | 2.613 | 6.127 | terminal_supported |
| precracked | 1 | 5 | 3.480 | 6.927 | terminal_supported |
| missing_evidence | 无 | 0 | 无确认 | 无完整长度 | no_candidate |
| boundary | 无 | 0 | 无确认 | 无完整长度 | image_boundary |

合成总体统计（每配置100次观察）：

| 配置 | 有真值确认数 | 尖端误差P50/P95/Max px | 确认误差>5px次数 | 长度有符号均值px | 长度绝对误差P50/P95/Max px | 可见尖端未确认 | 不可见尖端未确认 | 无当前裂纹却确认 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| default | 83 | 2.626/50.508/50.508 | 7 | 1.819 | 6.127/47.213/47.213 | 7 | 0 | 0 |
| guard_shadow | 83 | 2.626/50.508/50.508 | 7 | 1.819 | 6.127/47.213/47.213 | 7 | 0 | 0 |
| guard_verified | 78 | 2.619/3.662/4.629 | 0 | 6.259 | 6.127/7.187/11.727 | 5 | 7 | 0 |

5px仅为本轮合成诊断阈值，不是用户验收容差。只在确认输出上统计尖端/完整长度误差，未确认另列；不可见尖端不确认是预期保护，不能算已定位正确。每配置均无当前裂纹误确认。检测路径到真值采样点的单向最近距离在三配置相同，逐观察均值的P50/P95/Max约1.004/1.068/1.188px，逐观察最大值的最大约4.626px；该路径指标包含未确认路径，不代表完整覆盖。详细数字见 `results/validation_metrics.json`。

这些是生成数据，5次重复不是疲劳试验萌生检出率。occluded_tail旧正式与旧Shadow已知误差50.51px；新Verified保留可见断点、不确认物理尖端，不能给不存在的确认误差填0。遮挡恢复序列为确认→不确定→不确定→确认→确认；较短可见路径仍确认，未启用单调先验。

新增自动配准反例(7,-31)旧/新Shadow均有360.02px的已确认误差。Verified仅拒绝，未定位真实尖端；提供真实当前基准点则约2.61px。完整失败、丢失和对照均保存在 `results/auto_recovery_truth.json`。

## 工程验证

最终DLL重复通过上一轮15/15工程测试，含2250帧长循环、基线查询只读、invalid struct不推进状态、多实例、ResetTemporal、已有裂纹参考/缺失证据、GRAYSCALE stride与旧C/V2 ABI。长循环private bytes增量见 `results/engineering_anchor_final.json`，本次为0字节。新增5/5接口测试验证只读扩展查询、历史清理、无效flags、生产不收集调试图、恢复失败不回填历史。合成针对性断言通过。旧SDK已编译程序的兼容执行另见 `results/abi_smoke.json`。

## 状态与分歧完整分布

状态字符串保留原语义；weak_candidate可能通过旧正式确认，不能只按名称推断有效性。tip_confirmed/length_confirmed仍为测量权限。

| 组别 | 配置 | 全部当前帧状态计数 |
| --- | --- | --- |
| 开发组A测试-1 | old_default | no_new_candidate=44, candidate_pending=5, tip_only_detected=1, weak_candidate=10, main_segment_detected=490 |
| 开发组A测试-1 | new_experiments | no_new_candidate=44, candidate_pending=5, tip_only_detected=1, weak_candidate=10, main_segment_detected=490 |
| 开发组A测试-1 | old_verified | no_new_candidate=44, tip_only_detected=3, terminal_uncertain=67, verified_segment_detected=436 |
| 开发组A测试-1 | new_verified | no_new_candidate=44, tip_only_detected=3, terminal_uncertain=67, verified_segment_detected=436 |
| 验证组C | old_default | no_new_candidate=13, candidate_pending=3, weak_candidate=31, main_segment_detected=514 |
| 验证组C | new_experiments | no_new_candidate=13, candidate_pending=3, weak_candidate=31, main_segment_detected=514 |
| 验证组C | old_verified | no_new_candidate=13, verified_segment_detected=493, terminal_uncertain=55 |
| 验证组C | new_verified | no_new_candidate=13, verified_segment_detected=493, terminal_uncertain=55 |
| CT2 | old_default | main_segment_detected=371, error=27, tracking_incomplete=69 |
| CT2 | new_experiments | main_segment_detected=397, tracking_incomplete=69, weak_candidate=1 |
| CT2 | old_verified | terminal_uncertain=275, verified_segment_detected=165, error=27 |
| CT2 | new_verified | terminal_uncertain=279, verified_segment_detected=188 |
| 开发组HMT | old_default | no_new_candidate=57, candidate_pending=45, error=5, weak_candidate=275, tip_only_detected=15, tracking_incomplete=12 |
| 开发组HMT | new_experiments | no_new_candidate=59, candidate_pending=45, weak_candidate=278, tip_only_detected=15, tracking_incomplete=12 |
| 开发组HMT | old_verified | no_new_candidate=57, tip_only_detected=18, error=5, terminal_uncertain=134, verified_segment_detected=195 |
| 开发组HMT | new_verified | no_new_candidate=59, tip_only_detected=18, terminal_uncertain=136, verified_segment_detected=196 |

全部437个分歧的原因计数（含20个反向分歧）：

| 组别 | 原因 | 数目 |
| --- | --- | --- |
| 开发组A测试-1 | possible_forward_continuation | 50 |
| 开发组A测试-1 | weak_terminal_support | 8 |
| 开发组A测试-1 | endpoint_temporal_pending | 6 |
| 开发组A测试-1 | shadow_confirmed_legacy_pending | 3 |
| 开发组A测试-1 | path_quality_uncertain | 1 |
| 验证组C | possible_forward_continuation | 53 |
| 验证组C | shadow_confirmed_legacy_pending | 2 |
| 验证组C | endpoint_temporal_pending | 1 |
| CT2 | possible_forward_continuation | 79 |
| CT2 | registration_uncertain | 76 |
| CT2 | endpoint_temporal_pending | 41 |
| CT2 | weak_terminal_support | 10 |
| 开发组HMT | possible_forward_continuation | 62 |
| 开发组HMT | shadow_confirmed_legacy_pending | 15 |
| 开发组HMT | endpoint_temporal_pending | 15 |
| 开发组HMT | weak_terminal_support | 9 |
| 开发组HMT | registration_uncertain | 5 |
| 开发组HMT | path_quality_uncertain | 1 |

按早中晚、参考状态、配准模式、尾段支持、增量长度及逐帧闭环结果进一步拆分见同名CSV。它们仍是待审核分类，没有人工正确/错误标签。
