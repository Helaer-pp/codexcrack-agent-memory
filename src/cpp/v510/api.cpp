#include "CrackV510.h"
#include "internal.hpp"
#include <chrono>
#include <memory>
#include <string>
namespace {
using namespace v510;
thread_local std::string lastError;
struct Handle {
    Mat reference;
    Pair pair;
    Crack510Config config;
    Crack510Result baseline{};
    Path last;
};
void require(bool cond, const char *msg) {
    if (!cond)
        throw std::invalid_argument(msg);
}
Mat image(const Crack510Image *im) {
    require(im && im->data && im->width >= 20 && im->height >= 20 && im->width < 32767 && im->height < 32767 &&
                im->stride >= im->width && im->stride <= INT64_MAX / im->height,
            "Expected GRAY8 image, positive stride and dimensions in [20,32766].");
    return Mat(im->height, im->width, CV_8U, const_cast<uint8_t *>(im->data), size_t(im->stride));
}
Pair pairOf(const Crack510Point *p, cv::Size size) {
    require(p, "Two measured anchors are required.");
    Pair a;
    for (int i = 0; i < 2; ++i) {
        a[i] = {p[i].x, p[i].y};
        require(a[i].x >= 0 && a[i].x < size.width && a[i].y >= 0 && a[i].y < size.height, "Anchor outside image.");
    }
    require(a[1].y > a[0].y && cv::norm(a[1] - a[0]) >= 20, "P1 must be above P2; minimum distance is 20 pixels.");
    return a;
}
Rect boxOf(Crack510Box p, cv::Size size) {
    require(p.left >= 0 && p.top >= 0 && p.right <= size.width && p.bottom <= size.height && p.right >= p.left &&
                p.bottom >= p.top && p.right - p.left >= 50 && p.bottom - p.top >= 32,
            "Invalid material box.");
    return {p.left, p.top, p.right - p.left, p.bottom - p.top};
}
void material(const Handle &h, const Mat &cur, Rect upstream, Pair &rp, Pair &cp, Rect &box) {
    Rect fixed = boxOf(h.config.fixed_band, cur.size()), request = boxOf(h.config.reference_box, cur.size());
    Point2d d0 = cp[0] - rp[0], d1 = cp[1] - rp[1];
    int dx = rnd((d0.x + d1.x) / 2), dy0 = rnd(d0.y), dy1 = rnd(d1.y);
    auto moved = [&](Rect r) { return Rect(r.x + dx, r.y + dy0, r.width, r.height + dy1 - dy0); };
    box = upstream & fixed & moved(fixed);
    require(box.width >= 50 && box.height >= 32, "Material window outside acquisition area.");
    if (h.config.material_mode == 1)
        return;
    Rect r = moved(request) & upstream;
    require(r.width >= 50 && r.height >= 32, "Brightness sampling window outside acquisition area.");
    int margin = std::max(8, r.height / 3);
    Rect slab = Rect(r.x, r.y - margin, r.width, r.height + 2 * margin) & upstream;
    slab.x += r.width / 8;
    slab.width -= r.width / 8;
    Mat test = cur(slab), binary;
    double otsu = cv::threshold(test, binary, 0, 255, cv::THRESH_BINARY | cv::THRESH_OTSU);
    double floor = otsu + .35 * (quant(sample(test), .85) - otsu);
    auto safe = [&](const Mat &im, double threshold) {
        Mat m = f32(im(box)) >= threshold, out;
        cv::erode(m, out, kernel(9, 9), {-1, -1}, 1, cv::BORDER_CONSTANT, 0);
        return out;
    };
    Mat rf = safe(h.reference, h.config.fixed_floor), cf = safe(cur, floor);
    for (int i = 0; i < 2; ++i) {
        Point d(rnd(cp[i].x - rp[i].x), rnd(cp[i].y - rp[i].y)), pick;
        double best = INFINITY;
        Point2d target(h.config.virtual_points[i].x, h.config.virtual_points[i].y);
        for (int y = 0; y < box.height; ++y) {
            if (i ? y <= box.height / 2 + 4 : y >= box.height / 2 - 4)
                continue;
            for (int x = 0; x < box.width; ++x) {
                Point a(x, y), b = a + d;
                if (!Rect({}, box.size()).contains(b) || !rf.at<uchar>(a) || !cf.at<uchar>(b))
                    continue;
                Point2d off = Point2d(a + box.tl()) - target;
                double dist = off.dot(off);
                if (dist < best) {
                    best = dist;
                    pick = a + box.tl();
                }
            }
        }
        require(std::isfinite(best), "No paired bright anchor patch.");
        rp[i] = pick;
        cp[i] = pick + d;
    }
}
Crack510Result process(Handle &h, const Mat &cur, Pair pair) {
    auto start = std::chrono::steady_clock::now();
    require(cur.size() == h.reference.size(), "Frame size differs from reference.");
    Rect upstream = sceneBounds(cur.size(), pair), box = upstream;
    Pair rp = h.pair, cp = pair;
    require(box.width >= 20 && box.height >= 20, "Empty acquisition area.");
    if (h.config.material_mode)
        material(h, cur, upstream, rp, cp, box);
    Mat aligned;
    if (!h.config.raw_only) {
        Mat field = registerFrame(h.reference, cur, h.pair, pair, upstream);
        aligned = field(Rect(box.tl() - upstream.tl(), box.size()));
    }
    auto found = detect(cur(box), h.reference(box), aligned, midpoint(cp) - Point2d(box.tl()),
                        midpoint(rp) - Point2d(box.tl()));
    Crack510Result out{};
    out.struct_size = sizeof(out);
    out.status = found.notch ? CR510_NO_TIP : CR510_NO_NOTCH;
    out.root = out.tip = {NAN, NAN};
    out.projected_length_px = out.path_length_px = NAN;
    for (int i = 0; i < 2; ++i) {
        out.actual_current[i] = {cp[i].x, cp[i].y};
        out.actual_reference[i] = {rp[i].x, rp[i].y};
    }
    if (!found.path.empty()) {
        for (auto &p : found.path)
            p += box.tl();
        auto root = found.path.front(), tip = found.path.back();
        out.status = CR510_VALID;
        out.root = {double(root.x), double(root.y)};
        out.tip = {double(tip.x), double(tip.y)};
        out.path_points = int(found.path.size());
        out.bridge_columns = found.bridge;
        out.path_length_px = 0;
        for (size_t i = 1; i < found.path.size(); ++i)
            out.path_length_px += cv::norm(found.path[i] - found.path[i - 1]);
        auto v = cp[1] - cp[0];
        out.projected_length_px = (Point2d(tip) - midpoint(cp)).dot(Point2d(v.y, -v.x)) / cv::norm(v);
    }
    out.path_length_mm = h.config.mm_per_pixel > 0 ? out.path_length_px * h.config.mm_per_pixel : NAN;
    out.detector_ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - start).count();
    h.last = std::move(found.path);
    return out;
}
template <class Fn> int call(Fn fn) {
    try {
        lastError.clear();
        fn();
        return 0;
    } catch (const std::exception &e) {
        lastError = e.what();
        return -1;
    } catch (...) {
        lastError = "Unknown native error.";
        return -1;
    }
}
} // namespace
extern "C" {
void Crack510DefaultConfig(Crack510Config *c) {
    if (c) {
        *c = {};
        c->struct_size = sizeof(*c);
    }
}
int Crack510Create(const Crack510Image *im, const Crack510Point *pts, const Crack510Config *config,
                   Crack510Handle *output) {
    return call([&] {
        require(output, "Missing handle output.");
        *output = nullptr;
        auto h = std::make_unique<Handle>();
        Mat ref = image(im);
        h->pair = pairOf(pts, ref.size());
        Crack510DefaultConfig(&h->config);
        if (config) {
            require(config->struct_size == sizeof(*config) && std::isfinite(config->mm_per_pixel) &&
                        config->mm_per_pixel >= 0 && config->material_mode >= 0 && config->material_mode <= 2 &&
                        (config->raw_only == 0 || config->raw_only == 1),
                    "Unsupported config.");
            h->config = *config;
        }
        if (h->config.material_mode == 2) {
            pairOf(h->config.virtual_points, ref.size());
            require(h->config.fixed_floor >= 0 && h->config.fixed_floor <= 255,
                    "Invalid reference brightness floor.");
        }
        h->reference = ref.clone();
        h->baseline = process(*h, h->reference, h->pair);
        *output = h.release();
    });
}
int Crack510Process(Crack510Handle handle, const Crack510Image *im, const Crack510Point *pts, Crack510Result *out) {
    return call([&] {
        require(handle && out && out->struct_size == sizeof(*out), "Invalid handle or result size.");
        auto cur = image(im);
        *out = process(*static_cast<Handle *>(handle), cur, pairOf(pts, cur.size()));
    });
}
int Crack510GetBaseline(Crack510Handle h, Crack510Result *out) {
    return call([&] {
        require(h && out && out->struct_size == sizeof(*out), "Invalid handle or result size.");
        *out = static_cast<Handle *>(h)->baseline;
    });
}
int Crack510CopyPath(Crack510Handle h, Crack510Point *out, int capacity) {
    if (!h || capacity < 0)
        return -1;
    auto &p = static_cast<Handle *>(h)->last;
    if (!out)
        return int(p.size());
    if (size_t(capacity) < p.size())
        return -1;
    for (size_t i = 0; i < p.size(); ++i)
        out[i] = {double(p[i].x), double(p[i].y)};
    return int(p.size());
}
const char *Crack510LastError() { return lastError.c_str(); }
void Crack510Destroy(Crack510Handle h) { delete static_cast<Handle *>(h); }
void Crack510SetNumThreads(int n) {
    if (n > 0)
        cv::setNumThreads(n);
}
}
