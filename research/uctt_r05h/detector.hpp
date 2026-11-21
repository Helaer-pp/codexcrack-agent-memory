#pragma once
#include "reference.hpp"
#include <set>
namespace r05h {
struct Stop {int node=-1;P tip;double before=0,after=0,current=0,identity=0,terminal=0,score=0,reference=0,gap=0;bool boundary=false;std::string cause;ReferenceEvidence ref;};
struct CrackResult {std::string status="UNOBSERVED",reason="no_current_support";P working,observed;bool hasWorking=false,hasObserved=false,searchComplete=true,historyWritten=false;double confidence=0,rootQuality=0,rootMs=0,trackMs=0,terminalMs=0,referenceMs=0,stateMs=0,totalMs=0;int historyFrame=0,selected=-1;std::vector<int>path;std::vector<Stop>stops;ReferenceEvidence navigation;};
class Pipeline {
public:
 Tracker core;cv::Mat1b reference,historyImage;P referenceOrigin,historyOrigin;std::vector<P>historyPath;int historyFrame=0;CrackResult result;std::string json;bool notch=false;P notchEnd;
 Pipeline(const cv::Mat1b&ref,std::array<P,2>a):core(ref.size()),reference(ref.clone()),referenceOrigin((a[0]+a[1])*.5){}
 std::vector<int> chain(int id){std::vector<int> p;while(id>=0){p.push_back(id);id=core.r.nodes[id].parent;}std::reverse(p.begin(),p.end());return p;}
 void roots(Sampler&s){auto&r=core.r;P normal(-r.forward.y,r.forward.x);double stride=std::clamp(r.spacing*.012,2.,6.),half=std::clamp(.16*r.spacing,16.,70.);double last=-1;int broadRun=0,bestRun=0;P lastPoint;
  // Physical notch: connected broad dark material deficit, not three strong dark valleys.
  for(double d=-.08*r.spacing;d<.9*r.spacing;d+=stride){P c=r.origin+r.forward*d;double center=s.sample(c);int width=0;double sum=0;for(double u=-half;u<=half;u+=2){double v=s.sample(c+normal*u);if(std::isfinite(v)&&v<70){++width;sum+=u;}}
   if(width*2>=std::max(8.,.045*r.spacing)&&std::isfinite(center)&&center<90){++broadRun;if(broadRun>=3){last=d;lastPoint=c+normal*(sum/std::max(1,width));bestRun=broadRun;}}else broadRun=0;
  }
  notch=last>=0&&bestRun>=3;notchEnd=notch?lastPoint:r.origin+r.forward*(.12*r.spacing);result.rootQuality=notch?1:0;
  struct Candidate{Seed seed;double rank;};std::vector<Candidate> pool;
  double start=notch?last+stride:.12*r.spacing,limit=notch?start+std::max(28.,.16*r.spacing):.9*r.spacing;
  for(double d=start;d<=limit;d+=std::max(2.,stride)){P c=notch?notchEnd+r.forward*(d-last):r.origin+r.forward*d;auto sc=core.crossSection(s,c,r.forward,std::clamp(.12*r.spacing,16.,48.),-1,0,"origin");
   for(auto&o:sc.candidates){Seed z;z.p=o.p;z.t=r.forward;z.evidence=o.quality;z.identityProposal=notch;z.source=0;double rank=o.quality-.02*std::abs(o.u)-.012*(d-start);pool.push_back({z,rank});}
  }
  std::stable_sort(pool.begin(),pool.end(),[](auto&a,auto&b){return a.rank>b.rank;});
  for(auto&c:pool){bool duplicate=false;for(auto&z:r.seeds)if(norm(z.p-c.seed.p)<8)duplicate=true;if(!duplicate)r.seeds.push_back(c.seed);if(r.seeds.size()==3)break;}
 }
 double forwardSupport(Sampler&s,const Node&n,double before,bool&boundary){int hits=0,total=0;double scale=std::clamp(std::sqrt(core.r.spacing/256.),.75,1.5);for(double d=3;d<=50*scale;d+=4*scale){P p=n.p+n.t*d;if(!inside(p,s.im.size())){boundary=true;continue;}auto sc=core.crossSection(s,p,n.t,8,n.id,n.step,"terminal");bool hit=false;for(auto&o:sc.candidates)if(std::abs(o.u)<=std::max(3.,n.width*.35)&&o.strength>=std::max(3.,before*.35))hit=true;hits+=hit;++total;}return total?double(hits)/total:1.;}
 void stops(Sampler&s,int variant){auto&r=core.r;std::map<int,std::string> ids;
  for(auto&n:r.nodes){if(n.parent<0)continue;auto&p=r.nodes[n.parent];if(p.visible&&(!n.visible||n.strength<p.strength*.5))ids[p.id]=!n.visible?"support_gap":"contrast_drop";}
  for(auto&e:r.ends)if(e.tipNode>=0)ids[e.tipNode]=e.reason;
  // Persistent STOPs survive beam pruning and are never overwritten by further exploration.
  for(auto&entry:ids){auto&n=r.nodes[entry.first];if(n.visibleCount<2)continue;Stop q;q.node=n.id;q.tip=n.p;q.cause=entry.second;q.gap=n.maxMissing;
   int at=n.id,count=0;double support=0,travel=0;while(at>=0&&travel<24){auto&v=r.nodes[at];if(v.visible){support+=v.strength;++count;}if(v.parent>=0)travel+=norm(v.p-r.nodes[v.parent].p);at=v.parent;}q.before=count?support/count:0;
   q.current=std::min(1.,std::log1p(q.before)/std::log(33.));q.identity=r.seeds[n.seed].identityProposal?1.:0.;q.score=q.current+.4*q.identity;result.stops.push_back(q);
  }
  // Co-located STOPs are equivalent; retain the best current-supported prefix.
  std::stable_sort(result.stops.begin(),result.stops.end(),[](auto&a,auto&b){return a.score>b.score;});std::vector<Stop> unique;
  for(auto&q:result.stops){bool dup=false;for(auto&v:unique)if(norm(q.tip-v.tip)<4)dup=true;if(!dup)unique.push_back(q);}result.stops=unique;
  // Audit every preserved STOP, with explicit incomplete status if the research budget runs out.
  for(auto&q:result.stops){if(elapsed(core.started)>450){r.incomplete=true;r.reason="terminal_budget";q.cause+="|unaudited_budget";q.score=-100;continue;}auto&n=r.nodes[q.node];q.after=forwardSupport(s,n,q.before,q.boundary);q.terminal=1-q.after;
   double visibleFraction=n.distance>0?n.visibleDistance/n.distance:0;
   q.score=1.2*q.current+1.8*q.terminal+.6*q.identity+.3*std::min(1.,n.visibleDistance/24.)-.6*(1-visibleFraction)-.25*std::min(1.,n.maxMissing/48.);
   if(q.boundary||q.cause=="image_boundary")q.score-=2;
  }
  std::stable_sort(result.stops.begin(),result.stops.end(),[](auto&a,auto&b){return a.score>b.score;});
  if(variant!=1)for(size_t i=0;i<std::min(size_t(12),result.stops.size());++i){auto&q=result.stops[i];auto&n=r.nodes[q.node];if(q.score<0)continue;q.ref=compareReference(s.im,reference,q.tip,n.t,referenceOrigin-r.origin,r.spacing,n.width,"fixed");result.referenceMs+=q.ref.ms;q.reference=q.ref.bonus;
   // Existing true crack is neutral; old texture after a gap weakens the reassociation.
   if(q.ref.classification=="OLD_TEXTURE"&&n.maxMissing>8)q.reference=-.65;
   q.score+=.8*q.reference;
  }
  if(result.stops.empty())return;
  std::stable_sort(result.stops.begin(),result.stops.end(),[](auto&a,auto&b){return a.score>b.score;});result.selected=0;
  if(variant==2){double far=-1e30;for(size_t i=0;i<result.stops.size();++i){double d=(result.stops[i].tip-r.origin).dot(r.forward);if(d>far){far=d;result.selected=int(i);}}}
  auto&q=result.stops[result.selected];auto&n=r.nodes[q.node];result.path=chain(n.id);result.working=q.tip;result.hasWorking=true;
  // Fine current-only scan around the selected end. No extrapolated point is accepted.
  double furthest=0;for(double d=-2;d<=3;d+=.5){auto sc=core.crossSection(s,q.tip+n.t*d,n.t,3,n.id,n.step,"terminal_fine");for(auto&o:sc.candidates)if(std::abs(o.u)<=2&&o.strength>=std::max(3.,q.before*.3)&&d>furthest){result.working=o.p;furthest=d;}}
  double margin=10;for(size_t i=0;i<result.stops.size();++i)if(int(i)!=result.selected&&norm(result.stops[i].tip-q.tip)>12){margin=q.score-result.stops[i].score;break;}
  bool identity=q.identity>.5;bool terminal=q.after<=.2&&!q.boundary;bool current=n.visibleCount>=5&&n.visibleDistance>=10&&q.before>=3;
  result.confidence=std::clamp(.3*q.current+.3*q.terminal+.3*q.identity+.1*std::clamp(margin,0.,1.),0.,1.);
  result.hasObserved=identity&&terminal&&current&&margin>.08&&!r.incomplete;
  result.status=result.hasObserved?"OBSERVED":"TENTATIVE";result.reason=r.incomplete?r.reason:!identity?"origin_identity_unverified":!terminal?"continuation_or_boundary":margin<=.08?"competing_stops":"current_identity_terminal_supported";
  if(result.hasObserved)result.observed=result.working;
 }
 CrackResult process(const cv::Mat1b&im,const cv::Point2f&p1,const cv::Point2f&p2,int variant=0){
  core.started=Clock::now();core.r={};core.r.frame=++core.frame;result={};notch=false;auto&r=core.r;core.cfg={};core.cfg.beam=2;core.cfg.maxScans=18000;core.cfg.maxNodes=100000;core.cfg.maxUnique=4000000;core.cfg.maxTotal=32000000;core.cfg.maxMs=350;
  P a(p1.x,p1.y),b(p2.x,p2.y);if(im.size()!=core.initialSize||!inside(a,im.size())||!inside(b,im.size())||a.y>=b.y||norm(b-a)<16){r.incomplete=true;r.valid=false;r.reason="invalid_geometry";result.reason=r.reason;result.searchComplete=false;result.totalMs=elapsed(core.started);return result;}
  r.origin=(a+b)*.5;r.spacing=norm(b-a);P across=unit(b-a);r.forward={across.y,-across.x};Sampler sampler(im,r);auto tick=Clock::now();roots(sampler);result.rootMs=elapsed(tick);
  if(variant!=3&&!historyPath.empty()){P predicted=historyPath.front()+r.origin-historyOrigin;result.navigation=compareReference(im,historyImage,predicted,r.forward,historyOrigin-r.origin,r.spacing,4,"trusted_past");result.referenceMs+=result.navigation.ms;
   if(result.navigation.state=="VALID"){P mapped=historyPath.front()-result.navigation.shift;auto sc=core.crossSection(sampler,mapped,r.forward,8,-1,0,"history_revalidation");if(!sc.candidates.empty()){Seed z;z.p=sc.candidates[0].p;z.t=r.forward;z.evidence=sc.candidates[0].quality;z.source=2;z.identityProposal=true;r.seeds.insert(r.seeds.begin(),z);if(r.seeds.size()>3)r.seeds.resize(3);}}
  }
  tick=Clock::now();if(!r.seeds.empty())core.track(sampler);result.trackMs=elapsed(tick);tick=Clock::now();stops(sampler,variant);result.terminalMs=elapsed(tick)-result.referenceMs+result.navigation.ms;tick=Clock::now();
  if(!result.hasWorking&&result.navigation.state=="VALID"&&!historyPath.empty()){result.working=historyPath.back()-result.navigation.shift;result.hasWorking=true;result.status="PREDICTED";result.reason="past_trusted_material_prediction_only";}
  result.historyFrame=historyFrame;
  if(result.hasObserved&&variant!=3){historyPath.clear();for(int id:result.path)if(r.nodes[id].visible)historyPath.push_back(r.nodes[id].p);historyImage=im.clone();historyOrigin=r.origin;historyFrame=r.frame;result.historyWritten=true;}
  result.searchComplete=!r.incomplete;result.stateMs=elapsed(tick);result.totalMs=elapsed(core.started);return result;
 }
};
}
