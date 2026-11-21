#include "CrackV4.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <opencv2/imgcodecs.hpp>
static_assert(sizeof(CrackV4Result) == 88, "Legacy x64 ABI changed");
static_assert(sizeof(CrackV4ResultV2) == 376, "V2 x64 ABI differs from tested layout");
#ifdef _WIN32
int wmain(int argc, wchar_t **argv) {
#else
int main(int argc, char **argv) {
#endif
    if (argc != 11) {
        std::cout << "reference current refX1 refY1 refX2 refY2 curX1 curY1 curX2 curY2\n";
        return 2;
    }
    try {
        auto read = [](const std::filesystem::path &path) {
            std::ifstream f(path, std::ios::binary);
            std::vector<uchar> bytes((std::istreambuf_iterator<char>(f)), {});
            return cv::imdecode(bytes, cv::IMREAD_GRAYSCALE);
        };
        CrackV4SetNumThreads(4);
        CrackV4Detector detector; // keep this object for the whole ordered sequence
        detector.initialize(read(argv[1]), {std::stod(argv[3]), std::stod(argv[4])},
                            {std::stod(argv[5]), std::stod(argv[6])},
                            CrackV4Detector::ReferenceMode::Auto, 1.0);
        detector.getCrackTipPointCirculate(read(argv[2]), {std::stod(argv[7]), std::stod(argv[8])},
                                           {std::stod(argv[9]), std::stod(argv[10])});
        auto r = detector.resultV2();
        std::cout << "tip_px=(" << r.tip_px.x << ',' << r.tip_px.y << ") tip_valid=" << r.tip_confirmed
                  << " tracking_endpoint_px=(" << r.tracking_endpoint_px.x << ',' << r.tracking_endpoint_px.y
                  << ") complete_length_px=" << r.root_to_tip_length_px
                  << " length_valid=" << r.complete_length_valid << " terminal_verified=" << r.terminal_verified
                  << " terminal_reason=" << r.terminal_reason << " detector_ms=" << r.detector_ms << '\n';
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
