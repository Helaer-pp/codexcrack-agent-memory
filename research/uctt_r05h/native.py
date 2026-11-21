from common import *
import ctypes as C,time
from crackv4.abi import Image,Point,image,points
class Native:
 def __init__(self):
  self.directory=os.add_dll_directory(str(BUILD/'Release'));self.lib=C.CDLL(str(BUILD/'Release/R05H.dll'));l=self.lib
  l.R05HCreate.argtypes=[C.POINTER(Image),C.POINTER(Point)];l.R05HCreate.restype=C.c_void_p
  l.R05HProcess.argtypes=[C.c_void_p,C.POINTER(Image),C.POINTER(Point),C.c_int];l.R05HProcess.restype=C.c_int
  l.R05HRead.argtypes=[C.c_void_p];l.R05HRead.restype=C.c_char_p
  l.R05HDestroy.argtypes=[C.c_void_p];l.R05HDestroy.restype=None
 def create(self,im,pp):
  h=self.lib.R05HCreate(C.byref(image(im)),points(pp));assert h;return h
 def process(self,h,im,pp,variant=0):
  start=time.perf_counter();rc=self.lib.R05HProcess(h,C.byref(image(im)),points(pp),variant);wall=(time.perf_counter()-start)*1000;assert rc==0,rc
  start=time.perf_counter();r=json.loads(self.lib.R05HRead(h));r['debug_export_ms']=(time.perf_counter()-start)*1000;r['call_wall_ms']=wall;return r
 def close(self,h):self.lib.R05HDestroy(h)
