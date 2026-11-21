# R03 state-only experiment — not a production algorithm

This is the user-requested Gate0–2 experiment. **Gate2 failed**: a self-consistent injected wrong first candidate is accepted. The hard path-overlap rule also loses real confirmation coverage. A3 dynamic ROI and A4 recovery are prohibited until safety passes; they are not implemented here. Do not integrate `state.hpp` as a validated detector.

`CMakeLists.txt` builds unchanged production A0, read-only A1 observer, and native fault contracts. `pilot.py` replays seven R02 windows and four historical failures. `verify.py` runs the fault and legacy ABI checks. `profile.py` generates a timer-only copy under output, then measures full native calls. `report.py` derives artifacts from raw evidence. No sealed source is executed.

The run is [phase1_r03_dynamic_roi_20261110_r01](../../output/runs/phase1_r03_dynamic_roi_20261110_r01/development_report.md). Read its limitations and [reproduction commands](../../output/runs/phase1_r03_dynamic_roi_20261110_r01/build_and_replay_commands.md) before rerunning. Use fresh output/build paths for a new run; keep frozen evidence unchanged.

The sidecar has an explicit lifecycle: create one state per detector and initialization variant, observe once after each chronological frame result, recreate on detector reset, destroy before abandoning the sequence. Legacy GetBaseline remains a read-only cached query; it does not invoke or advance the sidecar. Predicted/fallback coordinates are finite but invalid, and cannot certify physical length. The proposed tracking rectangle is logged only and never drives detection.
