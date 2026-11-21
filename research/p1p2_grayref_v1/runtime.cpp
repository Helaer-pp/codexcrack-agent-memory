#include "detector.hpp"
#include "CrackV4.h"
using namespace grayref;
namespace {
cv::Mat1b view(const CrackV4Image*i){if(!i||!i->data||i->width<1||i->height<1||i->stride<i->width)throw std::runtime_error("Invalid image");return cv::Mat1b(i->height,i->width,const_cast<unsigned char*>(i->data),size_t(i->stride));}
std::array<P,2> points(const CrackV4Point*p){if(!p)throw std::runtime_error("Missing points");return {P(p[0].x,p[0].y),P(p[1].x,p[1].y)};}
void point(std::ostream&o,P p){if(!std::isfinite(p.x)||!std::isfinite(p.y)){o<<"null";return;}o<<'['<<p.x<<','<<p.y<<']';}
std::string describe(const Result&r){std::ostringstream o;o<<std::setprecision(17)<<std::boolalpha;o<<"{\"status\":\""<<r.status<<"\",\"error\":\""<<r.error<<"\",\"point_source\":\""<<r.pointSource<<"\",\"points\":[";point(o,r.points[0]);o<<',';point(o,r.points[1]);o<<"],\"ncc\":["<<r.ncc[0]<<','<<r.ncc[1]<<"],\"ROI\":{\"x_left\":"<<r.xleft<<",\"x_right\":"<<r.xright<<",\"y_top\":"<<r.upper<<",\"y_bottom\":"<<r.lower<<"},\"crop\":["<<r.xa<<','<<r.ya<<','<<r.xb<<','<<r.yb<<"],\"runtime\":{\"native_ms\":"<<r.totalMs<<",\"point_ms\":"<<r.pointMs<<",\"preprocess_ms\":"<<r.preprocessMs<<",\"track_ms\":"<<r.trackMs<<"},\"traces\":[";
 for(size_t i=0;i<r.traces.size();++i){if(i)o<<',';auto&t=r.traces[i];o<<"{\"mode\":\""<<t.mode<<"\",\"threshold\":"<<t.threshold<<",\"tip\":";if(t.hasTip)point(o,t.tip);else o<<"null";o<<",\"observed_points\":"<<t.observations.size()<<",\"candidate_count\":"<<t.candidateCount<<",\"stop_reason\":\""<<(t.hasTip?"gap_limit":"no_observed_point")<<"\",\"trace\":[";
  for(size_t j=0;j<t.rows.size();++j){if(j)o<<',';auto&v=t.rows[j];o<<'['<<v.x<<','<<v.y<<','<<v.contrast<<','<<v.delta<<','<<v.strength<<','<<v.visible<<','<<v.gap<<','<<v.predicted<<']';}o<<"]}";
 }o<<"]}";return o.str();}
}
extern "C" {
__declspec(dllexport) void* GrayRefCreate(const CrackV4Image*ref,const CrackV4Point*pp){try{cv::setNumThreads(4);auto d=new P1P2GrayRefV1;auto p=points(pp);d->initializeReference(view(ref),p[0],p[1]);return d;}catch(...){return nullptr;}}
__declspec(dllexport) int GrayRefProcess(void*h,const CrackV4Image*im,const CrackV4Point*pp){try{if(!h)return -1;auto*d=static_cast<P1P2GrayRefV1*>(h);if(pp){auto p=points(pp);d->process(view(im),&p);}else d->process(view(im));return 0;}catch(...){return -2;}}
__declspec(dllexport) const char* GrayRefRead(void*h){if(!h)return "{}";auto*d=static_cast<P1P2GrayRefV1*>(h);d->json=describe(d->result);return d->json.c_str();}
__declspec(dllexport) const float* GrayRefArray(void*h,int id,int*width,int*height){if(!h||id<0||id>=8)return nullptr;auto&a=static_cast<P1P2GrayRefV1*>(h)->arrays[id];*width=a.cols;*height=a.rows;return a.empty()?nullptr:a.ptr<float>();}
__declspec(dllexport) void GrayRefDestroy(void*h){delete static_cast<P1P2GrayRefV1*>(h);}
}
