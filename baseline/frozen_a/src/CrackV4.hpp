#pragma once
#include "CrackV4_v2.h"
#include <opencv2/core.hpp>
#include <stdexcept>
#include <string>

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
        CrackV4Point points[2] = {{p1.x, p1.y}, {p2.x, p2.y}};
        CrackV4Config cfg{};
        CrackV4DefaultConfig(&cfg);
        cfg.reference_mode = static_cast<int>(mode);
        cfg.mm_per_pixel = mmPerPixel;
        cfg.refine_anchor_motion = refineAnchorMotion ? 1 : 0;
        char error[4096]{};
        double ms = 0;
        if (CrackV4Create(&ref, points, &cfg, &handle_, &ms, error, sizeof(error)))
            throw std::runtime_error(error);
        return ms;
    }
    // Tracked corresponding points in the CURRENT image, in the same order as reference.
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
        if (CrackV4SetOptionsV2(handle_, &options))
            throw std::invalid_argument("Invalid V2 options or uninitialized detector");
    }
    void resetTemporal() {
        if (CrackV4ResetTemporal(handle_))
            throw std::runtime_error("Detector is not initialized");
    }
};
