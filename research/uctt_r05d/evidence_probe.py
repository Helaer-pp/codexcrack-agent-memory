"""Development-only single-variable missing-reference evidence intervention.
No human labels are read. Both control and intervention use exact native DP.
"""
import ctypes as C,os
import numpy as np
from common import *
def main():
 assert read(OUT/'dev_complete.json')['equivalence']=='PASS'
 directory=os.add_dll_directory(str(ROOT/'third_party/opencv440/bin'));lib=C.CDLL(str(BUILD/'Release/D2_LOCAL_AUDIT.dll'))
 lib.R05DProbeEvidence.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_int,C.c_int,C.c_int];lib.R05DProbeEvidence.restype=C.c_char_p
 count=0
 for r in rows(OUT/'selected_frames.csv'):
  if role(r['dataset_id'])!='DEVELOPMENT':continue
  require(r['dataset_id'],'development');name=f"{r['dataset_id']}__{int(r['frame_id']):06d}";t=read(OUT/'traces'/f'{name}.json')
  if t['reference'] or not t['registration_valid']:continue
  with np.load(OUT/'maps'/f'{name}.npz') as a:score=np.ascontiguousarray(a['score']);current=np.ascontiguousarray(a['current']);reason=np.ascontiguousarray(a['reason'])
  control=json.loads(lib.R05DProbeEvidence(score.ctypes.data,current.ctypes.data,reason.ctypes.data,*score.shape,0));assert control['selected_local']==t['selected_local'],(name,'DP_CONTROL_MISMATCH')
  intervention=json.loads(lib.R05DProbeEvidence(score.ctypes.data,current.ctypes.data,reason.ctypes.data,*score.shape,4));intervention.update(dataset_id=r['dataset_id'],frame_id=int(r['frame_id']),variant=4,source_sha256=r['source_sha256'],input_map_sha256=sha(OUT/'maps'/f'{name}.npz'),control_dp_exact=True,offline_only=True,unique_variable='Reference-eroded gate unavailable (reason2) pixels receive current valley score; all DP thresholds/ROI/registration fixed')
  write(OUT/'traces'/f'{name}__CF4.json',intervention);count+=1
 write(OUT/'evidence_probe_complete.json',dict(controls_exact=True,cases=count,annotation_reads=0,validation_cases=0));print('EVIDENCE PROBE',count,'controls exact')
if __name__=='__main__':main()
