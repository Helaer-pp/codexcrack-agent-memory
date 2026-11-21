#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <numeric>
#include <opencv2/opencv.hpp>
#include <optional>
#include <tuple>
#include <vector>

namespace v510 {
using cv::Mat;
using cv::Point;
using cv::Point2d;
using cv::Rect;
using Path = std::vector<Point>;
using Pair = std::array<Point2d, 2>;
constexpr double scale = 288;
inline int rnd(double x) { return static_cast<int>(std::nearbyint(x)); }
inline int px(double f) { return std::max(1, rnd(scale * f)); }
inline double clip(double x, double lo = 0, double hi = 1) { return std::clamp(x, lo, hi); }
inline Mat f32(const Mat &m) {
    Mat out;
    m.convertTo(out, CV_32F);
    return out;
}
inline Mat blur(const Mat &m, int w, int h) {
    Mat out;
    cv::blur(m, out, {w, h}, {-1, -1}, cv::BORDER_DEFAULT | cv::BORDER_ISOLATED);
    return out;
}
inline Mat gauss(const Mat &m, double x, double y = 0) {
    Mat out;
    cv::GaussianBlur(m, out, {}, x, y, cv::BORDER_DEFAULT | cv::BORDER_ISOLATED);
    return out;
}
inline Mat morph(const Mat &m, int op, const Mat &k) {
    Mat out;
    cv::morphologyEx(m, out, op, k, {-1, -1}, 1, cv::BORDER_CONSTANT | cv::BORDER_ISOLATED);
    return out;
}
inline Mat kernel(int w, int h) { return Mat::ones(h, w, CV_8U); }
inline Mat ellipse(int w, int h) { return cv::getStructuringElement(cv::MORPH_ELLIPSE, {w, h}); }
inline Rect limit(Rect r, const Mat &a) { return r & Rect(0, 0, a.cols, a.rows); }
inline Mat shift(const Mat &m, int dx, int dy) {
    Mat e;
    cv::copyMakeBorder(m, e, std::max(0, -dy), std::max(0, dy), std::max(0, -dx), std::max(0, dx),
                       cv::BORDER_REPLICATE | cv::BORDER_ISOLATED);
    return e(Rect(std::max(0, dx), std::max(0, dy), m.cols, m.rows)).clone();
}
inline double quant(std::vector<double> v, double p) {
    if (v.empty())
        return 0;
    double k = p * (v.size() - 1);
    size_t lo = size_t(k), hi = size_t(std::ceil(k));
    std::nth_element(v.begin(), v.begin() + lo, v.end());
    double a = v[lo];
    if (lo == hi)
        return a;
    return a + (k - lo) * (*std::min_element(v.begin() + hi, v.end()) - a);
}
inline std::vector<double> sample(const Mat &src, int sy = 1, int sx = 1, int x0 = 0) {
    Mat a = f32(src);
    std::vector<double> v;
    for (int y = 0; y < a.rows; y += sy)
        for (int x = x0; x < a.cols; x += sx)
            v.push_back(a.at<float>(y, x));
    return v;
}
inline double median(const std::vector<double> &v) { return quant(v, .5); }
inline Point2d midpoint(const Pair &a) { return (a[0] + a[1]) * .5; }
struct Scene {
    Mat raw, local;
    Rect sl;
    Point center;
    int localCenterY;
    int front, mid, top, bottom;
    double noise, span, black;
};
struct Field {
    Mat score, seeds, gray, delta, ref, fine, core, red, dip, strength;
    bool joint = false, pre = false;
};
struct Found {
    Path path;
    int bridge = 0;
    bool notch = false;
};
std::optional<Scene> prepare(const Mat &, const Mat &, Point2d, Point2d);
Mat registerLocal(const Scene &, const Mat &);
Rect sceneBounds(cv::Size, const Pair &);
Mat registerFrame(const Mat &, const Mat &, const Pair &, const Pair &, Rect);
Field makeField(const Scene &, const Mat &);
Found detect(const Mat &, const Mat &, const Mat &, Point2d, Point2d);
} // namespace v510