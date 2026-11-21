"""Offline comparison only: labels cannot reach the native pipeline."""
from common import *
import numpy as np,zipfile,gzip,collections
from scipy.spatial import cKDTree
SENTINELS=[('group_a',504),('ct2',395),('ct2',196),('ct2',431),('ct2',457),('group_h',78),('group_h',41),('group_h',115),('ct3',65)]
def dense(points):
 p=np.array(points,float).reshape(-1,2);out=[]
 for a,b in zip(p[:-1],p[1:]):
  k=max(1,int(np.ceil(np.linalg.norm(b-a))));out.extend(a+(b-a)*np.arange(k)[:,None]/k)
 if len(p):out.append(p[-1])
 return np.array(out,float).reshape(-1,2)
def stream(g,tag='FULL'):
 with gzip.open(OUT/'traces'/f'{g}_{tag}.jsonl.gz','rt',encoding='utf8') as f:
  for line in f:yield json.loads(line)
def labels():
 result={};access=[]
 with zipfile.ZipFile(LABELS) as z:
  for row in rows(OUT/'selection.csv'):
   g=row['dataset_id'];require(g,'comparison',uses_annotations=True)
   if g in VAL:assert (OUT/f'validation_entry_{g}.json').exists()
   raw=z.read(row['selected_json']);result[g,int(row['frame_id'])]=json.loads(raw);access.append(dict(dataset_id=g,frame_id=row['frame_id'],member=row['selected_json'],sha256=hashlib.sha256(raw).hexdigest(),use='offline_comparison_only'))
 save(OUT/'annotation_access_log.csv',access);return result
def measure(t,label):
 tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];gtparts=[dense(s['points']) for s in label['shapes'] if s['label']=='crack_path'];gt=np.concatenate(gtparts) if gtparts else np.empty((0,2));visible=bool(tips)
 r=dict(dataset_id=t['dataset_id'],frame_id=t['frame_id'],variant=t['variant'],visibility='VISIBLE' if visible else 'UNCERTAIN',status=t['status'],observed=t['observed'],working_tip=t['working_tip'],reason=t['reason'],search_complete=t['search_complete'],history_written=t['history_written'],working_error=None,observed_error=None,stop_nearest=None,path_recall5=None,path_recall10=None,path_precision5=None,path_precision10=None,overshoot=None,correct_stop_preserved=False,first_failure='UNCERTAIN_LABEL')
 if not visible:return r
 tip=np.array(tips[0]);r['gt_tip']=tips[0]
 for field in ['working','observed']:
  if t[field+'_tip'] is not None:r[field+'_error']=float(np.linalg.norm(np.array(t[field+'_tip'])-tip))
 parts=[dense(p) for p in t['visible_segments'] if p];cp=np.concatenate(parts) if parts else np.empty((0,2))
 if len(gt):
  d=cKDTree(cp).query(gt)[0] if len(cp) else np.full(len(gt),np.inf)
  reverse=cKDTree(gt).query(cp)[0] if len(cp) else np.empty(0)
  for tol in [5,10]:r[f'path_recall{tol}']=float(np.mean(d<=tol));r[f'path_precision{tol}']=float(np.mean(reverse<=tol)) if len(reverse) else 0.
 if t['alternative_stops']:
  distances=[float(np.linalg.norm(np.array(q['xy'])-tip)) for q in t['alternative_stops']];idx=int(np.argmin(distances));r['stop_nearest']=distances[idx];r['correct_stop_preserved']=distances[idx]<=10;r['near_stop_rank']=idx;r['near_stop_score']=t['alternative_stops'][idx]['score'];r['chosen_stop_score']=t['alternative_stops'][t['selected_stop']]['score'] if t['selected_stop']>=0 else None
 near=float(cKDTree(cp).query(tip)[0]) if len(cp) else 1e9
 r['path_tip_nearest']=near
 if t['working_tip'] is not None:r['signed_forward_error']=float((np.array(t['working_tip'])-tip)@np.array(t['forward']))
 if near<=10 and t['working_tip'] is not None:r['overshoot']=r['signed_forward_error']
 # A retained near-GT alternative proves candidate reachability even if the selected prefix misses it.
 r['first_failure']='NO_ROOT' if not t['seed_count'] else 'NO_CURRENT_PATH' if not len(cp) else 'STOP_SELECTION' if r['correct_stop_preserved'] and r['working_error'] is not None and r['working_error']>10 else 'PATH_MISSES_TIP' if near>10 else 'STOP_NOT_PRESERVED' if not r['correct_stop_preserved'] else 'CONFIRMATION_REJECTED' if not t['observed'] else 'WITHIN_10'
 r['path_and_endpoint10']=bool(r['working_error'] is not None and r['working_error']<=10 and (r['path_recall10'] or 0)>=.9 and (r['path_precision10'] or 0)>=.9)
 return r
def main():
 assert read(OUT/'replay_complete.json')['frames']==2647;lock=read(OUT/'freeze.json')
 assert all(sha(ROOT/p)==s for p,s in lock['files'].items());labs=labels();evaluations=[];summary=[];regs=[];stops=[];runtimes=[];state=[]
 for g in ALL:
  for tag in (['FULL'] if g in VAL else ['FULL','NO_REFERENCE','LAST_ENDPOINT','NO_HISTORY']):
   for t in stream(g,tag):
    key=g,t['frame_id'];runtimes.append(dict(dataset_id=g,frame_id=t['frame_id'],variant=tag,io_decode_hash_ms=t['io_decode_hash_ms'],debug_export_ms=t['debug_export_ms'],**t['runtime_breakdown']))
    state.append(dict(dataset_id=g,variant=tag,frame_id=t['frame_id'],status=t['status'],seed_count=t['seed_count'],search_complete=t['search_complete'],history_written=t['history_written'],history_nav_valid=t['navigation']['state']=='VALID'))
    if key in labs:evaluations.append(measure(t,labs[key]))
    if tag=='FULL':
     for i,q in enumerate(t['alternative_stops']):
      if key in labs:stops.append(dict(dataset_id=g,frame_id=t['frame_id'],rank=i,selected=i==t['selected_stop'],**{k:v for k,v in q.items() if k!='reference'},reference_state=q['reference']['state'],reference_class=q['reference']['classification']))
      ref=q['reference']
      if ref['matches']:regs.append(dict(dataset_id=g,frame_id=t['frame_id'],stop_rank=i,selected=i==t['selected_stop'],**ref))
     if t['navigation']['matches']:regs.append(dict(dataset_id=g,frame_id=t['frame_id'],stop_rank=-1,selected=False,**t['navigation']))
 save(OUT/'experiments/selected_evaluation.csv',evaluations);save(OUT/'experiments/candidate_stop_audit.csv',stops);save(OUT/'experiments/registration_quality.csv',regs);save(OUT/'experiments/runtime_breakdown.csv',runtimes);save(OUT/'experiments/error_attribution.csv',evaluations)
 for group in ALL+['DEVELOPMENT','VALIDATION_ONLY']:
  for tag in ['FULL','NO_REFERENCE','LAST_ENDPOINT','NO_HISTORY']:
   selected=[r for r in evaluations if r['variant']==tag and (r['dataset_id']==group or group=='DEVELOPMENT' and r['dataset_id'] in DEV or group=='VALIDATION_ONLY' and r['dataset_id'] in VAL)];v=[r for r in selected if r['visibility']=='VISIBLE']
   if not selected:continue
   s=dict(dataset_id=group,variant=tag,visible=len(v),uncertain=len(selected)-len(v),observed=sum(r['observed'] for r in v),working=sum(r['working_error'] is not None for r in v),rejected=sum(not r['observed'] for r in v),incomplete=sum(not r['search_complete'] for r in v),path_and_endpoint10=sum(r.get('path_and_endpoint10',False) for r in v))
   for field in ['working','observed']:
    errors=[r[field+'_error'] for r in v if r[field+'_error'] is not None]
    for tol in [3,5,10]:s[f'{field}_hit{tol}']=sum(e<=tol for e in errors)
    for tol in [100,500]:s[f'{field}_over{tol}']=sum(e>tol for e in errors)
    s[field+'_p50']=float(np.median(errors)) if errors else None;s[field+'_max']=max(errors) if errors else None
   for metric in ['path_recall5','path_recall10','path_precision5','path_precision10']:s[metric]=float(np.mean([r[metric] or 0 for r in v])) if v else None
   summary.append(s)
 save(OUT/'experiments/per_group_summary.csv',summary);save(OUT/'experiments/ablations.csv',[r for r in summary if r['dataset_id']=='DEVELOPMENT']);write(OUT/'evaluation_summary.json',summary)
 stats=[]
 for g in ALL:
  rr=[r for r in runtimes if r['dataset_id']==g and r['variant']=='FULL'];ss=[r for r in state if r['dataset_id']==g and r['variant']=='FULL'];v=np.array([r['total_native_ms'] for r in rr]);reg=[r for r in regs if r['dataset_id']==g]
  stats.append(dict(dataset_id=g,frames=len(rr),states=dict(collections.Counter(r['status'] for r in ss)),seed_missing=sum(r['seed_count']==0 for r in ss),incomplete=sum(not r['search_complete'] for r in ss),history_writes=sum(r['history_written'] for r in ss),history_navigation_valid=sum(r['history_nav_valid'] for r in ss),p50=float(np.percentile(v,50)),p95=float(np.percentile(v,95)),p99=float(np.percentile(v,99)),max=float(v.max()),over50=int(sum(v>50)),over500=int(sum(v>500)),reference_attempts=len(reg),reference_valid=sum(r['state']=='VALID' for r in reg),reference_new=sum(r['classification']=='NEW' for r in reg),reference_old=sum(r['classification']=='OLD_TEXTURE' for r in reg)))
 write(OUT/'full_sequence_stats.json',stats);save(OUT/'experiments/full_sequence_stats.csv',stats)
 old={ (r['dataset_id'],int(r['frame_id'])):r for r in rows(G/'experiments/selected_visible_eval.csv') if r['variant']=='E1_BEAM'};sent=[]
 for g,f in SENTINELS:
  r=next(r for r in evaluations if r['dataset_id']==g and r['frame_id']==f and r['variant']=='FULL');prior=old.get((g,f),{});sent.append(r|{'R05G_auto_beam_error':prior.get('tracking_error_px')})
 save(OUT/'experiments/sentinels.csv',sent);write(OUT/'evaluation_complete.json',dict(selected=120,development_visible=76,validation_visible=35,uncertain=9,annotation_training=False,negative_fpr='N/A: insufficient real negative GT'))
 print(json.dumps([r for r in summary if r['dataset_id'] in ['DEVELOPMENT','VALIDATION_ONLY']],indent=2),flush=True)
if __name__=='__main__':main()
