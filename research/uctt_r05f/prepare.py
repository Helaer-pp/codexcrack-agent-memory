from common import *
import shutil,difflib,winreg,platform
def replace(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def main():
 OUT.mkdir(parents=True,exist_ok=False);GEN.mkdir(parents=True,exist_ok=True)
 for n in ['experiments','logs','traces','tests','galleries/images','source_snapshot']:(OUT/n).mkdir(parents=True)
 protected={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'src/cpp/a').rglob('*') if p.is_file()}
 for folder in ['config','data/anchors']:
  for p in (ROOT/folder).rglob('*'):
   if p.is_file():protected[str(p.relative_to(ROOT))]=sha(p)
 for n in ['output/build/src/cpp/a/Release/CrackV4.dll','output/releases/A_Win64_OpenCV440/bin/CrackV4.dll']:protected[n]=sha(ROOT/n)
 assert protected['output/build/src/cpp/a/Release/CrackV4.dll']=='55a0e7a79162da79e691ede9ff58229e59a56fdd1e0b1e3f609dc51128860402'
 priors=[PRE/'input_inventory.csv',R05/'active_selection_manifest.csv',R05/'human_annotations_six_groups_snapshot.zip',R05/'production_tip_comparison.csv',D/'dev_frames.jsonl',D/'val_frames.jsonl',E/'artifact_manifest.json',E/'final_integrity.json',E/'gate_matrix.csv',E/'evaluation_B2_dev.csv']
 reports=['phase1_acceptance_r02/development_report.md','phase1_r03_dynamic_roi_20261110_r01/development_report.md','uctt_r04_path_tip_20261111_r01/development_report.md','r05_annotation_validation_20261111_r01/validation_report.md','uctt_r05d_20261111_r01/development_report.md','uctt_r05e_20261111_r01/development_report.md']
 priors += [ROOT/'output/runs'/p for p in reports]
 inventory=filter_rows(rows(PRE/'input_inventory.csv'),'validation');selected=filter_rows(rows(R05/'active_selection_manifest.csv'),'validation')
 assert len(inventory)==2647 and len(selected)==120
 save(OUT/'input_inventory_allowed.csv',inventory);save(OUT/'selected_frames.csv',selected)
 with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as k:cpu=winreg.QueryValueEx(k,'ProcessorNameString')[0].strip()
 write(OUT/'baseline_manifest.json',dict(protected=protected,prior_inputs={str(p.relative_to(ROOT)):sha(p) for p in priors},cpu=cpu,platform=platform.platform(),git_commit=None,git_reason='No git metadata in active project',dataset_policy=read(POLICY_PATH),flags=3572,policy=1,terminal=1,refine=True,threads=4,original_annotations_read_by_runtime=False))
 source=(ROOT/'src/cpp/a/CrackV4.cpp').read_text(encoding='utf8');roi=(ROOT/'src/cpp/a/roi_tip.inc').read_text(encoding='utf8')
 s=replace(source,'namespace {','#include "profile.hpp"\nnamespace {')
 s=replace(s,'    cv::Rect tip_roi, reference_roi;','    fprofile::Times f_times; std::string f_json;\n    cv::Rect tip_roi, reference_roi;')
 s=replace(s,'Result Detector::process(const cv::Mat &im, const std::array<P, 2> *ap, bool isref) {','Result Detector::process(const cv::Mat &im, const std::array<P, 2> *ap, bool isref) {\n    f_times={};fprofile::Guard fguard(&f_times);')
 q=replace(roi,'    cv::Mat1b aligned(roi.size(),uchar(0));','    fprofile::Scope localTimer(fprofile::active?&fprofile::active->local:nullptr);\n    cv::Mat1b aligned(roi.size(),uchar(0));')
 q=replace(q,'                cv::matchTemplate(ref(area),im(small),map,cv::TM_CCOEFF_NORMED);','                {fprofile::Scope matchTimer(fprofile::active?&fprofile::active->matching:nullptr);if(fprofile::active)++fprofile::active->calls;cv::matchTemplate(ref(area),im(small),map,cv::TM_CCOEFF_NORMED);}')
 q=replace(q,'    int h=score.rows,w=score.cols;','    fprofile::Scope dpTimer(fprofile::active?&fprofile::active->dp:nullptr);\n    int h=score.rows,w=score.cols;')
 q=replace(q,'    Path best;','    fprofile::Scope auditTimer(fprofile::active?&fprofile::active->audit:nullptr);\n    Path best;')
 q=replace(q,'void Detector::measureTip(Result &r,const cv::Mat &im,P center,P roiDirection,bool isReference) {','void Detector::measureTip(Result &r,const cv::Mat &im,P center,P roiDirection,bool isReference) {\n    fprofile::Guard fguard(&f_times);')
 q=replace(q,'        for(int y=5;y<current.rows-5;++y) for(int x=4;x<current.cols-4;++x) {','        {fprofile::Scope scoreTimer(&f_times.score);\n        for(int y=5;y<current.rows-5;++y) for(int x=4;x<current.cols-4;++x) {')
 q=replace(q,'        path=distalLine(score,current,isReference);','        }\n        path=distalLine(score,current,isReference);')
 exports='''\nextern "C" __declspec(dllexport) const char* R05FProfile(CrackV4Handle h){auto&d=*static_cast<Detector*>(h);auto&t=d.f_times;std::ostringstream o;o<<std::setprecision(17)<<"{\\"local_reference_ms\\":"<<t.local-t.matching<<",\\"match_template_ms\\":"<<t.matching<<",\\"match_calls\\":"<<t.calls<<",\\"legacy_score_ms\\":"<<t.score<<",\\"legacy_dp_ms\\":"<<t.dp-t.audit<<",\\"legacy_terminal_ms\\":"<<t.audit<<'}';d.f_json=o.str();return d.f_json.c_str();}\n'''
 for p in (ROOT/'src/cpp/a').glob('*.inc'):shutil.copy2(p,GEN/p.name)
 (GEN/'CrackV4.cpp').write_text(s+exports,encoding='utf8');(GEN/'roi_tip.inc').write_text(q,encoding='utf8')
 (OUT/'A0_instrumentation.patch').write_text(''.join(difflib.unified_diff(source.splitlines(True),(s+exports).splitlines(True)))+''.join(difflib.unified_diff(roi.splitlines(True),q.splitlines(True))),encoding='utf8')
 write(OUT/'A0_build_source_lock.json',dict(original=protected,generated={str(p.relative_to(ROOT)):sha(p) for p in GEN.glob('*') if p.is_file()},profile_header=sha(ROOT/'research/uctt_r05f/profile.hpp')))
 print('S0 PREPARED',OUT,flush=True)
if __name__=='__main__':main()
