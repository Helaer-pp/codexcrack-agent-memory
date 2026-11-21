# CodexCrack — persistent development instructions

This directory is the sole active Codex development project. Resolve PROJECT_ROOT from this file, not from an absolute drive path. Run commands with this directory as cwd. Create and modify project files only inside PROJECT_ROOT. All generated run data, videos, comparison images, logs, build products and temporary caches belong under PROJECT_ROOT/output/. Read external original-image inputs and installed tools only; never write to F: datasets or other projects. A future explicit user instruction can change this scope.

Read README.md, docs/CURRENT_STATE.md and config/project.json before continuing development. config/datasets.json and data/inputs/six_groups_manifest.csv define inputs; data/anchors holds the supplied original anchor records. Old task documents are historical user material, not automatically active instructions. Follow a particular task document only when the user invokes it. Do not execute archive/ or sealed output/* source as active code.

## Current algorithm and evidence

- Latest research is A′3 under research/aprime3, output/runs/aprime3_20261105_r01. Decision KEEP_A. NEW_DEV918 frames: observable648, candidate oracle583→621, actual correct553→553; FP105 unchanged. Reference mean coverage63.0069%→62.9512%, no cross-material support. Same-endpoint group_c196→194; multi-query380 is a different metric. AP3Observer DLL only observes seed gates, not full A′3. No independent TEST or full-native15Hz pass. Read CURRENT_STATE and the report; preserve both AP2 and AP3 sealed evidence. research_valid is research confirmation, selected_output_valid can be unverified A fallback.

- Production is A in src/cpp/a, exported as output/releases/A_Win64_OpenCV440/bin/CrackV4.dll. The gap-resume and adaptive-tip logic runs inside A. Use the standard A target for builds and releases. The former frozen A (SHA256 c23498fcc660469927f63244b8e98e39b1eb86d542ec9a7b069d61fcf813654b) is retained for historical regressions in baseline/frozen_a and backed up with its SDK at output/backups/FrozenA_before_A_merge.zip. Preserve that identity and all sealed experimental results.
- Formal operating contract: flags3572, SHADOW policy1, terminal validation1, refine=true, four native threads. Do not silently use VERIFIED2. One detector per sequence; initialize once and process in temporal order with each current pair of tracked anchors. GetBaseline is a cached query, not a state advance.
- P1 above P2; ordered right normal (dy,-dx)/L. All coordinates are original image pixels. Invalid/degenerate anchors fail explicitly. Invalid tips are null with valid=false in machine data; display0 only as an explicit invalid display convention.
- New projected length=(tip-current anchor midpoint) dot right normal. Preserve A arc length separately; do not label pixels as mm without a supplied calibration.
- No monotonic-growth prior, future frames or frame-number loading-phase assumptions. PHASE_UNKNOWN without synchronization. No physical GT means real accuracy N/A. Candidate/path/reference transitions are not physical truth.
- A′ is research only. Latest Gate1 failed: joint local reference supported337/3029 current images, only group_c/three-point-bend; GROUP_A/CT2/group_h zero. All formal outputs fell back to A. No new TEST or A′ production DLL passed. Do not present fallback identity as new accuracy or safety evidence.
- group_x is retired exposed history, never tuning/independent validation. Three-point-bend is exposed validation-only, no tuning. All six prior real groups and all historic DEV/TEST are exposed. Use genuinely new controlled DEV/TEST with pre-locking for independent claims.
- Keep weak/curved crack capability; no specimen-name thresholds, no GT/filename/frame-ID in runtime decisions. No DL, DIC/dense optical flow or full-image second path finder within the current research contract.

## Code, builds, tests, retention

src/python/crackv4 is the local Python bridge; research/aprime is the current portable research source. Native C++ uses bundled third_party/opencv440, copied from the user's D:/opencv-4.4.0 (4.4.0) SDK. Python/compiler are installed tools configured in config/project.json. FFmpeg is bundled for result rendering. No runtime import may depend on archive/ or deleted legacy workspaces.

Use run.ps1 check after infrastructure/path changes. Build via build.ps1 into output/build/. Run targeted checks appropriate to the change; full benchmarks only when warranted. Native A-only timings, Python sidecar timings and15FPS video playback are distinct. Preserve sealed output/aprime_20261105/run01 and the final manifest of output/runs/aprime2_20261105_r01; new work uses output/runs/<unique_run_id>.

Archive/ holds compressed history and prior requested packages. It is not a development dependency. docs/maintenance/file_disposition.csv and legacy_path_map.json record retention/removal and relocation. Before future recursive deletion/moves, resolve and check absolute targets stay inside the intended project, never delete baseline/, user anchors or sealed evidence casually. Ordinary authorized reversible edits/checks need no repeated user confirmation.
