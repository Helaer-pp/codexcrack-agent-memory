#include "CrackV4_experiments.h"
#include <opencv2/imgcodecs.hpp>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <iostream>
#include <stdexcept>
static_assert(sizeof(CrackV4ExperimentOptions)==16,"Experiment ABI");
static_assert(sizeof(CrackV4Result)==88 && sizeof(CrackV4ResultV2)==376,"Existing ABI");
static CrackV4Image image(const cv::Mat &m) {
    if(m.empty() || m.type()!=CV_8UC1) throw std::runtime_error("CV_8UC1 image required");
    return {m.data,m.cols,m.rows,static_cast<int64_t>(m.step)};
}
#ifdef _WIN32
int wmain(int argc,wchar_t **argv) {
#else
int main(int argc,char **argv) {
#endif
    if(argc!=11){std::cout<<"reference current refX1 refY1 refX2 refY2 curX1 curY1 curX2 curY2\n";return 2;}
    CrackV4Handle handle=nullptr;
    try {
        auto read=[](const std::filesystem::path &p){std::ifstream f(p,std::ios::binary);std::vector<uchar> b((std::istreambuf_iterator<char>(f)),{});return cv::imdecode(b,0);};
        cv::Mat reference=read(argv[1]),current=read(argv[2]);
        CrackV4Point rp[2]={{std::stod(argv[3]),std::stod(argv[4])},{std::stod(argv[5]),std::stod(argv[6])}};
        CrackV4Point cp[2]={{std::stod(argv[7]),std::stod(argv[8])},{std::stod(argv[9]),std::stod(argv[10])}};
        CrackV4SetNumThreads(4);
        CrackV4Config cfg{};CrackV4DefaultConfig(&cfg);cfg.reference_mode=2;cfg.mm_per_pixel=1.0;
        CrackV4ExperimentOptions exp{};CrackV4DefaultExperimentOptions(&exp);
        // This test's ordered P1->P2 right normal points into the material.
        // Keep the existing local refinement; do not globally disable it merely
        // because measured current anchors are supplied.
        cfg.refine_anchor_motion=1;
        exp.flags=CV4_DIRECTION_EXPERIMENT|CV4_REGISTRATION_RECOVERY|CV4_LAYERED_AUDIT|CV4_CURRENT_TEXTURE_GUARD|CV4_ANCHOR_PATCH_RECOVERY|CV4_DIRECTION_POSITIVE|CV4_GUARDED_REGISTRATION|CV4_REJECT_ERASED_TERMINAL;
        auto ri=image(reference);char error[4096]{};double initMs=0;
        if(CrackV4CreateExtended(&ri,rp,&cfg,&exp,&handle,&initMs,error,sizeof(error)))throw std::runtime_error(error);
        // Keep handle for the complete acquisition stream. Pass tracked cp for
        // each frame; use nullptr only when the current pair is unavailable.
        auto ci=image(current);CrackV4Result result{};result.struct_size=sizeof(result);
        if(CrackV4Process(handle,&ci,cp,&result))throw std::runtime_error(CrackV4LastJson(handle));
        CrackV4ResultV2 pixel{};pixel.struct_size=sizeof(pixel);pixel.api_version=2;
        if(CrackV4GetResultV2(handle,&pixel))throw std::runtime_error("V2 query failed");
        std::cout<<"tip=("<<pixel.tip_px.x<<','<<pixel.tip_px.y<<") valid="<<pixel.tip_confirmed
            <<" length_px="<<pixel.root_to_tip_length_px<<" valid="<<pixel.complete_length_valid
            <<" detector_ms="<<pixel.detector_ms<<'\n'<<CrackV4LastQualityJson(handle)<<'\n'<<CrackV4LastGeometryJson(handle)<<'\n';
        CrackV4Destroy(handle);return 0;
    }catch(const std::exception &e){if(handle)CrackV4Destroy(handle);std::cerr<<e.what()<<'\n';return 1;}
}
