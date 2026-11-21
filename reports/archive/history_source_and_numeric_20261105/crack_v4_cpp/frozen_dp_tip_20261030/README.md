# Frozen stable A + independent M/T/E feasibility study

This is a research sidecar, not a replacement of the production detector.
Stable A source and C ABI are under `baseline/src`. A is a verified, unchanged
prebuilt DLL; the exact hash and source file map are in the output freeze manifest.
No DP code, seed, scoring, tiled continuation, or internal history is changed.

Build with `powershell -File build.ps1` (C++17, v142, OpenCV 4.4 at
`D:/opencv-4.4.0/build/x64/vc15/lib`). New `TipSidecar.dll` is independent of A.
ASAN: `powershell -File build.ps1 -BuildDir build_asan -Asan`; it uses the locally
available v143 sanitizer runtime. Only the sidecar and tests are instrumented.

`TSDefaultConfig` gives ABI version 1 and active=0 (shadow). Create once from
original GRAY8 reference and original-coordinate reference anchors. On each
frame, pass current GRAY8, actual anchors when available, A's current formal flags,
original-coordinate double CopyPath, API-rounded tip/length, A width and A's final
reference-to-current 2x3 transform. `TSProcess` returns explicit diagnostics and
an optional strict path prefix. Never substitute candidate/raw or previous paths
when A has no confirmed full length. Check return code before consuming output.
`TSReset` clears bounded history after sequence changes. Destroy after use.

Modes 1=M (NO_CHANGE), 2=T (observations, always retains A), 3=E, 4=TE.
Research active=1 was tested separately; it must not be silently enabled in
production. E/TE can prematurely shorten a fading true synthetic crack, and
cannot recover a correct crack that has already left A's path. NO_IMPROVEMENT is
a permitted outcome. Two anchors do not validate local nonrigid material motion.

Test sequence: stage0_baseline.py, stage1_audit.py, stage4_replay.py,
synthetic_study.py, engineering_study.py, historical336.py, write_plan.py;
then finish_study.py prepare (freeze), holdout (ONE full fifth evaluation),
render, validate, diagnostics, report, hashes. DEV sources are four known groups;
fifth image/results/manifest are not read by development scripts. The final
manifest is first read only inside the frozen holdout operation.

CSV and JSONL preserve invalid measurements as empty/null; tip-only and full
length flags are separate. Media uses CopyPath's exact endpoint, retaining the
old API's 0.01px rounding in numerical records. Videos omit frame0 reference;
current IDs and raw filenames are mapped explicitly. Clean current-frame images
contain no anchors, candidate paths, text, historical/green/dashed overlays.

Synthetic errors are conditional on a confirmed program-GT path and are not
real-image accuracy. The generic stats helper's `over_budget` member is meaningful
only for millisecond timing arrays; for pixel errors use P50/P95/P99/Max only.
No manual GT is required or invented. Real precision and recall remain N/A.
