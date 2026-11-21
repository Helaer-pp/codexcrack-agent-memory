#pragma once
#include "../v510/internal.hpp"
namespace v512 {
using namespace v510;
struct Bounds { int left,top,right,bottom; };
struct MaterialPolicy { Bounds request,band; double floor; int mode; Pair targets; };
std::optional<MaterialPolicy> loadMaterialPolicy(cv::Size);
void material(const MaterialPolicy&,const Mat&,const Mat&,Rect,Pair&,Pair&,Rect&);
struct Evidence : v510::Field { Mat dual; };
Evidence makeEvidence(const Scene &, const Mat &);
Found detect512(const Mat &, const Mat &, const Mat &, Point2d, Point2d);
}
