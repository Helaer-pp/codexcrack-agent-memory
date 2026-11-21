# 自动检查结果

```json
{
  "production_source_and_DLL": "PASS",
  "all_frame_state_and_double_CopyPath_exact": 2515,
  "three_independent_states": "PASS",
  "integer_code_histograms_checked": 12281,
  "known_GT_cases_and_decisions": [
    960,
    15360
  ],
  "LOGO_selection_no_TEST_feedback": "PASS; all LEGACY",
  "prior_first_failure_counts_reaudited": "PASS; exact current-only attempt and accepted counts",
  "CT2_controls_and_grid": "PASS; 64 controls, 1216 trials, 337 exact reconstructed tiles",
  "480_archive_compatibility_and_exceptions": "PASS",
  "additional_digital_controls": {
    "photometric": 140,
    "known_motion_DP": 360
  },
  "full_video_decode_and_hash": "PASS",
  "HTML_broken_links": [],
  "performance_no_record_excluded": 2510
}
```

异常输入、旧接口、确定性、合成回归原始结果见regression.json。研究正对照、所有失败记录均保留。无真实物理尖端GT，不报告真实precision/recall。
