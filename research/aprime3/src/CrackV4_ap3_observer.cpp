#include "CrackV4_experiments.h"
#include "scipy_gaussian_kernels.h"
#include <algorithm>
#include <array>
#include <charconv>
#include <chrono>
#include <cmath>
#include <cstring>
#include <deque>
#include <iomanip>
#include <limits>
#include <memory>
#include <mutex>
#include <numeric>
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using P = cv::Point2d;
using Path = std::vector<P>;
using Clock = std::chrono::steady_clock;
constexpr double NaN = std::numeric_limits<double>::quiet_NaN();
double elapsed(Clock::time_point a) {
    return std::chrono::duration<double, std::milli>(Clock::now() - a).count();
}
#ifdef CRACK_V4_PROFILE
thread_local std::array<double, 16> profile_ms{};
struct ProfileScope {
    int slot;
    Clock::time_point begin = Clock::now();
    explicit ProfileScope(int s) : slot(s) {}
    ~ProfileScope() { profile_ms[slot] += elapsed(begin); }
};
#define PROFILE_SCOPE(slot) ProfileScope profile_scope_##slot(slot)
#define PROFILE_LAPS auto profile_lap_start = Clock::now()
#define PROFILE_LAP(slot) profile_ms[slot] += elapsed(profile_lap_start); profile_lap_start = Clock::now()
#else
#define PROFILE_SCOPE(slot)
#define PROFILE_LAPS
#define PROFILE_LAP(slot)
#endif
double norm(P p) {
    return std::sqrt(p.x * p.x + p.y * p.y);
}
P unit(P p) {
    return p / std::max(norm(p), 1e-8);
}
double dot(P a, P b) {
    return a.x * b.x + a.y * b.y;
}
int rnd(double x) {
    return static_cast<int>(std::nearbyint(x));
}
double round2(double v) {
    return std::nearbyint(v * 100.) / 100.;
}
double pyround(double v, int precision = 2) {
    char b[128];
    auto result = std::to_chars(b, b + sizeof(b), v, std::chars_format::fixed, precision);
    if (result.ec != std::errc())
        throw std::runtime_error("Decimal rounding overflow");
    double out = 0;
    std::from_chars(b, result.ptr, out, std::chars_format::fixed);
    return out;
}
P rounded(P p) {
    return {round2(p.x), round2(p.y)};
}
double sumd(const double *a, int n) {
    if (n < 8) {
        double s = -0.;
        for (int i = 0; i < n; i++)
            s += a[i];
        return s;
    }
    if (n <= 128) {
        double r[8];
        std::copy(a, a + 8, r);
        int i = 8;
        for (; i < n - (n % 8); i += 8)
            for (int k = 0; k < 8; k++)
                r[k] += a[i + k];
        double s = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
        for (; i < n; i++)
            s += a[i];
        return s;
    }
    int k = n / 2;
    k -= k % 8;
    return sumd(a, k) + sumd(a + k, n - k);
}
double arc(const Path &p) {
    std::vector<double> d;
    for (size_t i = 1; i < p.size(); i++)
        d.push_back(norm(p[i] - p[i - 1]));
    return sumd(d.data(), (int)d.size());
}
double clip(double x, double lo, double hi) {
    return std::min(hi, std::max(lo, x));
}
template <class F> void independentRows(int rows, int cols, const F &body) {
    if (int64_t(rows) * cols >= 131072) {
        cv::parallel_for_(cv::Range(0, rows), [&](const cv::Range &range) {
            for (int y = range.start; y < range.end; ++y)
                body(y);
        });
    } else {
        for (int y = 0; y < rows; ++y)
            body(y);
    }
}
double med(std::vector<double> v) {
    PROFILE_SCOPE(6);
    if (v.empty())
        return 0;
    size_t m = v.size() / 2;
    // Select the same order statistics without sorting every pixel in a large tile.
    // Preserve the original sort behavior for exceptional floating-point values.
    if (std::any_of(v.begin(), v.end(), [](double x) {
            return !std::isfinite(x) || (x == 0. && std::signbit(x));
        })) {
        std::sort(v.begin(), v.end());
        return v.size() % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
    }
    std::nth_element(v.begin(), v.begin() + m, v.end());
    double upper = v[m];
    return v.size() % 2 ? upper : (*std::max_element(v.begin(), v.begin() + m) + upper) / 2;
}
double percentile(std::vector<double> v, double q) {
    PROFILE_SCOPE(7);
    if (v.empty())
        return 0;
    double z = (v.size() - 1) * q;
    size_t i = (size_t)z;
    if (std::any_of(v.begin(), v.end(), [](double x) {
            return !std::isfinite(x) || (x == 0. && std::signbit(x));
        })) {
        std::sort(v.begin(), v.end());
        return v[i] + (v[std::min(i + 1, v.size() - 1)] - v[i]) * (z - i);
    }
    std::nth_element(v.begin(), v.begin() + i, v.end());
    double a = v[i], b = i + 1 == v.size() ? a : *std::min_element(v.begin() + i + 1, v.end());
    return a + (b - a) * (z - i);
}
// NumPy's float32 pairwise reduction (128-element block size).
float sumf(const float *a, int n) {
    if (n < 8) {
        float s = -0.f;
        for (int i = 0; i < n; i++)
            s += a[i];
        return s;
    }
    if (n <= 128) {
        float r[8];
        std::copy(a, a + 8, r);
        int i = 8;
        for (; i < n - (n % 8); i += 8)
            for (int k = 0; k < 8; k++)
                r[k] += a[i + k];
        float s = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
        for (; i < n; i++)
            s += a[i];
        return s;
    }
    int k = n / 2;
    k -= k % 8;
    return sumf(a, k) + sumf(a + k, n - k);
}
float meanf(const cv::Mat &a) {
    cv::Mat b = a.isContinuous() ? a : a.clone();
    return sumf(b.ptr<float>(), (int)b.total()) / (float)b.total();
}
float stdf(const cv::Mat &a) {
    float m = meanf(a);
    std::vector<float> z;
    z.reserve(a.total());
    for (int y = 0; y < a.rows; y++)
        for (int x = 0; x < a.cols; x++) {
            float d = a.at<float>(y, x) - m;
            z.push_back(d * d);
        }
    return std::sqrt(sumf(z.data(), (int)z.size()) / (float)z.size());
}
double medf(std::vector<double> v) {
    double m = med(std::move(v));
    return (double)(float)m;
}
std::vector<double> gauss(const std::vector<double> &a, double sigma, bool nearest) {
    int radius = (int)(sigma * 4 + .5);
    std::vector<double> w(2 * radius + 1), r(a.size());
    const double *kernel = sigma == .8   ? gaussian_08
                           : sigma == 2. ? gaussian_20
                           : sigma == 3. ? gaussian_30
                                         : nullptr;
    if (kernel)
        std::copy(kernel, kernel + w.size(), w.begin());
    else {
        for (int j = -radius; j <= radius; j++)
            w[j + radius] = std::exp((-.5 / (sigma * sigma)) * (j * j));
        double total = sumd(w.data(), (int)w.size());
        for (double &v : w)
            v /= total;
    }
    int n = (int)a.size();
    for (int i = 0; i < n; i++) {
        auto at = [&](int k) {
            if (nearest)
                k = std::max(0, std::min(n - 1, k));
            else {
                while (k < 0 || k >= n) {
                    if (k < 0)
                        k = -k - 1;
                    else
                        k = 2 * n - k - 1;
                }
            }
            return a[k];
        };
        // SciPy correlate1d's symmetric-kernel accumulation order.
        double v = at(i) * w[radius];
        for (int j = -radius; j < 0; j++)
            v += (at(i + j) + at(i - j)) * w[j + radius];
        r[i] = v;
    }
    return r;
}
Path smooth(const Path &a, double sigma) {
    std::vector<double> x, y;
    for (P p : a) {
        x.push_back(p.x);
        y.push_back(p.y);
    }
    x = gauss(x, sigma, true);
    y = gauss(y, sigma, true);
    Path b;
    for (size_t i = 0; i < a.size(); i++)
        b.emplace_back(x[i], y[i]);
    if (!a.empty()) {
        b.front() = a.front();
        b.back() = a.back();
    }
    return b;
}
std::vector<double> gradient(const std::vector<double> &a) {
    std::vector<double> b(a.size());
    if (a.size() < 2)
        return b;
    b.front() = a[1] - a[0];
    b.back() = a.back() - a[a.size() - 2];
    for (size_t i = 1; i + 1 < a.size(); i++)
        b[i] = (a[i + 1] - a[i - 1]) / 2;
    return b;
}
double interp(double x, const std::vector<double> &xs, const std::vector<double> &ys, double left = NaN,
              double right = NaN) {
    if (xs.empty())
        return NaN;
    if (x < xs.front())
        return std::isnan(left) ? ys.front() : left;
    if (x > xs.back())
        return std::isnan(right) ? ys.back() : right;
    auto it = std::lower_bound(xs.begin(), xs.end(), x);
    size_t k = (size_t)(it - xs.begin());
    if (k == 0 || *it == x)
        return ys[k];
    double u = (x - xs[k - 1]) / (xs[k] - xs[k - 1]);
    return ys[k - 1] + u * (ys[k] - ys[k - 1]);
}
double mapcoord(const cv::Mat &a, double y, double x, int order = 1, bool constant = false) {
    if (constant && (x < 0 || y < 0 || x > a.cols - 1 || y > a.rows - 1))
        return 0;
    x = clip(x, 0, a.cols - 1);
    y = clip(y, 0, a.rows - 1);
    auto at = [&](int yy, int xx) -> double {
        if (a.depth() == CV_32F)
            return a.at<float>(yy, xx);
        if (a.depth() == CV_64F)
            return a.at<double>(yy, xx);
        return a.at<uchar>(yy, xx);
    };
    if (!order)
        return at((int)std::floor(y + .5), (int)std::floor(x + .5));
    int x0 = (int)x, y0 = (int)y, x1 = std::min(x0 + 1, a.cols - 1), y1 = std::min(y0 + 1, a.rows - 1);
    double u = x - x0, v = y - y0;
    double z =
        (1 - v) * ((1 - u) * at(y0, x0) + u * at(y0, x1)) + v * ((1 - u) * at(y1, x0) + u * at(y1, x1));
    return a.depth() == CV_32F ? (double)(float)z : z;
}
Path linspace(P a, P b, int n) {
    Path p;
    for (int k = 0; k < n; k++)
        p.push_back(k == n - 1 ? b : a + (b - a) * (double(k) / (n - 1)));
    return p;
}
struct Grid {
    cv::Mat x, y;
};
struct Tile {
    cv::Mat score, reference, material, valid;
    cv::Mat current_gray; // shallow retained only by opt-in quality experiments
    Grid xy;
    int back = 0;
    double threshold = 0;
};
struct Patch {
    cv::Rect rect;
    cv::Mat patch, window;
    double quality;
};
struct Quality {
    double gain = 0, support = 0, median = 0, peak = 0, distance = NaN, span = 0, elongation = 0, width = 1;
};
struct Observation {
    Path path;
    P endpoint{}, direction{}; // reference coordinates, never replayed as current evidence
    bool terminal_verified = false;
    std::string stop;
    uint64_t frame_index = 0;
};
struct Result {
    uint64_t frame_index = 0;
    int policy = CV4_SHADOW, endpoint_hits = 0, probe_samples = 0;
    bool terminal = false, path_valid = false, legacy_tip = false, shadow_tip = false;
    double path_support = 0, tail_support = 0, tail_median = 0, path_width = 0, tail_width = 0;
    int longest_gap = 0, bends = 0;
    double reference_ahead_std=0,current_ahead_std=0,reference_ahead_clipped=0,current_ahead_clipped=0;
    bool texture_erased=false;
    std::string terminal_reason = "no_candidate", raw_stop = "no_seed", divergence = "none";

    int reference_state = 0;
    std::string reference_reason = "declared_clean";
    bool has = false, tip = false, length = false, root = false;
    P tipxy{}, endpoint{}, rootxy{}, first{}, rootref{}, tipref{};
    Path path, observed, prior, history_path;
    std::string status = "no_new_candidate", stop = "no_seed", basis = "no_candidate", method = "none", error;
    int hits = 0, tiles = 0, gaps = 0, patches = 0;
    double total = 0, visible = 0, bridge = 0, peak = 0, response = 0, initial = 0, detector_ms = 0,
           api_ms = 0;
    cv::Matx22d rotation = cv::Matx22d::eye();
    P shift{};
    Quality quality;
};
struct Config {
    int mode = 0;
    double ratio = .010753469541668892;
    bool refine = true;
    double score = 2.5, maxshift = 64;
    int tile = 96, advance = 48, maxgap = 10, temporal_window = 5, temporal_hits = 3;
    double entrance_fraction = .12, strong_peak = 15;
    bool fallback = true;
    uint32_t experiments = 0, max_debug_images = 96;
};

// DP tie ordering matches NumPy argmax: first predecessor, row and column win.
std::pair<Path, double> ridge(const cv::Mat &field, int start, double baseline) {
    PROFILE_SCOPE(4);
    int h = field.rows, w = field.cols;
    std::vector<double> acc(h), best(w);
    std::vector<int> ends(w), parent(w * h);
    for (int y = 0; y < h; y++) {
        float f = field.at<float>(y, 0) - (float)baseline;
        f = (float)(f - 2. * (y - start) * (y - start));
        acc[y] = f;
    }
    auto maximum = [&](const std::vector<double> &v) {
        return (int)(std::max_element(v.begin(), v.end()) - v.begin());
    };
    ends[0] = maximum(acc);
    best[0] = acc[ends[0]];
    for (int x = 1; x < w; x++) {
        std::vector<double> next(h);
        for (int y = 0; y < h; y++) {
            double v = -std::numeric_limits<double>::infinity();
            int by = 0;
            for (int d = -2; d <= 2; d++) {
                int z = y + d;
                if (z < 0 || z >= h)
                    continue;
                double q = acc[z] - 1.2 * d * d;
                if (q > v) {
                    v = q;
                    by = z;
                }
            }
            next[y] = v + field.at<float>(y, x) - baseline;
            parent[x * h + y] = by;
        }
        acc.swap(next);
        ends[x] = maximum(acc);
        best[x] = acc[ends[x]];
    }
    int end = maximum(best);
    std::vector<int> ys(end + 1);
    ys[end] = ends[end];
    for (int x = end; x > 0; x--)
        ys[x - 1] = parent[x * h + ys[x]];
    std::vector<double> yy;
    for (int x = 0; x <= end; x++) {
        int y = ys[x];
        double v = y;
        if (y > 0 && y < h - 1) {
            float a = field.at<float>(y - 1, x), b = field.at<float>(y, x), c = field.at<float>(y + 1, x);
            double den = a - 2. * b + c;
            if (den < -1e-5)
                v += clip(.5 * (double)(float)(a - c) / den, -.5, .5);
        }
        yy.push_back(v);
    }
    yy = gauss(yy, .8, true);
    Path p;
    for (int x = 0; x <= end; x++)
        p.emplace_back(x, yy[x]);
    return {p, best[end]};
}

struct MotionDebug { cv::Rect rect; double response=0, limit=0, residual=-1; P delta{}; bool accepted=false, inlier=false; };
struct RecoveryDebug { cv::Rect rect; P delta{}; double correlation=0, margin=0; bool accepted=false; };
struct TileDebug { P origin{}, direction{}; int u0=0, width=0, half=0, back=0; double offset=0, median=0, mad=0, noise=0, threshold=0, invalid=0; Path path; };
// Independent bounded observer. No writes to A state, DP or thresholds.
struct AP2Stop { double x,y,dx,dy,gain,support,median,threshold,invalid; int path_size,dp_size; };
class Detector {
  public:
    Config cfg;
    std::array<AP2Stop,256> ap2_stops{};
    std::array<double,9> ap3_seed{};
    int ap2_count=0;
    bool ap2_overflow=false;
    double brightness_minus=0, brightness_plus=0;
    bool direction_ambiguous=false;
    int registration_inliers=0, starts_count=0;
    double registration_residual=0;
    bool recovery_attempted=false, recovery_used=false;
    bool anchor_recovery_used=false;
    bool current_anchor_valid=false, registration_ambiguous=false;
    bool automatic_success_reviewed=false, automatic_success_repaired=false;
    std::string geometry_json;
    bool last_anchors_supplied=false;
    bool has_last_confirmed=false;
    P last_confirmed_original{};
    uint64_t last_confirmed_frame=0;
    std::string quality_json;
    std::vector<RecoveryDebug> recovery_debug;
    std::vector<MotionDebug> debug_motion;
    std::vector<TileDebug> debug_tiles;
    std::vector<std::pair<std::string,cv::Mat>> debug_images;
    std::string debug_json;
    bool debug() const { return (cfg.experiments & CV4_DIAGNOSTICS)!=0; }
    void capture(const std::string &name,const cv::Mat &m) {
        if (!(cfg.experiments & CV4_DEBUG_IMAGES) || m.empty() || debug_images.size()>=cfg.max_debug_images) return;
        cv::Mat data; m.convertTo(data,CV_32F); debug_images.emplace_back(name,data.clone());
    }
    void tracePath(const Path &path) { if(debug() && !debug_tiles.empty()) debug_tiles.back().path=path; }

    int reference_state = 0; // 0 caller-declared clean, 1 verified reference crack, 2 uncertain
    std::string reference_reason = "declared_clean";
    cv::Mat reference, baseline_mask, entry_mask, root_template;
    // Immutable reference-side data for the fixed first search tile. Current
    // pixels, valid masks, offsets, noise estimates and all decisions stay live.
    Grid seed_grid_cache;
    cv::Mat seed_reference_cache, seed_lines_cache, seed_background_cache, seed_old_cache;
    std::array<P, 2> anchors;
    P origin, across, forward, normal, translation{}, root_reference{}, frame_root{}, entrance_offset{};
    bool root_exists = false, absolute = false, baseline_exists = false, tangent = false;
    cv::Matx22d rotation = cv::Matx22d::eye();
    double spacing = 0, baseline_length = 0, root_response = 0;
    int width = 0, height = 0, curwidth = 0, curheight = 0, seed_u0 = 0, seed_width = 0, seed_half = 0,
        root_patch_u = 0, root_patch_width = 0, root_patch_half = 0;
    Path previous, baseline_path;
    std::deque<Observation> history;
    uint64_t frame_index = 0;
    int policy = CV4_SHADOW;
    bool terminal_validation = true;
    void resetTemporal() {
        previous.clear(); history.clear(); frame_index = 0;
        rotation = cv::Matx22d::eye(); translation = {};
        last = reference_result;
        last.policy = policy;
        has_last_confirmed=reference_result.tip;
        last_confirmed_original=reference_result.tipxy;last_confirmed_frame=0;
        current_anchor_valid=false;registration_ambiguous=false;
        automatic_success_reviewed=false;automatic_success_repaired=false;
        recovery_attempted=false;recovery_used=false;anchor_recovery_used=false;
    }
    void append(Observation observation) {
        history.push_back(std::move(observation));
        while ((int)history.size() > cfg.temporal_window - 1) history.pop_front();
    }
    std::vector<Patch> patches;
    std::vector<double> boundary;
    Tile seed_region;
    Quality quality;
    Result baseline, reference_result, last;
    std::string json;
    std::mutex mutex;
    Detector(const cv::Mat &ref, std::array<P, 2> ap, Config config)
        : cfg(config), reference(ref.clone()), anchors(ap) {
        width = ref.cols;
        height = ref.rows;
        curwidth = width;
        curheight = height;
        validatePoints(ap, ref.size(), 16);
        spacing = norm(ap[1] - ap[0]);
        origin = (ap[0] + ap[1]) * .5;
        across = unit(ap[1] - ap[0]);
        forward = {across.y, -across.x};
        auto brightness = [&](int sign) {
            Grid g;
            g.x.create(12, 20, CV_64F);
            g.y.create(12, 20, CV_64F);
            for (int y = 0; y < 12; y++)
                for (int x = 0; x < 20; x++) {
                    P q = origin + forward * (sign * (.3 * spacing + spacing * x / 19.)) +
                          across * (-.25 * spacing + .5 * spacing * y / 11.);
                    g.x.at<double>(y, x) = q.x;
                    g.y.at<double>(y, x) = q.y;
                }
            cv::Mat v = sample(ref, g);
            std::vector<double> a;
            for (int y = 0; y < v.rows; y++)
                for (int x = 0; x < v.cols; x++)
                    a.push_back(v.at<uchar>(y, x));
            return med(a);
        };
        brightness_minus=brightness(-1); brightness_plus=brightness(1);
        // Material on BOTH sides of an interior notch cannot define the growth
        // side by brightness. Preserve the ordered-anchor normal in that case.
        // 140 is the existing material threshold, not a dataset-specific split.
        direction_ambiguous=brightness_minus>140 && brightness_plus>140;
        if(cfg.experiments & CV4_DIRECTION_NEGATIVE)
            forward *= -1;
        else if (!(cfg.experiments & CV4_DIRECTION_POSITIVE) && brightness_minus > brightness_plus &&
            (!(cfg.experiments & CV4_DIRECTION_EXPERIMENT) || !direction_ambiguous))
            forward *= -1;
        normal = {-forward.y, forward.x};
        choosePatches();
        seed_u0 = -rnd(spacing / 6);
        seed_width = std::max(48, rnd(spacing));
        seed_half = std::max(12, rnd(spacing * .5 / 2));
        locateRoot();
        if (root_exists) {
            frame_root = root_reference;
            root_patch_u = -std::max(12, rnd(.22 * spacing));
            root_patch_width = std::max(16, rnd(.24 * spacing));
            root_patch_half = std::max(8, rnd(.13 * spacing));
            sample(reference, grid(root_reference, forward, root_patch_u, root_patch_width, root_patch_half))
                .convertTo(root_template, CV_32F);
        }
        if (cfg.mode) {
            reference_state = 2;
            reference_reason = "reference_crack_not_confirmed";
            absolute = true;
            Result b = process(reference, &anchors, true);
            absolute = false;
            if (!b.has || !b.tip) {
                previous.clear();
                if (cfg.mode == 1)
                    throw std::runtime_error("Cannot initialize a complete reference crack: " + b.stop);
            } else {
                reference_state = 1;
                reference_reason = "complete_reference_crack";
                baseline = b;
                baseline_exists = true;
                // Baseline mask needs the complete image-coordinate path, including
                // the accepted root bridge. b.prior can intentionally omit that bridge.
                baseline_path = b.path;
                baseline_length = b.total;
                baseline_mask = cv::Mat::zeros(reference.size(), CV_8U);
                std::vector<cv::Point> p;
                for (P q : baseline_path)
                    p.emplace_back(rnd(q.x), rnd(q.y));
                cv::polylines(baseline_mask, std::vector<std::vector<cv::Point>>{p}, false, 255,
                              2 * std::max(3, rnd(.03 * spacing)) + 1);
                baseline.status = "reference_cracked";
                baseline.initial = baseline_length;
            }
        }
        history.clear();
        frame_index = 0;
        reference_result = baseline_exists ? baseline : Result{};
        reference_result.reference_state = reference_state;
        reference_result.reference_reason = reference_reason;
        if (!baseline_exists)
            reference_result.status = "reference";
        last = reference_result;
        has_last_confirmed=reference_result.tip;
        last_confirmed_original=reference_result.tipxy;
    }
    static void validatePoints(std::array<P, 2> p, cv::Size size, double minimum) {
        for (P q : p)
            if (!std::isfinite(q.x) || !std::isfinite(q.y) || q.x < 0 || q.y < 0 || q.x >= size.width ||
                q.y >= size.height)
                throw std::runtime_error("Anchors must be finite and inside the image");
        if (norm(p[1] - p[0]) < minimum)
            throw std::runtime_error("Anchor spacing is too small");
    }
    P current(P p) const {
        return {rotation(0, 0) * p.x + rotation(0, 1) * p.y + translation.x,
                rotation(1, 0) * p.x + rotation(1, 1) * p.y + translation.y};
    }
    Grid grid(P o, P d, int u0, int w, int half) const {
        Grid g;
        g.x.create(half * 2 + 1, w, CV_64F);
        g.y.create(half * 2 + 1, w, CV_64F);
        P n(-d.y, d.x);
        for (int y = 0; y < g.x.rows; y++)
            for (int x = 0; x < w; x++) {
                P p = o + d * (x + u0) + n * (y - half);
                g.x.at<double>(y, x) = p.x;
                g.y.at<double>(y, x) = p.y;
            }
        return g;
    }
    Grid transformed(const Grid &g) const {
        Grid b;
        b.x.create(g.x.size(), CV_64F);
        b.y.create(g.y.size(), CV_64F);
        independentRows(g.x.rows, g.x.cols, [&](int y) {
            const double *gx = g.x.ptr<double>(y), *gy = g.y.ptr<double>(y);
            double *bx = b.x.ptr<double>(y), *by = b.y.ptr<double>(y);
            for (int x = 0; x < g.x.cols; x++) {
                P p = current({gx[x], gy[x]});
                bx[x] = p.x;
                by[x] = p.y;
            }
        });
        return b;
    }
    cv::Mat sample(const cv::Mat &im, const Grid &g) const {
        cv::Mat x, y, out;
        g.x.convertTo(x, CV_32F);
        g.y.convertTo(y, CV_32F);
        cv::remap(im, out, x, y, cv::INTER_LINEAR, cv::BORDER_CONSTANT, 0);
        return out;
    }
    std::vector<double> samples(const cv::Mat &im, const Path &p) const {
        Grid g;
        g.x.create(1, (int)p.size(), CV_64F);
        g.y.create(1, (int)p.size(), CV_64F);
        for (int i = 0; i < (int)p.size(); i++) {
            g.x.at<double>(0, i) = p[i].x;
            g.y.at<double>(0, i) = p[i].y;
        }
        cv::Mat m = sample(im, g);
        std::vector<double> v;
        for (int i = 0; i < m.cols; i++)
            v.push_back(m.depth() == CV_8U ? m.at<uchar>(0, i) : m.at<float>(0, i));
        return v;
    }
    void choosePatches();
    bool recoverMotion(const cv::Mat &,double &,int &);
    bool recoverAnchorMotion(const cv::Mat &,double &,int &);
    void motion(const cv::Mat &, const std::array<P, 2> *, bool, double &, int &);
    void locateRoot();
    void refineRoot(const cv::Mat &, bool);
    Tile tile(const cv::Mat &, P, P, int, int, int);
    bool seed(const cv::Mat &, bool, Path &, std::vector<double> &, double &);
    bool entrance(const Path &, P &, double &, std::string &);
    void measure(Path, std::vector<double>, double, Result &);
    void terminalAudit(const Path &, const std::vector<double> &, const std::vector<double> &,
                       const Tile &, P, P, int, bool, bool, Result &);
    Result process(const cv::Mat &, const std::array<P, 2> *, bool = false);
};
void Detector::choosePatches() {
    int pw = std::max(64, std::min(160, rnd(spacing * .7))),
        ph = std::max(32, std::min(64, rnd(spacing * .32)));
    for (double f : {1.5, 2.3, 3.2})
        for (double a : {-.28, .28}) {
            P center = origin + forward * (f * spacing) + normal * (a * spacing);
            int x = rnd(center.x - pw / 2.), y = rnd(center.y - ph / 2.);
            if (x < 0 || y < 0 || x + pw >= width || y + ph >= height)
                continue;
            cv::Mat p;
            reference(cv::Rect(x, y, pw, ph)).convertTo(p, CV_32F);
            int bright = cv::countNonZero(p > 100);
            if (double(bright) / p.total() < .93 || stdf(p) < 1)
                continue;
            cv::Mat lap;
            cv::Laplacian(p, lap, CV_32F);
            double patch_quality = stdf(lap);
            float mean = meanf(p);
            p -= mean;
            cv::Mat win;
            cv::createHanningWindow(win, {pw, ph}, CV_32F);
            patches.push_back({{x, y, pw, ph}, p, win, patch_quality});
        }
    std::stable_sort(patches.begin(), patches.end(),
                     [](const Patch &a, const Patch &b) { return a.quality > b.quality; });
    if (patches.size() > 4)
        patches.resize(4);
}

// Fixed bounded recovery only after automatic phase-correlation failure.
// It uses CURRENT-image evidence from at least two independent reference patches.
bool Detector::recoverAnchorMotion(const cv::Mat &im,double &response,int &count) {
    if(!(cfg.experiments & CV4_ANCHOR_PATCH_RECOVERY))return false;
    recovery_attempted=true;
    const int radius=64,half=std::max(8,std::min(80,rnd(.18*spacing)));
    std::array<P,2> matched{};double sum=0;
    for(int j=0;j<2;++j) {
        cv::Rect rect(rnd(anchors[j].x)-half,rnd(anchors[j].y)-half,2*half+1,2*half+1);
        if(rect.x<0||rect.y<0||rect.br().x>width||rect.br().y>height)return false;
        cv::Rect sr(rect.x-radius,rect.y-radius,rect.width+2*radius,rect.height+2*radius);
        sr &= cv::Rect(0,0,im.cols,im.rows);
        if(sr.width<=rect.width||sr.height<=rect.height)return false;
        cv::Mat templ,search,corr;reference(rect).convertTo(templ,CV_32F);
        if(stdf(templ)<3)return false;
        im(sr).convertTo(search,CV_32F);cv::matchTemplate(search,templ,corr,cv::TM_CCOEFF_NORMED);
        double best;cv::Point peak;cv::minMaxLoc(corr,nullptr,&best,nullptr,&peak);
        P pos(peak.x,peak.y),delta(sr.x+peak.x-rect.x,sr.y+peak.y-rect.y);
        // Parabolic peak interpolation stays inside the current matched patch.
        if(peak.x>0&&peak.y>0&&peak.x<corr.cols-1&&peak.y<corr.rows-1)for(int axis=0;axis<2;++axis) {
            double a=axis?corr.at<float>(peak.y-1,peak.x):corr.at<float>(peak.y,peak.x-1),
                b=corr.at<float>(peak.y,peak.x),c=axis?corr.at<float>(peak.y+1,peak.x):corr.at<float>(peak.y,peak.x+1),den=a-2*b+c;
            if(den<-1e-6)(axis?pos.y:pos.x)+=clip(.5*(a-c)/den,-.5,.5);
        }
        cv::Rect exclusion(peak.x-8,peak.y-8,17,17);exclusion &= cv::Rect(0,0,corr.cols,corr.rows);
        corr(exclusion).setTo(-1);double second;cv::minMaxLoc(corr,nullptr,&second);
        bool accepted=std::isfinite(best)&&best>=.9&&best-second>=.08&&
            std::max(std::abs(delta.x),std::abs(delta.y))<radius&&peak.x>0&&peak.y>0&&peak.x<corr.cols-1&&peak.y<corr.rows-1;
        if(debug())recovery_debug.push_back({rect,delta,best,best-second,accepted});
        if(!accepted)return false;
        matched[j]=anchors[j]+P(sr.x+pos.x-rect.x,sr.y+pos.y-rect.y);sum+=best;
    }
    P a=unit(anchors[1]-anchors[0]),b=unit(matched[1]-matched[0]);double c=dot(a,b),s=a.x*b.y-a.y*b.x;
    double ratio=norm(matched[1]-matched[0])/spacing;
    if(ratio<.5||ratio>1.5||std::abs(std::atan2(s,c))>.13962634015954636)return false;
    rotation={c,-s,s,c};translation=(matched[0]+matched[1])*.5-P(c*origin.x-s*origin.y,s*origin.x+c*origin.y);
    response=sum*.5;count=2;registration_inliers=2;registration_residual=0;
    recovery_used=true;anchor_recovery_used=true;return true;
}
bool Detector::recoverMotion(const cv::Mat &im,double &response,int &count) {
    if(recoverAnchorMotion(im,response,count))return true;
    if(!(cfg.experiments & CV4_REGISTRATION_RECOVERY)) return false;
    recovery_attempted=true;
    struct Match { P delta; double score; };
    std::vector<Match> matches;
    const int radius=64;
    for(const auto &p:patches) { // choosePatches has already bounded this to four.
        cv::Rect searchRect(p.rect.x-radius,p.rect.y-radius,p.rect.width+2*radius,p.rect.height+2*radius);
        searchRect &= cv::Rect(0,0,im.cols,im.rows);
        if(searchRect.width<=p.rect.width || searchRect.height<=p.rect.height) continue;
        cv::Mat search,corr; im(searchRect).convertTo(search,CV_32F);
        cv::matchTemplate(search,p.patch,corr,cv::TM_CCOEFF_NORMED);
        double best; cv::Point peak; cv::minMaxLoc(corr,nullptr,&best,nullptr,&peak);
        P delta(searchRect.x+peak.x-p.rect.x,searchRect.y+peak.y-p.rect.y);
        cv::Rect exclusion(peak.x-4,peak.y-4,9,9); exclusion &= cv::Rect(0,0,corr.cols,corr.rows);
        corr(exclusion).setTo(-1); double second; cv::minMaxLoc(corr,nullptr,&second);
        bool accepted=std::isfinite(best) && best>=.6 && best-second>=.08 &&
            std::max(std::abs(delta.x),std::abs(delta.y))<radius &&
            peak.x>0 && peak.y>0 && peak.x<corr.cols-1 && peak.y<corr.rows-1;
        if(debug()) recovery_debug.push_back({p.rect,delta,best,best-second,accepted});
        if(accepted) matches.push_back({delta,best});
    }
    if(matches.size()<2) return false;
    std::vector<double> xs,ys; for(auto &m:matches) {xs.push_back(m.delta.x);ys.push_back(m.delta.y);}
    P center(med(xs),med(ys)),sum{}; double weight=0;int good=0;
    for(auto &m:matches) if(norm(m.delta-center)<=2.) {sum+=m.delta*m.score;weight+=m.score;++good;}
    if(good<2) return false;
    translation=sum/weight;rotation=cv::Matx22d::eye();response=weight/good;count=good;
    registration_inliers=good; registration_residual=0;
    std::vector<double> residual;for(auto &m:matches)if(norm(m.delta-center)<=2.)residual.push_back(norm(m.delta-translation));
    registration_residual=med(residual);recovery_used=true;return true;
}
void Detector::motion(const cv::Mat &im, const std::array<P, 2> *ap, bool isref, double &response,
                      int &count) {
    PROFILE_SCOPE(0);
    struct Estimate {
        P source, delta;
        double weight;
    };
    std::vector<Estimate> es;
    response = 0;
    count = 0;
    registration_inliers=0; registration_residual=0;
    last_anchors_supplied=ap!=nullptr || isref;
    current_anchor_valid=false;registration_ambiguous=false;
    automatic_success_reviewed=false;automatic_success_repaired=false;
    recovery_attempted=false;recovery_used=false;anchor_recovery_used=false;if(debug())recovery_debug.clear();
    if(debug()) debug_motion.clear();
    if (isref) {
        rotation = cv::Matx22d::eye();
        translation = {};
        return;
    }
    if (ap) {
        validatePoints(*ap, im.size(), 2);
        current_anchor_valid=true;
        P a = unit(anchors[1] - anchors[0]), b = unit((*ap)[1] - (*ap)[0]);
        double c = dot(a, b), s = a.x * b.y - a.y * b.x;
        rotation = {c, -s, s, c};
        translation = ((*ap)[0] + (*ap)[1]) * .5 - P(rotation(0, 0) * origin.x + rotation(0, 1) * origin.y,
                                                     rotation(1, 0) * origin.x + rotation(1, 1) * origin.y);
    } else {
        if (im.size() != reference.size())
            throw std::runtime_error("Image size differs from reference");
        rotation = cv::Matx22d::eye();
        translation = {};
    }
    if (!ap || cfg.refine && !isref)
        for (auto &p : patches) {
            cv::Mat cur;
            if (ap) {
                Grid g;
                g.x.create(p.rect.height, p.rect.width, CV_64F);
                g.y.create(p.rect.height, p.rect.width, CV_64F);
                bool valid = true;
                for (int y = 0; y < g.x.rows; y++)
                    for (int x = 0; x < g.x.cols; x++) {
                        P q = current(P(p.rect.x + x, p.rect.y + y));
                        g.x.at<double>(y, x) = q.x;
                        g.y.at<double>(y, x) = q.y;
                        if (q.x < 1 || q.y < 1 || q.x >= im.cols - 1 || q.y >= im.rows - 1)
                            valid = false;
                    }
                if (!valid)
                    continue;
                sample(im, g).convertTo(cur, CV_32F);
            } else
                im(p.rect).convertTo(cur, CV_32F);
            cur -= meanf(cur);
            double r = 0;
            P d = cv::phaseCorrelate(p.patch.clone(), cur, p.window, &r);
            double limit = ap ? std::min(p.rect.width, p.rect.height) * .2 : cfg.maxshift;
            bool accepted=r > (ap ? .2 : .15) && std::isfinite(d.x) && std::isfinite(d.y) &&
                std::max(std::abs(d.x), std::abs(d.y)) <= limit;
            if(debug()) debug_motion.push_back({p.rect,r,limit,-1,d,accepted,false});
            if (accepted)
                es.push_back({{p.rect.x + p.rect.width / 2., p.rect.y + p.rect.height / 2.}, d, r});
        }
    count = (int)es.size();
    if (es.empty()) {
        if (!ap) {
            if(recoverMotion(im,response,count)) return;
            throw std::runtime_error("Registration failed for all automatically selected patches");
        }
        return;
    }
    std::vector<double> xs, ys;
    for (auto e : es) {
        xs.push_back(e.delta.x);
        ys.push_back(e.delta.y);
    }
    P center(med(xs), med(ys));
    std::vector<Estimate> good;
    double threshold = ap ? std::max(2., .035 * spacing) : std::max(1.5, .03 * spacing);
    double allresponse = 0;
    for (auto e : es) {
        allresponse += e.weight;
        if (norm(e.delta - center) < threshold)
            good.push_back(e);
    }
    if(debug()) for(auto &record:debug_motion) if(record.accepted) {
        record.residual=norm(record.delta-center); record.inlier=record.residual<threshold;
    }
    if (good.empty()) {
        if (!ap)
        {
            if(recoverMotion(im,response,count)) return;
            throw std::runtime_error("Automatic registration patch estimates disagree");
        }
        response = 0;
        count = 0;
        return;
    }
    registration_inliers=(int)good.size();
    double sw = 0;
    P delta{};
    for (auto e : good) {
        sw += e.weight;
        delta += e.delta * e.weight;
    }
    delta /= sw;
    if(debug()) { std::vector<double> residual; for(auto e:good) residual.push_back(norm(e.delta-delta)); registration_residual=med(residual); }
    if (!ap) {
        translation = delta;
        response = sw / good.size();
        // A low patch count triggers independent current-image verification;
        // it does not by itself prove that the successful phase estimate is wrong.
        if((cfg.experiments & CV4_GUARDED_REGISTRATION) &&
           (good.size()<2 || response<.2)) {
            automatic_success_reviewed=true;
            const auto previous_rotation=rotation;
            const auto previous_translation=translation;
            const int previous_count=count;
            const double previous_response=response;
            if(recoverMotion(im,response,count)) automatic_success_repaired=true;
            else {
                rotation=previous_rotation;translation=previous_translation;
                count=previous_count;response=previous_response;
                registration_ambiguous=true;
            }
        }
        return;
    }
    response = allresponse / es.size();
    bool refined = false;
    if (good.size() >= 3) {
        double xmin = 1e100, xmax = -1e100, ymin = 1e100, ymax = -1e100;
        P ca{}, cb{};
        for (auto e : good) {
            xmin = std::min(xmin, e.source.x);
            xmax = std::max(xmax, e.source.x);
            ymin = std::min(ymin, e.source.y);
            ymax = std::max(ymax, e.source.y);
            ca += e.source * e.weight;
            cb += current(e.source + e.delta) * e.weight;
        }
        ca /= sw;
        cb /= sw;
        if (std::hypot(xmax - xmin, ymax - ymin) > .3 * spacing) {
            cv::Matx22d m = cv::Matx22d::zeros();
            for (auto e : good) {
                P a = e.source - ca, b = (current(e.source + e.delta) - cb) * e.weight;
                m(0, 0) += a.x * b.x;
                m(0, 1) += a.x * b.y;
                m(1, 0) += a.y * b.x;
                m(1, 1) += a.y * b.y;
            }
            cv::SVD svd(cv::Mat(m), cv::SVD::FULL_UV);
            cv::Mat U = svd.u, V = svd.vt.t(), corr = cv::Mat::eye(2, 2, CV_64F);
            corr.at<double>(1, 1) = cv::determinant(V * U.t());
            cv::Mat rr = V * corr * U.t();
            cv::Matx22d rot(rr.at<double>(0, 0), rr.at<double>(0, 1), rr.at<double>(1, 0),
                            rr.at<double>(1, 1));
            P tr = cb - P(rot(0, 0) * ca.x + rot(0, 1) * ca.y, rot(1, 0) * ca.x + rot(1, 1) * ca.y);
            std::vector<double> residual;
            for (auto e : good) {
                P q(rot(0, 0) * e.source.x + rot(0, 1) * e.source.y + tr.x,
                    rot(1, 0) * e.source.x + rot(1, 1) * e.source.y + tr.y);
                residual.push_back(norm(q - current(e.source + e.delta)));
            }
            cv::Matx22d diff = rot * rotation.t();
            double angle = std::abs(std::atan2(diff(1, 0), diff(0, 0)) * 180 / CV_PI);
            if (angle < 8 && med(residual) < 2) {
                rotation = rot;
                translation = tr;
                refined = true;
            }
        }
    }
    if (!refined)
        translation += P(rotation(0, 0) * delta.x + rotation(0, 1) * delta.y,
                         rotation(1, 0) * delta.x + rotation(1, 1) * delta.y);
}

void Detector::locateRoot() {
    Grid xy = grid(origin, forward, seed_u0, seed_width, seed_half);
    cv::Mat ref = sample(reference, xy);
    cv::GaussianBlur(ref, ref, {3, 3}, .6);
    auto select = [&](bool opening, bool validmask) -> cv::Mat {
        cv::Mat tmp;
        double otsu = cv::threshold(ref, tmp, 0, 255, cv::THRESH_BINARY | cv::THRESH_OTSU);
        cv::Mat mask = ref < std::min(120., std::max(45., otsu));
        if (validmask)
            for (int y = 0; y < mask.rows; y++)
                for (int x = 0; x < mask.cols; x++) {
                    double xx = xy.x.at<double>(y, x), yy = xy.y.at<double>(y, x);
                    if (!(xx > 1 && yy > 1 && xx < width - 2 && yy < height - 2))
                        mask.at<uchar>(y, x) = 0;
                }
        if (opening)
            cv::morphologyEx(mask, mask, cv::MORPH_OPEN, cv::Mat::ones(3, 3, CV_8U));
        cv::Mat labels, stats, cents;
        int n = cv::connectedComponentsWithStats(mask, labels, stats, cents, 8);
        int best = -1, area = -1;
        for (int k = 1; k < n; k++) {
            int x = stats.at<int>(k, 0), y = stats.at<int>(k, 1), h = stats.at<int>(k, 3),
                a = stats.at<int>(k, 4);
            if (x > std::max(4, rnd(.08 * spacing)) || !(y <= seed_half && seed_half < y + h) ||
                (!opening && a < 20))
                continue;
            if (a > area || a == area && k > best) {
                area = a;
                best = k;
            }
        }
        if (best < 0)
            return cv::Mat::zeros(mask.size(), CV_8U);
        return labels == best;
    };
    cv::Mat selected = select(false, true);
    capture("root_selected",selected);
    int cutoff = std::max(4, rnd(.02 * spacing)), column = -1;
    std::vector<int> widths(selected.cols);
    for (int x = 0; x < selected.cols; x++) {
        widths[x] = cv::countNonZero(selected.col(x));
        if (widths[x] >= cutoff)
            column = x;
    }
    if (column >= 0 && column < seed_width - 3) {
        std::vector<double> rr;
        for (int y = 0; y < selected.rows; y++)
            if (selected.at<uchar>(y, column))
                rr.push_back(y);
        double row = med(rr);
        for (int x = column + 1, limit = std::min(seed_width, column + cutoff + 2); x < limit; x++) {
            rr.clear();
            for (int y = 0; y < selected.rows; y++)
                if (selected.at<uchar>(y, x) && std::abs(y - row) < cutoff)
                    rr.push_back(y);
            if (rr.empty() || widths[x] >= cutoff)
                break;
            column = x;
            row = med(rr);
        }
        root_reference = origin + forward * (column + seed_u0) + normal * (row - seed_half);
        root_exists = true;
    }
    entry_mask = select(true, false);
    capture("entry_mask",entry_mask);
    boundary.assign(entry_mask.rows, NaN);
    for (int y = 0; y < entry_mask.rows; y++)
        for (int x = 0; x < entry_mask.cols; x++)
            if (entry_mask.at<uchar>(y, x))
                boundary[y] = x + .5;
}
void Detector::refineRoot(const cv::Mat &im, bool isref) {
    frame_root = root_reference;
    root_response = 0;
    if (root_template.empty() || isref)
        return;
    int radius = std::max(4, std::min(20, rnd(spacing * .055)));
    cv::Mat search;
    sample(im, transformed(grid(root_reference, forward, root_patch_u - radius, root_patch_width + 2 * radius,
                                root_patch_half + radius)))
        .convertTo(search, CV_32F);
    cv::Mat res;
    cv::matchTemplate(search, root_template, res, cv::TM_CCOEFF_NORMED);
    cv::Point loc;
    cv::minMaxLoc(res, nullptr, &root_response, nullptr, &loc);
    if (root_response < .6)
        return;
    P position(loc.x, loc.y);
    for (int axis = 0; axis < 2; axis++) {
        int index = axis ? loc.y : loc.x, maximum = axis ? res.rows : res.cols;
        if (index > 0 && index < maximum - 1) {
            float a = axis ? res.at<float>(loc.y - 1, loc.x) : res.at<float>(loc.y, loc.x - 1),
                  b = res.at<float>(loc.y, loc.x),
                  c = axis ? res.at<float>(loc.y + 1, loc.x) : res.at<float>(loc.y, loc.x + 1);
            double denominator = a - 2. * b + c;
            if (denominator < -1e-6)
                (axis ? position.y : position.x) += clip(.5 * (double)(float)(a - c) / denominator, -.5, .5);
        }
    }
    P delta = position - P(radius, radius);
    frame_root += forward * delta.x + normal * delta.y;
}

Tile Detector::tile(const cv::Mat &im, P o, P d, int u0, int w, int half) {
    PROFILE_SCOPE(2);
    PROFILE_LAPS;
    bool tracking = !(std::abs(o.x - origin.x) <= 1e-8 + 1e-5 * std::abs(origin.x) &&
                      std::abs(o.y - origin.y) <= 1e-8 + 1e-5 * std::abs(origin.y));
    int back = tracking && u0 == 0 ? std::max(8, rnd(w * .25)) : 0;
    Tile t;
    t.back = back;
    const bool seed_tile = o == origin && d == forward && u0 == seed_u0 &&
                           w == seed_width && half == seed_half && !back;
    const bool cached = seed_tile && !seed_reference_cache.empty();
    t.xy = cached ? seed_grid_cache : grid(o, d, u0 - back, w + back, half);
    Grid cq = transformed(t.xy);
    if (cached)
        t.reference = seed_reference_cache;
    else {
        sample(reference, t.xy).convertTo(t.reference, CV_32F);
        cv::GaussianBlur(t.reference, t.reference, {3, 3}, .6);
    }
    cv::Mat cur;
    sample(im, cq).convertTo(cur, CV_32F);
    cv::GaussianBlur(cur, cur, {3, 3}, .6);
    int h = t.reference.rows, ww = t.reference.cols;
    PROFILE_LAP(8);
    t.valid = cv::Mat(h, ww, CV_8U);
    cv::Mat allowed = cv::Mat::zeros(h, ww, CV_8U);
    if (absolute)
        allowed.setTo(255);
    else if (!baseline_mask.empty()) {
        cv::Mat a = sample(baseline_mask, t.xy);
        allowed = a > 127;
    }
    std::vector<double> offsets;
    for (int y = 0; y < h; y++)
        for (int x = 0; x < ww; x++) {
            double xx = t.xy.x.at<double>(y, x), yy = t.xy.y.at<double>(y, x), cx = cq.x.at<double>(y, x),
                   cy = cq.y.at<double>(y, x);
            bool valid = xx > 2 && xx < width - 3 && yy > 2 && yy < height - 3 && cx > 2 &&
                         cx < curwidth - 3 && cy > 2 && cy < curheight - 3;
            t.valid.at<uchar>(y, x) = valid ? 255 : 0;
            if (valid && t.reference.at<float>(y, x) > 140)
                offsets.push_back((float)(cur.at<float>(y, x) - t.reference.at<float>(y, x)));
        }
    float offset = (float)medf(std::move(offsets));
    PROFILE_LAP(9);
    auto lines = [](const cv::Mat &a) {
        cv::Mat out = cv::Mat::zeros(a.size(), CV_32F);
        for (int k : {5, 9, 13}) {
            cv::Mat b;
            cv::morphologyEx(a, b, cv::MORPH_BLACKHAT, cv::getStructuringElement(cv::MORPH_RECT, {1, k}));
            cv::max(out, b, out);
        }
        return out;
    };
    cv::Mat rl = cached ? seed_lines_cache : lines(t.reference), cl = lines(cur), bg;
    cv::Mat rbg;
    if (cached)
        rbg = seed_background_cache;
    else
        rbg = t.reference + rl;
    cv::Mat cbg = cur + cl;
    cv::max(rbg, cbg, bg);
    PROFILE_LAP(10);
    t.score = cv::Mat(h, ww, CV_32F);
    t.material = cv::Mat(h, ww, CV_32F);
    float floor = 2;
    if (cv::countNonZero(allowed)) {
        std::vector<double> vals;
        for (int y = 0; y < h; y++)
            for (int x = 0; x < ww; x++)
                if (bg.at<float>(y, x) > 165 && t.valid.at<uchar>(y, x))
                    vals.push_back(cl.at<float>(y, x));
        float m = (float)medf(vals);
        for (double &v : vals)
            v = (float)std::abs((float)v - m);
        double mad = medf(std::move(vals));
        floor = (float)std::max(2., m + 3 * 1.4826 * mad);
    }
    cv::Mat old;
    if (cached)
        old = seed_old_cache;
    else
        cv::dilate(rl > 25, old, cv::Mat::ones(3, 3, CV_8U));
    for (int y = 0; y < h; y++)
        for (int x = 0; x < ww; x++) {
            float ref = t.reference.at<float>(y, x), c = cur.at<float>(y, x), rline = rl.at<float>(y, x),
                  cline = cl.at<float>(y, x), background = bg.at<float>(y, x);
            bool allow = allowed.at<uchar>(y, x) != 0;
            float score = std::max(0.f, std::min((float)(ref - c + offset), (float)(cline - rline)));
            if (allow)
                score = std::max(0.f, (float)(cline - floor));
            if (!t.valid.at<uchar>(y, x) || (old.at<uchar>(y, x) && !allow) ||
                (ref < 110 && !(allow && background > 140)))
                score = 0;
            t.score.at<float>(y, x) = score;
            t.material.at<float>(y, x) = allow ? background : ref;
        }
    cv::GaussianBlur(t.score, t.score, {3, 3}, .65);
    PROFILE_LAP(11);
    std::vector<double> vals, noise;
    int noise_band = std::max(6, rnd(.10 * spacing));
    for (int y = 0; y < h; y++)
        for (int x = 0; x < ww; x++)
            if (t.valid.at<uchar>(y, x) && t.material.at<float>(y, x) > 165) {
                double v = t.score.at<float>(y, x);
                vals.push_back(v);
                if (std::abs(y - half) > noise_band)
                    noise.push_back(v);
            }
    float m = (float)medf(vals);
    for (double &v : vals)
        v = (float)std::abs((float)v - m);
    double mad = medf(std::move(vals)), tail = noise.size() >= 32 ? percentile(std::move(noise), .95) : 0;
    t.threshold = std::max({cfg.score, m + 3 * 1.4826 * mad, tail});
    cv::Mat debug_raw;
    if(cfg.experiments & CV4_DEBUG_IMAGES) debug_raw=t.score.clone();
    PROFILE_LAP(12);
    float delta = (float)(t.threshold - cfg.score);
    for (int y = 0; y < h; y++)
        for (int x = 0; x < ww; x++)
            t.score.at<float>(y, x) = std::max(0.f, (float)(t.score.at<float>(y, x) - delta));
    if (seed_tile && !cached) {
        seed_grid_cache = t.xy;
        seed_reference_cache = t.reference;
        seed_lines_cache = rl;
        seed_background_cache = rbg;
        seed_old_cache = old;
    }
    if (back) {
        cv::Rect r(back, 0, ww - back, h);
        t.score = t.score(r).clone();
        t.reference = t.reference(r).clone();
        t.material = t.material(r).clone();
        t.valid = t.valid(r).clone();
        t.xy.x = t.xy.x(r).clone();
        t.xy.y = t.xy.y(r).clone();
    }
    if(cfg.experiments & (CV4_PHOTOMETRIC_EXPERIMENT | CV4_CURRENT_TEXTURE_GUARD))
        t.current_gray=cur(cv::Rect(back,0,ww-back,h));
    if(debug()) {
        TileDebug record; record.origin=o; record.direction=d; record.u0=u0; record.width=t.score.cols;
        record.half=half; record.back=back; record.offset=offset; record.median=m; record.mad=mad;
        record.noise=tail; record.threshold=t.threshold; record.invalid=1.-double(cv::countNonZero(t.valid))/t.valid.total();
        std::string prefix="tile"+std::to_string(debug_tiles.size())+"_";
        debug_tiles.push_back(record);
        capture(prefix+"score",t.score); capture(prefix+"reference",t.reference);
        cv::Rect crop(back,0,ww-back,h);
        capture(prefix+"current",cur(crop)); capture(prefix+"raw",debug_raw.empty()?debug_raw:debug_raw(crop));
        capture(prefix+"old",old(crop)); capture(prefix+"allowed",allowed(crop)); capture(prefix+"valid",t.valid);
    }
    PROFILE_LAP(13);
    return t;
}
bool Detector::seed(const cv::Mat &im, bool isref, Path &path, std::vector<double> &strengths, double &peak) {
    PROFILE_SCOPE(1);
    refineRoot(im, isref);
    entrance_offset = root_exists && root_response >= .6 ? frame_root - root_reference : P();
    quality = {};
    seed_region = tile(im, origin, forward, seed_u0, seed_width, seed_half);
    PROFILE_LAPS;
    cv::Mat field = seed_region.score.clone();
    field.setTo(0, seed_region.valid == 0);
    int h = field.rows, w = field.cols;
    std::vector<double> rows(h), profile(h), filled(h), finite, finitevalues;
    std::iota(rows.begin(), rows.end(), 0.);
    double transverse = dot(entrance_offset, normal), fwd = dot(entrance_offset, forward);
    for (int y = 0; y < h; y++) {
        double pos = y - transverse;
        profile[y] = (pos < 0 || pos > h - 1) ? NaN : interp(pos, rows, boundary) + fwd;
        if (std::isfinite(profile[y])) {
            finite.push_back(y);
            finitevalues.push_back(profile[y]);
        }
    }
    std::vector<double> slope(h);
    if (!finite.empty()) {
        for (int y = 0; y < h; y++)
            filled[y] = interp(y, finite, finitevalues);
        slope = gradient(gauss(filled, 2., false));
    }
    double allowance = std::max(12., cfg.entrance_fraction * spacing),
           band = std::max(2., std::min(6., .02 * spacing));
    cv::Mat reward(h, w, CV_32F), penalty(h, w, CV_64F), starts = cv::Mat::zeros(h, w, CV_8U);
    double priorv = previous.empty() ? 0 : dot(previous.front() - origin, normal) + seed_half;
    float base = (float)(6 * std::log1p(cfg.score / 3));
    independentRows(h, w, [&](int y) {
        // These terms depend only on the row, not on the column. Keep the
        // original expressions and addition order for every output pixel.
        double row_penalty = .6 * std::pow((y - seed_half) / std::max(6., .15 * spacing), 2);
        double prior_penalty = !previous.empty() && !absolute
                                   ? .3 * std::min(std::pow(y - priorv, 2) /
                                                        std::pow(std::max(6., .1 * spacing), 2), 4.)
                                   : 0.;
        float *field_row = field.ptr<float>(y), *reward_row = reward.ptr<float>(y);
        double *penalty_row = penalty.ptr<double>(y);
        uchar *starts_row = starts.ptr<uchar>(y);
        const uchar *valid_row = seed_region.valid.ptr<uchar>(y);
        const float *material_row = seed_region.material.ptr<float>(y);
        for (int x = 0; x < w; x++) {
            double gap = x - profile[y];
            bool start;
            if (!finite.empty()) {
                if (std::isfinite(profile[y]) && gap < band)
                    field_row[x] = 0;
                start =
                    std::isfinite(profile[y]) && gap >= band && gap <= allowance && std::abs(slope[y]) <= 1.5;
            } else
                start = x + seed_u0 >= 0 && x + seed_u0 <= .3 * spacing;
            float value = field_row[x];
            start = start && valid_row[x] && value > cfg.score && material_row[x] > 140;
            starts_row[x] = start ? 255 : 0;
            double distance = !finite.empty() ? std::abs(gap) : std::abs(x + seed_u0);
            if (std::isnan(distance))
                distance = allowance;
            double p = .08 * distance + row_penalty;
            if (!previous.empty() && !absolute)
                p += prior_penalty;
            penalty_row[x] = p;
            float v = std::max(value, 0.f) / 3.f;
            reward_row[x] = (float)((float)(6.f * std::log1p(v)) - base);
        }
    });
    if(debug()) starts_count=cv::countNonZero(starts);
    capture("seed_starts",starts); capture("seed_field",field); capture("entry_mask",entry_mask);
    std::vector<double> acc(h, -1e8);
    PROFILE_LAP(14);
    std::vector<int> parents(w * h, -1);
    double gain = -1e8;
    int bestx = 0, besty = 0;
    {
    PROFILE_SCOPE(3);
    for (int x = 0; x < w; x++) {
        std::vector<double> next(h);
        for (int y = 0; y < h; y++) {
            double v = -1e8;
            int by = 0;
            for (int d = -2; d <= 2; d++) {
                int p = y + d;
                if (p < 0 || p >= h)
                    continue;
                double q = acc[p] - 1.2 * d * d;
                if (q > v) {
                    v = q;
                    by = p;
                }
            }
            double continued = v + reward.at<float>(y, x),
                   fresh = starts.at<uchar>(y, x) ? reward.at<float>(y, x) - penalty.at<double>(y, x) : -1e8;
            bool restart = fresh > continued;
            next[y] = std::max(fresh, continued);
            parents[x * h + y] = restart ? -1 : by;
        }
        acc.swap(next);
        int y = (int)(std::max_element(acc.begin(), acc.end()) - acc.begin());
        if (acc[y] > gain) {
            gain = acc[y];
            bestx = x;
            besty = y;
        }
    }
    }
    Path ridgep;
    int x = bestx, y = besty;
    while (x >= 0) {
        ridgep.emplace_back(x, y);
        int before = parents[x * h + y];
        if (before < 0)
            break;
        --x;
        y = before;
    }
    std::reverse(ridgep.begin(), ridgep.end());
    tracePath(ridgep);
    for (P &p : ridgep) {
        int xx = (int)p.x, yy = (int)p.y;
        if (yy > 0 && yy < h - 1) {
            float a = field.at<float>(yy - 1, xx), b = field.at<float>(yy, xx),
                  c = field.at<float>(yy + 1, xx);
            double den = a - 2. * b + c;
            if (den < -1e-5)
                p.y += clip(.5 * (double)(float)(a - c) / den, -.5, .5);
        }
    }
    std::vector<double> ss;
    std::vector<int> supported;
    for (int k = 0; k < (int)ridgep.size(); k++) {
        double v = mapcoord(field, ridgep[k].y, ridgep[k].x);
        ss.push_back(v);
        if (v > cfg.score)
            supported.push_back(k);
    }
    int minimum = std::max(6, rnd(.025 * spacing));
    ap3_seed[0]=1; ap3_seed[1]=double(supported.size()); ap3_seed[2]=minimum;
    ap3_seed[3]=gain; ap3_seed[4]=double(ridgep.size());
    if ((int)supported.size() < minimum || gain < minimum * 1.5)
        return false;
    int first = supported.front(), lastidx = supported.back(), gaprun = 0;
    for (int j = first; j <= lastidx; j++) {
        gaprun = ss[j] > cfg.score ? 0 : gaprun + 1;
        if (gaprun > cfg.maxgap) {
            lastidx = std::max(first, j - gaprun);
            break;
        }
    }
    ap3_seed[0]=2; ap3_seed[5]=lastidx-first;
    if (lastidx - first < minimum)
        return false;
    int startup_end = std::min(lastidx + 1, first + std::max(12, minimum * 2));
    double maxstart = 0;
    int good = 0;
    for (int j = first; j < startup_end; j++) {
        good += ss[j] > cfg.score;
        maxstart = std::max(maxstart, ss[j]);
    }
    ap3_seed[0]=3; ap3_seed[6]=double(good)/(startup_end-first); ap3_seed[7]=maxstart; ap3_seed[8]=cfg.score;
    if (double(good) / (startup_end - first) < .6 || maxstart < 6)
        return false;
    ap3_seed[0]=4;
    int take = std::min(lastidx, first + cfg.advance);
    std::vector<double> widths;
    for (int j = first; j <= take; j += 3) {
        int xx = (int)ridgep[j].x, yy = rnd(ridgep[j].y), lo = yy, hi = yy;
        while (lo > 0 && field.at<float>(lo - 1, xx) > cfg.score)
            --lo;
        while (hi < h - 1 && field.at<float>(hi + 1, xx) > cfg.score)
            ++hi;
        widths.push_back(hi - lo + 1);
    }
    peak = 0;
    good = 0;
    std::vector<double> selected;
    for (int j = first; j <= take; j++) {
        P p = ridgep[j];
        path.push_back(origin + forward * (p.x + seed_u0) + normal * (p.y - seed_half));
        strengths.push_back(ss[j]);
        selected.push_back(ss[j]);
        peak = std::max(peak, ss[j]);
        good += ss[j] > cfg.score;
    }
    int row = std::max(0, std::min(h - 1, rnd(ridgep[first].y)));
    quality = {gain,
               double(good) / selected.size(),
               medf(selected),
               peak,
               std::isfinite(profile[row]) ? ridgep[first].x - profile[row] : NaN,
               ridgep[take].x - ridgep[first].x,
               (ridgep[take].x - ridgep[first].x) / std::max(1., med(widths)),
               med(widths)};
    return true;
}

bool Detector::entrance(const Path &path, P &root, double &distance, std::string &method) {
    tangent = false;
    root = path.front();
    distance = 0;
    method = "none";
    P direction = unit(path[std::min<size_t>(8, path.size() - 1)] - path[0]);
    double maximum = std::max(12., std::min(40., spacing * cfg.entrance_fraction));
    std::vector<double> ds;
    std::vector<bool> mask;
    for (double d = -maximum; d < .001; d += .25) {
        ds.push_back(d);
        P p = path[0] + direction * d - origin - entrance_offset;
        double x = dot(p, forward) - seed_u0, y = dot(p, normal) + seed_half;
        mask.push_back(mapcoord(entry_mask, y, x, 0, true) > .5);
    }
    std::vector<int> transitions;
    for (int i = 0; i + 1 < (int)mask.size(); i++)
        if (mask[i] && !mask[i + 1])
            transitions.push_back(i);
    double limit = std::min(12., double(cfg.maxgap + 2));
    auto contrast = [&](P edge, P dir, bool offsetbefore) {
        Path before, after;
        for (int k = 1; k <= 3; k++) {
            before.push_back(edge - dir * k - (offsetbefore ? entrance_offset : P()));
            after.push_back(edge + dir * k - (offsetbefore ? entrance_offset : P()));
        }
        auto a = samples(reference, before), b = samples(reference, after);
        double aa = std::accumulate(a.begin(), a.end(), 0.) / a.size(),
               bb = std::accumulate(b.begin(), b.end(), 0.) / b.size();
        return bb - aa >= 12 && bb >= 110;
    };
    for (auto it = transitions.rbegin(); it != transitions.rend(); ++it) {
        P edge = path[0] + direction * ds[*it + 1];
        double dist = norm(path[0] - edge);
        if (dist > limit)
            continue;
        if (contrast(edge, direction, true)) {
            root = edge;
            distance = dist;
            method = "tangent";
            tangent = true;
            return true;
        }
    }
    if (!cfg.fallback || seed_region.score.empty() || !cv::countNonZero(entry_mask))
        return false;
    std::vector<double> good, values;
    for (int i = 0; i < (int)boundary.size(); i++)
        if (std::isfinite(boundary[i])) {
            good.push_back(i);
            values.push_back(boundary[i]);
        }
    if (good.size() < 3)
        return false;
    std::vector<double> filled(boundary.size()), allrows(boundary.size());
    std::iota(allrows.begin(), allrows.end(), 0.);
    for (int i = 0; i < (int)filled.size(); i++)
        filled[i] = interp(i, good, values);
    auto slopes = gradient(gauss(filled, 2, false));
    struct Candidate {
        P root, delta;
        double distance, cost;
    };
    std::vector<Candidate> candidates;
    for (double row = good.front(); row < good.back() + .01; row += .25) {
        double xx = interp(row, good, values), slope = interp(row, allrows, slopes);
        P edge = origin + forward * (xx + seed_u0) + normal * (row - seed_half) + entrance_offset,
          delta = path[0] - edge;
        double dist = norm(delta);
        if (dist >= .25 && dist <= limit && dot(delta, forward) >= 0 && std::abs(slope) <= 1.5)
            candidates.push_back({edge, delta, dist, dist + 1 - dot(delta / dist, direction)});
    }
    std::stable_sort(candidates.begin(), candidates.end(),
                     [](const Candidate &a, const Candidate &b) { return a.cost < b.cost; });
    for (auto c : candidates) {
        P dir = unit(c.delta);
        bool inside = false;
        for (int k = 1; k <= 3; k++) {
            P p = c.root - dir * k - origin - entrance_offset;
            if (mapcoord(entry_mask, dot(p, normal) + seed_half, dot(p, forward) - seed_u0, 0, true) > .5)
                inside = true;
        }
        if (!inside || !contrast(c.root, dir, true))
            continue;
        Path seg = linspace(c.root, path[0], std::max(3, (int)std::ceil(c.distance) + 1)), test;
        test.insert(test.end(), seg.end() - std::min<size_t>(4, seg.size()), seg.end());
        test.insert(test.end(), path.begin(), path.begin() + std::min<size_t>(4, path.size()));
        int support = 0;
        for (P q : test) {
            P p = q - origin;
            support += mapcoord(seed_region.score, dot(p, normal) + seed_half, dot(p, forward) - seed_u0, 1,
                                true) > cfg.score;
        }
        if (double(support) / test.size() < .5)
            continue;
        root = c.root;
        distance = c.distance;
        method = "local_boundary";
        return true;
    }
    return false;
}

void Detector::measure(Path path, std::vector<double> strengths, double peak, Result &r) {
    PROFILE_SCOPE(5);
    path = smooth(path, 3.);
    P root;
    double distance;
    std::string method;
    bool root_supported = entrance(path, root, distance, method);
    bool shape = arc(path) / std::max(1., quality.width) >= 2.5;
    if (shape && !absolute) r.history_path = path;
    bool finite = std::any_of(boundary.begin(), boundary.end(), [](double d) { return std::isfinite(d); });
    bool strong = finite && quality.span >= std::max(12., .08 * spacing) && quality.peak >= cfg.strong_peak &&
                  quality.median >= 4 && quality.support >= .75;
    bool accepted = false;
    int hits = 0;
    std::string basis;
    if (absolute) {
        accepted = strong;
        basis = "reference_absolute_evidence";
    } else if (shape) {
        hits = 1;
        Path prefix;
        for (size_t k = 0; k < std::min<size_t>(30, path.size()); k += 3)
            prefix.push_back(path[k]);
        for (auto &observation : history) {
            const Path &prior = observation.path;
            if (prior.empty())
                continue;
            size_t n = std::min(prefix.size(),
                                (size_t)std::max(2, std::min((int)prefix.size(), (int)prior.size() / 3)));
            int good = 0;
            for (size_t k = 0; k < n; k++) {
                double nearest = 1e100;
                for (P p : prior)
                    nearest = std::min(nearest, norm(prefix[k] - p));
                good += nearest < std::max(3., .025 * spacing);
            }
            if (double(good) / n >= .75) {
                P a = unit(path[std::min<size_t>(15, path.size() - 1)] - path[0]),
                  b = unit(prior[std::min<size_t>(15, prior.size() - 1)] - prior[0]);
                if (dot(a, b) > .5)
                    ++hits;
            }
        }
        accepted = strong || hits >= cfg.temporal_hits;
        basis = strong ? "single_frame_strong" : accepted ? "temporal_confirmed" : "temporal_pending";
    } else {
        basis = "shape_rejected";
    }
    bool endpoint_valid = r.tip;
    r.tip = endpoint_valid && accepted;
    if (absolute && !root_supported)
        r.tip = false;
    r.length = r.tip && root_supported;
    r.root = root_supported;
    r.basis = basis;
    r.hits = hits;
    if (!accepted && endpoint_valid)
        r.stop = "temporal_pending";
    Path full;
    if (root_supported) {
        Path bridge = linspace(root, path[0], std::max(2, (int)std::ceil(distance * 2) + 1));
        full.assign(bridge.begin(), bridge.end() - 1);
        full.insert(full.end(), path.begin(), path.end());
    } else
        full = path;
    r.has = true;
    r.status = r.length ? (strong ? "main_segment_detected" : "weak_candidate")
                        : (r.tip                         ? "tip_only_detected"
                           : endpoint_valid && !accepted ? "candidate_pending"
                                                         : "tracking_incomplete");
    r.total = pyround(arc(full));
    r.visible = pyround(arc(path));
    r.bridge = pyround(distance);
    r.peak = pyround(peak);
    r.method = method;
    r.quality = quality;
    r.initial = pyround(baseline_length);
    r.rootref = rounded(root);
    r.tipref = rounded(full.back());
    r.endpoint = rounded(current(full.back()));
    r.tipxy = r.tip ? r.endpoint : P();
    r.rootxy = rounded(current(full.front()));
    r.first = rounded(current(path.front()));
    r.gaps = (int)std::count_if(strengths.begin(), strengths.end(), [&](double v) { return v < cfg.score; });
    r.prior = tangent ? full : path;
    for (P p : full)
        r.path.push_back(current(p));
    for (P p : path)
        r.observed.push_back(current(p));
}

Result Detector::process(const cv::Mat &im, const std::array<P, 2> *ap, bool isref) {
#ifdef CRACK_V4_PROFILE
    profile_ms.fill(0.);
#endif
    auto begin = Clock::now();
    ap2_count=0; ap2_overflow=false; ap3_seed.fill(0.);
    if(debug()) { debug_tiles.clear(); debug_images.clear(); starts_count=0; }
    curwidth = im.cols;
    curheight = im.rows;
    Result r;
    r.frame_index = frame_index + (isref ? 0 : 1);
    r.policy = policy;
    r.reference_state = reference_state;
    r.reference_reason = reference_reason;
    motion(im, ap, isref, r.response, r.patches);
    if (!isref) ++frame_index;
    r.rotation = rotation;
    r.shift = translation;
    if (isref && baseline_exists) {
        previous = baseline_path;
        return baseline;
    }
    Path path;
    std::vector<double> strengths;
    double peak = 0;
    bool found = seed(im, isref, path, strengths, peak);
    r.tiles = 1;
    if (!found) {
        if (!absolute) {
            Observation missing; missing.frame_index = r.frame_index; missing.stop = "no_seed";
            append(std::move(missing));
        }
        r.detector_ms = elapsed(begin);
        return r;
    }
    int half = std::max(20, std::min(40, rnd(spacing * .18))),
        limit = (int)std::ceil(2 * std::hypot(width, height) / std::max(8, cfg.advance));
    std::string stop = "safety_limit";
    Tile terminal_tile;
    P terminal_origin{}, terminal_direction{};
    std::vector<double> path_widths{quality.width};
    for (int iter = 0; iter < limit; iter++) {
        P d = unit(path.back() - path[path.size() - std::min<size_t>(14, path.size())]);
        if (dot(d, forward) < -.7) {
            stop = "direction_ambiguous";
            break;
        }
        P o = path.back();
        Tile t = tile(im, o, d, 0, cfg.tile, half);
        ++r.tiles;
        if (terminal_validation) {
            terminal_tile = t; // cv::Mat shallow references; no tile recomputation
            terminal_origin = o; terminal_direction = d;
        }
        cv::Mat field;
        cv::min(t.score, 15, field);
        auto dp = ridge(field, half, cfg.score);
        Path ridgep = dp.first;
        tracePath(ridgep);
        double gain = dp.second;
        std::vector<double> ss;
        std::vector<int> supported;
        for (int k = 0; k < (int)ridgep.size(); k++) {
            double v = mapcoord(t.score, ridgep[k].y, ridgep[k].x);
            ss.push_back(v);
            if (v > cfg.score)
                supported.push_back(k);
        }
        // Reuse the existing tile/path samples. Fixed 256 records, O(tile count).
        if (ap2_count < int(ap2_stops.size())) {
            P cp=current(o), cd=rotation*d;
            double med=0; if (!ss.empty()) { auto tmp=ss; auto mid=tmp.begin()+tmp.size()/2;
                std::nth_element(tmp.begin(),mid,tmp.end()); med=*mid; }
            ap2_stops[ap2_count++]={cp.x,cp.y,cd.x,cd.y,gain,
                ss.empty()?0.:double(supported.size())/ss.size(),med,t.threshold,
                1.-cv::mean(t.valid)[0]/255.,int(path.size()),int(ridgep.size())};
        } else ap2_overflow=true;
        if (supported.size() < 3 || gain < 4) {
            stop = "evidence_ended";
            break;
        }
        int end = supported.back(), gap = 0;
        bool blocked = false;
        for (int j = 1; j <= end; j++) {
            gap = ss[j] < cfg.score ? gap + 1 : 0;
            if (gap > cfg.maxgap) {
                int count = 0;
                for (int k = j + 1; k < (int)ss.size(); k++)
                    count += ss[k] > cfg.score;
                blocked = count >= 4;
                end = std::max(0, j - gap);
                break;
            }
        }
        int take = std::min(end, cfg.advance);
        if (take < 2) {
            stop = blocked ? "gap_unresolved" : "evidence_ended";
            break;
        }
        P n(-d.y, d.x);
        Path extension;
        for (int k = 1; k <= take; k++)
            extension.push_back(o + d * ridgep[k].x + n * (ridgep[k].y - half));
        if (path.size() > 40) {
            double nearest = 1e100;
            for (size_t k = 0; k < path.size() - 30; k++)
                nearest = std::min(nearest, norm(path[k] - extension.back()));
            if (nearest < 4) {
                stop = "loop_guard";
                break;
            }
        }
        if (terminal_validation) for (int k = 1; k <= take; k += 8) {
            int x = rnd(ridgep[k].x), y = rnd(ridgep[k].y), lo = y, hi = y;
            while (lo > std::max(0, y-8) && t.score.at<float>(lo-1,x) > cfg.score) --lo;
            while (hi < std::min(t.score.rows-1, y+8) && t.score.at<float>(hi+1,x) > cfg.score) ++hi;
            path_widths.push_back(hi-lo+1);
        }
        path.insert(path.end(), extension.begin(), extension.end());
        strengths.insert(strengths.end(), ss.begin() + 1, ss.begin() + take + 1);
        for (int k = 0; k <= take; k++)
            peak = std::max(peak, ss[k]);
        P endpoint = current(path.back());
        if (std::min({endpoint.x, endpoint.y, curwidth - 1 - endpoint.x, curheight - 1 - endpoint.y}) < 4) {
            stop = "image_boundary";
            break;
        }
        if (blocked && end <= cfg.advance) {
            stop = "gap_unresolved";
            break;
        }
    }
    if (stop == "evidence_ended") {
        P p = path.back(), e = current(p);
        if (std::min({e.x, e.y, curwidth - 1 - e.x, curheight - 1 - e.y, p.x, p.y, width - 1 - p.x,
                      height - 1 - p.y}) < cfg.maxgap + 4)
            stop = "image_boundary";
        else {
            P d = unit(path.back() - path[path.size() - std::min<size_t>(10, path.size())]);
            Path ahead;
            for (int k = 2; k < 12; k++)
                ahead.push_back(path.back() + d * k);
            auto gray = samples(reference, ahead);
            if (std::count_if(gray.begin(), gray.end(), [](double v) { return v < 100; }) >= 7)
                stop = "material_boundary";
        }
    }
    r.stop = stop;
    r.tip = stop == "evidence_ended";
    r.raw_stop = stop;
    measure(path, strengths, peak, r);
    r.legacy_tip = r.tip;
    if (terminal_validation)
        terminalAudit(path, strengths, path_widths, terminal_tile, terminal_origin,
                      terminal_direction, half, ap != nullptr || isref, isref, r);
    else r.terminal_reason = "disabled";
    if(registration_ambiguous) {
        r.terminal=false;r.shadow_tip=false;
        r.terminal_reason="registration_ambiguous";
    }
    const bool visibility_uncertain=!absolute &&
        (cfg.experiments & CV4_REJECT_ERASED_TERMINAL) && r.texture_erased;
    if(visibility_uncertain) {
        r.terminal=false;r.shadow_tip=false;
        r.terminal_reason="texture_erased_or_uncertain";
    }
    if (!absolute) {
        Observation observation;
        if(!registration_ambiguous) observation.path = std::move(r.history_path);
        observation.endpoint = path.back();
        observation.direction = unit(path.back()-path[path.size()-std::min<size_t>(10,path.size())]);
        observation.terminal_verified = r.terminal && r.path_valid;
        observation.stop = r.raw_stop; observation.frame_index = r.frame_index;
        append(std::move(observation));
    }
    if (policy == CV4_VERIFIED_EXPERIMENTAL && !absolute) {
        r.tip = r.shadow_tip; r.length = r.tip && r.root;
        r.tipxy = r.tip ? r.endpoint : P{};
        r.status = r.length ? "verified_segment_detected" : r.tip ? "tip_only_detected" : "terminal_uncertain";
    }
    if(registration_ambiguous && !absolute) {
        r.tip=false;r.root=false;r.length=false;r.tipxy={};
        r.status="registration_uncertain";r.stop="registration_ambiguous";
        r.basis="registration_uncertain";
    }
    if(visibility_uncertain) {
        // Preserve the currently visible path/root. A flat replacement patch
        // beyond the endpoint is not evidence of a physical crack termination.
        r.tip=false;r.length=false;r.tipxy={};
        r.status="terminal_visibility_uncertain";
        r.basis="current_terminal_not_visible";
    }
    if(!absolute && r.tip && (cfg.experiments & (CV4_LAYERED_AUDIT | CV4_CURRENT_TEXTURE_GUARD))) {
        has_last_confirmed=true;last_confirmed_original=r.tipxy;last_confirmed_frame=r.frame_index;
    }
    if (r.tip && !absolute)
        previous = r.prior;
    r.detector_ms = elapsed(begin);
    return r;
}
// Diagnostic-only thresholds: no changes to V4 DP, scores, root connection or smoothing.
// At most 48 forward samples (3 rays x 16) and bounded cross sections on the final tile.
void Detector::terminalAudit(const Path &path, const std::vector<double> &strengths,
                             const std::vector<double> &widths, const Tile &t,
                             P o, P d, int half, bool anchors_supplied, bool isref, Result &r) {
    PROFILE_SCOPE(15);
    if (path.empty() || strengths.empty()) return;
    int support = 0, run = 0, tail_good = 0;
    size_t tail_begin = strengths.size() > 16 ? strengths.size()-16 : 0;
    std::vector<double> tail;
    for (size_t k = 0; k < strengths.size(); ++k) {
        bool good = strengths[k] >= cfg.score;
        support += good;
        run = good ? 0 : run+1;
        r.longest_gap = std::max(r.longest_gap,run);
        if (k >= tail_begin) { tail.push_back(strengths[k]); tail_good += good; }
    }
    r.path_support = double(support)/strengths.size();
    r.tail_support = double(tail_good)/tail.size();
    r.tail_median = med(tail);
    r.path_width = med(widths);
    for (size_t k = 16; k < path.size(); k += 8) {
        P a=unit(path[k-8]-path[k-16]), b=unit(path[k]-path[k-8]);
        r.bends += dot(a,b) < .5;
    }
    r.path_valid = r.path_support >= .65 && r.longest_gap <= cfg.maxgap &&
                   r.bends <= std::max(1,int(path.size()/100));
    if (t.score.empty()) { r.terminal_reason="no_terminal_tile"; return; }
    P n(-d.y,d.x);
    auto local = [&](P q) { P v=q-o; return P(dot(v,d),dot(v,n)+half); };
    auto inside = [&](P q) { return q.x>=0 && q.y>=0 && q.x<t.score.cols-1 && q.y<t.score.rows-1; };
    auto value = [&](const cv::Mat &m,P q) { return mapcoord(m,q.y,q.x,1,true); };
    P end = local(path.back());
    std::vector<double> tail_widths;
    for (int k=0;k<8;++k) {
        P q=end-P(k,0);
        if (!inside(q)) continue;
        int w=0;
        for (int j=-8;j<=8;++j) {
            P z=q+P(0,j);
            if (inside(z) && value(t.score,z)>=cfg.score) ++w;
        }
        tail_widths.push_back(w);
    }
    r.tail_width=med(tail_widths);
    int valid=0, material=0, continuation=0;
    for (double angle : {-.2617993877991494,0.,.2617993877991494}) {
        int weak_run=0, longest=0;
        for (int k=1;k<=16;++k) {
            P q=end+P(std::cos(angle)*k,std::sin(angle)*k);
            ++r.probe_samples;
            bool ok=inside(q) && value(t.valid,q)>254;
            valid+=ok;
            bool mat=ok && value(t.material,q)>140;
            material+=mat;
            // Ignore the first 3 px: blur around a real endpoint is expected.
            weak_run = k>3 && mat && value(t.score,q)>=cfg.score*.65 ? weak_run+1 : 0;
            longest=std::max(longest,weak_run);
        }
        continuation=std::max(continuation,longest);
    }
    r.terminal_reason = r.raw_stop != "evidence_ended" ? r.raw_stop :
        valid<44 ? "valid_region_boundary" : material<40 ? "material_region_boundary" :
        !anchors_supplied && (r.patches<2 || r.response<.2) ? "registration_uncertain" :
        r.tail_support<.6 || r.tail_median<cfg.score ? "weak_terminal_support" :
        r.tail_width>std::max(8.,r.path_width*3) ? "terminal_width_anomaly" :
        !r.path_valid ? "path_quality_uncertain" :
        continuation>=4 ? "possible_forward_continuation" : "terminal_supported";
    // Evidence-only erasure diagnostic: no comparison with historical length.
    // This detects a nearly constant replacement patch, not arbitrary occlusion.
    if(!t.current_gray.empty()) {
        std::vector<double> refvalues,curvalues;int refclip=0,curclip=0;
        for(int k=8;k<=20;++k) for(int j=-3;j<=3;++j) {
            P q=end+P(k,j);if(!inside(q)||value(t.valid,q)<254)continue;
            double rv=value(t.reference,q),cv=value(t.current_gray,q);
            refvalues.push_back(rv);curvalues.push_back(cv);refclip+=rv>=254;curclip+=cv>=254;
        }
        if(refvalues.size()>=70) {
            auto deviation=[](const std::vector<double> &v) {double s=0,ss=0;for(double x:v){s+=x;ss+=x*x;}return std::sqrt(std::max(0.,ss/v.size()-std::pow(s/v.size(),2)));};
            r.reference_ahead_std=deviation(refvalues);r.current_ahead_std=deviation(curvalues);
            r.reference_ahead_clipped=double(refclip)/refvalues.size();r.current_ahead_clipped=double(curclip)/curvalues.size();
            r.texture_erased=r.reference_ahead_std>.8 && r.current_ahead_std<.05 && r.reference_ahead_clipped<.1;
            if((cfg.experiments & CV4_CURRENT_TEXTURE_GUARD) && r.texture_erased)
                r.terminal_reason="texture_erased_or_uncertain";
        }
    }
    r.terminal = r.terminal_reason == "terminal_supported";
    r.endpoint_hits = r.terminal && r.path_valid ? 1 : 0;
    // Qualified historical ENDPOINT evidence, not mere path-prefix association.
    // Growth is allowed: a prior endpoint may lie on the current trailing path.
    if (r.endpoint_hits) for (const auto &old:history) {
        if (!old.terminal_verified || old.path.empty() || r.frame_index<=old.frame_index ||
            r.frame_index-old.frame_index>=uint64_t(cfg.temporal_window)) continue;
        size_t best=0; double nearest=1e100;
        for (size_t k=0;k<path.size();++k) {
            double distance=norm(path[k]-old.endpoint);
            if (distance<nearest) { nearest=distance; best=k; }
        }
        P direction=unit(path[std::min(path.size()-1,best+5)]-path[best>5 ? best-5:0]);
        if (nearest<std::max(3.,.025*spacing) && dot(direction,old.direction)>.5)
            ++r.endpoint_hits;
    }
    bool strong_terminal = r.tail_median>=4 && r.tail_support>=.75;
    r.shadow_tip = r.terminal && r.path_valid &&
                   (strong_terminal || r.endpoint_hits>=cfg.temporal_hits) && (!isref || r.root);
    if (r.legacy_tip != r.shadow_tip)
        r.divergence = r.legacy_tip ? (r.terminal ? "endpoint_temporal_pending" : r.terminal_reason) :
                                    "shadow_confirmed_legacy_pending";
}
std::string escaped(const std::string &s) {
    std::string b = "\"";
    for (unsigned char c : s) {
        if (c == '"' || c == '\\') {
            b += '\\';
            b += (char)c;
        } else if (c == '\n')
            b += "\\n";
        else if (c == '\r')
            b += "\\r";
        else if (c < 32)
            b += ' ';
        else
            b += (char)c;
    }
    return b + '"';
}
std::string serialize(const Result &r) {
    std::ostringstream s;
    s << std::setprecision(17);
    auto boolean = [](bool v) { return v ? "true" : "false"; };
    auto point = [&](P p) { s << '[' << p.x << ',' << p.y << ']'; };
    auto path = [&](const Path &p) {
        s << '[';
        for (size_t i = 0; i < p.size(); i++) {
            if (i)
                s << ',';
            point(p[i]);
        }
        s << ']';
    };
    s << "{\"status\":" << escaped(r.error.empty() ? r.status : "error")
      << ",\"reference_state\":" << r.reference_state
      << ",\"reference_reason\":" << escaped(r.reference_reason)
      << ",\"temporal_frame_index\":" << r.frame_index
      << ",\"decision_policy\":" << r.policy
      << ",\"terminal_audit\":{\"verified\":" << boolean(r.terminal)
      << ",\"reason\":" << escaped(r.terminal_reason)
      << ",\"legacy_tip\":" << boolean(r.legacy_tip) << ",\"shadow_tip\":" << boolean(r.shadow_tip)
      << ",\"divergence\":" << escaped(r.divergence)
      << ",\"path_valid\":" << boolean(r.path_valid)
      << ",\"path_support\":" << r.path_support << ",\"tail_support\":" << r.tail_support
      << ",\"tail_median_score\":" << r.tail_median
      << ",\"path_width_median_px\":" << r.path_width << ",\"tail_width_median_px\":" << r.tail_width
      << ",\"longest_gap_samples\":" << r.longest_gap << ",\"sharp_bend_count\":" << r.bends
      << ",\"endpoint_hits\":" << r.endpoint_hits << ",\"probe_samples\":" << r.probe_samples << "}"
      << ",\"stop_reason\":" << escaped(r.stop) << ",\"error\":" << escaped(r.error)
      << ",\"tip_confirmed\":" << boolean(r.tip) << ",\"length_confirmed\":" << boolean(r.length)
      << ",\"root_confirmed\":" << boolean(r.root) << ",\"evidence_state\":" << escaped(r.basis)
      << ",\"temporal_hits\":" << r.hits << ",\"shift\":";
    point(r.shift);
    s << ",\"registration_response\":" << r.response << ",\"registration_patch_count\":" << r.patches
      << ",\"detector_ms\":" << r.detector_ms << ",\"api_ms\":" << r.api_ms
      << ",\"transform_reference_to_current\":[[" << r.rotation(0, 0) << ',' << r.rotation(0, 1) << ','
      << r.shift.x << "],[" << r.rotation(1, 0) << ',' << r.rotation(1, 1) << ',' << r.shift.y
      << "]],\"measurement\":";
    if (!r.has)
        s << "null";
    else {
        s << "{\"status\":" << escaped(r.status) << ",\"observed_centerline_length_px\":" << r.visible
          << ",\"estimated_root_to_tip_length_px\":" << r.total << ",\"complete_length_px\":";
        if (r.length)
            s << r.total;
        else
            s << "null";
        s << ",\"extrapolated_root_bridge_length_px\":" << r.bridge << ",\"tip_original_xy\":";
        if (r.tip)
            point(r.tipxy);
        else
            s << "null";
        s << ",\"tracking_endpoint_original_xy\":";
        point(r.endpoint);
        s << ",\"root_original_xy\":";
        point(r.rootxy);
        s << ",\"first_observed_original_xy\":";
        point(r.first);
        s << ",\"root_reference_xy\":";
        point(r.rootref);
        s << ",\"tip_reference_xy\":";
        point(r.tipref);
        s << ",\"interpolated_internal_gap_columns\":" << r.gaps << ",\"tile_count\":" << r.tiles
          << ",\"peak_score\":" << r.peak << ",\"initial_reference_length_px\":" << r.initial
          << ",\"entrance_audit\":{\"method\":" << escaped(r.method)
          << ",\"bridge_limit_px\":12},\"seed_quality\":{\"gain\":" << r.quality.gain
          << ",\"support_fraction\":" << r.quality.support << ",\"median_score\":" << r.quality.median
          << ",\"peak\":" << r.quality.peak << ",\"span_px\":" << r.quality.span
          << ",\"median_width_px\":" << r.quality.width << "}}";
    }
    s << ",\"centerline_original_px\":";
    path(r.path);
    s << ",\"observed_original_px\":";
    path(r.observed);
    s << '}';
    return s.str();
}
void output(const Result &r, CrackV4Result *out, double ratio) {
    if (!out || out->struct_size != sizeof(CrackV4Result))
        throw std::runtime_error("Invalid result struct_size");
    *out = {};
    out->struct_size = sizeof(*out);
    out->tip_confirmed = r.tip;
    out->length_confirmed = r.length;
    out->root_confirmed = r.root;
    out->has_candidate = r.has;
    out->tip = {r.tipxy.x, r.tipxy.y};
    out->length_px = r.length ? r.total : 0;
    out->observed_length_px = r.visible;
    out->length_mm = r.length ? pyround(r.total * ratio, 8) : 0;
    out->detector_ms = r.detector_ms;
    out->api_ms = r.api_ms;
    out->temporal_hits = r.hits;
    out->tile_count = r.tiles;
}
cv::Mat view(const CrackV4Image *im) {
    if (!im || !im->data || im->width <= 0 || im->height <= 0 || im->stride < im->width)
        throw std::runtime_error("Invalid GRAY8 image/stride");
    return cv::Mat(im->height, im->width, CV_8U, const_cast<uint8_t *>(im->data), (size_t)im->stride);
}
std::array<P, 2> points(const CrackV4Point *p) {
    if (!p)
        throw std::runtime_error("Reference points are required");
    return {P(p[0].x, p[0].y), P(p[1].x, p[1].y)};
}
} // namespace

extern "C" {
#ifdef CRACK_V4_PROFILE
__declspec(dllexport) const double* CrackV4ProfileMilliseconds() { return profile_ms.data(); }
#endif
void CrackV4DefaultConfig(CrackV4Config *c) {
    if (c)
        *c = {sizeof(*c), 0, .010753469541668892, 1};
}
int CrackV4Create(const CrackV4Image *reference, const CrackV4Point *rp, const CrackV4Config *c,
                  CrackV4Handle *handle, double *initms, char *error, int capacity) {
    auto begin = Clock::now();
    if (handle)
        *handle = nullptr;
    try {
        if (!handle)
            throw std::runtime_error("Output handle is required");
        Config cfg;
        if (c) {
            if (c->struct_size != sizeof(*c))
                throw std::runtime_error("Invalid config struct_size");
            cfg.mode = c->reference_mode;
            cfg.ratio = c->mm_per_pixel;
            cfg.refine = c->refine_anchor_motion != 0;
        }
        if (cfg.mode < 0 || cfg.mode > 2 || !std::isfinite(cfg.ratio) || cfg.ratio <= 0)
            throw std::runtime_error("Invalid reference mode or calibration ratio");
        auto d = std::make_unique<Detector>(view(reference), points(rp), cfg);
        *handle = d.release();
        if (initms)
            *initms = elapsed(begin);
        if (error && capacity > 0)
            error[0] = 0;
        return 0;
    } catch (const std::exception &e) {
        if (error && capacity > 0) {
            size_t n = std::min(std::strlen(e.what()), static_cast<size_t>(capacity - 1));
            std::memcpy(error, e.what(), n);
            error[n] = 0;
        }
        if (initms)
            *initms = elapsed(begin);
        return -1;
    }
}
int CrackV4Process(CrackV4Handle h, const CrackV4Image *current, const CrackV4Point *cp,
                   CrackV4Result *result) {
    auto begin = Clock::now();
    // Reject output ABI mistakes before processing can advance temporal state.
    if (!result || result->struct_size != sizeof(*result))
        return -1;
    *result = {};
    result->struct_size = sizeof(*result);
    if (!h)
        return -1;
    auto &d = *static_cast<Detector *>(h);
    std::lock_guard<std::mutex> lock(d.mutex);
    try {
        std::array<P, 2> ap;
        if (cp)
            ap = points(cp);
        d.last = d.process(view(current), cp ? &ap : nullptr);
        d.last.api_ms = elapsed(begin);
        output(d.last, result, d.cfg.ratio);
        return 0;
    } catch (const std::exception &e) {
        d.last = {};
        d.last.reference_state = d.reference_state;
        d.last.reference_reason = d.reference_reason;
        d.last.frame_index = d.frame_index;
        d.last.policy = d.policy;
        d.last.terminal_reason = "error";
        d.last.status = "error";
        d.last.stop = "error";
        d.last.raw_stop = "error";
        d.last.error = e.what();
        d.last.api_ms = elapsed(begin);
        d.last.detector_ms = d.last.api_ms;
        try {
            output(d.last, result, d.cfg.ratio);
        } catch (...) {
        }
        return -1;
    }
}
int CrackV4GetBaseline(CrackV4Handle h, CrackV4Result *result) {
    if (!h)
        return -1;
    auto &d = *static_cast<Detector *>(h);
    std::lock_guard<std::mutex> lock(d.mutex);
    try {
        // Pure cached query: no registration, history, last-result or prior updates.
        output(d.reference_result, result, d.cfg.ratio);
        return 0;
    } catch (const std::exception &) {
        return -1;
    }
}
const char *CrackV4LastJson(CrackV4Handle h) {
    if (!h)
        return "{\"error\":\"null handle\"}";
    auto &d = *static_cast<Detector *>(h);
    std::lock_guard<std::mutex> lock(d.mutex);
    d.json = serialize(d.last);
    return d.json.c_str();
}
int CrackV4CopyPath(CrackV4Handle h, int observed, CrackV4Point *out, int cap) {
    if (!h)
        return -1;
    auto &d = *static_cast<Detector *>(h);
    std::lock_guard<std::mutex> lock(d.mutex);
    const Path &p = observed ? d.last.observed : d.last.path;
    if (out && cap > 0)
        for (int i = 0; i < std::min(cap, (int)p.size()); i++)
            out[i] = {p[i].x, p[i].y};
    return (int)p.size();
}
void CrackV4DefaultOptionsV2(CrackV4OptionsV2 *o) {
    if(o) *o={sizeof(*o),2,CV4_SHADOW,1};
}
int CrackV4SetOptionsV2(CrackV4Handle h,const CrackV4OptionsV2 *o) {
    if (!h || !o || o->struct_size!=sizeof(*o) || o->api_version!=2 ||
        o->decision_policy<0 || o->decision_policy>2 || (o->terminal_validation!=0 && o->terminal_validation!=1) ||
        (o->decision_policy==CV4_VERIFIED_EXPERIMENTAL && !o->terminal_validation)) return -1;
    auto &d=*static_cast<Detector*>(h); std::lock_guard<std::mutex> lock(d.mutex);
    if (d.policy!=o->decision_policy || d.terminal_validation!=bool(o->terminal_validation)) {
        d.policy=o->decision_policy; d.terminal_validation=o->terminal_validation!=0; d.resetTemporal();
    }
    return 0;
}
int CrackV4ResetTemporal(CrackV4Handle h) {
    if (!h) return -1;
    auto &d=*static_cast<Detector*>(h); std::lock_guard<std::mutex> lock(d.mutex);
    d.resetTemporal(); return 0;
}
int CrackV4GetResultV2(CrackV4Handle h,CrackV4ResultV2 *out) {
    if (!out || out->struct_size!=sizeof(*out) || out->api_version!=2) return -1;
    *out={}; out->struct_size=sizeof(*out); out->api_version=2;
    if (!h) return -1;
    auto &d=*static_cast<Detector*>(h); std::lock_guard<std::mutex> lock(d.mutex);
    const Result &r=d.last;
    out->frame_index=r.frame_index; out->reference_state=r.reference_state; out->decision_policy=d.policy;
    out->has_candidate=r.has; out->root_confirmed=r.root; out->terminal_verified=r.terminal;
    out->path_quality_valid=r.path_valid; out->tip_confirmed=r.tip; out->complete_length_valid=r.length;
    out->legacy_tip_confirmed=r.legacy_tip; out->shadow_tip_confirmed=r.shadow_tip;
    out->tip_px={r.tipxy.x,r.tipxy.y};
    out->root_px=r.root ? CrackV4Point{r.rootxy.x,r.rootxy.y} : CrackV4Point{};
    out->tracking_endpoint_px={r.endpoint.x,r.endpoint.y};
    out->observed_length_px=r.visible;
    out->root_to_tip_length_px=r.length ? r.total : 0.;
    out->root_bridge_length_px=r.root ? r.bridge : 0.;
    out->path_support_fraction=r.path_support; out->tail_support_fraction=r.tail_support;
    out->tail_median_score=r.tail_median; out->path_width_median_px=r.path_width;
    out->tail_width_median_px=r.tail_width; out->detector_ms=r.detector_ms; out->api_ms=r.api_ms;
    out->longest_gap_samples=r.longest_gap; out->sharp_bend_count=r.bends;
    out->endpoint_temporal_hits=r.endpoint_hits; out->probe_samples=r.probe_samples;
    auto copy=[](char *dest,size_t cap,const std::string &text) {
        size_t n=std::min(cap-1,text.size()); std::memcpy(dest,text.data(),n); dest[n]=0;
    };
    copy(out->terminal_reason,sizeof(out->terminal_reason),r.terminal_reason);
    copy(out->stop_reason,sizeof(out->stop_reason),r.raw_stop);
    copy(out->divergence_reason,sizeof(out->divergence_reason),r.divergence);
    return 0;
}
void CrackV4DefaultExperimentOptions(CrackV4ExperimentOptions *o) {
    if(o) *o={sizeof(*o),1,0,96};
}
int CrackV4CreateExtended(const CrackV4Image *reference,const CrackV4Point *rp,const CrackV4Config *c,
                        const CrackV4ExperimentOptions *o,CrackV4Handle *handle,double *initms,char *error,int capacity) {
    auto begin=Clock::now(); if(handle) *handle=nullptr;
    try {
        if(!handle || !c || c->struct_size!=sizeof(*c) || !o || o->struct_size!=sizeof(*o) || o->api_version!=1 ||
           (o->flags & ~4095u) || ((o->flags & CV4_DIRECTION_POSITIVE) && (o->flags & CV4_DIRECTION_NEGATIVE)) ||
           o->max_debug_images>256 || c->reference_mode<0 || c->reference_mode>2 ||
           !std::isfinite(c->mm_per_pixel) || c->mm_per_pixel<=0) throw std::runtime_error("Invalid extended config");
        Config cfg; cfg.mode=c->reference_mode; cfg.ratio=c->mm_per_pixel; cfg.refine=c->refine_anchor_motion!=0;
        cfg.experiments=o->flags; if(cfg.experiments & CV4_DEBUG_IMAGES) cfg.experiments|=CV4_DIAGNOSTICS;
        cfg.max_debug_images=o->max_debug_images;
        auto d=std::make_unique<Detector>(view(reference),points(rp),cfg); *handle=d.release();
        if(initms) *initms=elapsed(begin); if(error && capacity>0) error[0]=0; return 0;
    } catch(const std::exception &e) {
        if(error && capacity>0) { size_t n=std::min(std::strlen(e.what()),size_t(capacity-1)); std::memcpy(error,e.what(),n); error[n]=0; }
        if(initms) *initms=elapsed(begin); return -1;
    }
}
const char *CrackV4LastDebugJson(CrackV4Handle h) {
    if(!h) return "{}";
    auto &d=*static_cast<Detector*>(h); std::lock_guard<std::mutex> lock(d.mutex);
    std::ostringstream s; s<<std::setprecision(17);
    s<<"{\"enabled\":"<<(d.debug()?"true":"false")<<",\"geometry\":{\"brightness_minus\":"<<d.brightness_minus
     <<",\"brightness_plus\":"<<d.brightness_plus<<",\"direction_ambiguous\":"<<(d.direction_ambiguous?"true":"false")
     <<",\"direction_source\":"<<escaped((d.cfg.experiments & CV4_DIRECTION_EXPERIMENT) && d.direction_ambiguous ? "ordered_anchor_convention":"brightness")
     <<",\"forward\":["<<d.forward.x<<','<<d.forward.y
     <<"],\"normal\":["<<d.normal.x<<','<<d.normal.y<<"],\"origin\":["<<d.origin.x<<','<<d.origin.y
     <<"],\"spacing\":"<<d.spacing<<",\"root\":["<<d.root_reference.x<<','<<d.root_reference.y
     <<"],\"root_exists\":"<<(d.root_exists?"true":"false")<<",\"root_response\":"<<d.root_response
     <<",\"seed_u0\":"<<d.seed_u0<<",\"seed_half\":"<<d.seed_half<<",\"starts_count\":"<<d.starts_count<<"}"
     <<",\"registration\":{\"selected_patches\":"<<d.patches.size()<<",\"inliers\":"<<d.registration_inliers
     <<",\"residual_median\":"<<d.registration_residual<<",\"patches\":[";
    for(size_t i=0;i<d.debug_motion.size();++i) { if(i) s<<','; const auto &p=d.debug_motion[i];
        s<<"{\"rect\":["<<p.rect.x<<','<<p.rect.y<<','<<p.rect.width<<','<<p.rect.height<<"],\"response\":"<<p.response
         <<",\"delta\":["<<p.delta.x<<','<<p.delta.y<<"],\"limit\":"<<p.limit<<",\"accepted\":"<<(p.accepted?"true":"false")
         <<",\"inlier\":"<<(p.inlier?"true":"false")<<",\"residual\":"<<p.residual<<'}'; }
    s<<"],\"recovery_attempted\":"<<(d.recovery_attempted?"true":"false")<<",\"recovery_used\":"<<(d.recovery_used?"true":"false")
     <<",\"anchor_recovery_used\":"<<(d.anchor_recovery_used?"true":"false")<<",\"recovery_patches\":[";
    for(size_t i=0;i<d.recovery_debug.size();++i) {if(i)s<<',';const auto &p=d.recovery_debug[i];
        s<<"{\"delta\":["<<p.delta.x<<','<<p.delta.y<<"],\"correlation\":"<<p.correlation<<",\"margin\":"<<p.margin<<",\"accepted\":"<<(p.accepted?"true":"false")<<'}';}
    s<<"]},\"tiles\":[";
    for(size_t i=0;i<d.debug_tiles.size();++i) { if(i) s<<','; const auto &t=d.debug_tiles[i];
        s<<"{\"origin\":["<<t.origin.x<<','<<t.origin.y<<"],\"direction\":["<<t.direction.x<<','<<t.direction.y
         <<"],\"u0\":"<<t.u0<<",\"half\":"<<t.half<<",\"width\":"<<t.width<<",\"back\":"<<t.back
         <<",\"offset\":"<<t.offset<<",\"median\":"<<t.median<<",\"mad\":"<<t.mad<<",\"noise_tail\":"<<t.noise
         <<",\"threshold\":"<<t.threshold<<",\"invalid_fraction\":"<<t.invalid<<",\"dp\":[";
        for(size_t k=0;k<t.path.size();++k) {if(k) s<<','; s<<'['<<t.path[k].x<<','<<t.path[k].y<<']';} s<<"]}"; }
    s<<"],\"result\":"<<serialize(d.last)<<'}'; d.debug_json=s.str(); return d.debug_json.c_str();
}
const char *CrackV4LastQualityJson(CrackV4Handle h) {
    if(!h)return "{}";
    auto &d=*static_cast<Detector*>(h);std::lock_guard<std::mutex> lock(d.mutex);const auto &r=d.last;
    const bool enabled=(d.cfg.experiments & (CV4_LAYERED_AUDIT|CV4_CURRENT_TEXTURE_GUARD))!=0;
    std::string registration=!r.error.empty()?"invalid_current_registration":d.registration_ambiguous?"ambiguous_current_registration":
        d.last_anchors_supplied?"supported_by_current_anchors":d.anchor_recovery_used?"supported_by_recovered_anchor_pair":d.recovery_used?"supported_by_current_zncc":
        d.registration_inliers>=2 && r.response>=.2 && d.registration_residual<=2?"supported":
        d.registration_inliers==1?"uncertain_single_patch":"uncertain_registration";
    std::string path=!r.has?"not_evaluated":r.path_valid?"supported":"uncertain_path";
    std::string terminal=!r.has?"not_evaluated":r.texture_erased?"uncertain_texture_erasure":
        r.raw_stop!="evidence_ended"?"invalid_terminal_at_stop":r.terminal?"supported":
        r.terminal_reason=="possible_forward_continuation"?"uncertain_forward_response":"uncertain_terminal";
    std::string temporal=r.endpoint_hits>=d.cfg.temporal_hits?"supported_by_endpoint_history":
        r.terminal && r.tail_median>=4 && r.tail_support>=.75?"supported_by_current_strong_tail":"needs_more_evidence";
    std::string authority=!r.error.empty() || (r.has && r.raw_stop!="evidence_ended")?"hard_invalid":
        r.shadow_tip?"verified_experimental":r.terminal && r.path_valid?"needs_more_frames":"uncertain";
    std::ostringstream s;s<<std::setprecision(17);
    s<<"{\"enabled\":"<<(enabled?"true":"false")<<",\"monotonic_length_prior\":false,\"registration_quality\":"<<escaped(registration)
     <<",\"path_quality\":"<<escaped(path)<<",\"terminal_quality\":"<<escaped(terminal)<<",\"temporal_quality\":"<<escaped(temporal)
     <<",\"audit_authority\":"<<escaped(authority)<<",\"legacy_decision_changed\":"<<(r.tip!=r.legacy_tip?"true":"false")
     <<",\"current_tracking_endpoint_px\":";
    if(r.has)s<<'['<<r.endpoint.x<<','<<r.endpoint.y<<']';else s<<"null";
    s<<",\"current_confirmed_tip_px\":";if(r.tip)s<<'['<<r.tipxy.x<<','<<r.tipxy.y<<']';else s<<"null";
    s<<",\"current_detector_frame_index\":"<<r.frame_index<<",\"last_confirmed_tip\":";
    if(enabled && d.has_last_confirmed)s<<"{\"pixel_xy\":["<<d.last_confirmed_original.x<<','<<d.last_confirmed_original.y<<"],\"detector_frame_index\":"<<d.last_confirmed_frame<<'}';else s<<"null";
    s<<",\"photometric_ahead\":{\"reference_std\":"<<r.reference_ahead_std<<",\"current_std\":"<<r.current_ahead_std
     <<",\"reference_clipped_fraction\":"<<r.reference_ahead_clipped<<",\"current_clipped_fraction\":"<<r.current_ahead_clipped
     <<",\"texture_erased\":"<<(r.texture_erased?"true":"false")<<"}}";
    d.quality_json=s.str();return d.quality_json.c_str();
}
const char *CrackV4LastGeometryJson(CrackV4Handle h) {
    if(!h)return "{}";
    auto &d=*static_cast<Detector*>(h);std::lock_guard<std::mutex> lock(d.mutex);
    const auto &r=d.last;
    std::ostringstream s;
    s<<"{\"registration_state\":"<<escaped(!r.error.empty()?"REGISTRATION_FAILED":d.registration_ambiguous?"REGISTRATION_AMBIGUOUS":"REGISTRATION_VALID")
     <<",\"current_anchor_valid\":"<<(d.current_anchor_valid?"true":"false")
     <<",\"current_anchor_supplied\":"<<(d.last_anchors_supplied?"true":"false")
     <<",\"automatic_success_reviewed\":"<<(d.automatic_success_reviewed?"true":"false")
     <<",\"automatic_success_repaired\":"<<(d.automatic_success_repaired?"true":"false")
     <<",\"fallback_attempted\":"<<(d.recovery_attempted?"true":"false")
     <<",\"fallback_used\":"<<(d.recovery_used?"true":"false")
     <<",\"anchor_motion_refinement\":"<<(d.cfg.refine?"true":"false")
     <<",\"direction_mode\":"<<escaped(d.cfg.experiments & CV4_DIRECTION_POSITIVE?"AnchorPositive":d.cfg.experiments & CV4_DIRECTION_NEGATIVE?"AnchorNegative":"Auto")<<'}';
    d.geometry_json=s.str();return d.geometry_json.c_str();
}
int CrackV4GetDebugImage(CrackV4Handle h,int index,float *data,int cap,int *width,int *height,char *name,int namecap) {
    if(!h || index<0) return -1;
    auto &d=*static_cast<Detector*>(h); std::lock_guard<std::mutex> lock(d.mutex);
    if(index>=int(d.debug_images.size())) return -1;
    const auto &image=d.debug_images[index]; const cv::Mat &m=image.second;
    if(width) *width=m.cols; if(height) *height=m.rows;
    if(name && namecap>0) { size_t n=std::min(image.first.size(),size_t(namecap-1)); std::memcpy(name,image.first.data(),n); name[n]=0; }
    int n=int(m.total()); if(data && cap>=n) std::memcpy(data,m.ptr<float>(),size_t(n)*sizeof(float));
    return n;
}
void CrackV4Destroy(CrackV4Handle h) {
    delete static_cast<Detector *>(h);
}
const char *CrackV4BuildInfo() {
    return "Native C++17 V4 reliability revision 2026-10-28; pixel V2; default shadow; OpenCV " CV_VERSION "; no Python runtime or inference model";
}
void CrackV4SetNumThreads(int threads) {
    cv::setNumThreads(threads);
}
}

// Research-only export; production ABI/source unchanged. Flat rows, 11 doubles.
extern "C" __declspec(dllexport) int AP2CopyStops(CrackV4Handle h, double* out, int capacity) {
    if(!h) return -1;
    auto &d=*static_cast<Detector*>(h); std::lock_guard<std::mutex> lock(d.mutex);
    if(!out) return d.ap2_count;
    int n=std::min(capacity,d.ap2_count);
    for(int i=0;i<n;++i) { auto &v=d.ap2_stops[i]; double *p=out+11*i;
        p[0]=v.x;p[1]=v.y;p[2]=v.dx;p[3]=v.dy;p[4]=v.gain;p[5]=v.support;
        p[6]=v.median;p[7]=v.threshold;p[8]=v.invalid;p[9]=v.path_size;p[10]=v.dp_size; }
    return d.ap2_overflow?-n-1:n;
}

extern "C" __declspec(dllexport) int AP3CopySeed(CrackV4Handle h,double* out,int capacity) {
 if(!h || !out || capacity<9) return -1;
 auto &d=*static_cast<Detector*>(h); std::lock_guard<std::mutex> lock(d.mutex);
 std::copy(d.ap3_seed.begin(),d.ap3_seed.end(),out); return 9;
}
