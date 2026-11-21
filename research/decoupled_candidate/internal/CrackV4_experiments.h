#pragma once
#include "CrackV4_v2.h"
#ifdef __cplusplus
extern "C" {
#endif
/* Opt-in extensions. Existing C ABI / Pixel V2 layouts are unchanged. */
enum CrackV4ExperimentFlags {
    CV4_DIAGNOSTICS = 1, CV4_DEBUG_IMAGES = 2,
    CV4_DIRECTION_EXPERIMENT = 4,
    CV4_PHOTOMETRIC_EXPERIMENT = 8, /* diagnostics only: clipped/texture stats */
    CV4_REGISTRATION_RECOVERY = 16, CV4_LAYERED_AUDIT = 32,
    CV4_CURRENT_TEXTURE_GUARD = 64,
    CV4_ANCHOR_PATCH_RECOVERY = 128, /* failed automatic registration only */
    CV4_DIRECTION_POSITIVE = 256, /* ordered-anchor right normal; explicit override */
    CV4_DIRECTION_NEGATIVE = 512, /* opposite normal; mutually exclusive with POSITIVE */
    CV4_GUARDED_REGISTRATION = 1024, /* recheck low-confidence automatic successes */
    CV4_REJECT_ERASED_TERMINAL = 2048 /* formal uncertainty for current erased texture */
};
typedef struct CrackV4ExperimentOptions {
    uint32_t struct_size, api_version, flags, max_debug_images;
} CrackV4ExperimentOptions;
CV4_API void CrackV4DefaultExperimentOptions(CrackV4ExperimentOptions *options);
CV4_API int CrackV4CreateExtended(const CrackV4Image *reference, const CrackV4Point *points,
    const CrackV4Config *config, const CrackV4ExperimentOptions *experiments,
    CrackV4Handle *handle, double *initialization_ms, char *error, int error_capacity);
/* Diagnostics only; read-only. Copy the returned text before another debug query. */
CV4_API const char *CrackV4LastDebugJson(CrackV4Handle handle);
/* Read-only four-layer audit; historical coordinates retain their own frame. */
CV4_API const char *CrackV4LastQualityJson(CrackV4Handle handle);
/* Read-only geometric state; current_anchor_valid is independent of tip validity. */
CV4_API const char *CrackV4LastGeometryJson(CrackV4Handle handle);
/* Index 0.. until -1; returns required float count, names are ASCII. NULL data queries size. */
CV4_API int CrackV4GetDebugImage(CrackV4Handle handle, int index, float *data, int capacity,
    int *width, int *height, char *name, int name_capacity);
#ifdef __cplusplus
}
#endif
