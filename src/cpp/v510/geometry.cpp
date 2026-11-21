#include "internal.hpp"
namespace v510 {
static Point tipOf(const Mat &labels, int id, int right) {
    std::vector<double> ys;
    for (int y = 0; y < labels.rows; ++y)
        if (labels.at<int>(y, right) == id)
            ys.push_back(y);
    return {right, rnd(median(ys))};
}
static std::optional<Point> apex(const Mat &im, Point2d h) {
    int left = std::max(0, rnd(h.x) - px(.85)), right = std::min(im.cols, rnd(h.x) + px(1.));
    if (right - left < 10)
        return {};
    auto slab = im.colRange(left, right);
    auto v = sample(slab, 2, 2);
    double lo = quant(v, .03), hi = quant(v, .84);
    Mat cc, st, c;
    cv::connectedComponentsWithStats(morph(f32(slab) < (lo + .29 * (hi - lo)), cv::MORPH_OPEN, ellipse(5, 5)), cc,
                                     st, c);
    std::optional<Point> best;
    double loss = INFINITY;
    for (int i = 1; i < st.rows; ++i) {
        auto a = st.ptr<int>(i);
        if (a[0] > 2 || a[2] < 8 || a[0] + a[2] >= slab.cols - 1 || a[4] < 40)
            continue;
        int end = a[0] + a[2] - 1;
        std::vector<double> ys;
        for (int y = 0; y < im.rows; ++y)
            if (cc.at<int>(y, end) == i)
                ys.push_back(y);
        double y = median(ys), d = std::abs(y - rnd(h.y));
        Point pt(left + end, rnd(y));
        if (std::min(y, im.rows - 1 - y) >= 3 &&
            (d < loss || (d == loss && best && std::tie(pt.x, pt.y) < std::tie(best->x, best->y)))) {
            loss = d;
            best = pt;
        }
    }
    return best;
}
std::optional<Scene> prepare(const Mat &raw, const Mat &ref, Point2d h, Point2d rh) {
    if (raw.cols < 10 || raw.rows < 16)
        return {};
    int l = std::clamp(rnd(rh.x) + px(.45), 0, raw.cols - 8), r = std::clamp(rnd(rh.x) + px(1.8), l + 1, raw.cols);
    auto v = sample(ref, 3, 5);
    double lo = quant(v, .03), cut = lo + .43 * (quant(v, .85) - lo);
    int top = -1, bottom = 0, loss = INT_MAX, begin = 0;
    for (int y = 0; y <= raw.rows; ++y) {
        bool bright = y < raw.rows && median(sample(ref.row(y).colRange(l, r), 1, 3)) > cut;
        if (bright)
            continue;
        int d = std::max({begin - rnd(rh.y), rnd(rh.y) - y + 1, 0});
        if (y - begin >= 16 && d < loss) {
            loss = d;
            top = begin;
            bottom = y;
        }
        begin = y + 1;
    }
    if (top < 0)
        return {};
    int dy = rnd(h.y - rh.y);
    top += std::max(0, dy);
    bottom += std::min(0, dy);
    if (bottom - top < 12)
        return {};
    auto f = apex(ref.rowRange(top, bottom), rh - Point2d(0, top));
    if (!f)
        return {};
    auto a = apex(raw.rowRange(top, bottom), Point2d(*f) + h - rh);
    if (!a)
        return {};
    int rad = px(.23);
    Mat band = raw.rowRange(top, bottom);
    auto box = limit({a->x - 2 * rad, a->y - rad, 3 * rad + 1, 2 * rad + 1}, band);
    Mat patch = band(box);
    v = sample(patch);
    lo = quant(v, .03);
    double span = std::max(quant(v, .70) - lo, double(FLT_EPSILON));
    int k = 2 * px(.007) + 1;
    if (std::min(patch.cols, patch.rows) < k)
        return {};
    Mat labels, stats, centers;
    cv::connectedComponentsWithStats(morph(f32(patch) < (lo + .28 * span), cv::MORPH_OPEN, ellipse(k, k)), labels,
                                     stats, centers);
    int id = -1;
    double dist = INFINITY;
    Point end;
    for (int i = 1; i < stats.rows; ++i) {
        auto s = stats.ptr<int>(i);
        if (s[0] > px(.007) || s[2] < px(.035) || s[3] < k || s[4] < .0006 * scale * scale)
            continue;
        Point p = tipOf(labels, i, s[0] + s[2] - 1);
        std::vector<double> ys;
        for (int y = 0; y < labels.rows; ++y)
            if (labels.at<int>(y, p.x) == i)
                ys.push_back(y);
        p.y = int(median(ys));
        double d = cv::norm(box.tl() + p - *a);
        if (d < dist) {
            id = i;
            end = p;
            dist = d;
        }
    }
    if (id < 0)
        return {};
    std::vector<int> frontier(labels.rows, -1);
    std::vector<double> nose;
    for (int y = 0; y < labels.rows; ++y) {
        for (int x = 0; x < labels.cols; ++x)
            if (labels.at<int>(y, x) == id)
                frontier[y] = x;
        if (frontier[y] >= std::max(0, end.x - px(.04)))
            nose.push_back(y);
    }
    int mid = int(median(nose));
    std::vector<int> ys = {mid, end.y};
    for (int sign : {-1, 1}) {
        std::vector<int> half;
        for (int y = 0; y < labels.rows; ++y)
            if (frontier[y] >= std::max(0, end.x - px(.13)) && std::abs(y - mid) <= px(.15) &&
                sign * (y - mid) >= 0)
                half.push_back(y);
        if (!half.empty())
            for (int j = 0; j < 7; ++j)
                ys.push_back(half[rnd(j * ((half.size() - 1) / 6.))]);
    }
    std::vector<double> xs, yy;
    std::vector<int> visited;
    for (int y : ys)
        if (frontier[y] >= 0 && std::find(visited.begin(), visited.end(), y) == visited.end()) {
            visited.push_back(y);
            xs.push_back(box.x + frontier[y]);
            yy.push_back(top + box.y + y);
        }
    Point front = end + box.tl() + Point(0, top);
    int t = std::max(top, front.y - px(.27)), b = std::min(bottom, front.y + px(.27) + 1),
        x = std::max(0, front.x - px(.08));
    Rect sl(x, t, raw.cols - x, b - t);
    Mat local = raw(sl).clone(), med;
    cv::medianBlur(local, med, 3);
    auto sub = sample(f32(local) - f32(med), px(.012), px(.012));
    double m = median(sub);
    for (auto &val : sub)
        val = std::abs(val - m);
    return Scene{raw,
                 local,
                 sl,
                 {rnd(median(xs)), rnd(median(yy))},
                 rnd(median(yy) - t),
                 front.x - x,
                 int(median(yy)) - t,
                 top,
                 bottom,
                 std::max({.006 * span, 1.4826 * median(sub), 1e-6}),
                 span,
                 lo};
}
} // namespace v510