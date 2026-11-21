"""Isolated E0/E2, never used by AUTO. Same frozen seed across paired variants."""
from native import *
import cv2,numpy as np,math
def main():
 assert read(OUT/'G1_gate.json')['status']=='PASS';cv2.setNumThreads(1);n=Native();seedfile=OUT/'seeds/diagnostic_seeds.json';assert sha(seedfile)==read(OUT/'seeds/provenance_lock.json')['seed_sha256'];seeds={(r['dataset_id'],r['frame_id']):r for r in read(seedfile)};rr=[]
 variants={'E0_GREEDY':0,'E0_BEAM':1,'E0_CAPACITY_GREEDY':5,'E0_CAPACITY_BEAM':6}
 for row in rows(OUT/'selection.csv'):
  g=row['dataset_id'];f=int(row['frame_id']);require(g,'development');raw=Path(row['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=json.loads(row['points']);seed=seeds[g,f]['seed']
  for tag,variant in variants.items():
   h=n.create(im)
   try:t=n.diagnostic(h,im,pp,seed,variant,2)
   finally:n.close(h)
   assert not t['trusted_history_written'];t.update(dataset_id=g,frame_id=f,variant=tag,seed_quality=seeds[g,f]['quality']);write(OUT/'traces'/f'{tag}_{g}_{f}.json',t);rr.append({k:v for k,v in t.items() if k not in ['scans','nodes','seeds','ends','selected_path']})
  for name,offset,ang in [('normal_minus2',-2,0),('normal_plus2',2,0),('angle_minus5',0,-math.pi/36),('angle_plus5',0,math.pi/36)]:
   x,y,tx,ty=seed;s=[x-offset*ty,y+offset*tx,math.cos(ang)*tx-math.sin(ang)*ty,math.sin(ang)*tx+math.cos(ang)*ty];h=n.create(im)
   try:t=n.diagnostic(h,im,pp,s,1,0)
   finally:n.close(h)
   t.update(dataset_id=g,frame_id=f,variant='E0_PERTURB_'+name,seed_quality=seeds[g,f]['quality']);write(OUT/'traces'/f'E0_PERTURB_{name}_{g}_{f}.json',t);rr.append({k:v for k,v in t.items() if k not in ['scans','nodes','seeds','ends','selected_path']})
  print('E0/E2',g,f,flush=True)
 save(OUT/'experiments/seeded_frame_summary.csv',rr);write(OUT/'E0_E2_complete.json',dict(selected_frames=80,variant_calls=len(rr),labels_opened=0,seed_sha256=sha(seedfile),capacity='fixed high-capacity diagnostic, still2048px forward cap; NOT truly unbounded; not online default',perturbations='all80 x4 single-factor variants; no choosing best seed'))
if __name__=='__main__':main()
