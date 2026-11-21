# 第五组已曝光frame_id=473：冻结后研究复核

| mode | image | tip_confirmed | full_valid | tip | length_px | path_support | tail_support | terminal | status | Process_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 7490090569.bmp | True | True | [2344.05, 2409.42] | 1084.13 | 0.7339357429718876 | 0.9375 | terminal_supported | weak_candidate | 37.675100000342354 |
| A2 | 7490090569.bmp | False | False | None | None | 0.8868360277136259 | 0.5 | joint_tip_uncertain | weak_candidate | 53.164299999480136 |
| COMPAT | 7490090569.bmp | True | True | [2344.05, 2409.42] | 1084.13 | 0.7339357429718876 | 0.9375 | terminal_supported | weak_candidate | 38.24270000040997 |
| D | 7490090569.bmp | False | False | None | None | 0.9380281690140845 | 0.5 | stop_not_established | supported_prefix_only | 48.77729999134317 |

原图与各版本叠加位于frames/frame_0473_raw.png及_A/_A2/_COMPAT/_D.png。正式path、背景/停止字段见results.jsonl；A2另含failed_joint局部证据。真实尖端GT不存在，不能说未确认等于找对，也不能说正式确认等于物理正确。最终保留A与COMPAT未变，历史问题不自动视为解决；D的任何不同均记NEXT_CYCLE_FINDING，不返调本轮。

A/COMPAT 完整有效路径根部为(1680.03,2076.78)，尖端为(2344.05,2409.42)，弧长1084.13px，完整复现此前已知长尾输出。其旧式末段审核仍判 `terminal_supported`，尾支持0.9375、尾中位得分3.961；这些是当前选中轨迹的局部形态支持，不能判断该纹理仍属于真实裂纹，说明错误在最终审核前已进入候选路径。

D 根部(1680.03,2076.68)，内部可见段358.31px、路径支持0.938、尾支持0.5，但9个tile中没有建立最终STOP，正式 `tip_confirmed=false/full_length_valid=false`。D只得到一个不完整的内部前段，不输出正式长度或尖端；不能声称长度已纠正为358.31px。A2同样拒绝，不能视为真正定位成功。下一周期发现为停止目标与路径最优目标不一致、背景零MAD以及当前图像弱终端的消歧，详见root_cause.md；本轮不据第五组返调。

注意表中 A 的 `status=weak_candidate` 与正式有效标志并不冲突：冻结源码在 `r.length==true && !strong` 时也赋这个描述词，时序接受可使其完整有效；该字符串不是独立的正式无效判定。渲染与CSV统一按 GetResultV2 的 tip/full 标志和 CopyPath，不能按 status 字面删除这个实际错误输出来让视频更好看。
