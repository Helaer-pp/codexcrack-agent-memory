"""Offline comparison only. Never imports detector/replay/native ABI."""
from common import *
import argparse,zipfile,numpy as np,collections
def original(points,t):
 p=np.array(points,float).reshape(-1,2).copy();x,y,w,h=t['roi'];u,v=p[:,0].copy(),p[:,1].copy()
 if t['turn']==1:p[:,0]=w-1-v;p[:,1]=u
 elif t['turn']==2:p[:,0]=w-1-u;p[:,1]=h-1-v
 elif t['turn']==3:p[:,0]=v;p[:,1]=h-1-u
 return p+[x,y]
def local(points,t):
 x,y,w,h=t['roi'];p=np.array(points,float).reshape(-1,2)-[x,y];u,v=p[:,0].copy(),p[:,1].copy()
 if t['turn']==1:p[:,0]=v;p[:,1]=w-1-u
 elif t['turn']==2:p[:,0]=w-1-u;p[:,1]=h-1-v
 elif t['turn']==3:p[:,0]=h-1-v;p[:,1]=u
 return p
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['B1','B2']);p.add_argument('phase',choices=['dev','val']);a=p.parse_args();mode,phase=a.mode,a.phase
 assert read(OUT/f'{mode}_{phase}_complete.json')['status']=='PASS'
 if phase=='val':assert (OUT/'validation_freeze.json').exists()
 subset=DEV if phase=='dev' else VAL;records=[]
 old={(r['dataset_id'],r['frame_id']):r for r in rows(D/f'reachability_{phase}.csv')}
 selection=[r for r in rows(OUT/'selected_frames.csv') if r['dataset_id'] in subset]
 with zipfile.ZipFile(R05/'human_annotations_six_groups_snapshot.zip') as z:
  for r in selection:
   g=r['dataset_id'];f=int(r['frame_id']);require(g,'comparison',uses_annotations=True);name=f'{g}__{f:06d}'
   t=read(OUT/'traces'/f'{mode}_{name}.json');e=t['evidence'];label=json.loads(z.read(r['selected_json']));tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];visible=len(tips)==1;gt=np.array(tips[0]) if visible else None
   cand=e['candidates'];raw=original([p['xy'] for p in cand],t)
   # A duplicate's retained_id refers to its representative, NOT its own coordinate.
   retained=original([p['xy'] for p in cand if p['retained_id']>=0 and not p['reason'].startswith('directional_duplicate')],t)
   rd=np.linalg.norm(raw-gt,axis=1) if visible else np.array([]);kd=np.linalg.norm(retained-gt,axis=1) if visible else np.array([])
   tip=t['formal']['tip'];err=float(np.linalg.norm(np.array(tip)-gt)) if visible and tip is not None else None
   v=dict(dataset_id=g,frame_id=f,mode=mode,phase=phase,gt_visibility='VISIBLE' if visible else 'UNCERTAIN',observed=t['formal']['confirmed_tip'],predicted=False,fallback=False,output_kind='unchanged legacy output; new sidecar has no output',output_x=tip[0] if tip else None,output_y=tip[1] if tip else None,gt_x=float(gt[0]) if visible else None,gt_y=float(gt[1]) if visible else None,error_px=err,raw_count=e['raw_count'],retained_count=e['retained_count'],raw_nearest_px=float(rd.min()) if len(rd) else None,retained_nearest_px=float(kd.min()) if len(kd) else None,r05d_stage=old[g,str(f)]['first_failure_stage'],new_sidecar_observed=False,wrong_lock_flag=None,missing_reason=t['terminal_cause'],denominator='76 VISIBLE + 4 UNCERTAIN development selections' if phase=='dev' else '35 VISIBLE + 5 UNCERTAIN validation-only selections')
   with np.load(OUT/'maps'/f'{name}.npz') as maps:
    for tol in [3,5,10]:
     v[f'hit{tol}']=err<=tol if err is not None else False if visible else None
     v[f'raw_candidate{tol}']=bool(np.any(rd<=tol)) if visible else None;v[f'retained_candidate{tol}']=bool(np.any(kd<=tol)) if visible else None
     v[f'current_evidence{tol}']=None;v[f'legacy_evidence{tol}']=None;v[f'current_max{tol}']=None
     if visible and 'currentEvidence' in maps:
      q=local([gt],t)[0];h,w=maps['currentEvidence'].shape;yy,xx=np.ogrid[:h,:w];mask=(xx-q[0])**2+(yy-q[1])**2<=tol*tol
      if np.any(mask):
       values=maps['currentEvidence'][mask];v[f'current_evidence{tol}']=bool(np.any(values>=3));v[f'legacy_evidence{tol}']=bool(np.any(maps['legacy'][mask]>=3));v[f'current_max{tol}']=float(values.max())
       if tol==10:v['reference_valid_fraction10']=float(np.mean(maps['referenceQuality'][mask]>0));v['restored_pixels10']=int(np.sum((values>=3)&(maps['legacy'][mask]<3)))
   v['capacity_lost_true_candidate10']=visible and v['raw_candidate10'] and not v['retained_candidate10']
   v['raw_distant_from_gt10_count_not_fp']=int(np.sum(rd>10)) if visible else None
   v['retained_distant_from_gt10_count_not_fp']=int(np.sum(kd>10)) if visible else None
   v['current_source_near10']=any(d<=10 and 'current' in c.get('source_channel','current') for c,d in zip(cand,rd)) if visible else None
   v['first_failure_stage']='UNCERTAIN' if not visible else 'G0' if v['current_evidence10'] is None else 'G1' if not v['current_evidence10'] else 'G2_RAW' if not v['raw_candidate10'] else 'G2_BUDGET' if not v['retained_candidate10'] else 'B3_BLOCKED'
   records.append(v)
 save(OUT/f'evaluation_{mode}_{phase}.csv',records)
 if phase=='dev' and mode=='B1':
  sent=[r for r in records if (r['dataset_id'],r['frame_id']) in [('ct2',395),('group_h',78)]]
  restored=[r for r in records if r['r05d_stage']=='G1' and r['current_evidence10']]
  passed=len(sent)==2 and all(r['current_evidence10'] for r in sent) and len(restored)>0
  write(OUT/'B1_gate.json',dict(status='PASS' if passed else 'FAIL',sentinels=sent,restored_G1=len(restored),visible=76,full_replay_equivalence=1565,meaning='independent current response only; NOT candidate recall/accuracy'))
 if phase=='dev' and mode=='B2':
  lost=[r for r in records if r['capacity_lost_true_candidate10']];group_a=next(r for r in records if r['dataset_id']=='group_a' and r['frame_id']==504)
  write(OUT/'B2_gate.json',dict(status='FAIL' if lost or not group_a['retained_candidate10'] else 'NOT_VERIFIED',capacity_losses=lost,group_a504=group_a,visible=76,meaning='Any raw true candidate lost within10px fails. Timing and control prerequisites also required before a PASS.'))
 print(mode,phase,'visible',sum(r['gt_visibility']=='VISIBLE' for r in records),'current10',sum(bool(r['current_evidence10']) for r in records),'raw10',sum(bool(r['raw_candidate10']) for r in records),'retained10',sum(bool(r['retained_candidate10']) for r in records),'losses',sum(bool(r['capacity_lost_true_candidate10']) for r in records),flush=True)
if __name__=='__main__':main()
