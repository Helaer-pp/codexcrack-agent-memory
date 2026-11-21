# Blockers & Technical Limitations Report

**Run ID**: `uctip_60q_geminicode_20261114_r01`  

## 1. Input Contract & Execution Blockers
- **Data Availability**: Zero blockers. All 1,633 raw BMP images and tracking anchor records were successfully loaded from disk.
- **Runtime Execution**: Zero execution crashes. All 1,633 frames completed processing across all phases.
- **GT Leakage**: Zero leakage blockers. All inference runs were strictly GT-free.

## 2. Algorithmic Bottlenecks & Accuracy Blockers
1. **Optical Invisibility under Cyclic Crack Closure**:
   - In fatigue testing, cyclic load troughs cause physical crack closure. The crack tip is optically invisible in 2D grayscale during closed phases.
   - Ground truth annotations marked the tip positions established during peak opening, causing apparent large errors on closed frames.
2. **Pre-Machined Slits & Machining Striations**:
   - In specimens with EDM pre-cracks or grinding marks (notably group_c), dark valley continuity extends ahead of nascent fatigue cracks, causing $\text{argmax}(\text{image\_x})$ to over-extend to the end of the pre-machined mark.
