#pragma once
#include <stdint.h>
#ifdef _WIN32
#ifdef CRACK_V4_EXPORTS
#define CV4_API __declspec(dllexport)
#else
#define CV4_API __declspec(dllimport)
#endif
#else
#define CV4_API
#endif
#ifdef __cplusplus
extern "C" {
#endif
typedef void *CrackV4Handle;
typedef struct CrackV4Point {
    double x, y;
} CrackV4Point;
typedef struct CrackV4Image {
    const uint8_t *data;
    int width, height;
    int64_t stride;
} CrackV4Image;
typedef struct CrackV4Config {
    uint32_t struct_size;
    int reference_mode; /* 0 clean, 1 cracked, 2 auto */
    double mm_per_pixel;
    int refine_anchor_motion;
} CrackV4Config;
typedef struct CrackV4Result {
    uint32_t struct_size;
    int tip_confirmed, length_confirmed, root_confirmed, has_candidate;
    CrackV4Point tip;
    double length_px, observed_length_px, length_mm;
    double detector_ms, api_ms;
    int temporal_hits, tile_count;
} CrackV4Result;
CV4_API void CrackV4DefaultConfig(CrackV4Config *config);
/* UTF-8 diagnostic copied to error_buffer on failure. Inputs are GRAY8. */
CV4_API int CrackV4Create(const CrackV4Image *reference, const CrackV4Point *reference_points,
                          const CrackV4Config *config, CrackV4Handle *handle, double *initialization_ms,
                          char *error_buffer, int error_capacity);
/* current_points=NULL selects existing automatic-translation fallback. */
CV4_API int CrackV4Process(CrackV4Handle handle, const CrackV4Image *current,
                           const CrackV4Point *current_points, CrackV4Result *result);
CV4_API int CrackV4GetBaseline(CrackV4Handle handle, CrackV4Result *result);
CV4_API const char *CrackV4LastJson(CrackV4Handle handle);
/* count returned; points=NULL/capacity=0 queries count. observed=1 excludes inferred bridge. */
CV4_API int CrackV4CopyPath(CrackV4Handle handle, int observed, CrackV4Point *points, int capacity);
CV4_API void CrackV4Destroy(CrackV4Handle handle);
CV4_API const char *CrackV4BuildInfo(void);
/* Optional, process-wide OpenCV setting; never changed implicitly by Create. */
CV4_API void CrackV4SetNumThreads(int threads);
#ifdef __cplusplus
}
#endif
