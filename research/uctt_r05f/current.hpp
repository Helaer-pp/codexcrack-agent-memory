#pragma once
#include <opencv2/opencv.hpp>
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <deque>
#include <map>
#include <set>
#include <sstream>
#include <iomanip>
#include <vector>
namespace r05f {
using P=cv::Point2d;using Clock=std::chrono::steady_clock;
inline double ms(Clock::time_point t){return std::chrono::duration<double,std::milli>(Clock::now()-t).count();}
inline P unit(P p){double n=cv::norm(p);return n>1e-9?p/n:P(1,0);}
inline bool inside(P p,cv::Size s){return std::isfinite(p.x)&&std::isfinite(p.y)&&p.x>=0&&p.y>=0&&p.x<s.width&&p.y<s.height;}
struct Config {
 int maxWindows=192,maxSegments=8192,maxCandidates=32768;
 int maxPixels=4000000,maxFrontiers=8,maxReferenceCalls=12;
 double response=3,softTimeMs=50;
};
struct Candidate {int id=0,segment=0,canonical=0,window=0;P p,tangent;double support=0,width=0;std::string source;bool windowCut=false;};
struct Segment {int id=0,window=0,seed=-1,parent=-1;std::vector<P> points;P start,end,tangent;double support=0,width=0,length=0;bool cut=false;std::string refState="reference_unknown",association="unknown";};
struct Window {int id=0,parent=-1,seed=0;P center,forward;int w=0,h=0;std::vector<P> polygon;std::string source="static_control";int segments=0,candidates=0,localPixels=0,newPixels=0;double currentMs=0;bool clipped=false;};
struct Frame {
 int frame=0,mode=0;P origin,forward,normal;double spacing=0;bool validAnchors=true,searchIncomplete=false;
 std::string reason="shadow_evidence_only",state="fallback";
 std::vector<Window> windows;std::vector<Segment> segments;std::vector<Candidate> candidates;
 int rawCandidates=0,retainedCandidates=0,uniquePixels=0,totalPixels=0,rawSegments=0,cacheHits=0;
 double currentMs=0,apiMs=0;bool trustedHistoryWritten=false;cv::Mat1b visited;
 std::map<std::pair<long long,long long>,int> endpointIndex;
 std::map<std::pair<int,int>,std::vector<int>> structures;
};
struct Patch {cv::Mat1f intensity,score,scale;cv::Mat1b valid;};
inline P global(const Window&w,double x,double y){P n(-w.forward.y,w.forward.x);return w.center+w.forward*(x-(w.w-1)*.5)+n*(y-(w.h-1)*.5);}
inline Patch sampleCurrent(const cv::Mat1b&im,Window&w,Frame&f,double spacing){
 Patch p;cv::Mat1f xx(w.h,w.w),yy(w.h,w.w);p.valid=cv::Mat1b(w.h,w.w,uchar(0));
 double minx=w.polygon[0].x,maxx=minx,miny=w.polygon[0].y,maxy=miny;
 for(P q:w.polygon){minx=std::min(minx,q.x);maxx=std::max(maxx,q.x);miny=std::min(miny,q.y);maxy=std::max(maxy,q.y);}
 int bx=int(std::floor(minx)),by=int(std::floor(miny));
 cv::Mat1b localFootprint(int(std::ceil(maxy))-by+2,int(std::ceil(maxx))-bx+2,uchar(0));
 for(int y=0;y<w.h;++y)for(int x=0;x<w.w;++x){P q=global(w,x,y);xx(y,x)=float(q.x);yy(y,x)=float(q.y);
  int ix=int(std::floor(q.x)),iy=int(std::floor(q.y));if(ix<0||iy<0||ix+1>=im.cols||iy+1>=im.rows){w.clipped=true;continue;}
  p.valid(y,x)=255;for(int dy=0;dy<2;++dy)for(int dx=0;dx<2;++dx){int sx=ix+dx,sy=iy+dy;if(!localFootprint(sy-by,sx-bx)){localFootprint(sy-by,sx-bx)=255;++w.localPixels;}if(!f.visited(sy,sx)){f.visited(sy,sx)=255;++w.newPixels;}}
 }
 f.totalPixels+=w.localPixels;f.uniquePixels+=w.newPixels;
 cv::Mat patch;cv::remap(im,patch,xx,yy,cv::INTER_LINEAR,cv::BORDER_CONSTANT,cv::Scalar(0));patch.convertTo(p.intensity,CV_32F);cv::GaussianBlur(p.intensity,p.intensity,{3,3},.8);
 p.score=cv::Mat1f(w.h,w.w,-3.f);p.scale=cv::Mat1f(w.h,w.w,0.f);
 std::set<int> radii;double factor=std::clamp(std::sqrt(spacing/256.),.5,1.5);for(int r:{1,2,4,8})radii.insert(std::clamp(int(std::lround(r*factor)),1,12));
 for(int r:radii)for(int y=r+1;y<w.h-r-1;++y)for(int x=1;x<w.w-1;++x){if(!p.valid(y-r-1,x)||!p.valid(y+r+1,x))continue;
  float flank=std::min(p.intensity(y-r,x),p.intensity(y+r,x));if(flank<75)continue;float value=flank-p.intensity(y,x);
  if(value>p.score(y,x)){p.score(y,x)=value;p.scale(y,x)=float(r);}
 }
 return p;
}
inline void addCandidate(Frame&f,const Config&cfg,const Segment&s,P p,double support,double width,const char*source,bool cut){
 ++f.rawCandidates;if(int(f.candidates.size())>=cfg.maxCandidates){f.searchIncomplete=true;f.reason="candidate_budget";return;}
 Candidate c;c.id=int(f.candidates.size());c.canonical=c.id;c.segment=s.id;c.window=s.window;c.p=p;c.tangent=s.tangent;c.support=support;c.width=width;c.source=source;c.windowCut=cut;
 // Geometric duplicates require location, direction, scale and stop type.
 // Keep every alias for auditing; no global strongest-K suppression.
 int gx=int(std::floor(p.x/2)),gy=int(std::floor(p.y/2));bool found=false;
 for(int dy=-1;dy<=1&&!found;++dy)for(int dx=-1;dx<=1&&!found;++dx){auto it=f.structures.find({gx+dx,gy+dy});if(it==f.structures.end())continue;
  for(int id:it->second){auto&old=f.candidates[id];if(old.source==c.source&&old.windowCut==c.windowCut&&cv::norm(old.p-p)<=1.5&&old.tangent.dot(c.tangent)>=.965925826&&std::max(old.width,width)<=2*std::max(1.,std::min(old.width,width))){c.canonical=id;found=true;break;}}
 }
 if(!found){f.structures[{gx,gy}].push_back(c.id);++f.retainedCandidates;}
 f.candidates.push_back(c);
}
inline void findCurrentDarklineSegments(const cv::Mat1b&im,Window&w,Frame&f,const Config&cfg){
 auto start=Clock::now();Patch p=sampleCurrent(im,w,f,f.spacing);cv::Mat1b ridge(w.h,w.w,uchar(0));
 for(int y=1;y<w.h-1;++y)for(int x=1;x<w.w-1;++x)if(p.score(y,x)>=cfg.response&&p.score(y,x)>=p.score(y-1,x)&&p.score(y,x)>p.score(y+1,x))ridge(y,x)=255;
 cv::Mat1i labels,stats;cv::Mat centroids;int count=cv::connectedComponentsWithStats(ridge,labels,stats,centroids,8,CV_32S);
 std::vector<std::vector<cv::Point>> components(count);
 for(int y=1;y<w.h-1;++y)for(int x=1;x<w.w-1;++x)if(labels(y,x)>0)components[labels(y,x)].push_back({x,y});
 int before=int(f.segments.size()),candBefore=int(f.candidates.size());
 for(int id=1;id<count;++id){auto&nodes=components[id];if(nodes.size()<4||stats(id,cv::CC_STAT_WIDTH)<4)continue;++f.rawSegments;
  if(int(f.segments.size())>=cfg.maxSegments){f.searchIncomplete=true;f.reason="segment_budget";break;}
  // Actual ridge centers, one strongest center per column in each connected
  // local structure. Multiple components never compete for one global score.
  std::map<int,cv::Point> columns;for(auto q:nodes){auto it=columns.find(q.x);if(it==columns.end()||p.score(q)>p.score(it->second))columns[q.x]=q;}
  if(columns.size()<4)continue;Segment s;s.id=int(f.segments.size());s.window=w.id;s.seed=w.seed;s.parent=w.parent;
  std::vector<cv::Point> line;for(auto&entry:columns){auto q=entry.second;line.push_back(q);s.points.push_back(global(w,q.x,q.y));s.support+=p.score(q);s.width+=2*p.scale(q);}
  s.support/=line.size();s.width/=line.size();s.start=s.points.front();s.end=s.points.back();s.tangent=unit(s.end-s.points[std::max(0,int(s.points.size())-8)]);
  for(size_t i=1;i<s.points.size();++i)s.length+=cv::norm(s.points[i]-s.points[i-1]);
  auto last=line.back();s.cut=last.x>=w.w-3||last.y<3||last.y>=w.h-3;
  f.segments.push_back(s);addCandidate(f,cfg,s,s.end,p.score(last),2*p.scale(last),"component_end",s.cut);
  // Retain a real contrast-drop shoulder as a separate unconfirmed stop.
  // No equally spaced oracle points and no DP forward-maximum requirement.
  for(int j=3;j+3<int(line.size());++j){float a=p.score(line[j-3]),b=p.score(line[j]),c=p.score(line[j+3]);
   if(a-b>=3&&b>=cfg.response&&c<=b&&b<=p.score(line[j-1])&&b<p.score(line[j+1]))addCandidate(f,cfg,s,s.points[j],b,2*p.scale(line[j]),"contrast_drop_stop",false);
  }
 }
 w.segments=int(f.segments.size())-before;w.candidates=int(f.candidates.size())-candBefore;w.currentMs=ms(start);f.currentMs+=w.currentMs;
}
inline Window makeWindow(P center,P direction,int width,int height,int parent,int seed,const char*source){
 Window w;w.center=center;w.forward=unit(direction);w.w=width;w.h=height;w.parent=parent;w.seed=seed;w.source=source;
 for(P p:{P(0,0),P(width-1,0),P(width-1,height-1),P(0,height-1)})w.polygon.push_back(global(w,p.x,p.y));return w;
}
struct Detector {
 cv::Mat1b fixed;std::array<P,2> initial;Config cfg;Frame last;int frame=0,mode=0;bool capture=false;std::string json;
 // Trusted history is separate from all per-frame exploration data. S1 has
 // no verification producer and therefore cannot write this store.
 std::vector<P> trustedPath;
 Detector(const cv::Mat1b&ref,std::array<P,2>pp,int m):fixed(ref.clone()),initial(pp),mode(m){}
 bool anchorsOK(const std::array<P,2>&a,cv::Size sz){return inside(a[0],sz)&&inside(a[1],sz)&&a[0].y<a[1].y&&cv::norm(a[1]-a[0])>=16;}
 void process(const cv::Mat1b&im,std::array<P,2>a){
  auto start=Clock::now();last={};auto&f=last;f.frame=++frame;f.mode=mode;
  if(im.size()!=fixed.size()||!anchorsOK(a,im.size())){f.validAnchors=false;f.searchIncomplete=true;f.reason="invalid_current_geometry";f.apiMs=ms(start);return;}
  f.origin=(a[0]+a[1])*.5;f.spacing=cv::norm(a[1]-a[0]);P across=unit(a[1]-a[0]);f.forward=P(across.y,-across.x);f.normal=P(-f.forward.y,f.forward.x);f.visited=cv::Mat1b(im.size(),uchar(0));
  int width=std::clamp(int(std::lround(.6*f.spacing)),96,192),height=std::clamp(int(std::lround(.4*f.spacing)),64,128);
  double behind=std::clamp(.38*f.spacing,24.,192.),ahead=std::clamp(4.5*f.spacing,256.,1536.),half=std::clamp(1.4*f.spacing,96.,384.);
  for(double v=-half;v<=half;v+=height*.75)for(double u=-behind;u<=ahead;u+=width*.75){
   if(int(f.windows.size())>=cfg.maxWindows||f.totalPixels>=cfg.maxPixels){f.searchIncomplete=true;f.reason="static_window_budget";break;}
   Window w=makeWindow(f.origin+f.forward*u+f.normal*v,f.forward,width,height,-1,0,"static_current_control");w.id=int(f.windows.size());findCurrentDarklineSegments(im,w,f,cfg);f.windows.push_back(std::move(w));
  }
  f.apiMs=ms(start);
 }
};
}
