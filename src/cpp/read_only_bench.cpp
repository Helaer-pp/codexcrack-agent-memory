// Read-only caller of frozen A. No detector implementation is built here.
#include <windows.h>
#include <opencv2/opencv.hpp>
#include "CrackV4_experiments.h"
#include <filesystem>
#include <fstream>
#include <sstream>
#include <chrono>
#include <vector>
#include <iomanip>
using Clock=std::chrono::steady_clock;
double elapsed(Clock::time_point t){return std::chrono::duration<double,std::milli>(Clock::now()-t).count();}
struct Frame{std::string path;CrackV4Point p[2];cv::Mat image;};
int main(int argc,char**argv){try{
 if(argc!=7)throw std::runtime_error("dll input.tsv output-prefix mode refine auto-points");
 auto lib=LoadLibraryW(std::filesystem::u8path(argv[1]).c_str());if(!lib)throw std::runtime_error("LoadLibrary");
#define API(n) auto n=(decltype(&::n))GetProcAddress(lib,#n);if(!n)throw std::runtime_error(#n)
 API(CrackV4SetNumThreads);API(CrackV4CreateExtended);API(CrackV4SetOptionsV2);API(CrackV4Process);API(CrackV4GetBaseline);API(CrackV4GetResultV2);API(CrackV4CopyPath);API(CrackV4LastJson);API(CrackV4Destroy);
 CrackV4SetNumThreads(4);std::ifstream in(std::filesystem::u8path(argv[2]));std::string line;std::vector<Frame> f;
 while(std::getline(in,line)){if(line.empty())continue;std::istringstream s(line);Frame x;std::getline(s,x.path,'\t');s>>x.p[0].x>>x.p[0].y>>x.p[1].x>>x.p[1].y;std::ifstream img(std::filesystem::u8path(x.path),std::ios::binary);std::vector<unsigned char>b((std::istreambuf_iterator<char>(img)),{});x.image=cv::imdecode(b,0);if(x.image.empty())throw std::runtime_error("decode "+x.path);f.push_back(x);}
 if(f.empty())throw std::runtime_error("empty input");
 auto image=[](const cv::Mat&m){return CrackV4Image{m.data,m.cols,m.rows,(int64_t)m.step};};
 CrackV4Config config{sizeof(config),std::stoi(argv[4]),1.,std::stoi(argv[5])};CrackV4ExperimentOptions exp{sizeof(exp),1,3572,0};CrackV4Handle h=nullptr;double init=0;char error[4096]{};auto ref=image(f[0].image);
 if(CrackV4CreateExtended(&ref,f[0].p,&config,&exp,&h,&init,error,sizeof(error)))throw std::runtime_error(error);
 CrackV4OptionsV2 opt{sizeof(opt),2,1,1};if(CrackV4SetOptionsV2(h,&opt))throw std::runtime_error("options");
 const std::string prefix=argv[3];std::ofstream csv(std::filesystem::u8path(prefix+".csv")),bin(std::filesystem::u8path(prefix+".pathbin"),std::ios::binary),json(std::filesystem::u8path(prefix+".jsonl"));
 csv<<"frame_id,tip_valid,length_valid,tip_x,tip_y,length_px,path_count,Process_call_ms,native_detector_ms,native_api_ms,necessary_extract_ms,complete_core_ms,json_logging_ms,thread_id,working_set_bytes\n"<<std::setprecision(17);
 for(size_t i=0;i<f.size();++i){auto im=image(f[i].image);CrackV4Result r{};r.struct_size=sizeof(r);auto core=Clock::now();auto process=Clock::now();int rc=i?CrackV4Process(h,&im,std::stoi(argv[6])?nullptr:f[i].p,&r):CrackV4GetBaseline(h,&r);double processMs=elapsed(process);if(rc)throw std::runtime_error("Process");auto extract=Clock::now();CrackV4ResultV2 v{};v.struct_size=sizeof(v);v.api_version=2;CrackV4GetResultV2(h,&v);int n=CrackV4CopyPath(h,0,nullptr,0);std::vector<CrackV4Point> path(n);CrackV4CopyPath(h,0,path.data(),n);double extractMs=elapsed(extract),coreMs=elapsed(core);auto logging=Clock::now();json<<CrackV4LastJson(h)<<'\n';bin.write((char*)&n,sizeof(n));if(n)bin.write((char*)path.data(),n*sizeof(CrackV4Point));double loggingMs=elapsed(logging);
 csv<<i<<','<<v.tip_confirmed<<','<<v.complete_length_valid<<','<<v.tip_px.x<<','<<v.tip_px.y<<','<<v.root_to_tip_length_px<<','<<n<<','<<processMs<<','<<v.detector_ms<<','<<v.api_ms<<','<<extractMs<<','<<coreMs<<','<<loggingMs<<','<<GetCurrentThreadId()<<",\n";
 if(i%100==0)std::cout<<i<<'/'<<f.size()<<std::endl;
 }CrackV4Destroy(h);return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 2;}}
