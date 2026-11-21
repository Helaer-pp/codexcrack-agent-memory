from common import *
import ctypes as C,time
from crackv4.abi import Image,Point,image,points
class Native:
 def __init__(self):
  self.directory=os.add_dll_directory(str(BUILD/'Release'));self.lib=C.CDLL(str(BUILD/'Release/R05G.dll'));l=self.lib
  l.R05GCreate.argtypes=[C.POINTER(Image)];l.R05GCreate.restype=C.c_void_p
  l.R05GProcessAuto.argtypes=[C.c_void_p,C.POINTER(Image),C.POINTER(Point),C.c_int,C.c_int];l.R05GProcessAuto.restype=C.c_int
  l.R05GProcessDiagnostic.argtypes=[C.c_void_p,C.POINTER(Image),C.POINTER(Point),C.POINTER(C.c_double),C.c_int,C.c_int,C.c_int];l.R05GProcessDiagnostic.restype=C.c_int
  l.R05GRead.argtypes=[C.c_void_p];l.R05GRead.restype=C.c_char_p
  l.R05GDestroy.argtypes=[C.c_void_p];l.R05GDestroy.restype=None
 def create(self,im):
  h=self.lib.R05GCreate(C.byref(image(im)));assert h;return h
 def process(self,h,im,pp,variant=0,detail=1):
  start=time.perf_counter();rc=self.lib.R05GProcessAuto(h,C.byref(image(im)),points(pp),variant,detail);wall=(time.perf_counter()-start)*1000;assert rc==0,rc
  return self.result(h,wall)
 def diagnostic(self,h,im,pp,seed,variant=0,detail=2):
  values=(C.c_double*len(seed))(*seed);start=time.perf_counter();rc=self.lib.R05GProcessDiagnostic(h,C.byref(image(im)),points(pp),values,len(seed)//4,variant,detail);wall=(time.perf_counter()-start)*1000;assert rc==0,rc
  return self.result(h,wall)
 def result(self,h,wall):
  start=time.perf_counter();r=json.loads(self.lib.R05GRead(h));r['export_ms']=(time.perf_counter()-start)*1000;r['call_wall_ms']=wall;return r
 def close(self,h):self.lib.R05GDestroy(h)
