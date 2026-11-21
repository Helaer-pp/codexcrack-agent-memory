import shutil,difflib,os,platform,winreg
from common import *
def rep(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def main():
 OUT.mkdir(parents=True,exist_ok=False);GEN.mkdir(parents=True,exist_ok=True)
 for n in ['traces','maps','images','logs']: (OUT/n).mkdir()
 prior=read(R05/'final_integrity.json');assert prior['status']=='PASS'
 protected={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'src/cpp/a').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 for n in ['output/build/src/cpp/a/Release/CrackV4.dll','output/releases/A_Win64_OpenCV440/bin/CrackV4.dll','config/dataset_usage_policy.json']:
  protected[n]=sha(ROOT/n)
 with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as k:cpu=winreg.QueryValueEx(k,'ProcessorNameString')[0].strip()
 reports=['phase1_audit_decoupling_20261110_r01/development_report.md','phase1_acceptance_r02/development_report.md','phase1_r03_dynamic_roi_20261110_r01/development_report.md','uctt_r04_path_tip_20261111_r01/development_report.md','r05_annotation_validation_20261111_r01/validation_report.md']
 required=[ROOT/'output/runs'/p for p in reports]+[R05/'pre_evaluation_lock.json',R05/'production_tip_comparison.csv',R05/'human_annotations_six_groups_snapshot.zip',PRE/'input_inventory.csv']
 assert all(p.exists() for p in required)
 inventory=filter_rows(rows(PRE/'input_inventory.csv'),'validation');assert len(inventory)==2647
 assert all(Path(r['source_image']).exists() for r in inventory)
 save(OUT/'input_inventory_allowed.csv',inventory)
 # No labels opened here: both raw-input replay and trace are label-free.
 selected=filter_rows(rows(R05/'active_selection_manifest.csv'),'validation');save(OUT/'selected_frames.csv',selected)
 write(OUT/'frozen_manifest.json',dict(protected=protected,required={str(p):sha(p) for p in required},cpu=cpu,platform=platform.platform(),logical_cpus=os.cpu_count(),compiler='MSVC v142 x64 Release /O2 /fp:precise',opencv=sha(ROOT/'third_party/opencv440/bin/opencv_world440.dll'),flags=3572,policy=1,terminal=1,threads=4,refine=True,dataset_policy=read(POLICY_PATH),full_frames=2647,source_tree_sha=protected,original_annotations_read_by_detector=False))
 generate()
def generate():
 source=(ROOT/'src/cpp/a/CrackV4.cpp').read_text(encoding='utf8');roi=(ROOT/'src/cpp/a/roi_tip.inc').read_text(encoding='utf8')
 s=rep(source,'namespace {','#include "trace.hpp"\nnamespace {')
 s=rep(s,'    cv::Rect tip_roi, reference_roi;','    r05d::Trace r05d_trace; std::string r05d_json;\n    cv::Rect tip_roi, reference_roi;')
 s=rep(s,'Result Detector::process(const cv::Mat &im, const std::array<P, 2> *ap, bool isref) {','Result Detector::process(const cv::Mat &im, const std::array<P, 2> *ap, bool isref) {\n    r05d_trace={};r05d::Guard r05d_guard(&r05d_trace);')
 s=rep(s,'      double angle=std::abs(std::atan2(rot(1,0),rot(0,0))*180/CV_PI);','      double angle=std::abs(std::atan2(rot(1,0),rot(0,0))*180/CV_PI);\n      if(r05d::active){auto&t=*r05d::active;t.solve_angle=angle;t.solve_residual=residual;t.solve_inliers=int(inliers.size());t.solve_matches=int(matches.size());}')
 s=rep(s,'        if(response<=.15 || !std::isfinite(delta.x) || !std::isfinite(delta.y) ||','        if(r05d::active)r05d::active->matches.push_back({p.rect,delta,response,0,"phase"});\n        if(response<=.15 || !std::isfinite(delta.x) || !std::isfinite(delta.y) ||')
 s=rep(s,'    if(solve(matches,.3)) return true;','    if(solve(matches,.3)){if(r05d::active)r05d::active->motion_branch="phase";return true;}')
 s=rep(s,'        if(!std::isfinite(best) || best<.55 || best-second<.03 ||','        if(r05d::active)r05d::active->matches.push_back({p.rect,delta,best,second,"template"});\n        if(!std::isfinite(best) || best<.55 || best-second<.03 ||')
 s=rep(s,'    return solve(matches,.85);','    bool ok=solve(matches,.85);if(r05d::active)r05d::active->motion_branch=ok?"template":"failed";return ok;')
 s=rep(s,'    Grid cq = transformed(t.xy);','    Grid cq = transformed(t.xy);\n    if(r05d::active){std::vector<P> box;for(cv::Point z:{cv::Point(0,0),cv::Point(cq.x.cols-1,0),cv::Point(cq.x.cols-1,cq.x.rows-1),cv::Point(0,cq.x.rows-1)})box.push_back(P(cq.x.at<double>(z),cq.y.at<double>(z)));r05d::active->main_rois.push_back(box);}')
 # Endpoint arrays and actual branch conditions, no changes to D0 decisions.
 q=rep(roi,'void Detector::measureTip(Result &r,const cv::Mat &im,P center,P roiDirection,bool isReference) {','void Detector::measureTip(Result &r,const cv::Mat &im,P center,P roiDirection,bool isReference) {\n    r05d::Guard guard(&r05d_trace);auto &tr=r05d_trace;tr.center=center;tr.direction=roiDirection;tr.reference=isReference;tr.registration=isReference||tip_registration_valid;tr.mainpath=r.path;')
 q=rep(q,'        r.status="registration_uncertain";','        r.status="registration_uncertain";tr.terminal="registration_unavailable";')
 q=rep(q,'    tip_roi=tipWindow(center,spacing,turn,im.size());','''    tip_roi=tipWindow(center,spacing,turn,im.size());
#ifdef R05D_OFFLINE
    // Generic image-bounded expansion, independent of labels, specimen and frame.
    if(r05d::offline_variant==1){cv::Rect z=tip_roi;tip_roi=cv::Rect(z.x-z.width/2,z.y-z.height/2,z.width*2,z.height*2)&cv::Rect({},im.size());}
    if(r05d::offline_variant==2)tip_roi=r05d::offline_fixed_roi;
#endif
    tr.roi=tip_roi;tr.turn=turn;
''')
 q=rep(q,'    if(isReference && cfg.mode==0)return;','    if(isReference && cfg.mode==0){tr.terminal="declared_clean_reference_skip";return;}')
 q=rep(q,'        cv::Mat1f score(current.size(),-3.f);','        cv::Mat1f score(current.size(),-3.f);cv::Mat1b why(current.size(),uchar(0));')
 q=rep(q,'            if(flank<75) continue;','            if(flank<75){why(y,x)=1;continue;}why(y,x)=2;')
 q=rep(q,'                if(std::abs(upper-lower)<15 && flank>105)score(y,x)=valley-12;','                if(std::abs(upper-lower)<15 && flank>105){score(y,x)=valley-12;why(y,x)=5;}')
 q=rep(q,'            } else if(eroded(y,x)>75) {','            } else if(eroded(y,x)>75) {\n                why(y,x)=3;')
 q=rep(q,'                    score(y,x)=std::min(valley,novel);','                    {score(y,x)=std::min(valley,novel);why(y,x)=5;}')
 q=rep(q,'                if(prior(y,x)) score(y,x)=std::max(score(y,x),valley-5.f);','                if(prior(y,x)){score(y,x)=std::max(score(y,x),valley-5.f);why(y,x)=6;}')
 q=rep(q,'        path=distalLine(score,current,isReference);','''        if(r05d::capture){tr.current=current.clone();tr.score=score.clone();tr.registered=registered.clone();tr.prior=prior.clone();tr.reason=why.clone();}
        path=distalLine(score,current,isReference);
        tr.local=path;
''')
 q=rep(q,'    r.tip_measure_reason=path.empty()','    tr.original=path;tr.terminal=path.empty()?"empty_distal_path":"nonempty_distal_path";\n    r.tip_measure_reason=path.empty()')
 q=rep(q,'    knownCrack=cv::Mat1b(roi.size(),uchar(0));','    knownCrack=cv::Mat1b(roi.size(),uchar(0));\n    if(r05d::active&&r05d::capture)r05d::active->valid=cv::Mat1b(roi.size(),uchar(0));')
 q=rep(q,'            cv::Rect tile=cv::Rect(x,y,side,side)&ib;','            cv::Rect tile=cv::Rect(x,y,side,side)&ib;\n            r05d::LocalTile* lt=nullptr;if(r05d::active&&r05d::capture){r05d::active->local_tiles.push_back({});lt=&r05d::active->local_tiles.back();lt->tile=tile;}')
 q=rep(q,'            if(box.width<tile.width || box.height<tile.height) continue;','            if(box.width<tile.width || box.height<tile.height){if(lt)lt->stage="reference_search_too_small";continue;}')
 q=rep(q,'                if(corr<.62)continue;','                if(lt)lt->correlations.push_back(corr);\n                if(corr<.62)continue;')
 q=rep(q,'            if(dx.size()<2)continue;','            if(lt)lt->votes=int(dx.size());\n            if(dx.size()<2){if(lt)lt->stage="fewer_than_two_corr_ge062_votes";continue;}')
 q=rep(q,'            if(agree<2)continue;','            if(lt){lt->agree=agree;lt->offset=P(offset);}\n            if(agree<2){if(lt)lt->stage="fewer_than_two_consistent_votes_within2px";continue;}')
 q=rep(q,'            if((patch+offset & rb)!=(patch+offset))continue;','            if((patch+offset & rb)!=(patch+offset)){if(lt)lt->stage="reference_patch_outside";continue;}\n            if(lt)lt->stage="accepted";')
 q=rep(q,'            ref(patch+offset).copyTo(aligned(patch-roi.tl()));','            ref(patch+offset).copyTo(aligned(patch-roi.tl()));\n            if(r05d::active&&r05d::capture)r05d::active->valid(patch-roi.tl()).setTo(255);')
 q=rep(q,'    Path best;','''    if(r05d::active&&r05d::capture){auto&t=*r05d::active;t.gains=gains.clone();t.back=back.clone();for(auto&p:peaks){r05d::Peak z;z.gain=p.gain;z.x=p.x;z.y=p.y;t.peaks.push_back(z);}}
    Path best;''')
 q=rep(q,'    for(Peak peak:peaks) {','    for(Peak peak:peaks) {\n        auto*trace=r05d::peak(peak.x,peak.y);r05d::stage(trace,"visited");')
 q=rep(q,'        if(!best.empty() && peak.gain<.8f*bestGain) break;','        if(!best.empty() && peak.gain<.8f*bestGain){r05d::stage(trace,"rank_gain_stop");break;}')
 q=rep(q,'        if(!best.empty() && norm(best.back()-P(peak.x,peak.y))<4) continue;','        if(!best.empty() && norm(best.back()-P(peak.x,peak.y))<4){r05d::stage(trace,"duplicate_endpoint");continue;}')
 q=rep(q,'        if(line.size()<size_t(absolute?24:5) || hits<.72*line.size()) continue;','        if(trace){trace->line=line;trace->hits=hits;}\n        if(line.size()<size_t(absolute?24:5) || hits<.72*line.size()){r05d::stage(trace,line.size()<size_t(absolute?24:5)?"path_too_short":"path_hits_below_72pct");continue;}')
 q=rep(q,'        if(tailHits<.65*tailCount)continue;','        if(trace)trace->tail=tailHits;\n        if(tailHits<.65*tailCount){r05d::stage(trace,"tail_hits_below_65pct");continue;}')
 q=rep(q,'        })) continue;','        })){r05d::stage(trace,"interior_shoulder");continue;}')
 q=rep(q,'        if(t.x<=0)continue;','        if(t.x<=0){r05d::stage(trace,"nonforward_tail");continue;}')
 q=rep(q,'        double slope=t.y/t.x;','        double slope=t.y/t.x;if(trace)trace->slope=slope;')
 q=rep(q,'            if(yy<3 || yy>=h-3 || intensity(yy,xx)<55) {material=false;break;}','            if(yy<3 || yy>=h-3 || intensity(yy,xx)<55) {r05d::stage(trace,yy<3||yy>=h-3?"ahead_outside":"ahead_dark_below55");material=false;break;}')
 q=rep(q,'            if(i>=4 && run>=4){material=false;break;}','            if(i>=4 && run>=4){r05d::stage(trace,"ahead_continues_4");material=false;break;}')
 q=rep(q,'            if(shared<4)return {};','''            if(trace)trace->shared=shared;
            if(shared<4){r05d::stage(trace,"competing_disjoint_paths");
#ifdef R05D_OFFLINE
              if(r05d::offline_variant==3)continue;
#endif
              return {};}
''')
 q=rep(q,'            if(line.back().x>best.back().x) best=std::move(line);','            if(line.back().x>best.back().x){r05d::stage(trace,"accepted_later_same_path");best=std::move(line);}else r05d::stage(trace,"same_path_earlier");')
 q=rep(q,'        } else {best=std::move(line);bestGain=peak.gain;}','        } else {r05d::stage(trace,"accepted_best");best=std::move(line);bestGain=peak.gain;}')
 for f in (ROOT/'src/cpp/a').glob('*.inc'):shutil.copy2(f,GEN/f.name)
 (GEN/'CrackV4.cpp').write_text(s+'\n#include "exports.inc"\n',encoding='utf8');(GEN/'roi_tip.inc').write_text(q,encoding='utf8')
 (OUT/'instrumentation.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True),s.splitlines(True)))+'\n'+''.join(difflib.unified_diff(roi.splitlines(True),q.splitlines(True))),encoding='utf8')
 print('PREPARED',OUT,flush=True)
if __name__=='__main__':
 if '--generate-only' in sys.argv:generate()
 else:main()
