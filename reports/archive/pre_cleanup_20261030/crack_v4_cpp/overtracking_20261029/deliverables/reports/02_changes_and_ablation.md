> 用户最新约束：第五组排除组X是独立实验，禁止参与算法调优。v1/v2/v3在澄清前已观察51/473，现全部退出正式候选；其第五组输出仅作排查记录，不能称独立验证。正式独立实验只采用见第五组之前已冻结的旧发布算法。新版本选择仅可依据原四组+合成测试，本轮四组回归未通过，因此不发布算法变更。

# 最小开关与消融

新增4096横截面支撑审计和8192合格路径历史；原DP选路/根部连接12px/配准/平滑/默认0及3572不变。新增只读版本1 JSON查询，不改旧struct布局。

支撑审计每2点取原图横截面±20px、局部MAD噪声和多宽度双侧暗谷，SNR≥2.5作为局部证据。8采样/块、至少5点支撑；连续2弱块才截去后缀。该阈值是实验参数，不是已验证通用尺度。保留candidate，supported_prefix分开，不使用固定长度上限或单调增长。新末端独立采当前图前方4/8/12/16px、五条局部方向射线，检查暗线是否继续。

v1要求历史端点先合格会抑制弱裂纹启动，已否决。v2将旧DP末端审查硬门控，旧组大幅丢确认，已否决。v3改用当前灰度横截面，但仍有覆盖损失，故也不进入生产。全部v1/v2真实结果保存在results/trial_v1及results/final，v2 DLL为build_final；可复现最终v3源码/DLL为交付bin。

| 组 | 配置 | 尖端 | 完整 | 截断 | 首次确认 |
|---|---|---|---|---|---|
| group_a | FROZEN_CURRENT | 497 | 496 | 0 | 49 |
| group_a | BASELINE_ANCHOR_SHADOW | 497 | 496 | 0 | 49 |
| group_a | CANDIDATE_SHADOW | 428 | 427 | 2 | 58 |
| group_a | CANDIDATE_OFF | 497 | 496 | 0 | 49 |
| group_a | CANDIDATE_VERIFIED_DIAGNOSTIC | 390 | 389 | 2 | 58 |
| group_a | PATH_ONLY | 428 | 427 | 2 | 58 |
| group_a | HISTORY_ONLY | 497 | 496 | 0 | 49 |
| group_c | FROZEN_CURRENT | 543 | 543 | 0 | 18 |
| group_c | BASELINE_ANCHOR_SHADOW | 543 | 543 | 0 | 18 |
| group_c | CANDIDATE_SHADOW | 448 | 448 | 1 | 29 |
| group_c | CANDIDATE_OFF | 543 | 543 | 0 | 18 |
| group_c | CANDIDATE_VERIFIED_DIAGNOSTIC | 403 | 403 | 1 | 27 |
| group_c | PATH_ONLY | 452 | 452 | 1 | 23 |
| group_c | HISTORY_ONLY | 543 | 543 | 0 | 18 |
| ct2 | FROZEN_CURRENT | 403 | 403 | 0 | 1 |
| ct2 | BASELINE_ANCHOR_SHADOW | 403 | 403 | 0 | 1 |
| ct2 | CANDIDATE_SHADOW | 281 | 281 | 43 | 3 |
| ct2 | CANDIDATE_OFF | 403 | 403 | 0 | 1 |
| ct2 | CANDIDATE_VERIFIED_DIAGNOSTIC | 196 | 196 | 43 | 3 |
| ct2 | PATH_ONLY | 281 | 281 | 43 | 3 |
| ct2 | HISTORY_ONLY | 403 | 403 | 0 | 1 |
| group_h | FROZEN_CURRENT | 345 | 344 | 0 | 42 |
| group_h | BASELINE_ANCHOR_SHADOW | 345 | 344 | 0 | 42 |
| group_h | CANDIDATE_SHADOW | 295 | 294 | 6 | 42 |
| group_h | CANDIDATE_OFF | 345 | 344 | 0 | 42 |
| group_h | CANDIDATE_VERIFIED_DIAGNOSTIC | 235 | 234 | 6 | 44 |
| group_h | PATH_ONLY | 296 | 295 | 6 | 42 |
| group_h | HISTORY_ONLY | 345 | 344 | 0 | 42 |
| group_x | FROZEN_CURRENT | 269 | 263 | 0 | 26 |
| group_x | BASELINE_ANCHOR_SHADOW | 269 | 263 | 0 | 26 |
| group_x | CANDIDATE_SHADOW | 58 | 58 | 286 | 26 |
| group_x | CANDIDATE_OFF | 269 | 263 | 0 | 26 |
| group_x | CANDIDATE_VERIFIED_DIAGNOSTIC | 68 | 68 | 286 | 26 |
| group_x | PATH_ONLY | 82 | 82 | 286 | 26 |
| group_x | HISTORY_ONLY | 260 | 254 | 0 | 26 |

Shadow保留旧语义；新开关主动增加正式输出门控。Verified为独立诊断分支，不自动等于准确。无AUTO全组试验：全部已有实测点，只有case单帧诊断比较AUTO/no_refine。
