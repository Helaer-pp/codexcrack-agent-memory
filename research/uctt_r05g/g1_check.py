from native import *
import cv2,numpy as np,shutil,subprocess

def main():
 cv2.setNumThreads(1);n=Native();records=[]
 def run(im,seed,pp=[[100,150],[100,350]]):
  h=n.create(im)
  try:return n.diagnostic(h,im,pp,seed,0,2)
  finally:n.close(h)
 for name,gap,curve in [('straight',0,False),('curved',0,True),('gap12',12,False),('gap24',24,False)]:
  im=np.full((512,768),180,np.uint8);prev=None
  for x in range(110,601):
   y=int(round(250+(.00022*(x-110)**2 if curve else 0)))
   if 330<=x<330+gap:prev=None;continue
   if prev is not None:cv2.line(im,prev,(x,y),65,2)
   prev=(x,y)
  t=run(im,[140,250,1,0]);write(OUT/'tests'/f'G1_{name}.json',t);tip=t['tracking_tip'];expected=np.array([600,250+(.00022*490**2 if curve else 0)]);error=float(np.linalg.norm(np.array(tip)-expected)) if tip else None
  records.append(dict(test=name,kind='synthetic',passed=error is not None and error<10 and not t['search_incomplete'],tracking_tip=tip,error=error,scans=t['scanline_count'],unique=t['unique_pixels_sampled'],ms=t['time_total_native_ms'],history_written=t['trusted_history_written']))
 im=np.full((512,768),180,np.uint8);t=run(im,[140,250,1,0]);records.append(dict(test='constant_gray',kind='synthetic',passed=not t['observed'] and not t['proposed_observed'],tracking_tip=t['tracking_tip']))
 # Projection geometry is tested under a non-horizontal seed/anchor frame.
 im=np.full((512,768),180,np.uint8);cv2.line(im,(160,170),(500,340),65,2);t=run(im,[180,180,2,1],[[180,80],[100,240]]);records.append(dict(test='rotated_coordinate',kind='synthetic',passed=bool(t['tracking_tip'] is not None and np.linalg.norm(np.array(t['tracking_tip'])-[500,340])<10)))
 save(OUT/'tests/G1_contracts.csv',records)
 write(OUT/'G1_pre_run_lock.json',dict(files={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [ROOT/'research/uctt_r05g/tracker.hpp',ROOT/'research/uctt_r05g/runtime.cpp',BUILD/'Release/R05G.dll']},parameters='beam=1 only build; no reference; no GT; thresholds fixed before real evaluation'))
 real=[]
 for row in rows(OUT/'selection.csv'):
  g=row['dataset_id'];f=int(row['frame_id']);require(g,'development');raw=Path(row['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=json.loads(row['points']);h=n.create(im)
  try:t=n.process(h,im,pp,0,2)
  finally:n.close(h)
  t.update(dataset_id=g,frame_id=f,variant='G1_GREEDY');write(OUT/'traces'/f'G1_{g}_{f}.json',t)
  path=[p for p in t['selected_path'] if p['visible']];distance=sum(np.linalg.norm(np.array(b['xy'])-a['xy']) for a,b in zip(path[:-1],path[1:]));dependent=0
  for scan in t['scans']:
   if scan['parent']>=0 and scan['phase']=='tracking':
    parent=t['nodes'][scan['parent']];delta=np.array(scan['predicted_point'])-parent['xy'];tangent=np.array(parent['tangent']);assert np.linalg.norm(delta-np.dot(delta,tangent)*tangent)<1e-6;assert np.dot(delta,tangent)>0;dependent+=1
  real.append(dict(dataset_id=g,frame_id=f,seeds=len(t['seeds']),visible_centers=len(path),visible_travel=distance,dependent_scanlines=dependent,scans=t['scanline_count'],unique_pixels=t['unique_pixels_sampled'],incomplete=t['search_incomplete'],reason=t['reason'],ms=t['time_total_native_ms']))
  print('G1',g,f,'centers',len(path),'travel',round(distance,1),'ms',round(t['time_total_native_ms'],2),flush=True)
 save(OUT/'experiments/G1_mechanism.csv',real)
 passed=all(r['passed'] for r in records[:2]) and all(any(r['dataset_id']==g and r['visible_centers']>=20 and r['visible_travel']>=30 and r['dependent_scanlines']>=20 for r in real) for g in DEV)
 write(OUT/'G1_gate.json',dict(status='PASS' if passed else 'FAIL',meaning='actual local dependent tracking mechanism only; no main-crack identity or final tip accuracy claim',synthetic=records,real_frames=len(real),supported_trajectories=sum(r['visible_centers']>=20 and r['visible_travel']>=30 for r in real),labels_opened=0))
 dest=OUT/'g1_build';dest.mkdir(exist_ok=True)
 for p in [ROOT/'research/uctt_r05g/tracker.hpp',ROOT/'research/uctt_r05g/runtime.cpp',BUILD/'Release/R05G.dll']:shutil.copy2(p,dest/p.name)
 print('G1 gate',passed,records,flush=True)
if __name__=='__main__':main()
