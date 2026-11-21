import csv,json,re,hashlib,subprocess,math,shutil
import numpy as np,cv2
from PIL import Image,ImageDraw
from common import *
def rows(name):return list(csv.DictReader((OUT/name).open(encoding='utf-8-sig')))
def main():
 required=['development_report.md','frozen_manifest_r04.json','dependency_trace.md','reproduction_commands.md','frame_manifest.csv','candidate_evidence.csv','candidate_paths.jsonl','lock_injection_results.csv','original_fixture_r04.csv','factorial_roi_reference_registration.csv','first_divergence_r04.csv','tip_stop_candidates.csv','comparison_results.csv','metric_summary.csv','performance_report.md','performance_summary.csv','failure_gallery.html','acceptance_matrix.csv','R04_results.mp4']
 for name in required:assert (OUT/name).is_file() and (OUT/name).stat().st_size,name
 manifest=json.loads((OUT/'frozen_manifest_r04.json').read_text());changed=[p for p,h in manifest['protected'].items() if sha(ROOT/p)!=h];assert not changed,changed
 identities=json.loads((OUT/'build_identity.json').read_text())
 for name,h in identities.items():assert sha(BUILD/'Release'/name)==h,name
 checks=rows('baseline_checks.csv');assert len(checks)==642 and all(r['R03_equivalent']==r['shadow_equal']==r['cached_observe_readonly']=='True' for r in checks)
 rr=rows('comparison_results.csv');assert len(rr)==2568
 for r in rr:
  if r['version'].startswith('B2'):
   x,y=float(r['output_x']),float(r['output_y']);assert math.isfinite(x) and math.isfinite(y) and 0<=x<int(r['image_w']) and 0<=y<int(r['image_h'])
   assert (r['visual_confirmed']=='True')==(r['source_type']=='observed')
   if r['source_type']!='observed':assert r['tip_x']==r['tip_y']=='' and r['lock_committed']=='0'
 frames=rows('frame_manifest.csv');assert len(frames)==len(set(r['image_sha256'] for r in frames))==472
 queue=[]
 for r in frames:
  if r['selected_for_review']=='True':queue.append(dict(dataset_id=r['dataset_id'],frame_id=r['frame_id'],image_path=r['image_path'],image_sha256=r['image_sha256'],role=r['role'],label_status='GT_UNAVAILABLE',reviewer1=None,reviewer2=None,visible_tip_x=None,visible_tip_y=None,source_identity=None,unresolvable=None))
 save('annotation_review_queue.csv',queue)
 maprecords=json.loads((OUT/'map_manifest.json').read_text());archives=0
 for r in maprecords:
  if 'archive' not in r['arrays']:continue
  with np.load(OUT/r['arrays']['archive']) as z:
   for name in z.files:assert hashlib.sha256(z[name].tobytes()).hexdigest()==r['arrays'][name]['sha256']
  archives+=1
 scopes=rows('performance_scopes.csv');keys=['main_motion_ms','tip_motion_ms','main_other_ms','local_reference_ms','distal_path_ms','tip_other_and_trace_ms','new_audit_ms','json_and_api_residual_ms']
 for r in scopes:assert abs(sum(float(r[k]) for k in keys)-float(r['B1_api_ms']))<1e-7
 # Verify legacy exported API identity, add diagnostic exports only.
 dump='D:/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.29.30133/bin/Hostx64/x64/dumpbin.exe';exports={}
 for name,path in [('original',ROOT/'output/build/src/cpp/a/Release/CrackV4.dll'),('B0',BUILD/'Release/B0_R02_A0.dll'),('B1',BUILD/'Release/B1_DIAGNOSTIC.dll')]:
  result=subprocess.run([dump,'/exports',str(path)],capture_output=True);assert result.returncode==0
  txt=result.stdout.decode('utf8',errors='replace');(OUT/f'exports_{name}.txt').write_text(txt,encoding='utf8');exports[name]=re.findall(r'^\s+\d+\s+[0-9A-F]+\s+[0-9A-F]+\s+(\w+)\s*$',txt,re.M)
 assert set(exports['original'])==set(exports['B0'])=={x for x in exports['B1'] if not x.startswith('R04') and not x.startswith('CrackV4Profile')}
 write('abi_verification.json',dict(legacy_exports_equal=True,exports=exports,legacy_headers_unchanged=True,scope='Export names and frozen struct headers; full cross-platform/calling-convention certification not claimed'))
 video=json.loads((OUT/'video_manifest.json').read_text());probe=json.loads((OUT/'video_probe.json').read_text());stream=next(s for s in probe['streams'] if s['codec_type']=='video')
 assert stream['codec_name']=='h264' and int(stream['width'])==1600 and int(stream['height'])==900 and int(stream['nb_frames'])==video['frames']==2070
 assert sha(OUT/'R04_results.mp4')==video['sha256'];idx=rows('video_frame_index.csv');assert sum(int(r['display_frames']) for r in idx)==2070
 real=[r for r in idx if r['kind']=='real_original'];assert len(real)==153 and len(set(r['image_sha256'] for r in real))==153
 assert len(queue)==153
 # Decode the encoded MP4, not the source render, for user-facing visual QA.
 cap=cv2.VideoCapture(str(OUT/'R04_results.mp4'));assert cap.isOpened();qa=OUT/'video_qa';qa.mkdir(exist_ok=True)
 selections=[idx[0],next(r for r in idx if r['kind']=='synthetic_injection' and r['case_id']=='connected_false_branch'),next(r for r in real if r['dataset_id']=='ct2' and r['frame_id']=='8'),next(r for r in real if r['dataset_id']=='group_h' and r['frame_id']=='5'),next(r for r in real if r['dataset_id']=='ct3' and r['frame_id']=='20'),idx[-1]]
 sheet=Image.new('RGB',(1200,1050),'#101827')
 for k,r in enumerate(selections):
  frame=int(r['start_video_frame']);cap.set(cv2.CAP_PROP_POS_FRAMES,frame);ok,im=cap.read();assert ok,(k,frame)
  cv2.imencode('.png',im)[1].tofile(str(qa/f'decoded_{k}_{frame}.png'));thumb=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)).resize((600,338));sheet.paste(thumb,((k%2)*600,(k//2)*350))
 cap.release();sheet.save(qa/'contact_sheet.jpg',quality=95)
 # A complete decode checks all encoded frames and stream errors.
 result=subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-v','error','-i',str(OUT/'R04_results.mp4'),'-f','null','-'],capture_output=True);(OUT/'video_decode.log').write_bytes(result.stderr);assert result.returncode==0 and not result.stderr
 for p in re.findall(r'(?:src)="([^"]+)"',(OUT/'failure_gallery.html').read_text(encoding='utf8')):assert (OUT/p).is_file()
 manifest['experimental_sources']=tree(ROOT/'research/uctt_r04');manifest['generated_source_hashes']=tree(GEN);manifest['binaries']={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in (BUILD/'Release').glob('*') if p.suffix in ['.exe','.dll']};manifest['input_manifest_sha256']=sha(OUT/'frame_manifest.csv');manifest['video_sha256']=video['sha256'];write('frozen_manifest_r04.json',manifest)
 snapshot=OUT/'experimental_source';snapshot.mkdir(exist_ok=True)
 for p in (ROOT/'research/uctt_r04').iterdir():
  if p.is_file():shutil.copy2(p,snapshot/p.name)
 assert 'PROJECT CHECK PASSED' in (OUT/'project_check.log').read_text(encoding='utf8')
 (OUT/'api_abi_compatibility.md').write_text('''# ABI and regression verification

Original and B0 legacy exported names are identical; B1 preserves them and adds R04Process/R04Observe/R04Map and the explicit profile getter. Original headers and production DLL are hash-protected. Baseline/observer output equality passed 642 chronological initialization/frame cases. Existing run.ps1 check passed production smoke, frozen regressions, six-group current-anchor invariance and invalid-current-anchor checks (project_check.log). These checks do not establish R04 attribution safety.

R04Process returns the original CrackV4Result unchanged; diagnostic states are separate JSON. Predicted/fallback are finite but invalid and never become legacy confirmed lengths. R04Observe is cached per frame; reset clears state. Map pointers are borrowed until next process/reset/destroy, used synchronously under caller serialization. Full concurrent-client lifetime and cross-platform ABI testing are not claimed. No production replacement occurred.
''',encoding='utf8')
 (OUT/'source_changes.md').write_text('''NO_PRODUCTION_CODE_CHANGE

Added research/uctt_r04 native audits, instrument generator, deterministic replay/analysis and video tools. Updated root README and docs/CURRENT_STATE pointers. Generated instrumented native copy and builds live only under output/build/uctt_r04*. experimental_source is a frozen restore-only source snapshot, not an active runtime import. Gates failed; no E2/E3/B3/B4/B5 integration and no dynamic ROI loop.
''',encoding='utf8')
 write('final_verification.json',dict(required_artifacts=len(required),protected_unchanged=len(manifest['protected']),baseline_shadow_cases=642,comparison_rows=len(rr),unique_originals=len(frames),review_queue=len(queue),map_archives_verified=archives,video_frames=2070,video_duration_seconds=138,video_decode='PASS',legacy_exports='PASS',physical_accuracy='NOT_VERIFIED',production_replacement=False))
 write('deliverable_manifest.json',{str(p.relative_to(OUT)).replace('\\','/'):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='deliverable_manifest.json' and p.suffix!='.log'})
 print((OUT/'final_verification.json').read_text())
if __name__=='__main__':main()
