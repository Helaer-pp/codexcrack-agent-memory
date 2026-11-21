"""Offline queries of actual visited windows, selected by comparator only."""
from common import *
import replay,ctypes as C,cv2,numpy as np,zipfile

def main():
 dest=OUT/'pixel_audit';dest.mkdir(exist_ok=False);replay.BUILD=ROOT/'output/build/uctt_r05f_probe';n=replay.Native()
 n.lib.R05FWindowAudit.argtypes=[C.c_void_p,C.c_int,C.POINTER(C.c_float),C.POINTER(C.c_ubyte),C.POINTER(C.c_ubyte),C.POINTER(C.c_int)];n.lib.R05FWindowAudit.restype=C.c_int
 metrics=rows(OUT/'experiments/B0_candidate_reachability.csv');keys={(r['dataset_id'],int(r['frame_id'])) for r in metrics if r['visibility']=='VISIBLE' and r['raw_hit10']=='False'}|{('ct2',395),('group_h',78),('group_a',504),('ct3',65),('group_a',398)}
 result=[]
 write(dest/'scope.json',dict(kind='OFFLINE_DIAGNOSTIC_NOT_RUNTIME',selection='all raw10 misses plus four required sentinels and prior budget-loss GROUP_A398',keys=sorted(keys),query='GT selects among ACTUAL visited windows for failure localization only; never detector windows or seeds',native_sha=sha(replay.BUILD/'Release/R05F.dll')))
 with zipfile.ZipFile(R05/'human_annotations_six_groups_snapshot.zip') as z:
  for s in filter_rows(rows(OUT/'selected_frames.csv'),'development'):
   g=s['dataset_id'];frame=int(s['frame_id'])
   if (g,frame) not in keys:continue
   require(g,'comparison',uses_annotations=True);label=json.loads(z.read(s['selected_json']));gt=np.array(next(x['points'][0] for x in label['shapes'] if x['label']=='crack_tip'))
   raw=Path(s['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==s['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=json.loads(s['points']);h=n.create(im,pp)
   try:
    t=n.process(h,im,pp);query=[]
    for w in t['windows']:
     forward=np.array(w['direction']);normal=np.array([-forward[1],forward[0]]);rel=gt-np.array(w['center']);width,height=w['size'];local=np.array([rel@forward+(width-1)/2,rel@normal+(height-1)/2])
     if not (-10<=local[0]<width+10 and -10<=local[1]<height+10):continue
     score=np.zeros((height,width),np.float32);valid=np.zeros((height,width),np.uint8);ridge=np.zeros_like(valid);labels=np.zeros((height,width),np.int32)
     rc=n.lib.R05FWindowAudit(h,w['id'],score.ctypes.data_as(C.POINTER(C.c_float)),valid.ctypes.data_as(C.POINTER(C.c_ubyte)),ridge.ctypes.data_as(C.POINTER(C.c_ubyte)),labels.ctypes.data_as(C.POINTER(C.c_int)));assert rc==width*height
     yy,xx=np.indices(score.shape);dist=np.hypot(xx-local[0],yy-local[1]);near=dist<=10
     components=[]
     for cid in np.unique(labels[near]):
      if cid==0:continue
      ys,xs=np.where(labels==cid);cols=np.unique(xs);endx=int(xs.max());iy=ys[xs==endx];endy=int(iy[np.argmax(score[iy,endx])]);endpoint=np.array(w['center'])+forward*(endx-(width-1)/2)+normal*(endy-(height-1)/2)
      components.append(dict(id=int(cid),pixels=len(xs),x_columns=len(cols),x_span=int(xs.max()-xs.min()+1),qualified=len(xs)>=4 and xs.max()-xs.min()+1>=4 and len(cols)>=4,endpoint_original=endpoint.tolist(),endpoint_distance=float(np.linalg.norm(endpoint-gt)),ridge_nearest=float(dist[ys,xs].min())))
     item=dict(dataset_id=g,frame_id=frame,window_id=w['id'],kind='offline_actual_window_audit',components=components)
     for tol in [3,5,10]:
      mask=dist<=tol;item[f'max_response{tol}']=float(score[mask].max()) if np.any(mask) else None;item[f'response_pixels{tol}']=int(np.sum((score>=3)&mask));item[f'ridge_pixels{tol}']=int(np.sum((ridge>0)&mask))
     result.append(item);np.savez_compressed(dest/f'{g}_{frame}_w{w["id"]}.npz',score=score,valid=valid,ridge=ridge,components=labels,gt_local=local,window=np.array(w['polygon']))
   finally:n.close(h)
 save(dest/'response_to_segment_audit.csv',result)
 write(dest/'response_to_segment_audit.json',result)
 print('PIXEL AUDIT',len(keys),'frames',len(result),'actual windows',flush=True)
 for r in result:
  if r['dataset_id']=='group_h' and r['frame_id']==78:print(r,flush=True)
if __name__=='__main__':main()
