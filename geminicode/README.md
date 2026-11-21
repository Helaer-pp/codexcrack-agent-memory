# Unified Crack Tip Detection (`geminicode`)

Implementation of the 60-Resolution Unified Fatigue Crack Rightmost Tip Detection Algorithm (`UCTIP-60Q-v1.0`).

## Directory Structure
```
geminicode/
├── README.md
├── configs/
│   └── unified_global.yaml
├── src/
│   ├── common.py
│   ├── data_contract.py
│   ├── geometry_notch.py
│   ├── raw_multiscale_valley.py
│   ├── registration.py
│   ├── segment_features.py
│   ├── segment_graph.py
│   ├── multitrack.py
│   ├── dynamic_roi.py
│   ├── tip_selection.py
│   └── engine.py
├── tests/
│   ├── test_synthetic.py
│   └── test_contracts.py
├── scripts/
│   ├── inventory.py
│   ├── run_inference.py
│   ├── run_ablations.py
│   ├── prevalidation_freeze.py
│   ├── evaluate.py
│   └── render_gallery.py
└── docs/
    ├── DATA_CONTRACT.md
    ├── STATE_MACHINE.md
    ├── ABLATION_PROTOCOL.md
    └── NO_GT_LEAKAGE_AUDIT.md
```

## Reproducible Command Sequence
```powershell
# 1. Verification of unit and invariant contracts
python -m pytest geminicode/tests -v

# 2. Phase P0: Inventory and baseline seal
python -m geminicode.scripts.inventory --run output/experiments/uctip_60q_geminicode_20261114_r01

# 3. Phase P2: Full DEV inference & offline evaluation
python -m geminicode.scripts.run_inference --run output/experiments/uctip_60q_geminicode_20261114_r01 --split dev
python -m geminicode.scripts.evaluate --run output/experiments/uctip_60q_geminicode_20261114_r01 --split dev

# 4. Phase P2: Pre-registered ablations
python -m geminicode.scripts.run_ablations --run output/experiments/uctip_60q_geminicode_20261114_r01

# 5. Phase P3: Pre-validation freeze
python -m geminicode.scripts.prevalidation_freeze --run output/experiments/uctip_60q_geminicode_20261114_r01

# 6. Phase P4: Locked group_c validation & evaluation
python -m geminicode.scripts.run_inference --run output/experiments/uctip_60q_geminicode_20261114_r01 --split locked
python -m geminicode.scripts.evaluate --run output/experiments/uctip_60q_geminicode_20261114_r01 --split locked

# 7. Phase P5: Interactive HTML Gallery
python -m geminicode.scripts.render_gallery --run output/experiments/uctip_60q_geminicode_20261114_r01
```
