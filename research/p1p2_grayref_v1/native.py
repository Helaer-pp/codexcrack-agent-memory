from common import *
import ctypes as C,time
import numpy as np
from crackv4.abi import Image,Point,image,points
class Native:
 def __init__(self):
  self.directory=os.add_dll_directory(str(BUILD/'Release'));self.lib=C.CDLL(str(BUILD/'Release/P1P2GrayRefV1.dll'));l=self.lib
  l.GrayRefCreate.argtypes=[C.POINTER(Image),C.POINTER(Point)];l.GrayRefCreate.restype=C.c_void_p
  l.GrayRefProcess.argtypes=[C.c_void_p,C.POINTER(Image),C.POINTER(Point)];l.GrayRefProcess.restype=C.c_int
  l.GrayRefRead.argtypes=[C.c_void_p];l.GrayRefRead.restype=C.c_char_p
  l.GrayRefArray.argtypes=[C.c_void_p,C.c_int,C.POINTER(C.c_int),C.POINTER(C.c_int)];l.GrayRefArray.restype=C.POINTER(C.c_float)
  l.GrayRefDestroy.argtypes=[C.c_void_p];l.GrayRefDestroy.restype=None
 def create(self,im,pp):
  h=self.lib.GrayRefCreate(C.byref(image(im)),points(pp));assert h;return h
 def process(self,h,im,pp=None):
  start=time.perf_counter();rc=self.lib.GrayRefProcess(h,C.byref(image(im)),points(pp) if pp is not None else None);wall=(time.perf_counter()-start)*1000;assert rc==0,rc
  start=time.perf_counter();r=json.loads(self.lib.GrayRefRead(h));r['debug_export_ms']=(time.perf_counter()-start)*1000;r['call_wall_ms']=wall;return r
 def arrays(self,h):
  result={}
  for i,name in enumerate(['reference_aligned','csm','rsm','valley','newdark','flank_low','valid_material','score']):
   w=C.c_int();height=C.c_int();p=self.lib.GrayRefArray(h,i,C.byref(w),C.byref(height))
   if p:result[name]=np.ctypeslib.as_array(p,shape=(height.value,w.value)).copy()
  return result
 def close(self,h):self.lib.GrayRefDestroy(h)
