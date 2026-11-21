# C++ 实际完成范围
新增研究专用 CrackV4AP3Observer.dll，只增加 seed 门槛和 tile 观察；不包含 A′3 Python 候选、选块及联合判决。
使用项目内 OpenCV 4.4.0 SDK（来自用户 D:/opencv-4.4.0）、MSVC v142 编译；见 configure.log/build_observer.log。
AP3 observer 在 3035 帧真实图和 540 帧曝光 DEV 上对照原生结果，状态、坐标、弧长、float64 路径完全一致。
隔离媒体/DEV负载的双原生计时是 A 与原 AP2 tile observer；AP3 seed observer 运行时与研究计算并发，不能把它当独立性能测试。
完整 A′3 原生15Hz：NOT_TESTED。联合研究 Gate 不足，未移植发布全算法 DLL。所有 DLL 仅在 output/build/Release，冻结生产 DLL 不变。
