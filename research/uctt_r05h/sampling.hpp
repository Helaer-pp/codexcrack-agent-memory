#pragma once
#include <opencv2/opencv.hpp>
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <deque>
#include <iomanip>
#include <limits>
#include <map>
#include <sstream>
#include <string>
#include <vector>
namespace hcore {
using P=cv::Point2d;using Clock=std::chrono::steady_clock;
inline double elapsed(Clock::time_point t){return std::chrono::duration<double,std::milli>(Clock::now()-t).count();}
inline double norm(P p){return std::hypot(p.x,p.y);}inline P unit(P p){double n=norm(p);return n>1e-9?p/n:P(1,0);}
inline double angle(P p){return std::atan2(p.y,p.x);}inline double wrap(double a){while(a>CV_PI)a-=2*CV_PI;while(a< -CV_PI)a+=2*CV_PI;return a;}
inline P rotate(P p,double a){return P(p.x*std::cos(a)-p.y*std::sin(a),p.x*std::sin(a)+p.y*std::cos(a));}
inline bool inside(P p,cv::Size size){return std::isfinite(p.x)&&std::isfinite(p.y)&&p.x>=1&&p.y>=1&&p.x<size.width-2&&p.y<size.height-2;}
struct Params {int beam=1,maxCandidates=3,maxScans=4096,maxNodes=24000,maxUnique=500000,maxTotal=4000000;bool gap=true,weak=true,history=false;double maxMs=50;};
struct Seed {P p,t;double evidence=0;int source=0;bool identityProposal=false;};
struct Observation {P p;double u=0,strength=0,width=0,quality=0,intensity=0,asymmetry=0;bool weak=false,border=false;};
struct Scan {int id=0,parent=-1,step=0;P predicted,tangent;double half=0,maxRadius=0,time=0;int sampleCount=0,uniqueAfter=0;std::string phase;std::vector<Observation> candidates,rawCandidates;std::vector<double> profile,response;std::vector<int> children;};
struct Node {int id=0,parent=-1,scan=-1,seed=0,step=0,lastVisible=-1,visibleCount=0,weakCount=0,missingCount=0,reacquisitions=0,pending=0;P p,t;double width=2,strength=0,quality=0,ema=0,missing=0,distance=0,visibleDistance=0,maxMissing=0;bool visible=true,retained=true;std::string decision="root";};
struct End {int node=-1,tipNode=-1;P tip;double progress=0,coverage=0,rank=0;bool terminal=false,ambiguous=true,identityProposal=false;int forwardHits=0,backwardHits=0;std::string reason;};
struct Result {int frame=0,mode=0;P origin,forward;double spacing=0;bool valid=true,incomplete=false;std::string reason="no_current_visible_tip",state="fallback";std::vector<Seed> seeds;std::vector<Scan> scans;std::vector<Node> nodes;std::vector<End> ends;int selected=-1,totalSamples=0,uniquePixels=0,sourceReads=0,beamExpansions=0,branchDeletions=0,mergeDeletions=0,weakObservations=0,missingSteps=0,gapReacquisitions=0,stopAuditSamples=0,seedScans=0,maxActive=0;double totalMs=0,scanMs=0,beamMs=0,terminalMs=0;bool proposedObserved=false;};
struct Sampler {
 const cv::Mat1b& im;Result&r;std::vector<unsigned char> seen;
 Sampler(const cv::Mat1b&i,Result&v):im(i),r(v),seen((size_t(i.cols)*i.rows+7)/8,0){}
 double sample(P p){
  ++r.totalSamples;int x=int(std::floor(p.x)),y=int(std::floor(p.y));if(x<0||y<0||x+1>=im.cols||y+1>=im.rows)return std::numeric_limits<double>::quiet_NaN();
  // Exactly the four original-image addresses read by this scalar bilinear sampler.
  for(int dy=0;dy<2;++dy)for(int dx=0;dx<2;++dx){size_t k=size_t(y+dy)*im.cols+x+dx;unsigned char bit=uchar(1u<<(k&7));if(!(seen[k>>3]&bit)){seen[k>>3]|=bit;++r.uniquePixels;}++r.sourceReads;}
  double fx=p.x-x,fy=p.y-y;return (1-fy)*((1-fx)*im(y,x)+fx*im(y,x+1))+fy*((1-fx)*im(y+1,x)+fx*im(y+1,x+1));
 }
};
struct Tracker {
 Params cfg;Result r;cv::Size initialSize;int frame=0,detail=0;std::string json;Clock::time_point started;std::vector<P> trustedHistory;
 explicit Tracker(cv::Size size):initialSize(size){}
 bool budget(){
  if(r.incomplete)return true;
  if(int(r.scans.size())>=cfg.maxScans)r.reason="scanline_budget";
  else if(int(r.nodes.size())>=cfg.maxNodes)r.reason="node_budget";
  else if(r.uniquePixels>=cfg.maxUnique)r.reason="unique_pixel_budget";
  else if(r.totalSamples>=cfg.maxTotal)r.reason="sampling_budget";
  else if(cfg.maxMs>0&&elapsed(started)>=cfg.maxMs)r.reason="time_budget";
  else return false;
  r.incomplete=true;return true;
 }
 Scan crossSection(Sampler&s,P center,P tangent,double half,int parent,int step,const char*phase){
  auto tick=Clock::now();Scan scan;scan.id=int(r.scans.size());scan.predicted=center;scan.tangent=unit(tangent);scan.half=half;scan.parent=parent;scan.step=step;scan.phase=phase;
  P normal(-scan.tangent.y,scan.tangent.x);double scale=std::clamp(std::sqrt(r.spacing/256.),.6,1.5);std::vector<int> radii;
  for(int v:{1,2,4,8}){int radius=std::clamp(int(std::lround(v*scale)),1,12);if(std::find(radii.begin(),radii.end(),radius)==radii.end())radii.push_back(radius);}
  scan.maxRadius=radii.back();int extent=int(std::ceil(half))+radii.back()+2,count=2*extent+1;std::vector<double>raw(count),smooth(count),score(count,-3),width(count,0),asym(count,0);int before=r.totalSamples;
  for(int j=0;j<count;++j){P q=center+normal*double(j-extent);raw[j]=(.25*s.sample(q-scan.tangent*.8)+.5*s.sample(q)+.25*s.sample(q+scan.tangent*.8));}
  for(int j=1;j+1<count;++j)smooth[j]=.25*raw[j-1]+.5*raw[j]+.25*raw[j+1];
  for(int j=radii.back()+1;j<count-radii.back()-1;++j){
   for(int radius:radii){double left=smooth[j-radius],right=smooth[j+radius],flank=std::min(left,right);if(!std::isfinite(left)||!std::isfinite(right)||!std::isfinite(smooth[j])||flank<75)continue;double value=flank-smooth[j];
    if(value>score[j]){score[j]=value;width[j]=2*radius;asym[j]=std::abs(left-right)/(std::abs(left-smooth[j])+std::abs(right-smooth[j])+1);}
   }
  }
  std::vector<Observation> candidates;
  for(int j=extent-int(std::floor(half));j<=extent+int(std::floor(half));++j){
   if(score[j]<3||score[j]<score[j-1]||score[j]<=score[j+1])continue;
   Observation c;c.u=j-extent;c.p=center+normal*c.u;c.strength=score[j];c.width=width[j];c.intensity=smooth[j];c.asymmetry=asym[j];c.weak=c.strength<8;c.border=std::abs(c.u)>=half-1;
   c.quality=std::min(2.,std::log1p(c.strength)/std::log(16.))-.25*c.asymmetry-.02*std::abs(c.u);
   scan.rawCandidates.push_back(c);if(!cfg.weak&&c.weak)continue;candidates.push_back(c);
  }
  std::stable_sort(candidates.begin(),candidates.end(),[](const Observation&a,const Observation&b){return a.quality>b.quality;});
  for(const auto&c:candidates){bool duplicate=false;for(const auto&old:scan.candidates)if(norm(old.p-c.p)<2)duplicate=true;if(!duplicate&&int(scan.candidates.size())<cfg.maxCandidates)scan.candidates.push_back(c);}
  if(detail>=2){scan.profile=raw;scan.response=score;for(auto&v:scan.profile)if(!std::isfinite(v))v=-1;}
  scan.sampleCount=r.totalSamples-before;scan.uniqueAfter=r.uniquePixels;scan.time=elapsed(tick);r.scanMs+=scan.time;
  if(scan.phase=="origin")++r.seedScans;if(scan.phase=="terminal")r.stopAuditSamples+=scan.sampleCount;
  r.scans.push_back(scan);return scan;
 }
 std::vector<Seed> originSeeds(Sampler&s,bool centralOnly){
  std::vector<Seed> seeds;P normal(-r.forward.y,r.forward.x);double longitudinal=std::clamp(.9*r.spacing,40.,450.),step=std::clamp(r.spacing*.025,4.,12.),half=std::clamp(.10*r.spacing,12.,32.);int stable=0;Observation previous;bool had=false;
  // A bounded origin corridor only, never a distal ROI candidate enumeration.
  for(double along=.12*r.spacing;along<=longitudinal&&!budget();along+=step){
   auto scan=crossSection(s,r.origin+r.forward*along,r.forward,half,-1,0,"origin");
   auto it=std::find_if(scan.candidates.begin(),scan.candidates.end(),[&](const Observation&c){return c.strength>=8&&std::abs(c.u)<half*.8&&c.width<=std::max(8.,.08*r.spacing);});
   if(it==scan.candidates.end()){stable=0;had=false;continue;}
   auto c=*it;if(had&&std::abs((c.p-previous.p).dot(normal))<std::max(3.,step*.4))++stable;else stable=1;
   if(stable>=3){Seed seed;seed.p=c.p;seed.t=unit(c.p-previous.p);if(seed.t.dot(r.forward)<.8)seed.t=r.forward;seed.evidence=c.quality;seed.source=0;seed.identityProposal=std::abs(c.u)<half*.4;bool dup=false;for(auto&old:seeds)if(norm(old.p-seed.p)<step*3)dup=true;if(!dup)seeds.push_back(seed);if(centralOnly||seeds.size()>=3)break;}
   previous=c;had=true;
  }
  return seeds;
 }
 P fittedDirection(const Node&node,P next){
  std::vector<P>points{next};int id=node.id;
  while(id>=0&&points.size()<9){const auto&v=r.nodes[id];if(v.visible)points.push_back(v.p);id=v.parent;}
  if(points.size()<4||norm(points.front()-points.back())<6)return node.t;
  P mean;for(P p:points)mean+=p;mean*=1./points.size();double xx=0,xy=0,yy=0;
  for(P p:points){p-=mean;xx+=p.x*p.x;xy+=p.x*p.y;yy+=p.y*p.y;}
  double a=.5*std::atan2(2*xy,xx-yy);P fit(std::cos(a),std::sin(a));if(fit.dot(node.t)<0)fit=-fit;
  double change=std::clamp(wrap(angle(fit)-angle(node.t)),-.14,.14);P t=rotate(node.t,.4*change);return t.dot(r.forward)>.25?t:node.t;
 }
 void finishNode(int id,const char*reason){
  const auto&node=r.nodes[id];if(node.lastVisible<0)return;const auto&tip=r.nodes[node.lastVisible];End end;end.node=id;end.tipNode=tip.id;end.tip=tip.p;end.progress=(tip.p-r.origin).dot(r.forward);end.coverage=node.distance>0?node.visibleDistance/node.distance:0;end.rank=node.ema;end.reason=reason;end.identityProposal=r.seeds[node.seed].identityProposal;r.ends.push_back(end);
 }
 void track(Sampler&s){
  std::vector<int>active;
  for(size_t i=0;i<r.seeds.size();++i){Node n;n.id=int(r.nodes.size());n.seed=int(i);n.p=r.seeds[i].p;n.t=unit(r.seeds[i].t);n.visible=false;n.lastVisible=-1;n.visibleCount=0;n.ema=r.seeds[i].evidence;r.nodes.push_back(n);active.push_back(n.id);}
  while(!active.empty()&&!budget()){
   r.maxActive=std::max(r.maxActive,int(active.size()));std::vector<int>expanded;
   for(int id:active){
    if(budget())break;Node previous=r.nodes[id];double step=std::clamp(r.spacing/160.,1.5,3.);if(previous.missing>0||previous.strength<8)step=1.;double half=std::clamp(8.+previous.width*.5+previous.missing*.18,8.,24.);P pred=previous.p+previous.t*step;
    if(!inside(pred,s.im.size())){finishNode(id,"image_boundary");continue;}
    if((pred-r.origin).dot(r.forward)>1.5*std::max(s.im.cols,s.im.rows)){r.incomplete=true;r.reason="forward_distance_budget";finishNode(id,"search_incomplete");break;}
    auto scan=crossSection(s,pred,previous.t,half,id,previous.step+1,"tracking");auto start=Clock::now();
    int branches=0;
    for(size_t j=0;j<scan.candidates.size();++j){const auto&c=scan.candidates[j];
     if(std::abs(c.u)>std::max(4.,step*1.8+previous.missing*.15)){++r.branchDeletions;continue;}
     if(previous.missing>0&&c.asymmetry>.8){++r.branchDeletions;continue;}
     Node n=previous;n.id=int(r.nodes.size());n.parent=id;n.scan=scan.id;n.step=previous.step+1;n.p=c.p;n.t=fittedDirection(previous,c.p);n.width=.8*previous.width+.2*c.width;n.strength=c.strength;n.quality=c.quality;n.visible=true;n.visibleCount++;n.weakCount+=c.weak;n.missing=0;n.distance+=norm(c.p-previous.p);n.visibleDistance+=previous.visible?norm(c.p-previous.p):0;n.lastVisible=n.id;
     n.pending=previous.missing>0?2:std::max(0,previous.pending-1);if(previous.pending==1&&n.pending==0){n.reacquisitions++;r.gapReacquisitions++;}
     n.ema=.85*previous.ema+.15*(c.quality-.08*std::abs(c.u)-.3*std::abs(wrap(angle(n.t)-angle(previous.t))));n.decision=c.weak?"weak_observation":"strong_observation";
     r.nodes.push_back(n);expanded.push_back(n.id);r.scans[scan.id].children.push_back(n.id);++r.beamExpansions;if(c.weak)++r.weakObservations;++branches;
     if(cfg.beam==1)break;
    }
    double gapLimit=cfg.gap?std::clamp(.04*r.spacing+4*previous.width,48.,64.):0.;
    if((branches==0||cfg.beam>1)&&previous.missing+step<=gapLimit){Node n=previous;n.id=int(r.nodes.size());n.parent=id;n.scan=scan.id;n.step++;n.p=pred;n.visible=false;n.missing+=step;n.maxMissing=std::max(n.maxMissing,n.missing);n.distance+=step;n.missingCount++;n.ema=previous.ema-.045*step;n.decision="inferred_gap";r.nodes.push_back(n);expanded.push_back(n.id);r.scans[scan.id].children.push_back(n.id);++r.missingSteps;++r.beamExpansions;}
    else if(branches==0)finishNode(id,cfg.gap?"gap_search_exhausted":"first_missing_no_gap");
    r.beamMs+=elapsed(start);
   }
   auto start=Clock::now();std::stable_sort(expanded.begin(),expanded.end(),[&](int a,int b){auto score=[&](int id){auto&n=r.nodes[id];return n.ema+.5*(n.visibleCount/double(n.step+1))-.025*n.missing;};return score(a)>score(b);});
   std::vector<int>next;
   for(int id:expanded){auto&n=r.nodes[id];bool dup=false;for(int old:next){auto&o=r.nodes[old];if(n.seed==o.seed&&norm(n.p-o.p)<2&&n.t.dot(o.t)>.985&&n.visible==o.visible){dup=true;break;}}
    if(dup){n.retained=false;n.decision+="|merged";++r.mergeDeletions;}
    else if(int(next.size())<cfg.beam)next.push_back(id);
    else{n.retained=false;n.decision+="|beam_pruned";++r.branchDeletions;}
   }
   active=next;r.beamMs+=elapsed(start);
  }
  if(r.incomplete)for(int id:active)finishNode(id,"search_incomplete");
 }
 void terminalAudit(Sampler&s){
  auto start=Clock::now();double scanBefore=r.scanMs;std::stable_sort(r.ends.begin(),r.ends.end(),[](const End&a,const End&b){return a.progress>b.progress;});
  if(r.ends.size()>12)r.ends.resize(12);
  for(auto&end:r.ends){Node tip=r.nodes[end.tipNode];int at=tip.id,back=0,seen=0;
   while(at>=0&&seen<8){auto&n=r.nodes[at];if(n.visible){++seen;if(n.strength>=3)++back;}at=n.parent;}end.backwardHits=back;
   if(!r.incomplete&&end.reason=="gap_search_exhausted"&&tip.pending==0&&tip.visibleCount>=8&&end.coverage>=.5){
    for(double d:{4.,12.,24.,40.}){if(budget())break;auto scan=crossSection(s,tip.p+tip.t*d,tip.t,12.,tip.id,tip.step+1,"terminal");for(auto&c:scan.candidates)if(std::abs(c.u)<=6&&c.strength>=3)++end.forwardHits;}
    end.terminal=!r.incomplete&&back>=6&&end.forwardHits==0;end.ambiguous=!end.terminal;end.reason=end.terminal?"local_stop_supported_identity_unverified":"terminal_ambiguous";
   }
  }
  // Choose actual visible progress among locally supported paths, never gap points.
  for(size_t i=0;i<r.ends.size();++i){auto&e=r.ends[i];auto&n=r.nodes[e.tipNode];if(n.visibleCount>=8&&e.coverage>=.5){r.selected=int(i);break;}}
  if(r.selected<0&&!r.ends.empty())r.selected=0;
  if(r.selected>=0){auto&e=r.ends[r.selected];r.proposedObserved=e.terminal&&e.identityProposal&&!r.incomplete;if(!r.incomplete)r.reason=e.reason;}
  // Deliberately separate a geometric acquisition proposal from a validated identity.
  // G3 must supply a successful independent identity certificate before history writes.
  // No such certificate exists in this research build; do not claim safety success.
  r.terminalMs=std::max(0.,elapsed(start)-(r.scanMs-scanBefore));
 }
 void process(const cv::Mat1b&im,std::array<P,2>a,const std::vector<Seed>*diagnostic){
  started=Clock::now();r={};r.frame=++frame;r.mode=diagnostic?1:0;
  if(im.size()!=initialSize||!inside(a[0],im.size())||!inside(a[1],im.size())||a[0].y>=a[1].y||norm(a[1]-a[0])<16){r.valid=false;r.incomplete=true;r.reason="invalid_geometry";r.totalMs=elapsed(started);return;}
  r.origin=(a[0]+a[1])*.5;r.spacing=norm(a[1]-a[0]);P across=unit(a[1]-a[0]);r.forward=P(across.y,-across.x);Sampler sampler(im,r);
  if(diagnostic){for(auto seed:*diagnostic)if(inside(seed.p,im.size())&&norm(seed.t)>.5&&unit(seed.t).dot(r.forward)>.25){seed.t=unit(seed.t);seed.identityProposal=false;r.seeds.push_back(seed);}}
  else r.seeds=originSeeds(sampler,false);
  if(r.seeds.empty()){if(!r.incomplete)r.reason="seed_missing";}else {track(sampler);terminalAudit(sampler);}
  r.totalMs=elapsed(started);
 }
};
}

