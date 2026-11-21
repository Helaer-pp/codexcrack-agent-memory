#include "internal.hpp"
namespace v63 {
static Point tipOf(const Mat &labels, int id, int right) {
    std::vector<double> ys;
    for (int y = 0; y < labels.rows; ++y)
        if (labels.at<int>(y, right) == id)
            ys.push_back(y);
    return {right, rnd(median(ys))};
}
static std::optional<Point> scan(const Mat &im, Point2d h, int left, int right, bool edge) {
    if (right - left < 10)
        return {};
    auto slab = im.colRange(left, right);
    auto v = sample(slab, 2, 2);
    double lo = quant(v, .03), hi = quant(v, .84);
    Mat cc, st, c;
    cv::connectedComponentsWithStats(morph(f32(slab) < (lo + .29 * (hi - lo)), cv::MORPH_OPEN, ellipse(5, 5)),
                                     cc, st, c);
    std::optional<Point> best;
    double loss = INFINITY;
    for (int i = 1; i < st.rows; ++i) {
        auto a = st.ptr<int>(i);
        if ((edge && a[0] > 2) || a[2] < 8 || a[0] + a[2] >= slab.cols - 1 || a[4] < 40)
            continue;
        int end = a[0] + a[2] - 1;
        std::vector<double> ys;
        for (int y = 0; y < im.rows; ++y)
            if (cc.at<int>(y, end) == i)
                ys.push_back(y);
        double y = median(ys),
               d = std::abs(y - (edge ? rnd(h.y) : h.y)) + (edge ? 0. : .15 * std::abs(left + end - h.x));
        Point pt(left + end, rnd(y));
        if (std::min(y, im.rows - 1 - y) >= 3 &&
            (d < loss || (d == loss && best && std::tie(pt.x, pt.y) < std::tie(best->x, best->y)))) {
            loss = d;
            best = pt;
        }
    }
    return best;
}
static std::optional<Point> locate(const Mat &im, Point2d hint, bool reference) {
    int l = std::max(0, rnd(hint.x) - px(.85)), r = std::min(im.cols, rnd(hint.x) + px(1.));
    auto edge = scan(im, hint, l, r, true);
    if (edge)
        return edge;
    if (!reference)
        return scan(im, hint, l, r, false);
    auto coarse = scan(im, hint, 0, im.cols, false);
    if (!coarse)
        return {};
    int top = std::max(0, coarse->y - px(.45)), bot = std::min(im.rows, coarse->y + px(.45) + 1);
    auto fine = scan(im.rowRange(top, bot), Point2d(*coarse) - Point2d(0, top),
                     std::max(0, coarse->x - px(1.25)), std::min(im.cols, coarse->x + px(.20) + 1), false);
    if (!fine)
        return {};
    fine->y += top;
    return std::max(std::abs(fine->x - coarse->x), std::abs(fine->y - coarse->y)) <= .2 * scale ? fine
                                                                                                : std::nullopt;
}
static double physicalScale(const Mat &ref, Point p) {
    Mat area = ref(limit(Rect(p.x - 8, p.y - 64, 41, 129), ref));
    auto values = sample(area);
    double low = quant(values, .08), cut = low + .30 * (quant(values, .85) - low);
    std::vector<double> widths;
    for (int back : {2, 4, 6}) {
        int x = std::max(0, p.x - back), start = 0, best = 0;
        for (int y = 0; y <= ref.rows; ++y) {
            if (y < ref.rows && ref.at<uchar>(y, x) < cut)
                continue;
            if (y > start && start - 2 <= p.y && p.y < y + 2)
                best = std::max(best, y - start);
            start = y + 1;
        }
        if (best)
            widths.push_back(best);
    }
    return clip(11.5 * clip(widths.empty() ? 4. : median(widths), 4., 32.), 64., 384.);
}
static bool quietMouth(const Mat &a, const Mat &b, Point p, Point q) {
    int half = std::min({std::max(5, px(.055)), p.y, q.y, a.rows - 1 - p.y, b.rows - 1 - q.y});
    int width = std::min({px(.13), a.cols - p.x, b.cols - q.x});
    if (half < 4 || width < 8)
        return false;
    auto patch = [&](const Mat &im, Point pt) {
        Mat out;
        cv::GaussianBlur(f32(im(Rect(pt.x, pt.y - half, width, 2 * half + 1))), out, {3, 3}, .75);
        return out;
    };
    Mat cur = patch(a, p), ref = patch(b, q), med;
    Rect core(2, 2, width - 4, cur.rows - 4);
    double best = 255, lo, hi;
    cv::minMaxLoc(ref, &lo, &hi);
    cv::medianBlur(cur, med, 3);
    for (int y = -1; y <= 1; ++y)
        for (int x = -1; x <= 1; ++x) {
            auto vals = sample(ref(core + Point(x, y)) - cur(core));
            auto bias = median(vals);
            for (auto &v : vals)
                v = std::abs(v - bias);
            best = std::min(best, quant(vals, .95));
        }
    return best <= std::max({4., .035 * (hi - lo), 3 * median(sample(cv::abs(cur - med)))});
}
std::optional<Scene> prepareScene(const Mat &raw, const Mat &ref, Point2d h, Point2d rh) {
    if (raw.cols < 10 || raw.rows < 16)
        return {};
    scale = 288.;
    std::vector<double> v, profile;
    for (int y = 0; y < ref.rows; ++y) {
        std::vector<double> row;
        for (int x = ref.cols - 1; x >= 0; x -= 7)
            row.push_back(ref.at<uchar>(y, x));
        if (y % 3 == 0)
            v.insert(v.end(), row.begin(), row.end());
        profile.push_back(median(row));
    }
    double lo = quant(v, .03), hi = quant(v, .85);
    if (hi <= lo)
        lo = *std::min_element(v.begin(), v.end());
    double cut = lo + .43 * (hi - lo);
    int top = -1, bottom = 0, begin = 0;
    double loss = INFINITY;
    for (int y = 0; y <= raw.rows; ++y) {
        bool bright = y < raw.rows && profile[y] > cut;
        if (bright)
            continue;
        double d = std::max({begin - rh.y, rh.y - y + 1., 0.});
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
    auto f = locate(ref.rowRange(top, bottom), rh - Point2d(0, top), true);
    if (!f)
        return {};
    auto a = locate(raw.rowRange(top, bottom), Point2d(*f) + h - rh, false);
    if (!a)
        return {};
    scale = physicalScale(ref.rowRange(top, bottom), *f);
    bool quiet = quietMouth(raw.rowRange(top, bottom), ref.rowRange(top, bottom), *a, *f);
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
    cv::connectedComponentsWithStats(morph(f32(patch) < (lo + .28 * span), cv::MORPH_OPEN, ellipse(k, k)),
                                     labels, stats, centers);
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
    return Scene{{raw,
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
                  lo},
                 quiet,
                 int(*std::min_element(yy.begin(), yy.end())) - t,
                 int(*std::max_element(yy.begin(), yy.end())) - t,
                 median(yy) - t};
}
} // namespace v63