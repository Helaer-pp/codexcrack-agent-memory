from v2common import *
from algorithm import FIELDS
from crackv4.abi import Image,Point,image,points
import ctypes as C,numpy as np,time
BUILD=OUT/'cpp_build/Release'
class Native:
 def __init__(self):
  self.directory=os.add_dll_directory(str(BUILD));self.lib=C.CDLL(str(BUILD/'GrayRefV2.dll'));l=self.lib;l.GrayRefV2Create.argtypes=[C.POINTER(Image),C.POINTER(Point)];l.GrayRefV2Create.restype=C.c_void_p;l.GrayRefV2Process.argtypes=[C.c_void_p,C.POINTER(Image),C.POINTER(Point)];l.GrayRefV2Process.restype=C.c_int;l.GrayRefV2Read.argtypes=[C.c_void_p];l.GrayRefV2Read.restype=C.c_char_p;l.GrayRefV2Destroy.argtypes=[C.c_void_p];l.GrayRefV2Array.argtypes=[C.c_void_p,C.c_int,C.POINTER(C.c_int),C.POINTER(C.c_int)];l.GrayRefV2Array.restype=C.POINTER(C.c_float);assert l.GrayRefV2NumericSelfTest()==0
 def run(self,R,Ccur,rp,cp):
  tick=time.perf_counter();h=self.lib.GrayRefV2Create(C.byref(image(R)),points(rp));assert h
  try:
   rc=self.lib.GrayRefV2Process(h,C.byref(image(Ccur)),points(cp));assert rc==0;data=json.loads(self.lib.GrayRefV2Read(h));arrays={}
   if data['status']=='OK':
    for i,key in enumerate(FIELDS):
     w=C.c_int();ht=C.c_int();p=self.lib.GrayRefV2Array(h,i,C.byref(w),C.byref(ht));assert p;arrays[key]=np.ctypeslib.as_array(p,shape=(w.value*ht.value,)).reshape(ht.value,w.value).copy()
  finally:self.lib.GrayRefV2Destroy(h)
  data['api_wall_ms']=(time.perf_counter()-tick)*1000;return data,arrays
