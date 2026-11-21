# UCTT Phase 1 audit / decoupling

- G0 PASS
- G1 PASS
- G2 PASS
- G3 PASS
- T1 PASS for valid current-anchor perturbations (12874 executed, state/coordinate mismatches 0/0, P95=max 0 px)
- T2 BLOCKED: initial-anchor reinitialization matrix not completed
- T3 PASS at interface/status level; no physical GT
- T4 BLOCKED: no unseen holdout with manual GT
- T5 FAIL: measured historical end-to-end P95 exceeds 50 ms on several groups
- T6 PASS for smoke/ABI layout checks; external host integration not run

See `development_report.md`, `dependency_audit.md`, `change_plan.md`, and `strict_report.md`.

`baseline_results.csv` is the historical frozen A; its differences from the candidate reflect the earlier ROI-tip release evolution, not the current invalid-anchor patch.


