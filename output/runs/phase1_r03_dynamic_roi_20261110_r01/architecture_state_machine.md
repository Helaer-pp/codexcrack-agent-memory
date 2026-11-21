# R03 experimental state-only architecture

Entry: research/uctt_r03/observer.cpp R03Observe reads immutable production result under detector mutex. State::step in state.hpp runs native C++; no image operation is added to production. A0 compiles production directly; A1 includes that same source unchanged. A2 runs a second independent State instance on A1 evidence, not a separate detector/closed-loop DLL. Shadow observes the same frame after image processing.

| State/condition | Next state | Output | Trusted history |
|---|---|---|---|
| Never acquired, no candidate | SEARCHING | search center fallback, valid=false | empty |
| Never acquired, weak/edge/invalid evidence | ACQUIRING | fallback, valid=false | empty |
| Accepted terminal/path, motion and direction | TRACKING | observed | write original point, reference-transformed point, direction and frame |
| Acquired, 1-2 misses, motion reliable | OCCLUDED | predicted, valid=false | preserve |
| Acquired, >=3 misses / disconnected / bad motion | RECOVERING | predicted if usable, otherwise fallback | preserve |
| Connected visual evidence returns | TRACKING | observed | write |

All coordinates are original pixels. The historical last_confirmed point retains its original measurement frame. A separate reference-space point projects with the current tip-specific rigid transform. Main-anchor registration is not substituted. Image size change requires a new state/reference; persistent changed size stays degraded. NaN/Inf motion or candidate cannot write history. Output bounds failure is explicit. No phase assumption or monotonicity rule. Although there is no explicit speed threshold, the hard 6-pixel overlap gate can suppress fast expansion or fragmented visible paths; the large real replay coverage loss means this requirement is NOT SATISFIED.

SEARCH_ROI is the current A0 tipWindow, always retained. It still depends on initial origin/direction/spacing. There is NO search normalization in this experiment. TRACK_ROI is only a proposal after an accepted state. Proposal uses a 24-pixel tail, 64-pixel forward extent, 24-pixel half-width; uncertainty +12 pixels/miss capped at 96; corners transformed and bounds clipped. These are unvalidated experimental choices, not tuned per specimen. There is no recovery image search and no closed-loop enlargement. Search ROI never changes from the proposal.

The 6-pixel connectivity gate and 10-pixel edge margin are experimental assumptions. Runtime path/terminal booleans are correlated by measureTip, so they cannot certify physical ownership. The injected coherent wrong-first-lock passes them: this architecture fails acquisition safety. No confidence-score calibration or independent ownership verifier exists. No GT/filename/frame loading phase enters the runtime.

R03Observe is a consuming diagnostic operation, called once per result and state in the harness. Legacy GetBaseline remains a cached query and does not advance State automatically. Resetting/reinitializing a detector requires destroying/recreating its sidecar; no hidden reset interception or changed legacy ABI. Separate sidecar mutexes protect state but callers must keep handles alive and serialize observe/destroy. returned JSON is owned by sidecar until next observe/destroy.
