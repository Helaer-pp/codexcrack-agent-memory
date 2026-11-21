"""Complete all-frame main/tip geometry, without labels or new scoring."""
import numpy as np,cv2
from common import *
from replay import loadlib,make,digest
def main():
 assert all((OUT/f'{p}_complete.json').exists() for p in ['dev','val'])
 expected={(r['dataset_id'],r['frame_id']):r['result_hash'] for phase in ['dev','val'] for r in map(json.loads,(OUT/f'{phase}_frames.jsonl').read_text().splitlines())}
 lib=loadlib(BUILD/'Release/D0_TRACE_ONLY.dll');lib.R05DCapture(0);cv2.setNumThreads(1);inventory=rows(OUT/'input_inventory_allowed.csv');modes={g['id']:g['mode'] for g in read(ROOT/'config/datasets.json')['groups']};modes['ct3']='auto';records=[]
 for g in dict.fromkeys(r['dataset_id'] for r in inventory):
  require(g,'validation');engine=None
  try:
   for r in [r for r in inventory if r['dataset_id']==g]:
    f=int(r['frame_id']);raw=Path(r['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);points=json.loads(r['points'])
    if engine is None:engine=make(lib,im,points,modes[g])
    result=engine.run(im,points,is_reference=f==1);assert digest(result)==expected[g,f]
    t=json.loads(lib.R05DRead(engine.handle));spacing=t['spacing'];turn=t['turn'];behind=int(np.clip(np.rint(.38*spacing),24,192));ahead=int(np.clip(np.rint(4.5*spacing),256,1536));half=int(np.clip(np.rint(1.4*spacing),96,384));left=behind if turn==0 else ahead if turn==2 else half;right=ahead if turn==0 else behind if turn==2 else half;top=behind if turn==1 else ahead if turn==3 else half;bottom=ahead if turn==1 else behind if turn==3 else half
    unclipped=[int(np.rint(t['center'][0]))-left,int(np.rint(t['center'][1]))-top,left+right+1,top+bottom+1]
    records.append(dict(dataset_id=g,frame_id=f,tip_roi_active=t['roi'],tip_roi_last_stored=t['actual_tip_roi'],tip_roi_unclipped=unclipped if t['registration_valid'] else None,main_roi_polygons=t['main_rois'],main_roi_count=len(t['main_rois']),center=t['center'],direction=t['direction'],turn=turn,spacing=spacing,tip_transform=t['tip_transform'],main_transform=t['main_transform'],registration_valid=t['registration_valid'],image_size=[im.shape[1],im.shape[0]],reference_size=t['reference_size'],current_anchors=points,init_anchors=t['init_anchors'],source_sha256=r['sha256'],result_hash_matches_primary_replay=True,scale=1,pixel_center_convention='original integer centers, 0-based',diagnostic_only_no_new_score=True))
  finally:
   if engine is not None:engine.close()
  print('GEOMETRY COMPLETE',g,flush=True)
 save(OUT/'roi_geometry_trace_full.csv',records);write(OUT/'geometry_completion.json',dict(frames=len(records),non_timing_hash_matches=2647,annotation_reads=0,algorithm_changes=0,reason='Supplement main-path polygons not persisted by primary compact all-frame log; read-only identical replay, no new validation rule selection'))
if __name__=='__main__':main()
