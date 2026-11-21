"""Fixed +2% spacing x-shift initial-anchor sensitivity, development only."""
import numpy as np,cv2
from common import *
from replay import loadlib,make,maps
def main():
 cv2.setNumThreads(1);lib=loadlib(BUILD/'Release/D0_TRACE_ONLY.dll');targets={'ct2':395,'group_h':78,'group_a':504,'ct3':65};inventory=rows(OUT/'input_inventory_allowed.csv');modes={g['id']:g['mode'] for g in read(ROOT/'config/datasets.json')['groups']};modes['ct3']='auto';records=[]
 for g,last in targets.items():
  require(g,'development');engine=None
  try:
   for r in [r for r in inventory if r['dataset_id']==g and int(r['frame_id'])<=last]:
    f=int(r['frame_id']);raw=Path(r['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=json.loads(r['points']);lib.R05DCapture(int(f==last))
    if engine is None:
     shifted=np.array(pp,float);shift=.02*np.linalg.norm(shifted[1]-shifted[0]);shifted[:,0]+=shift;assert np.all(shifted[:,0]<im.shape[1]);engine=make(lib,im,shifted.tolist(),modes[g])
    result=engine.run(im,pp,is_reference=f==1)
    if f==last:
     t=json.loads(lib.R05DRead(engine.handle));t.update(dataset_id=g,frame_id=f,variant='INIT_X_PLUS_2PCT',formal=result['formal'],source_sha256=r['sha256'],original_current_anchors=pp,init_shift_x=shift)
     write(OUT/'traces'/f'{g}__{f:06d}__init.json',t);np.savez_compressed(OUT/'maps'/f'{g}__{f:06d}__init.npz',**maps(engine));records.append(dict(dataset_id=g,frame_id=f,init_shift_x=shift,tip_transform=t['tip_transform'],roi=t['roi'],motion_branch=t['motion_branch'],observed=result['formal']['confirmed_tip'],tip=result['formal']['tip'],source=f'traces/{g}__{f:06d}__init.json'))
  finally:
   if engine is not None:engine.close()
  print('INITIALIZATION PROBE',g,last,flush=True)
 save(OUT/'initialization_transform_comparison.csv',records);write(OUT/'initialization_probe_complete.json',dict(cases=4,frames=sum(targets.values()),fixed_rule='initial P1 and P2 +0.02*spacing in x; current tracking unchanged',annotation_reads=0,validation_uses=0,real_new_upstream_trajectories=False))
if __name__=='__main__':main()
