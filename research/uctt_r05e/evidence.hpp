#pragma once
#include <chrono>
#include <limits>
#include <map>
// Independent current-image, dark-valley evidence. No Detector/history/GT access.
namespace r05e {
using Clock=std::chrono::steady_clock;
inline double elapsed(Clock::time_point t){return std::chrono::duration<double,std::milli>(Clock::now()-t).count();}
constexpr int RawBudget=8192,RetainedBudget=64,PerBucket=4,TraceBudget=16;
struct Candidate {int id=0,x=0,y=0,bucket=0,merged=-1,retained=-1;float gain=0,support=0;double direction=0;int length=0;std::string reason,source="current";};
struct Evidence {
 cv::Mat1f current,reference,change,novel,valley,quality,reason;
 cv::Mat debug_eroded,debug_refmin,debug_refmax;
 std::vector<Candidate> candidates;
 int raw_total=0,merged_count=0,retained_count=0,valid_pixels=0,current_pixels=0,legacy_pixels=0;
 bool exhausted=false;double current_ms=0,reference_ms=0,dp_ms=0,candidates_ms=0;
};
inline void channels(Evidence&e,const cv::Mat1f&im,const cv::Mat1f&registered,const cv::Mat1f&eroded,const cv::Mat1f&refMin,const cv::Mat1f&refMax,const cv::Mat1b&prior,const cv::Mat1b&valid,const cv::Mat1f&legacy){
 auto start=Clock::now();const float nan=std::numeric_limits<float>::quiet_NaN();
 e.current=cv::Mat1f(im.size(),-3.f);e.valley=cv::Mat1f(im.size(),nan);e.reason=cv::Mat1f(im.size(),1.f);
 for(int y=5;y<im.rows-5;++y)for(int x=4;x<im.cols-4;++x){
  float flank=std::min(im(y-4,x),im(y+4,x));e.valley(y,x)=flank-im(y,x);
  int mask=0;if(flank<75)mask|=2;else e.current(y,x)=e.valley(y,x);
  e.reason(y,x)=float(mask);e.current_pixels+=e.current(y,x)>=3;e.legacy_pixels+=legacy(y,x)>=3;
 }
 e.current_ms=elapsed(start);start=Clock::now();
 e.reference=cv::Mat1f(im.size(),nan);e.change=cv::Mat1f(im.size(),nan);e.novel=cv::Mat1f(im.size(),nan);e.quality=cv::Mat1f(im.size(),0.f);
 // The full blur + y +/-4 footprint must be spatially supported. UNKNOWN is NaN.
 cv::Mat1b spatial;if(!valid.empty())cv::erode(valid,spatial,cv::Mat::ones(11,11,CV_8U),{-1,-1},1,cv::BORDER_CONSTANT,cv::Scalar(0));
 for(int y=5;y<im.rows-5;++y)for(int x=4;x<im.cols-4;++x){
  int mask=int(e.reason(y,x));bool ok=!registered.empty()&&!spatial.empty()&&spatial(y,x)!=0;
  if(!ok)mask|=4;
  else {e.quality(y,x)=1;++e.valid_pixels;float ridge=std::min(registered(y-4,x),registered(y+4,x))-registered(y,x);
   e.reference(y,x)=ridge;e.change(y,x)=registered(y,x)-im(y,x);
   e.novel(y,x)=std::min(eroded(y,x)-im(y,x),e.valley(y,x)-std::max(0.f,ridge));
   if(eroded(y,x)<=75)mask|=8;if(refMin(y,x)<=85||refMax(y,x)-refMin(y,x)>=40)mask|=16;
   if(!prior.empty()&&prior(y,x))mask|=32;
  }
  if(e.current(y,x)>=3&&legacy(y,x)<3)mask|=64;e.reason(y,x)=float(mask);
 }
 e.reference_ms=elapsed(start);
}
inline void candidates(Evidence&e,const std::vector<cv::Point3f>&legacy={}){
 auto start=Clock::now();auto&s=e.current;int h=s.rows,w=s.cols;if(h<16||w<20)return;
 cv::Mat1f gain(h,w,0.f);cv::Mat1b gaps(h,w,uchar(0));cv::Mat_<signed char> back(h,w,static_cast<signed char>(2));
 // Same native local alignment recurrence as legacy distalLine, but current-only.
 for(int x=4;x<w-4;++x)for(int y=5;y<h-5;++y){double best=0;
  for(int k:{0,-1,1}){if(s(y,x)<3&&gaps(y+k,x-1)>=3)continue;double g=gain(y+k,x-1)-(k?.6:0.);if(g>best){best=g;back(y,x)=static_cast<signed char>(k);}}
  gain(y,x)=float(std::max(0.,best+std::clamp(double(s(y,x))/3.-1.,-2.,4.)));
  if(s(y,x)<3&&back(y,x)!=2)gaps(y,x)=1+gaps(y+back(y,x),x-1);
 }
 e.dp_ms=elapsed(start);start=Clock::now();
 for(int x=4;x<w-10;++x)for(int y=5;y<h-5;++y){float g=gain(y,x);
  if(g<12||s(y,x)<3||g<gain(y-1,x)||g<gain(y+1,x)||g<=std::max({gain(y-1,x+1),gain(y,x+1),gain(y+1,x+1)}))continue;
  int id=e.raw_total++;if(int(e.candidates.size())>=RawBudget){e.exhausted=true;continue;}
  Candidate p;p.id=id;p.x=x;p.y=y;p.gain=g;p.support=s(y,x);p.bucket=std::min(3,4*x/w)+4*std::min(3,4*y/h);
  int xx=x,yy=y;for(int j=0;j<TraceBudget&&xx>=4&&gain(yy,xx)>0;++j){++p.length;int k=back(yy,xx);if(k==2)break;yy+=k;--xx;}
  p.direction=std::atan2(double(y-yy),double(std::max(1,x-xx)));e.candidates.push_back(p);
 }
 // Preserve peaks already present in the unchanged legacy DP. This union is
 // image-derived and uniform; no human location or specimen-specific reserve.
 std::map<std::pair<int,int>,int> xy;for(auto&p:e.candidates)xy[{p.x,p.y}]=p.id;
 for(auto&z:legacy){int x=int(z.x),y=int(z.y);auto it=xy.find({x,y});
  if(it!=xy.end()){e.candidates[it->second].source="current+legacy";continue;}
  int id=e.raw_total++;if(int(e.candidates.size())>=RawBudget){e.exhausted=true;continue;}
  Candidate p;p.id=id;p.x=x;p.y=y;p.gain=z.z;p.support=s(y,x);p.bucket=std::min(3,4*x/w)+4*std::min(3,4*y/h);p.source="legacy";
  int xx=x,yy=y;for(int j=0;j<TraceBudget&&xx>=4&&gain(yy,xx)>0;++j){++p.length;int k=back(yy,xx);if(k==2)break;yy+=k;--xx;}p.direction=std::atan2(double(y-yy),double(std::max(1,x-xx)));
  xy[{x,y}]=p.id;e.candidates.push_back(p);
 }
#ifdef R05E_BUDGET
 // Spatial hashing bounds comparisons. Merge only nearby endpoints with similar
 // local direction; different stop locations survive to bucket reservation.
 std::map<std::pair<int,int>,std::vector<int>> grid;std::vector<int> representatives;
 for(auto&p:e.candidates){int merge=-1;int gx=p.x/4,gy=p.y/4;
  for(int yy=gy-1;yy<=gy+1&&merge<0;++yy)for(int xx=gx-1;xx<=gx+1&&merge<0;++xx){auto it=grid.find({xx,yy});if(it==grid.end())continue;
   for(int j:it->second){auto&q=e.candidates[j];if(std::hypot(double(p.x-q.x),double(p.y-q.y))<=3&&std::abs(p.direction-q.direction)<=.25){merge=q.merged;break;}}}
  if(merge>=0){p.merged=merge;p.reason="directional_duplicate_within3px";}
  else {p.merged=int(representatives.size());representatives.push_back(p.id);grid[{gx,gy}].push_back(p.id);}
 }
 e.merged_count=int(representatives.size());
 for(int bucket=0;bucket<16;++bucket){std::vector<int> ids;for(int id:representatives)if(e.candidates[id].bucket==bucket)ids.push_back(id);
  // Reserve strongest accumulation, strongest local contrast, furthest stop,
  // and weakest local contrast. These are structural alternatives, not a lock.
  for(int slot=0;slot<PerBucket&&!ids.empty();++slot){auto quality=[&](int id){auto&p=e.candidates[id];return slot==0?double(p.gain):slot==1?double(p.support):slot==2?double(p.x):-double(p.support);};
   auto best=std::max_element(ids.begin(),ids.end(),[&](int a,int b){return quality(a)<quality(b);});auto&p=e.candidates[*best];p.retained=e.retained_count++;p.reason="reserved_bucket_slot_"+std::to_string(slot);ids.erase(best);
  }
  for(int id:ids)e.candidates[id].reason="bucket_capacity_drop";
 }
 for(auto&p:e.candidates)if(p.reason=="directional_duplicate_within3px")p.retained=e.candidates[representatives[p.merged]].retained;
#else
 e.merged_count=int(e.candidates.size());for(auto&p:e.candidates){p.merged=p.id;p.retained=p.id;p.reason="B1_uncompressed_shadow";}e.retained_count=int(e.candidates.size());
#endif
 e.candidates_ms=elapsed(start);
}
}
