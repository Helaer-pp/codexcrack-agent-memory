#include "v2_detector.hpp"
#include "GrayRefV2.h"
namespace {
cv::Mat1b image(const GrayRefV2Image*i){if(!i||!i->data||i->width<1||i->height<1||i->stride<i->width)throw std::runtime_error("Invalid image");return cv::Mat1b(i->height,i->width,const_cast<unsigned char*>(i->data),size_t(i->stride));}
std::array<v2::P,2> points(const GrayRefV2Point*p){if(!p)throw std::runtime_error("Missing points");return {v2::P(p[0].x,p[0].y),v2::P(p[1].x,p[1].y)};}
}
extern "C" {
void* GrayRefV2Create(const GrayRefV2Image*ref,const GrayRefV2Point*rp){try{cv::setNumThreads(1);auto d=new v2::Detector;auto p=points(rp);d->base.initializeReference(image(ref),p[0],p[1]);return d;}catch(...){return nullptr;}}
int GrayRefV2Process(void*h,const GrayRefV2Image*c,const GrayRefV2Point*cp){if(!h)return -1;try{static_cast<v2::Detector*>(h)->process(image(c),points(cp));return 0;}catch(...){return -2;}}
const char* GrayRefV2Read(void*h){return h?static_cast<v2::Detector*>(h)->json.c_str():"{}";}
const float* GrayRefV2Array(void*h,int id,int*w,int*height){if(!h||id<0||id>=8)return nullptr;auto&a=static_cast<v2::Detector*>(h)->base.arrays[id];*w=a.cols;*height=a.rows;return a.empty()?nullptr:a.ptr<float>();}
void GrayRefV2Destroy(void*h){delete static_cast<v2::Detector*>(h);}
int GrayRefV2NumericSelfTest(){for(long long n=-10000;n<=10000;++n){auto expected=n>=0?static_cast<long long>(std::floor(n/1024.+.5)):-static_cast<long long>(std::floor(-n/1024.+.5));if(v2::divround(n,1024)!=expected)return 1;}std::vector<cv::Point> p;for(int i=0;i<12;++i)p.emplace_back(i,100);if(v2::prediction(p,12,0)!=102400)return 2;for(auto&v:p)v.y=100+v.x;if(v2::prediction(p,12,0)!=111*1024+v2::divround(1024,5))return 3;for(double eps:{-1e-10,0.,1e-10})if(v2::quant(19+eps)!=19000000)return 4;return 0;}
}
