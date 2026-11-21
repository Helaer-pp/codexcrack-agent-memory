#include "internal.hpp"
#include <filesystem>
#include <fstream>
#include <iterator>
#include <cstdlib>
namespace v512 {
static void require(bool ok,const char* message){if(!ok)throw std::invalid_argument(message);}
Rect boxOf(const Bounds &p, cv::Size size) {
    require(p.left >= 0 && p.top >= 0 && p.right <= size.width && p.bottom <= size.height && p.right >= p.left &&
                p.bottom >= p.top && p.right - p.left >= 50 && p.bottom - p.top >= 32,
            "Invalid material box.");
    return {p.left, p.top, p.right - p.left, p.bottom - p.top};
}
void material(const MaterialPolicy &cfg,const Mat &reference, const Mat &cur, Rect upstream, Pair &rp, Pair &cp, Rect &box) {
    Rect fixed = boxOf(cfg.band, cur.size()), request = boxOf(cfg.request, cur.size());
    Point2d d0 = cp[0] - rp[0], d1 = cp[1] - rp[1];
    int dx = rnd((d0.x + d1.x) / 2), dy0 = rnd(d0.y), dy1 = rnd(d1.y);
    auto moved = [&](Rect r) { return Rect(r.x + dx, r.y + dy0, r.width, r.height + dy1 - dy0); };
    box = upstream & fixed & moved(fixed);
    require(box.width >= 50 && box.height >= 32, "Material window outside acquisition area.");
    if (cfg.mode == 1)
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
    Mat rf = safe(reference, cfg.floor), cf = safe(cur, floor);
    for (int i = 0; i < 2; ++i) {
        Point d(rnd(cp[i].x - rp[i].x), rnd(cp[i].y - rp[i].y)), pick;
        double best = INFINITY;
        Point2d target(cfg.targets[i].x, cfg.targets[i].y);
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

std::optional<MaterialPolicy> loadMaterialPolicy(cv::Size size) {
    const wchar_t* file=_wgetenv(L"CRACKV4_V512_MATERIAL_POLICY");
    if(!file||!*file)return {};
    std::ifstream in(std::filesystem::path(file),std::ios::binary);
    require(in.good(),"Cannot open material policy");
    std::string bytes((std::istreambuf_iterator<char>(in)),std::istreambuf_iterator<char>());
    cv::FileStorage doc(bytes,cv::FileStorage::READ|cv::FileStorage::MEMORY|cv::FileStorage::FORMAT_JSON);
    require(doc.isOpened(),"Invalid material policy");
    auto bounds=[&](const char* key){
        auto node=doc[key];require(node.isSeq()&&node.size()==4,"Invalid material box");
        Bounds v{int(node[0]),int(node[1]),int(node[2]),int(node[3])};boxOf(v,size);return v;
    };
    MaterialPolicy cfg{};
    cfg.request=bounds("reference_box");cfg.band=bounds("fixed_band");
    auto floor=doc["fixed_floor"];require(floor.isReal()||floor.isInt(),"Missing brightness floor");
    cfg.floor=double(floor);require(cfg.floor>=0 && cfg.floor<=255,"Invalid brightness floor");
    cfg.mode=doc["material_mode"].empty()?2:int(doc["material_mode"]);
    require(cfg.mode==1||cfg.mode==2,"Unknown material mode");
    auto points=doc["reference_virtual_points"];require(points.isSeq()&&points.size()==2,"Missing virtual points");
    for(int i=0;i<2;++i){
        auto p=points[i];require(p.isSeq()&&p.size()==2,"Invalid virtual point");
        cfg.targets[i]={double(p[0]),double(p[1])};
        require(cfg.targets[i].x>=0 && cfg.targets[i].y>=0 && cfg.targets[i].x<size.width && cfg.targets[i].y<size.height,"Virtual point outside frame");
    }
    return cfg;
}
} // namespace v512
