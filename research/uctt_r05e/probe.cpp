// Stateless diagnostic only. Reuses the exact generated legacy recurrence;
// its current-only peaks must match B1 current-source peaks before any GT query.
#include "../../output/build/uctt_r05e_source/CrackV4.cpp"
static thread_local r05d::Trace probe_trace;
static thread_local std::string probe_result;
extern "C" {
__declspec(dllexport) const char* R05ECurrentProbe(const float* scores,const float* intensity,int h,int w){
 probe_trace={};r05d::Guard guard(&probe_trace);bool old=r05d::capture;r05d::capture=true;
 cv::Mat1f score(h,w,const_cast<float*>(scores)),im(h,w,const_cast<float*>(intensity));auto path=distalLine(score,im,false);r05d::capture=old;
 std::ostringstream o;o<<std::setprecision(17)<<"{\"peaks\":[";for(size_t i=0;i<probe_trace.peaks.size();++i){if(i)o<<',';auto&p=probe_trace.peaks[i];o<<"{\"xy\":["<<p.x<<','<<p.y<<"],\"gain\":"<<p.gain<<'}';}o<<"]}";probe_result=o.str();return probe_result.c_str();
}
__declspec(dllexport) const void* R05EProbeGain(int*rows,int*cols,int*stride){auto&m=probe_trace.gains;*rows=m.rows;*cols=m.cols;*stride=int(m.step);return m.data;}
}
