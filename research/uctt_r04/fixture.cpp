#include "audit.hpp"
#include <fstream>
#include <iostream>
using namespace r04;
int main(int argc,char**argv){
 if(argc!=4)return 1;std::ifstream raw(argv[1],std::ios::binary);int w,h;raw.read((char*)&w,4);raw.read((char*)&h,4);if(w<1||h<1)return 1;cv::Mat im(h,w,CV_8UC1);raw.read((char*)im.data,w*h);if(!raw)return 1;
 std::ifstream f(argv[2]);int sw,sh;cv::Rect roi;size_t n;f>>sw>>sh>>roi.x>>roi.y>>roi.width>>roi.height>>n;Path p;for(size_t i=0;i<n;++i){Pt q;f>>q.x>>q.y;p.push_back(q);}if(!f||sw!=w||sh!=h)return 1;
 std::ifstream fp(argv[3]);bool root;fp>>root>>n;Path prefix;for(size_t i=0;i<n;++i){Pt q;fp>>q.x>>q.y;prefix.push_back(q);}if(!fp)return 1;
 std::cout<<"candidate,method,observed,history_written,raw_support,prefix_support,overlap,reason\n";
 for(int shifted=0;shifted<2;++shifted){Path q=p;if(shifted)for(auto&x:q)x+=Pt(-30,-30);auto a=audit(im,q,prefix,root,roi);
  for(int m=1;m<=2;++m){State s;bool accepted=m==1?a.structure_only:a.prefix_connected;s.step(q.back(),accepted,true,cv::Matx22d::eye(),{},roi,im.size(),1);std::cout<<(shifted?"R03_exact_shifted_distractor":"R03_original_unverified_candidate")<<','<<m<<','<<s.valid<<','<<s.valid<<','<<a.path.support<<','<<a.prefix.support<<','<<a.overlap_fraction<<','<<a.reason<<'\n';}
 }
}
