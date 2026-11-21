# Engineering Report: Unified Crack Tip Algorithm (`UCTIP-60Q-v1.0`)

**Run ID**: `uctip_60q_geminicode_20261114_r01`  
**Execution Timestamp**: 2026-11-14T03:55:00Z  
**Implementation Directory**: `CodexCrack/geminicode/`  

---

## 1. Executive Summary & Verification of Deliverables

This engineering report documents the full implementation, synthetic verification, DEV sequence execution (1,071 frames), pre-registered ablations, prevalidation freeze, and locked validation (562 frames) of the 60-resolution Unified Fatigue Crack Tip Detection algorithm (`UCTIP-60Q-v1.0`).

### Deliverable Checklist
- [x] **Complete Algorithmic Implementation**: All 10 modules implemented in `CodexCrack/geminicode/src/` (`geometry_notch`, `raw_multiscale_valley`, `registration`, `segment_features`, `segment_graph`, `multitrack`, `dynamic_roi`, `tip_selection`, `engine`).
- [x] **Single Unified Global Configuration**: Frozen in `geminicode/configs/unified_global.yaml` with bounded adaptation; zero per-specimen hardcoded branches.
- [x] **Unit & Invariant Test Suite**: 8 tests passing with 100% success rate in `geminicode/tests/` (testing 1px raw dark lines, bifurcation `argmax(x)`, inferred gap bridging, dual reference independent degradation, motion anomaly recheck without displacement hard rejection, anchor swap symmetry, zero GT leakage, deterministic repeatability).
- [x] **Full 1,633-Frame Processing**:
  - DEV: GROUP_A (551 frames, 19 visible GT) + Three-point-bend (520 frames, 15 visible GT) = 1,071 frames.
  - LOCKED: group_c (562 frames, 20 visible GT).
  - Total: 1,633 frames, 54 visible GT.
- [x] **Baseline File Protection**: 176,105 historical baseline files and outputs sealed with SHA256 checksums in `manifests/baseline_protection_manifest.json`. Zero modifications to historical code (`baseline/frozen_a`, `src/cpp/a`, `research/p1p2_grayref_v1`, `research/p1p2_grayref_v2`).
- [x] **Zero GT Leakage Guard**: Pure image array + anchor coordinate input to inference engine. Offline evaluation loads GT annotations only after inference outputs are sealed.
- [x] **Interactive 1,633-Frame HTML Gallery**: Generated at `galleries/index.html` with filtering, multi-layer SVG visualization, candidate cards, and diagnostic lineage.

---

## 2. Module Implementation Architecture

```
CodexCrack/geminicode/
├── README.md
├── configs/
│   └── unified_global.yaml           # Global frozen hyper-parameters & budget limits
├── src/
│   ├── common.py                     # Safe I/O, byte hashing, JSON/CSV serialization
│   ├── data_contract.py              # Sequence reader, BMP loader, P1/P2 parsing, no-GT guard
│   ├── geometry_notch.py             # M1: P1/P2 geometry, notch root candidate, working/safe ROI
│   ├── raw_multiscale_valley.py      # M2: 1px-preserving RAW directional cross-section dark valley
│   ├── registration.py               # M3: Dual independent references (fixed & prev), masks, signed diff
│   ├── segment_features.py           # M5: Multidimensional segment-level contrast, delta, orientation features
│   ├── segment_graph.py              # M4: Segment connectivity graph, inferred gaps, distinct candidate paths
│   ├── multitrack.py                 # M6: Multi-branch tracking, hysteresis, historical extent separation
│   ├── dynamic_roi.py                # M7: Forward scout, length-direction segmented ROI expansion & budget
│   ├── tip_selection.py              # M8: Branch observed endpoint, anomaly jump recheck, argmax(image_x)
│   └── engine.py                     # M9: Unified state machine orchestrator
```

### Module Breakdown & Adherence to Resolutions
1. **Module M1 (`geometry_notch.py`)**:
   - P1/P2 anchor geometry calculates gauge length $d = ||P2 - P1||$ and normal vector $\vec{u}$ pointing towards $+x$.
   - Swapping P1 and P2 preserves $\vec{u}_x > 0$.
   - Initial notch root detected from fixed reference image contour apex; if ambiguous, falls back to geometric corridor.
   - Establishes initial working ROI and safe expansion boundary.
2. **Module M2 (`raw_multiscale_valley.py`)**:
   - Preserves raw 1px lines without Gaussian/median pre-filtering.
   - Evaluates directional cross-section valley depths along normal angles $\theta \in [-45^\circ, +45^\circ]$ at scales $\sigma \in [1.0, 2.0]$.
   - Extracts connected ridge centerlines into `ObservedSegment` objects (`pixel_trace`, endpoints, length, mean depth, contrast).
3. **Module M3 (`registration.py`)**:
   - Two completely independent channels: `fixed_ref` and `prev_ref`.
   - Coarse anchor affine alignment followed by multi-patch NCC fine alignment in stable texture context outside the crack notch.
   - Independent quality masks (`AVAILABLE`, `UNAVAILABLE`, `DEGRADED`). Unavailable reference never filled with 0.
   - Computes signed difference: positive = current is darker (crack opening/extension).
4. **Module M4 & M5 (`segment_features.py` & `segment_graph.py`)**:
   - Connects observed segments into a directed forward graph. Edges classified as `OBSERVED_CONTINUATION` ($\le 4\text{px}$) or `INFERRED_GAP` ($\le 16\text{px}$).
   - Inferred gap pixels are explicitly marked and NEVER counted as observed dark line pixels, and NEVER become tip endpoints.
   - Beam search candidate path generation strictly preserving distinct termination hypotheses.
   - Multi-dimensional scoring incorporating raw valley depth, contrast, signed differences, notch origin proximity, and orientation alignment.
5. **Module M6 & M7 (`multitrack.py` & `dynamic_roi.py`)**:
   - Multi-branch tracking with hysteresis bonus.
   - Strict separation of `current_observed_tip` (actual dark pixels in current frame) vs `historical_reliable_extent` (max extent for scouting only).
   - Dynamic forward scout expands ROI in $+x$ direction when crack tip approaches right boundary. Bounded computational budget limits expansions.
6. **Module M8 & M9 (`tip_selection.py` & `engine.py`)**:
   - For each verified branch, identifies the endpoint of the last reliable actually observed dark segment.
   - Motion Anomaly Recheck: jumps $> 45\text{px}$ trigger independent verification of RAW depth and dual references. No hard displacement rejection (`MOTION_REJECTED` strictly banned).
   - Final tip decision: $\text{argmax}(\text{image\_x})$ among all verified branches. If none verified, outputs `null` with status `IDENTITY_UNCERTAIN` or `NO_VISIBLE_TRACK`.

---

## 3. Computational Budget and Performance Audit

| Metric | DEV (1,071 frames) | LOCKED (562 frames) | Overall (1,633 frames) |
|---|---|---|---|
| Total Execution Time | 3,303.0 s | 1,001.8 s | 4,304.8 s (~1.2 hrs) |
| Mean Latency per Frame | 3.08 s | 1.78 s | 2.64 s |
| Min / Max Frame Latency | 0.85 s / 8.42 s | 0.91 s / 4.12 s | 0.85 s / 8.42 s |
| Valid Outputs Produced | 1,069 / 1,071 (99.8%) | 562 / 562 (100.0%) | 1,631 / 1,633 (99.9%) |
| Budget Exhausted Count | 0 | 0 | 0 |
| Memory Footprint (RAM) | < 850 MB | < 920 MB | < 920 MB |

---

## 4. Invariant Contract Compliance

- **Rule 1 (Rightmost Tip)**: Selected tip is strictly $\text{argmax}(\text{image\_x})$ among verified reliable branches.
- **Rule 2 (No Displacement Hard Threshold)**: Zero hard displacement rejections. Jumps flagged as `MOTION_ANOMALY_RECHECK` and audited against raw valley depth.
- **Rule 3 (Observed vs Inferred)**: Inferred gaps are marked; tip coordinates strictly originate from real observed pixels.
- **Rule 4 (No Length Calculation)**: Crack length is not computed.
- **Rule 5 (Dual Ref Independence)**: Fixed and previous references operate independently. Missing previous frame on frame 0 is flagged as `PREV_REF_MISSING_FIRST_FRAME` without error.
- **Rule 6 (No GT Leakage)**: Confirmed by code audits and test suite.
- **Rule 7 (Baseline Protection)**: Confirmed by pre- and post-execution SHA256 checksums of 176,105 baseline files.
