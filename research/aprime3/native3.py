from common3 import *
def engine3(ref,rp,mode='auto'):
 old=api.BASE,api.EXPECTED_BASE,api._base
 try:
  api.BASE=ROOT/'output/build/Release/CrackV4AP3Observer.dll';api.EXPECTED_BASE=sha(api.BASE);api._base=None
  e=api.Baseline(ref,rp,mode=mode,flags=3572)
  for name in ['AP3CopySeed','AP2CopyStops']:
   fn=getattr(e.lib,name);fn.argtypes=[api.C.c_void_p,api.C.POINTER(api.C.c_double),api.C.c_int];fn.restype=api.C.c_int
  return e
 finally:api.BASE,api.EXPECTED_BASE,api._base=old
def seed(e):
 a=np.zeros(9,np.float64);assert e.lib.AP3CopySeed(e.handle,a.ctypes.data_as(api.C.POINTER(api.C.c_double)),9)==9
 return dict(zip(['stage','support_count','minimum','gain','ridge_size','contiguous_span','startup_fraction','startup_peak','score_threshold'],a.tolist()))

