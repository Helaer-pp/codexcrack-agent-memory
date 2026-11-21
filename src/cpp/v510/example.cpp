#include "CrackV510.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <opencv2/imgcodecs.hpp>

// Decode from bytes so Windows Unicode paths work with OpenCV 4.4.
static cv::Mat loadGray(const wchar_t *name) {
    std::ifstream file(std::filesystem::path(name), std::ios::binary);
    if (!file)
        throw std::runtime_error("Cannot open input image");
    std::vector<uchar> bytes((std::istreambuf_iterator<char>(file)), {});
    return cv::imdecode(bytes, cv::IMREAD_GRAYSCALE);
}
int wmain(int argc, wchar_t **argv) {
    try {
        Crack510SetNumThreads(4);
        if (argc != 11) {
            std::wcerr << L"Usage: CrackV510Example fixed.bmp current.bmp refX1 refY1 refX2 refY2 curX1 curY1 "
                          L"curX2 curY2\n";
            return 2;
        }
        auto point = [&](int i) { return cv::Point2d(std::stod(argv[i]), std::stod(argv[i + 1])); };
        CrackV510Detector detector;
        detector.initialize(loadGray(argv[1]), point(3), point(5));
        const auto baseline = detector.referenceResult();
        Crack510Result result{};
        detector.getCrackTipPointCirculate(loadGray(argv[2]), point(7), point(9), &result);
        std::cout << "baseline_status=" << baseline.status << " status=" << result.status << " tip=("
                  << result.tip.x << "," << result.tip.y << ") arc_px=" << result.path_length_px
                  << " projected_px=" << result.projected_length_px << " points=" << detector.rawPath().size()
                  << "\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << "\n";
        return 1;
    }
}
