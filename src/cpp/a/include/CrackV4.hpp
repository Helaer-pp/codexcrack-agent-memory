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

#ifdef __cplusplus
#include <opencv2/core.hpp>
#include <stdexcept>
#include <string>
#include <vector>

// One object per acquisition stream. Preserve it between frames, in time order.
// Header-only adapter: OpenCV objects never cross the DLL ABI boundary.
class CrackV4Detector {
    CrackV4Handle handle_ = nullptr;
    static CrackV4Image image(const cv::Mat &m) {
        if (m.empty() || m.type() != CV_8UC1)
            throw std::invalid_argument("CrackV4 expects non-empty CV_8UC1 images");
        return {m.ptr<uint8_t>(), m.cols, m.rows, static_cast<int64_t>(m.step)};
    }

  public:
    enum class ReferenceMode { Clean = 0, Cracked = 1, Auto = 2 };
    CrackV4Detector() = default;
    ~CrackV4Detector() {
        reset();
    }
    CrackV4Detector(const CrackV4Detector &) = delete;
    CrackV4Detector &operator=(const CrackV4Detector &) = delete;
    void reset() {
        CrackV4Destroy(handle_);
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
        static const bool configured = [] { CrackV4SetNumThreads(4); return true; }();
        (void)configured;
        CrackV4Point points[2] = {{p1.x, p1.y}, {p2.x, p2.y}};
        CrackV4Config cfg{};
        CrackV4DefaultConfig(&cfg);
        cfg.reference_mode = static_cast<int>(mode);
        cfg.mm_per_pixel = mmPerPixel;
        cfg.refine_anchor_motion = refineAnchorMotion ? 1 : 0;
        char error[4096]{};
        double ms = 0;
        const CrackV4ExperimentOptions frozen{sizeof(CrackV4ExperimentOptions), 1, 3572u, 0};
        if (CrackV4CreateExtended(&ref, points, &cfg, &frozen, &handle_, &ms, error, sizeof(error)))
            throw std::runtime_error(error);
        const CrackV4OptionsV2 options{sizeof(CrackV4OptionsV2), 2, CV4_SHADOW, 1};
        if (CrackV4SetOptionsV2(handle_, &options)) {
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
                                          CrackV4Result *detail = nullptr) {
        auto im = image(current);
        CrackV4Point points[2] = {{p1.x, p1.y}, {p2.x, p2.y}};
        CrackV4Result r{};
        r.struct_size = sizeof(r);
        int code = CrackV4Process(handle_, &im, points, &r);
        if (detail)
            *detail = r;
        if (code)
            throw std::runtime_error(CrackV4LastJson(handle_));
        return {r.tip.x, r.tip.y};
    }
    // Existing automatic translation mode, when measured current points are unavailable.
    cv::Point2d getCrackTipPointCirculate(const cv::Mat &current, CrackV4Result *detail = nullptr) {
        auto im = image(current);
        CrackV4Result r{};
        r.struct_size = sizeof(r);
        int code = CrackV4Process(handle_, &im, nullptr, &r);
        if (detail)
            *detail = r;
        if (code)
            throw std::runtime_error(CrackV4LastJson(handle_));
        return {r.tip.x, r.tip.y};
    }
    CrackV4Result referenceResult() {
        CrackV4Result r{};
        r.struct_size = sizeof(r);
        if (CrackV4GetBaseline(handle_, &r))
            throw std::runtime_error(CrackV4LastJson(handle_));
        return r;
    }
    std::string diagnostics() const {
        return CrackV4LastJson(handle_);
    }
    CrackV4ResultV2 resultV2() const {
        CrackV4ResultV2 r{};
        r.struct_size = sizeof(r);
        r.api_version = 2;
        if (CrackV4GetResultV2(handle_, &r))
            throw std::runtime_error("Cannot read pixel V2 result");
        return r;
    }
    void setOptionsV2(const CrackV4OptionsV2 &options) {
        if (options.decision_policy != CV4_SHADOW || options.terminal_validation != 1)
            throw std::invalid_argument("A requires SHADOW and terminal_validation=1");
        if (CrackV4SetOptionsV2(handle_, &options))
            throw std::invalid_argument("Invalid V2 options or uninitialized detector");
    }
    void resetTemporal() {
        if (CrackV4ResetTemporal(handle_))
            throw std::runtime_error("Detector is not initialized");
    }
    // Query after referenceResult() or Process, before advancing the stream.
    std::vector<CrackV4Point> rawPath() const {
        int count = CrackV4CopyPath(handle_, 0, nullptr, 0);
        if (count < 0) throw std::runtime_error("Cannot query current path");
        std::vector<CrackV4Point> path(static_cast<size_t>(count));
        if (count && CrackV4CopyPath(handle_, 0, path.data(), count) != count)
            throw std::runtime_error("Cannot copy current path");
        return path;
    }
    // Draw each polyline independently; a break is an unmeasured gap.
    std::vector<std::vector<CrackV4Point>> pathSegments() const {
        int count = CrackV4SegmentCount(handle_);
        if (count < 0) throw std::runtime_error("Cannot query path segments");
        std::vector<std::vector<CrackV4Point>> segments(count);
        for (int i = 0; i < count; ++i) {
            int size = CrackV4CopySegment(handle_, i, nullptr, 0);
            if (size < 0) throw std::runtime_error("Cannot query segment size");
            segments[i].resize(size);
            if (CrackV4CopySegment(handle_, i, segments[i].data(), size) != size)
                throw std::runtime_error("Cannot copy path segment");
        }
        return segments;
    }
};
#endif // __cplusplus
