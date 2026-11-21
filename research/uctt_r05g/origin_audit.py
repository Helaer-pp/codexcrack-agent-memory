"""Offline audit of native origin-selection predicates; no annotation reads."""
from common import *
import numpy as np,collections
def main():
 rr=[];summary=[]
 for row in rows(OUT/'selection.csv'):
  g=row['dataset_id'];f=int(row['frame_id']);t=read(OUT/'traces'/f'E1_BEAM_{g}_{f}.json');L=t['spacing'];step=float(np.clip(L*.025,4,12));normal=np.array([-t['forward'][1],t['forward'][0]]);streak=longest=0;previous=None;reject=collections.Counter();eligible_count=0
  for s in t['scans']:
   if s['phase']!='origin':continue
   eligible=[]
   for j,c in enumerate(s['candidates']):
    reasons=[]
    if c['strength']<8:reasons.append('strength_below8')
    if abs(c['normal_offset'])>=s['halfwidth']*.8:reasons.append('origin_normal_gate')
    if c['width_scale']>max(8,.08*L):reasons.append('origin_width_scale_gate')
    if not reasons:eligible.append(c)
    reject.update(reasons);rr.append(dict(dataset_id=g,frame_id=f,scan_id=s['id'],candidate=j,xy=c['xy'],strength=c['strength'],normal_offset=c['normal_offset'],width_scale=c['width_scale'],width_limit=max(8,.08*L),normal_limit=.8*s['halfwidth'],eligible=not reasons,rejections=reasons))
   if not eligible:streak=0;previous=None
   else:
    c=eligible[0];eligible_count+=1;streak=streak+1 if previous is not None and abs((np.array(c['xy'])-previous)@normal)<max(3,step*.4) else 1;previous=np.array(c['xy']);longest=max(longest,streak)
  summary.append(dict(dataset_id=g,frame_id=f,seeds=len(t['seeds']),eligible_origin_scans=eligible_count,longest_admissible_streak=longest,**dict(reject)))
 save(OUT/'experiments/origin_candidate_audit.csv',rr);save(OUT/'experiments/origin_failure_summary.csv',summary);print([r for r in summary if r['dataset_id']=='ct3'],flush=True)
if __name__=='__main__':main()
