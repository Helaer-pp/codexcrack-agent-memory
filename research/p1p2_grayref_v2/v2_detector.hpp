#pragma once
#include "evidence.hpp"
#include "json_value.hpp"
#include <set>
#include <tuple>
#include <cstdint>
namespace v2 {
using namespace grayrefv2base;
using I=long long;
inline I quant(double v){return v>=0?I(std::floor(v*1e6+.5)):-I(std::floor(-v*1e6+.5));}
inline I divround(I n,I d){return n>=0?(2*n+d)/(2*d):-((2*(-n)+d)/(2*d));}
inline I floordiv(I n,I d){return n>=0?n/d:-((-n+d-1)/d);}
inline I ceildiv(I n,I d){return -floordiv(-n,d);}
inline I prediction(const std::vector<cv::Point>&obs,int x,int y0){
 if(obs.empty())return I(y0)*1024;int n=std::min(12,int(obs.size()));auto last=obs.back();if(n<5)return I(last.y)*1024;
 I sx=0,sy=0,sxy=0,sxx=0;for(size_t i=obs.size()-n;i<obs.size();++i){auto p=obs[i];sx+=p.x;sy+=p.y;sxy+=I(p.x)*p.y;sxx+=I(p.x)*p.x;}I num=n*sxy-sx*sy,den=n*sxx-sx*sx;if(!den)return I(last.y)*1024;if(5*std::abs(num)>den){num=num>0?1:-1;den=5;}return I(last.y)*1024+divround(num*(x-last.x)*1024,den);
}
inline J point(cv::Point p){return J::a({p.x,p.y});}
inline J point(P p){return J::a({p.x,p.y});}
const char* modes[]={"V2_NUMERIC_CONTROL","V2_ORIGIN_ONLY","V2_REF_ONLY","V2_COMBINED","V2_TERMINAL"};
const char* statuses[]={"REFERENCE_UNAVAILABLE","REFERENCE_UNRELIABLE","EXISTING_DARK_OR_NO_INCREMENT","NEW_DARK_SUPPORTED"};
struct Quality {int x0=0,x1=0,code=0;double quality=0;J data;};
struct Pixel {double valley,delta;bool valid;I strength;int status;bool accept;};
struct Row {int x,y;bool hit;int gap;I predicted;int low,high;double valley,delta;int status;I strength,merit;J json()const{return J::a({x,y,hit,gap,predicted,low,high,valley,delta,status,strength,merit});}};
using Trace=std::vector<Row>;
inline J tracejson(const Trace&t){J out=J::a();for(auto&r:t)out.push(r.json());return out;}
struct Seed {int id=0,x=0,y=0,rank=0,shortObserved=0,maxRun=0;I initial=0,shortScore=0;double valley=0,delta=0,connection=0;int status=0;bool edge=false,single=false;std::string reason="BUDGET";
 J json()const{J r=J::o({{"id",id},{"x",x},{"y",y},{"initial_score",initial},{"reason",reason},{"rank",rank},{"short_score",shortScore}});if(!single){r["valley"]=valley;r["delta"]=delta;r["reference_status"]=status;r["edge_risk"]=edge;r["connection"]=connection;r["short_observed"]=shortObserved;r["max_run"]=maxRun;}return r;}
};
struct Path {Seed seed;Trace trace;J json()const{return J::o({{"id",seed.id},{"seed",J::a({seed.x,seed.y})},{"trace",tracejson(trace)},{"short_score",seed.shortScore}});}};
struct Stop {int index,x,y;I score;double before,after;bool compatible,selected=false;J json()const{return J::o({{"index",index},{"x",x},{"y",y},{"score",score},{"before_density",before},{"after_density",after},{"compatible_recapture",compatible},{"selected",selected}});}};
class Detector {
public:
 EvidenceV2 base;cv::Mat1b current;std::vector<Quality> qualities;J output;std::string json;
 J geometry(){auto&r=base.result;return J::o({{"xleft",r.xleft},{"xr",r.xright},{"upper",r.upper},{"lower",r.lower},{"xa",r.xa},{"ya",r.ya},{"xb",r.xb},{"yb",r.yb}});}
 void quality(){
  qualities.clear();auto&g=base.result;auto&ar=base.arrays[0];bool same=cv::countNonZero(base.reference!=current)==0;
  for(int x=g.xleft;x<g.xright;x+=64){Quality q;q.x0=x;q.x1=std::min(x+64,g.xright);J sides=J::a();bool availableAll=true;q.quality=1;
   for(bool top:{true,false}){int y0=top?g.upper+14:g.lower-30,y1=y0+16;I n=0,sc=0,sr=0,scc=0,srr=0,scr=0,bright=0;bool inside=true;
    for(int y=y0;y<y1;++y)for(int xx=x;xx<q.x1;++xx){I c=current(y,xx),r=I(ar(y-g.ya,xx-g.xa));++n;sc+=c;sr+=r;scc+=c*c;srr+=r*r;scr+=c*r;bright+=c>135&&r>135;auto p1=g.points[0],p2=g.points[1];float alpha=std::clamp((float(y)-float(p1.y))/float(p2.y-p1.y),0.f,1.f);float dx=(1-alpha)*float(g.translations[0].x)+alpha*float(g.translations[1].x),dy=(1-alpha)*float(g.translations[0].y)+alpha*float(g.translations[1].y);float mx=float(xx)-dx,my=float(y)-dy;inside=inside&&mx>=0&&mx<current.cols-1&&my>=0&&my<current.rows-1;}
    I cc=n*scc-sc*sc,rr=n*srr-sr*sr,cr=n*scr-sc*sr;double stdc=std::sqrt(double(std::max(I(0),cc)))/std::max(I(1),n),stdr=std::sqrt(double(std::max(I(0),rr)))/std::max(I(1),n),ncc=cc>0&&rr>0?double(cr)/std::sqrt(double(cc)*double(rr)):0.,fraction=n?double(bright)/n:0.;bool available=n>=64&&stdc>=2&&stdr>=2&&fraction>=.5&&inside&&!same;availableAll=availableAll&&available;double corr=quant(ncc)/1e6;q.quality=std::min(q.quality,corr);sides.push(J::o({{"side",top?"upper":"lower"},{"bounds",J::a({x,y0,q.x1,y1})},{"n",n},{"ncc",corr},{"std_current",quant(stdc)/1e6},{"std_reference",quant(stdr)/1e6},{"bright_fraction",quant(fraction)/1e6},{"available",available}}));
   }
   q.code=!availableAll?0:q.quality>=.75?2:1;q.data=J::o({{"x0",q.x0},{"x1",q.x1},{"code",q.code},{"quality",q.quality},{"reason",same?"SAME_IMAGE_NO_INCREMENT":"QUALITY_CHECK"},{"sides",sides}});qualities.push_back(q);
  }
 }
 Pixel pixel(int x,int y,bool m2){auto&g=base.result;int i=y-g.ya,j=x-g.xa;double v=base.arrays[3](i,j),d=base.arrays[4](i,j);bool valid=base.arrays[6](i,j)!=0;auto&q=qualities[std::clamp((x-g.xleft)/64,0,int(qualities.size())-1)];int status=q.code==2&&d>=10?3:q.code;double strength=m2?(status==3?v*(1+.25*std::min(std::max(d,0.),40.)/40*std::max(0.,q.quality)):v):double(float(std::sqrt(std::max(v,0.)*std::max(d,0.))));return {v,d,valid,quant(strength),status,valid&&v>=10&&(m2||d>=10)};}
 I seedscore(int x,int y,bool m2,bool currentOnly=false){auto p=pixel(x,y,m2);auto&g=base.result;double center=(g.points[0].y+g.points[1].y)/2.,sigma=std::max(12.,(g.lower-g.upper)*.23),z=(y-center)/sigma,value=currentOnly?std::max(p.valley,0.):p.strength/1e6;return p.valid?quant(value*std::exp(-.5*z*z)):0;}
 Seed initial(bool m2){auto&g=base.result;Seed c;c.x=g.xleft+6;c.y=g.upper+7;c.initial=-1;c.single=true;for(int y=g.upper+7;y<g.lower-7;++y){I s=seedscore(c.x,y,m2);if(s>c.initial){c.initial=s;c.y=y;}}c.reason=c.initial>0?"SINGLE_COLUMN":"ZERO_INIT_GUARD";c.rank=1;return c;}
 Trace walk(const Seed&seed,bool m2,int limit=0){auto&g=base.result;std::vector<cv::Point> obs;Trace trace;int gap=0,end=limit?std::min(g.xright,seed.x+limit):g.xright;
  for(int x=seed.x;x<end;++x){I pred=prediction(obs,x,seed.y);int low=std::max(g.upper+3,int(floordiv(pred-7*1024,1024))),high=std::min(g.lower-3,int(ceildiv(pred+7*1024,1024))+1);bool has=false,any=false;Row best{},fallback{};I bestMerit=std::numeric_limits<I>::min(),anyMerit=bestMerit;
   for(int y=low;y<high;++y){auto p=pixel(x,y,m2);I merit=p.strength-divround(550000*std::abs(I(y)*1024-pred),1024);Row row{x,y,p.accept,0,pred,low,high,p.valley,p.delta,p.status,p.strength,merit};if(!any||merit>anyMerit){any=true;anyMerit=merit;fallback=row;}if(p.accept&&(!has||merit>bestMerit)){has=true;bestMerit=merit;best=row;}}
   if(!any)break;Row r=has?best:fallback;r.hit=has;if(has){obs.emplace_back(x,r.y);gap=0;}else ++gap;r.gap=gap;trace.push_back(r);if(gap>20)break;
  }return trace;
 }
 double connection(int x,int y){auto&g=base.result;int total=0,hits=0;for(int xx=x-1;xx>g.xleft+5;--xx){int bestY=std::max(g.upper+3,y-3);I best=-2;for(int yy=std::max(g.upper+3,y-3);yy<std::min(g.lower-3,y+4);++yy){auto p=pixel(xx,yy,true);I val=p.valid?quant(p.valley):-1;if(val>best){best=val;bestY=yy;}}auto p=pixel(xx,bestY,true);++total;if(p.valid&&p.valley>=10){y=bestY;++hits;}}return total?double(hits)/total:1.;}
 std::pair<std::vector<Seed>,std::vector<int>> seeds(bool m2){auto&g=base.result;int start=g.xleft+6,width=std::min(96,std::max(24,int(std::floor(.35*(g.lower-g.upper)+.5))));std::set<std::pair<int,int>> points;
  for(int x=start;x<std::min(start+width+1,g.xright);x+=4)for(int y=g.upper+7;y<g.lower-7;++y){auto p=pixel(x,y,true);if(p.valid&&p.valley>=10&&p.valley>=base.arrays[3](y-g.ya-1,x-g.xa)&&p.valley>base.arrays[3](y-g.ya+1,x-g.xa))points.emplace(x,y);}
  for(bool ref:{false,true}){auto c=initial(ref);if(pixel(c.x,c.y,true).accept)points.emplace(c.x,c.y);}
  std::vector<Seed> candidates;for(auto xy:points){Seed c;c.id=int(candidates.size());c.x=xy.first;c.y=xy.second;auto p=pixel(c.x,c.y,m2);c.initial=seedscore(c.x,c.y,true,true);c.valley=p.valley;c.delta=p.delta;c.status=p.status;c.edge=base.arrays[1](c.y-g.ya,c.x-g.xa)<80;candidates.push_back(c);}
  std::vector<int> order;for(int i=0;i<int(candidates.size());++i)order.push_back(i);std::sort(order.begin(),order.end(),[&](int i,int j){auto&a=candidates[i];auto&b=candidates[j];return std::make_tuple(-a.initial,a.x,a.y)<std::make_tuple(-b.initial,b.x,b.y);});std::vector<int> kept;
  for(int id:order){auto&c=candidates[id];bool duplicate=false;for(int k:kept){auto&b=candidates[k];if(std::abs(c.x-b.x)<=8&&std::abs(c.y-b.y)<=6){duplicate=true;break;}}if(duplicate){c.reason="NMS_DUPLICATE";continue;}if(kept.size()>=24)continue;kept.push_back(id);auto t=walk(c,m2,32);std::vector<Row> obs;int run=0,longest=0;double strength=0,curve=0;for(auto&r:t){run=r.hit?run+1:0;longest=std::max(longest,run);if(r.hit){obs.push_back(r);strength+=std::min(r.valley,30.);}}
   double connect=connection(c.x,c.y),density=double(obs.size())/std::max(size_t(1),t.size());strength/=std::max(size_t(1),obs.size());strength/=30;for(int i=2;i<int(obs.size());++i)curve+=std::abs(obs[i].y-2*obs[i-1].y+obs[i-2].y);curve/=std::max(1,int(obs.size())-2);c.shortScore=quant(70*density+15*strength+15*connect-2*curve);c.connection=quant(connect)/1e6;c.shortObserved=int(obs.size());c.maxRun=longest;c.reason=obs.size()>=8&&longest>=4&&connect>=.5?"SHORT_SUPPORTED":"SHORT_OR_CONNECTION_UNSUPPORTED";
  }
  std::vector<int> ranked;for(int id:kept)if(candidates[id].reason=="SHORT_SUPPORTED")ranked.push_back(id);std::sort(ranked.begin(),ranked.end(),[&](int i,int j){auto&a=candidates[i];auto&b=candidates[j];return std::make_tuple(-a.shortScore,a.x,a.y)<std::make_tuple(-b.shortScore,b.x,b.y);});std::vector<int> chosen;int rank=0;
  for(int id:ranked){auto&c=candidates[id];c.rank=++rank;bool duplicate=false;for(int k:chosen)if(std::abs(c.y-candidates[k].y)<=7)duplicate=true;if(duplicate){c.reason="SAME_ORIGIN_BAND";continue;}if(chosen.size()<3){chosen.push_back(id);c.reason="PATH_HYPOTHESIS";}else c.reason="PATH_BUDGET";}
  return {candidates,chosen};
 }
 std::vector<Stop> stops(const Trace&t){std::vector<Stop> out;int last=-1;for(int i=0;i<int(t.size());++i)if(t[i].hit)last=i;
  for(int i=0;i<int(t.size());++i){if(!t[i].hit||(i!=last&&t[i+1].hit))continue;int hits=0,afterhits=0,next=-1;double pv=0,av=0;for(int j=std::max(0,i-7);j<=i;++j)if(t[j].hit){++hits;pv+=std::max(0.,t[j].valley);}for(int j=i+1;j<std::min(int(t.size()),i+9);++j){if(t[j].hit){++afterhits;if(next<0)next=j;}av+=std::max(0.,t[j].valley);}pv/=std::max(1,hits);av/=8;double pre=hits/8.,post=afterhits/8.;bool compatible=post>=.75&&next>=0&&std::abs(I(t[next].y)*1024-t[next].predicted)<=3*1024;I score=quant(2*(1-post)+pre+std::max(0.,(pv-av)/std::max(10.,pv))-(compatible?2:0));out.push_back({i,t[i].x,t[i].y,score,pre,post,compatible,false});}
  if(!out.empty()){int best=0;for(int i=1;i<int(out.size());++i)if(out[i].score>out[best].score)best=i;out[best].selected=true;}return out;
 }
 J mode(int index){auto start=Clock::now();bool m1=index==1||index==3||index==4,m2=index>=2;std::vector<Seed> candidates;std::vector<int> chosen;bool ambiguous=false;
  if(m1){auto pair=seeds(m2);candidates=pair.first;chosen=pair.second;if(chosen.size()>1)ambiguous=candidates[chosen[0]].shortScore-candidates[chosen[1]].shortScore<=3000000;}
  else{candidates.push_back(initial(m2));if(candidates[0].initial>0)chosen.push_back(0);}
  std::vector<Path> paths;for(int id:chosen)paths.push_back({candidates[id],walk(candidates[id],m2)});Trace trace=paths.empty()?Trace{}:paths[0].trace;auto terminal=index==4?stops(trace):std::vector<Stop>{};std::string stop=paths.empty()?"NO_SUPPORTED_ORIGIN":!trace.empty()&&trace.back().gap>20?"GAP_LIMIT":"RIGHT_BOUNDARY";
  if(!terminal.empty()){for(auto&s:terminal)if(s.selected){trace.resize(s.index+1);break;}stop="COMPETING_STOP_EVIDENCE";}
  std::vector<cv::Point> obs;int missing=0;std::array<int,4> counts{};for(auto&r:trace){if(r.hit)obs.emplace_back(r.x,r.y);else ++missing;++counts[r.status];}
  std::string state=obs.empty()?"NO_TIP":obs.size()<8||ambiguous?"UNCERTAIN":obs.back().x>=base.result.xright-2?"ROI_LIMITED":"PROVISIONAL_OBSERVED";if(obs.empty()&&!candidates.empty()&&m1)state="UNCERTAIN";J seedJson=J::a(),pathJson=J::a(),stopJson=J::a(),countJson=J::o();for(auto&c:candidates)seedJson.push(c.json());for(auto&p:paths)pathJson.push(p.json());for(auto&s:terminal)stopJson.push(s.json());for(int i=0;i<4;++i)countJson[statuses[i]]=counts[i];
  return J::o({{"mode",modes[index]},{"output_state",state},{"tip",state=="PROVISIONAL_OBSERVED"?point(obs.back()):J()},{"candidate_tip",obs.empty()?J():point(obs.back())},{"roi",geometry()},{"seed_candidates_count",candidates.size()},{"seeds",seedJson},{"paths",pathJson},{"chosen_seed",paths.empty()?J():J::a({paths[0].seed.x,paths[0].seed.y})},{"chosen_path_id",paths.empty()?J():J(paths[0].seed.id)},{"trace",tracejson(trace)},{"terminal_candidates",stopJson},{"ambiguous",ambiguous},{"observed_path_count",obs.size()},{"predicted_gap_count",missing},{"last_visited_x",paths.empty()||paths[0].trace.empty()?J():J(paths[0].trace.back().x)},{"stop_reason",stop},{"reference_status_counts",countJson},{"gt_accessed_at_inference",false},{"runtime_ms",ms(start)}});
 }
 void process(const cv::Mat1b&im,const std::array<P,2>&points){auto start=Clock::now();current=im;
  try{if(current.size()!=base.reference.size()||current.empty())throw std::runtime_error("Image shape/type invalid");for(auto pair:{points,base.referencePoints}){if(pair[0].y>=pair[1].y)throw std::runtime_error("Expected valid upper/lower P coordinates");for(auto p:pair)if(!std::isfinite(p.x)||!std::isfinite(p.y)||p.x<0||p.x>=im.cols||p.y<0||p.y>=im.rows)throw std::runtime_error("Invalid P coordinates");}
   base.process(current,&points);if(base.result.status!="OK")throw std::runtime_error(base.result.error);quality();double preprocessing=ms(start);J rs=J::a(),qs=J::a();for(int i=0;i<5;++i)rs.push(mode(i));for(auto&q:qualities)qs.push(q.data);output=J::o({{"status","OK"},{"roi",geometry()},{"reference_points",J::a({point(base.referencePoints[0]),point(base.referencePoints[1])})},{"current_points",J::a({point(points[0]),point(points[1])})},{"reference_quality",qs},{"results",rs},{"preprocess_ms",preprocessing},{"runtime_ms",ms(start)}});
  }catch(const std::exception&e){J rs=J::a();for(auto m:modes)rs.push(J::o({{"mode",m},{"output_state","INPUT_ERROR"},{"tip",J()},{"trace",J::a()},{"seeds",J::a()},{"paths",J::a()},{"error",e.what()}}));output=J::o({{"status","INPUT_ERROR"},{"error",e.what()},{"results",rs}});base.arrays={};}json=output.dump();
 }
};
}
