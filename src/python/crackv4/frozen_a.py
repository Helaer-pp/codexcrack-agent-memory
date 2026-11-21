from pathlib import Path
import ctypes as C,os,json,time,hashlib,csv,subprocess
import numpy as np,cv2
from .abi import Point,Image,Config,Experiment,Options,Result,image,points,normalized
from .paths import ROOT
W=ROOT;D=ROOT/'data/frozen_a_replay';GROUPS=('group_a','group_c','ct2','group_h')
BASE=ROOT/'baseline/frozen_a/bin/CrackV4.dll';EXPECTED_BASE='c23498fcc660469927f63244b8e98e39b1eb86d542ec9a7b069d61fcf813654b'
_dll_dirs=[os.add_dll_directory(str(ROOT/'third_party/opencv440/bin'))];_base=None

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def save(p,x):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def read(p):
 a=cv2.imdecode(np.fromfile(str(p),np.uint8),0)
 if a is None:raise RuntimeError('image decode failure '+str(p))
 return a
def load(p):return [json.loads(s)for s in Path(p).read_text(encoding='utf-8').splitlines()]
def csvout(p,rows):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8-sig',newline='')as f:
  if not rows:return
  wr=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));wr.writeheader()
  for r in rows:wr.writerow({k:json.dumps(v,ensure_ascii=False)if isinstance(v,(dict,list,tuple))else v for k,v in r.items()})
def arc(p):return float(np.linalg.norm(np.diff(np.asarray(p),axis=0),axis=1).sum())if len(p)>1 else 0.
def stats(v):
 return dict(n=len(v),**dict(zip(['P50','P95','P99','Max'],map(float,np.percentile(v,[50,95,99,100])))),over_budget=sum(t>1000/15 for t in v))if v else dict(n=0)
class V2(C.Structure):
 _fields_=[('struct_size',C.c_uint32),('api_version',C.c_uint32),('frame_index',C.c_uint64),('reference_state',C.c_int),('decision_policy',C.c_int),*[(k,C.c_int)for k in ['has_candidate','root_confirmed','terminal_verified','path_quality_valid','tip_confirmed','complete_length_valid','legacy_tip_confirmed','shadow_tip_confirmed']],('tip_px',Point),('root_px',Point),('tracking_endpoint_px',Point),*[(k,C.c_double)for k in ['observed_length_px','root_to_tip_length_px','root_bridge_length_px','path_support_fraction','tail_support_fraction','tail_median_score','path_width_median_px','tail_width_median_px','detector_ms','api_ms']],*[(k,C.c_int)for k in ['longest_gap_samples','sharp_bend_count','endpoint_temporal_hits','probe_samples']],('terminal_reason',C.c_char*64),('stop_reason',C.c_char*48),('divergence_reason',C.c_char*64)]
def base_library():
 global _base
 if _base:return _base
 assert sha(BASE)==EXPECTED_BASE
 l=C.CDLL(str(BASE));l.CrackV4SetNumThreads(4)
 l.CrackV4CreateExtended.argtypes=[C.POINTER(Image),C.POINTER(Point),C.POINTER(Config),C.POINTER(Experiment),C.POINTER(C.c_void_p),C.POINTER(C.c_double),C.c_char_p,C.c_int]
 l.CrackV4Create.argtypes=[C.POINTER(Image),C.POINTER(Point),C.POINTER(Config),C.POINTER(C.c_void_p),C.POINTER(C.c_double),C.c_char_p,C.c_int]
 l.CrackV4Process.argtypes=[C.c_void_p,C.POINTER(Image),C.POINTER(Point),C.POINTER(Result)];l.CrackV4GetBaseline.argtypes=[C.c_void_p,C.POINTER(Result)];l.CrackV4GetResultV2.argtypes=[C.c_void_p,C.POINTER(V2)];l.CrackV4SetOptionsV2.argtypes=[C.c_void_p,C.POINTER(Options)];l.CrackV4ResetTemporal.argtypes=[C.c_void_p];l.CrackV4Destroy.argtypes=[C.c_void_p];l.CrackV4CopyPath.argtypes=[C.c_void_p,C.c_int,C.POINTER(Point),C.c_int]
 for name in ['CrackV4LastJson','CrackV4LastGeometryJson']:
  getattr(l,name).argtypes=[C.c_void_p];getattr(l,name).restype=C.c_char_p
 l.CrackV4BuildInfo.restype=C.c_char_p;_base=l;return l
class Baseline:
 def __init__(self,ref,pp,mode='clean',refine=True,flags=3572,create_extended=True):
  self.lib=base_library();self.handle=C.c_void_p();self.init_ms=C.c_double();cfg=Config(C.sizeof(Config),{'clean':0,'cracked':1,'auto':2}[mode],1.,int(refine));exp=Experiment(C.sizeof(Experiment),1,flags,0);error=C.create_string_buffer(4096);ii=image(ref)
  args=[C.byref(ii),points(pp),C.byref(cfg)]
  if create_extended:args.append(C.byref(exp))
  args += [C.byref(self.handle),C.byref(self.init_ms),error,len(error)]
  rc=(self.lib.CrackV4CreateExtended if create_extended else self.lib.CrackV4Create)(*args)
  if rc:raise RuntimeError(error.value.decode())
  options=Options(C.sizeof(Options),2,1,1);assert self.lib.CrackV4SetOptionsV2(self.handle,C.byref(options))==0
 def run(self,im,pp,is_reference=False):
  r=Result();r.struct_size=C.sizeof(r);ii=image(im);t=time.perf_counter();rc=self.lib.CrackV4GetBaseline(self.handle,C.byref(r))if is_reference else self.lib.CrackV4Process(self.handle,C.byref(ii),points(pp),C.byref(r));wall=(time.perf_counter()-t)*1000
  if rc:raise RuntimeError('frozen A returned error '+str(rc))
  n=json.loads(self.lib.CrackV4LastJson(self.handle));g=json.loads(self.lib.CrackV4LastGeometryJson(self.handle));v=V2();v.struct_size=C.sizeof(v);v.api_version=2;assert self.lib.CrackV4GetResultV2(self.handle,C.byref(v))==0
  count=self.lib.CrackV4CopyPath(self.handle,0,None,0);p=(Point*max(0,count))();self.lib.CrackV4CopyPath(self.handle,0,p,count);path=[[q.x,q.y]for q in p];valid=bool(v.tip_confirmed and v.complete_length_valid)
  f=dict(confirmed_tip=bool(v.tip_confirmed),valid_full_length=bool(v.complete_length_valid),confirmed=valid,tip=[v.tip_px.x,v.tip_px.y]if v.tip_confirmed else None,length_px=v.root_to_tip_length_px if v.complete_length_valid else None,path=path if valid else[],raw_path=path,path_point_count=len(path),width_px=v.path_width_median_px,process_ms=wall,detector_ms=v.detector_ms,api_ms=v.api_ms,terminal_reason=v.terminal_reason.decode(),reference_state=v.reference_state)
  if valid:assert path and np.linalg.norm(np.array(path[-1])-f['tip'])<=.0072 and abs(arc(path)-f['length_px'])<=.0051
  return dict(formal=f,native=n,geometry=g)
 def close(self):
  if self.handle:self.lib.CrackV4Destroy(self.handle);self.handle=None
 def __del__(self):self.close()
