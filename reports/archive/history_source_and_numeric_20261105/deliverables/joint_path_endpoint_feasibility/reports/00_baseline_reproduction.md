# 实物身份与基线复现

| group | images | current | stable_full | failed_research_full | v3_full | numeric_differences |
| --- | --- | --- | --- | --- | --- | --- |
| group_a | 551 | 550 | 496 | 496 | 427 | 0 |
| group_c | 562 | 561 | 543 | 543 | 448 | 0 |
| ct2 | 468 | 467 | 403 | 456 | 281 | 0 |
| group_h | 410 | 409 | 344 | 344 | 294 | 0 |

固定DLL的SHA与源码Git身份见 config/baseline_identity.json；实际复现日志见 tests/dev4_replay.log。历史结果已应用户清理要求删除，不能对已删除旧JSONL做字节比较；本次重新独立时序运行三份冻结DLL。新DLL flags3572与EVIDENCE_ONLY和稳定DLL同帧逐项数值一致（仅排除耗时）。原四组当前帧应为1987，本次实际为1987。

原v3净失336的集合本次重新计算为336，逐张照片见 data/v3_lost336.csv。原13场景260次观察的脚本现已从清理前源码备份中恢复，并在冻结V3_REJECTED DLL上完整重跑：准确复现2项原断言失败，distractor_retains_true_short_crack与large_turn_retained。实际数据见tests/historical_v3_13cases.json，脚本SHA256为53fd32809b23dcf5ffb3bb4bec860985d5dead6d0928bdcf5c8d8e5508c86150。历史原JSON仍已删除，本次结果为独立重新执行，未削弱断言。CT2 refinement差异见 data/anchor_refinement_differences.csv，该值不是GT误差。历史自动配准失败编号清单已清理，故原27+5集合精确成员复现标为数据缺失；本轮故障注入若运行则另存。
