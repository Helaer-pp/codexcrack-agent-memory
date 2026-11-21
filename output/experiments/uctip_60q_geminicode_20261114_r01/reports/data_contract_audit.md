# Data Contract Audit (Phase P0)

## Summary
- Total Frames: 1,633 (GROUP_A: 551 DEV, three_point_bend: 520 DEV, group_c: 562 LOCKED)
- All image paths and P1/P2 anchor files verified existing and readable on disk.
- Contiguous 0-based tracking numbers verified for all 3 datasets.
- Historical baseline files sealed (176105 files hashed in `baseline_protection_manifest.json`).
- GT Leakage Guard: Active. No GT opened or referenced during inventory.
- group_c Holdout Guard: Active. group_c images/anchors held sealed until post-freeze.
