"""Exact stateless localReference audit from original pixels and traced geometry."""
import argparse,ctypes as C
import numpy as np,cv2
from common import *
from crackv4.abi import Image,image
def main():
 parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['dev','val']);phase=parser.parse_args().phase
 cv2.setNumThreads(4);dll_dir=os_dll_dir=__import__('os').add_dll_directory(str(ROOT/'third_party/opencv440/bin'))
 lib=C.CDLL(str(BUILD/'Release/D2_LOCAL_AUDIT.dll'));lib.R05DAuditLocal.argtypes=[C.POINTER(Image),C.POINTER(Image),*([C.c_int]*7)];lib.R05DAuditLocal.restype=C.c_char_p;lib.R05DHashBytes.argtypes=[C.c_void_p,C.c_size_t];lib.R05DHashBytes.restype=C.c_uint64
 selected=[r for r in rows(OUT/'selected_frames.csv') if (role(r['dataset_id'])=='DEVELOPMENT')==(phase=='dev')];refs={};records=[]
 for r in selected:
  g=r['dataset_id'];require(g,'validation');f=int(r['frame_id']);name=f'{g}__{f:06d}';t=read(OUT/'traces'/f'{name}.json')
  if t['reference'] or not t['registration_valid']:continue
  if g not in refs:
   first=next(v for v in rows(OUT/'input_inventory_allowed.csv') if v['dataset_id']==g and v['frame_id']=='1');b=Path(first['source_image']).read_bytes();assert hashlib.sha256(b).hexdigest()==first['sha256'];refs[g]=cv2.imdecode(np.frombuffer(b,np.uint8),0)
  raw=Path(r['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['source_sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);ref=refs[g];a=image(ref);b=image(im)
  # C++ rnd is nearbyint, matching NumPy bankers rounding.
  delta=np.rint(np.array(t['center'])-t['origin']).astype(int)
  result=json.loads(lib.R05DAuditLocal(C.byref(a),C.byref(b),*t['roi'],*map(int,delta),t['turn']))
  with np.load(OUT/'maps'/f'{name}.npz') as archive:
   registered=np.ascontiguousarray(archive['registered']);observed_hash=lib.R05DHashBytes(registered.ctypes.data,registered.nbytes)
   assert str(observed_hash)==result['registered_fnv64'],(g,f,'LOCAL_REFERENCE_REPLAY_MISMATCH')
  result.update(dataset_id=g,frame_id=f,registered_bitwise_hash_matches_D0=True,source_sha256=r['source_sha256'],roi=t['roi'],drift=delta.tolist(),source='exact production localReference in stateless D2; baseline_mask omitted ONLY because it does not affect matching/aligned reference')
  write(OUT/'traces'/f'{name}__local.json',result)
  records.append(dict(dataset_id=g,frame_id=f,local_reference_bitwise_equal=True,tile_count=len(result['tiles']),accepted=sum(v['stage']=='accepted' for v in result['tiles']),source=f'traces/{name}__local.json'))
 save(OUT/f'local_reference_{phase}.csv',records);print('LOCAL AUDIT',phase,len(records),'exact registered-image hashes match',flush=True)
if __name__=='__main__':main()
