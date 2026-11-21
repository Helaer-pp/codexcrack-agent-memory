"""Offline query of native scans against the already diagnosed R05F short fragments."""
from common import *
from evaluate import SENTINELS
import numpy as np
def main():
 prior=read(F/'pixel_audit/response_to_segment_audit.json');components=[]
 for r in prior:
  if r['dataset_id']=='group_h' and r['frame_id']==78:
   for c in r['components']:
    if c['x_columns'] in [2,3] and c['endpoint_distance']<6:components.append(dict(window_id=r['window_id'],**c))
 oldtrace=read(F/'traces/B0_group_h_78.json')
 records=[]
 for c in components:
  p=np.array(c['endpoint_original'])
  w=next(w for w in oldtrace['windows'] if w['id']==c['window_id']);data=np.load(F/'pixel_audit'/f'group_h_78_w{c["window_id"]}.npz');ys,xs=np.where(data['components']==c['id']);direction=np.array(w['direction']);normal=np.array([-direction[1],direction[0]]);width,height=w['size'];ridge=np.array(w['center'])+(xs-(width-1)/2)[:,None]*direction+(ys-(height-1)/2)[:,None]*normal
  support=set()
  for rp in ridge:
   ix,iy=np.floor(rp).astype(int)
   for dx in [0,1]:
    for dy in [0,1]:support.add((int(ix+dx),int(iy+dy)))
  for tag in ['E1_GREEDY','E1_BEAM','E1_NO_GAP','E1_STRONG','E0_GREEDY','E0_BEAM']:
   t=read(OUT/'traces'/f'{tag}_group_h_78.json');hits=[]
   for s in t['scans']:
    delta=p-np.array(s['predicted_point']);a=float(delta@np.array(s['tangent']));u=float(delta@np.array(s['normal']));extent=int(np.ceil(s['halfwidth'])+s['max_radius']+2)
    if abs(a)<=1.8 and abs(u)<=extent+1:
     index=int(round(u))+extent;response=s['response'][index] if 0<=index<len(s.get('response',[])) else None
     near=[x for x in s.get('candidates',[]) if np.linalg.norm(np.array(x['xy'])-p)<=3];raw=[x for x in s.get('raw_candidates',[]) if np.linalg.norm(np.array(x['xy'])-p)<=3];children=[t['nodes'][i] for i in s.get('children',[])];kids=[n for n in children if n['visible'] and np.linalg.norm(np.array(n['xy'])-p)<=3]
     addresses=set();center=np.array(s['predicted_point']);tan=np.array(s['tangent']);normal=np.array(s['normal'])
     for nu in range(-extent,extent+1):
      for along in [-.8,0,.8]:
       ix,iy=np.floor(center+nu*normal+along*tan).astype(int)
       for dx in [0,1]:
        for dy in [0,1]:addresses.add((int(ix+dx),int(iy+dy)))
     hits.append(dict(scan_id=s['id'],step=s['step_index'],phase=s['phase'],longitudinal_distance=a,normal_offset=u,response_at_nearest_sample=response,raw_near3=raw,candidates_near3=near,exact_original_pixel_support_overlap=sorted(addresses&support),children_near3=[dict(node_id=n['id'],retained=n['retained'],decision=n['decision']) for n in kids]))
   chosen=[n for n in t['selected_path'] if n['visible'] and np.linalg.norm(np.array(n['xy'])-p)<=3]
   records.append(dict(variant=tag,R05F_window=c['window_id'],columns=c['x_columns'],fragment_endpoint=p.tolist(),fragment_ridge_original=ridge.tolist(),original_bilinear_support=sorted(support),R05F_distance_to_GT=c['endpoint_distance'],actual_sampling_strip_hits=hits,selected_chain_nodes_near3=[n['id'] for n in chosen],selected_chain_steps_near3=[n['step'] for n in chosen],read_semantics='native scalar bilinear addresses reconstructed from logged scan geometry; overlap with actual R05F component source support; subpixel endpoint itself is not an exact address',conclusion='CONNECTED_AS_UNCONFIRMED_CURRENT_OBSERVATION' if chosen else 'READ_BUT_NOT_SELECTED_CHAIN' if hits else 'NOT_VISITED_BY_TRACKER'))
 write(OUT/'tests/group_h78_short_fragment_audit.json',records)
 flat=[dict(variant=r['variant'],R05F_window=r['R05F_window'],columns=r['columns'],original_endpoint=r['fragment_endpoint'],visited_scans=len(r['actual_sampling_strip_hits']),retained_candidate_scans=sum(bool(s['candidates_near3']) for s in r['actual_sampling_strip_hits']),chosen_steps=r['selected_chain_steps_near3'],conclusion=r['conclusion']) for r in records];save(OUT/'experiments/group_h78_short_fragment_audit.csv',flat);print(flat,flush=True)
if __name__=='__main__':main()
