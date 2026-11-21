#include "internal.hpp"
namespace v63 {
struct Lattice {
    Mat values, dirs, back;
    Point best{-1, -1};
    Path trace(Point p) const {
        Path out;
        if (p.x < 0)
            return out;
        int d = dirs.at<signed char>(p);
        while (p.x >= 0 && d >= 0) {
            out.push_back(p);
            int k = back.ptr<signed char>(p.y)[5 * p.x + d];
            if (k < 0)
                break;
            p += Point(-1, 2 - d);
            d = k;
        }
        std::reverse(out.begin(), out.end());
        return out;
    }
    Lattice(const Mat &field, const Mat &seed, bool joint) {
        values = Mat(field.size(), CV_32F, cv::Scalar(-INFINITY));
        dirs = Mat(field.size(), CV_8S, cv::Scalar(-1));
        back = Mat(field.rows, field.cols * 5, CV_8S, cv::Scalar(-2));
        using State = std::array<float, 5>;
        State empty;
        empty.fill(-INFINITY);
        std::vector<State> prev(field.rows, empty), next = prev;
        double peak = 0;
        int low = field.rows, high = -1;
        for (int x = 0; x < field.cols; ++x) {
            int a = std::max(0, low - 2), b = std::min(field.rows, high + 3);
            if (x < seed.cols)
                for (int y = 0; y < field.rows; ++y)
                    if (seed.at<uchar>(y, x)) {
                        a = std::min(a, y);
                        b = std::max(b, y + 1);
                    }
            std::fill(next.begin(), next.end(), empty);
            int newLow = field.rows, newHigh = -1;
            double floor = -(joint && x <= .24 * scale ? .105 : .025) * scale;
            for (int y = a; y < b; ++y) {
                double val = field.at<float>(y, x);
                auto bk = back.ptr<signed char>(y) + 5 * x;
                if (x < seed.cols && seed.at<uchar>(y, x)) {
                    next[y][2] = float(std::max(0., val));
                    bk[2] = -1;
                }
                for (int d = 0; d < 5; ++d) {
                    int yy = y - d + 2;
                    if (yy >= low && yy <= high) {
                        double bestCost = -INFINITY;
                        int arg = -1;
                        for (int k = 0; k < 5; ++k) {
                            double c = prev[yy][k] - .19 * std::abs(d - k);
                            if (c > bestCost) {
                                bestCost = c;
                                arg = k;
                            }
                        }
                        double v = bestCost - .13 * std::abs(d - 2) + val;
                        if (v > next[y][d] && v >= floor) {
                            next[y][d] = float(v);
                            bk[d] = static_cast<signed char>(arg);
                        }
                    }
                    float v = next[y][d];
                    if (v > values.at<float>(y, x)) {
                        values.at<float>(y, x) = v;
                        dirs.at<signed char>(y, x) = static_cast<signed char>(d);
                    }
                    if (v > peak) {
                        best = {x, y};
                        peak = v;
                    }
                }
                if (std::isfinite(values.at<float>(y, x))) {
                    newLow = std::min(newLow, y);
                    newHigh = std::max(newHigh, y);
                }
            }
            low = newLow;
            high = newHigh;
            if (high < 0 && x + 1 >= seed.cols)
                break;
            prev.swap(next);
        }
    }
};
static std::vector<double> increments(const Mat &f, const Path &path) {
    std::vector<double> r;
    int last = 0;
    for (size_t i = 0; i < path.size(); ++i) {
        int d = i ? path[i].y - path[i - 1].y : 0;
        r.push_back(f.at<float>(path[i]) - .13 * std::abs(d) - .19 * std::abs(d - last));
        last = d;
    }
    if (!r.empty())
        r[0] = std::max(0., r[0]);
    return r;
}
static bool closed(const Mat &g, const Path &path) {
    Point end = path.back();
    Rect box = cv::boundingRect(path);
    int pad = px(.10);
    box = limit(Rect(box.x - pad, box.y - pad, box.width + 2 * pad, box.height + 2 * pad), g);
    Mat patch = g(box);
    auto sampleGray = sample(patch);
    std::vector<double> ink;
    for (auto p : path)
        ink.push_back(g.at<float>(p));
    double dark = median(ink);
    for (int pass = 0; pass < 2; ++pass) {
        double cut = pass ? .7 * quant(sampleGray, .75) + .3 * dark : .5 * (quant(sampleGray, .70) + dark);
        Mat mask = patch < cut;
        if (pass)
            mask = morph(mask, cv::MORPH_CLOSE, ellipse(2 * px(.004) + 1, 2 * px(.004) + 1));
        std::vector<Path> contours;
        std::vector<cv::Vec4i> tree;
        cv::findContours(mask, contours, tree, cv::RETR_CCOMP, cv::CHAIN_APPROX_SIMPLE);
        for (size_t i = 0; i < tree.size(); ++i) {
            if (tree[i][3] < 0)
                continue;
            Rect r = cv::boundingRect(contours[i]) + box.tl();
            int x = r.br().x - 1;
            double area = cv::contourArea(contours[i]);
            if (pass) {
                if (area >= .00045 * scale * scale && r.width > .045 * scale && r.height > .014 * scale &&
                    std::abs(end.x - x) < .033 * scale && end.y >= r.y - .025 * scale &&
                    end.y <= r.br().y + .025 * scale)
                    return true;
            } else if (r.width >= .045 * scale && r.height >= .018 * scale && area >= .0005 * scale * scale &&
                       std::abs(end.x - x) <= .025 * scale && end.y >= r.y - .02 * scale &&
                       end.y <= r.br().y + .02 * scale && path.front().x <= x - r.width / 2.)
                return true;
        }
        if (!pass && end.x < .055 * scale &&
            std::abs(end.y - path.front().y) > .55 * std::max(1, end.x - path.front().x)) {
            Mat dist;
            cv::distanceTransform(mask, dist, cv::DIST_L2, 3);
            std::vector<double> ds;
            for (auto pt : path)
                ds.push_back(dist.at<float>(pt - box.tl()));
            if (median(ds) >= .003 * scale)
                return false;
        }
    }
    return false;
}
struct Mouth {
    Mat dark, added, glare, diff;
};
static Mouth profile(const Evidence &f, const Scene &p) {
    int n = std::min(f.score.cols, px(.27) + 1), r = std::max(2, px(.008));
    Mat g = f.gray.colRange(0, n), ref = f.ref.colRange(0, n), d = f.delta.colRange(0, n);
    auto contrast = [&](const Mat &im) -> Mat {
        return cv::max(im - cv::max(shift(im, 0, r), shift(im, 0, -r)), 0.);
    };
    double floor = std::max(2.8 * p.noise, .028 * p.span);
    Mat z = contrast(-g);
    return {z / cv::max(d, floor), cv::max(z - contrast(-ref), 0.) / floor,
            (morph(g, cv::MORPH_DILATE, kernel(1, 2 * px(.030) + 1)) - g) / p.span, d / floor};
}
static bool deadMouth(const Path &path, const Mat &field, const Mouth &m) {
    Point p = path.back();
    if (p.x >= m.dark.cols - px(.018))
        return false;
    int n = std::min(int(path.size()), std::max(3, px(.025))), core = 0, newCore = 0, glare = 0, inc = 0;
    for (auto it = path.end() - n; it != path.end(); ++it) {
        bool c = m.dark.at<float>(*it) > .22;
        core += c;
        newCore += c && m.added.at<float>(*it) > .5;
        glare += m.glare.at<float>(*it) > .12;
        inc += m.diff.at<float>(*it) > 1;
    }
    int y0 = std::max(0, p.y - 1), y1 = std::min(field.rows, p.y + 2);
    auto col = [&](const Mat &mat, int x) {
        double mx;
        cv::minMaxLoc(mat(Rect(x, y0, 1, y1 - y0)), nullptr, &mx);
        return mx;
    };
    int ahead = std::min(px(.018), field.cols - p.x - 1), fall = 0;
    for (int j = 1; j <= ahead; ++j)
        fall += col(field, p.x + j) < -.15;
    bool cliff = ahead && fall >= .60 * ahead;
    int width = std::min(m.dark.cols - p.x, 1 + px(.015)), flat = 0;
    for (int j = 0; j < width; ++j)
        flat += col(m.dark, p.x + j) < .22 && col(m.diff, p.x + j) > 1;
    return inc >= .48 * n &&
           ((core < .36 * n && (glare >= .35 * n || cliff)) ||
            (cliff && glare >= .70 * n &&
             (newCore < .36 * n || (p.x - path.front().x <= .055 * scale && 3 * flat >= width))));
}

static Mat physical(const Evidence &f, const Scene &p) {
    int radius = px(.012);
    Mat high = morph(f.gray, cv::MORPH_DILATE, kernel(1, 2 * radius + 1));
    Mat low = morph(f.gray, cv::MORPH_ERODE, kernel(1, 2 * radius + 1));
    Mat result(f.gray.size(), CV_32F);
    double span = std::max(1., p.span), floor = std::max({1., 2.7 * p.noise, .030 * span});
    for (int x = 0; x < result.cols; ++x) {
        double weight = .36 + .38 * std::exp(-x / (.14 * scale));
        for (int y = 0; y < result.rows; ++y) {
            Point pt(x, y);
            double prior = f.score.at<float>(pt), d = f.delta.at<float>(pt);
            double bright = clip((f.gray.at<float>(pt) - p.black - .68 * span) / (.27 * span));
            double reflect =
                bright * clip(1 - (high.at<float>(pt) - low.at<float>(pt)) / std::max(4 * p.noise, .12 * span));
            double red = std::tanh(std::max(0., d) / (2 * floor)) * std::tanh(f.strength.at<float>(pt) / 2.);
            double blue = std::tanh(std::max(0., -d) / (2 * floor));
            double gain = red * (f.core.at<uchar>(pt) ? 1. : .45) + .35 * bool(f.dual.at<uchar>(pt));
            double net = 1.65 * gain + weight * clip(prior, -1.2, 1.4) -
                         (.72 - .53 * reflect) * (1 - clip(gain)) - .85 * blue -
                         .40 * bool(f.dip.at<uchar>(pt)) - .14;
            result.at<float>(pt) = std::isfinite(prior) ? float(net) : -INFINITY;
        }
    }
    return result;
}
static double trimPeak(Path &path, const Mat &field, const Mat &dual) {
    auto inc = increments(field, path);
    int n = int(path.size()), reach = std::max(2, px(.025));
    for (int a = 0; a < n;) {
        if (dual.at<uchar>(path[a])) {
            ++a;
            continue;
        }
        int b = a + 1;
        while (b < n && !dual.at<uchar>(path[b]))
            ++b;
        int left = std::max(0, a - 1), right = std::min(n - 1, b);
        int k = std::max(0, left - reach), j = std::min(n - 1, right + reach);
        double incoming = double(path[left].y - path[k].y) / std::max(1, left - k);
        double outgoing = double(path[j].y - path[right].y) / std::max(1, j - right);
        inc[right] -=
            .32 * std::abs(path[right].y - path[left].y - clip(incoming, -1, 1) * std::max(1, right - left)) +
            1.15 * std::abs(std::atan(incoming) - std::atan(outgoing));
        a = b;
    }
    std::partial_sum(inc.begin(), inc.end(), inc.begin());
    auto at = std::max_element(inc.begin(), inc.end());
    path.resize(at - inc.begin() + 1);
    return *at;
}
struct Search {
    Path path;
    bool reached = false, dead = false;
};
static Search search(const Scene &s, const Mapping &m, Rect box) {
    Rect region = s.sl + box.tl();
    Mat aligned(s.local.size(), CV_32F, cv::Scalar(NAN));
    Rect overlap = m.box & region;
    if (!overlap.empty())
        m.tile(overlap - m.box.tl()).copyTo(aligned(overlap - region.tl()));
    Evidence f = makeEvidence(s, aligned);
    int lo = std::clamp(s.mid - px(.23), 0, s.local.rows),
        hi = std::clamp(s.mid + px(.23) + 1, 0, s.local.rows);
    for (Rect rect : {Rect(0, 0, f.score.cols, lo), Rect(0, hi, f.score.cols, f.score.rows - hi)}) {
        if (rect.empty())
            continue;
        f.score(rect).setTo(-INFINITY);
        f.seeds(Rect(0, rect.y, f.seeds.cols, rect.height)).setTo(0);
    }
    Mat scores = f.joint ? physical(f, s) : f.score;
    std::vector<std::vector<int>> groups;
    for (int y = 0; y < f.seeds.rows; ++y)
        if (cv::countNonZero(f.seeds.row(y))) {
            if (groups.empty() || y - groups.back().back() > px(.008))
                groups.emplace_back();
            groups.back().push_back(y);
        }
    while (groups.size() > 3) {
        int idx = 0;
        for (int j = 1; j + 1 < int(groups.size()); ++j)
            if (groups[j + 1][0] - groups[j].back() < groups[idx + 1][0] - groups[idx].back())
                idx = j;
        groups[idx].insert(groups[idx].end(), groups[idx + 1].begin(), groups[idx + 1].end());
        groups.erase(groups.begin() + idx + 1);
    }
    if (groups.size() == 1 && groups[0].size() >= std::max(8., .038 * scale)) {
        auto all = groups[0];
        auto split = all.begin() + (all.size() + 1) / 2;
        groups = {{all.begin(), split}, {split, all.end()}};
    }
    std::vector<double> centers;
    for (auto &gr : groups)
        centers.push_back(median(std::vector<double>(gr.begin(), gr.end())));
    int width = f.seeds.cols;
    double gap = INFINITY;
    for (size_t j = 1; j < centers.size(); ++j)
        gap = std::min(gap, centers[j] - centers[j - 1]);
    if (groups.size() > 1)
        width = std::min(f.score.cols, std::max(width, rnd(3 * gap)));
    Search result;
    double best = -INFINITY;
    bool mapped = std::any_of(m.windows.begin(), m.windows.end(), [](auto &w) { return w.mapped; });
    Mouth mouth;
    if (f.joint)
        mouth = profile(f, s);
    for (int j = 0; j < int(groups.size()); ++j) {
        Mat field = scores.clone(), entry = Mat::zeros(f.seeds.size(), CV_8U);
        for (int y : groups[j])
            f.seeds.row(y).copyTo(entry.row(y));
        if (groups.size() > 1)
            for (int y = 0; y < field.rows; ++y) {
                size_t owner = 0;
                for (size_t k = 1; k < centers.size(); ++k)
                    if (std::abs(y - centers[k]) < std::abs(y - centers[owner]))
                        owner = k;
                if (owner != j) {
                    field.row(y).colRange(0, width).setTo(-INFINITY);
                    entry.row(y).setTo(0);
                }
            }
        Lattice dp(field, entry, f.joint);
        auto path = dp.trace(dp.best);
        result.reached |=
            cv::countNonZero(dp.values.colRange(std::max(0, field.cols - 48), field.cols) > -INFINITY) > 0;
        if (path.empty())
            continue;
        double total = dp.values.at<float>(dp.best);
        if (f.joint)
            total = trimPeak(path, field, f.dual);
        auto inc = increments(f.score, path);
        double initial = std::accumulate(inc.begin(), inc.end(), 0.);
        int run = 0, longest = 0, count = 0, clean = 0, longClean = 0, near = 0, longNear = 0, nStrong = 0;
        double threshold = std::max({1., 2.7 * s.noise, .03 * s.span});
        for (auto pt : path) {
            bool active = field.at<float>(pt) > .08;
            nStrong += active;
            near = (field.at<float>(pt) > .10 && pt.x <= px(.20) && pt.x > px(.015)) ? near + 1 : 0;
            longNear = std::max(longNear, near);
            if (!f.joint)
                continue;
            bool dual = f.dual.at<uchar>(pt) != 0;
            count += dual;
            run = dual ? run + 1 : 0;
            longest = std::max(longest, run);
            if (!mapped && dual) {
                int worldX = region.x + s.front + pt.x;
                auto w = std::lower_bound(m.windows.begin(), m.windows.end(), worldX,
                                          [](const Window &win, int x) { return win.x1 <= x; });
                int flank = px(.02);
                double d = f.delta.at<float>(pt);
                double neg = std::min(f.delta.at<float>(std::max(0, pt.y - flank), pt.x),
                                      f.delta.at<float>(std::min(f.delta.rows - 1, pt.y + flank), pt.x));
                clean = (w != m.windows.end() && w->x0 <= worldX && w->lowWhite &&
                         !f.originalDip.at<uchar>(pt) && d > 2 * threshold && neg >= -.25 * d)
                            ? clean + 1
                            : 0;
                longClean = std::max(longClean, clean);
            } else
                clean = 0;
        }
        if (f.joint && deadMouth(path, field, mouth)) {
            result.dead = true;
            continue;
        }
        if (initial <= .040 * scale && !(f.joint && count >= 8 && total > 0))
            continue;
        if (path.back().x - path.front().x < px(.030) || closed(f.gray, path))
            continue;
        int shortRun = std::max(10, px(.035));
        if (f.joint && !mapped && longest < std::max(10, px(.065)) && longClean < shortRun)
            continue;
        if (f.joint && mapped && longest < shortRun && path.size() < 2 * shortRun)
            continue;
        if (f.pre && longNear < px(.035))
            continue;
        double merit = total + (f.joint ? 0. : .65 * nStrong);
        if (merit > best) {
            best = merit;
            result.path = path;
        }
    }
    for (auto &pt : result.path)
        pt += region.tl() + Point(s.front, 0);
    return result;
}
static Scene cutScene(Scene scene, int top, int bot, int width) {
    scene.sl = Rect(scene.sl.x, scene.sl.y + top, width, bot - top);
    scene.local = scene.raw(scene.sl).clone();
    scene.mid -= top;
    scene.middle -= top;
    scene.minStart -= top;
    scene.maxStart -= top;
    return scene;
}
Detection detect(const Mat &image, const Mat &fixed, Rect box, const Pair &cp, const Pair &rp) {
    auto scene = prepareScene(image(box), fixed(box), midpoint(cp) - Point2d(box.tl()),
                              midpoint(rp) - Point2d(box.tl()));
    if (!scene)
        return {};
    Detection result;
    result.notch = true;
    Scene reduced = *scene;
    bool narrow = scene->local.total() > 250000;
    int height = scene->local.rows, width = scene->local.cols, low = 0, high = height;
    if (narrow) {
        int mid = rnd(scene->middle), half = std::max(8, px(.085));
        low = std::max(0, std::min(mid - half, scene->minStart));
        high = std::min(height, std::max(mid + half + 1, scene->maxStart + 1));
        reduced = cutScene(*scene, low, high, width);
    }
    int budget =
        narrow ? std::min(width, std::max(reduced.front + px(.75), 180000 / reduced.local.rows)) : width;
    Search best;
    for (;;) {
        Scene part = budget == width ? reduced : cutScene(reduced, 0, reduced.local.rows, budget);
        result.mapping =
            mapReference(image, fixed, box, midpoint(rp) - midpoint(cp), *scene, part.sl.x + budget);
        best = search(part, result.mapping, box);
        if (budget == width || !best.reached)
            break;
        budget = std::min(width, 2 * budget);
    }
    if (narrow && best.path.empty() && best.dead) {
        int halo = px(.055), end = std::min(width, scene->front + px(.20) + 1 + std::max(12, px(.08)));
        auto near = cutScene(*scene, std::max(0, low - halo), std::min(height, high + halo), end);
        auto trial = search(near, result.mapping, box);
        if (!trial.path.empty() && trial.path.back().x - box.x - near.sl.x - near.front < .20 * scale)
            best = std::move(trial);
    }
    result.path.assign(best.path.begin(), best.path.end());
    if (narrow && !best.path.empty()) {
        Point pt = best.path.back();
        auto &m = result.mapping;
        if (pt.y > box.y && pt.y + 1 < box.br().y && pt.x < m.box.br().x) {
            double v[3], ref[3];
            bool finite = true;
            for (int j = 0; j < 3; ++j) {
                Point p = pt + Point(0, j - 1);
                v[j] = -image.at<uchar>(p);
                ref[j] = m.box.contains(p) ? m.tile.at<float>(p - m.box.tl()) : NAN;
                finite &= std::isfinite(ref[j]);
            }
            if (finite)
                for (int j = 0; j < 3; ++j)
                    v[j] += .25 * (ref[j] + v[j]);
            double curv = 2 * v[1] - v[0] - v[2];
            if (v[1] > v[0] && v[1] > v[2] && curv >= scene->noise) {
                double offset = clip(.5 * (v[2] - v[0]) / curv, -.5, .5);
                result.path.back().y = ((pt.y - box.y) + offset) + box.y;
            }
        }
    }
    return result;
}
} // namespace v63
