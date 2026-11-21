# 后缀与确认回退排查

DP累计分数包含历史主体奖励，终点累计分数高不能证明新增后缀仍有暗线。旧v3把多个局部证据不足情况提升为硬拒绝，净失去336个完整确认；不能将这336帧全部当成人工已证实的误拒。

本轮保留DP，沿候选做当前暗谷、参考差分、Hessian方向与可用性采样。变化点为持续证据损失位置，不自动等同物理尖端。稳定版的旧确认若未触发新审计可能保留，因此新模块也没有证明杜绝无证据追踪。

逐帧336清单：../tests/v3_lost336.json。全部变化：../tests/changed_frames.json。原图ROI及完整证据曲线：../review/evidence/index.html。无人工真值，不能为每条实际后缀下“真实错误/真实延续”结论。

| group | old_net_lost | new_restored | new_lost | new_gained | cp |
| --- | --- | --- | --- | --- | --- |
| group_a | 69 | 69 | 0 | 0 | 0 |
| group_c | 95 | 95 | 0 | 0 | 0 |
| ct2 | 122 | 119 | 4 | 57 | 0 |
| group_h | 50 | 50 | 0 | 0 | 0 |

旧v3净损失集合的自动状态分类（这是程序原因，未由人工确认误拒）：

|组|v3停止|v3末端|新完整有效|帧数|
|---|---|---|---|---:|
| group_a | evidence_ended | current_trace_continues | True | 50 |
| group_a | evidence_ended | current_trace_terminal_uncertain | True | 16 |
| group_a | temporal_pending | current_trace_continues | True | 1 |
| group_a | trace_support_lost | trace_support_lost | True | 2 |
| ct2 | evidence_ended | current_trace_continues | False | 3 |
| ct2 | evidence_ended | current_trace_continues | True | 56 |
| ct2 | evidence_ended | current_trace_terminal_uncertain | True | 20 |
| ct2 | trace_support_lost | trace_support_lost | True | 43 |
| group_h | evidence_ended | current_trace_continues | True | 21 |
| group_h | evidence_ended | current_trace_terminal_uncertain | True | 22 |
| group_h | temporal_pending | current_trace_terminal_supported | True | 1 |
| group_h | trace_support_lost | trace_support_lost | True | 6 |
| group_c | evidence_ended | current_trace_continues | True | 40 |
| group_c | evidence_ended | current_trace_terminal_uncertain | True | 36 |
| group_c | temporal_pending | current_trace_continues | True | 2 |
| group_c | temporal_pending | current_trace_terminal_supported | True | 4 |
| group_c | temporal_pending | current_trace_terminal_uncertain | True | 12 |
| group_c | trace_support_lost | trace_support_lost | True | 1 |

CT2新增4个相对稳定版丢失完整确认的程序原因：frame_id=26、32、59、77。四帧根部均仍有效，局部重定位也找到终点，但全路径证据可用比例分别为0.5133、0.4967、0.5033、0.5166，低于预先固定的0.7，故unknown=true，tip/full被清零。这不是12px根部连接失败，也不是CP裁剪；包含过曝/剖面不可用处理的保守影响。是否属于真实误拒仍需独立GT。未在冻结后修改阈值。
