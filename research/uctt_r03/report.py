"""Build auditable pilot/failure reports; never infer closed-loop success."""
import csv,json,math,html,collections,shutil
from pathlib import Path
import numpy as np,cv2
from prepare import ROOT,OUT,BUILD,sha,tree,write
from pilot import api,LIMITS,EXTRA
def read(name):return list(csv.DictReader((OUT/name).open(encoding='utf-8-sig')))
def save(name,rows):api.csvout(OUT/name,rows)
def md(name,text):(OUT/name).write_text(text,encoding='utf8')
def stats(values):
 return dict(zip(['P50','P95','P99','max'],map(float,np.percentile(values,[50,95,99,100])))) if values else dict.fromkeys(['P50','P95','P99','max'])
def table(rows,keys):
 def cell(v):return f'{v:.4f}' if isinstance(v,float) else str(v if v is not None else 'N/A')
 return '| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+'\n'.join('| '+' | '.join(cell(r.get(k)) for k in keys)+' |' for r in rows)
def coord(r):return np.array([float(r['output_x']),float(r['output_y'])]) if r['valid']=='1' else None
def main():
 rows=read('r03_frame_results.csv');checks=read('baseline_shadow_checks.csv');faults=read('fault_injection_results.csv');perf=read('performance_scopes.csv')
 gate=json.loads((OUT/'gate01.json').read_text());g2=json.loads((OUT/'gate2.json').read_text());abi=json.loads((OUT/'abi_summary.json').read_text());profile=json.loads((OUT/'profile_identity.json').read_text())
 assert g2['A3_A4']=='BLOCKED','Report must be revised if Gate 2 passes'
 snaps={}
 with (OUT/'snapshots.jsonl').open(encoding='utf8') as f:
  for r in map(json.loads,f):snaps[r['dataset_id'],r['variant_id'],r['frame_id']]=r
 # Add scalar fields and explicitly unavailable motion residual. Do not substitute main registration residual.
 for r in rows:
  s=snaps[r['dataset_id'],r['variant_id'],int(r['frame_id'])]['stateonly'] if r['group']!='A0_R02' else None
  for prefix,key,names in [('track_roi','track_roi','xywh'),('last_confirmed','last_confirmed','xy')]:
   values=s[key] if s else None
   for i,k in enumerate(names):r[prefix+'_'+k]=values[i] if values else None
  r['registration_state']=('VALID' if s['tip_motion_valid'] else 'UNRELIABLE') if s else None
  r['motion_quality']=s['tip_inliers'] if s else None;r['motion_quality_kind']='inlier_count' if s else None
  r['tip_motion_residual']=None;r['lock_reason']=r['transition_reason'];r['closed_loop_enabled']=False
 save('r03_frame_results.csv',rows)
 save('t2_reinit_results.csv',[dict(r,run_type='T2_A_PILOT_INCOMPLETE') for r in rows if r['group'] in ['A0_R02','A2_STATE_ONLY']])
 save('lock_events.csv',[r for r in rows if r['group']=='A2_STATE_ONLY' and (r['lock_attempted']=='True' or r['state_before']!=r['state_after'] or r['source']!='observed')])
 grouped=collections.defaultdict(list)
 for r in rows:grouped[r['group'],r['dataset_id'],r['variant_id']].append(r)
 metrics=[];coverage=[];div=[]
 for (group,g,v),rs in grouped.items():
  valid=[r for r in rs if r['valid']=='1'];control=grouped[group,g,'measured'];c0=sum(r['valid']=='1' for r in control);pairs=[(r,c) for r,c in zip(rs,control) if r['valid']==c['valid']=='1'];ds=[float(np.linalg.norm(coord(r)-coord(c))) for r,c in pairs]
  transitions=sum(r['state_after']=='TRACKING' and r['state_before'] in ['OCCLUDED','RECOVERING'] for r in rs) if group!='A0_R02' else None
  run=longest=0
  for r in rs:run=run+1 if r['valid']=='1' else 0;longest=max(longest,run)
  rec=dict(group=group,dataset_id=g,variant_id=v,N=len(rs),C0=c0,Cv=len(valid),Cpair=len(pairs),Cpair_C0=len(pairs)/c0 if c0 else None,Cv_C0=len(valid)/c0 if c0 else None,tip_state_mismatches=sum(r['valid']!=c['valid'] for r,c in zip(rs,control)),length_state_mismatches=sum(r['complete_length_valid']!=c['complete_length_valid'] for r,c in zip(rs,control)),first_lock_frame=int(valid[0]['frame_id']) if valid else None,longest_confirmed_run=longest,relocks=transitions,prediction_frames=sum(r['source']=='predicted' for r in rs),fallback_frames=sum(r['source']=='fallback' for r in rs),support='INSUFFICIENT_OBSERVED_SUPPORT' if c0<2 else 'EXPOSED_PILOT_ONLY',**stats(ds))
  rec['perturbation_class']='control' if v=='measured' else 'stress_10pct' if '10pct' in v else 'normal_2_or_5pct'
  rec['mean']=float(np.mean(ds)) if ds else None
  rec['worst_frame_id']=int(pairs[int(np.argmax(ds))][0]['frame_id']) if ds else None
  for threshold in [2,5,10]:rec[f'paired_above_{threshold}px_ratio']=sum(d>threshold for d in ds)/len(ds) if ds else None
  coverage.append(rec)
  if v!='measured':metrics.append(rec)
  if v=='measured' or group=='A1_SHADOW':continue
  def differs(r,c):
   point_changed=(r['output_x']!=c['output_x'] or r['output_y']!=c['output_y'])
   return point_changed or r['valid']!=c['valid'] or r['source']!=c['source'] or r['raw_status']!=c['raw_status']
  for kind,fn in [('first_output',differs),('first_substantive',lambda r,c:r['valid']!=c['valid'] or (r['valid']=='1' and np.linalg.norm(coord(r)-coord(c))>2)),('first_paired_tip',lambda r,c:r['valid']==c['valid']=='1' and np.linalg.norm(coord(r)-coord(c))>2)]:
   for r,c in zip(rs,control):
    if fn(r,c):
     frame=int(r['frame_id']);ss=snaps[g,v,frame];cs=snaps[g,'measured',frame]
     div.append(dict(group=group,dataset_id=g,variant_id=v,kind=kind,frame_id=frame,control_valid=c['valid'],variant_valid=r['valid'],control_tip=[c['output_x'],c['output_y']],variant_tip=[r['output_x'],r['output_y']],control_raw_status=c['raw_status'],variant_raw_status=r['raw_status'],roi_equal=cs['raw_debug']['tip_roi_xywh']==ss['raw_debug']['tip_roi_xywh'],tip_transform_equal=cs['shadow']['tip_transform']==ss['shadow']['tip_transform'],path_equal=cs['raw']['observed_original_px']==ss['raw']['observed_original_px'],input_sha_equal=cs['input']['sha256']==ss['input']['sha256'],source_code='src/cpp/a/roi_tip.inc:146; src/cpp/a/CrackV4.cpp:509,748',causality='Initial geometry changes ROI and reference-dependent pipeline; ROI vs motion vs baseline mask NOT isolated',snapshot=f'first_divergence/{g}_{v}_{frame}.json'))
     break
 for (group,g,v),rs in grouped.items():
  if group!='A2_STATE_ONLY':continue
  for other in ['A1_SHADOW','A2_STATE_ONLY']:
   rr=grouped[other,g,v];aa=grouped['A0_R02',g,v]
   for kind in ['first_output','first_substantive']:
    found=None
    for a,b in zip(aa,rr):
     diff=a['valid']!=b['valid'] or (a['valid']==b['valid']=='1' and np.linalg.norm(coord(a)-coord(b))>(1e-6 if kind=='first_output' else 2))
     if kind=='first_output':diff=diff or a['source']!=b['source'] or a['raw_status']!=b['raw_status']
     if diff:found=int(a['frame_id']);break
    div.append(dict(group='A0_vs_'+other,dataset_id=g,variant_id=v,kind=kind,frame_id=found,status='DIVERGED' if found else 'NO_DIVERGENCE',source_code='research/uctt_r03/state.hpp:47',causality='A1 raw equivalence; A2 finite invalid semantics or acceptance rejection; ROI not changed'))
 save('t2_pairwise_metrics.csv',metrics);save('confirmation_coverage.csv',coverage);save('first_divergence_r03.csv',div)
 # Matched A0->A2 coverage and observed disagreement, not pseudo-stability from predictions.
 statecompare=[]
 for (group,g,v),rs in grouped.items():
  if group!='A2_STATE_ONLY':continue
  a=grouped['A0_R02',g,v];pairs=[(x,y) for x,y in zip(a,rs) if x['valid']==y['valid']=='1']
  statecompare.append(dict(dataset_id=g,variant_id=v,N=len(rs),A0_confirmed=sum(x['valid']=='1' for x in a),A2_confirmed=sum(x['valid']=='1' for x in rs),Cpair=len(pairs),observed_coordinate_changes=sum(np.linalg.norm(coord(x)-coord(y))>1e-6 for x,y in pairs),removed_confirmation=sum(x['valid']=='1' and y['valid']!='1' for x,y in zip(a,rs)),A2_finite_inbounds=all(math.isfinite(float(x[k])) for x in rs for k in ['output_x','output_y']) and all(0<=float(x['output_x'])<int(x['image_w']) and 0<=float(x['output_y'])<int(x['image_h']) for x in rs)))
 save('state_only_comparison.csv',statecompare)
 # Performance grouped by dataset + state + resolution. This is A0 measured native scope replay.
 pg=collections.defaultdict(list)
 for r in perf:
  for key in [('dataset',r['dataset_id']),('state',r['state_after']),('resolution',r['image_w']+'x'+r['image_h'])]:pg[key].append(r)
 ps=[]
 for (kind,name),rs in pg.items():
  vv=[float(r['api_wall_ms']) for r in rs];ps.append(dict(kind=kind,name=name,N=len(vv),**stats(vv),over_50=sum(x>50 for x in vv),over_50_ratio=sum(x>50 for x in vv)/len(vv)))
 save('performance_summary.csv',ps)
 scopes=['main_motion_ms','tip_motion_ms','main_other_ms','local_reference_ms','terminal_path_ms','tip_response_prepost_residual_ms','outer_residual_ms']
 total=sum(float(r['api_wall_ms']) for r in perf);attribution=[dict(scope=k,mean_ms=np.mean([float(r[k]) for r in perf]),share=sum(float(r[k]) for r in perf)/total) for k in scopes]
 save('performance_attribution.csv',attribution)
 # Real originals + measured and perturbed paths. A3 is deliberately absent.
 (OUT/'images').mkdir(exist_ok=True);(OUT/'first_divergence').mkdir(exist_ok=True)
 for d in div:
  if d.get('snapshot'):
   key=d['dataset_id'],d['variant_id'],d['frame_id'];control=snaps[d['dataset_id'],'measured',d['frame_id']]
   (OUT/d['snapshot']).write_text(json.dumps(dict(control=control,variant=snaps[key]),ensure_ascii=False,indent=2),encoding='utf8')
 gallery=[];selected=set()
 for d in div:
  if d['group']=='A0_R02':
   for frame in range(max(1,d['frame_id']-1),min(LIMITS[d['dataset_id']],d['frame_id']+1)+1):selected.add((d['dataset_id'],d['variant_id'],frame))
 for r in metrics:
  if r['group']=='A0_R02' and r['worst_frame_id']:
   for frame in range(max(1,r['worst_frame_id']-1),min(LIMITS[r['dataset_id']],r['worst_frame_id']+1)+1):selected.add((r['dataset_id'],r['variant_id'],frame))
 for g,v,frame in sorted(selected):
  c=snaps[g,'measured',frame];s=snaps[g,v,frame];im=api.read(c['input']['path']);scale=min(1.,1500/im.shape[1]);canvas=cv2.cvtColor(cv2.resize(im,None,fx=scale,fy=scale),cv2.COLOR_GRAY2BGR)
  def point(p):return tuple(np.rint(np.array(p)*scale).astype(int))
  def rect(q,color):
   if q:cv2.rectangle(canvas,point(q[:2]),point([q[0]+q[2],q[1]+q[3]]),color,2)
  for item,color in [(c,(60,60,255)),(s,(60,255,80))]:
   rect(item['raw_debug']['tip_roi_xywh'],color);path=item['raw']['observed_original_px']
   if path:cv2.polylines(canvas,[np.array([point(p) for p in path])],False,color,2);cv2.circle(canvas,point(path[-1]),7,color,2)
   rect(item['stateonly']['track_roi'],(255,160,40))
   if item['stateonly']['predicted']:cv2.drawMarker(canvas,point(item['stateonly']['predicted']),(255,200,0),cv2.MARKER_CROSS,14,2)
  header=np.zeros((115,canvas.shape[1],3),np.uint8)
  labels=[f'{g} / {v} / frame {frame} | EXPOSED REAL IMAGE | no physical GT',f'Red=A0 measured; Green=A0 perturbed; Blue=A2 proposed ROI ONLY; A3/A4 BLOCKED',f"A2 measured={c['stateonly']['state_after']} ({c['stateonly']['source']}); variant={s['stateonly']['state_after']} ({s['stateonly']['source']})"]
  for j,label in enumerate(labels):cv2.putText(header,label,(12,26+j*30),cv2.FONT_HERSHEY_SIMPLEX,.48,(240,240,240),1,cv2.LINE_AA)
  fn=f'{g}_{v}_{frame}.jpg';cv2.imencode('.jpg',np.vstack([header,canvas]),[cv2.IMWRITE_JPEG_QUALITY,90])[1].tofile(str(OUT/'images'/fn))
  (OUT/'first_divergence'/f'{g}_{v}_{frame}.json').write_text(json.dumps(dict(control=c,variant=s),ensure_ascii=False,indent=2),encoding='utf8')
  gallery.append(f'<figure><img src="images/{fn}" style="max-width:100%"><figcaption>{html.escape(labels[0])}; original SHA256 {c["input"]["sha256"]}</figcaption></figure>')
 md('failure_gallery.html','<!doctype html><meta charset="utf-8"><title>R03 failure evidence</title><h1>R03: A0 / A2 shadow proposals</h1><p>A3/A4 blocked by wrong-first-lock injection. Blue rectangles never drive image processing. Images are scaled original photographs with overlays, not generated scenes.</p>'+''.join(gallery))
 lock_failed=','.join(g2['failed']);protect=json.loads((OUT/'frozen_manifest_r03.json').read_text());changed=[k for k,h in protect['protected_files'].items() if not (ROOT/k).exists() or sha(ROOT/k)!=h]
 write('protected_verification.json',dict(checked=len(protect['protected_files']),changed=changed));assert not changed
 import winreg
 with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
  protect['cpu_registry']={n:winreg.QueryValueEx(key,n)[0] for n in ['ProcessorNameString','~MHz','Identifier']}
 protect['cpu_target_match']=False
 protect['experimental_sources']=tree(ROOT/'research/uctt_r03');protect['builds']={str(p.relative_to(ROOT)):sha(p) for p in (BUILD/'Release').glob('*') if p.suffix in ['.dll','.exe']};protect['image_manifest_sha256']=sha(OUT/'input_manifest.csv');protect['compiler']='MSVC 19.29.30159.0 / v142 x64 Release /O2 /fp:precise';protect['opencv']='4.4.0 native';protect['profile_identity']=profile;write('frozen_manifest_r03.json',protect)
 acceptance=[dict(gate='Gate0_R02_reproduction',status='PASS' if gate['baseline_mismatches']==0 else 'FAIL',evidence='gate01.json',scope=f"{gate['frames']} pilot sequence-frame cases; not full matrix"),dict(gate='Gate1_shadow_equivalence',status='PASS' if not gate['shadow_mismatches'] and not gate['mutation_failures'] else 'FAIL',evidence='baseline_shadow_checks.csv',scope='raw JSON includes path, tip, length, status; timing excluded'),dict(gate='Gate2_state_faults',status='FAIL',evidence='fault_injection_results.csv',scope=lock_failed),dict(gate='Gate3_A3_A4',status='BLOCKED',evidence='gate2.json',scope='R03 mandatory ordering prohibits closed loop'),dict(gate='Gate4_production_integration',status='BLOCKED',evidence='protected_verification.json',scope='NO_PRODUCTION_CODE_CHANGE'),dict(gate='FULL_T2_A',status='BLOCKED',evidence='t2_reinit_report.md',scope='Full R02 16 variants and new 5% sweep not executed after safety stop'),dict(gate='T2_B_REAL',status='BLOCKED',evidence='development_report.md',scope='No multiple initializations of real external tracker trajectories'),dict(gate='CPU_50MS',status='FAIL' if any(float(r['api_wall_ms'])>50 for r in perf) else 'PASS',evidence='performance_summary.csv',scope='A0 full native API; A3/A4 not available'),dict(gate='ABI_COMPATIBILITY',status='PASS' if abi['legacy_exports_equal'] and abi['checks_pass'] else 'FAIL',evidence='abi_summary.json',scope='Legacy exports/structs/input isolation; no production finite fallback semantics'),dict(gate='R03_EVIDENCE',status='PARTIAL',evidence='development_report.md',scope='Gate0-2 stopped experiment complete; full requested closed-loop evidence blocked'),dict(gate='STABLE_DECOUPLING',status='FAIL',evidence='t2_pairwise_metrics.csv',scope='R02 sensitivity reproduced; dynamic ROI improvement not tested'),dict(gate='WRONG_LOCK_RISK',status='FAIL',evidence='fault_injection_results.csv',scope='Coherent wrong initial candidate accepted; physical-image wrong-lock rate NOT_VERIFIED'),dict(gate='PHASE1_GATE',status='FAIL',evidence='acceptance_matrix.csv',scope='No merge')]
 save('acceptance_matrix.csv',acceptance)
 project_check=(OUT/'project_check.log').exists() and 'PROJECT CHECK PASSED' in (OUT/'project_check.log').read_text(encoding='utf8')
 acceptance.append(dict(gate='PROJECT_CHECK',status='PASS' if project_check else 'NOT_VERIFIED',evidence='project_check.log',scope='Existing production and research regression checks; not R03 lock-safety approval'))
 save('acceptance_matrix.csv',acceptance)
 md('architecture_state_machine.md','''# R03 experimental state-only architecture

Entry: research/uctt_r03/observer.cpp R03Observe reads immutable production result under detector mutex. State::step in state.hpp runs native C++; no image operation is added to production. A0 compiles production directly; A1 includes that same source unchanged. A2 runs a second independent State instance on A1 evidence, not a separate detector/closed-loop DLL. Shadow observes the same frame after image processing.

| State/condition | Next state | Output | Trusted history |
|---|---|---|---|
| Never acquired, no candidate | SEARCHING | search center fallback, valid=false | empty |
| Never acquired, weak/edge/invalid evidence | ACQUIRING | fallback, valid=false | empty |
| Accepted terminal/path, motion and direction | TRACKING | observed | write original point, reference-transformed point, direction and frame |
| Acquired, 1-2 misses, motion reliable | OCCLUDED | predicted, valid=false | preserve |
| Acquired, >=3 misses / disconnected / bad motion | RECOVERING | predicted if usable, otherwise fallback | preserve |
| Connected visual evidence returns | TRACKING | observed | write |

All coordinates are original pixels. The historical last_confirmed point retains its original measurement frame. A separate reference-space point projects with the current tip-specific rigid transform. Main-anchor registration is not substituted. Image size change requires a new state/reference; persistent changed size stays degraded. NaN/Inf motion or candidate cannot write history. Output bounds failure is explicit. No phase assumption or monotonicity rule. Although there is no explicit speed threshold, the hard 6-pixel overlap gate can suppress fast expansion or fragmented visible paths; the large real replay coverage loss means this requirement is NOT SATISFIED.

SEARCH_ROI is the current A0 tipWindow, always retained. It still depends on initial origin/direction/spacing. There is NO search normalization in this experiment. TRACK_ROI is only a proposal after an accepted state. Proposal uses a 24-pixel tail, 64-pixel forward extent, 24-pixel half-width; uncertainty +12 pixels/miss capped at 96; corners transformed and bounds clipped. These are unvalidated experimental choices, not tuned per specimen. There is no recovery image search and no closed-loop enlargement. Search ROI never changes from the proposal.

The 6-pixel connectivity gate and 10-pixel edge margin are experimental assumptions. Runtime path/terminal booleans are correlated by measureTip, so they cannot certify physical ownership. The injected coherent wrong-first-lock passes them: this architecture fails acquisition safety. No confidence-score calibration or independent ownership verifier exists. No GT/filename/frame loading phase enters the runtime.

R03Observe is a consuming diagnostic operation, called once per result and state in the harness. Legacy GetBaseline remains a cached query and does not advance State automatically. Resetting/reinitializing a detector requires destroying/recreating its sidecar; no hidden reset interception or changed legacy ABI. Separate sidecar mutexes protect state but callers must keep handles alive and serialize observe/destroy. returned JSON is owned by sidecar until next observe/destroy.
''')
 md('t2_reinit_report.md','''# T2-A: safety-gated pilot, INCOMPLETE

Seven measured continuous R02 windows: GROUP_A252, group_c80, CT2/group_h/group_x120 each, three-point-bend160, CT3 full136. Four R02 failing initial variants replayed independently (group_c single P1 +5% x; CT2 common +2% x; group_h/group_x common +10% y). Initial points are copied exactly from R02 t2_variants.csv; each variant gets its own detector and state, reference image and current anchor trajectory unchanged. 988 distinct group-frames, 1428 initialization/frame cases. All are exposed evidence; group_x historical-only and three-point-bend validation-only, no tuning.

The full 16-variant matrix, added symmetric 5% sweep and non-control pairwise matrix are NOT COMPLETE. Gate2 failed before A3/A4 creation. This CSV explicitly says T2_A_PILOT_INCOMPLETE; it must not be used as full acceptance. T2-B-real is BLOCKED by missing real external tracker trajectories. No synthetic anchor sequence is relabeled real.

Statistics compare valid observed pairs only; predicted/fallback never shrink reported jitter. C0/Cv/Cpair and state mismatches are separate from complete-length mismatches. GROUP_A one observed control frame is INSUFFICIENT_OBSERVED_SUPPORT. Partial A2 coverage reduction is not an improvement.

'''+table(metrics,['group','dataset_id','variant_id','N','C0','Cv','Cpair','P95','max','tip_state_mismatches','length_state_mismatches']))
 md('controlled_ablation_report.md',f'''# Controlled ablation / STOP after Gate 2

A0_R02: same production source rebuilt. A1_SHADOW: same source plus read-only observer and state proposals. A2_STATE_ONLY: independent state instance consumes the same A1 frame; output semantics are evaluated offline/native-sidecar, no ROI feedback. A3_DYNAMIC_ROI and A4_DYNAMIC_ROI_RECOVERY: BLOCKED, neither compiled nor run. No dynamic-ROI improvement is established.

{gate['frames']} case-frames: baseline mismatch {gate['baseline_mismatches']}, raw shadow mismatch {gate['shadow_mismatches']}, raw mutation {gate['mutation_failures']}, independent-state difference {gate['independent_sidecar_failures']}. Raw JSON comparisons include paths/coordinates/status/length and exclude only clocks. Gate0 comparison against R02 checks stored confirmed tip and raw status, not an unavailable complete R02 path archive.

First-output and first-substantive divergences are in first_divergence_r03.csv. Adjacent real frames and complete paths/transforms are in first_divergence/. Geometry/ROI diverges from initialization; same image SHA and current anchors are held fixed. Different reference templates, baseline masks, tip transforms and search windows may co-vary. This is an initialization intervention, NOT an isolated proof that ROI clipping alone causes the error. No ROI-swap/motion-swap counterfactual was performed. Stale main-path audit scores are not independent ROI-path quality measurements.

Fault safety: {g2['passed']}/{g2['total']} pass; failure {lock_failed}. Fault evidence is injected after candidate detection, not an image-level synthetic accuracy benchmark. The known distractor label stays in the harness; runtime sees shifted self-consistent path/terminal flags and accepts. This proves a missing guard in this candidate protocol, not the physical identity of any real-image tip. The next closed-loop step is prohibited by the requested Gate2 rule.

'''+table(statecompare,['dataset_id','variant_id','N','A0_confirmed','A2_confirmed','Cpair','removed_confirmation','observed_coordinate_changes']))
 md('performance_report.md',f'''# CPU performance: FAIL against 50 ms

{len(perf)} current-image calls (7 cached reference queries excluded), flags3572/policy1/terminal1/refine=true/4 native threads, OpenCV4.4. Timer-only copy is recorded in profile_instrumentation.diff; original production untouched. Profile raw-output differences: {profile['raw_mismatches']}. It runs serially after the behavior replay, excluding disk decode, JSON, drawing, hashing, and report generation. It includes native C API call/packing and image processing; DLL initialization is separately listed in initialization_timings.csv. CPU is AMD Ryzen 9 7950X, 32 logical processors; registry frequency value 4491 MHz is not a measured dynamic clock. This is NOT the requested i7-12700K target machine; target-hardware performance remains NOT_VERIFIED. CPU/platform/compiler are in frozen_manifest_r03.json. These are this machine's measurements, not a real-time guarantee.

Fresh counters are read after each process; no after-minus-before of reset counters. main_total and tip_total are top-level disjoint scopes. Within them localReference and distalLine are nested. The attribution table uses disjoint components only. Tip residual includes score/pre/post operations not separately timed; outer residual includes C API plumbing and measurement overhead. Remaining residual is explicitly unassigned, not attributed to seed search. Nested old seed/response/follow columns are diagnostics only and must NOT be summed.

State breakdown labels the A0 call using the corresponding A2 shadow state; it is NOT A3 recovery performance. A2 processing_ms is A1 native call plus native state cost, an estimate for a future integration. diagnostic_overhead_ms in frame CSV contains TWO observer calls and JSON parsing, not production algorithm time. A1/A2 pilot timings overlap a short profile build; authoritative native timings below are isolated profile replay. SEARCHING/ACQUIRING/OCCLUDED/RECOVERING states with no calls are NOT_MEASURED rather than zero.

'''+table(ps,['kind','name','N','P50','P95','P99','max','over_50_ratio'])+'\n\nDisjoint attribution:\n\n'+table(attribution,['scope','mean_ms','share']))
 md('api_abi_compatibility.md',f'''# Legacy compatibility and sidecar semantics

Legacy exports equal: {abi['legacy_exports_equal']}; checked ABI sizes: {abi['sizes']}. exports_R02/A0/A1.txt are dumpbin output; header files are protected by hashes. A1 adds only R03CreateState, R03DestroyState and R03Observe. Legacy structs are unchanged. {abi['rows']} input/query/struct-size check rows; boolean checks pass={abi['checks_pass']}. NaN/Inf/coincident/out-of-image/null current anchors tested over five CT3 frames with independent detectors; tip-coordinate invariance is separate from coarse-main status. Repeated GetBaseline queries do not mutate current result. Invalid output struct size is tested before state advance. This is targeted compatibility, not exhaustive ABI/platform certification.

Legacy invalid output remains null/valid=false in CSV and its binary Result semantics remain unchanged. The requested every-frame finite point + source + original historical frame is provided only by experimental JSON sidecar. Predicted/fallback are valid=false and cannot certify length. Production finite-output semantic integration is INTERFACE_BLOCKED pending a versioned extension with source enum, valid flag, frame ID and last-confirmed frame. No placeholder is silently inserted into the production ABI. No new production DLL was released.

Real image resize, broad C++ allocation exceptions and concurrent destruction are not end-to-end certified; native evidence fault test covers size change and nonfinite values. cv::Mat pixels are processed synchronously in native calls, no image data retained by State (only value coordinates/path).
''')
 md('build_and_replay_commands.md',r'''# Reproduction (PowerShell, project root)

The existing run is evidence; do not overwrite it. For a fresh run change OUT and BUILD in research/uctt_r03/prepare.py and PBUILD/SRC in profile.py to new output paths first. All runtime imports are active research/src files, never sealed output sources. The frozen_production copy is restore-only.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP=(Resolve-Path output/cache/tmp).Path
$env:TMP=$env:TEMP
& D:/ProgramData/anaconda3/python.exe research/uctt_r03/prepare.py
& D:/CMake/bin/cmake.exe -S research/uctt_r03 -B output/build/uctt_r03 -G 'Visual Studio 17 2022' -A x64 -T v142
& D:/CMake/bin/cmake.exe --build output/build/uctt_r03 --config Release -- /m:1 /nodeReuse:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r03/pilot.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r03/verify.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r03/profile.py --generate
& D:/CMake/bin/cmake.exe -S output/build/uctt_r03_profile_source -B output/build/uctt_r03_profile -G 'Visual Studio 17 2022' -A x64 -T v142
& D:/CMake/bin/cmake.exe --build output/build/uctt_r03_profile --config Release -- /m:1 /nodeReuse:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r03/profile.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r03/report.py
```

Contracts exit2 means safety FAIL (not infrastructure crash); verify.py preserves that result and does not open A3. CMake parallel build hung in this sandbox; serial /nodeReuse:false completed. Failed build logs retained. Any next source change requires rebuilding/replaying affected evidence.
''')
 md('source_changes.md','NO_PRODUCTION_CODE_CHANGE\n\nExperiment sources added only in research/uctt_r03. README.md and docs/CURRENT_STATE.md updated to point to the failed experiment and prevent accidental integration. Generated timer instrumentation exists exclusively under output/build/uctt_r03_profile_source. Frozen source/DLL and all R01/R02 files checked unchanged. No release/production rebuild or merge.\n')
 md('development_report.md',f'''# R03 第一阶段第三轮：Gate 2 安全失败，停止闭环

1. **生产源码：未修改。** 新代码仅 research/uctt_r03；生产及 R01/R02 共 {len(protect['protected_files'])} 个文件哈希复核无变化。MSVC19.29/v142、OpenCV4.4、CPU四线程。R02 DLL SHA256=55a0e7a79162da79e691ede9ff58229e59a56fdd1e0b1e3f609dc51128860402。新 A0/A1 DLL、源码及图像清单哈希见 frozen_manifest_r03.json。不存在生产合入；隔离实验可直接弃用。

2. **R02 复现：** CT2、group_h、group_c、group_x 的四个已知失败变体与七组 measured 连续窗口共 {gate['frames']} 初始化/帧案例全部对齐 R02 已存尖端和原始状态，差异 {gate['baseline_mismatches']}。Three-point-bend、CT3 仅 measured 回放，未独立重跑它们完整扰动矩阵；GROUP_A仅1次控制确认，证据不足。group_x仅曝光历史；其他数据也非独立TEST。不能称七组扰动全部完成。

3. **A0–A4：** A1 raw/path/length 与 A0 差异 {gate['shadow_mismatches']}/{gate['frames']}，旁路未改原始结果。A2有限输出/预测/回退已落地为实验 sidecar，配对确认坐标不变；它会拒绝部分原确认，覆盖损失见 state_only_comparison.csv，不能解释为稳定性改善。A3/A4因首次错锁测试失败被强制阻断，未创建闭环版本。完整16变体及±5%扫描未执行，R03全证据不完整。

4. **首次分歧：** 相同原图SHA和当前点轨迹下，不同初始点改变 origin/spacing/forward、搜索ROI及参考相关状态；候选路径/尖端随后分歧。实际变换、路径、状态与相邻帧已保存。具体首帧见 first_divergence_r03.csv。尚未分离ROI、参考mask、局部配准的因果贡献；“单纯缩小ROI可修复”仍是假设。完整长度状态差异与尖端失锁分别统计，不混算。

5. **状态机：** {g2['total']}个明确标记的候选证据注入用例，{g2['passed']}通过。无候选连续8帧 SEARCHING/无TRACK ROI；已确认静止裂纹维持TRACKING；闭合首帧OCCLUDED且预测无效、历史不更新；连续3次丢失RECOVERING；运动失效fallback；尺寸变化需重置。{lock_failed}失败：整体平移的自洽干扰路径被首次接受并写历史，说明当前终端/路径证据不足以防错锁。这不是图像级真实准确率测试；真实错锁率仍NOT_VERIFIED。

6. **性能：** {len(perf)}个非参考帧完整原生API计时，50ms未达标。按状态/组/分辨率P50/P95/P99/max及超时率见 performance_report.md / performance_summary.csv。新增 localReference、终端路径和tip-motion计时；所有相加统计使用互斥scope，R02重置计时器作差错误已规避。残余时间明确保留，未虚构归因。A3/A4性能不存在。

7. **限制：** 无物理GT、无真实多初始点外部跟踪轨迹（T2-B-real BLOCKED）；当前988张独立组帧原图可读取且哈希核对，无本批缺图。完整矩阵/闭环恢复/独立新TEST均未完成；原ABI没有预测来源字段，有限占位仅在实验扩展输出。并发/真实尺寸改变未全面认证。故障注入不等于真实无裂纹/闭合数据验证。

8. **结论：** R03_EVIDENCE=PARTIAL（Gate0–2停止证据已交付，完整R03未齐）；STABLE_DECOUPLING=FAIL（基线敏感性仍在，动态ROI未验证）；WRONG_LOCK_RISK=FAIL（注入错锁已证实，真实图像安全NOT_VERIFIED）；CPU_50MS=FAIL；PHASE1_GATE=FAIL。分离验收：EVIDENCE_COMPLETE=NO，BEHAVIOR=BLOCKED，LOCK_SAFETY=FAIL，PERF=FAIL，T2_B_REAL=BLOCKED，OVERALL_PHASE1=FAIL。保留A0，不合入。

9. **下一步最小实验（最多3项）：** (1) 用有独立归属标签的真实/受控干扰图对验证首次获取证据，替换相关的terminal/path布尔值；(2) 在已保存首分歧帧上分别固定运动/参考mask后交换ROI，定位敏感性的直接来源；(3) 仅对profile确认的最大互斥耗时项做输出等价优化。状态安全通过后再恢复完整扰动矩阵和A3/A4，不能提前宣称动态ROI有效。

## 本批确认覆盖

'''+table(statecompare,['dataset_id','variant_id','N','A0_confirmed','A2_confirmed','Cpair','removed_confirmation'])+'\n\n## 本批初始化扰动差值（真实准确率N/A）\n\n'+table(metrics,['group','dataset_id','variant_id','C0','Cv','Cpair','P95','max'])+'\n\n## 原生API性能\n\n'+table(ps,['kind','name','N','P50','P95','P99','max','over_50_ratio']))
 md('README.md','# R03 stopped experiment\n\nStart with [development_report.md](development_report.md). A3/A4 are blocked, no production code change. Raw evidence and source locations are recorded in the frozen manifest. [Gallery](failure_gallery.html) contains packaged real-image assets.\n')
 print(json.dumps(dict(gate01=gate,gate2=g2,profile=profile['raw_mismatches'],source_protected=len(protect['protected_files']),gallery_images=len(gallery)),ensure_ascii=False))
if __name__=='__main__':main()
