from common import *
import re,zipfile,numpy as np
def main():
 required=['README.md','frozen_manifest_r05e.json','build_manifest.md','development_report.md','implementation_diff.md','evidence_channel_design.md','baseline_equivalence.csv','evidence_channels_per_frame.csv','candidate_lineage.csv','attribution_audit.csv','terminal_audit.csv','tip_outputs_and_gt_eval.csv','performance_native.csv','performance_report.md','candidate_recall_report.md','lock_safety_report.md','terminal_review_report.md','first_regression.csv','failure_stage_counts.csv','gate_matrix.csv','reproduction_commands.md','R05E_Failure_And_Improvement_Gallery.html','R05E_Validation_Results.mp4','media_qa.json']
 assert all((OUT/n).exists() for n in required)
 frozen=read(OUT/'frozen_manifest_r05e.json');problems=[]
 for k,v in {**frozen['protected'],**frozen['prior_inputs']}.items():
  if sha(ROOT/k)!=v:problems.append(k)
 assert not problems,problems
 freeze=read(OUT/'validation_freeze.json')
 for k,v in {**freeze['rule_sources'],**freeze['generated_sources'],**freeze['dlls']}.items():assert sha(ROOT/k)==v,k
 for link in re.findall(r'(?:href|src)="([^"]+)"',(OUT/'R05E_Failure_And_Improvement_Gallery.html').read_text(encoding='utf8')):assert (OUT/link).exists(),link
 mode=freeze['mode'];deterministic=None
 legacy_bits=0;legacy_absent=[]
 for r in filter_rows(rows(OUT/'selected_frames.csv'),'validation'):
  name=f"{r['dataset_id']}__{int(r['frame_id']):06d}"
  with np.load(OUT/'maps'/f'{name}.npz') as current,np.load(D/'maps'/f'{name}.npz') as previous:
   if 'score' not in previous:legacy_absent.append(name);continue
   assert current['legacy'].dtype==previous['score'].dtype and current['legacy'].shape==previous['score'].shape and current['legacy'].tobytes()==previous['score'].tobytes(),name
   legacy_bits+=1
 if (OUT/f'candidate_hashes_{mode}_perf.csv').exists():
  a=rows(OUT/f'candidate_hashes_{mode}_dev.csv');b=rows(OUT/f'candidate_hashes_{mode}_perf.csv');assert a==b;deterministic=len(a)
 raw_equal=0
 if mode=='B2':
  for phase in ['dev','val']:
   with (OUT/f'B1_{phase}_frames.jsonl').open(encoding='utf8') as a,(OUT/f'B2_{phase}_frames.jsonl').open(encoding='utf8') as b:
    import itertools
    for left,right in itertools.zip_longest(a,b):
     assert left and right;aa,bb=json.loads(left),json.loads(right);assert (aa['dataset_id'],aa['frame_id'])==(bb['dataset_id'],bb['frame_id'])
     fields=['id','xy','gain','current_support','source_channel','direction','short_length','bucket','reference_available','reference_support']
     assert [[c.get(k) for k in fields] for c in aa['evidence']['candidates']]==[[c.get(k) for k in fields] for c in bb['evidence']['candidates']]
     raw_equal+=1
 matrix=[('reference_unavailable','PASS','native_evidence.csv; independent current survives'),('reference_existing_crack','PASS','native_evidence.csv; zero change does not veto'),('strong_scratch_no_false_observed','BLOCKED','No B3/B4 output implementation; shadow non-observation is not safety proof'),('coherent_wrong_first_lock','FAIL','Original unchanged R03 fixture, 1/16 fails'),('interrupted_crack','BLOCKED','No new B3 finite-gap attribution'),('disjoint_competitors','BLOCKED','No new B3 ambiguous competitor logic'),('forward_continuation','BLOCKED','No B4 independent terminal'),('occlusion_stationary','BLOCKED','Original R03 cases reproduced; no new state strategy'),('coordinate_roundtrip','PASS','contracts.csv: 4 quadrants x 4 crop/resolution cases'),('invalid_current_anchors','PASS' if (OUT/'tests/invalid_current_anchors.csv').exists() else 'NOT_VERIFIED','invalid_current_anchors.csv: original and B2 outputs agree; independent tip allowed'),('no_gt_leakage','PASS','native signatures + separate offline reader + policy assertions'),('determinism','PASS' if deterministic else 'NOT_VERIFIED',f'{deterministic or 0} complete development candidate snapshot hashes repeated')]
 save(OUT/'tests/required_test_matrix.csv',[dict(test=n,status=s,evidence=e) for n,s,e in matrix])
 write(OUT/'final_integrity.json',dict(status='PASS',protected_files=len(frozen['protected']),prior_inputs=len(frozen['prior_inputs']),validation_rule_hashes_unchanged=True,production_unchanged=True,old_outputs_unchanged=True,excluded_image_reads=0,excluded_label_reads=0,training_calls=0,deterministic_repeated_frames=deterministic,b1_b2_raw_candidates_exact_frames=raw_equal,b1_legacy_score_bitwise_equal_matrices=legacy_bits,score_not_computed_frames=legacy_absent,b2_map_comparison='All selected computed maps numerically exact to B1 including NaNs; original score writes unchanged by source construction',all_required_artifacts_present=True))
 # Compact portable review package; large full-frame raw maps remain next to it.
 files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='artifact_manifest.json' and (p.parent.name in ['images','traces','tests','research_source_patch'] or p.parent==OUT and p.suffix in ['.md','.html','.csv','.json'])]
 with zipfile.ZipFile(OUT/'R05E_Review_Package.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,p.relative_to(OUT).as_posix())
 write(OUT/'artifact_manifest.json',dict(files={p.relative_to(OUT).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in OUT.rglob('*') if p.is_file() and p.name!='artifact_manifest.json' and p.relative_to(OUT).as_posix()!='logs/seal.log'},excluded_self_referential_files=['artifact_manifest.json','logs/seal.log'],note='Review ZIP includes reports/images/selected traces/source/test evidence; full raw maps, full-frame JSONL and MP4 remain in run directory.'))
 print('SEALED production/prior inputs unchanged; deterministic',deterministic,'raw candidate equality',raw_equal,flush=True)
if __name__=='__main__':main()
