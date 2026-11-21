#pragma once

#include <stdint.h>
#ifdef _WIN32
#ifdef GRAYDETECTIONV2_EXPORTS
#define GRAYDETECTIONV2_API __declspec(dllexport)
#else
#define GRAYDETECTIONV2_API __declspec(dllimport)
#endif
#else
#define GRAYDETECTIONV2_API
#endif
#ifdef __cplusplus
extern "C" {
#endif
typedef void *GrayDetectionV2Handle;
typedef struct GrayDetectionV2Point {
    double x, y;
} GrayDetectionV2Point;
typedef struct GrayDetectionV2Image {
    const uint8_t *data;
    int width, height;
    int64_t stride;
} GrayDetectionV2Image;
typedef struct GrayDetectionV2Config {
    uint32_t struct_size;
    int reference_mode; /* 0 clean, 1 cracked, 2 auto */
    double mm_per_pixel;
    int refine_anchor_motion;
} GrayDetectionV2Config;
typedef struct GrayDetectionV2Result {
    uint32_t struct_size;
    int tip_confirmed, length_confirmed, root_confirmed, has_candidate;
    GrayDetectionV2Point tip;
    double length_px, observed_length_px, length_mm;
    double detector_ms, api_ms;
    int temporal_hits, tile_count;
} GrayDetectionV2Result;
GRAYDETECTIONV2_API void GrayDetectionV2DefaultConfig(GrayDetectionV2Config *config);
/* UTF-8 diagnostic copied to error_buffer on failure. Inputs are GRAY8. */
GRAYDETECTIONV2_API int GrayDetectionV2Create(const GrayDetectionV2Image *reference, const GrayDetectionV2Point *reference_points,
                          const GrayDetectionV2Config *config, GrayDetectionV2Handle *handle, double *initialization_ms,
                          char *error_buffer, int error_capacity);
/*
 * current_points are optional tracked corresponding points used as a coarse
 * rigid-localization prior. The returned crack result is
 * measured in the fixed reference geometry after reference-texture image
 * registration; changing these points must not redefine the endpoint ROI or
 * direction. NULL selects the automatic-registration fallback.
 */
GRAYDETECTIONV2_API int GrayDetectionV2Process(GrayDetectionV2Handle handle, const GrayDetectionV2Image *current,
                           const GrayDetectionV2Point *current_points, GrayDetectionV2Result *result);
GRAYDETECTIONV2_API int GrayDetectionV2GetBaseline(GrayDetectionV2Handle handle, GrayDetectionV2Result *result);
GRAYDETECTIONV2_API const char *GrayDetectionV2LastJson(GrayDetectionV2Handle handle);
/* count returned; points=NULL/capacity=0 queries count. observed=1 excludes inferred bridge. */
GRAYDETECTIONV2_API int GrayDetectionV2CopyPath(GrayDetectionV2Handle handle, int observed, GrayDetectionV2Point *points, int capacity);
/* Confirmed visible polylines. Query count, then size/copy each segment separately. */
GRAYDETECTIONV2_API int GrayDetectionV2SegmentCount(GrayDetectionV2Handle handle);
GRAYDETECTIONV2_API int GrayDetectionV2CopySegment(GrayDetectionV2Handle handle, int index, GrayDetectionV2Point *out, int capacity);
GRAYDETECTIONV2_API void GrayDetectionV2Destroy(GrayDetectionV2Handle handle);
GRAYDETECTIONV2_API const char *GrayDetectionV2BuildInfo(void);
/* Optional, process-wide OpenCV setting; never changed implicitly by Create. */
GRAYDETECTIONV2_API void GrayDetectionV2SetNumThreads(int threads);
#ifdef __cplusplus
}
#endif

#ifdef __cplusplus
extern "C" {
#endif
/* Versioned, pixel-only extension. No existing ABI layout is changed. */
enum GrayDetectionV2DecisionPolicy { GRAYDETECTIONV2_LEGACY = 0, GRAYDETECTIONV2_SHADOW = 1, GRAYDETECTIONV2_VERIFIED_EXPERIMENTAL = 2 };
enum GrayDetectionV2ReferenceState { GRAYDETECTIONV2_DECLARED_CLEAN = 0, GRAYDETECTIONV2_REFERENCE_CRACK = 1, GRAYDETECTIONV2_REFERENCE_UNCERTAIN = 2 };
typedef struct GrayDetectionV2OptionsV2 {
    uint32_t struct_size, api_version;
    int decision_policy; /* default SHADOW: legacy decisions, new diagnostics */
    int terminal_validation; /* default 1; VERIFIED requires this to be 1 */
} GrayDetectionV2OptionsV2;
typedef struct GrayDetectionV2ResultV2 {
    uint32_t struct_size, api_version;
    uint64_t frame_index;
    int reference_state, decision_policy;
    int has_candidate, root_confirmed, terminal_verified, path_quality_valid;
    int tip_confirmed, complete_length_valid, legacy_tip_confirmed, shadow_tip_confirmed;
    GrayDetectionV2Point tip_px, root_px, tracking_endpoint_px;
    double observed_length_px, root_to_tip_length_px, root_bridge_length_px;
    double path_support_fraction, tail_support_fraction, tail_median_score;
    double path_width_median_px, tail_width_median_px;
    double detector_ms, api_ms;
    int longest_gap_samples, sharp_bend_count, endpoint_temporal_hits, probe_samples;
    char terminal_reason[64], stop_reason[48], divergence_reason[64];
} GrayDetectionV2ResultV2;
GRAYDETECTIONV2_API void GrayDetectionV2DefaultOptionsV2(GrayDetectionV2OptionsV2 *options);
/* Changes/reset must be made between frames. Changing options resets temporal state. */
GRAYDETECTIONV2_API int GrayDetectionV2SetOptionsV2(GrayDetectionV2Handle handle, const GrayDetectionV2OptionsV2 *options);
/* Read-only latest frame. Ordered Process->GetResultV2 per acquisition stream. */
GRAYDETECTIONV2_API int GrayDetectionV2GetResultV2(GrayDetectionV2Handle handle, GrayDetectionV2ResultV2 *result);
/* Keep reference/caches/config, clear prior/history/latest result/frame index. */
GRAYDETECTIONV2_API int GrayDetectionV2ResetTemporal(GrayDetectionV2Handle handle);
#ifdef __cplusplus
}
#endif

#ifdef __cplusplus
extern "C" {
#endif
/* Opt-in extensions. Existing C ABI / Pixel V2 layouts are unchanged. */
enum GrayDetectionV2ExperimentFlags {
    GRAYDETECTIONV2_DIAGNOSTICS = 1, GRAYDETECTIONV2_DEBUG_IMAGES = 2,
    GRAYDETECTIONV2_DIRECTION_EXPERIMENT = 4,
    GRAYDETECTIONV2_PHOTOMETRIC_EXPERIMENT = 8, /* diagnostics only: clipped/texture stats */
    GRAYDETECTIONV2_REGISTRATION_RECOVERY = 16, GRAYDETECTIONV2_LAYERED_AUDIT = 32,
    GRAYDETECTIONV2_CURRENT_TEXTURE_GUARD = 64,
    GRAYDETECTIONV2_ANCHOR_PATCH_RECOVERY = 128, /* failed automatic registration only */
    GRAYDETECTIONV2_DIRECTION_POSITIVE = 256, /* ordered-anchor right normal; explicit override */
    GRAYDETECTIONV2_DIRECTION_NEGATIVE = 512, /* opposite normal; mutually exclusive with POSITIVE */
    GRAYDETECTIONV2_GUARDED_REGISTRATION = 1024, /* recheck low-confidence automatic successes */
    GRAYDETECTIONV2_REJECT_ERASED_TERMINAL = 2048 /* formal uncertainty for current erased texture */
};
typedef struct GrayDetectionV2ExperimentOptions {
    uint32_t struct_size, api_version, flags, max_debug_images;
} GrayDetectionV2ExperimentOptions;
GRAYDETECTIONV2_API void GrayDetectionV2DefaultExperimentOptions(GrayDetectionV2ExperimentOptions *options);
GRAYDETECTIONV2_API int GrayDetectionV2CreateExtended(const GrayDetectionV2Image *reference, const GrayDetectionV2Point *points,
    const GrayDetectionV2Config *config, const GrayDetectionV2ExperimentOptions *experiments,
    GrayDetectionV2Handle *handle, double *initialization_ms, char *error, int error_capacity);
/* Diagnostics only; read-only. Copy the returned text before another debug query. */
GRAYDETECTIONV2_API const char *GrayDetectionV2LastDebugJson(GrayDetectionV2Handle handle);
/* Read-only four-layer audit; historical coordinates retain their own frame. */
GRAYDETECTIONV2_API const char *GrayDetectionV2LastQualityJson(GrayDetectionV2Handle handle);
/* Read-only geometric state; current_anchor_valid is independent of tip validity. */
GRAYDETECTIONV2_API const char *GrayDetectionV2LastGeometryJson(GrayDetectionV2Handle handle);
/* Index 0.. until -1; returns required float count, names are ASCII. NULL data queries size. */
GRAYDETECTIONV2_API int GrayDetectionV2GetDebugImage(GrayDetectionV2Handle handle, int index, float *data, int capacity,
    int *width, int *height, char *name, int name_capacity);
#ifdef __cplusplus
}
#endif

#ifdef __cplusplus
#include <opencv2/core.hpp>
#include <stdexcept>
#include <string>
#include <vector>

// One object per acquisition stream. Preserve it between frames, in time order.
// Header-only adapter: OpenCV objects never cross the DLL ABI boundary.
class GrayDetectionV2 {
    GrayDetectionV2Handle handle_ = nullptr;
    static GrayDetectionV2Image image(const cv::Mat &m) {
        if (m.empty() || m.type() != CV_8UC1)
            throw std::invalid_argument("GrayDetectionV2 expects non-empty CV_8UC1 images");
        return {m.ptr<uint8_t>(), m.cols, m.rows, static_cast<int64_t>(m.step)};
    }

  public:
    enum class ReferenceMode { Clean = 0, Cracked = 1, Auto = 2 };
    GrayDetectionV2() = default;
    ~GrayDetectionV2() {
        reset();
    }
    GrayDetectionV2(const GrayDetectionV2 &) = delete;
    GrayDetectionV2 &operator=(const GrayDetectionV2 &) = delete;
    void reset() {
        GrayDetectionV2Destroy(handle_);
        handle_ = nullptr;
    }
    double initialize(const cv::Mat &reference, cv::Point2d p1, cv::Point2d p2,
                      ReferenceMode mode = ReferenceMode::Auto, double mmPerPixel = 1.,
                      bool refineAnchorMotion = true) {
        reset();
        auto ref = image(reference);
        if (!refineAnchorMotion)
            throw std::invalid_argument("A requires refineAnchorMotion=true");
        // OpenCV thread count is process-wide. Initialize before acquisition workers start.
        static const bool configured = [] { GrayDetectionV2SetNumThreads(4); return true; }();
        (void)configured;
        GrayDetectionV2Point points[2] = {{p1.x, p1.y}, {p2.x, p2.y}};
        GrayDetectionV2Config cfg{};
        GrayDetectionV2DefaultConfig(&cfg);
        cfg.reference_mode = static_cast<int>(mode);
        cfg.mm_per_pixel = mmPerPixel;
        cfg.refine_anchor_motion = refineAnchorMotion ? 1 : 0;
        char error[4096]{};
        double ms = 0;
        const GrayDetectionV2ExperimentOptions frozen{sizeof(GrayDetectionV2ExperimentOptions), 1, 3572u, 0};
        if (GrayDetectionV2CreateExtended(&ref, points, &cfg, &frozen, &handle_, &ms, error, sizeof(error)))
            throw std::runtime_error(error);
        const GrayDetectionV2OptionsV2 options{sizeof(GrayDetectionV2OptionsV2), 2, GRAYDETECTIONV2_SHADOW, 1};
        if (GrayDetectionV2SetOptionsV2(handle_, &options)) {
            reset();
            throw std::runtime_error("Cannot initialize A options");
        }
        return ms;
    }
    // Tracked corresponding points in the CURRENT image, in the same order as
    // reference. They provide a coarse rigid-localization prior only. Endpoint
    // detection uses the fixed reference geometry after reference-texture
    // image registration;
    // changing these points must not redefine the result ROI or direction.
    // Tip is (0,0) if unconfirmed. Check detail.tip_confirmed to distinguish a real coordinate.
    cv::Point2d getCrackTipPointCirculate(const cv::Mat &current, cv::Point2d p1, cv::Point2d p2,
                                          GrayDetectionV2Result *detail = nullptr) {
        auto im = image(current);
        GrayDetectionV2Point points[2] = {{p1.x, p1.y}, {p2.x, p2.y}};
        GrayDetectionV2Result r{};
        r.struct_size = sizeof(r);
        int code = GrayDetectionV2Process(handle_, &im, points, &r);
        if (detail)
            *detail = r;
        if (code)
            throw std::runtime_error(GrayDetectionV2LastJson(handle_));
        return {r.tip.x, r.tip.y};
    }
    // Existing automatic translation mode, when measured current points are unavailable.
    cv::Point2d getCrackTipPointCirculate(const cv::Mat &current, GrayDetectionV2Result *detail = nullptr) {
        auto im = image(current);
        GrayDetectionV2Result r{};
        r.struct_size = sizeof(r);
        int code = GrayDetectionV2Process(handle_, &im, nullptr, &r);
        if (detail)
            *detail = r;
        if (code)
            throw std::runtime_error(GrayDetectionV2LastJson(handle_));
        return {r.tip.x, r.tip.y};
    }
    GrayDetectionV2Result referenceResult() {
        GrayDetectionV2Result r{};
        r.struct_size = sizeof(r);
        if (GrayDetectionV2GetBaseline(handle_, &r))
            throw std::runtime_error(GrayDetectionV2LastJson(handle_));
        return r;
    }
    std::string diagnostics() const {
        return GrayDetectionV2LastJson(handle_);
    }
    GrayDetectionV2ResultV2 resultV2() const {
        GrayDetectionV2ResultV2 r{};
        r.struct_size = sizeof(r);
        r.api_version = 2;
        if (GrayDetectionV2GetResultV2(handle_, &r))
            throw std::runtime_error("Cannot read pixel V2 result");
        return r;
    }
    void setOptionsV2(const GrayDetectionV2OptionsV2 &options) {
        if (options.decision_policy != GRAYDETECTIONV2_SHADOW || options.terminal_validation != 1)
            throw std::invalid_argument("A requires SHADOW and terminal_validation=1");
        if (GrayDetectionV2SetOptionsV2(handle_, &options))
            throw std::invalid_argument("Invalid V2 options or uninitialized detector");
    }
    void resetTemporal() {
        if (GrayDetectionV2ResetTemporal(handle_))
            throw std::runtime_error("Detector is not initialized");
    }
    // Query after referenceResult() or Process, before advancing the stream.
    std::vector<GrayDetectionV2Point> rawPath() const {
        int count = GrayDetectionV2CopyPath(handle_, 0, nullptr, 0);
        if (count < 0) throw std::runtime_error("Cannot query current path");
        std::vector<GrayDetectionV2Point> path(static_cast<size_t>(count));
        if (count && GrayDetectionV2CopyPath(handle_, 0, path.data(), count) != count)
            throw std::runtime_error("Cannot copy current path");
        return path;
    }
    // Draw each polyline independently; a break is an unmeasured gap.
    std::vector<std::vector<GrayDetectionV2Point>> pathSegments() const {
        int count = GrayDetectionV2SegmentCount(handle_);
        if (count < 0) throw std::runtime_error("Cannot query path segments");
        std::vector<std::vector<GrayDetectionV2Point>> segments(count);
        for (int i = 0; i < count; ++i) {
            int size = GrayDetectionV2CopySegment(handle_, i, nullptr, 0);
            if (size < 0) throw std::runtime_error("Cannot query segment size");
            segments[i].resize(size);
            if (GrayDetectionV2CopySegment(handle_, i, segments[i].data(), size) != size)
                throw std::runtime_error("Cannot copy path segment");
        }
        return segments;
    }
};
#endif // __cplusplus
