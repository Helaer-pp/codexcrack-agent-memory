from common import *
import ctypes as C,os,numpy as np,statistics
def main():
 directory=os.add_dll_directory(str(ROOT/'third_party/opencv440/bin'));lib=C.CDLL(str(BUILD/'Release/B2.dll'))
 lib.CrackV4SetNumThreads.argtypes=[C.c_int];lib.CrackV4SetNumThreads(4)
 lib.R05ECF4Cost.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_int,C.c_int];lib.R05ECF4Cost.restype=C.c_double
 result=[]
 for r in filter_rows(rows(OUT/'selected_frames.csv'),'development'):
  g=r['dataset_id'];f=int(r['frame_id']);require(g,'development');name=f'{g}__{f:06d}';t=read(D/'traces'/f'{name}.json')
  if t['reference'] or not t['registration_valid']:continue
  with np.load(D/'maps'/f'{name}.npz') as m:s=np.ascontiguousarray(m['score']);im=np.ascontiguousarray(m['current']);why=np.ascontiguousarray(m['reason'])
  times=[lib.R05ECF4Cost(s.ctypes.data,im.ctypes.data,why.ctypes.data,*s.shape) for _ in range(6)]
  result.append(dict(dataset_id=g,frame_id=f,mode='CF4_OFFLINE_COST_CONTROL',median_ms=statistics.median(times[1:]),repeats=5,warmup=1,counts_source='R05D exact CF4 evidence intervention',scope='score clone + reason2 replacement + unchanged distalLine; no IO/debug exports/history',not_end_to_end=True))
 save(OUT/'performance_CF4_control.csv',result);print('CF4 COST',len(result),flush=True)
if __name__=='__main__':main()
