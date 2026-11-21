# Zero Ground Truth Leakage Audit Protocol

## 1. Architectural Guardrails
1. **Module Isolation**:
   - `geminicode/src/engine.py` and all sub-modules receive only raw image arrays, anchor coordinates, and state history.
   - None of the inference modules import or have access to `labels.zip`, `selected_frames.csv`, or ground truth paths.
2. **Offline Evaluator Separation**:
   - `geminicode/scripts/evaluate.py` is invoked strictly after inference CSV/JSONL results are flushed to disk.
   - The evaluator never writes back into the prediction files or feeds scores into subsequent frame iterations.
3. **group_c Holdout Guard**:
   - group_c images and anchors are held sealed until after the prevalidation freeze.
   - All algorithm rules, thresholds, and hyperparameters are finalized using DEV (GROUP_A and Three-point-bend) only.
