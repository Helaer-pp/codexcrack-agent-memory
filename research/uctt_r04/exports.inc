// Appended only to generated experimental translation unit.
namespace {
std::string r04Describe(Detector &d,const cv::Mat &im,bool reference){
 const Result &raw=reference?d.reference_result:d.last;uint64_t frame=reference?0:raw.frame_index;
 if(d.r04_seen==frame)return d.r04_json;
 auto begin=Clock::now();auto &tr=d.r04_trace;
 auto a=r04::audit(im,raw.observed,tr.prefix,tr.root,d.tip_roi);
 bool motion=reference||d.tip_registration_valid;auto R=reference?cv::Matx22d::eye():d.tip_rotation;P t=reference?P():d.tip_translation;
 d.r04_states[0].step(raw.tipxy,raw.tip&&a.structure_only,motion,R,t,d.tip_roi,im.size(),frame);
 d.r04_states[1].step(raw.tipxy,raw.tip&&a.prefix_connected,motion,R,t,d.tip_roi,im.size(),frame);
 std::vector<r04::Audit> branchAudit;for(auto &b:tr.branches)branchAudit.push_back(r04::audit(im,b.original,tr.prefix,tr.root,d.tip_roi));
 double audit_ms=elapsed(begin);std::ostringstream o;o<<std::setprecision(17);
 auto point=[&](P p){o<<'['<<p.x<<','<<p.y<<']';};
 auto path=[&](const Path &p){o<<'[';for(size_t i=0;i<p.size();++i){if(i)o<<',';point(p[i]);}o<<']';};
 auto describe=[&](const r04::Audit &v){o<<"{\"support\":"<<v.path.support<<",\"contrast\":"<<v.path.contrast<<",\"noise\":"<<v.path.noise<<",\"width\":"<<v.path.width<<",\"polarity\":"<<v.path.polarity<<",\"max_gap\":"<<v.path.max_gap<<",\"samples\":"<<v.path.samples<<",\"prefix_support\":"<<v.prefix.support<<",\"connection_distance\":";if(v.connection_distance<0)o<<"null";else o<<v.connection_distance;o<<",\"overlap_fraction\":"<<v.overlap_fraction<<",\"tangent_alignment\":"<<v.tangent_alignment<<",\"S_before\":"<<v.before<<",\"S_ahead\":"<<v.ahead<<",\"S_terminal\":"<<v.terminal<<",\"S_compete\":null,\"S_delta\":null,\"edge\":"<<v.edge<<",\"D1_structure_only\":"<<v.structure_only<<",\"D2_prefix_connected\":"<<v.prefix_connected<<",\"reason\":"<<escaped(v.reason)<<'}';};
 o<<"{\"frame_index\":"<<frame<<",\"audit_ms\":"<<audit_ms<<",\"prefix_root_supported_proxy\":"<<tr.root<<",\"prefix\":";path(tr.prefix);
 o<<",\"audit\":";describe(a);o<<",\"states\":[";
 for(int i=0;i<2;++i){if(i)o<<',';auto&s=d.r04_states[i];o<<"{\"method\":"<<i+1<<",\"source\":"<<escaped(s.source)<<",\"valid\":"<<s.valid<<",\"output\":";point(s.output);o<<",\"last_confirmed\":";if(s.has)point(s.last);else o<<"null";o<<",\"last_confirmed_frame\":"<<s.last_frame<<",\"history_written\":"<<s.valid<<'}';}
 o<<"],\"branches\":[";
 for(size_t i=0;i<tr.branches.size();++i){if(i)o<<',';auto&b=tr.branches[i];o<<"{\"candidate_id\":"<<i<<",\"gain\":"<<b.gain<<",\"path\":";path(b.original);o<<",\"audit\":";describe(branchAudit[i]);o<<'}';}
 o<<"],\"tip_motion_valid\":"<<motion<<",\"tip_inliers\":"<<d.tip_registration_inliers<<",\"tip_transform\":["<<R(0,0)<<','<<R(0,1)<<','<<t.x<<','<<R(1,0)<<','<<R(1,1)<<','<<t.y<<"],\"diagnostic_ms\":"<<elapsed(begin)<<'}';
 d.r04_seen=frame;d.r04_json=o.str();return d.r04_json;
}
}
extern "C" {
__declspec(dllexport) int R04Process(CrackV4Handle h,const CrackV4Image *im,const CrackV4Point *p,CrackV4Result *r){
 int rc=CrackV4Process(h,im,p,r);if(rc)return rc;
 auto &d=*static_cast<Detector*>(h);std::lock_guard<std::mutex> lock(d.mutex);
 try{r04Describe(d,view(im),false);return 0;}catch(...){return -2;}
}
__declspec(dllexport) const char* R04Observe(CrackV4Handle h,const CrackV4Image *im,int reference){
 if(!h)return "{}";auto &d=*static_cast<Detector*>(h);std::lock_guard<std::mutex> lock(d.mutex);
 try{r04Describe(d,view(im),reference!=0);return d.r04_json.c_str();}catch(...){return "{}";}
}
__declspec(dllexport) const void* R04Map(CrackV4Handle h,int kind,int *rows,int *cols,int *type,int *stride){
 if(!h)return nullptr;auto &d=*static_cast<Detector*>(h);auto&t=d.r04_trace;
 const cv::Mat &m=kind==0?t.current:kind==1?t.score:kind==2?t.registered:kind==3?t.prior:d.baseline_mask;
 *rows=m.rows;*cols=m.cols;*type=m.type();*stride=int(m.step);return m.data;
}
}
