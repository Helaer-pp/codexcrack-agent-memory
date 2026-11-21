import json,shutil,os,platform,difflib,winreg
from common import *
def main():
 OUT.mkdir(parents=True,exist_ok=False);GEN.mkdir(parents=True,exist_ok=True)
 protected={}
 for folder in ['src/cpp/a','research/uctt_r03','output/runs/phase1_audit_decoupling_20261110_r01','output/runs/phase1_acceptance_r02','output/runs/phase1_r03_dynamic_roi_20261110_r01']:
  protected.update(tree(ROOT/folder))
 for file in ['config/project.json','config/datasets.json','data/inputs/six_groups_manifest.csv','output/build/src/cpp/a/Release/CrackV4.dll','output/releases/A_Win64_OpenCV440/bin/CrackV4.dll']:
  protected[file]=sha(ROOT/file)
 old=json.loads((R03/'frozen_manifest_r03.json').read_text());changed=[p for p,h in old['protected_files'].items() if sha(ROOT/p)!=h];assert not changed,changed
 with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as k:cpu=winreg.QueryValueEx(k,'ProcessorNameString')[0].strip()
 write('frozen_manifest_r04.json',dict(protected=protected,prior_R03_protected_match=True,platform=platform.platform(),cpu=cpu,logical_cpus=os.cpu_count(),threads=4,flags=3572,policy=1,terminal=1,refine=True,opencv='4.4.0 native',compiler='MSVC v142 x64 Release /O2 /fp:precise',GT='UNAVAILABLE',holdout='NO_INDEPENDENT_HOLDOUT',source_hashes=tree(ROOT/'research/uctt_r04')))
 write('selection.json',dict(selection_seed=None,reason='Deterministic R04 supplied failure neighborhoods and chronological stable controls, before new results',windows=WINDOWS,variants=VARIANTS,full_R03_cases=1428,full_R02_matrix='GATED',roles={'group_x':'EXPOSURE','ct3':'REGRESSION','three_point_bend':'REGRESSION','group_a':'INSUFFICIENT_SUPPORT','ct2':'DEBUG','group_h':'DEBUG','group_c':'DEBUG'}))
 # Generated copies are experiments; all active source instructions remain in research.
 for f in (ROOT/'src/cpp/a').glob('*.inc'):shutil.copy2(f,GEN/f.name)
 source=(ROOT/'src/cpp/a/CrackV4.cpp').read_text(encoding='utf8');roi=(ROOT/'src/cpp/a/roi_tip.inc').read_text(encoding='utf8')
 def replace(s,a,b):assert s.count(a)==1,a;return s.replace(a,b)
 patched=replace(source,'namespace {','#include "audit.hpp"\nnamespace {')
 patched=replace(patched,'    cv::Rect tip_roi, reference_roi;','    r04::Trace r04_trace,r04_reference_trace;\n    r04::State r04_states[2];\n    uint64_t r04_seen=~uint64_t(0);\n    std::string r04_json;\n    cv::Rect tip_roi, reference_roi;')
 patched=replace(patched,'    void resetTemporal() {','    void resetTemporal() {\n        r04_seen=~uint64_t(0);r04_states[0]={};r04_states[1]={};r04_trace=r04_reference_trace;')
 patched=replace(patched,'        reference_roi=tip_roi;','        reference_roi=tip_roi;\n        r04_reference_trace=r04_trace;')
 # Add disjoint top-level profile timers. Existing nested timers kept, never summed.
 patched=replace(patched,'std::array<double, 16> profile_ms','std::array<double, 24> profile_ms')
 patched=replace(patched,'bool Detector::estimateTipMotion(const cv::Mat &im) {','bool Detector::estimateTipMotion(const cv::Mat &im) {\n    PROFILE_SCOPE(16);')
 patched=replace(patched,'    profile_ms.fill(0.);\n#endif','    profile_ms.fill(0.);\n#endif\n    PROFILE_SCOPE(20);')
 modified=replace(roi,'void Detector::measureTip(Result &r,const cv::Mat &im,P center,P roiDirection,bool isReference) {','void Detector::measureTip(Result &r,const cv::Mat &im,P center,P roiDirection,bool isReference) {\n    PROFILE_SCOPE(17);\n    r04_trace={};r04_trace.prefix=r.path;r04_trace.root=r.root;\n    r04::Active traceGuard(&r04_trace);')
 modified=replace(modified,'        std::reverse(line.begin(),line.end());','        std::reverse(line.begin(),line.end());\n        if(r04::active && r04::active->branches.size()<5)r04::active->branches.push_back({line,{},peak.gain});')
 modified=replace(modified,'        path=distalLine(score,current,isReference);','''        r04_trace.current=current.clone();r04_trace.score=score.clone();r04_trace.registered=registered.clone();r04_trace.prior=prior.clone();r04_trace.roi=tip_roi;r04_trace.turn=turn;
        path=distalLine(score,current,isReference);
        for(auto &branch:r04_trace.branches){branch.original=branch.local;for(P &p:branch.original){
            if(turn==1)p=P(tip_roi.width-1-p.y,p.x);
            else if(turn==2)p=P(tip_roi.width-1-p.x,tip_roi.height-1-p.y);
            else if(turn==3)p=P(p.y,tip_roi.height-1-p.x);
            p+=P(tip_roi.tl());}}
''')
 modified=replace(modified,'cv::Point drift,cv::Mat1b &knownCrack,const cv::Mat &mask) {','cv::Point drift,cv::Mat1b &knownCrack,const cv::Mat &mask) {\n    PROFILE_SCOPE(18);')
 modified=replace(modified,'Path distalLine(const cv::Mat1f &score,const cv::Mat1f &intensity,bool absolute) {','Path distalLine(const cv::Mat1f &score,const cv::Mat1f &intensity,bool absolute) {\n    PROFILE_SCOPE(19);')
 (GEN/'CrackV4.cpp').write_text(patched+'\n#include "exports.inc"\n',encoding='utf8');(GEN/'roi_tip.inc').write_text(modified,encoding='utf8')
 diff=''.join(difflib.unified_diff(source.splitlines(True),patched.splitlines(True),fromfile='production/CrackV4.cpp',tofile='generated/CrackV4.cpp'))+''.join(difflib.unified_diff(roi.splitlines(True),modified.splitlines(True),fromfile='production/roi_tip.inc',tofile='generated/roi_tip.inc'))
 (OUT/'instrumentation.diff').write_text(diff,encoding='utf8')
 print(OUT,'protected files',len(protected))
if __name__=='__main__':main()
