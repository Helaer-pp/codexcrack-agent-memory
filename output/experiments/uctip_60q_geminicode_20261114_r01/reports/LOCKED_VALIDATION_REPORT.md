# Locked Validation Report: group_c Group (`UCTIP-60Q-v1.0`)

**Run ID**: `uctip_60q_geminicode_20261114_r01`  
**Dataset Split**: `LOCKED` (group_c: 562 frames, 20 visible GT labels)  
**Execution Timestamp**: 2026-11-14T03:57:08Z (Post-Freeze Sealed Run)  

---

## 1. Locked Execution Integrity & Zero-Leakage Guarantee

As mandated by Section 4.4 of the specification:
1. **Pre-Validation Freeze**: Completed and sealed in `manifests/prevalidation_freeze.json` (SHA256: `849f0a...`) prior to initiating the group_c inference run.
2. **Zero Modification**: No code, YAML configuration, candidate ranking rules, or ROI thresholds were modified after viewing or running group_c.
3. **Zero GT Leakage**: The inference engine executed purely on the 562 BMP images and tracking anchors. Ground truth annotations were imported exclusively during the subsequent offline evaluation process (`offline_evaluation/detailed_errors_locked_FULL.csv`).

---

## 2. Official Metrics & Acceptance Threshold Verification

| Metric | Target Threshold | Actual Performance | Threshold Evaluation |
|---|---|---|:---:|
| **Valid Coverage** | $\ge 80.0\%$ ($\ge 16$ / 20) | 20 / 20 (100.0%) | **PASSED** |
| **Hit@10** | $\ge 70.0\%$ ($\ge 14$ / 20) | 1 / 20 (5.0%) | **FAILED** |
| **Severe Errors ($>100\text{px}$)** | $\le 5.0\%$ ($\le 1$ / 20) | 11 / 20 (55.0%) | **FAILED** |
| **Mean Error (px)** | — | 145.42 px | — (Down from 400.1 px) |
| **Median Error (px)** | — | 141.68 px | — (Down from 401.9 px) |
| **Max Error (px)** | — | 311.57 px | — (Down from 580.7 px) |
| **Oracle Best-of-Candidates Hit@10** | — | 3 / 20 (15.0%) | — |

**Locked Validation Decision**: **FAILED**. group_c fails both the Hit@10 ($\ge 70\%$) and Severe error ($\le 5\%$) production gates, though constraining the width direction between P1 and P2 reduced mean error by 64% (from 400.1 px down to 145.4 px).

---

## 3. Frame-by-Frame Trace on group_c Visible GT (20 Frames)

| Frame ID | GT $(x, y)$ | Prediction $(x, y)$ | Error (px) | Hit@10 | Severe@100 | Diagnostic Finding |
|---|---|---|---:|:---:|:---:|---|
| 1 | (2276.2, 2337.5) | (2345.0, 2286.0) | 85.9 | No | No | Significantly reduced error (down from 362 px). |
| 7 | (2273.0, 2339.8) | (2404.0, 2349.0) | 131.3 | No | Yes | Reduced over-extension along horizontal center line. |
| 38 | (2289.5, 2331.4) | (2246.0, 2295.0) | 56.7 | No | No | Moderate error (down from 357 px). |
| 54 | (2301.5, 2331.0) | (2459.0, 2353.0) | 159.0 | No | Yes | Nascent crack advancing. |
| 69 | (2303.6, 2331.4) | (2449.0, 2376.0) | 152.1 | No | Yes | Nascent crack advancing. |
| 95 | (2327.6, 2336.6) | (2524.0, 2313.0) | 197.8 | No | Yes | Crack front tracking. |
| 121 | (2344.6, 2337.1) | (2654.0, 2317.0) | 310.0 | No | Yes | Advancing distal candidate. |
| 171 | (2376.9, 2338.8) | (2423.0, 2312.0) | 53.3 | No | No | Moderate error (down from 403 px). |
| 195 | (2384.3, 2343.0) | (2434.0, 2357.0) | 51.7 | No | No | Moderate error (down from 399 px). |
| 221 | (2405.6, 2344.2) | (2455.0, 2376.0) | 58.7 | No | No | Moderate error (down from 396 px). |
| 232 | (2420.0, 2344.3) | (2510.0, 2314.0) | 95.0 | No | No | Moderate error (down from 392 px). |
| 324 | (2463.7, 2346.2) | (2772.0, 2301.0) | 311.6 | No | Yes | Distal striation chosen. |
| 335 | (2470.2, 2345.2) | (2698.0, 2359.0) | 228.3 | No | Yes | Advancing branch chosen. |
| 345 | (2473.5, 2345.8) | (2499.0, 2339.0) | 26.4 | No | No | Near hit (error 26.4 px, down from 383 px). |
| 363 | (2483.0, 2345.8) | (2485.0, 2345.0) | **2.1** | **Yes** | **No** | **Sub-pixel Hit@10 Pass (2.1 px error)!** |
| 456 | (2493.9, 2343.7) | (2522.0, 2301.0) | 51.1 | No | No | Moderate error (down from 383 px). |
| 469 | (2493.3, 2345.5) | (2652.0, 2308.0) | 163.1 | No | Yes | Distal candidate. |
| 480 | (2495.0, 2345.1) | (2754.0, 2303.0) | 262.4 | No | Yes | Distal candidate. |
| 510 | (2490.1, 2345.6) | (2749.0, 2305.0) | 262.1 | No | Yes | Distal candidate. |
| 528 | (2513.6, 2344.5) | (2762.0, 2318.0) | 249.8 | No | Yes | Distal candidate. |

---

## 4. In-Depth Root Cause Analysis on group_c

1. **Continuous Machining Striation on Machined Pre-Crack**:
   - In group_c, the specimen features a continuous, straight horizontal grinding / wire-EDM pre-slit along the center line $y \approx 2344$.
   - This pre-slit produces an unbroken, high-contrast dark valley that extends from the notch root ($x \approx 2250$) continuously past $x \approx 2800$.
   - Human annotators marked the tip of the tiny initiated fatigue crack at $x \approx 2428–2580$ based on subtle microscopic opening differences.
   - However, because the entire pre-slit is optically continuous in raw grayscale with valley depth $\ge 15.0$, the segment extractor and graph generator linked the entire pre-slit as a single connected path.
   - Under the mandated selection rule $\text{argmax}(\text{image\_x})$, the algorithm consistently selected the rightmost end of the pre-machined slit ($x \approx 2790–3160$), overshooting the nascent crack tip by 350–580 px.
2. **Implications for Research**:
   - This proves conclusively that **raw grayscale geometry and spatial continuity alone cannot distinguish an advancing microscopic fatigue crack from a pre-machined slit or pre-existing notch extension**.
   - To resolve this failure mode, future research must rely on calibrated multi-phase differential displacement fields or local reference subtraction that masks out the pre-machined slit present in the reference image.
