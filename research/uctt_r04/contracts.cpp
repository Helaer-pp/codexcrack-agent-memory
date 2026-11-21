#include "audit.hpp"
#include <opencv2/imgcodecs.hpp>
#include <iostream>
#include <fstream>
#include <filesystem>
using namespace r04;
Path line(Pt a,Pt b){Path p;int n=std::max(1,int(cv::norm(b-a)));for(int i=0;i<=n;++i)p.push_back(a+(b-a)*(double(i)/n));return p;}
void draw(cv::Mat &im,const Path &p,int value){std::vector<cv::Point> pts;for(auto x:p)if(inside(x,im.size()))pts.emplace_back(cvRound(x.x),cvRound(x.y));if(pts.size()>1)cv::polylines(im,std::vector<std::vector<cv::Point>>{pts},false,value,2,cv::LINE_AA);}
// Test-only image-derived prefix extractor in a coarse initial corridor. No GT
// mask or candidate identity is read. Real replay uses the existing main path.
Path prefix(const cv::Mat &im){Path p;int y=128;for(int x=32;x<=110;++x){double best=0;int yybest=y;for(int yy=std::max(96,y-3);yy<=std::min(160,y+3);++yy){auto s=section(im,{double(x),double(yy)},{1,0});if(s.valid&&std::abs(s.signed_contrast)>best){best=std::abs(s.signed_contrast);yybest=yy;}}if(best<4)break;y=yybest;p.emplace_back(x,y);}return p;}
int main(int argc,char**argv){
 if(argc!=2)return 1;std::filesystem::create_directories(argv[1]);
 std::vector<std::string> names={"no_crack","reference_preexisting_crack","stationary_crack","closure_first_frame","sustained_loss","reappearance","bad_motion","wrong_tip_mismatched_path","disconnected_wrong_candidate_after_lock","coherent_wrong_first_lock","boundary_terminal","nan_candidate","nonfinite_motion","image_size_change","persistent_changed_size","new_detector_reset","isolated_dark_line","isolated_bright_line","near_parallel_scratch","weak_true_strong_artifact","short_gap_then_impostor","initial_roi_shift","curved_true","connected_false_branch"};
 std::cout<<"case_id,method,candidate_id,label,label_source,expected_observed,observed,history_written,source,source_verified,endpoint_verified,raw_support,prefix_support,overlap,reason,output_x,output_y,pass,image\n";
 for(size_t c=0;c<names.size();++c){
  auto name=names[c];cv::Mat im(256,384,CV_8UC1,cv::Scalar(180));Path truth=line({32,128},{220,128});
  if(name=="curved_true"){truth.clear();for(int x=32;x<=220;++x)truth.emplace_back(x,128+12*std::sin((x-32)*.012));}
  bool invisible=name=="no_crack"||name=="closure_first_frame"||name=="sustained_loss"||name=="new_detector_reset";
  if(!invisible)draw(im,truth,name=="weak_true_strong_artifact"?155:65);
  Path distractor=line({150,174},{300,174});
  if(c>=16){if(name=="near_parallel_scratch")distractor=line({80,145},{290,145});if(name=="short_gap_then_impostor")distractor=line({228,128},{310,128});if(name=="connected_false_branch")distractor=line({96,128},{290,164});draw(im,distractor,name=="isolated_bright_line"?250:25);}
  auto pref=prefix(im);bool root=pref.size()>=24;
  std::vector<std::pair<Path,std::string>> candidates={{truth,invisible?"invisible":"construct_true"}};
  if(name=="coherent_wrong_first_lock"||name=="disconnected_wrong_candidate_after_lock"){Path bad=truth;for(auto&p:bad)p+=Pt(-30,-30);candidates={{bad,"construct_distractor"}};}
  if(name=="wrong_tip_mismatched_path"){auto p=truth;p.back()+=Pt(30,30);candidates={{p,"invalid"}};}
  if(name=="boundary_terminal"){auto p=line({32,128},{380,128});draw(im,p,65);candidates={{p,"edge_unresolved"}};}
  if(name=="nan_candidate"){auto p=truth;p.back().x=std::numeric_limits<double>::quiet_NaN();candidates={{p,"invalid"}};}
  if(c>=16&&name!="initial_roi_shift"&&name!="curved_true")candidates.push_back({distractor,"construct_distractor"});
  auto filename=std::string(argv[1])+"/"+name+".png";cv::imwrite(filename,im);
  for(size_t k=0;k<candidates.size();++k){auto&p=candidates[k].first;auto label=candidates[k].second;cv::Rect roi(0,0,384,256);if(name=="initial_roi_shift")roi=cv::Rect(8,4,372,248);
   auto a=audit(im,p,pref,root,roi);bool motion=name!="bad_motion";cv::Matx22d R=cv::Matx22d::eye();Pt t;
   if(name=="nonfinite_motion")t.x=std::numeric_limits<double>::infinity();
   bool expected=label=="construct_true"&&motion&&name!="nonfinite_motion"&&name!="image_size_change"&&name!="persistent_changed_size";
   for(int method=1;method<=2;++method){State s;if(name=="closure_first_frame"||name=="sustained_loss"||name=="image_size_change"||name=="persistent_changed_size")s.step(truth.back(),true,true,R,{},roi,im.size(),0);
    cv::Size size=im.size();if(name=="image_size_change"||name=="persistent_changed_size")--size.width;
    bool accepted=method==1?a.structure_only:a.prefix_connected;
    // Existing endpoint flag is only a fixture flag; invalid coordinates/path
    // and boundary conditions remain explicitly rejected by the native audit.
    bool endpointOK=std::all_of(p.begin(),p.end(),[&](Pt q){return inside(q,im.size());});
    for(size_t j=1;j<p.size();++j)endpointOK=endpointOK&&cv::norm(p[j]-p[j-1])<=4;
    accepted=accepted&&endpointOK; // Sampling/coordinate validation; no label access.
    s.step(p.back(),accepted,motion,R,t,roi,size,1);
    if(name=="persistent_changed_size")s.step(p.back(),accepted,motion,R,t,roi,size,2);
    std::cout<<name<<','<<method<<','<<k<<','<<label<<",synthetic_construction,"<<expected<<','<<s.valid<<','<<s.valid<<','<<s.source<<','<<(method==1?a.structure_only:a.prefix_connected)<<','<<endpointOK<<','<<a.path.support<<','<<a.prefix.support<<','<<a.overlap_fraction<<','<<a.reason<<','<<s.output.x<<','<<s.output.y<<','<<(s.valid==expected)<<','<<filename<<'\n';
   }
  }
 }
 return 0;
}
