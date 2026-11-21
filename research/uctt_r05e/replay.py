"""Sequential native shadow runner; labels and human coordinates are not inputs."""
from common import *
from baseline import load,make,clean,digest
import argparse,ctypes as C,cv2,numpy as np,collections,psutil
def configure(lib):
 lib.R05DRead.argtypes=[C.c_void_p];lib.R05DRead.restype=C.c_char_p
 lib.R05ERead.argtypes=[C.c_void_p];lib.R05ERead.restype=C.c_char_p
 lib.R05DCapture.argtypes=[C.c_int]
 lib.R05DMap.argtypes=[C.c_void_p,C.c_int,*([C.POINTER(C.c_int)]*4)];lib.R05DMap.restype=C.c_void_p
 lib.R05EMap.argtypes=[C.c_void_p,C.c_int,*([C.POINTER(C.c_int)]*3)];lib.R05EMap.restype=C.c_void_p
def maps(e):
 out={}
 for extended,names in [(False,['current','legacy','registered','prior','legacy_reason','valid','legacy_gains','legacy_back']),(True,['currentEvidence','referenceEvidence','referenceChange','referenceQuality','reasonMask','valley','novel','eroded','refMin','refMax'])]:
  for i,name in enumerate(names):
   h,w,typ,stride=[C.c_int() for _ in range(4)]
   if extended:p=e.lib.R05EMap(e.handle,i,C.byref(h),C.byref(w),C.byref(stride));dtype=np.float32
   else:p=e.lib.R05DMap(e.handle,i,C.byref(h),C.byref(w),C.byref(typ),C.byref(stride));dtype={0:np.uint8,1:np.int8,5:np.float32}[typ.value]
   if not p or not h.value:continue
   raw=C.string_at(p,h.value*stride.value);out[name]=np.ndarray((h.value,w.value),dtype=dtype,buffer=raw,strides=(stride.value,np.dtype(dtype).itemsize)).copy()
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['B1','B2']);p.add_argument('phase',choices=['dev','val','perf']);args=p.parse_args();mode,phase=args.mode,args.phase
 assert read(OUT/'B0_complete.json')['status']=='PASS'
 if mode=='B2':assert read(OUT/'B1_gate.json')['status']=='PASS'
 if phase=='val':assert (OUT/'validation_freeze.json').exists()
 cv2.setNumThreads(1);tag=mode+'_'+phase;assert not (OUT/f'{tag}_complete.json').exists()
 lib=load(BUILD/f'Release/{mode}.dll');configure(lib);proc=psutil.Process()
 subsets=VAL if phase=='val' else DEV;purpose='validation' if phase=='val' else 'development'
 groups=collections.defaultdict(list)
 for r in filter_rows(rows(OUT/'input_inventory_allowed.csv'),purpose):
  if r['dataset_id'] in subsets:groups[r['dataset_id']].append(r)
 selected={(r['dataset_id'],int(r['frame_id'])) for r in rows(OUT/'selected_frames.csv') if r['dataset_id'] in subsets}
 old={(r['dataset_id'],r['frame_id']):r for r in map(json.loads,(D/('val_frames.jsonl' if phase=='val' else 'dev_frames.jsonl')).read_text().splitlines())}
 modes={g['id']:g['mode'] for g in read(ROOT/'config/datasets.json')['groups']};modes['ct3']='auto'
 write(OUT/f'{tag}_replay_lock.json',dict(dll_sha=sha(BUILD/f'Release/{mode}.dll'),source={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'research/uctt_r05e').glob('*') if p.is_file()},input_inventory=sha(OUT/'input_inventory_allowed.csv'),groups=subsets,annotation_reads=0,threads=4))
 perf=[];counts=[];eq=[];candidate_hashes=[]
 with (OUT/f'{tag}_frames.jsonl').open('w',encoding='utf8') as output:
  for g,seq in groups.items():
   e=None
   try:
    for i,r in enumerate(seq):
     require(g,purpose);assert int(r['frame_order'])==i;f=int(r['frame_id']);chosen=(g,f) in selected and phase!='perf';lib.R05DCapture(int(chosen))
     raw=Path(r['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=json.loads(r['points'])
     if e is None:e=make(lib,im,pp,modes[g])
     res=e.run(im,pp,is_reference=i==0);rh=digest(res);exact=rh==old[g,f]['result_hash'];assert exact,(tag,g,f,'PRODUCTION_CHANGED')
     trace=json.loads(lib.R05DRead(e.handle));side=json.loads(lib.R05ERead(e.handle));name=f'{g}__{f:06d}'
     trace.update(dataset_id=g,frame_id=f,current_anchors=pp,image_size=[im.shape[1],im.shape[0]],formal=clean(res['formal']),source_sha256=r['sha256'],result_hash=rh,evidence=side)
     # Complete raw lineage comes from native snapshots, before any offline GT join.
     output.write(json.dumps(trace,allow_nan=False)+'\n')
     if chosen:
      write(OUT/'traces'/f'{mode}_{name}.json',trace);mm=maps(e)
      if mode=='B1':np.savez_compressed(OUT/'maps'/f'{name}.npz',**mm)
      else:
       with np.load(OUT/'maps'/f'{name}.npz') as previous:
        for k in mm:assert np.array_equal(mm[k],previous[k],equal_nan=True),(g,f,k,'B1_B2_MAP_CHANGE')
      with np.load(D/'maps'/f'{name}.npz') as legacy:
       if 'score' in legacy:assert np.array_equal(mm['legacy'],legacy['score']),(g,f,'LEGACY_SCORE_CHANGED')
     summ={k:v for k,v in side.items() if k not in ['candidates','tiles','mode']}
     counts.append(dict(dataset_id=g,frame_id=f,mode=mode,phase=phase,reference_query=i==0,roi=trace['roi'],**summ,denominator=f'all {sum(map(len,groups.values()))} chronological frames'))
     mem=proc.memory_info();total=res['formal']['process_ms'];side_ms=sum(side[k] for k in ['current_ms','reference_ms','dp_ms','candidates_ms','prep_ms','tipmotion_ms','localref_ms','legacydp_ms'])
     perf.append(dict(dataset_id=g,frame_id=f,mode=mode,phase=phase,width=im.shape[1],height=im.shape[0],state='legacy_observed' if res['formal']['confirmed_tip'] else 'legacy_unconfirmed',reference_query=i==0,debug_capture=chosen,api_ms=total,native_api_ms=res['formal']['api_ms'],prep_ms=side['prep_ms'],tipmotion_ms=side['tipmotion_ms'],local_reference_ms=side['localref_ms'],legacy_dp_ms=side['legacydp_ms'],current_ms=side['current_ms'],reference_channel_ms=side['reference_ms'],candidates_ms=side['candidates_ms'],dp_ms=side['dp_ms'],attribution_ms=None,terminal_ms=None,other_ms=total-side_ms if i else None,peak_memory_bytes=getattr(mem,'peak_wset',mem.rss),candidate_count=side['raw_count'],retained_count=side['retained_count']))
     eq.append(dict(dataset_id=g,frame_id=f,mode=mode,phase=phase,exact=exact,hash=rh,denominator='full chronological sequence; all non-timing formal/native/geometry fields'))
     candidate_hashes.append(dict(dataset_id=g,frame_id=f,hash=hashlib.sha256(json.dumps(side['candidates'],sort_keys=True).encode()).hexdigest()))
     if (i+1)%50==0:output.flush();print(tag,g,f,'/',len(seq),flush=True)
   finally:
    if e is not None:e.close()
 save(OUT/f'performance_{tag}.csv',perf);save(OUT/f'counts_{tag}.csv',counts);save(OUT/f'equivalence_{tag}.csv',eq);save(OUT/f'candidate_hashes_{tag}.csv',candidate_hashes)
 write(OUT/f'{tag}_complete.json',dict(status='PASS',equivalence='PASS',frames=len(eq),selected=len(selected) if phase!='perf' else 0,annotation_reads=0,excluded_images_read=0))
 print(tag,'COMPLETE',len(eq),flush=True)
if __name__=='__main__':main()
