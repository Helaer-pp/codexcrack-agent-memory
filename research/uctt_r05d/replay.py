"""Chronological image-only native replay. Never opens any human annotations."""
import argparse,ctypes as C,time,collections
import numpy as np,cv2
from common import *
from crackv4 import frozen_a as api
from crackv4.abi import image

def loadlib(path):
 api.BASE=path;api.EXPECTED_BASE=sha(path);api._base=None
 lib=api.base_library()
 if hasattr(lib,'R05DRead'):
  lib.R05DRead.argtypes=[C.c_void_p];lib.R05DRead.restype=C.c_char_p
  lib.R05DCapture.argtypes=[C.c_int]
  lib.R05DMap.argtypes=[C.c_void_p,C.c_int,*([C.POINTER(C.c_int)]*4)];lib.R05DMap.restype=C.c_void_p
 if hasattr(lib,'R05DOffline'):
  lib.R05DOffline.argtypes=[C.c_void_p,C.POINTER(api.Image),C.c_int]
  lib.R05DOfflineRead.argtypes=[C.c_void_p];lib.R05DOfflineRead.restype=C.c_char_p
 return lib
def make(lib,im,pp,mode):
 api._base=lib
 return api.Baseline(im,pp,mode=mode,flags=3572,refine=True)
def clean(v):
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if not k.endswith('_ms')}
 if isinstance(v,list):return [clean(x) for x in v]
 return v
def digest(r):return hashlib.sha256(json.dumps(clean(r),sort_keys=True,allow_nan=False).encode()).hexdigest()
def maps(engine):
 result={}
 for i,name in enumerate(['current','score','registered','prior','reason','valid','gains','back']):
  h,w,typ,stride=[C.c_int() for _ in range(4)];p=engine.lib.R05DMap(engine.handle,i,C.byref(h),C.byref(w),C.byref(typ),C.byref(stride))
  if not p or not h.value:continue
  dtype={0:np.uint8,1:np.int8,5:np.float32}[typ.value];raw=C.string_at(p,h.value*stride.value)
  result[name]=np.ndarray((h.value,w.value),dtype=dtype,buffer=raw,strides=(stride.value,np.dtype(dtype).itemsize)).copy()
 return result
def main():
 parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['dev','val','cf']);args=parser.parse_args();phase=args.phase
 cv2.setNumThreads(1)
 if phase=='val':assert (OUT/'diagnosis_frozen_before_validation.json').exists()
 if phase=='cf':assert read(OUT/'dev_complete.json')['equivalence']=='PASS' and (OUT/'reachability_dev.csv').exists()
 subset=['group_a','ct2','group_h','ct3'] if phase!='val' else ['group_c','three_point_bend']
 inventory=[r for r in rows(OUT/'input_inventory_allowed.csv') if r['dataset_id'] in subset]
 selected={(r['dataset_id'],int(r['frame_id'])) for r in rows(OUT/'selected_frames.csv') if r['dataset_id'] in subset}
 groups=collections.defaultdict(list)
 for r in inventory:require(r['dataset_id'],'development' if phase=='cf' else 'validation');groups[r['dataset_id']].append(r)
 configs={g['id']:g['mode'] for g in read(ROOT/'config/datasets.json')['groups']};configs['ct3']='auto'
 frozen=ROOT/'output/build/src/cpp/a/Release/CrackV4.dll'
 a=loadlib(frozen);b=loadlib(BUILD/'Release'/('D1_OFFLINE_ONLY.dll' if phase=='cf' else 'D0_TRACE_ONLY.dll'))
 same=loadlib(BUILD/'Release/A0_SAME_SOURCE.dll')
 assert not (OUT/f'{phase}_complete.json').exists()
 write(OUT/f'{phase}_replay_lock.json',dict(libraries={str(p):sha(p) for p in [frozen,BUILD/'Release/D0_TRACE_ONLY.dll',BUILD/'Release/D1_OFFLINE_ONLY.dll',BUILD/'Release/A0_SAME_SOURCE.dll']},source={str(p):sha(p) for p in (ROOT/'research/uctt_r05d').glob('*') if p.is_file()},groups=subset,annotation_reads=0))
 previous={(r['dataset_id'],int(r['frame_id'])):r for r in rows(R05/'production_selected_predictions.csv')}
 baseline={}
 if phase=='cf':baseline={(r['dataset_id'],r['frame_id']):r for r in map(json.loads,(OUT/'dev_frames.jsonl').read_text().splitlines())}
 eq=[];times=[];count=0
 with (OUT/f'{phase}_frames.jsonl').open('w',encoding='utf8') as output:
  for g,seq in groups.items():
   ea=eb=es=None
   try:
    for i,r in enumerate(seq):
     assert int(r['frame_order'])==i;f=int(r['frame_id']);assert f==i+1
     key=(g,f);chosen=key in selected;b.R05DCapture(int(chosen))
     start=time.perf_counter();raw=Path(r['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);io=(time.perf_counter()-start)*1000;pp=json.loads(r['points'])
     if eb is None:
      eb=make(b,im,pp,configs[g])
      if phase!='cf':ea=make(a,im,pp,configs[g]);es=make(same,im,pp,configs[g])
     rb=eb.run(im,pp,is_reference=i==0);dh=digest(rb)
     if phase!='cf':
      ra=ea.run(im,pp,is_reference=i==0);ah=digest(ra);assert ah==dh,(g,f,'A0_D0_MISMATCH')
      if i<3:rs=es.run(im,pp,is_reference=i==0);assert digest(rs)==ah,(g,f,'REBUILD_SOURCE_MISMATCH')
      if i==2:es.close();es=None
      if key in previous:
       old=previous[key];tip=ra['formal']['tip'];assert (old['observed']=='True')==ra['formal']['confirmed_tip']
       if tip is not None:assert tip==[float(old['tip_x']),float(old['tip_y'])],(g,f,'R05_REPRODUCTION_MISMATCH')
      eq.append(dict(dataset_id=g,frame_id=f,phase=phase,a0_sha=ah,d0_sha=dh,non_timing_exact=True,scope='native+geometry+formal+float64_path',reference_query=i==0))
      for name,res in [('A0_FROZEN',ra),('D0_TRACE_ONLY',rb)]:times.append(dict(dataset_id=g,frame_id=f,variant=name,reference_query=i==0,api_wall_ms=res['formal']['process_ms'],native_detector_ms=res['formal']['detector_ms'],native_api_ms=res['formal']['api_ms'],io_ms=io))
     else:assert dh==baseline[key]['result_hash'],(g,f,'D1_BASELINE_CHANGED')
     trace=json.loads(b.R05DRead(eb.handle));name=f'{g}__{f:06d}';trace.update(dataset_id=g,frame_id=f,current_anchors=pp,image_size=[im.shape[1],im.shape[0]],source_sha256=r['sha256'],formal=clean(rb['formal']),geometry=rb['geometry'])
     record=dict(dataset_id=g,frame_id=f,result_hash=dh,roi=trace['roi'],center=trace['center'],tip_transform=trace['tip_transform'],main_transform=trace['main_transform'],motion_branch=trace['motion_branch'],registration_valid=trace['registration_valid'],observed=rb['formal']['confirmed_tip'],tip=rb['formal']['tip'],terminal_reason=rb['formal']['terminal_reason'],selected=chosen)
     output.write(json.dumps(record,allow_nan=False)+'\n')
     if chosen and phase!='cf':write(OUT/'traces'/f'{name}.json',trace);np.savez_compressed(OUT/'maps'/f'{name}.npz',**maps(eb))
     if chosen and phase=='cf' and i>0:
      for variant in [1,2,3]:
       ii=image(im);assert b.R05DOffline(eb.handle,C.byref(ii),variant)==0
       cf=json.loads(b.R05DOfflineRead(eb.handle));cf.update(dataset_id=g,frame_id=f,variant=variant,source_sha256=r['sha256'],offline_only=True)
       write(OUT/'traces'/f'{name}__CF{variant}.json',cf);np.savez_compressed(OUT/'maps'/f'{name}__CF{variant}.npz',**maps(eb))
       # The existing detector result and history must stay unchanged.
       assert json.loads(b.CrackV4LastJson(eb.handle))==rb['native']
     count+=1
     if (i+1)%50==0:output.flush();print(phase,g,f,'/',len(seq),flush=True)
   finally:
    for e in [ea,eb,es]:
     if e is not None:e.close()
   print('FINISHED',phase,g,len(seq),flush=True)
 if eq:save(OUT/f'equivalence_{phase}.csv',eq);save(OUT/f'timings_{phase}.csv',times)
 write(OUT/f'{phase}_complete.json',dict(equivalence='PASS',frames=count,selected=len(selected),annotation_reads=0,excluded_images_read=0))
 print('COMPLETE',phase,count,flush=True)
if __name__=='__main__':main()
