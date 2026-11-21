#include <windows.h>
#include <opencv2/opencv.hpp>
#include "CrackV4_experiments.h"
#include <filesystem>
#include <fstream>
#include <sstream>
#include <chrono>
#include <vector>
#include <iomanip>
#include <cstring>
using Clock=std::chrono::steady_clock;
double ms(Clock::time_point t){return std::chrono::duration<double,std::milli>(Clock::now()-t).count();}
struct Api {
 HMODULE dll; CrackV4Handle h=nullptr;
#define FN(n) decltype(&::n) n;
 FN(CrackV4SetNumThreads) FN(CrackV4CreateExtended) FN(CrackV4SetOptionsV2)
 FN(CrackV4Process) FN(CrackV4GetBaseline) FN(CrackV4GetResultV2)
 FN(CrackV4CopyPath) FN(CrackV4LastJson) FN(CrackV4Destroy)
#undef FN
 using Copy=int(*)(CrackV4Handle,double*,int);Copy stops=nullptr;
 Api(const char* path){dll=LoadLibraryW(std::filesystem::u8path(path).c_str());if(!dll)throw std::runtime_error("DLL load");
#define LOAD(n) n=(decltype(n))GetProcAddress(dll,#n);if(!n)throw std::runtime_error(#n);
 LOAD(CrackV4SetNumThreads) LOAD(CrackV4CreateExtended) LOAD(CrackV4SetOptionsV2)
 LOAD(CrackV4Process) LOAD(CrackV4GetBaseline) LOAD(CrackV4GetResultV2)
 LOAD(CrackV4CopyPath) LOAD(CrackV4LastJson) LOAD(CrackV4Destroy)
#undef LOAD
 stops=(Copy)GetProcAddress(dll,"AP2CopyStops");CrackV4SetNumThreads(4);
 }
 double init(CrackV4Image &im,CrackV4Point *p,int mode){CrackV4Config c{sizeof(c),mode,1.,1};CrackV4ExperimentOptions e{sizeof(e),1,3572,0};double t=0;char err[4096]{};
  if(CrackV4CreateExtended(&im,p,&c,&e,&h,&t,err,4096))throw std::runtime_error(err);
  CrackV4OptionsV2 o{sizeof(o),2,1,1};if(CrackV4SetOptionsV2(h,&o))throw std::runtime_error("options");return t;}
 struct Output{CrackV4ResultV2 v{};std::vector<CrackV4Point> p;std::vector<double> obs;double core=0;std::string json;};
 Output run(CrackV4Image &im,CrackV4Point *p,bool ref){Output out;auto t=Clock::now();CrackV4Result r{};r.struct_size=sizeof(r);
  if(ref?CrackV4GetBaseline(h,&r):CrackV4Process(h,&im,p,&r))throw std::runtime_error("Process");
  out.v.struct_size=sizeof(out.v);out.v.api_version=2;if(CrackV4GetResultV2(h,&out.v))throw std::runtime_error("V2");
  int n=CrackV4CopyPath(h,0,nullptr,0);out.p.resize(n);CrackV4CopyPath(h,0,out.p.data(),n);
  if(stops){int count=stops(h,nullptr,0);out.obs.resize(count*11);if(stops(h,out.obs.data(),count)<0)throw std::runtime_error("Observer capacity exceeded");}
  out.core=ms(t);out.json=CrackV4LastJson(h);return out;
 }
 ~Api(){if(h)CrackV4Destroy(h);if(dll)FreeLibrary(dll);}
};
int main(int argc,char **argv){try{
 if(argc!=6)throw std::runtime_error("baseline.dll shadow.dll input.tsv output-prefix mode");
 Api a(argv[1]),b(argv[2]);std::ifstream in(std::filesystem::u8path(argv[3]));std::string line;int i=0;
 std::string prefix=argv[4];std::ofstream out(std::filesystem::u8path(prefix+".csv")),ja(std::filesystem::u8path(prefix+"_A.jsonl")),jb(std::filesystem::u8path(prefix+"_shadow.jsonl"));
 out<<"frame_id,A_complete_core_ms,shadow_observer_core_ms,path_bytes_equal,formal_equal,observer_records,A_init_ms,shadow_init_ms\n"<<std::setprecision(17);
 while(std::getline(in,line)){if(line.empty())continue;std::istringstream ss(line);std::string path;CrackV4Point pp[2];std::getline(ss,path,'\t');ss>>pp[0].x>>pp[0].y>>pp[1].x>>pp[1].y;
  std::ifstream f(std::filesystem::u8path(path),std::ios::binary);std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(f)),{});auto img=cv::imdecode(bytes,0);if(img.empty())throw std::runtime_error("decode");
  CrackV4Image im{img.data,img.cols,img.rows,(int64_t)img.step};double ia=0,ib=0;if(i==0){ia=a.init(im,pp,std::stoi(argv[5]));ib=b.init(im,pp,std::stoi(argv[5]));}
  Api::Output x,y;if(i%2){y=b.run(im,pp,i==0);x=a.run(im,pp,i==0);}else{x=a.run(im,pp,i==0);y=b.run(im,pp,i==0);}
  bool samepath=x.p.size()==y.p.size()&&(x.p.empty()||std::memcmp(x.p.data(),y.p.data(),x.p.size()*sizeof(CrackV4Point))==0);
  bool same=x.v.tip_confirmed==y.v.tip_confirmed&&x.v.complete_length_valid==y.v.complete_length_valid&&std::memcmp(&x.v.tip_px,&y.v.tip_px,sizeof(CrackV4Point))==0&&x.v.root_to_tip_length_px==y.v.root_to_tip_length_px;
  if(!samepath||!same)throw std::runtime_error("GATE0 mismatch");
  ja<<x.json<<'\n';jb<<y.json<<'\n';out<<i<<','<<x.core<<','<<y.core<<','<<samepath<<','<<same<<','<<y.obs.size()/11<<','<<ia<<','<<ib<<'\n';
  if(i%100==0)std::cout<<i<<std::endl;++i;
 }return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 2;}}
