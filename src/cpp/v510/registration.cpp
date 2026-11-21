#include "internal.hpp"
namespace v510 {
Rect sceneBounds(cv::Size size, const Pair &p) {
    double s = cv::norm(p[1] - p[0]);
    int x = std::max(0, int(std::floor(std::min(p[0].x, p[1].x) - .6 * s)));
    int y = std::max(0, int(std::floor(p[0].y - .35 * s)));
    int b = std::min(size.height, int(std::ceil(p[1].y + .35 * s)) + 1);
    return {x, y, size.width - x, b - y};
}
static double corrSubset(const Mat &a, const Mat &b, int parity) {
    double sx = 0, sy = 0, xx = 0, yy = 0, xy = 0, n = 0;
    for (int y = parity; y < a.rows; y += 2)
        for (int x = parity; x < a.cols; x += 2) {
            double u = a.at<float>(y, x), v = b.at<float>(y, x);
            sx += u;
            sy += v;
            xx += u * u;
            yy += v * v;
            xy += u * v;
            ++n;
        }
    double den = std::sqrt(std::max(0., (xx - sx * sx / n) * (yy - sy * sy / n)));
    return den > 1e-7 ? (xy - sx * sy / n) / den : 0;
}
Mat registerFrame(const Mat &ref, const Mat &raw, const Pair &rp, const Pair &cp, Rect box) {
    Mat mx(box.size(), CV_32F), my(mx.size(), CV_32F), valid(mx.size(), CV_8U);
    double s = cv::norm(cp[1] - cp[0]);
    for (int y = 0; y < mx.rows; ++y) {
        float a = float(clip((box.y + y - cp[0].y) / std::max(1., cp[1].y - cp[0].y)));
        Point2d d = (cp[0] - rp[0]) * (1.f - a) + (cp[1] - rp[1]) * a;
        for (int x = 0; x < mx.cols; ++x) {
            float u = float(x + box.x - d.x), v = float(y + box.y - d.y);
            mx.at<float>(y, x) = u;
            my.at<float>(y, x) = v;
            valid.at<uchar>(y, x) = u >= 0 && v >= 0 && u < ref.cols - 1 && v < ref.rows - 1;
        }
    }
    Mat coarse;
    cv::remap(ref, coarse, mx, my, cv::INTER_LINEAR);
    coarse = f32(coarse);
    Mat cur = f32(raw(box));
    for (int x = 5, tile = 0; x < box.width - 5 && tile < 200; x += 96, ++tile) {
        int w = std::min(96, box.width - 5 - x);
        if (w < 12 || box.height < 42)
            continue;
        std::array<Point, 2> moves;
        int ys[2];
        bool good = true;
        for (int i = 0; i < 2; ++i) {
            int y = std::clamp(rnd(cp[i].y + (i ? .18 : -.18) * s - box.y) - 16, 5, box.height - 37);
            ys[i] = y + box.y;
            Rect check(x - 5, y - 5, w + 10, 42), r(x, y, w, 32);
            Mat a = cur(r), b = coarse(r);
            cv::Scalar mu, sa, sb;
            cv::meanStdDev(a, mu, sa);
            cv::meanStdDev(b, mu, sb);
            if (cv::countNonZero(valid(check)) != check.area() || sa[0] < 2 || sb[0] < 2 ||
                cv::countNonZero((a >= 75) & (b >= 75)) < .65 * r.area()) {
                good = false;
                break;
            }
            Mat scores;
            cv::matchTemplate(coarse(check), a, scores, cv::TM_CCOEFF_NORMED);
            Point pos;
            double peak;
            cv::minMaxLoc(scores, nullptr, &peak, nullptr, &pos);
            moves[i] = pos - Point(5, 5);
            Mat matched = coarse(r + moves[i]);
            if (peak < .78 || std::min(corrSubset(matched, a, 0), corrSubset(matched, a, 1)) < .73 ||
                std::abs(median(sample(matched - a))) > 22) {
                good = false;
                break;
            }
        }
        if (good)
            for (int y = 0; y < mx.rows; ++y) {
                float f = float(clip(double(box.y + y - ys[0]) / std::max(1, ys[1] - ys[0])));
                for (int j = x; j < x + w; ++j) {
                    mx.at<float>(y, j) += (1 - f) * moves[0].x + f * moves[1].x;
                    my.at<float>(y, j) += (1 - f) * moves[0].y + f * moves[1].y;
                }
            }
    }
    Mat out;
    cv::remap(ref, out, mx, my, cv::INTER_LINEAR);
    out = f32(out);
    out.setTo(NAN, (mx < 0) | (my < 0) | (mx >= ref.cols - 1) | (my >= ref.rows - 1));
    return out;
}
struct Match {
    bool ok = false;
    Point shift{};
    double margin = 0;
};
template <class Mask>
static Match align(const Mat &cur, const Mat &ref, Rect roi, int s, Point off, double noise, double span,
                   Mask accept) {
    int x = std::max({roi.x, 0, s - off.x}), y = std::max({roi.y, 0, s - off.y});
    int r = std::min({roi.br().x, cur.cols, cur.cols - s - off.x}),
        b = std::min({roi.br().y, cur.rows, cur.rows - s - off.y});
    if (r - x < 2 * s + 1 || b - y < 2 * s + 1)
        return {};
    Rect box(x, y, r - x, b - y);
    Mat search = ref(Rect(x + off.x - s, y + off.y - s, r - x + 2 * s, b - y + 2 * s)).clone();
    Mat invalid = morph(search != search, cv::MORPH_DILATE, kernel(2 * s + 1, 2 * s + 1)), mask(box.size(), CV_32F);
    cv::patchNaNs(search, 0);
    for (int j = 0; j < mask.rows; ++j)
        for (int k = 0; k < mask.cols; ++k)
            mask.at<float>(j, k) = accept(k + x, j + y) && !invalid.at<uchar>(j + s, k + s);
    double n = cv::sum(mask)[0];
    if (n < .35 * box.area())
        return {};
    Mat a = cur(box);
    Mat tpl = (a - cv::sum(a.mul(mask))[0] / n).mul(mask);
    double e = tpl.dot(tpl);
    if (e / n < std::pow(std::max(1.8 * noise, .02 * span), 2))
        return {};
    Mat sum, sq, dot;
    cv::matchTemplate(search, mask, sum, cv::TM_CCORR);
    cv::matchTemplate(search.mul(search), mask, sq, cv::TM_CCORR);
    cv::matchTemplate(search, tpl, dot, cv::TM_CCORR);
    Mat denom;
    cv::sqrt(cv::max(sq - sum.mul(sum) / n, 1e-5) * e, denom);
    Mat scores = dot / denom;
    double best, second;
    Point pos;
    cv::minMaxLoc(scores, nullptr, &best, nullptr, &pos);
    best = clip(best, -1, 1);
    int rad = std::max(1, rnd(.32 * s));
    scores(limit(Rect(pos.x - rad, pos.y - rad, 2 * rad + 1, 2 * rad + 1), scores)).setTo(-1);
    cv::minMaxLoc(scores, nullptr, &second);
    return {best >= .75 && best - second >= .012, pos + off - Point(s, s), best - second};
}
static Match contour(const Scene &p, const Mat &ref) {
    Point c = p.center;
    int r = px(.24), b = px(.025), l = c.x - px(.30), w = c.x - l + 1;
    if (l < b || c.x + b >= ref.cols || c.y - r < 0 || c.y + r >= ref.rows)
        return {};
    auto edges = [&](const Mat &im, int dx) {
        Mat a = f32(im(Rect(l + dx, c.y - r, w, 2 * r + 1)));
        std::vector<Point> e(w, {-1, -1});
        if (cv::countNonZero(a != a))
            return e;
        auto v = sample(a);
        double low = quant(v, .12), span = quant(v, .85) - low;
        if (span < std::max(8 * p.noise, .28 * p.span))
            return e;
        Mat mask = a < (low + .40 * span);
        for (int x = 0; x < w; ++x) {
            int t = 0, k = 2 * r;
            while (t <= k && !mask.at<uchar>(t, x))
                ++t;
            while (k >= t && !mask.at<uchar>(k, x))
                --k;
            if (k - t > px(.035) && t > 0 && k < 2 * r && mask.at<uchar>(r, x))
                e[x] = {t, k};
        }
        return e;
    };
    auto cur = edges(p.raw, 0);
    double loss = INFINITY;
    Match result;
    for (int dx = -b; dx <= b; ++dx) {
        auto f = edges(ref, dx);
        std::vector<double> mid, gaps, dev;
        for (int j = 0; j < w; ++j)
            if (cur[j].x >= 0 && f[j].x >= 0) {
                auto d = f[j] - cur[j];
                mid.push_back(.5 * (d.x + d.y));
                gaps.push_back(cur[j].y - cur[j].x);
                dev.push_back(d.x);
                dev.push_back(d.y);
            }
        if (mid.size() < .75 * w)
            continue;
        auto mm = std::minmax_element(gaps.begin(), gaps.end());
        if (*mm.second - *mm.first < px(.04))
            continue;
        int dy = rnd(median(mid));
        for (auto &z : mid)
            z = std::abs(z - dy);
        for (auto &z : dev)
            z = std::abs(z - dy);
        double cost = median(mid) + .3 * std::accumulate(dev.begin(), dev.end(), 0.) / dev.size() +
                      .08 * (std::abs(dx) + std::abs(dy));
        if (std::abs(dy) <= b && quant(dev, .85) <= px(.022) && cost < loss) {
            loss = cost;
            result = {true, {dx, dy}, 0};
        }
    }
    return result;
}
Mat registerLocal(const Scene &p, const Mat &ref) {
    Mat a = f32(p.raw), b = ref.clone(), bad = b != b;
    a.copyTo(b, bad);
    Mat ta = a - gauss(a, .018 * scale), tb = b - gauss(b, .018 * scale);
    tb.setTo(NAN, bad);
    Point c = p.center;
    auto box = [](Point pt, double l, double t, double r, double b) {
        return Rect(pt.x - px(l), pt.y - px(t), px(l) + px(r), px(t) + px(b));
    };
    Match m = align(ta, tb, box(c, .40, .23, .52, .23), px(.04), {}, p.noise, p.span,
                    [&](int x, int y) { return x < c.x - px(.05) || std::abs(y - c.y) > px(.04); });
    if (!m.ok) {
        Match sides[2];
        for (int i = 0; i < 2; ++i) {
            Point pt = c + Point(0, (2 * i - 1) * px(.22));
            sides[i] = align(ta, tb, box(pt, .22, .12, .50, .12), px(.04), {}, p.noise, p.span,
                             [](int, int) { return true; });
        }
        if (sides[0].ok && sides[1].ok && cv::norm(sides[0].shift - sides[1].shift) <= px(.01))
            m = sides[sides[1].margin > sides[0].margin];
    }
    if (!m.ok)
        m = contour(p, ref);
    if (!m.ok)
        return {};
    Point q(std::min(p.local.cols - 1, p.front + px(.24)), p.localCenterY);
    for (int i = 0; i < 2; ++i) {
        auto local =
            align(ta(p.sl), tb(p.sl), i ? box(q, .32, .24, .15, .24) : box(q, .21, .12, .11, .12), px(.015),
                  m.shift, p.noise, p.span, [&](int, int y) { return std::abs(y - q.y) > px(i ? .05 : .027); });
        if (local.ok) {
            m = local;
            break;
        }
    }
    Mat out;
    cv::warpAffine(ref(p.sl), out, cv::Matx23f(1, 0, float(m.shift.x), 0, 1, float(m.shift.y)), p.sl.size(),
                   cv::INTER_NEAREST | cv::WARP_INVERSE_MAP, cv::BORDER_CONSTANT, cv::Scalar(NAN));
    return out;
}
} // namespace v510