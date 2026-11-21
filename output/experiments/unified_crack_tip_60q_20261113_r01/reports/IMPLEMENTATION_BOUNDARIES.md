# 实际实现与验收边界

| requirement | status | evidence |
|---|---|---|
| 1633 complete frames and 12343 mode outputs | PASS | manifests/*inference_seal.json; reports/final_integrity.json |
| RAW1px/2px, current max-x branch, retreat, jump review, independent reference masks | PASS_SYNTHETIC_CONTRACTS | reports/synthetic_tests.txt |
| Original-source numeric replay and deterministic sequence state | PASS_CHECKED_SAMPLES | diagnostics/*determinism_and_source.csv; 30 source frames + 9 sequential replay frames |
| Independent batch execution matches original scalar semantics | PASS_133_NATIVE_CHECKPOINTS_AND_15_SYNTHETIC | qa/batch_backend_contract.json; qa/batch_backend_native_parity.csv; reports/EXECUTION_BACKEND_EQUIVALENCE.md |
| Physical crack identity / detached dark stroke safety | FAIL | synthetic_risk_probes_extended/static_detached_dark_stroke_near_origin/result.json.gz |
| Strict pre-freeze group_c input isolation | FAIL_WITH_DISCLOSED_DEVIATION | reports/PROTOCOL_DEVIATION.md |
| Budget exhaustion never promoted to an official endpoint | PASS_CHECKED_FRAMES | diagnostics/all_frame_integrity.csv |
| Hard worst-case memory guarantee before neighbor proposal enumeration | NOT_PROVEN | graph.py enumerates spatial neighbor pairs before the final pair budget cap |
| Three-group frozen accuracy gates | FAIL | offline_evaluation/DEV_metrics.csv; LOCKED_metrics.csv |
| C++ parity | NOT_IMPLEMENTED_NOT_CLAIMED | Python-only implementation permitted by task |
| Registration quality proxy interpretation | POST_FIT_SUBSET_CHECK_ONLY | holdout_ncc is a post-fit interleaved subset consistency check, not independent holdout |
| Physical notch and deformation-field ground truth | UNRESOLVED | Image hypotheses / local texture quality only |
| Batch evidence adapter for invalid current P1/P2 | FAIL_FAST_ADAPTER_LIMITATION | Engine supports historical-geometry degradation in synthetic tests; stateless pipeline.prepare_one rejects invalid real P instead of adapting it |
| Real-browser interactive viewer verification | NOT_VERIFIED_TOOL_POLICY_BLOCK | qa/browser_interaction_attempt.json; Node DOM contracts and image inspection passed separately |
| Preserve historical source, DLL and sealed results | PASS | reports/final_integrity.json |

M4的图首先提出当前RAW/方向/间断支持的几何连接，参考变化在整条候选路径身份验证中消费；不声称边提案本身具有独立参考分类器。每个有向段保留词典序最优前驱，其他前驱保存为拒绝血缘；这不是所有路径的穷举。开口只作用于不确定候选弱平局，未影响正式结果时如实报告。动态工作掩膜仍需完整安全区RAW scout，因此不能声称减少全部特征成本。核心Engine.process具备P点降级与历史几何支持，但当前无历史批量证据缓存入口prepare_one遇非法P会明确停止；不能将核心合成测试等同批入口已覆盖所有异常输入。当前三组是否存在此类输入，以实际prepare完成记录为准。

“完成研究代码和实验交付”不等于全部规范验收通过。独立暗线误输出、隔离执行偏差、极端内存保证和物理真值缺口均保留，禁止发布为生产替代。
