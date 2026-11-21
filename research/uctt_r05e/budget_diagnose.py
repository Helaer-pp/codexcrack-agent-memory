"""Explain losses from frozen B2 lineage; no rules/threshold changes."""
from common import *
from compare import original
import numpy as np
def main():
 assert (OUT/'B2_gate.json').exists();records=[];summary=[]
 for phase in ['dev','val']:
  file=OUT/f'evaluation_B2_{phase}.csv'
  if not file.exists():continue
  for row in rows(file):
   if row['capacity_lost_true_candidate10']!='True':continue
   g,f=row['dataset_id'],int(row['frame_id']);require(g,'comparison',uses_annotations=True);t=read(OUT/'traces'/f'B2_{g}__{f:06d}.json');candidates=t['evidence']['candidates'];gt=np.array([float(row['gt_x']),float(row['gt_y'])]);points=original([c['xy'] for c in candidates],t);dist=np.linalg.norm(points-gt,axis=1)
   reps={c['merged_id']:i for i,c in enumerate(candidates) if not c['reason'].startswith('directional_duplicate')};causes=[]
   for i in np.where(dist<=10)[0]:
    c=candidates[i];j=reps[c['merged_id']];rep=candidates[j];cause='BUCKET_CAPACITY' if rep['retained_id']<0 else 'MERGE_REPRESENTATIVE_OUTSIDE10';causes.append(cause)
    selected=[dict(id=q['id'],xy=q['xy'],gain=q['gain'],current_support=q['current_support'],slot=q['reason']) for q in candidates if q['bucket']==rep['bucket'] and q['retained_id']>=0 and not q['reason'].startswith('directional_duplicate')]
    records.append(dict(dataset_id=g,frame_id=f,phase=phase,raw_id=c['id'],source=c['source_channel'],raw_distance_px=float(dist[i]),raw_original=points[i].tolist(),raw_gain=c['gain'],raw_current_support=c['current_support'],raw_direction=c['direction'],raw_short_length=c['short_length'],merged_id=c['merged_id'],representative_raw_id=rep['id'],representative_distance_px=float(dist[j]),representative_original=points[j].tolist(),retained_id=rep['retained_id'],bucket=rep['bucket'],raw_reason=c['reason'],representative_reason=rep['reason'],first_loss=cause,retained_in_same_bucket=selected,old_A_hit5=row['hit5'],old_A_hit10=row['hit10'],counterfactual_control='B1/B2 raw peak lists identical; only compression differs',denominator='all near10px raw candidates in selected losses; labels joined after snapshots'))
   summary.append(dict(dataset_id=g,frame_id=f,phase=phase,causes=sorted(set(causes)),near_raw_count=int(np.sum(dist<=10)),raw_count=t['evidence']['raw_count'],retained_count=t['evidence']['retained_count'],old_A_hit5=row['hit5'],old_A_hit10=row['hit10'],trace=f'traces/B2_{g}__{f:06d}.json'))
 save(OUT/'budget_loss_lineage.csv',records);save(OUT/'budget_loss_cases.csv',summary)
 print('BUDGET LOSSES',len(summary),'cases',len(records),'near raw candidates',flush=True)
if __name__=='__main__':main()
