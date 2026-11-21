namespace {
std::string r05dDescribe(Detector &d){
 auto&t=d.r05d_trace;std::ostringstream o;o<<std::setprecision(17);
 auto point=[&](P p){o<<'['<<p.x<<','<<p.y<<']';};
 auto rect=[&](cv::Rect r){o<<'['<<r.x<<','<<r.y<<','<<r.width<<','<<r.height<<']';};
 auto path=[&](const Path&p){o<<'[';for(size_t i=0;i<p.size();++i){if(i)o<<',';point(p[i]);}o<<']';};
 auto transform=[&](cv::Matx22d r,P p){o<<'['<<r(0,0)<<','<<r(0,1)<<','<<p.x<<','<<r(1,0)<<','<<r(1,1)<<','<<p.y<<']';};
 o<<"{\"roi\":";rect(t.roi);o<<",\"actual_tip_roi\":";rect(d.tip_roi);
 o<<",\"reference\":"<<t.reference<<",\"turn\":"<<t.turn<<",\"center\":";point(t.center);o<<",\"direction\":";point(t.direction);
 o<<",\"origin\":";point(d.origin);o<<",\"forward\":";point(d.forward);o<<",\"spacing\":"<<d.spacing;
 o<<",\"reference_size\":["<<d.reference.cols<<','<<d.reference.rows<<"],\"init_anchors\":[";point(d.anchors[0]);o<<',';point(d.anchors[1]);o<<']';
 o<<",\"tip_transform\":";transform(d.tip_rotation,d.tip_translation);o<<",\"main_transform\":";transform(d.rotation,d.translation);
 o<<",\"registration_valid\":"<<t.registration<<",\"motion_branch\":"<<escaped(t.motion_branch)<<",\"solve_angle\":"<<t.solve_angle<<",\"solve_residual\":"<<t.solve_residual<<",\"solve_inliers\":"<<t.solve_inliers<<",\"solve_matches\":"<<t.solve_matches;
 o<<",\"matches\":[";for(size_t i=0;i<t.matches.size();++i){if(i)o<<',';auto&m=t.matches[i];o<<"{\"rect\":";rect(m.rect);o<<",\"delta\":";point(m.delta);o<<",\"quality\":"<<m.quality<<",\"second\":"<<m.second<<",\"method\":"<<escaped(m.method)<<'}';}o<<']';
 o<<",\"main_rois\":[";for(size_t i=0;i<t.main_rois.size();++i){if(i)o<<',';path(t.main_rois[i]);}o<<']';
 o<<",\"main_path_before_endpoint\":";path(t.mainpath);o<<",\"selected_local\":";path(t.local);o<<",\"selected_original\":";path(t.original);
 o<<",\"terminal_cause\":"<<escaped(t.terminal)<<",\"peaks\":[";
 for(size_t i=0;i<t.peaks.size();++i){if(i)o<<',';auto&p=t.peaks[i];o<<"{\"id\":"<<i<<",\"xy\":["<<p.x<<','<<p.y<<"],\"gain\":"<<p.gain<<",\"stage\":"<<escaped(p.stage)<<",\"hits\":"<<p.hits<<",\"tail_hits\":"<<p.tail<<",\"shared\":"<<p.shared<<",\"slope\":"<<p.slope<<",\"line_local_reverse\":";path(p.line);o<<'}';}o<<"]}";
 return o.str();
}
}
extern "C" {
__declspec(dllexport) uint64_t R05DHashBytes(const unsigned char* p,size_t n){uint64_t hash=1469598103934665603ULL;for(size_t i=0;i<n;++i){hash^=p[i];hash*=1099511628211ULL;}return hash;}
__declspec(dllexport) const char* R05DProbeEvidence(const float* scores,const float* current,const unsigned char* reasons,int h,int w,int variant){
 static thread_local std::string result;r05d::Trace tr;r05d::Guard guard(&tr);r05d::capture=true;
 cv::Mat1f score=cv::Mat1f(h,w,const_cast<float*>(scores)).clone();cv::Mat1f intensity(h,w,const_cast<float*>(current));
 int changed=0;if(variant==4)for(int y=5;y<h-5;++y)for(int x=4;x<w-4;++x)if(reasons[y*w+x]==2){score(y,x)=std::min(intensity(y-4,x),intensity(y+4,x))-intensity(y,x);++changed;}
 auto path=distalLine(score,intensity,false);std::ostringstream o;o<<std::setprecision(17)<<"{\"changed_pixels\":"<<changed<<",\"selected_local\":[";
 for(size_t i=0;i<path.size();++i){if(i)o<<',';o<<'['<<path[i].x<<','<<path[i].y<<']';}o<<"],\"peaks\":[";
 for(size_t i=0;i<tr.peaks.size();++i){if(i)o<<',';auto&p=tr.peaks[i];o<<"{\"xy\":["<<p.x<<','<<p.y<<"],\"gain\":"<<p.gain<<",\"stage\":"<<escaped(p.stage)<<'}';}o<<"]}";result=o.str();return result.c_str();
}
// Stateless re-execution of EXACT localReference, using previously traced
// geometry. It cannot change a Detector and takes no human coordinates.
__declspec(dllexport) const char* R05DAuditLocal(const CrackV4Image* reference,const CrackV4Image* current,int x,int y,int w,int h,int dx,int dy,int turn){
 static thread_local std::string result; r05d::Trace tr;r05d::Guard guard(&tr);r05d::capture=true;
 cv::Mat1b known;auto aligned=localReference(view(reference),view(current),cv::Rect(x,y,w,h),cv::Point(dx,dy),known,cv::Mat());
 std::ostringstream o;o<<std::setprecision(17)<<"{\"tiles\":[";
 for(size_t i=0;i<tr.local_tiles.size();++i){if(i)o<<',';auto&t=tr.local_tiles[i];o<<"{\"tile\":["<<t.tile.x<<','<<t.tile.y<<','<<t.tile.width<<','<<t.tile.height<<"],\"votes\":"<<t.votes<<",\"agree\":"<<t.agree<<",\"offset\":["<<t.offset.x<<','<<t.offset.y<<"],\"stage\":"<<escaped(t.stage)<<",\"correlations\":[";for(size_t j=0;j<t.correlations.size();++j){if(j)o<<',';if(std::isfinite(t.correlations[j]))o<<t.correlations[j];else o<<"null";}o<<"]}";}
 // Bitwise hash of the actual registered float image is checked in Python.
 cv::Mat1f reg;aligned.convertTo(reg,CV_32F);cv::GaussianBlur(reg,reg,{3,3},.8);orientWindow(reg,turn);
 uint64_t hash=1469598103934665603ULL;const unsigned char* p=reg.ptr<unsigned char>();for(size_t i=0;i<reg.total()*4;++i){hash^=p[i];hash*=1099511628211ULL;}
 o<<"],\"registered_fnv64\":\""<<hash<<"\"}";result=o.str();return result.c_str();
}
__declspec(dllexport) void R05DCapture(int enabled){r05d::capture=enabled!=0;}
__declspec(dllexport) const char* R05DRead(CrackV4Handle h){if(!h)return "{}";auto&d=*static_cast<Detector*>(h);std::lock_guard<std::mutex> lock(d.mutex);d.r05d_json=r05dDescribe(d);return d.r05d_json.c_str();}
__declspec(dllexport) const void* R05DMap(CrackV4Handle h,int kind,int *rows,int *cols,int *type,int *stride){
 if(!h)return nullptr;auto&d=*static_cast<Detector*>(h);auto&t=d.r05d_trace;
 const cv::Mat&m=kind==0?t.current:kind==1?t.score:kind==2?t.registered:kind==3?t.prior:kind==4?t.reason:kind==5?t.valid:kind==6?t.gains:t.back;
 *rows=m.rows;*cols=m.cols;*type=m.type();*stride=int(m.step);return m.data;
}
#ifdef R05D_OFFLINE
// Explicit OFFLINE side-effect-restored measurement. Only original image input
// plus a fixed diagnostic variant; no label, human coordinate or fitted value.
__declspec(dllexport) int R05DOffline(CrackV4Handle h,const CrackV4Image* input,int variant){
 if(!h || (variant!=1 && variant!=2 && variant!=3))return -1;
 auto&d=*static_cast<Detector*>(h);std::lock_guard<std::mutex> lock(d.mutex);
 auto oldTrace=d.r05d_trace;auto oldRoi=d.tip_roi;auto rotation=d.tip_rotation;auto translation=d.tip_translation;bool valid=d.tip_registration_valid;
 try{
  r05d::offline_variant=variant;r05d::offline_fixed_roi=oldRoi;d.r05d_trace={};Result candidate=d.last;auto originalDirection=d.tipDirection();
  // CF2 changes only the registration transform feeding the independent ROI.
  // Coarse main-image transform is an alternative, not asserted to be truth.
  if(variant==2){d.tip_rotation=d.rotation;d.tip_translation=d.translation;}
  d.measureTip(candidate,view(input),d.tipCenter(),originalDirection,false);
  d.r05d_json=r05dDescribe(d);d.tip_roi=oldRoi;d.tip_rotation=rotation;d.tip_translation=translation;d.tip_registration_valid=valid;r05d::offline_variant=0;
  // Keep isolated offline trace until next normal frame; detector last/history unchanged.
  return 0;
 }catch(...){d.r05d_trace=oldTrace;d.tip_roi=oldRoi;d.tip_rotation=rotation;d.tip_translation=translation;d.tip_registration_valid=valid;r05d::offline_variant=0;return -2;}
}
__declspec(dllexport) const char* R05DOfflineRead(CrackV4Handle h){return static_cast<Detector*>(h)->r05d_json.c_str();}
#endif
}
