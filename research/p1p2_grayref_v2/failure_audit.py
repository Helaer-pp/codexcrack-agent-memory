from v2common import *
from evaluate_v2 import getlabels,dense,observed_dense
from scipy.spatial import cKDTree
import numpy as np,itertools,math
def main():
 assert (OUT/'validation_evaluation_complete.json').exists();labels,_=getlabels(DEV+VAL);records=[];overlap=[]
 for (group,fid),label in labels.items():
  folder=OUT/'frames'/group/str(fid);data=unpack(folder/'result.json.gz');parts=[dense(s['points']) for s in label['shapes'] if s['label']=='crack_path'];gt=np.concatenate(parts) if parts else np.empty((0,2));tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];tree=cKDTree(gt) if len(gt) else None;g=data['roi'];width=min(96,max(24,math.floor(.35*(g['lower']-g['upper'])+.5)));inorigin=(gt[:,0]>=g['xleft']+6)&(gt[:,0]<=g['xleft']+6+width)&(gt[:,1]>=g['upper']+7)&(gt[:,1]<g['lower']-7) if len(gt) else []
  with np.load(folder/'evidence.npz') as z:a={k:z[k] for k in z.files}
  for r in data['results']:
   near=[s for s in r['seeds'] if tree is not None and tree.query([s['x'],s['y']])[0]<=10];probe=[]
   if len(gt):
    for x,y in gt[np.asarray(inorigin,dtype=bool)]:
     xx=round(x)-g['xa'];yy=round(y)-g['ya']
     if 0<=yy<a['valley'].shape[0] and 0<=xx<a['valley'].shape[1]:probe.append((float(a['valley'][yy,xx]),float(a['newdark'][yy,xx]),bool(a['valid_material'][yy,xx])))
   records.append(dict(group=group,frame_id=fid,visibility='VISIBLE' if tips else 'UNCERTAIN',mode=r['mode'],state=r['output_state'],origin_gt_points=int(np.sum(inorigin)) if len(gt) else None,raw_seeds_near_gt10=len(near),near_seed_reasons={reason:sum(s['reason']==reason for s in near) for reason in sorted(set(s['reason'] for s in near))},origin_gt_current_pass=sum(v>=10 and valid for v,d,valid in probe),origin_gt_joint_pass=sum(v>=10 and d>=10 and valid for v,d,valid in probe),chosen_seed=r['chosen_seed'],ambiguous=r['ambiguous'],offline_only=True))
   for p,q in itertools.combinations(r['paths'],2):
    x=observed_dense(p['trace']);y=observed_dense(q['trace']);pq=float(np.mean(cKDTree(y).query(x)[0]<=5)) if len(x) and len(y) else 0.;qp=float(np.mean(cKDTree(x).query(y)[0]<=5)) if len(x) and len(y) else 0.;overlap.append(dict(group=group,frame_id=fid,mode=r['mode'],path_a=p['id'],path_b=q['id'],a_within5_b=pq,b_within5_a=qp,ambiguous=r['ambiguous'],interpretation='Computed path overlap, not independent physical identity truth'))
 # D has no exact LabelMe GT: audit only overlaps and explicitly exported origins.
 d=unpack(OUT/'sentinels/D/result.json.gz')
 for r in d['results']:
  for p,q in itertools.combinations(r['paths'],2):
   x=observed_dense(p['trace']);y=observed_dense(q['trace']);overlap.append(dict(group='D_same_BMP',frame_id=237,mode=r['mode'],path_a=p['id'],path_b=q['id'],a_within5_b=float(np.mean(cKDTree(y).query(x)[0]<=5)) if len(x) and len(y) else 0,b_within5_a=float(np.mean(cKDTree(x).query(y)[0]<=5)) if len(x) and len(y) else 0,ambiguous=r['ambiguous'],interpretation='Unlabeled D computed-path overlap only'))
 save(OUT/'origin_failure_audit.csv',records);save(OUT/'hypothesis_overlap_audit.csv',overlap)
 audit=rows(OUT/'D_two_origins_audit.csv')
 for r in audit:
  if r['mode']=='V1_LOCKED':r['generated_raw']='';r['note']='V1 raw initializer list not exported here; empty wrapper seed list is NOT evidence of no candidate. Full y scan in immutable source/previous initial_candidate_audit.csv. This row reports only the original chosen seed.'
 save(OUT/'D_two_origins_audit.csv',audit);write(OUT/'failure_audit_complete.json',dict(utc=utc(),labeled_records=len(records),overlap_records=len(overlap),no_inference_changes=True));print('FAILURE AUDIT COMPLETE',flush=True)
if __name__=='__main__':main()
