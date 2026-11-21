# 发布判定

{
  "decision": "KEEP_A / C2_RESEARCH_ONLY",
  "DEV_effect_passed": false,
  "TEST_effect_passed": false,
  "TEST_damaged_A_correct": 2,
  "CPP_C2": "NOT_BUILT",
  "real_holdout": "NOT_AVAILABLE",
  "physical_precision": "N/A",
  "A_DLL_sha256": "c23498fcc660469927f63244b8e98e39b1eb86d542ec9a7b069d61fcf813654b",
  "production_modified": false,
  "TEST_once_only": true,
  "TEST_after_DEV_failure": "FROZEN_EXPLORATORY_VALIDATION",
  "guard_checked_utc": "2026-11-04T14:51:54.225604+00:00"
}

以零正确A损害为硬门槛，本轮失败；平均风险改善不能抵消2帧错误截断。无C2 DLL，不替换现有SDK，不宣称C2完整原生15Hz。