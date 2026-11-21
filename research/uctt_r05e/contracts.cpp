#include <opencv2/opencv.hpp>
#include <algorithm>
#include <cmath>
#include <vector>
#include <string>
#include <iostream>
#include "evidence.hpp"
int main(){
 int failed=0;auto check=[&](const char*n,bool ok){std::cout<<n<<','<<(ok?"PASS":"FAIL")<<",CONSTRUCTED_NATIVE_PROPERTY\n";failed+=!ok;};
 std::cout<<"test,status,scope\n";
 cv::Mat1f im(64,128,140.f),legacy(64,128,-3.f);for(int x=8;x<90;++x)im(32,x)=110;
 cv::Mat1f eroded=im.clone(),low=im.clone(),high=im.clone();cv::Mat1b prior(im.size(),uchar(0)),valid(im.size(),uchar(255)),missing(im.size(),uchar(0));
 r05e::Evidence absent,present;
 r05e::channels(absent,im,im,eroded,low,high,prior,missing,legacy);
 r05e::channels(present,im,im,eroded,low,high,prior,valid,legacy);
 check("reference_unavailable_current_survives",absent.current(32,50)==30&&std::isnan(absent.change(32,50))&&(int(absent.reason(32,50))&4));
 check("reference_existing_crack_zero_change_not_veto",present.current(32,50)==30&&present.change(32,50)==0&&present.reference(32,50)==30);
 check("reference_validity_cannot_change_current",cv::norm(absent.current,present.current,cv::NORM_INF)==0);
 check("legacy_score_unchanged",cv::countNonZero(legacy!=-3.f)==0);
 check("unknown_reference_spatial_footprint",present.quality(5,5)==1&&present.quality(5,4)==0);
 r05e::candidates(absent);r05e::candidates(present);
 check("same_current_same_raw_candidates",absent.raw_total==present.raw_total&&absent.raw_total>0);
 check("candidate_budget_bounded",present.retained_count<=64&&present.candidates.size()<=8192);
 bool lineage=true;for(auto&p:present.candidates)lineage&=p.merged>=0&&p.retained<64&&!p.reason.empty();check("candidate_lineage_explicit",lineage);
 r05e::Evidence again;r05e::channels(again,im,im,eroded,low,high,prior,valid,legacy);r05e::candidates(again);
 bool same=again.candidates.size()==present.candidates.size();for(size_t i=0;same&&i<again.candidates.size();++i){auto&a=again.candidates[i];auto&b=present.candidates[i];same=a.x==b.x&&a.y==b.y&&a.gain==b.gain&&a.retained==b.retained;}
 check("deterministic_native_candidates",same);
 cv::Mat1f bright(64,128,110.f);for(int x=8;x<90;++x)bright(32,x)=140;
 r05e::Evidence polarity;r05e::channels(polarity,bright,im,eroded,low,high,prior,missing,legacy);
 check("bright_line_not_claimed_as_dark_evidence",polarity.current(32,50)<0);
 return failed?2:0;
}
