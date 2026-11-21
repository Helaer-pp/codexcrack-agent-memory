#include "internal.hpp"
namespace v512 {
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
static Path downstream(const Evidence &f, const Mat &field, const Lattice &dp, const Path &path, int contact) {
    Point end = path.back();
    bool near = end.x - path.front().x <= std::max(18, 4 * contact);
    Mat local = morph(dp.values, cv::MORPH_DILATE, kernel(3, 3));
    std::vector<Point> peaks;
    for (int x = end.x + 4; x < field.cols; ++x)
        for (int y = 0; y < field.rows; ++y) {
            Point p(x, y);
            float v = dp.values.at<float>(p);
            if (v >= local.at<float>(p) && field.at<float>(p) > .08 && v > 1)
                peaks.push_back(p);
        }
    std::stable_sort(peaks.begin(), peaks.end(),
                     [&](Point a, Point b) { return dp.values.at<float>(a) > dp.values.at<float>(b); });
    for (auto peak : peaks) {
        auto alt = dp.trace(peak);
        if (alt.empty())
            continue;
        int first = std::max(0, end.x - alt[0].x), n = int(alt.size());
        if (first >= n - 4)
            continue;
        if (!near && (std::abs(alt[first].y - end.y) > 2 || first != int(path.size()) - 1 ||
                      !std::equal(alt.begin(), alt.begin() + first, path.begin())))
            continue;
        auto v = increments(field, alt);
        auto c = v;
        std::partial_sum(v.begin(), v.end(), c.begin());
        auto lifted = [&](int start) {
            int measured = 0;
            double net = 0;
            for (int i = start; i < n; ++i) {
                auto p = alt[i];
                net += v[i];
                if (f.red.at<uchar>(p)) {
                    ++measured;
                    net += std::max(0., std::min(.94, .16 + .22 * f.strength.at<float>(p)) - field.at<float>(p));
                }
            }
            return measured >= .30 * (n - start) && net > 0;
        };
        if (!near && !lifted(first + 1))
            continue;
        int bottom = int(std::min_element(c.begin() + first, c.end()) - c.begin());
        int tail = n - bottom - 1;
        if (tail < 5 || c.back() - c[bottom] < 2.5 || !lifted(bottom + 1))
            continue;
        int runs = 0, maxrun = 0, pos = 0;
        for (int i = bottom + 1; i < n; ++i) {
            bool b = field.at<float>(alt[i]) > .08;
            runs = b ? runs + 1 : 0;
            maxrun = std::max(runs, maxrun);
            pos += b;
        }
        if (maxrun >= 3 && pos >= .52 * tail && std::accumulate(v.end() - 4, v.end(), 0.) / 4 > .06 &&
            !closed(f.gray, alt))
            return alt;
    }
    return path;
}
#include "extensions.inc"
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
    return inc >= .48 * n && ((core < .36 * n && (glare >= .35 * n || cliff)) ||
                              (cliff && glare >= .70 * n &&
                               (newCore < .36 * n || (p.x - path.front().x <= .055 * scale && 3 * flat >= width))));
}

struct Candidate {
    Path path;
    double merit;
    int bridge, columns = 0;
    double gain = 0;
    bool active = false, inactive = false;
    bool promoted=false, fork=false;
    int dualColumns=0, blueColumns=0;
};
Found detect512(const Mat &raw, const Mat &fixed, const Mat &aligned, Point2d hint, Point2d refHint) {
    auto scene = prepare(raw, fixed, hint, refHint);
    if (!scene)
        return {};
    Evidence f = makeEvidence(*scene, aligned);
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
    std::vector<Candidate> candidates;
    Mouth mouth;
    if (f.joint)
        mouth = profile(f, *scene);
    for (int j = 0; j < int(groups.size()); ++j) {
        Mat field = f.score.clone(), entry = Mat::zeros(f.seeds.size(), CV_8U);
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
        double total=path.empty()?0.:dp.values.at<float>(dp.best);
        bool promoted=false,fork=false;
        if(f.joint && total<=.040*scale) {
            Path alt=rescue(f,*scene,field,entry,false,total);
            if(alt.empty()) {
                alt=rescue(f,*scene,field,entry,true,total);fork=!alt.empty();
            }
            if(!alt.empty()) {path.swap(alt);promoted=true;}
        }
        if(path.empty())continue;
        int bridged=0;
        if(f.joint && !promoted && total>.040*scale) {
            auto initial=path;
            path=downstream(f,field,dp,initial,groups.back().back()-groups.front().front()+f.seeds.cols);
            if(path==initial)path=recovery(f,field,initial,dp);
            if(blankCrossing(initial.back(),path,f.dual))path=initial;
            total=dp.values.at<float>(path.back());
            bridged=bridge(f,*scene,field,path);
        }
        if ((!promoted && total <= .040 * scale) || path.back().x-path.front().x<px(.030) || closed(f.gray,path) ||
            (f.joint && deadMouth(path,field,mouth)))continue;
        int fine = 0, core = 0, run = 0, longest = 0;
        for (auto p : path) {
            if (f.joint) {
                fine += bool(f.fine.at<uchar>(p));
                core += f.fine.at<uchar>(p) && f.core.at<uchar>(p);
            } else
                fine += field.at<float>(p) > .08;
            bool near = p.x <= px(.20) && p.x > px(.015) && field.at<float>(p) > .10;
            run = near ? run + 1 : 0;
            longest = std::max(run, longest);
        }
        if (f.pre && longest < px(.035))
            continue;
        candidates.push_back({std::move(path), total + .65 * fine + .70 * core, bridged});
        candidates.back().promoted=promoted; candidates.back().fork=fork;
    }
    double threshold=std::max({1.,2.7*scene->noise,.030*scene->span});
    if(f.joint) {
        const Candidate* leader=nullptr;
        for(const auto& c:candidates)if(!c.promoted && (!leader || c.merit>leader->merit))leader=&c;
        std::vector<Candidate> allowed;
        for(const auto& c:candidates)if(!c.promoted)allowed.push_back(c);
        for(const auto& c:candidates)if(c.promoted) {
            Runs red,blue;bool early=false;int plus=0,k=0;
            for(auto p:c.path) {
                bool hit=f.dual.at<uchar>(p)!=0;
                if(k++<std::max(4,px(.025)))early |=hit;
                red.add(hit);
            }
            if(leader)for(auto p:leader->path) {
                int j=p.x-c.path[0].x;
                bool unique=j<0 || j>=int(c.path.size()) || std::abs(p.y-c.path[j].y)>2;
                blue.add(unique && f.delta.at<float>(p)<-threshold);
                plus+=unique && f.dual.at<uchar>(p);
            }
            if(red.longest>=8 && early && red.maxGap<=std::max(4,px(.025)) &&
               ((!leader&&!c.fork)||(blue.longest>=3 && blue.count>plus)))allowed.push_back(c);
        }
        candidates.swap(allowed);
    }
    if (candidates.empty())
        return {{}, 0, true};
    if (f.joint && candidates.size() > 1) {
        double threshold = std::max({1., 2.7 * scene->noise, .030 * scene->span});
        bool active = false, inactive = false;
        bool hasDualRun=false,hasRed=false,hasBlue=false;
        for (auto &c : candidates) {
            Runs support;
            int unique = 0, run = 0, longest = 0;
            double sum = 0;
            for (auto p : c.path) {
                bool disjoint = true;
                for (auto &other : candidates)
                    if (&other != &c) {
                        int i = p.x - other.path[0].x;
                        if (i >= 0 && i < int(other.path.size()) && std::abs(other.path[i].y - p.y) <= 2) {
                            disjoint = false;
                            break;
                        }
                    }
                bool paired=f.dual.at<uchar>(p)!=0;
                support.add(paired);
                c.dualColumns+=disjoint && paired;
                c.blueColumns+=disjoint && f.delta.at<float>(p)<-threshold;
                double val = f.delta.at<float>(p) / threshold;
                if (disjoint) {
                    ++unique;
                    sum += val;
                }
                if (disjoint && f.red.at<uchar>(p) && val > 1) {
                    ++c.columns;
                    c.gain += clip(val - 1, 0, 3);
                    longest = std::max(longest, ++run);
                } else
                    run = 0;
            }
            c.active = c.columns >= 4 && longest >= 3 && c.gain >= 6 && sum > 0;
            c.inactive = unique && (c.columns <= 2 || sum <= 0);
            hasDualRun|=support.longest>=8;
            hasRed|=c.dualColumns>=8;
            hasBlue|=c.blueColumns>=3 && c.blueColumns>c.dualColumns;
            active |= c.active;
            inactive |= c.inactive;
        }
        if (active && inactive)
            for (auto &c : candidates)
                c.merit = c.merit * (c.inactive ? .35 : 1) + (c.active ? 2 * c.columns + .65 * c.gain : 0);
        if(hasDualRun && hasRed && hasBlue)
            for(auto &c:candidates)c.merit+=1.5*c.dualColumns-2.*c.blueColumns;
    }
    auto &win =
        *std::max_element(candidates.begin(), candidates.end(), [](auto &a, auto &b) { return a.merit < b.merit; });
    for (auto &p : win.path)
        p += scene->sl.tl() + Point(scene->front, 0);
    return {std::move(win.path), win.bridge, true};
}
} // namespace v512