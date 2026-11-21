#include "internal.hpp"
namespace v63 {
namespace {
Point2d correction(double y, const Window &w) {
    double t = clip((y - w.mid + 3.) / 6.);
    t = t * t * (3. - 2. * t);
    return Point2d(w.up) + t * Point2d(w.down - w.up);
}
Mat resample(const Mat &fixed, const Mapping &m) {
    Mat xmap(m.box.size(), CV_32F), ymap(m.box.size(), CV_32F);
    for (int y = 0; y < m.box.height; ++y) {
        int wy = m.box.y + y;
        float *xx = xmap.ptr<float>(y), *yy = ymap.ptr<float>(y);
        for (int x = 0; x < m.box.width; ++x) {
            xx[x] = float(m.box.x + x) + float(m.offset.x);
            yy[x] = float(wy) + float(m.offset.y);
        }
        for (const auto &w : m.windows) {
            auto shift = correction(wy, w);
            for (int x = w.x0 - m.box.x; x < w.x1 - m.box.x; ++x) {
                xx[x] = float(xx[x] + shift.x);
                yy[x] = float(yy[x] + shift.y);
            }
        }
    }
    Mat image;
    cv::remap(fixed, image, xmap, ymap, cv::INTER_LINEAR);
    Mat tile = f32(image);
    tile.setTo(NAN, (xmap < 0) | (ymap < 0) | (xmap >= fixed.cols - 1) | (ymap >= fixed.rows - 1));
    return tile;
}
struct Estimate {
    Point shift{};
    bool ok = false, low = false;
};
Estimate align(const Mat &cur, const Mat &ref, const Mat &allowed, Rect box, int mid, bool combined,
               double floor) {
    box &= Rect(5, 5, std::max(0, cur.cols - 10), std::max(0, cur.rows - 10));
    if (box.width < 11 || box.height < 11)
        return {};
    Mat mask = f32(allowed(box)) / 255.;
    if (combined) {
        int lo = std::max(0, mid - 3 - box.y), hi = std::min(box.height, mid + 4 - box.y);
        if (hi > lo)
            mask.rowRange(lo, hi).setTo(0);
    }
    double n = cv::sum(mask)[0];
    if (n < .35 * mask.total())
        return {};
    Mat patch = cur(box);
    Mat tpl = (patch - cv::sum(patch.mul(mask))[0] / n).mul(mask);
    double energy = tpl.dot(tpl);
    if (energy / n < floor * floor)
        return {{}, false, true};
    Mat block = ref(Rect(box.x - 5, box.y - 5, box.width + 10, box.height + 10));
    auto corr = [](const Mat &a, const Mat &b) {
        Mat out;
        cv::matchTemplate(a, b, out, cv::TM_CCORR);
        return out;
    };
    Mat sum = corr(block, mask), variance = corr(block.mul(block), mask) - sum.mul(sum) / n;
    cv::max(variance, 1e-5, variance);
    cv::sqrt(variance * energy, variance);
    Mat scores = corr(block, tpl) / variance;
    Point bestAt;
    double best, other;
    cv::minMaxLoc(scores, nullptr, &best, nullptr, &bestAt);
    best = clip(best, -1, 1);
    scores(limit(Rect(bestAt.x - 2, bestAt.y - 2, 5, 5), scores)).setTo(-1);
    cv::minMaxLoc(scores, nullptr, &other);
    return {bestAt - Point(5, 5), best >= .84 && best - other >= .012, false};
}
} // namespace
Point2d Mapping::referencePoint(Point2d p) const {
    for (const auto &w : windows)
        if (p.x >= w.x0 && p.x < w.x1)
            return p + offset + correction(p.y, w);
    return p + offset;
}
Mapping mapReference(const Mat &image, const Mat &ref, Rect box, Point2d offset, const Scene &p, int stop) {
    int front = box.x + p.sl.x + p.front, mid = box.y + p.sl.y + p.mid;
    int half = rnd((p.local.total() > 250000 ? .23 : .51) * scale);
    int x = std::max(box.x, front - px(.08)), top = std::max(box.y + p.top, mid - half);
    int right = box.x + std::min(stop, box.width), bot = std::min(box.y + p.bottom, mid + half + 1);
    Mapping m;
    m.box = Rect(x, top, right - x, bot - top);
    m.offset = offset;
    Mat base = resample(ref, m), cur = f32(image(m.box));
    double floor = std::max(5., 2 * p.noise);
    Mat good;
    cv::erode(base > floor, good, kernel(11, 11), {-1, -1}, 1, cv::BORDER_CONSTANT, 0);
    Mat allowed = (cur > floor) & good;
    Mat ca = cur - 255., rb = base - 255.;
    cv::patchNaNs(rb, 0);
    int stride = std::clamp(px(.45), 48, 160), depth = std::clamp(px(.16), 12, 48), cy = mid - top;
    for (int start = front; start < right; start += stride) {
        int end = std::min(right, start + stride);
        auto estimate = [&](int a, int b, bool combined = false) {
            return align(ca, rb, allowed, Rect(start - x, a, end - start, b - a), cy, combined,
                         std::max(1.8 * p.noise, .02 * p.span));
        };
        auto up = estimate(cy - depth, cy - 3), down = estimate(cy + 4, cy + depth + 1);
        Estimate single;
        if (!up.ok || !down.ok)
            single = estimate(cy - depth, cy + depth + 1, true);
        auto choose = [&](Estimate e) { return e.ok ? e.shift : single.ok ? single.shift : Point(); };
        Mat column = base.colRange(start - x, end - x);
        bool white = cv::countNonZero(column >= 250) >= .5 * column.total();
        m.windows.push_back({start, end, mid, choose(up), choose(down), up.ok || down.ok || single.ok,
                             white && up.low && down.low && !single.ok});
    }
    m.tile = resample(ref, m);
    return m;
}
} // namespace v63
