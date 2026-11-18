#include "CrackV4.hpp"
#include <opencv2/imgcodecs.hpp>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>

static cv::Mat grayImage(const wchar_t* file) {
    std::ifstream input(std::filesystem::path(file), std::ios::binary);
    if (!input) throw std::runtime_error("Cannot open input image");
    std::vector<unsigned char> bytes{std::istreambuf_iterator<char>(input), {}};
    return cv::imdecode(bytes, cv::IMREAD_GRAYSCALE);
}

int wmain(int argc, wchar_t** argv) {
    if (argc < 8 || (argc - 3) % 5 != 0) {
        std::cerr << "Usage: CrackV4Example MODE MM_PER_PIXEL IMAGE P1X P1Y P2X P2Y [IMAGE P1X P1Y P2X P2Y ...]\n";
        return 2;
    }
    try {
        const auto mode = static_cast<CrackV4Detector::ReferenceMode>(std::stoi(argv[1]));
        const double ratio = std::stod(argv[2]);
        CrackV4Detector detector;  // Same object for the entire sequence.
        std::cout << std::setprecision(17);
        for (int index = 3; index < argc; index += 5) {
            const cv::Mat gray = grayImage(argv[index]);
            const cv::Point2d p1(std::stod(argv[index + 1]), std::stod(argv[index + 2]));
            const cv::Point2d p2(std::stod(argv[index + 3]), std::stod(argv[index + 4]));
            CrackV4Result result{};
            if (index == 3) {
                detector.initialize(gray, p1, p2, mode, ratio);
                result = detector.referenceResult();
            } else {
                detector.getCrackTipPointCirculate(gray, p1, p2, &result);
            }
            const auto state = detector.resultV2();
            const auto segments = detector.pathSegments();
            std::cout << state.frame_index << ' ' << state.tip_confirmed << ' ' << state.complete_length_valid
                      << ' ' << state.tip_px.x << ' ' << state.tip_px.y << ' ' << state.root_to_tip_length_px
                      << ' ' << result.length_mm << ' ' << state.detector_ms << ' ' << segments.size();
            for (const auto& line : segments) {
                std::cout << ' ' << line.size();
                for (const auto& point : line) std::cout << ' ' << point.x << ' ' << point.y;
            }
            std::cout << '\n';
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
    return 0;
}
