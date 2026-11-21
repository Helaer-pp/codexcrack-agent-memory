"""Image-only causal research runner. Annotations are never imported here."""
from common import *
import ctypes as C,os,time,collections,gzip
import cv2,numpy as np
from crackv4.abi import Image,Point,image,points

class Native:
 def __init__(self):
  self.directory=os.add_dll_directory(str(BUILD/'Release'))
  self.lib=C.CDLL(str(BUILD/'Release/R05F.dll'));l=self.lib
  l.R05FCreate.argtypes=[C.POINTER(Image),C.POINTER(Point),C.c_int];l.R05FCreate.restype=C.c_void_p
  l.R05FProcess.argtypes=[C.c_void_p,C.POINTER(Image),C.POINTER(Point)];l.R05FProcess.restype=C.c_int
  l.R05FCapture.argtypes=[C.c_void_p,C.c_int];l.R05FCapture.restype=None
  l.R05FRead.argtypes=[C.c_void_p];l.R05FRead.restype=C.c_char_p
  l.R05FDestroy.argtypes=[C.c_void_p];l.R05FDestroy.restype=None
 def create(self,im,pp,mode=0):
  h=self.lib.R05FCreate(C.byref(image(im)),points(pp),mode)
  assert h,'invalid initialization';return h
 def process(self,h,im,pp,capture=False):
  self.lib.R05FCapture(h,int(capture));start=time.perf_counter()
  rc=self.lib.R05FProcess(h,C.byref(image(im)),points(pp));elapsed=(time.perf_counter()-start)*1000
  assert rc==0,rc
  start=time.perf_counter();r=json.loads(self.lib.R05FRead(h));r['call_wall_ms']=elapsed;r['debug_export_ms']=(time.perf_counter()-start)*1000
  return r
 def close(self,h):self.lib.R05FDestroy(h)

def lock(name):
 files=sorted((ROOT/'research/uctt_r05f').glob('*.*'))+[BUILD/'Release/R05F.dll',OUT/'selected_frames.csv',OUT/'input_inventory_allowed.csv',R05/'human_annotations_six_groups_snapshot.zip',POLICY_PATH]
 write(OUT/(name+'_lock.json'),dict(files={str(p.relative_to(ROOT)):sha(p) for p in files},data_role='DEVELOPMENT',labels='offline comparison only; no tuning',parameters='Config in current.hpp; shared across all groups',created=time.time()))

def main():
 assert read(OUT/'S0_complete.json')['status']=='PASS'
 cv2.setNumThreads(1);n=Native();tag='B0';path=OUT/'traces'/f'{tag}_frames.jsonl.gz';assert not path.exists()
 lock(tag)
 selections={(r['dataset_id'],int(r['frame_id'])) for r in filter_rows(rows(OUT/'selected_frames.csv'),'development')}
 groups=collections.defaultdict(list)
 for r in filter_rows(rows(OUT/'input_inventory_allowed.csv'),'development'):groups[r['dataset_id']].append(r)
 metrics=[]
 with gzip.open(path,'wt',encoding='utf8',compresslevel=1) as stream:
  for g,seq in groups.items():
   h=None
   try:
    for i,r in enumerate(seq):
     require(g,'development');assert int(r['frame_order'])==i
     start=time.perf_counter();raw=Path(r['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256']
     im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=json.loads(r['points']);io=(time.perf_counter()-start)*1000;f=int(r['frame_id'])
     if h is None:h=n.create(im,pp)
     out=n.process(h,im,pp,(g,f) in selections);out.update(dataset_id=g,frame_id=f,variant=tag,io_decode_hash_ms=io,source_sha256=r['sha256'])
     stream.write(json.dumps(out,allow_nan=False,separators=(',',':'))+'\n')
     metrics.append({k:v for k,v in out.items() if k not in ['windows','segments','candidates']})
     if (g,f) in selections:write(OUT/'traces'/f'{tag}_{g}_{f}.json',out)
     if (i+1)%50==0:stream.flush();print(tag,g,f,'/',len(seq),'ms',round(out['api_ms'],2),'segments',len(out['segments']),'candidates',len(out['candidates']),flush=True)
   finally:
    if h:n.close(h)
 save(OUT/'experiments'/f'{tag}_frame_metrics.csv',metrics)
 write(OUT/f'{tag}_complete.json',dict(frames=len(metrics),annotations_opened=0,excluded_images_opened=0,validation_images_opened=0,full_causal_prefix=True))
 print(tag,'COMPLETE',len(metrics),flush=True)
if __name__=='__main__':main()
