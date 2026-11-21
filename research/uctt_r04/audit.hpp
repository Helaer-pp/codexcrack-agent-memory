#pragma once
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <algorithm>
#include <cmath>
#include <vector>
#include <string>
#include <limits>
namespace r04 {
using Pt=cv::Point2d;using Path=std::vector<Pt>;
inline bool inside(Pt p,cv::Size s){return std::isfinite(p.x)&&std::isfinite(p.y)&&p.x>=0&&p.y>=0&&p.x<s.width&&p.y<s.height;}
inline double median(std::vector<double> v){if(v.empty())return 0;auto i=v.begin()+v.size()/2;std::nth_element(v.begin(),i,v.end());return *i;}
inline Pt unit(Pt p){return p/std::max(1e-12,cv::norm(p));}
inline double pixel(const cv::Mat &im,Pt p){if(!inside(p,im.size()))return std::numeric_limits<double>::quiet_NaN();int x=cvRound(p.x),y=cvRound(p.y);if(x>=im.cols||y>=im.rows)return std::numeric_limits<double>::quiet_NaN();return im.at<uchar>(y,x);}
struct Section {double signed_contrast=0,noise=0,width=0;bool valid=false;};
inline Section section(const cv::Mat &im,Pt p,Pt tangent){
 Section s;Pt n(-tangent.y,tangent.x);if(!inside(p+n*7,im.size())||!inside(p-n*7,im.size()))return s;
 double c=(pixel(im,p)+pixel(im,p+n)+pixel(im,p-n))/3.;
 double left=(pixel(im,p-n*4)+pixel(im,p-n*6))*.5,right=(pixel(im,p+n*4)+pixel(im,p+n*6))*.5;
 if(!std::isfinite(c)||!std::isfinite(left)||!std::isfinite(right))return s;
 double dark=std::min(left,right)-c,bright=c-std::max(left,right);s.signed_contrast=dark>=bright?dark:-bright;
 s.noise=.5*(std::abs(pixel(im,p-n*7)-pixel(im,p-n*6))+std::abs(pixel(im,p+n*7)-pixel(im,p+n*6)));
 if(!std::isfinite(s.noise))return s;
 int polarity=s.signed_contrast>=0?1:-1;double center=pixel(im,p),half=std::max(2.,std::abs(s.signed_contrast)*.5);int width=1;
 for(int sign:{-1,1})for(int k=1;k<=6;++k){if(polarity*(pixel(im,p+n*double(k*sign))-center)>=half)break;++width;}
 s.width=width;s.valid=true;return s;
}
struct Structure {double support=0,contrast=0,width=0,noise=0;int samples=0,max_gap=0,polarity=0;bool strong=false;};
inline Structure structure(const cv::Mat &im,const Path &path){
 Structure q;if(path.size()<5)return q;std::vector<Section> ss;std::vector<double> cs,ws,ns;
 size_t stride=std::max<size_t>(1,(path.size()+255)/256);
 for(size_t i=0;i<path.size();i+=stride){Pt d=unit(path[std::min(path.size()-1,i+4)]-path[i>4?i-4:0]);auto s=section(im,path[i],d);ss.push_back(s);if(s.valid){cs.push_back(s.signed_contrast);ws.push_back(s.width);ns.push_back(s.noise);}}
 q.contrast=median(cs);q.width=median(ws);q.noise=median(ns);q.polarity=q.contrast>=0?1:-1;int hits=0,gap=0;
 for(auto s:ss){bool hit=s.valid&&q.polarity*s.signed_contrast>=std::max(4.,2*s.noise);hits+=hit;gap=hit?0:gap+int(stride);q.max_gap=std::max(q.max_gap,gap);}
 q.samples=int(ss.size());q.support=double(hits)/std::max(1,q.samples);q.strong=q.samples>=5&&q.support>=.7;return q;
}
struct Audit {Structure path,prefix;double connection_distance=-1,tangent_alignment=0,overlap_fraction=0,before=0,ahead=0,terminal=0;int overlap_samples=0;bool edge=false,structure_only=false,prefix_connected=false;std::string reason;};
inline Audit audit(const cv::Mat &im,const Path &path,const Path &prefix,bool rootSupported,cv::Rect roi){
 Audit a;a.path=structure(im,path);a.prefix=structure(im,prefix);
 if(path.empty()){a.reason="NO_CANDIDATE";return a;}
 if(!std::all_of(path.begin(),path.end(),[&](Pt p){return inside(p,im.size());})){a.reason="INVALID_PATH";return a;}
 Pt tip=path.back();a.edge=!roi.contains(cv::Point(cvRound(tip.x),cvRound(tip.y)))||std::min({tip.x-roi.x,tip.y-roi.y,roi.br().x-1-tip.x,roi.br().y-1-tip.y})<10;
 a.structure_only=a.path.strong&&!a.edge;
 size_t count=std::min<size_t>(16,path.size());double closest=1e100;size_t pi=0;double radius=std::max(3.,a.path.width);
 for(size_t i=0;i<count;++i){double best=1e100;size_t kbest=0;for(size_t k=0;k<prefix.size();++k){double d=cv::norm(path[i]-prefix[k]);if(d<best){best=d;kbest=k;}}if(best<=radius)++a.overlap_samples;if(best<closest){closest=best;pi=kbest;}}
 a.overlap_fraction=double(a.overlap_samples)/std::max<size_t>(1,count);if(!prefix.empty())a.connection_distance=closest;
 if(prefix.size()>1&&path.size()>1){Pt d=unit(path[std::min<size_t>(8,path.size()-1)]-path.front());Pt p=unit(prefix[std::min(prefix.size()-1,pi+4)]-prefix[pi>4?pi-4:0]);a.tangent_alignment=d.dot(p);}
 a.prefix_connected=a.structure_only&&rootSupported&&a.prefix.strong&&a.overlap_fraction>=.5&&a.tangent_alignment>=.5&&a.path.max_gap<=std::max(3.,2*a.path.width);
 a.reason=a.edge?"ROI_EDGE":!a.path.strong?"RAW_STRUCTURE_UNSUPPORTED":!rootSupported?"NO_ROOT_SUPPORTED_PREFIX":!a.prefix.strong?"PREFIX_STRUCTURE_UNSUPPORTED":a.overlap_fraction<.5?"DISCONNECTED_FROM_PREFIX":a.tangent_alignment<.5?"PREFIX_DIRECTION_CONFLICT":a.path.max_gap>std::max(3.,2*a.path.width)?"UNSUPPORTED_GAP":"PREFIX_CONNECTED_PROXY";
 Path tail(path.end()-std::min<size_t>(16,path.size()),path.end());a.before=structure(im,tail).support;
 if(path.size()>1){Pt d=unit(tip-path[path.size()-std::min<size_t>(8,path.size())]);int hit=0,valid=0;for(int i=1;i<=12;++i){auto s=section(im,tip+d*double(i),d);valid+=s.valid;hit+=s.valid&&a.path.polarity*s.signed_contrast>=std::max(4.,2*s.noise);}a.ahead=valid?double(hit)/valid:0;}
 a.terminal=a.before-a.ahead;return a;
}
struct Branch {Path local,original;double gain=0;};
struct Trace {Path prefix;bool root=false;std::vector<Branch> branches;cv::Mat score,current,registered,prior;cv::Rect roi;int turn=0;};
inline thread_local Trace *active=nullptr;
struct Active {Trace *old;explicit Active(Trace *p):old(active){active=p;}~Active(){active=old;}};
struct State {bool has=false;Pt reference{},last{};uint64_t last_frame=0;cv::Size size;
 std::string source="fallback";Pt output{};bool valid=false;
 void step(Pt tip,bool accept,bool motion,const cv::Matx22d &R,Pt t,cv::Rect roi,cv::Size sz,uint64_t frame){
  bool finite=std::isfinite(t.x)&&std::isfinite(t.y);for(double v:R.val)finite=finite&&std::isfinite(v);
  motion=motion&&finite&&(size.empty()||size==sz);if(size.empty())size=sz;
  valid=accept&&motion&&inside(tip,sz);source="fallback";output=Pt(roi.x+roi.width*.5,roi.y+roi.height*.5);
  if(valid){has=true;last=tip;last_frame=frame;reference=R.t()*(tip-t);output=tip;source="observed";}
  else if(has&&motion){Pt p=R*reference+t;if(inside(p,sz)){output=p;source="predicted";}}
  output.x=std::clamp(output.x,0.,double(sz.width-1));output.y=std::clamp(output.y,0.,double(sz.height-1));
 }
};
}
