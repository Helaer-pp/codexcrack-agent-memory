#pragma once
#include <opencv2/opencv.hpp>
#include <array>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <vector>
namespace grayref {
using P=cv::Point2d;using Clock=std::chrono::steady_clock;
inline double ms(Clock::time_point start){return std::chrono::duration<double,std::milli>(Clock::now()-start).count();}
inline int reflect(int i,int n){while(i<0||i>=n){if(i<0)i=-i-1;if(i>=n)i=2*n-i-1;}return i;}
inline std::vector<double> gaussianKernel(double sigma){int radius=int(4*sigma+.5);std::vector<double>w(2*radius+1);double sum=0;for(int i=-radius;i<=radius;++i){w[i+radius]=std::exp(-.5*(i*i)/(sigma*sigma));sum+=w[i+radius];}for(double&v:w)v/=sum;return w;}
inline cv::Mat1f correlate(const cv::Mat1f&im,const std::vector<double>&w,int axis){
 int radius=int(w.size()/2);cv::Mat1f out(im.size());
 for(int y=0;y<im.rows;++y)for(int x=0;x<im.cols;++x){double sum=double(im(y,x))*w[radius];for(int j=1;j<=radius;++j){double a=axis==0?im(reflect(y-j,im.rows),x):im(y,reflect(x-j,im.cols));double b=axis==0?im(reflect(y+j,im.rows),x):im(y,reflect(x+j,im.cols));sum+=(a+b)*w[radius-j];}out(y,x)=float(sum);}return out;
}
inline cv::Mat1f gaussian(const cv::Mat1f&im){auto k=gaussianKernel(.7);return correlate(correlate(im,k,0),k,1);}
struct TraceRow {int x=0,y=0,gap=0;float contrast=0,delta=0,strength=0;bool visible=false;double predicted=0;};
struct Trace {std::string mode;int threshold=0;std::vector<TraceRow>rows;std::vector<cv::Point>observations;bool hasTip=false;cv::Point tip;int candidateCount=0;};
struct Result {std::string status="OK",error,pointSource="provided";std::array<P,2>points,translations;std::array<double,2>ncc{{-2,-2}};int xleft=0,xright=0,upper=0,lower=0,xa=0,ya=0,xb=0,yb=0;std::vector<Trace>traces;double totalMs=0,pointMs=0,preprocessMs=0,trackMs=0;};
class P1P2GrayRefV1 {
public:
 cv::Mat1b reference;std::array<P,2>referencePoints;Result result;std::array<cv::Mat1f,8>arrays;std::string json;
 void initializeReference(const cv::Mat1b&im,P p1,P p2){reference=im.clone();referencePoints={p1,p2};}
 P trackPoint(const cv::Mat1b&current,P p,double&ncc){int ix=int(std::nearbyint(p.x)),iy=int(std::nearbyint(p.y));const int radius=29,search=25;
  if(ix-radius-search<0||iy-radius-search<0||ix+radius+search>=reference.cols||iy+radius+search>=reference.rows)throw std::runtime_error("P point too close to image boundary");
  cv::Rect tpl(ix-radius,iy-radius,2*radius+1,2*radius+1),area(ix-radius-search,iy-radius-search,2*(radius+search)+1,2*(radius+search)+1);cv::Mat1f map;cv::matchTemplate(current(area),reference(tpl),map,cv::TM_CCOEFF_NORMED);cv::Point loc;cv::minMaxLoc(map,nullptr,&ncc,nullptr,&loc);
  if(!std::isfinite(ncc)||ncc<.8)throw std::runtime_error("P point NCC below 0.80");return p+P(loc.x-search,loc.y-search);
 }
 double slope(const std::vector<cv::Point>&points){int n=std::min(12,int(points.size()));if(n<5)return 0.;cv::Mat1d design(n,2),target(n,1);double scale=0;for(int i=0;i<n;++i){auto&p=points[points.size()-n+i];design(i,0)=p.x;design(i,1)=1.;target(i)=p.y;scale+=double(p.x)*p.x;}scale=std::sqrt(scale);double ones=std::sqrt(double(n));for(int i=0;i<n;++i){design(i,0)/=scale;design(i,1)/=ones;}cv::Mat1d solution;cv::solve(design,target,solution,cv::DECOMP_SVD);return std::clamp(solution(0)/scale,-.20,.20);}
 Trace track(bool joint,int threshold,const cv::Mat1f&valley,const cv::Mat1f&delta,const cv::Mat1f&score,const cv::Mat1f&valid){
  auto&r=result;Trace t;t.mode=joint?"joint":"current";t.threshold=threshold;int xstart=r.xleft+6;double center=(r.points[0].y+r.points[1].y)/2.,priorSigma=std::max(12.,(r.lower-r.upper)*.23);
  if(r.upper+7>=r.lower-7||xstart<r.xa||xstart>=r.xright)throw std::runtime_error("Empty initialization region");
  int y0=r.upper+7;double bestInit=-1;
  for(int y=r.upper+7;y<r.lower-7;++y){double z=(y-center)/priorSigma;double evidence=joint?score(y-r.ya,xstart-r.xa):(valid(y-r.ya,xstart-r.xa)?std::max(valley(y-r.ya,xstart-r.xa),0.f):0.f);double merit=evidence*std::exp(-.5*z*z);if(merit>bestInit){bestInit=merit;y0=y;}}
  for(int y=0;y<valley.rows;++y)for(int x=0;x<valley.cols;++x)if(valid(y,x)&&valley(y,x)>=threshold&&(!joint||delta(y,x)>=threshold))++t.candidateCount;
  int gap=0;
  for(int x=xstart;x<r.xright;++x){double predicted=y0;if(!t.observations.empty()){auto last=t.observations.back();predicted=last.y+slope(t.observations)*(x-last.x);}int low=std::max(r.upper+3,int(std::floor(predicted-7))),high=std::min(r.lower-3,int(std::ceil(predicted+7))+1);
   int acceptedY=-1,anyY=-1;double best=-std::numeric_limits<double>::infinity(),any=-std::numeric_limits<double>::infinity();
   for(int y=low;y<high;++y){int i=y-r.ya,j=x-r.xa;float c=valley(i,j),d=delta(i,j),strength=joint?std::sqrt(std::max(c,0.f)*std::max(d,0.f)):std::max(c,0.f);double merit=double(strength)-.55*std::abs(y-predicted);if(merit>any){any=merit;anyY=y;}bool accepted=valid(i,j)&&c>=threshold&&(!joint||d>=threshold);if(accepted&&merit>best){best=merit;acceptedY=y;}}
   TraceRow row;row.x=x;row.predicted=predicted;row.visible=acceptedY>=0;row.y=row.visible?acceptedY:anyY>=0?anyY:int(std::nearbyint(predicted));
   if(anyY>=0){row.contrast=valley(row.y-r.ya,x-r.xa);row.delta=delta(row.y-r.ya,x-r.xa);row.strength=joint?std::sqrt(std::max(row.contrast,0.f)*std::max(row.delta,0.f)):std::max(row.contrast,0.f);}
   if(row.visible){t.observations.emplace_back(x,row.y);t.tip={x,row.y};t.hasTip=true;gap=0;}else ++gap;row.gap=gap;t.rows.push_back(row);if(gap>20)break;
  }
  return t;
 }
 const Result& process(const cv::Mat1b&current,const std::array<P,2>*provided=nullptr){
  auto start=Clock::now();result={};arrays={};auto&r=result;
  try{
   if(current.size()!=reference.size())throw std::runtime_error("Reference and current sizes differ");auto tick=Clock::now();r.pointSource=provided?"provided":"NCC template";
   for(int i=0;i<2;++i){r.points[i]=provided?(*provided)[i]:trackPoint(current,referencePoints[i],r.ncc[i]);r.translations[i]=r.points[i]-referencePoints[i];if(!std::isfinite(r.points[i].x)||!std::isfinite(r.points[i].y))throw std::runtime_error("Nonfinite P point");}r.pointMs=ms(tick);tick=Clock::now();
   auto p1=r.points[0],p2=r.points[1];int w=current.cols,h=current.rows;
   if(p1.y>p2.y)throw std::runtime_error("Expected P1 above P2");r.upper=int(std::ceil(std::min(p1.y,p2.y)));r.lower=int(std::floor(std::max(p1.y,p2.y)));r.xleft=int(std::ceil(std::max(p1.x,p2.x)));
   if(r.lower-r.upper<25)throw std::runtime_error("P1/P2 vertical distance too narrow");if(!(0<=r.xleft+50&&r.xleft+50<w&&15<=r.upper&&r.upper<r.lower&&r.lower<h-15))throw std::runtime_error("Point geometry outside image bounds");
   int mid=int(std::nearbyint((p1.y+p2.y)/2));cv::Mat1f mean(1,w);for(int x=0;x<w;++x){float sum=0;for(int y=mid-8;y<mid+9;++y)sum+=current(y,x);mean(0,x)=sum/17.f;}mean=correlate(mean,gaussianKernel(25.),1);r.xright=w-25;
   for(int x=r.xleft+300;x<w-120;++x)if(mean(0,x)<95){float sum=0;for(int k=x;k<x+95;++k)sum+=mean(0,k);if(sum/95.f<95){r.xright=x;break;}}
   if(!(r.xleft+8<r.xright&&r.xright<=w-1))throw std::runtime_error("Invalid right search boundary");r.xa=std::max(0,r.xleft-30);r.xb=std::min(w,r.xright+24);r.ya=std::max(0,r.upper-24);r.yb=std::min(h,r.lower+24);
   cv::Rect crop(r.xa,r.ya,r.xb-r.xa,r.yb-r.ya);cv::Mat1f ca;current(crop).convertTo(ca,CV_32F);cv::Mat1f mapx(crop.size()),mapy(crop.size());
   for(int y=0;y<mapx.rows;++y)for(int x=0;x<mapx.cols;++x){float Y=float(y+r.ya),X=float(x+r.xa),alpha=std::clamp((Y-float(p1.y))/float(p2.y-p1.y),0.f,1.f);float dx=(1.f-alpha)*float(r.translations[0].x)+alpha*float(r.translations[1].x),dy=(1.f-alpha)*float(r.translations[0].y)+alpha*float(r.translations[1].y);mapx(y,x)=X-dx;mapy(y,x)=Y-dy;}
   cv::Mat1b aligned;cv::remap(reference,aligned,mapx,mapy,cv::INTER_LINEAR,cv::BORDER_REFLECT_101);cv::Mat1f ar;aligned.convertTo(ar,CV_32F);cv::Mat1f csm=gaussian(ca),rsm=gaussian(ar),valley=cv::Mat1f::zeros(ca.size()),delta(ca.size()),flank(ca.size()),valid(ca.size()),score(ca.size());int H=ca.rows;
   for(int y=0;y<H;++y)for(int x=0;x<ca.cols;++x){float c=csm(y,x);for(int offset:{6,9,12}){float f=(csm((y+offset)%H,x)+csm((y-offset+H)%H,x))*.5f;valley(y,x)=std::max(valley(y,x),f-c);}delta(y,x)=rsm(y,x)-c;flank(y,x)=std::min(csm((y+10)%H,x),csm((y-10+H)%H,x));bool inroi=y>=r.upper-r.ya+2&&y<r.lower-r.ya-1&&x>=r.xleft-r.xa&&x<r.xright-r.xa;valid(y,x)=flank(y,x)>135&&inroi?1.f:0.f;score(y,x)=valid(y,x)?std::sqrt(std::max(valley(y,x),0.f)*std::max(delta(y,x),0.f)):0.f;}
   arrays={ar,csm,rsm,valley,delta,flank,valid,score};r.preprocessMs=ms(tick);tick=Clock::now();for(bool joint:{true,false})for(int threshold:{8,10,12})r.traces.push_back(track(joint,threshold,valley,delta,score,valid));r.trackMs=ms(tick);
  }catch(const std::exception&e){r.status="ERROR";r.error=e.what();r.traces.clear();}
  r.totalMs=ms(start);return r;
 }
};
}
