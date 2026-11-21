from common import *
import numpy as np
def main():
 tags=['E1_GREEDY','E1_BEAM','E1_NO_GAP','E1_STRONG','E0_GREEDY','E0_BEAM','E0_CAPACITY_GREEDY','E0_CAPACITY_BEAM'];records=[]
 for row in rows(OUT/'selection.csv'):
  g=row['dataset_id'];f=int(row['frame_id'])
  for tag in tags:
   t=read(OUT/'traces'/f'{tag}_{g}_{f}.json');count=0;err=0.;maxstep=0.;maxc=0;assert not t['observed'] and not t['predicted'] and not t['trusted_history_written'] and t['tip'] is None
   for s in t['scans']:
    maxc=max(maxc,len(s['candidates']));assert len(s['candidates'])<=3
    if s['phase']=='tracking':
     p=t['nodes'][s['parent']];d=np.array(s['predicted_point'])-p['xy'];tan=np.array(p['tangent']);along=float(d@tan);error=float(np.linalg.norm(d-along*tan));err=max(err,error);maxstep=max(maxstep,along);assert error<1e-6 and 0<along<=3.000001;count+=1
   for p in t['nodes']:
    if p['parent']==-1:assert not p['visible'] and p['scan']==-1
    if p['visible']:
     assert p['strength']>=3-1e-8;scan=t['scans'][p['scan']];assert any(np.linalg.norm(np.array(c['xy'])-p['xy'])<1e-6 for c in scan['candidates'])
    elif p['parent']>=0:assert p['missing_distance']>0
   assert t['max_active_beam']<=max(t['beam_width'],len(t['seeds']))
   records.append(dict(dataset_id=g,frame_id=f,variant=tag,dependent_tracking_scans=count,max_cross_tangent_residual_px=err,max_forward_step_px=maxstep,max_local_candidates=maxc,max_active=t['max_active_beam'],bootstrap_seeds=len(t['seeds']),all_visible_nodes_have_current_candidate=True,seed_root_not_visible=True,history_write=False,formal_tip_null=True))
 save(OUT/'tests/native_trace_contracts.csv',records);write(OUT/'tests/native_trace_contracts_summary.json',dict(traces=len(records),dependent_scans=sum(r['dependent_tracking_scans'] for r in records),max_residual=max(r['max_cross_tangent_residual_px'] for r in records),max_step=max(r['max_forward_step_px'] for r in records),status='PASS',auto_greedy_bootstrap='up to3 origin hypotheses expanded once, thereafter width1; E0 uses one independent seed and is strict width1'))
 print(read(OUT/'tests/native_trace_contracts_summary.json'),flush=True)
if __name__=='__main__':main()
