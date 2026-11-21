// Explicitly offline S1 intervention. Never loaded by the chronological runner.
#include "runtime.cpp"
extern "C" __declspec(dllexport) int R05FDiagnosticBudget(void*h){
 if(!h)return -1;auto&d=*static_cast<r05f::Detector*>(h);
 d.cfg.maxSegments*=8;d.cfg.maxCandidates*=8;return 0;
}
// Offline export of an ACTUAL previously visited window, with the same native
// sampler and NMS. Caller buffers have exactly window.w * window.h elements.
// This probe initializes from the queried current image, so fixed == current.
extern "C" __declspec(dllexport) int R05FWindowAudit(void*h,int index,float*score,unsigned char*valid,unsigned char*ridge,int*labels){
 try{if(!h||!score||!valid||!ridge||!labels)return -1;auto&d=*static_cast<r05f::Detector*>(h);if(index<0||index>=int(d.last.windows.size()))return -1;
  auto w=d.last.windows[index];r05f::Frame f;f.visited=cv::Mat1b(d.fixed.size(),uchar(0));auto p=r05f::sampleCurrent(d.fixed,w,f,d.last.spacing);
  cv::Mat1b r(w.h,w.w,uchar(0));for(int y=1;y<w.h-1;++y)for(int x=1;x<w.w-1;++x)if(p.score(y,x)>=d.cfg.response&&p.score(y,x)>=p.score(y-1,x)&&p.score(y,x)>p.score(y+1,x))r(y,x)=255;
  cv::Mat1i l;cv::connectedComponents(r,l,8,CV_32S);size_t count=size_t(w.w)*w.h;
  std::copy(p.score.ptr<float>(),p.score.ptr<float>()+count,score);std::copy(p.valid.ptr<uchar>(),p.valid.ptr<uchar>()+count,valid);std::copy(r.ptr<uchar>(),r.ptr<uchar>()+count,ridge);std::copy(l.ptr<int>(),l.ptr<int>()+count,labels);return int(count);
 }catch(...){return -2;}
}
