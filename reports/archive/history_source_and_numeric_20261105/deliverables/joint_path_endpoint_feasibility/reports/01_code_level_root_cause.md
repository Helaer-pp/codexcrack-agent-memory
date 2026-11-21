# 代码级最早失效环节

本轮没有人工真值，真实图仅定位“算法决策在哪一环发生分歧”，不能把未确认一律解释为物理漏检。所有路径与分数均来自实际DLL输出；下表包含原文件名/frame_id/模式/版本SHA，完整证据在对应native/stage JSONL。

## CONFIRMED_BY_EXPERIMENT

1. 极弱线先死于seed。`src/CrackV4.cpp`既有seed阶段在新搜索之前；生成weak_6端到端5帧均no_seed，候选新DP没有机会运行；不能通过末端细化解决。独立局部graph weak6的可运行性只属于已给正确起始位置的诊断，不能等同端到端成功。实际记录：tests/synthetic_v4/end_to_end.json。
2. 联合终止引入新误伤。`src/CrackV4.cpp:1963–1971`要求图内终止且旧terminalAudit不提示向前续接/宽度异常。在生成curve_90中，稳定/M3可确认、M4/M5被joint_stop_forward_conflict否决；不应算“纠正长尾”。开发组H409个当前帧中239个forward_conflict、124个tip_uncertain，46个no_candidate，完整确认0。
3. 12px gap约束并不保证跨过12px物理间隙。`src/JointPath.hpp:145–162`按每列负证据累计gap，二阶约束和弯曲边缘也会增加负列；`ForwardStopEvidence:107–117`的有界向前支持仍可在gap附近失败。生成gap_12第5帧错误确认[327.02,361.23]，误差208.437px，长度少206.103px；短gap4/8通过。它是合成已知真值的严重假尖端。
4. K不等于全局分支恢复。`src/JointPath.hpp:128–170`以顺序排斥产生几何不同的次优候选，`src/CrackV4.cpp:1833`始终选candidates[0]；各tile仍每48px前进。当前K1/2/3在四组1991张结果数值完全相同（仅排除耗时），额外分支未参与跨tile选择；生成fork的GT终点亦未在候选中。H2本次实现未证明可行。
5. CT2几何细化会导致较大路径分歧：367个两种模式共同确认帧的尖端差P95=127.213878px、Max=133.902312px。它是算法间差异，物理正确方向无GT不能判定。
6. 自动配准可返回成功但几何失准：开发组H源frame_id=12，本次相对实测双点残差65.986531px，状态REGISTRATION_VALID。新路径模型未改变这部分；不能把新输出不确定误报成配准修复。外部实测点输入与自动模式分开记录。

## SUPPORTED_HYPOTHESIS

`src/JointPath.hpp:77–86`的min(横截面、新增差异)、背景扣分和Hessian符号约束组合可能压制宽线、弱线、曲线；生成已有参考裂纹和镜像案例确有退化，但尚缺足够真实GT/逐项受控消融，不能把所有真实拒绝归因于某一项。参考已有裂纹使用absolute分支并非必然差分否决，当前端到端仍失败。

`src/JointPath.hpp:138–140`平均分与停止奖励消除了纯累计长度奖励，但可能偏爱局部短高分段，尚未证明全局无偏。新增划痕与断裂线若光度相同，局部证据不能单独证实材料断裂。

## NOT_VERIFIED / 明确边界

无真实GT，不能给每个分歧帧指定“真正首次偏离位置”。H4仅记录持续分歧，没有执行恢复；H5未执行新亚像素细化；SAFE_TEMPORAL独立新策略未准入。未确认状态仍沿用旧seed的NO_CRACK语义，不能声称所有证据不可用情况都已正确区分。阶段计时并未把result_fill单独隔离。

实例分数：

| group | frame_id | image_filename | mode | dll_sha256 | old_full | new_full | stop | state | stop_margin | graph_count | feature_samples | positive_llr | unavailable | physical_correctness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | 57 | 20240328171347309-572.bmp | M5_JOINT_K2 | a576a4f77bbac6b9364745edf972f1e3064186af82e9c1743d44e08c9c628a5f | True | False | joint_stop_forward_conflict | PATH_SUPPORTED_TIP_UNCERTAIN | 0.3218622727112638 | 1 | 1 | 0 | 0 | N/A |
| group_c | 18 | 1 (19).bmp | M5_JOINT_K2 | a576a4f77bbac6b9364745edf972f1e3064186af82e9c1743d44e08c9c628a5f | True | False | joint_absorbing_stop | PATH_SUPPORTED_TIP_UNCERTAIN | 1.1252380230857266 | 1 | 5 | 3 | 0 | N/A |
| ct2 | 2 | 20241101162904919-1866.bmp | M5_JOINT_K2 | a576a4f77bbac6b9364745edf972f1e3064186af82e9c1743d44e08c9c628a5f | True | False | joint_stop_forward_conflict | PATH_SUPPORTED_TIP_UNCERTAIN | 0 | 1 | 1 | 0 | 0 | N/A |
| group_h | 42 | 20250314144138112-36.bmp | M5_JOINT_K2 | a576a4f77bbac6b9364745edf972f1e3064186af82e9c1743d44e08c9c628a5f | True | False | joint_tip_uncertain | PATH_SUPPORTED_TIP_UNCERTAIN | 0 | 1 | 1 | 0 | 1 | N/A |

四组最终门控原因（包含所有当前帧）：

| group | joint_absorbing_stop | joint_stop_forward_conflict | joint_tip_uncertain | no_candidate |
| --- | --- | --- | --- | --- |
| group_a | 128 | 355 | 18 | 49 |
| group_c | 362 | 170 | 14 | 15 |
| ct2 | 284 | 172 | 11 | 0 |
| group_h | 0 | 239 | 124 | 46 |

新鲜实例与闭环输出的可执行对照见tests/temporal_fresh_vs_closed_loop.json；帧序索引自然不同，仅比较尖端/有效位/路径决策。此对照无需GT即可执行，但哪种结果物理正确仍N/A。
