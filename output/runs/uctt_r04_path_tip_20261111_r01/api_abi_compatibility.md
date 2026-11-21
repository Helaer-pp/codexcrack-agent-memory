# ABI and regression verification

Original and B0 legacy exported names are identical; B1 preserves them and adds R04Process/R04Observe/R04Map and the explicit profile getter. Original headers and production DLL are hash-protected. Baseline/observer output equality passed 642 chronological initialization/frame cases. Existing run.ps1 check passed production smoke, frozen regressions, six-group current-anchor invariance and invalid-current-anchor checks (project_check.log). These checks do not establish R04 attribution safety.

R04Process returns the original CrackV4Result unchanged; diagnostic states are separate JSON. Predicted/fallback are finite but invalid and never become legacy confirmed lengths. R04Observe is cached per frame; reset clears state. Map pointers are borrowed until next process/reset/destroy, used synchronously under caller serialization. Full concurrent-client lifetime and cross-platform ABI testing are not claimed. No production replacement occurred.
