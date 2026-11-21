#pragma once
#include "CrackV510.h"
#include <chrono>
#include <opencv2/core.hpp>
#include <stdexcept>
#include <vector>

class CrackV510Detector {
    Crack510Handle handle_ = nullptr;
    static Crack510Image view(const cv::Mat &m) {
        if (m.empty() || m.type() != CV_8UC1)
            throw std::invalid_argument("Expected CV_8UC1");
        return {m.ptr<uint8_t>(), m.cols, m.rows, static_cast<int64_t>(m.step)};
    }
    static void check(int code) {
        if (code)
            throw std::runtime_error(Crack510LastError());
    }

  public:
    CrackV510Detector() = default;
    CrackV510Detector(const CrackV510Detector &) = delete;
    CrackV510Detector &operator=(const CrackV510Detector &) = delete;
    ~CrackV510Detector() { reset(); }
    void reset() {
        Crack510Destroy(handle_);
        handle_ = nullptr;
    }
    double initialize(const cv::Mat &fixed, cv::Point2d p1, cv::Point2d p2,
                      const Crack510Config *config = nullptr) {
        Crack510Handle fresh = nullptr;
        auto im = view(fixed);
        Crack510Point p[] = {{p1.x, p1.y}, {p2.x, p2.y}};
        auto start = std::chrono::steady_clock::now();
        check(Crack510Create(&im, p, config, &fresh));
        reset();
        handle_ = fresh;
        return std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - start).count();
    }
    Crack510Result referenceResult() const {
        Crack510Result out{};
        out.struct_size = sizeof(out);
        check(Crack510GetBaseline(handle_, &out));
        return out;
    }
    cv::Point2d getCrackTipPointCirculate(const cv::Mat &current, cv::Point2d p1, cv::Point2d p2,
                                          Crack510Result *detail = nullptr) {
        auto im = view(current);
        Crack510Point p[] = {{p1.x, p1.y}, {p2.x, p2.y}};
        Crack510Result out{};
        out.struct_size = sizeof(out);
        check(Crack510Process(handle_, &im, p, &out));
        if (detail)
            *detail = out;
        return out.status == CR510_VALID ? cv::Point2d(out.tip.x, out.tip.y) : cv::Point2d(0, 0);
    }
    std::vector<std::vector<Crack510Point>> pathSegments() const {
        auto path = rawPath();
        if (path.empty())
            return {};
        return {std::move(path)};
    }
    std::vector<Crack510Point> rawPath() const {
        int n = Crack510CopyPath(handle_, nullptr, 0);
        if (n < 0)
            throw std::logic_error("Detector is not initialized.");
        std::vector<Crack510Point> path(n);
        if (n && Crack510CopyPath(handle_, path.data(), n) != n)
            throw std::runtime_error("Path copy failed.");
        return path;
    }
};
