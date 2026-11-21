#pragma once
#include "../v512/internal.hpp"
namespace v63 {
using namespace v510;
inline thread_local double scale = 288.;
inline int px(double f) { return std::max(1, rnd(f * scale)); }
struct Scene : v510::Scene {
    bool quiet;
    int minStart, maxStart;
    double middle;
};
struct Window {
    int x0, x1, mid;
    Point up, down;
    bool mapped, lowWhite;
};
struct Mapping {
    Mat tile;
    Rect box;
    std::vector<Window> windows;
    Point2d offset;
    Point2d referencePoint(Point2d p) const;
};
struct Evidence : v510::Field {
    Mat dual, originalDip;
};
struct Detection {
    std::vector<Point2d> path;
    bool notch = false;
    Mapping mapping;
};
std::optional<Scene> prepareScene(const Mat &, const Mat &, Point2d, Point2d);
Mapping mapReference(const Mat &, const Mat &, Rect, Point2d, const Scene &, int);
Evidence makeEvidence(const Scene &, const Mat &);
Detection detect(const Mat &, const Mat &, Rect, const Pair &, const Pair &);
} // namespace v63
