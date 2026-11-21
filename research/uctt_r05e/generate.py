"""Generate an isolated instrumented copy; never writes production or R05D."""
from common import *
import importlib.util,shutil,difflib
def main():
 assert read(OUT/'B0_complete.json')['status']=='PASS'
 GEN.mkdir(parents=True,exist_ok=True)
 spec=importlib.util.spec_from_file_location('r05d_generator_readonly',ROOT/'research/uctt_r05d/prepare.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.ROOT=ROOT;m.OUT=OUT;m.GEN=GEN;m.generate()
 header=(ROOT/'research/uctt_r05d/trace.hpp').read_text(encoding='utf8').replace('#pragma once','#pragma once\n#include "evidence.hpp"')
 header=header.replace('struct Trace {','struct Trace {\n r05e::Evidence evidence;double prep_ms=0,tipmotion_ms=0,localref_ms=0,legacydp_ms=0;')
 header=header.replace('std::vector<double> correlations;','std::vector<double> correlations;std::vector<Point> deltas;std::vector<Point> positions;')
 (GEN/'trace.hpp').write_text(header,encoding='utf8')
 s=(GEN/'CrackV4.cpp').read_text(encoding='utf8')
 s=m.rep(s,'    if(isref) {\n        tip_rotation','    auto r05e_motion_start=r05e::Clock::now();\n    if(isref) {\n        tip_rotation')
 s=m.rep(s,'    } else tip_registration_valid=estimateTipMotion(im);','    } else tip_registration_valid=estimateTipMotion(im);\n    r05d_trace.tipmotion_ms=r05e::elapsed(r05e_motion_start);')
 (GEN/'CrackV4.cpp').write_text(s,encoding='utf8')
 q=(GEN/'roi_tip.inc').read_text(encoding='utf8')
 q=q.replace('if(r05d::active&&r05d::capture)r05d::active->valid','if(r05d::active)r05d::active->valid')
 q=q.replace('if(lt)lt->correlations.push_back(corr);','if(lt){lt->correlations.push_back(corr);lt->deltas.push_back(P(area.tl()+match-small.tl()));lt->positions.push_back(P(small.tl()));}')
 q=m.rep(q,'if(r05d::active&&r05d::capture){auto&t=*r05d::active;t.gains=gains.clone();t.back=back.clone();for(auto&p:peaks)', 'if(r05d::active){auto&t=*r05d::active;if(r05d::capture){t.gains=gains.clone();t.back=back.clone();}for(auto&p:peaks)')
 q=m.rep(q,'        im(tip_roi).convertTo(current,CV_32F);','        auto r05e_prep_start=r05e::Clock::now();\n        im(tip_roi).convertTo(current,CV_32F);')
 q=m.rep(q,'        cv::GaussianBlur(current,current,{3,3},.8);','        cv::GaussianBlur(current,current,{3,3},.8);\n        tr.prep_ms=r05e::elapsed(r05e_prep_start);')
 q=m.rep(q,'            auto aligned=localReference(reference,im,tip_roi,','            auto r05e_reference_start=r05e::Clock::now();\n            auto aligned=localReference(reference,im,tip_roi,')
 q=m.rep(q,'                cv::Point(rnd(center.x-origin.x),rnd(center.y-origin.y)),prior,baseline_mask);','                cv::Point(rnd(center.x-origin.x),rnd(center.y-origin.y)),prior,baseline_mask);\n            tr.localref_ms=r05e::elapsed(r05e_reference_start);')
 q=q.replace('        path=distalLine(score,current,isReference);','''        cv::Mat1b spatial=tr.valid.clone();orientWindow(spatial,turn);
        auto r05e_legacy_start=r05e::Clock::now();
        path=distalLine(score,current,isReference);
        tr.legacydp_ms=r05e::elapsed(r05e_legacy_start);
        r05e::channels(tr.evidence,current,registered,eroded,refMin,refMax,prior,spatial,score);
        std::vector<cv::Point3f> legacy_peaks;for(auto&p:tr.peaks)legacy_peaks.emplace_back(float(p.x),float(p.y),float(p.gain));
        r05e::candidates(tr.evidence,legacy_peaks);
        if(r05d::capture){tr.evidence.debug_eroded=eroded.clone();tr.evidence.debug_refmin=refMin.clone();tr.evidence.debug_refmax=refMax.clone();}''')
 (GEN/'roi_tip.inc').write_text(q,encoding='utf8')
 exports=(ROOT/'research/uctt_r05d/exports.inc').read_text(encoding='utf8')
 (GEN/'exports.inc').write_text(exports+'\n#include "evidence_exports.inc"\n',encoding='utf8')
 write(OUT/'rules_before_B1.json',dict(source={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'research/uctt_r05e').glob('*') if p.is_file()},raw_budget=8192,retained_budget=64,buckets=16,slots_per_bucket=4,merge_radius=3,merge_direction_radians=.25,trace_budget=16,tolerances=[3,5,10],dark_valley_only=True,reference_unknown='NaN + reason bit4',reason_bits={1:'uncomputed_border',2:'current_flank_below75',4:'reference_unavailable',8:'legacy_eroded_gate',16:'legacy_ref_texture_gate',32:'known_crack',64:'current_restored'},parameter_search=False))
 for p in GEN.glob('*'):
  if p.is_file():shutil.copy2(p,OUT/'research_source_patch'/p.name)
 print('GENERATED R05E',GEN,flush=True)
if __name__=='__main__':main()
