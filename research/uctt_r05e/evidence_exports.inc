extern "C" {
// Offline cost control: exact old CF4 intervention and distalLine, capture off.
// Not a detector output and not allowed to update any history.
__declspec(dllexport) double R05ECF4Cost(const float* scores,const float* intensity,const unsigned char* why,int h,int w){
 bool old=r05d::capture;r05d::capture=false;r05d::Guard guard(nullptr);auto start=r05e::Clock::now();
 cv::Mat1f score=cv::Mat1f(h,w,const_cast<float*>(scores)).clone();cv::Mat1f im(h,w,const_cast<float*>(intensity));
 for(int y=5;y<h-5;++y)for(int x=4;x<w-4;++x)if(why[y*w+x]==2)score(y,x)=std::min(im(y-4,x),im(y+4,x))-im(y,x);
 auto path=distalLine(score,im,false);double ms=r05e::elapsed(start);r05d::capture=old;return ms;
}
__declspec(dllexport) const void* R05EMap(CrackV4Handle h,int kind,int *rows,int *cols,int *stride){
 if(!h)return nullptr;auto&e=static_cast<Detector*>(h)->r05d_trace.evidence;
 const cv::Mat&m=kind==0?e.current:kind==1?e.reference:kind==2?e.change:kind==3?e.quality:kind==4?e.reason:kind==5?e.valley:kind==6?e.novel:kind==7?e.debug_eroded:kind==8?e.debug_refmin:e.debug_refmax;
 *rows=m.rows;*cols=m.cols;*stride=int(m.step);return m.data;
}
__declspec(dllexport) const char* R05ERead(CrackV4Handle h){
 static thread_local std::string result;auto&t=static_cast<Detector*>(h)->r05d_trace;auto&e=t.evidence;std::ostringstream o;o<<std::setprecision(17);
 o<<"{\"raw_count\":"<<e.raw_total<<",\"stored_count\":"<<e.candidates.size()<<",\"merged_count\":"<<e.merged_count<<",\"retained_count\":"<<e.retained_count<<",\"budget_exhausted\":"<<e.exhausted<<",\"valid_pixels\":"<<e.valid_pixels<<",\"current_pixels\":"<<e.current_pixels<<",\"legacy_pixels\":"<<e.legacy_pixels<<",\"current_ms\":"<<e.current_ms<<",\"reference_ms\":"<<e.reference_ms<<",\"dp_ms\":"<<e.dp_ms<<",\"candidates_ms\":"<<e.candidates_ms<<",\"candidates\":[";
 for(size_t i=0;i<e.candidates.size();++i){if(i)o<<',';auto&p=e.candidates[i];o<<"{\"id\":"<<p.id<<",\"xy\":["<<p.x<<','<<p.y<<"],\"gain\":"<<p.gain<<",\"current_support\":"<<p.support<<",\"source_channel\":"<<escaped(p.source)<<",\"direction\":"<<p.direction<<",\"short_length\":"<<p.length<<",\"bucket\":"<<p.bucket<<",\"merged_id\":"<<p.merged<<",\"retained_id\":"<<p.retained<<",\"reason\":"<<escaped(p.reason)<<",\"reference_available\":"<<(e.quality(p.y,p.x)>0)<<",\"reference_support\":";if(std::isfinite(e.reference(p.y,p.x)))o<<e.reference(p.y,p.x);else o<<"null";o<<'}';}
 o<<"],\"prep_ms\":"<<t.prep_ms<<",\"tipmotion_ms\":"<<t.tipmotion_ms<<",\"localref_ms\":"<<t.localref_ms<<",\"legacydp_ms\":"<<t.legacydp_ms<<",\"tiles\":[";for(size_t i=0;i<t.local_tiles.size();++i){if(i)o<<',';auto&v=t.local_tiles[i];o<<"{\"rect\":["<<v.tile.x<<','<<v.tile.y<<','<<v.tile.width<<','<<v.tile.height<<"],\"votes\":"<<v.votes<<",\"agree\":"<<v.agree<<",\"offset\":["<<v.offset.x<<','<<v.offset.y<<"],\"stage\":"<<escaped(v.stage)<<",\"patches\":[";
  for(size_t j=0;j<v.correlations.size();++j){if(j)o<<',';o<<"{\"xy\":["<<v.positions[j].x<<','<<v.positions[j].y<<"],\"delta\":["<<v.deltas[j].x<<','<<v.deltas[j].y<<"],\"corr\":";if(std::isfinite(v.correlations[j]))o<<v.correlations[j];else o<<"null";o<<",\"vote\":"<<(v.correlations[j]>=.62)<<'}';}o<<"]}";
 }o<<"],\"sidecar_output\":null,\"trusted_history_write\":false,\"mode\":\"shadow_only\"}";result=o.str();return result.c_str();
}
}
