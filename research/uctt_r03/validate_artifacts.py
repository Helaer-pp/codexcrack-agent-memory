"""Validate final evidence integrity, including links and finite-output contract."""
import json,csv,re,math
from prepare import ROOT,OUT,sha,write
def rows(name):return list(csv.DictReader((OUT/name).open(encoding='utf-8-sig')))
def main():
 required=['development_report.md','frozen_manifest_r03.json','architecture_state_machine.md','controlled_ablation_report.md','r03_frame_results.csv','t2_reinit_results.csv','t2_reinit_report.md','lock_events.csv','first_divergence_r03.csv','failure_gallery.html','performance_report.md','performance_scopes.csv','api_abi_compatibility.md','build_and_replay_commands.md','acceptance_matrix.csv','source_changes.md']
 for name in required:assert (OUT/name).is_file() and (OUT/name).stat().st_size>0,name
 manifest=json.loads((OUT/'frozen_manifest_r03.json').read_text());checked={**manifest['protected_files'],**manifest['experimental_sources'],**manifest['builds']}
 for name,h in checked.items():assert sha(ROOT/name)==h,name
 rr=rows('r03_frame_results.csv');assert len(rr)==4284
 a2=[r for r in rr if r['group']=='A2_STATE_ONLY'];assert len(a2)==1428
 for r in a2:
  x,y=float(r['output_x']),float(r['output_y']);assert math.isfinite(x) and math.isfinite(y) and 0<=x<int(r['image_w']) and 0<=y<int(r['image_h'])
  assert (r['valid']=='1')==(r['source']=='observed')
  if r['source']!='observed':assert r['history_written']=='False'
  if not r['last_confirmed_x']:assert r['track_roi'] in ['','null']
 for r in rows('first_divergence_r03.csv'):
  if r['snapshot']:assert (OUT/r['snapshot']).is_file(),r['snapshot']
 images=re.findall(r'<img src="([^"]+)"',(OUT/'failure_gallery.html').read_text(encoding='utf8'))
 assert images
 for p in images:assert (OUT/p).is_file(),p
 pp=rows('performance_scopes.csv');assert len(pp)==981 and all(r['raw_equivalent']=='True' for r in pp)
 scopes=['main_motion_ms','tip_motion_ms','main_other_ms','local_reference_ms','terminal_path_ms','tip_response_prepost_residual_ms','outer_residual_ms']
 for r in pp:assert abs(sum(float(r[k]) for k in scopes)-float(r['api_wall_ms']))<1e-8
 assert 'PROJECT CHECK PASSED' in (OUT/'project_check.log').read_text(encoding='utf8')
 write('final_verification.json',dict(required_artifacts=len(required),integrity_files=len(checked),production_and_R01_R02_protected=len(manifest['protected_files']),frame_rows=len(rr),sidecar_finite_invalid_history_checks=len(a2),profile_equivalent_calls=len(pp),gallery_assets=len(images),result='PASS_FOR_STOPPED_EXPERIMENT_INTEGRITY_NOT_PHASE1_ACCEPTANCE'))
 # Manifest of packaged evidence, excluding this manifest and running log files.
 write('deliverable_manifest.json',{str(p.relative_to(OUT)).replace('\\','/'):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='deliverable_manifest.json' and p.suffix!='.log' and 'frozen_production' not in p.parts})
 print((OUT/'final_verification.json').read_text())
if __name__=='__main__':main()
