"""Offline only. No native tracker imports. All rules fixed before first label read."""
from common import *
import numpy as np,zipfile,collections
from scipy.spatial import cKDTree
TAGS=['E1_GREEDY','E1_BEAM','E1_NO_GAP','E1_STRONG','E0_GREEDY','E0_BEAM','E0_CAPACITY_GREEDY','E0_CAPACITY_BEAM']
PERTURB=['E0_PERTURB_'+s for s in ['normal_minus2','normal_plus2','angle_minus5','angle_plus5']]
SENTINELS=[('group_a',504),('ct2',395),('group_h',78),('ct3',65),('ct2',196),('ct2',431),('ct2',457),('group_h',41),('group_h',115)]
def dense(points):
 p=np.array(points,float).reshape(-1,2);out=[]
 for a,b in zip(p[:-1],p[1:]):
  k=max(1,int(np.ceil(np.linalg.norm(b-a))));out.extend(a+(b-a)*np.arange(k)[:,None]/k)
 if len(p):out.append(p[-1])
 return np.array(out,float).reshape(-1,2)
def path_samples(label):
 chunks=[dense(s['points']) for s in label['shapes'] if s['label']=='crack_path'];return np.concatenate(chunks) if chunks else np.empty((0,2))
def current_path(t):
 pieces=[];chain=[]
 for n in t['selected_path']:
  if n['visible']:chain.append(n['xy'])
  else:
   if chain:pieces.extend(dense(chain));chain=[]
 if chain:pieces.extend(dense(chain))
 return np.array(pieces,float).reshape(-1,2)
def nearest(points,point):
 return float(np.linalg.norm(np.array(points).reshape(-1,2)-point,axis=1).min()) if len(points) else None
def max_gap(dist,gt,tol=10):
 longest=running=0.
 for i,d in enumerate(dist):
  running=running+(float(np.linalg.norm(gt[i]-gt[i-1])) if i else 0) if d>tol else 0.;longest=max(longest,running)
 return longest
def divergence(t,gt,tip,error):
 out=dict(stage='IDENTITY_UNVERIFIED',step=None,scan_id=None,node_id=None,recovery_step=None,off_path_distance=None,detail='tentative tracking endpoint can be close, but independent identity certificate is absent',near_gt_candidates=0,near_gt_pruned_nodes=0)
 if not t['seeds']:return out|dict(stage='SEED_MISSING',detail='bounded automatic origin corridor produced no admissible three-section start')
 if not t.get('nodes'):return out|dict(stage='PERTURBATION_ENDPOINT_ONLY',detail='seed sensitivity probe retains selected path but not complete native alternatives; first-cause NOT_VERIFIED')
 tree=cKDTree(gt);vis=[p for p in t['selected_path'] if p['visible']]
 if not vis:return out|dict(stage='NO_CURRENT_OBSERVATION',detail='legal seed supplied but no current visible center survived')
 ds,ix=tree.query(np.array([p['xy'] for p in vis]));first=next((i for i,d in enumerate(ds) if d>10),None)
 # A native step that leaves the labeled path is a directly locatable diagnostic event.
 if first is not None:
  node=vis[first];scan=t['scans'][node['scan']];out.update(step=node['step'],scan_id=node['scan'],node_id=node['id'],off_path_distance=float(ds[first]))
  rec=next((i for i in range(first+1,len(vis)) if ds[i]<=10),None);out['recovery_step']=vis[rec]['step'] if rec is not None else None
  raw=scan.get('raw_candidates',[]);ret=scan.get('candidates',[]);rd=tree.query(np.array([c['xy'] for c in raw]))[0] if raw else np.empty(0);cd=tree.query(np.array([c['xy'] for c in ret]))[0] if ret else np.empty(0)
  children=[t['nodes'][i] for i in scan.get('children',[])];nearpruned=[n for n in children if n['visible'] and tree.query(n['xy'])[0]<=10 and not n['retained']];out['near_gt_candidates']=int(sum(cd<=10));out['near_gt_pruned_nodes']=len(nearpruned)
  parent=t['nodes'][node['parent']]
  if first==0:out.update(stage='WRONG_SEED_OR_FIRST_ACQUISITION',detail='first actual observation >10px from offline path; seed is not a certified identity')
  elif len(nearpruned):out.update(stage='BEAM_PRUNED_NEAR_PATH',detail='a current near-label child existed and native pruning removed it')
  elif sum(cd<=10):out.update(stage='WRONG_ALTERNATIVE_SELECTION',detail='same scan has near-path retained candidate but selected chain takes another observation')
  elif sum(rd<=10):out.update(stage='LOCAL_CANDIDATE_FILTER',detail='near-path raw local extremum exists but weak/NMS/top3 filtering removed it')
  elif ix[first]>=len(gt)-5 and ds[first]>10:out.update(stage='TERMINAL_OVERRUN',detail='selected current observations continue beyond labeled visible end into other texture')
  elif parent['missing_distance']>0:out.update(stage='GAP_WRONG_REACQUISITION',detail='first off-path current observation follows explicit missing steps')
  else:out.update(stage='DIRECTION_OR_CURRENT_RESPONSE',detail='selected chain first leaves label band; inspect native profile, no proof that a correct valley existed at this scan')
 elif error is None or error>10:
  last=vis[-1];out.update(step=last['step'],scan_id=last['scan'],node_id=last['id'])
  if t['search_incomplete']:out.update(stage='BUDGET_INCOMPLETE',detail=t['budget_reason'])
  elif any(p['missing_distance']>0 for p in t['selected_path']):out.update(stage='GAP_REACQUISITION_OR_EARLY_STOP',detail='chain remains near path but terminates before offline tip after missing search; raw response evidence must disambiguate')
  else:out.update(stage='EARLY_STOP',detail='current visible chain ends short of labeled tip')
 return out
def evaluate_trace(t,label):
 tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];tip=np.array(tips[0]) if len(tips)==1 else None;gt=path_samples(label);visible=tip is not None
 r=dict(visibility='VISIBLE' if visible else 'UNCERTAIN',observed=t['observed'],predicted=t['predicted'],fallback=True,observed_error_px=None,proposed_observed=bool(t['proposed_observed']),search_incomplete=bool(t['search_incomplete']),tracking_tip=t['tracking_tip'],tracking_error_px=float(np.linalg.norm(np.array(t['tracking_tip'])-tip)) if visible and t['tracking_tip'] is not None else None,reason=t['reason'],ms=t['time_total_native_ms'],seed_count=len(t['seeds']),path_sample_count=len(gt),first_failure_stage='UNCERTAIN_UNSCORED')
 if not visible:return r,dict(stage='UNCERTAIN_UNSCORED',step=None,detail='not a negative and not a zero-error case')
 cp=current_path(t);distance=cKDTree(cp).query(gt)[0] if len(cp) else np.full(len(gt),np.inf)
 path_error=cKDTree(gt).query(cp)[0] if len(cp) and len(gt) else np.empty(0)
 for tol in [3,5,10]:r[f'visible_path_precision{tol}']=float(np.mean(path_error<=tol)) if len(path_error) else None
 r['max_visible_off_path_distance']=float(path_error.max()) if len(path_error) else None
 selected_seed=t['selected_path'][0]['seed'] if t['selected_path'] else 0
 seed_index=int(cKDTree(gt).query(t['seeds'][selected_seed]['xy'])[1]) if t['seeds'] and len(gt) else 0
 if t['seeds'] and len(gt):
  seed=t['seeds'][selected_seed];sd=float(cKDTree(gt).query(seed['xy'])[0]);tangent=gt[min(len(gt)-1,seed_index+3)]-gt[max(0,seed_index-3)];tangent=tangent/max(1e-9,np.linalg.norm(tangent));ad=float(np.degrees(np.arccos(np.clip(tangent@np.array(seed['tangent']),-1,1))));r.update(seed_distance_to_GT_path=sd,seed_tangent_error_degrees=ad,offline_favorable_seed=bool(sd<=5 and ad<=25))
 else:r.update(seed_distance_to_GT_path=None,seed_tangent_error_degrees=None,offline_favorable_seed=False)
 candidates=[c['xy'] for s in t['scans'] for c in s.get('candidates',[])];raw=[c['xy'] for s in t['scans'] for c in s.get('raw_candidates',[])];r.update(candidate_count=len(candidates),raw_extrema=len(raw),candidate_nearest_px=nearest(candidates,tip),raw_nearest_px=nearest(raw,tip),selected_visible_nearest_px=nearest(cp,tip),max_path_uncovered10_px=max_gap(distance,gt),seed_path_index=seed_index)
 for tol in [3,5,10]:r[f'path_coverage{tol}']=float(np.mean(distance<=tol)) if len(gt) else None;r[f'seed_onward_path_coverage{tol}']=float(np.mean(distance[seed_index:]<=tol)) if len(gt) else None
 nodes=t.get('nodes',[]);near_nodes=[n for n in nodes if n['visible'] and cKDTree(gt).query(n['xy'])[0]<=10] if len(gt) else [];r['near_path_nodes']=len(near_nodes);r['near_path_pruned_nodes']=sum(not n['retained'] for n in near_nodes)
 # Prespecified descriptive density control, not a physical-negative FPR.
 if candidates and t['scans']:
  corners=np.array([p for s in t['scans'] for p in s['window_polygon']]);lo=corners.min(axis=0);hi=corners.max(axis=0);random=np.random.default_rng(20261112).uniform(lo,hi,(1000,2));r['random_points_within10_candidate_fraction']=float(np.mean(cKDTree(candidates).query(random)[0]<=10));r['random_control_scope']='uniform1000 in axis-aligned union bounds of actual sampled strips; conditional spatial-density control only'
 failure=divergence(t,gt,tip,r['tracking_error_px']);r['first_failure_stage']=failure['stage'];r['correct_follow10_and_tip10']=bool(r['seed_onward_path_coverage10']>=.9 and r['tracking_error_px'] is not None and r['tracking_error_px']<=10)
 r['path_and_endpoint_supported10']=bool(r['correct_follow10_and_tip10'] and r['visible_path_precision10'] is not None and r['visible_path_precision10']>=.9)
 return r,failure
def main():
 assert read(OUT/'E1_complete.json')['frames']==1565;assert read(OUT/'E0_E2_complete.json')['selected_frames']==80
 core=['tracker.hpp','runtime.cpp'];lock=read(OUT/'E1_pre_run_lock.json')['files']
 for name in core:assert sha(ROOT/'research/uctt_r05g'/name)==lock[f'research/uctt_r05g/{name}']
 write(OUT/'offline_evaluation_lock.json',dict(script_sha256=sha(Path(__file__)),labels_sha256=sha(LABELS),metrics='all76 visible;3/5/10px; sampled visible path only; follow requires >=.9 seed-onward coverage10 AND endpoint<=10; uncertain separate; no parameter fitting',detector_frozen_before_label_scoring=True))
 results=[];failures=[];annotations=[];summary=[]
 with zipfile.ZipFile(LABELS) as z:
  for row in rows(OUT/'selection.csv'):
   g=row['dataset_id'];f=int(row['frame_id']);require(g,'development');require(g,'comparison',uses_annotations=True);label=json.loads(z.read(row['selected_json']));annotations.append(dict(dataset_id=g,frame_id=f,member=row['selected_json'],sha256=hashlib.sha256(z.read(row['selected_json'])).hexdigest()))
   for tag in TAGS+PERTURB:
    t=read(OUT/'traces'/f'{tag}_{g}_{f}.json');r,fail=evaluate_trace(t,label);r.update(dataset_id=g,frame_id=f,variant=tag,seed_quality=t.get('seed_quality','AUTO'),trace=f'traces/{tag}_{g}_{f}.json');results.append(r);failures.append(dict(dataset_id=g,frame_id=f,variant=tag,visibility=r['visibility'],**fail,trace=r['trace']))
   print('offline',g,f,flush=True)
 save(OUT/'experiments/selected_visible_eval.csv',results);save(OUT/'failure_first_divergence.csv',failures);save(OUT/'annotation_access_log.csv',annotations)
 for tag in TAGS+PERTURB:
  for group in DEV+['ALL']:
   part=[r for r in results if r['variant']==tag and (group=='ALL' or r['dataset_id']==group)];vv=[r for r in part if r['visibility']=='VISIBLE'];errors=[r['tracking_error_px'] for r in vv if r['tracking_error_px'] is not None];pp=[r['tracking_error_px'] for r in vv if r['proposed_observed'] and r['tracking_error_px'] is not None]
   summary.append(dict(variant=tag,dataset_id=group,selected=len(part),visible=len(vv),uncertain=len(part)-len(vv),observed=0,predicted=0,rejected=len(vv),observed_hit3=0,observed_hit5=0,observed_hit10=0,observed_over100=0,observed_over500=0,observed_error_p50=None,observed_error_p95=None,observed_error_max=None,incomplete=sum(r['search_incomplete'] for r in vv),tentative_tips=len(errors),tentative_error_p50=float(np.median(errors)) if errors else None,tentative_error_p95=float(np.percentile(errors,95)) if errors else None,tentative_error_max=max(errors) if errors else None,tentative_over100=sum(e>100 for e in errors),tentative_over500=sum(e>500 for e in errors),correct_follow10_and_tip10=sum(r.get('correct_follow10_and_tip10',False) for r in vv),mean_full_path_coverage10=float(np.mean([r['path_coverage10'] for r in vv])) if vv else None,mean_seed_onward_path_coverage10=float(np.mean([r['seed_onward_path_coverage10'] for r in vv])) if vv else None,proposed_observed=len(pp),proposed_over100=sum(e>100 for e in pp),proposed_over500=sum(e>500 for e in pp),**{f'tentative_hit{tol}':sum(e<=tol for e in errors) for tol in [3,5,10]},**{f'candidate_hit{tol}':sum(r.get('candidate_nearest_px') is not None and r['candidate_nearest_px']<=tol for r in vv) for tol in [3,5,10]}))
 for s in summary:
  vv=[r for r in results if r['variant']==s['variant'] and r['visibility']=='VISIBLE' and (s['dataset_id']=='ALL' or r['dataset_id']==s['dataset_id'])];prec=[r['visible_path_precision10'] for r in vv if r['visible_path_precision10'] is not None]
  s['path_and_endpoint_supported10']=sum(r['path_and_endpoint_supported10'] for r in vv);s['mean_visible_path_precision10']=float(np.mean(prec)) if prec else None
 save(OUT/'experiments/comparison_by_group.csv',summary)
 favorable=[]
 for tag in TAGS:
  for g in DEV+['ALL']:
   vv=[r for r in results if r['variant']==tag and r['visibility']=='VISIBLE' and (g=='ALL' or r['dataset_id']==g)];good=[r for r in vv if r.get('offline_favorable_seed')]
   favorable.append(dict(variant=tag,dataset_id=g,all_visible=len(vv),offline_start_distance5_angle25=len(good),follow_and_tip10=sum(r.get('correct_follow10_and_tip10',False) for r in good),endpoint10=sum(r['tracking_error_px'] is not None and r['tracking_error_px']<=10 for r in good),definition='offline diagnostic subset only; never used for picking seeds, parameters, pruning or online reporting'))
 save(OUT/'experiments/favorable_start_comparison.csv',favorable)
 assert len([r for r in results if r['variant']=='E1_BEAM' and r['visibility']=='VISIBLE'])==76
 print([r for r in summary if r['dataset_id']=='ALL' and r['variant'] in TAGS],flush=True)
if __name__=='__main__':main()
