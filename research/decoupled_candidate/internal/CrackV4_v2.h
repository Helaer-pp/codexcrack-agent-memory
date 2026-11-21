#pragma once
#include "CrackV4.h"
#ifdef __cplusplus
extern "C" {
#endif
/* Versioned, pixel-only extension. No existing ABI layout is changed. */
enum CrackV4DecisionPolicy { CV4_LEGACY = 0, CV4_SHADOW = 1, CV4_VERIFIED_EXPERIMENTAL = 2 };
enum CrackV4ReferenceState { CV4_DECLARED_CLEAN = 0, CV4_REFERENCE_CRACK = 1, CV4_REFERENCE_UNCERTAIN = 2 };
typedef struct CrackV4OptionsV2 {
    uint32_t struct_size, api_version;
    int decision_policy; /* default SHADOW: legacy decisions, new diagnostics */
    int terminal_validation; /* default 1; VERIFIED requires this to be 1 */
} CrackV4OptionsV2;
typedef struct CrackV4ResultV2 {
    uint32_t struct_size, api_version;
    uint64_t frame_index;
    int reference_state, decision_policy;
    int has_candidate, root_confirmed, terminal_verified, path_quality_valid;
    int tip_confirmed, complete_length_valid, legacy_tip_confirmed, shadow_tip_confirmed;
    CrackV4Point tip_px, root_px, tracking_endpoint_px;
    double observed_length_px, root_to_tip_length_px, root_bridge_length_px;
    double path_support_fraction, tail_support_fraction, tail_median_score;
    double path_width_median_px, tail_width_median_px;
    double detector_ms, api_ms;
    int longest_gap_samples, sharp_bend_count, endpoint_temporal_hits, probe_samples;
    char terminal_reason[64], stop_reason[48], divergence_reason[64];
} CrackV4ResultV2;
CV4_API void CrackV4DefaultOptionsV2(CrackV4OptionsV2 *options);
/* Changes/reset must be made between frames. Changing options resets temporal state. */
CV4_API int CrackV4SetOptionsV2(CrackV4Handle handle, const CrackV4OptionsV2 *options);
/* Read-only latest frame. Ordered Process->GetResultV2 per acquisition stream. */
CV4_API int CrackV4GetResultV2(CrackV4Handle handle, CrackV4ResultV2 *result);
/* Keep reference/caches/config, clear prior/history/latest result/frame index. */
CV4_API int CrackV4ResetTemporal(CrackV4Handle handle);
#ifdef __cplusplus
}
#endif
