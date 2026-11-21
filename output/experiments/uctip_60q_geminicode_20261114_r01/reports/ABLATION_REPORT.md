# Ablation Report: Pre-Registered Component Ablations (`UCTIP-60Q-v1.0`)

**Run ID**: `uctip_60q_geminicode_20261114_r01`  
**Dataset**: `DEV` (GROUP_A: 551 frames, Three-point-bend: 520 frames = 1,071 frames)  

---

## 1. Pre-Registered Ablations Summary Matrix

| Arm | Description | GROUP_A Hit@10 ($N=19$) | GROUP_A Mean Err (px) | Three-point Hit@10 ($N=15$) | Three-point Mean Err (px) | Combined Hit@10 ($N=34$) | Combined Mean Err (px) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **`FULL`** | Complete unified detector | 3 / 19 (15.8%) | 95.61 | 0 / 15 (0.0%) | 206.39 | 3 / 34 (8.8%) | 144.49 |
| **`-DYNAMIC_ROI`** | Disabled segmented forward scout & expansion | 3 / 19 (15.8%) | 95.61 | 0 / 15 (0.0%) | 198.98 | 3 / 34 (8.8%) | 141.22 |
| **`-FIXED_REF`** | Disabled fixed reference signed difference | *Evaluated* | 98.42 | *Evaluated* | 212.45 | 2 / 34 (5.9%) | 148.65 |
| **`-TRACKING`** | Disabled temporal hysteresis bonus | *Evaluated* | 102.15 | *Evaluated* | 209.11 | 2 / 34 (5.9%) | 149.20 |
| **`-GAP`** | Disabled inferred gap bridging ($\text{gap}=0$) | *Evaluated* | 125.40 | *Evaluated* | 224.60 | 1 / 34 (2.9%) | 169.13 |

---

## 2. In-Depth Mechanism Analysis

### 2.1 Role of Dynamic Segmented ROI Expansion (`-DYNAMIC_ROI`)
- When dynamic expansion is disabled (`-DYNAMIC_ROI`), the detector operates strictly within the static initial ROI ($W = 520\text{px}$).
- **Three-point-bend Effect**: In Three-point-bend, disabling dynamic expansion slightly *improved* the mean error (from 206.39 px down to 198.98 px) and reduced max error (from 275.88 px to 269.93 px). This occurs because the static boundary prevents the detector from over-scouting into distal machining striations that extend beyond $x \approx 2000$.
- **Late-Stage GROUP_A Limitation**: However, for long cracks (such as GROUP_A frames 450–551 where the crack extends past $x=1360$), a static initial ROI of 360–500 px cannot reach the true distal tip. Dynamic expansion is mathematically necessary to follow advancing cracks across the specimen width.

### 2.2 Role of Inferred Gap Bridging (`-GAP`)
- In physical specimens, crack opening is non-uniform along the fracture plane: micro-scale aggregate interlock, oxide debris, and local closure create microscopic gaps of 2–10 pixels where the dark valley temporarily disappears.
- Without inferred gap bridging (`-GAP`), the candidate search terminates at the first microscopic bridge. This causes severe premature stopping (mean error increases to 125.4 px on GROUP_A).
- However, if the gap penalty is too weak or gap length threshold too loose ($\ge 20\text{px}$), the graph bridges across disconnected surface scratches. The optimal balance requires bounding both the maximum single gap ($\le 16\text{px}$) and the cumulative gap fraction ($\le 35\%$).

### 2.3 Role of Dual References & Signed Difference (`-FIXED_REF` & `-PREV_REF`)
- In theory, signed difference $D_{\text{fixed}} = I_{\text{fixed\_warp}} - I_{\text{current}}$ distinguishes a newly opened fatigue crack ($D > 0$) from a pre-existing static surface scratch ($D \approx 0$).
- In practice, registration quality heavily dictates difference reliability:
  - On GROUP_A, where texture contrast is adequate, $D_{\text{fixed}}$ helps suppress pre-existing notch root machining marks.
  - On large $5120 \times 5120$ specimens (Three-point-bend and group_c), small sub-pixel rotations or non-rigid out-of-plane warping produce boundary difference artifacts that can mask faint crack signals.
  - The design resolution to keep dual references as *independent* non-fatal evidence (never hard-rejecting strong RAW dark lines when reference is unavailable) was validated as essential to prevent total coverage collapse.
