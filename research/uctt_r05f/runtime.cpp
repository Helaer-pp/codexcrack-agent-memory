#include "current.hpp"
#include "CrackV4.h"
namespace {
cv::Mat1b viewF(const CrackV4Image*i){if(!i||!i->data||i->width<16||i->height<16||i->stride<i->width)throw std::runtime_error("invalid image");return cv::Mat1b(i->height,i->width,const_cast<unsigned char*>(i->data),size_t(i->stride));}
std::array<r05f::P,2> ptsF(const CrackV4Point*p){if(!p)throw std::runtime_error("missing anchors");return {r05f::P(p[0].x,p[0].y),r05f::P(p[1].x,p[1].y)};}
std::string describe(r05f::Detector&d){auto&f=d.last;std::ostringstream o;o<<std::setprecision(17);auto point=[&](r05f::P p){o<<'['<<p.x<<','<<p.y<<']';};
 o<<"{\"frame\":"<<f.frame<<",\"mode\":"<<f.mode<<",\"origin\":";point(f.origin);o<<",\"forward\":";point(f.forward);o<<",\"spacing\":"<<f.spacing<<",\"valid_anchors\":"<<f.validAnchors<<",\"search_incomplete\":"<<f.searchIncomplete<<",\"reason\":\""<<f.reason<<"\",\"state\":\""<<f.state<<"\",\"observed\":false,\"output_tip\":null,\"trusted_history_written\":false,\"trusted_path_size\":"<<d.trustedPath.size()<<",\"raw_segments\":"<<f.rawSegments<<",\"raw_candidates\":"<<f.rawCandidates<<",\"retained_candidates\":"<<f.retainedCandidates<<",\"window_pixels_sum\":"<<f.totalPixels<<",\"unique_source_pixels\":"<<f.uniquePixels<<",\"current_ms\":"<<f.currentMs<<",\"api_ms\":"<<f.apiMs<<",\"reference_calls\":0,\"windows\":[";
 for(size_t i=0;i<f.windows.size();++i){if(i)o<<',';auto&w=f.windows[i];o<<"{\"id\":"<<w.id<<",\"parent_segment\":"<<w.parent<<",\"seed\":"<<w.seed<<",\"center\":";point(w.center);o<<",\"direction\":";point(w.forward);o<<",\"size\":["<<w.w<<','<<w.h<<"],\"polygon\":[";for(size_t j=0;j<w.polygon.size();++j){if(j)o<<',';point(w.polygon[j]);}o<<"],\"source\":\""<<w.source<<"\",\"segments\":"<<w.segments<<",\"candidates\":"<<w.candidates<<",\"source_pixels\":"<<w.localPixels<<",\"new_source_pixels\":"<<w.newPixels<<",\"current_ms\":"<<w.currentMs<<",\"clipped\":"<<w.clipped<<'}';}
 o<<"],\"segments\":[";
 for(size_t i=0;i<f.segments.size();++i){if(i)o<<',';auto&s=f.segments[i];o<<"{\"id\":"<<s.id<<",\"window\":"<<s.window<<",\"seed\":"<<s.seed<<",\"parent\":"<<s.parent<<",\"start\":";point(s.start);o<<",\"end\":";point(s.end);o<<",\"tangent\":";point(s.tangent);o<<",\"current_support\":"<<s.support<<",\"width_scale\":"<<s.width<<",\"length\":"<<s.length<<",\"window_cut\":"<<s.cut<<",\"polarity\":\"dark\",\"reference_state\":\""<<s.refState<<"\",\"attribution\":\""<<s.association<<"\",\"points\":[";if(d.capture)for(size_t j=0;j<s.points.size();++j){if(j)o<<',';point(s.points[j]);}o<<"]}";}
 o<<"],\"candidates\":[";
 for(size_t i=0;i<f.candidates.size();++i){if(i)o<<',';auto&c=f.candidates[i];o<<"{\"id\":"<<c.id<<",\"segment\":"<<c.segment<<",\"window\":"<<c.window<<",\"canonical_id\":"<<c.canonical<<",\"xy\":";point(c.p);o<<",\"current_support\":"<<c.support<<",\"width\":"<<c.width<<",\"source\":\""<<c.source<<"\",\"window_cut\":"<<c.windowCut<<",\"terminal_supported\":false}";}
 o<<"]}";return o.str();}
}
extern "C" {
__declspec(dllexport) void* R05FCreate(const CrackV4Image*ref,const CrackV4Point*pp,int mode){try{auto im=viewF(ref);auto p=ptsF(pp);if(!r05f::inside(p[0],im.size())||!r05f::inside(p[1],im.size())||p[0].y>=p[1].y||cv::norm(p[1]-p[0])<16||mode!=0)return nullptr;cv::setNumThreads(4);return new r05f::Detector(im,p,mode);}catch(...){return nullptr;}}
__declspec(dllexport) int R05FProcess(void*h,const CrackV4Image*im,const CrackV4Point*pp){try{if(!h)return -1;static_cast<r05f::Detector*>(h)->process(viewF(im),ptsF(pp));return 0;}catch(...){if(h){auto&d=*static_cast<r05f::Detector*>(h);d.last={};d.last.validAnchors=false;d.last.searchIncomplete=true;d.last.reason="invalid_api_input";}return -2;}}
__declspec(dllexport) void R05FCapture(void*h,int enabled){if(h)static_cast<r05f::Detector*>(h)->capture=enabled!=0;}
__declspec(dllexport) const char* R05FRead(void*h){if(!h)return "{}";auto&d=*static_cast<r05f::Detector*>(h);d.json=describe(d);return d.json.c_str();}
__declspec(dllexport) void R05FDestroy(void*h){delete static_cast<r05f::Detector*>(h);}
}
