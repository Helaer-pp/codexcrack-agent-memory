from common import *
import gzip,numpy as np,collections
TAGS=['E1_GREEDY','E1_BEAM','E1_NO_GAP','E1_STRONG']
def stream(tag):
 with gzip.open(OUT/'traces'/f'{tag}_frames.jsonl.gz','rt',encoding='utf8') as f:
  for line in f:yield json.loads(line)
def main():
 metrics=rows(OUT/'experiments/all_variants_frame_summary.csv');index={(r['variant'],r['dataset_id'],int(r['frame_id'])):r for r in metrics};audit=[];locks=collections.defaultdict(list)
 for i,ts in enumerate(zip(*(stream(tag) for tag in TAGS))):
  base=ts[1];g=base['dataset_id'];f=base['frame_id']
  for tag,t in zip(TAGS,ts):
   assert (t['dataset_id'],t['frame_id'])==(g,f);r=index[tag,g,f];maximum=0.;lengths=[]
   for prev,node in zip(t['selected_path'][:-1],t['selected_path'][1:]):
    assert prev['id']==node['parent'];scan=t['scans'][node['scan']];delta=np.array(scan['predicted_point'])-prev['xy'];tan=np.array(prev['tangent']);step=float(delta@tan);assert np.linalg.norm(delta-step*tan)<1e-6 and 0<step<=3.000001;maximum=max(maximum,step)
   selected=t['ends'][t['selected_end']] if t['selected_end']>=0 else None
   r.update(observation_center_child_count=t['beam_expansions']-t['missing_steps'],candidate_count_scope='all local extrema count captured for80 detailed frames only; observation_center_child_count available for every frame',selected_chain_max_prediction_step_px=maximum,all_branch_rule_step_bound_px=float(np.clip(t['spacing']/160,1.5,3)),selected_chain_visible_fraction=selected['visible_fraction'] if selected else None,exploration_frontier_projection_px=max((float((np.array(s['predicted_point'])-t['origin'])@np.array(t['forward'])) for s in t['scans']),default=None),trusted_frontier=None,physical_phase='PHASE_UNKNOWN')
   if tag!='E1_BEAM':audit.append(dict(dataset_id=g,frame_id=f,variant=tag,seeds_exact=t['seeds']==base['seeds']))
   if tag=='E1_BEAM':locks[g].append((f,bool(t['proposed_observed'])))
  if (i+1)%200==0:print('full trace audit',i+1,flush=True)
 assert len(metrics)==6260 and len(audit)==4695
 save(OUT/'experiments/all_variants_frame_summary.csv',metrics);save(OUT/'experiments/frame_summary.csv',[r for r in metrics if r['variant']=='E1_BEAM']);save(OUT/'experiments/full_automatic_seed_pairing_audit.csv',audit)
 write(OUT/'tests/full_trace_summary.json',dict(frames=1565,variants=4,seed_pairs=4695,seed_pairs_equal=sum(r['seeds_exact'] for r in audit),different_pairs=[r for r in audit if not r['seeds_exact']],all_selected_chain_dependency_verified=True,all_branches_step_max='rule bound from frozen native implementation; exhaustive actual per-branch node verification in640 detailed traces',first_formal_lock=None,first_proposed={g:next((f for f,v in seq if v),None) for g,seq in locks.items()}));print(read(OUT/'tests/full_trace_summary.json'),flush=True)
if __name__=='__main__':main()
