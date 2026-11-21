# Development Report: DEV Sequences Analysis (`UCTIP-60Q-v1.0`)

**Run ID**: `uctip_60q_geminicode_20261114_r01`  
**Dataset Split**: `DEV` (GROUP_A: 551 frames; Three-point-bend: 520 frames; Total: 1,071 frames)  
**Visible Ground Truth**: 34 frames (GROUP_A: 19, Three-point-bend: 15)  

---

## 1. Overall DEV Performance Metrics

| Group | Split | Total Frames | Visible GT ($N$) | Valid Outputs ($M$) | Coverage | Hit@3 | Hit@5 | Hit@10 | Hit@20 | Severe ($>100\text{px}$) | Mean Err (px) | Median Err (px) | Oracle Hit@10 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **GROUP_A** | DEV | 551 | 19 | 19 | 100.0% | 2 (10.5%) | 2 (10.5%) | **3 (15.8%)** | 3 (15.8%) | 9 (47.4%) | 95.61 | 95.96 | 4 (21.1%) |
| **Three-point-bend** | DEV | 520 | 15 | 15 | 100.0% | 0 (0.0%) | 0 (0.0%) | **0 (0.0%)** | 0 (0.0%) | 13 (86.7%) | 206.39 | 239.05 | 0 (0.0%) |
| **DEV Combined** | DEV | 1,071 | 34 | 34 | 100.0% | 2 (5.9%) | 2 (5.9%) | **3 (8.8%)** | 3 (8.8%) | 22 (64.7%) | 144.49 | 120.96 | 4 (11.8%) |

---

## 2. Formal Threshold Verification on DEV

| Group | Visible GT ($N$) | Metric | Target Threshold | Actual Performance | Threshold Evaluation |
|---|---:|---|---|---|:---:|
| **GROUP_A** | 19 | Coverage | $\ge 80.0\%$ ($\ge 16$ frames) | 19 / 19 (100.0%) | **PASSED** |
| | | Hit@10 | $\ge 70.0\%$ ($\ge 14$ frames) | 3 / 19 (15.8%) | **FAILED** |
| | | Severe@100 | $\le 5.0\%$ ($0$ frames) | 9 / 19 (47.4%) | **FAILED** |
| **Three-point-bend** | 15 | Coverage | $\ge 80.0\%$ ($\ge 12$ frames) | 15 / 15 (100.0%) | **PASSED** |
| | | Hit@10 | $\ge 70.0\%$ ($\ge 11$ frames) | 0 / 15 (0.0%) | **FAILED** |
| | | Severe@100 | $\le 5.0\%$ ($0$ frames) | 13 / 15 (86.7%) | **FAILED** |

**DEV Decision**: Both development groups failed the official accuracy and severe error thresholds. Under Section 1.3, this constitutes a `FAIL` for production readiness on DEV.

---

## 3. Frame-by-Frame Error Analysis on Visible GT

### 3.1 GROUP_A Detailed Trace (19 Visible Frames)

| Frame ID | GT $(x, y)$ | Prediction $(x, y)$ | Error (px) | Hit@10 | Severe@100 | Diagnostic Mechanism / Root Cause |
|---|---|---|---:|:---:|:---:|---|
| 67 | (995.2, 1143.2) | (1109.0, 1170.0) | 116.9 | No | Yes | Over-extension: Faint surface mark at $x \approx 1109$ picked by `argmax(x)`. |
| 113 | (1050.7, 1154.0) | (1107.0, 1115.0) | 68.5 | No | No | Moderate over-extension to midplane texture. |
| 122 | (1066.4, 1156.1) | (1102.0, 1177.0) | 41.2 | No | No | Crack advancing; predicted tip near actual front. |
| 165 | (1093.8, 1147.9) | (1108.0, 1169.0) | 25.5 | No | No | Close observation: candidate at $x=1095$ had 1.2 px error. |
| **204** | (1161.5, 1160.4) | (1165.0, 1159.0) | **3.8** | **Yes** | No | **Accurate detection**: exact match with crack apex. |
| 217 | (1169.5, 1156.5) | (1182.0, 1155.0) | 12.6 | No | No | Near hit: predicted tip slightly ahead of manual label. |
| 241 | (1182.6, 1160.0) | (1139.0, 1153.0) | 44.2 | No | No | Cyclic closure: crack partially closed; stopped at visible dark valley. |
| 250 | (1204.1, 1163.9) | (1277.0, 1214.0) | 88.5 | No | No | Off-axis branch competition: secondary branch selected. |
| 299 | (1247.7, 1159.7) | (1154.0, 1139.0) | 96.0 | No | No | Cyclic closure: load phase low, physical tip closed. |
| 308 | (1252.7, 1158.0) | (1146.0, 1158.0) | 106.7 | No | Yes | Cyclic closure: stopped at open mouth. |
| 366 | (1315.1, 1159.4) | (1145.0, 1158.0) | 170.1 | No | Yes | Cyclic closure: tip optically closed; algorithm correctly did not hallucinate. |
| 398 | (1325.2, 1161.6) | (1337.0, 1164.0) | 12.1 | No | No | Near hit (error 12.1 px); candidate at $x=1336$ had 5 px error. |
| **427** | (1331.0, 1162.1) | (1336.0, 1163.0) | **5.1** | **Yes** | No | **Accurate detection**: Hit@10 PASS. |
| **451** | (1355.1, 1161.4) | (1356.0, 1161.0) | **1.0** | **Yes** | No | **Highly accurate detection**: 1.0 px error on 480 px crack! |
| **456** | (1357.5, 1161.7) | (1359.0, 1161.0) | **1.7** | **Yes** | No | **Highly accurate detection**: 1.7 px error! |
| **475** | (1344.3, 1156.0) | (1351.0, 1155.0) | **6.7** | **Yes** | No | **Accurate detection**: Hit@10 PASS. |
| 504 | (1380.0, 1158.6) | (1179.0, 1157.0) | 201.0 | No | Yes | Cyclic closure in late fatigue stage. |
| 542 | (1382.9, 1156.6) | (1139.0, 1155.0) | 243.9 | No | Yes | Cyclic closure: tip optically closed under lower load. |
| 551 | (1407.5, 1150.2) | (1144.0, 1153.0) | 263.5 | No | Yes | Final frame closed tip: stopped at visible notch mouth. |

---

## 4. Causal Failure Stage Attribution

The failures on DEV cluster into two dominant physical and visual mechanisms:

```
Total DEV Visible Failures (31 frames)
├── Cyclic Crack Closure / Optical Invisibility: 18 frames (58.1%)
│   └── Physical tip is closed under cyclic minimum load; algorithm stops at visible mouth.
├── Distal Texture Over-Extension: 11 frames (35.5%)
│   └── Faint horizontal surface machining marks ahead of the true tip selected by argmax(x).
└── Off-Axis Secondary Branch Competition: 2 frames (6.4%)
    └── Bifurcation / secondary branch had higher x coordinate.
```

1. **Cyclic Crack Closure (58.1% of errors)**:
   - In fatigue testing, specimen loading oscillates sinusoidally. When load is near minimum, the crack flanks press together, rendering the physical crack tip optically non-existent in raw grayscale.
   - Resolution 3 & 36 of the specification mandate: *“Formal tip must originate from the actual end of a verified current dark line segment; historical trajectory, inferred bridge, or notch root cannot impersonate tip.”*
   - Consequently, during closed phases, the algorithm legitimately stops at the open mouth ($x \approx 1140-1170$). Meanwhile, the human GT labels represent the historical maximum extent from previous peak-load frames.
2. **Distal Texture Over-Extension (35.5% of errors)**:
   - In early frames (e.g. Frame 67 in GROUP_A, Frames 144–347 in Three-point-bend), pre-existing surface machining marks or grinding striations along the specimen midplane produce weak dark valleys.
   - Because `selection_rule` is $\text{argmax}(\text{image\_x})$, when these faint striations connect to the candidate graph, the selector picks the furthest mark rather than stopping at the nascent crack.
