#include "internal.hpp"
namespace v510 {
static Mat depthAt(const Mat &im, int r) { return cv::max(im - cv::max(shift(im, 0, r), shift(im, 0, -r)), 0.); }
static Mat bilateral(const Mat &im) {
    return cv::max(depthAt(im, px(.007)), cv::max(depthAt(im, px(.014)), depthAt(im, px(.024))));
}
static Mat oriented(const Mat &a, double slope, int reach, int op) {
    Mat out = Mat::zeros(a.size(), CV_32F);
    for (double v : {-slope, 0., slope}) {
        int dy = rnd(v * reach), h = std::abs(dy);
        Mat k = Mat::zeros(2 * h + 1, 2 * reach + 1, CV_8U);
        cv::line(k, {0, h - dy}, {2 * reach, h + dy}, 1);
        cv::max(out, morph(a, op, k), out);
    }
    return out;
}
static Mat spanWidth(const Mat &mask) {
    Mat out = Mat::zeros(mask.size(), CV_32F);
    for (int x = 0; x < mask.cols; ++x)
        for (int y = 0; y < mask.rows;) {
            if (!mask.at<uchar>(y, x)) {
                ++y;
                continue;
            }
            int a = y;
            while (y < mask.rows && mask.at<uchar>(y, x))
                ++y;
            for (int j = a; j < y; ++j)
                out.at<float>(j, x) = float(y - a);
        }
    return out;
}
static Mat ridge(const Mat &im, double uniform, const Scene &p) {
    Mat a = bilateral(im), sustained = oriented(a, .55, px(.011), cv::MORPH_OPEN);
    double clean = clip((.026 * p.span - p.noise) / (.020 * p.span));
    for (int y = 0; y < a.rows; ++y)
        for (int x = 0; x < a.cols; ++x) {
            auto &v = a.at<float>(y, x);
            double mix = .03 + .87 * uniform * clean * clip((.19 * p.span - v) / (.10 * p.span));
            v = float((1 - mix) * v + mix * sustained.at<float>(y, x));
        }
    return .60 * a + .40 * gauss(a, .003 * scale, .003 * scale * .52);
}
static void normalField(Field &f, const Scene &p) {
    Mat g = f.gray, d = f.delta;
    double th = std::max({1., 2.7 * p.noise, .030 * p.span});
    Mat dark = Mat::zeros(g.size(), CV_32F), ridge = dark.clone(), dip = Mat::zeros(g.size(), CV_8U);
    for (double slope : {-.70, -.34, 0., .34, .70}) {
        int step = px(.009), rise = rnd(step * slope);
        Mat sm = .25 * (2 * d + shift(d, step, rise) + shift(d, -step, -rise));
        for (int r : {px(.008), px(.016)}) {
            int x = rnd(-r * slope / std::hypot(1., slope)), y = std::max(1, rnd(r / std::hypot(1., slope)));
            Mat prom = sm - cv::max(shift(sm, x, y), shift(sm, -x, -y));
            Mat on = (sm > 1.25 * th) & (prom > .28 * sm);
            Mat strength = prom / th;
            strength.setTo(0, ~on);
            cv::max(ridge, strength, ridge);
            cv::max(dark, cv::min(shift(g, x, y), shift(g, -x, -y)) - g, dark);
            Mat blue = cv::min(shift(sm, 2 * x, 2 * y), shift(sm, -2 * x, -2 * y));
            dip |= (sm > th) & (blue < -th) & (-blue > .48 * sm);
        }
    }
    auto persistent = [](const Mat &mask, int n) {
        return blur(morph(f32(mask) / 255., cv::MORPH_DILATE, kernel(1, 3)), n, 1) >= .65;
    };
    f.core = dark > std::max(3 * p.noise, .035 * p.span);
    dip &= ~(f.core & persistent(f.core, 7));
    f.dip = dip;
    Mat wide = (spanWidth(d > th) > std::max(3., .035 * scale)) & (ridge < 1.6);
    f.fine = (ridge > 1.) & persistent(ridge > 1., 5) & ~dip & ~wide;
    Mat prior = morph(bilateral(-f.ref), cv::MORPH_DILATE, kernel(3, 2 * px(.035) + 1));
    f.red = f.fine & (prior < cv::max(.52 * cv::max(d, th), 4 * p.noise));
    f.strength = ridge;
    Mat cap = cv::min(f.score, -.70);
    cap.copyTo(f.score, dip);
}

Field makeField(const Scene &p, const Mat &fixed) {
    Field out;
    Mat g = f32(p.local);
    double sig = .003 * scale, noise = p.noise, span = p.span;
    Mat tex = cv::abs(g - gauss(g, .017 * scale));
    auto vals = sample(tex, px(.012), px(.012), p.front + px(.035));
    double uniform = vals.empty() ? 0 : clip((3.2 * noise - quant(vals, .925)) / (1.1 * noise));
    Mat depth = ridge(-g, uniform, p);
    int size = 2 * px(.036) + 1;
    Mat tau = cv::max(1.9 * blur(depth, size, size), 2.25 * noise + .007 * span);
    Mat raw(g.size(), CV_32F), legacy(g.size(), CV_32F);
    for (int y = 0; y < g.rows; ++y)
        for (int x = 0; x < g.cols; ++x) {
            double z = depth.at<float>(y, x), t = tau.at<float>(y, x);
            raw.at<float>(y, x) =
                float(std::max(-.56, 2.45 * std::tanh(z / (2 * std::max({t, .033 * span, 3.8 * noise}))) - 1.46));
            legacy.at<float>(y, x) = float(2.1 * std::tanh(z / (2 * t)) - .97);
        }
    Mat score = raw.clone(), aligned;
    if (!fixed.empty())
        aligned = registerLocal(p, fixed);
    if (!aligned.empty()) {
        Mat valid = aligned == aligned, f = aligned.clone();
        g.copyTo(f, ~valid);
        Mat d = f - g;
        out.delta = d.colRange(p.front, g.cols).clone();
        out.ref = f.colRange(p.front, g.cols).clone();
        if (quant(sample(cv::abs(d), 4, 4), .995) > .01 * span) {
            out.joint = true;
            Mat inc = ridge(d, uniform, p), fd = bilateral(-f), smooth = gauss(d, sig, std::max(.35, .5 * sig));
            int rh = 2 * px(.014) + 1;
            Mat pos = blur(cv::max(smooth, 0.), 1, rh), neg = blur(cv::max(-smooth, 0.), 1, rh);
            Mat polar = cv::max(1 - neg / cv::max(pos, noise), 0.);
            inc = inc.mul(polar);
            Mat coherent = blur(fd, 2 * px(.012) + 1, 1);
            int reach = 2 * px(.025) + 1;
            Mat prior = morph(coherent, cv::MORPH_DILATE, ellipse(reach, reach)),
                col = morph(coherent, cv::MORPH_DILATE, kernel(3, reach));
            Mat overlap = cv::min(col / cv::max(prior, noise), 1.);
            Mat risk = cv::min(cv::max((prior / cv::max(depth, tau) - .40) / .45, 0.), 1.)
                           .mul(cv::min(cv::max((prior - 2 * noise) / tau, 0.), 1.));
            risk = risk.mul(.30 + .70 * overlap);
            Mat diffTau = cv::max(2 * blur(inc, size, size), 2.45 * noise + .007 * span);
            Mat line = oriented(bilateral(d), .55, px(.011), cv::MORPH_OPEN),
                straight = morph(inc, cv::MORPH_OPEN, kernel(2 * px(.011) + 1, 1));
            int width = 2 * px(.013) + 1;
            Mat averaged = blur(d, width, 1), slow = bilateral(averaged).mul(polar);
            double slowBase = std::max(2.4 * noise / std::sqrt(width), .025 * span);
            int m = 2 * px(.026) + 1, b = 2 * px(.085) + 1;
            Mat flank = cv::abs(blur(g, m, m) - blur(g, b, b));
            std::vector<double> rough;
            for (int y = 0; y < g.rows; ++y)
                if (std::abs(y - p.mid) > .12 * scale)
                    for (int x = p.front + px(.06); x < g.cols; x += 5)
                        rough.push_back(flank.at<float>(y, x));
            double smoothMaterial = clip((.008 - (rough.empty() ? 1. : quant(rough, .9) / span)) / .0025),
                   clean = clip((.028 * span - noise) / (.015 * span));
            int neckEnd = std::min(g.cols, p.front + px(.26));
            Mat stem(g.rows, neckEnd, CV_32F);
            for (int y = 0; y < stem.rows; ++y)
                for (int x = 0; x < stem.cols; ++x) {
                    double w = clip((std::max(0, x - p.front) - .04 * scale) / (.14 * scale));
                    stem.at<float>(y, x) = float(std::min(depth.at<float>(y, x), inc.at<float>(y, x)) *
                                                 (1 - risk.at<float>(y, x) * w));
                }
            stem = morph(stem, cv::MORPH_DILATE, kernel(1, 2 * px(.003) + 1));
            Mat closed = oriented(stem, .16, px(.032), cv::MORPH_CLOSE);
            Mat bridge = (closed > std::max(.17 * span, 7 * noise)) & (stem < .6 * closed);
            Mat ratio, added;
            if (smoothMaterial > .05) {
                Mat sm = gauss(d, std::max(.65, .0045 * scale)), gx, gy;
                cv::Sobel(sm, gx, -1, 1, 0);
                cv::Sobel(sm, gy, -1, 0, 1);
                int w = 2 * px(.020) + 1, h = 2 * px(.009) + 1;
                ratio = blur(gx.mul(gx), w, h) / cv::max(blur(gy.mul(gy), w, h), .01 * noise * noise);
                int n = 2 * px(.08) + 1;
                Mat res = d - blur(d, n, n);
                w = 2 * px(.012) + 1;
                h = 2 * px(.045) + 1;
                Mat mass = blur(res, w, h) / cv::max(blur(cv::abs(res), w, h), .50 * noise);
                added = cv::min(cv::max((mass - .07) / .26, 0.), 1.);
            }
            Mat strong(g.size(), CV_32F);
            for (int y = 0; y < g.rows; ++y)
                for (int x = 0; x < g.cols; ++x) {
                    double dist = std::max(0, x - p.front), w = clip((dist - .04 * scale) / (.14 * scale)),
                           far = clip((dist - .25 * scale) / (.12 * scale)), neck = 1 - w;
                    double z = depth.at<float>(y, x), iv = inc.at<float>(y, x), rs = raw.at<float>(y, x),
                           ds = 2.1 * std::tanh(iv / (2 * diffTau.at<float>(y, x))) - .97;
                    double riskv = risk.at<float>(y, x), t = tau.at<float>(y, x),
                           q = clip((ds - .32) / .42) * (1 - riskv * w);
                    strong.at<float>(y, x) = float(q);
                    double fused = (.90 - .47 * w) * rs + (.10 + .47 * w) * ds - 1.38 * riskv * w;
                    fused += .43 * w * std::max(0., legacy.at<float>(y, x) - rs) * clip((ds + .2) / .65);
                    fused =
                        std::max(fused, neck * std::max(rs, .93 * ds) - .16 - 1.38 * riskv * w - (1 - neck) * 2.5);
                    fused = std::max(fused, q > .55 ? .90 * ds - 1.2 * riskv : -2.5);
                    fused += 1.15 * clip(1 - dist / (.24 * scale)) *
                             clip(z / std::max(.16 * span, 6 * noise) - .85, -.50, 1.6);
                    fused = std::max(fused, rs - (2.2 + 1.2 * riskv) * clip((dist - .15 * scale) / (.12 * scale)));
                    bool gap = x < neckEnd && bridge.at<uchar>(y, x);
                    fused = std::max(fused, gap ? .66 : -2.5);
                    double weak = clip((.21 * span - iv) / (.10 * span)), av = averaged.at<float>(y, x),
                           sv = slow.at<float>(y, x);
                    bool sustained = sv > slowBase && av > slowBase && riskv < .35 && z > .55 * noise && far > .5;
                    fused = std::max(fused, sustained ? clip(sv / slowBase - 1, 0, .75) * (1 - clean) - .14 : -2.5);
                    double den = std::max(iv, noise), corr = clip(straight.at<float>(y, x) / den);
                    fused -= far * clean * smoothMaterial * weak *
                             (1.65 * clip(1 - line.at<float>(y, x) / den) + .40 * (1 - corr));
                    if (!ratio.empty()) {
                        double rat = ratio.at<float>(y, x), a = added.at<float>(y, x);
                        double fade = clip(1 - rat / .60) * clip(sv / (.60 * slowBase));
                        fused = std::max(fused, av > noise && z > .4 * noise && riskv < .40 && far > .5
                                                    ? .9 * fade - .34
                                                    : -2.5);
                        fused -= 1.55 * smoothMaterial * far * weak * clip((rat - .20) / .40) +
                                 .45 * smoothMaterial * far * riskv * overlap.at<float>(y, x);
                        if (riskv > .2 && far > .5 && a > .3 && sv > .7 * slowBase && rat < .55)
                            fused = std::max(fused, std::min(rs, ds) + .26 * a - .62 * (1 - a));
                    }
                    if (z < std::max(1.35 * noise, .007 * span) && q <= .55 && !gap && !sustained)
                        fused = std::min(fused, -.8);
                    score.at<float>(y, x) = float(valid.at<uchar>(y, x) ? fused : rs);
                }
            if (cv::countNonZero(valid) > .65 * valid.total()) {
                std::vector<double> v;
                int count = 0;
                for (int y = 0; y < g.rows; ++y)
                    for (int x = 0; x < g.cols; ++x)
                        if (valid.at<uchar>(y, x) && count++ % 8 == 0)
                            v.push_back(std::abs(d.at<float>(y, x)));
                if (quant(v, .95) < std::max(4 * noise, .025 * span)) {
                    double peak;
                    cv::minMaxLoc(blur(strong.colRange(p.front, std::min(g.cols, p.front + px(.30))), px(.035), 1),
                                  nullptr, &peak);
                    out.pre = peak < .40;
                }
            }
        } else
            out.pre = cv::countNonZero(valid) > .65 * valid.total();
    }
    if (out.pre) {
        score = raw.clone();
        Mat limited = cv::min(raw, -.55);
        limited.copyTo(score, depth < std::max(5.5 * noise, .105 * span));
        out.joint = false;
    }
    int f = p.front, end = std::min(g.cols, f + px(.020) + 1), left = std::max(0, f - px(.055));
    Mat patch = g.colRange(left, end);
    int j0 = f - left;
    Mat cc;
    cv::connectedComponents(patch < (quant(sample(patch), .7) - std::max(4 * noise, .10 * span)), cc);
    double maxid;
    cv::minMaxLoc(cc, nullptr, &maxid);
    std::vector<int> counts(int(maxid) + 2);
    for (int y = 0; y < cc.rows; ++y)
        for (int x = 0; x < std::max(1, j0 - px(.025)); ++x)
            if (patch.at<float>(y, x) < p.black + .26 * span)
                ++counts[cc.at<int>(y, x)];
    counts[0] = 0;
    int body = int(std::max_element(counts.begin(), counts.end()) - counts.begin());
    out.seeds = Mat::zeros(g.rows, end - f, CV_8U);
    Mat audit = morph(depth, cv::MORPH_DILATE, kernel(1, 2 * px(.004) + 1));
    if (counts[body])
        for (int y = std::max(0, p.mid - px(.16)); y < std::min(g.rows, p.mid + px(.16) + 1); ++y)
            for (int x = f; x < end; ++x) {
                int n = std::min(px(.010), g.cols - x - 1), good = 0;
                for (int j = 1; j <= n; ++j)
                    good += audit.at<float>(y, x + j) > std::max(2 * noise, .018 * span);
                out.seeds.at<uchar>(y, x - f) = cc.at<int>(y, x - left) == body &&
                                                depth.at<float>(y, x) > tau.at<float>(y, x) && good >= .65 * n;
            }
    out.score = score.colRange(f, g.cols).clone();
    out.gray = g.colRange(f, g.cols).clone();
    if (out.joint) {
        int n = std::min(out.score.cols, px(.25) + 1);
        Mat d = gauss(out.delta.colRange(0, n), std::max(.4, .0025 * scale)), gray = out.gray.colRange(0, n);
        double floor = std::max(3 * noise, .038 * span);
        Mat width = spanWidth(d > floor),
            crest = cv::max(depthAt(d, px(.012)), depthAt(-gray, px(.012))) / cv::max(d, floor);
        for (int y = 0; y < g.rows; ++y)
            for (int x = 0; x < n; ++x) {
                auto &z = out.score.at<float>(y, x);
                double w = clip((width.at<float>(y, x) - .024 * scale) / (.015 * scale)) *
                           clip((.56 - crest.at<float>(y, x)) / .36) * clip((.25 - x / scale) / .05);
                z -= float(w * std::max(0., z - .015));
            }
        normalField(out, p);
    }
    return out;
}
} // namespace v510