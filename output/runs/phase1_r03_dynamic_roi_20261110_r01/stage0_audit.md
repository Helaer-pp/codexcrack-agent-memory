# R03 preflight / Gate 0 pending replay

Production src/cpp/a/CrackV4.cpp and roi_tip.inc match R02 candidate DLL identity. R01/R02 evidence is hash-frozen; restore-only copy exists. No production edits are authorized by a PASS yet.

Constructor fixes origin/spacing/forward, reference templates and baseline_mask. estimateTipMotion is current-anchor independent. measureTip uses tipWindow, localReference, distalLine; a nonempty accepted path overwrites tip/path_valid/terminal. Therefore these three bits are correlated, not three independent proofs of physical ownership. Its status also depends on main-path length certification; separate tip-state and length-state metrics are required.

R02 profiling erroneously differences a counter reset each frame. R03 will use fresh per-frame values and independent outer timings, with nested scopes excluded from sums. R02 scripts' parents[3] relocation and sparse windows are not silently inherited.

Pilot: all seven measured R02 continuous windows plus four recorded failing variants; CT3 full 136, GROUP_A 252 (one confirmation, explicitly insufficient). Full 16-variant + additional 5% acceptance and A3/A4 are gated on A2 safety, never inferred from pilot.

Experimental lock gate reuses current terminal/path evidence, image-only motion, forward compatibility, 10 px boundary margin (9-sample terminal probe), 6 px connected-path locality. Strong first-frame structure may acquire immediately; this is a hypothesis requiring wrong-first-lock tests. No specimen-dependent thresholds. No GT enters runtime. State-only proposals never feed the detector. No production merge.
