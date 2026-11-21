"""Image-only complete causal replay. No annotation ZIP imports or reads."""
from common import *
import cv2,numpy as np,collections
from crackv4 import frozen_a as api
def load(path):
 api.BASE=path;api.EXPECTED_BASE=sha(path);api._base=None
 return api.base_library()
def make(lib,im,pp,mode):
 api._base=lib
 return api.Baseline(im,pp,mode=mode,flags=3572,refine=True)
def clean(v):
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if not k.endswith('_ms')}
 if isinstance(v,list):return [clean(x) for x in v]
 return v
def digest(v):return hashlib.sha256(json.dumps(clean(v),sort_keys=True,allow_nan=False).encode()).hexdigest()
def main():
 cv2.setNumThreads(1)
 assert not (OUT/'B0_complete.json').exists()
 a=load(ROOT/'output/build/src/cpp/a/Release/CrackV4.dll');b=load(BUILD/'Release/B0.dll')
 old={(r['dataset_id'],r['frame_id']):r for r in map(json.loads,(D/'dev_frames.jsonl').read_text().splitlines())}
 modes={r['id']:r['mode'] for r in read(ROOT/'config/datasets.json')['groups']};modes['ct3']='auto'
 groups=collections.defaultdict(list)
 for r in filter_rows(rows(OUT/'input_inventory_allowed.csv'),'development'):groups[r['dataset_id']].append(r)
 write(OUT/'B0_replay_lock.json',dict(libraries={str(p):sha(p) for p in [ROOT/'output/build/src/cpp/a/Release/CrackV4.dll',BUILD/'Release/B0.dll']},annotations_opened=0,frames=1565))
 eq=[];perf=[]
 with (OUT/'B0_frames.jsonl').open('w',encoding='utf8') as out:
  for g,seq in groups.items():
   ea=eb=None
   try:
    for i,r in enumerate(seq):
     require(g,'development');assert int(r['frame_order'])==i
     raw=Path(r['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256']
     im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=json.loads(r['points']);f=int(r['frame_id'])
     if ea is None:ea=make(a,im,pp,modes[g]);eb=make(b,im,pp,modes[g])
     ra=ea.run(im,pp,is_reference=i==0);rb=eb.run(im,pp,is_reference=i==0)
     ah,bh=digest(ra),digest(rb);match=ah==bh==old[g,f]['result_hash']
     eq.append(dict(dataset_id=g,frame_id=f,mode='B0',a_hash=ah,b_hash=bh,r05d_hash=old[g,f]['result_hash'],exact=match,reference_query=i==0,denominator='all 1565 development frames including 4 cached reference queries'))
     assert match,(g,f,'BASELINE_MISMATCH')
     out.write(json.dumps(dict(dataset_id=g,frame_id=f,result_hash=ah,formal=clean(ra['formal']),geometry=ra['geometry']))+'\n')
     for mode,res in [('A',ra),('B0',rb)]:perf.append(dict(dataset_id=g,frame_id=f,mode=mode,width=im.shape[1],height=im.shape[0],reference_query=i==0,api_ms=res['formal']['process_ms'],native_api_ms=res['formal']['api_ms'],detector_ms=res['formal']['detector_ms']))
     if (i+1)%50==0:out.flush();print('B0',g,f,'/',len(seq),flush=True)
   finally:
    for e in [ea,eb]:
     if e is not None:e.close()
 save(OUT/'baseline_equivalence.csv',eq);save(OUT/'performance_B0.csv',perf)
 write(OUT/'B0_complete.json',dict(status='PASS',frames=len(eq),annotations_opened=0,excluded_images_opened=0,non_timing_exact=True))
 print('B0 PASS',len(eq),flush=True)
if __name__=='__main__':main()
