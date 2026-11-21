#pragma once
#include <opencv2/core.hpp>
#include <algorithm>
#include <cmath>
#include <string>
#include <vector>
namespace r03 {
using Pt=cv::Point2d;
struct Evidence {
 cv::Size size; cv::Rect search; Pt tip{}, direction{1,0};
 cv::Matx22d rotation=cv::Matx22d::eye(); Pt translation{};
 bool candidate=false, terminal=false, path_valid=false, motion=false;
 std::vector<Pt> path;
};
struct Decision {
 std::string before,after,source,reason; Pt output{},predicted{};
 bool accepted=false,attempted=false,valid=false,edge=false,history_written=false;
 bool predicted_valid=false,clipped=false;
 cv::Rect proposed,unclipped;
};
struct State {
 std::string state="SEARCHING"; bool has=false;
 Pt last{},reference_tip{},reference_direction{1,0}; cv::Size last_size{};
 unsigned long long frame=0,last_frame=0; int misses=0;
 static bool inside(Pt p,cv::Size s) { return std::isfinite(p.x)&&std::isfinite(p.y)&&p.x>=0&&p.y>=0&&p.x<s.width&&p.y<s.height; }
 Decision step(const Evidence &e) {
  Decision z;z.before=state;++frame;z.attempted=e.candidate;
  const cv::Rect bounds({},e.size);
  auto center=e.search.empty()?Pt((e.size.width-1)*.5,(e.size.height-1)*.5):Pt(e.search.x+e.search.width*.5,e.search.y+e.search.height*.5);
  z.output=center;z.source="fallback";
  const bool same_size=last_size.empty()||last_size==e.size;
  bool transform_ok=std::isfinite(e.translation.x)&&std::isfinite(e.translation.y);
  for(double v:e.rotation.val) transform_ok=transform_ok&&std::isfinite(v);
  const bool motion=e.motion&&same_size&&transform_ok;
  if(has&&motion) { z.predicted=e.rotation*reference_tip+e.translation;z.predicted_valid=inside(z.predicted,e.size); }
  bool supported=e.candidate&&e.path_valid&&e.terminal&&e.path.size()>=2&&inside(e.tip,e.size);
  if(supported) supported=cv::norm(e.path.back()-e.tip)<=1e-4;
  // Nine forward samples are required by the unchanged distalLine terminal audit.
  if(e.candidate) z.edge=!inside(e.tip,e.size)||!e.search.contains(cv::Point(int(e.tip.x),int(e.tip.y))) ||
    std::min({e.tip.x-e.search.x,e.tip.y-e.search.y,e.search.br().x-1-e.tip.x,e.search.br().y-1-e.tip.y})<10;
  bool compatible=!has||z.predicted_valid;
  if(supported&&has&&z.predicted_valid) {
   // Existing locality/overlap constants (6 px, 24 samples), not a speed limit.
   compatible=std::any_of(e.path.begin(),e.path.end(),[&](Pt p){return cv::norm(p-z.predicted)<=6;}) || cv::norm(e.tip-z.predicted)<=6;
  }
  bool forward=supported&&((e.tip-e.path.front()).dot(e.direction)>0);
  if(supported&&motion&&!z.edge&&compatible&&forward) {
   z.accepted=z.valid=z.history_written=true;z.source="observed";z.output=e.tip;
   z.reason=has?"current_path_connected":"existing_terminal_and_path_support";
   has=true;last=e.tip;last_frame=frame;reference_tip=e.rotation.t()*(e.tip-e.translation);
   Pt dir=e.tip-e.path[e.path.size()-std::min<size_t>(24,e.path.size())];
   if(cv::norm(dir)>0) reference_direction=e.rotation.t()*(dir/cv::norm(dir));
   misses=0;state="TRACKING";
  } else {
   ++misses;
   z.reason=!same_size?"image_size_changed":!motion?"motion_unreliable":!e.candidate?"no_visual_candidate":!supported?"path_endpoint_mismatch":z.edge?"roi_edge_risk":!forward?"direction_incompatible":"disconnected_candidate";
   state=has?((!motion||misses>=3||!compatible)?"RECOVERING":"OCCLUDED"):(e.candidate?"ACQUIRING":"SEARCHING");
   if(z.predicted_valid){z.output=z.predicted;z.source="predicted";}
   else if(has) z.reason+="_no_current_prediction";
  }
  if(has&&motion&& (z.accepted||z.predicted_valid)) {
   Pt c=z.accepted?z.output:z.predicted,dir=e.rotation*reference_direction,n(-dir.y,dir.x);
   // Proposal only: 24 px connected tail, 64 px capture, bounded uncertainty.
   const double u=std::min(96,misses*12),back=24+u,ahead=64+u,half=24+u;
   Pt corners[]={c-dir*back-n*half,c-dir*back+n*half,c+dir*ahead-n*half,c+dir*ahead+n*half};
   double x=corners[0].x,y=corners[0].y,xx=x,yy=y;
   for(auto p:corners){x=std::min(x,p.x);y=std::min(y,p.y);xx=std::max(xx,p.x);yy=std::max(yy,p.y);}
   z.unclipped=cv::Rect(int(std::floor(x)),int(std::floor(y)),int(std::ceil(xx)-std::floor(x))+1,int(std::ceil(yy)-std::floor(y))+1);
   z.proposed=z.unclipped&bounds;z.clipped=z.proposed!=z.unclipped;
  }
  if(!inside(z.output,e.size)) {z.output=Pt(std::clamp(z.output.x,0.,double(e.size.width-1)),std::clamp(z.output.y,0.,double(e.size.height-1)));z.source="fallback";z.valid=false;z.reason+="_boundary_fallback";}
  if(last_size.empty())last_size=e.size;z.after=state;return z;
 }
};
}
