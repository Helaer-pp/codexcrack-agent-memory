#pragma once
#include "sampling.hpp"
namespace r05h {
using namespace hcore;
struct Match {bool valid=false;P shift;double correlation=0,margin=0,texture=0,cycle=999;bool boundary=false;std::string reason="UNAVAILABLE";};
inline cv::Rect box(P p,int half){return cv::Rect(int(std::lround(p.x))-half,int(std::lround(p.y))-half,2*half+1,2*half+1);}
inline bool fits(cv::Rect r,cv::Size size){return r.x>=0&&r.y>=0&&r.x+r.width<=size.width&&r.y+r.height<=size.height;}
inline Match matchMaterial(const cv::Mat1b&im,const cv::Mat1b&ref,P p,P predicted,int radius,int search){
 Match q;auto a=box(p,radius),area=box(predicted,radius+search);if(!fits(a,im.size())||!fits(area,ref.size())){q.reason="image_boundary";return q;}
 cv::Scalar mean,sd;cv::meanStdDev(im(a),mean,sd);q.texture=sd[0];if(q.texture<4){q.reason="low_texture";return q;}
 cv::Mat1f map;cv::matchTemplate(ref(area),im(a),map,cv::TM_CCOEFF_NORMED);double peak;cv::Point location;cv::minMaxLoc(map,nullptr,&peak,nullptr,&location);q.correlation=peak;
 q.boundary=location.x<=1||location.y<=1||location.x>=map.cols-2||location.y>=map.rows-2;
 auto masked=map.clone();cv::rectangle(masked,cv::Rect(location.x-3,location.y-3,7,7)&cv::Rect(0,0,map.cols,map.rows),cv::Scalar(-1),cv::FILLED);double second;cv::minMaxLoc(masked,nullptr,&second);q.margin=peak-second;
 P matched(area.x+location.x+radius,area.y+location.y+radius);P actualCenter(a.x+radius,a.y+radius);q.shift=matched-actualCenter;
 auto backArea=box(p,radius+8),b=box(matched,radius);if(fits(backArea,im.size())&&fits(b,ref.size())){cv::Mat1f reverse;cv::matchTemplate(im(backArea),ref(b),reverse,cv::TM_CCOEFF_NORMED);cv::Point back;cv::minMaxLoc(reverse,nullptr,nullptr,nullptr,&back);q.cycle=norm(P(backArea.x+back.x+radius,backArea.y+back.y+radius)-actualCenter);}
 q.valid=q.correlation>=.75&&q.margin>=.025&&q.cycle<=2.5&&!q.boundary;
 q.reason=q.valid?"VALID":q.boundary?"search_boundary":q.correlation<.75?"weak_correlation":q.margin<.025?"nonunique_peak":"cycle_inconsistent";return q;
}
struct ReferenceEvidence {std::string state="UNAVAILABLE",classification="INDETERMINATE",source="fixed";std::vector<Match>matches;P shift;double residual=999,current=0,previous=0,bonus=0,ms=0;int validSides=0;};
inline double valley(const cv::Mat1b&im,P p,P t,double scale){
 auto sample=[&](P v){int x=int(std::floor(v.x)),y=int(std::floor(v.y));if(x<0||y<0||x+1>=im.cols||y+1>=im.rows)return std::numeric_limits<double>::quiet_NaN();double fx=v.x-x,fy=v.y-y;return (1-fy)*((1-fx)*im(y,x)+fx*im(y,x+1))+fy*((1-fx)*im(y+1,x)+fx*im(y+1,x+1));};P n(-t.y,t.x);double best=0;
 for(int radius:{1,2,4,8}){double r=std::clamp(radius*scale,1.,12.);double center=sample(p),l=sample(p-n*r),h=sample(p+n*r);if(std::isfinite(l)&&std::isfinite(h)&&std::isfinite(center)&&std::min(l,h)>=75)best=std::max(best,std::min(l,h)-center);}
 return best;
}
inline ReferenceEvidence compareReference(const cv::Mat1b&im,const cv::Mat1b&ref,P p,P tangent,P approximateShift,double spacing,double width,const char*source){
 auto clock=Clock::now();ReferenceEvidence e;e.source=source;P normal(-tangent.y,tangent.x);int radius=int(std::clamp(std::sqrt(spacing/256.)*10.,7.,15.)),search=int(std::clamp(.14*spacing,24.,80.));double off=std::clamp(radius+width+8.,22.,60.);std::vector<P>sideShifts;
 for(int side:{-1,1}){std::vector<P>shifts;for(double along:{-12.,12.}){P center=p+normal*(off*side)+tangent*along;auto m=matchMaterial(im,ref,center,center+approximateShift,radius,search);e.matches.push_back(m);if(m.valid)shifts.push_back(m.shift);}
  if(shifts.size()==2){double error=norm(shifts[0]-shifts[1]);e.residual=std::min(e.residual,error);if(error<=3){e.validSides++;sideShifts.push_back((shifts[0]+shifts[1])*.5);}}
 }
 if(e.validSides==2){e.state="VALID";e.shift=(sideShifts[0]+sideShifts[1])*.5;double scale=std::clamp(std::sqrt(spacing/256.),.6,1.5);e.current=valley(im,p,tangent,scale);e.previous=.5*(valley(ref,p+sideShifts[0],tangent,scale)+valley(ref,p+sideShifts[1],tangent,scale));
  if(e.current>=3&&e.current-e.previous>=std::max(3.,.3*e.current)){e.classification="NEW";e.bonus=std::min(1.,(e.current-e.previous)/(e.current+3));}
  else if(e.previous>=3&&e.previous>=.8*e.current)e.classification="OLD_TEXTURE";
 }else if(e.validSides==1)e.state="UNCERTAIN";
 e.ms=elapsed(clock);return e;
}
}
