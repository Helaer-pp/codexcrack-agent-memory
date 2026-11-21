// Experimental translation unit. Production source is included unchanged.
#include "../../src/cpp/a/CrackV4.cpp"
#include "state.hpp"
struct R03Sidecar {r03::State state;std::string json;std::mutex mutex;};
extern "C" {
__declspec(dllexport) void* R03CreateState(){return new R03Sidecar;}
__declspec(dllexport) void R03DestroyState(void *p){delete static_cast<R03Sidecar*>(p);}
__declspec(dllexport) const char* R03Observe(CrackV4Handle h,void *p,int reference_frame){
 if(!h||!p)return "{}";
 auto &d=*static_cast<Detector*>(h);auto &s=*static_cast<R03Sidecar*>(p);
 std::scoped_lock lock(d.mutex,s.mutex);auto start=Clock::now();
 const auto &r=reference_frame?d.reference_result:d.last;
 r03::Evidence e;e.size={d.curwidth,d.curheight};e.search=d.tip_roi;e.tip=r.tipxy;e.path=r.observed;
 e.candidate=r.tip;e.terminal=r.terminal;e.path_valid=r.path_valid;
 e.motion=reference_frame||d.tip_registration_valid;
 e.rotation=reference_frame?cv::Matx22d::eye():d.tip_rotation;e.translation=reference_frame?P():d.tip_translation;
 e.direction=reference_frame?d.forward:d.tipDirection();
 auto z=s.state.step(e);double state_ms=elapsed(start);
 auto boolean=[](bool v){return v?"true":"false";};
 std::ostringstream o;o<<std::setprecision(17);
 auto point=[&](P q){o<<'['<<q.x<<','<<q.y<<']';};
 auto rect=[&](cv::Rect q){o<<'['<<q.x<<','<<q.y<<','<<q.width<<','<<q.height<<']';};
 o<<"{\"state_before\":"<<escaped(z.before)<<",\"state_after\":"<<escaped(z.after)<<",\"source\":"<<escaped(z.source)<<",\"transition_reason\":"<<escaped(z.reason);
 o<<",\"valid\":"<<boolean(z.valid)<<",\"visual_confirmed\":"<<boolean(z.accepted)<<",\"lock_attempted\":"<<boolean(z.attempted)<<",\"lock_accepted\":"<<boolean(z.accepted)<<",\"history_written\":"<<boolean(z.history_written)<<",\"roi_edge_risk\":"<<boolean(z.edge)<<",\"track_clipped\":"<<boolean(z.clipped);
 o<<",\"search_roi\":";rect(e.search);o<<",\"track_roi\":";if(z.proposed.empty())o<<"null";else rect(z.proposed);
 o<<",\"track_roi_unclipped\":";if(z.unclipped.empty())o<<"null";else rect(z.unclipped);
 o<<",\"raw_tip\":";if(e.candidate)point(e.tip);else o<<"null";
 o<<",\"output\":";point(z.output);o<<",\"last_confirmed\":";if(s.state.has)point(s.state.last);else o<<"null";
 o<<",\"last_confirmed_frame\":"<<s.state.last_frame<<",\"predicted\":";if(z.predicted_valid)point(z.predicted);else o<<"null";
 o<<",\"tip_motion_valid\":"<<boolean(e.motion)<<",\"tip_inliers\":"<<d.tip_registration_inliers<<",\"tip_transform\":[";
 o<<e.rotation(0,0)<<','<<e.rotation(0,1)<<','<<e.translation.x<<','<<e.rotation(1,0)<<','<<e.rotation(1,1)<<','<<e.translation.y<<']';
 o<<",\"state_ms\":"<<state_ms<<",\"diagnostic_ms\":"<<elapsed(start)<<",\"input_path\":[";
 for(size_t i=0;i<e.path.size();++i){if(i)o<<',';point(e.path[i]);}o<<"]}";s.json=o.str();return s.json.c_str();
}
}
