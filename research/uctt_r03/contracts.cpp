#include "state.hpp"
#include <iostream>
#include <fstream>
#include <limits>
using namespace r03;
int main(int argc,char**argv){
 if(argc!=2){std::cerr<<"Expected seed file exported from replay\n";return 1;}
 Evidence e;size_t n;std::ifstream in(argv[1]);
 in>>e.size.width>>e.size.height>>e.search.x>>e.search.y>>e.search.width>>e.search.height>>n;
 for(size_t i=0;i<n;++i){Pt p;in>>p.x>>p.y;e.path.push_back(p);}
 if(!in||n<2)return 1;
 e.tip=e.path.back();e.direction=e.tip-e.path.front();e.direction/=cv::norm(e.direction);
 e.candidate=e.terminal=e.path_valid=e.motion=true;
 std::cout<<"case_id,evidence_level,expected,actual,state,source,valid,history_written,track_roi_present,pass\n";
 int fails=0;
 auto check=[&](const char*name,const char*expected,const State&s,const Decision&z,bool pass){
  std::cout<<name<<",INJECTED_CANDIDATE_EVIDENCE,"<<expected<<','<<z.reason<<','<<s.state<<','<<z.source<<','<<z.valid<<','<<z.history_written<<','<<!z.proposed.empty()<<','<<pass<<'\n';fails+=!pass;
 };
 State a;Evidence no=e;no.candidate=no.terminal=no.path_valid=false;no.path.clear();Decision z;
 for(int i=0;i<8;++i)z=a.step(no);
 check("no_crack","SEARCHING_no_track_no_history",a,z,a.state=="SEARCHING"&&!a.has&&z.proposed.empty()&&!z.valid&&State::inside(z.output,no.size));
 State s;z=s.step(e);check("reference_preexisting_crack","strong_single_frame_acquires",s,z,z.valid&&s.has);
 auto remembered=s.last;auto frame=s.last_frame;
 z=s.step(e);check("stationary_crack","TRACKING_observed",s,z,z.valid&&s.state=="TRACKING"&&cv::norm(s.last-remembered)<1e-8);
 frame=s.last_frame;
 z=s.step(no);check("closure_first_frame","OCCLUDED_predicted_no_write",s,z,s.state=="OCCLUDED"&&!z.valid&&!z.history_written&&s.last_frame==frame&&z.source=="predicted");
 z=s.step(no);z=s.step(no);check("sustained_loss","RECOVERING_no_write",s,z,s.state=="RECOVERING"&&!z.history_written&&s.last_frame==frame);
 z=s.step(e);check("reappearance","connected_visual_reacquires",s,z,z.valid&&s.state=="TRACKING");
 Evidence bad=e;bad.motion=false;frame=s.last_frame;z=s.step(bad);
 check("bad_motion","fallback_no_write",s,z,!z.valid&&!z.history_written&&s.last_frame==frame&&z.source=="fallback"&&z.proposed.empty());
 bad=e;bad.tip+=Pt(30,30);z=s.step(bad);
 check("wrong_tip_mismatched_path","reject_no_history",s,z,!z.valid&&!z.history_written&&s.last_frame==frame);
 bad=e;for(auto&p:bad.path)p+=Pt(-30,-30);bad.tip=bad.path.back();z=s.step(bad);
 check("disconnected_wrong_candidate_after_lock","reject_no_history",s,z,!z.valid&&!z.history_written&&s.last_frame==frame);
 // Known-injected distractor truth is held by the test harness only. Runtime sees
 // a fully self-consistent candidate; accepting it is a failed safety gate.
 State first;z=first.step(bad);
 check("coherent_wrong_first_lock","reject_injected_distractor",first,z,!z.valid&&!first.has&&z.proposed.empty());
 State border;bad=e;Pt shift(e.search.x+2-e.tip.x,0);for(auto&p:bad.path)p+=shift;bad.tip=bad.path.back();z=border.step(bad);
 check("boundary_terminal","reject_edge",border,z,!z.valid&&!border.has&&z.edge);
 bad=e;bad.tip.x=std::numeric_limits<double>::quiet_NaN();z=s.step(bad);
 check("nan_candidate","finite_fallback_or_prediction",s,z,!z.valid&&!z.history_written&&State::inside(z.output,e.size));
 bad=e;bad.translation.x=std::numeric_limits<double>::infinity();z=s.step(bad);
 check("nonfinite_motion","finite_fallback_no_write",s,z,!z.valid&&!z.history_written&&State::inside(z.output,e.size));
 bad=e;bad.size.width-=1;z=s.step(bad);check("image_size_change","reset_required_no_write",s,z,!z.valid&&!z.history_written&&z.proposed.empty());
 z=s.step(bad);check("persistent_changed_size","still_reset_required",s,z,!z.valid&&!z.history_written);
 State reset;z=reset.step(no);check("new_detector_reset","SEARCHING_empty_history",reset,z,!reset.has&&reset.state=="SEARCHING"&&z.proposed.empty());
 return fails?2:0;
}
