"""Offline comparison only. Imports no labels until complete split inference exists."""
from v2common import *
import numpy as np,zipfile,argparse,collections,math
from scipy.spatial import cKDTree
def dense(points):
 p=np.asarray(points,float).reshape(-1,2);parts=[]
 for a,b in zip(p[:-1],p[1:]):
  n=max(1,math.ceil(float(np.linalg.norm(b-a))));parts.append(a+(b-a)*np.arange(n)[:,None]/n)
 if len(p):parts.append(p[-1:])
 return np.concatenate(parts) if parts else np.empty((0,2))
def observed_dense(trace):
 out=[];part=[]
 for r in trace:
  if r[2]:part.append(r[:2])
  elif part:out.append(dense(part));part=[]
 if part:out.append(dense(part))
 return np.concatenate(out) if out else np.empty((0,2))
def getlabels(groups):
 labels={};access=[]
 with zipfile.ZipFile(LABELS) as z:
  for r in rows(ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv'):
   if r['dataset_id'] not in groups:continue
   g=r['dataset_id'];require(g,'comparison',uses_annotations=True);b=z.read(r['selected_json']);labels[g,int(r['frame_id'])]=json.loads(b);access.append(dict(group=g,frame_id=int(r['frame_id']),member=r['selected_json'],sha=hashlib.sha256(b).hexdigest(),utc=utc(),usage='offline_after_complete_split_inference'))
 return labels,access
def baseline_trace(folder,roi):
 # Exact float predictions from immutable V1 CSV, not quantized display fields.
 return [[int(r['x']),int(r['selected_y']),r['is_observed']=='True',int(r['missing_run']),float(r['predicted_y'])*1024,max(roi['upper']+3,math.floor(float(r['predicted_y'])-7)),min(roi['lower']-3,math.ceil(float(r['predicted_y'])+7)+1),float(r['current_contrast']),float(r['reference_new_darkening']),-1] for r in rows(folder/'v1/trace_joint_T10p0.csv')]
def score_frame(group,fid,folder,data,label):
 tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];parts=[dense(s['points']) for s in label['shapes'] if s['label']=='crack_path'];gt=np.concatenate(parts) if parts else np.empty((0,2));tip=np.asarray(tips[0],float) if tips else None;tree=cKDTree(gt) if len(gt) else None;out=[]
 for result in [data['baseline']]+data['results']:
  trace=baseline_trace(folder,result['roi']) if result['mode']=='V1_LOCKED' else result['trace'];path=observed_dense(trace);public=result['tip'];candidate=result.get('candidate_tip');g=result.get('roi');r=dict(group=group,frame_id=fid,mode=result['mode'],visibility='VISIBLE' if tip is not None else 'UNCERTAIN',output_state=result['output_state'],tip=public,candidate_tip=candidate,error=float(np.linalg.norm(np.asarray(public)-tip)) if tip is not None and public is not None else None,raw_candidate_error=float(np.linalg.norm(np.asarray(candidate)-tip)) if tip is not None and candidate is not None else None,path_gt_status='AVAILABLE' if len(gt) else 'PATH_GT_UNAVAILABLE',path_recall5=None,path_recall10=None,path_precision5=None,path_precision10=None,roi_contains_gt=None,first_observation_distance_to_gt_path=None,first_mislock_x=None,any_seed_near_gt=None,gt_path_sampled_fraction=None,overextension_x=None,stage='UNLABELED_OR_UNCERTAIN')
  if tip is not None:
   r['roi_contains_gt']=bool(g['xleft']<=tip[0]<g['xr'] and g['upper']<=tip[1]<=g['lower']) if g else False
   if public is not None:r['overextension_x']=public[0]-float(tip[0])
   if len(gt):
    dist=cKDTree(path).query(gt)[0] if len(path) else np.full(len(gt),np.inf);back=tree.query(path)[0] if len(path) else []
    for tol in [5,10]:r[f'path_recall{tol}']=float(np.mean(dist<=tol));r[f'path_precision{tol}']=float(np.mean(np.asarray(back)<=tol)) if len(back) else 0.
    obs=[row for row in trace if row[2]]
    if obs:r['first_observation_distance_to_gt_path']=float(tree.query(obs[0][:2])[0]);r['first_mislock_x']=next((row[0] for row in obs if tree.query(row[:2])[0]>10),None)
    seeds=result['seeds'];r['any_seed_near_gt']=bool(seeds and min(tree.query([s['x'],s['y']])[0] for s in seeds)<=10)
    ranges=collections.defaultdict(list)
    for hypothesis in result['paths'] or [dict(trace=trace)]:
     for row in hypothesis['trace']:ranges[row[0]].append((row[5],row[6]))
    r['gt_path_sampled_fraction']=sum(any(lo<=p[1]<hi for lo,hi in ranges[round(p[0])]) for p in gt)/len(gt)
   if not r['roi_contains_gt']:r['stage']='ROI_GEOMETRY_EXCLUSION'
   elif result['output_state']=='UNCERTAIN':r['stage']='UNCERTAIN_ORIGIN_OR_SUPPORT'
   elif public is None:r['stage']=result['output_state']
   elif r['error']<=10:r['stage']='TIP_WITHIN10_PATH_SEPARATE'
   elif (r['first_observation_distance_to_gt_path'] or 0)>10:r['stage']='WRONG_INITIAL_OBSERVATION'
   elif r['overextension_x']>10:r['stage']='OVEREXTENSION'
   else:r['stage']='EARLY_STOP_OR_UNRESOLVED'
  r['joint_tip_path_success']=bool(r['error'] is not None and r['error']<=10 and (r['path_recall10'] or 0)>=.8 and (r['path_precision10'] or 0)>=.8);out.append(r)
 return out
def main(validation=False):
 groups=VAL if validation else DEV;scope='validation' if validation else 'dev';assert (OUT/('validation_inference_complete.json' if validation else 'development_inference_complete.json')).exists()
 labels,access=getlabels(groups);save(OUT/f'annotation_access_{scope}.csv',access);metrics=[];allrows=[];runtime=[];divergences=[]
 for group in groups:
  group_rows=rows(OUT/'tables'/f'results_{group}.csv');assert len(group_rows)==COUNTS[group]*6;allrows.extend(group_rows)
  for fid in range(1,COUNTS[group]+1):
   folder=OUT/'frames'/group/str(fid);data=unpack(folder/'result.json.gz')
   if (group,fid) in labels:metrics.extend(score_frame(group,fid,folder,data,labels[group,fid]))
   runtime.append(dict(group=group,frame_id=fid,python_v2_ms=data['runtime_ms'],python_preprocess_ms=data['preprocess_ms'],decode_hash_ms=data['decode_hash_ms'],v1_compute_export_ms=data['baseline']['runtime_ms'],process_peak_rss_bytes=data['process_peak_rss_bytes'],startup_included=False,v2_io_included=False,worker_threads=1))
   base={r[0]:r for r in data['baseline']['trace']}
   for result in data['results']:
    first=next((r for r in result['trace'] if r[0] in base and (r[1]!=base[r[0]][1] or r[2]!=base[r[0]][2])),None);divergences.append(dict(group=group,frame_id=fid,mode=result['mode'],v1_seed=data['baseline']['chosen_seed'],v2_seed=result['chosen_seed'],first_shared_x=first[0] if first else None,v1_y=base[first[0]][1] if first else None,v2_y=first[1] if first else None,v1_observed=base[first[0]][2] if first else None,v2_observed=first[2] if first else None,v1_tip=data['baseline']['tip'],v2_tip=result['tip'],state=result['output_state']))
 save(OUT/f'offline_evaluation_{scope}.csv',metrics);save(OUT/f'all_results_{scope}.csv',allrows);save(OUT/f'first_divergence_vs_v1_{scope}.csv',divergences);save(OUT/f'runtime_frames_{scope}.csv',runtime)
 summary=[]
 for group in groups+['DEVELOPMENT' if not validation else 'EXPOSED_VALIDATION']:
  for mode in ['V1_LOCKED']+MODES:
   part=[r for r in metrics if r['mode']==mode and (group not in groups or r['group']==group)];v=[r for r in part if r['visibility']=='VISIBLE'];full=[r for r in allrows if r['mode']==mode and (group not in groups or r['group']==group)];err=[r['error'] for r in v if r['error'] is not None];rawerr=[r['raw_candidate_error'] for r in v if r['raw_candidate_error'] is not None];s=dict(group=group,mode=mode,frames=len(full),visible=len(v),uncertain_labels=len(part)-len(v),output_coverage=len(err),error_n=len(err),error_p50=float(np.percentile(err,50)) if err else None,error_p95=float(np.percentile(err,95)) if err else None,error_max=max(err) if err else None,roi_gt_outside=sum(r['roi_contains_gt'] is False for r in v),joint_tip_path_success=sum(r['joint_tip_path_success'] for r in v),real_FPR='N/A')
   for tol in [3,5,10]:s[f'hit{tol}']=sum(e<=tol for e in err);s[f'hit{tol}_fraction_all_visible']=s[f'hit{tol}']/max(1,len(v))
   for tol in [100,500]:s[f'over{tol}']=sum(e>tol for e in err);s[f'raw_candidate_over{tol}']=sum(e>tol for e in rawerr)
   for key in ['path_recall5','path_recall10','path_precision5','path_precision10','gt_path_sampled_fraction']:s[key]=float(np.mean([r[key] or 0 for r in v])) if v else None
   for state in ['PROVISIONAL_OBSERVED','UNCERTAIN','NO_TIP','ROI_LIMITED','INPUT_ERROR']:s['visible_'+state]=sum(r['output_state']==state for r in v);s['full_'+state]=sum(r['output_state']==state for r in full)
   summary.append(s)
 save(OUT/f'group_summary_{scope}.csv',summary)
 if not validation:
  base=next(r for r in summary if r['group']=='DEVELOPMENT' and r['mode']=='V1_LOCKED');assert base['visible']==76 and base['hit10']==12 and base['over100']==31
  comb=next(r for r in summary if r['group']=='DEVELOPMENT' and r['mode']=='V2_COMBINED');nonct3=sum(r['hit10']>0 for r in summary if r['group'] in ['group_a','ct2','group_h'] and r['mode']=='V2_COMBINED');accepted=comb['hit10']>12 and nonct3>=2 and comb['over100']<=31 and comb['over500']<=18 and comb['path_recall10']>=base['path_recall10'] and comb['path_precision10']>=base['path_precision10'];write(OUT/'development_acceptance.json',dict(accepted=accepted,combined=comb,non_ct3_groups_with_hit=nonct3,physical_path_identity_independent_truth=False))
 write(OUT/('validation_evaluation_complete.json' if validation else 'development_evaluation_complete.json'),dict(utc=utc(),frames=sum(COUNTS[g] for g in groups),labels=len(labels),visible=sum(r['visibility']=='VISIBLE' for r in metrics if r['mode']=='V1_LOCKED'),rules_unchanged=True));print('OFFLINE EVALUATION',scope,[(r['mode'],r['hit10'],r['over100']) for r in summary if r['group'] not in groups],flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--validation',action='store_true');a=p.parse_args();main(a.validation)
