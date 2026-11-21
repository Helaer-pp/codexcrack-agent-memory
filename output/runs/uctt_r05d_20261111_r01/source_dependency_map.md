# 当前生产调用链

初始化 choosePatches -> 固定 origin/spacing/forward -> 每帧 CrackV4Process -> Detector::process -> motion（主路径）及 estimateTipMotion（端点独立）-> 主路径 seed/tile/Frangi -> measureTip覆盖最终尖端 -> tipWindow -> localReference -> 暗线/参考score -> distalLine -> 非空路径直接确认 -> V2返回。主路径仅参与完整长度，不决定端点是否存在。

端点DP是自由起点，best=0允许任意列重新起步；没有显式物理主裂纹身份验证。主路径Frangi图未导出，端点实际score/gains/back均已导出。逐tile相关值和票数由同一原生函数stateless重算，注册后float数组与D0逐位hash一致，见traces/*__local.json。主路径完整Frangi数组标NOT_EXPOSED，不用替代算法补画。

- `CrackV4.cpp:748` `bool Detector::estimateTipMotion(const cv::Mat &im) {`
- `CrackV4.cpp:911` `void Detector::motion(const cv::Mat &im, const std::array<P, 2> *ap, bool isref, double &response,`
- `CrackV4.cpp:2245` `int CrackV4Process(CrackV4Handle h, const CrackV4Image *current, const CrackV4Point *cp,`
- `roi_tip.inc:8` `cv::Rect tipWindow(P center,double spacing,int turn,cv::Size image) {`
- `roi_tip.inc:25` `cv::Mat1b localReference(const cv::Mat &ref,const cv::Mat &im,cv::Rect roi,`
- `roi_tip.inc:68` `Path distalLine(const cv::Mat1f &score,const cv::Mat1f &intensity,bool absolute) {`
- `roi_tip.inc:88` `if(g<(absolute?55:12) || score(y,x)<3.f) continue;`
- `roi_tip.inc:139` `if(shared<4)return {};`
- `roi_tip.inc:146` `void Detector::measureTip(Result &r,const cv::Mat &im,P center,P roiDirection,bool isReference) {`
- `roi_tip.inc:149` `r.tip=r.has=r.path_valid=r.terminal=r.length=r.root=false;`
- `roi_tip.inc:150` `r.endpoint=r.tipxy=r.first=r.rootxy=r.rootref={};`
- `roi_tip.inc:224` `r.tip=r.has=r.path_valid=r.terminal=!path.empty();`
- `roi_tip.inc:225` `r.endpoint=r.tipxy=r.tip?path.back():P();`

原始生产源码见source_evidence/，trace为生成副本的只读采集。主路径采样ROI为变换后的网格多边形，并非端点ROI。端点尺度1、0-based整数像素中心，quarter-turn逆映射后加roi.tl。
