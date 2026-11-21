#include "CrackV4.hpp"
#include <iomanip>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <iostream>
#include <opencv2/imgcodecs.hpp>
#ifdef _WIN32
int wmain(int argc, wchar_t **argv) {
#else
int main(int argc, char **argv) {
#endif
    if (argc != 11) {
        std::cout
            << "usage: example reference.bmp current.bmp refX1 refY1 refX2 refY2 curX1 curY1 curX2 curY2\n";
        return 2;
    }
    try {
        auto read=[](const std::filesystem::path& path){
            std::ifstream f(path,std::ios::binary);
            std::vector<uchar> bytes((std::istreambuf_iterator<char>(f)),std::istreambuf_iterator<char>());
            if(bytes.empty())throw std::runtime_error("Cannot read image file");
            return cv::imdecode(bytes,cv::IMREAD_GRAYSCALE);
        };
        cv::Mat reference = read(std::filesystem::path(argv[1]));
        cv::Mat current = read(std::filesystem::path(argv[2]));
        CrackV4SetNumThreads(4);
        CrackV4Detector detector;
        double initializationMs = detector.initialize(reference, {std::stod(argv[3]), std::stod(argv[4])},
                                                      {std::stod(argv[5]), std::stod(argv[6])},
                                                      CrackV4Detector::ReferenceMode::Auto);
        CrackV4Result result{};
        cv::Point2d tip =
            detector.getCrackTipPointCirculate(current, {std::stod(argv[7]), std::stod(argv[8])},
                                               {std::stod(argv[9]), std::stod(argv[10])}, &result);
        std::cout << std::fixed << std::setprecision(4) << "tip=" << tip << " valid=" << result.tip_confirmed
                  << " length_px=" << result.length_px << " length_valid=" << result.length_confirmed
                  << " detector_ms=" << result.detector_ms << " api_ms=" << result.api_ms
                  << " initialization_ms=" << initializationMs << '\n';
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
