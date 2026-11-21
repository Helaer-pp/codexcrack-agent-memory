"""Predeclared one-factor x8 capacity intervention; image-only stateless probe."""
from common import *
import replay,ctypes as C,cv2,numpy as np

def main():
 assert (OUT/'B0_complete.json').exists()
 dest=OUT/'stateless_budget_x8';dest.mkdir(exist_ok=False)
 replay.BUILD=ROOT/'output/build/uctt_r05f_probe';n=replay.Native()
 n.lib.R05FDiagnosticBudget.argtypes=[C.c_void_p];n.lib.R05FDiagnosticBudget.restype=C.c_int
 write(dest/'lock.json',dict(kind='STATELESS_PROBE_NOT_ONLINE_ABLATION',intervention='8x segment/candidate caps only; no threshold, no reference, no GT runtime input',files={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'research/uctt_r05f/current.hpp',ROOT/'research/uctt_r05f/budget_probe.cpp',replay.BUILD/'Release/R05F.dll',Path(__file__)]},selection='all80 existing DEVELOPMENT selection; no sentinel-only selection'))
 metrics=[]
 for r in filter_rows(rows(OUT/'selected_frames.csv'),'development'):
  g=r['dataset_id'];f=int(r['frame_id']);require(g,'development');raw=Path(r['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256']
  im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=json.loads(r['points']);h=n.create(im,pp)
  try:
   assert n.lib.R05FDiagnosticBudget(h)==0
   t=n.process(h,im,pp,True);t.update(dataset_id=g,frame_id=f,kind='stateless_probe',source_sha256=r['sha256']);write(dest/f'{g}_{f}.json',t)
  finally:n.close(h)
  orig=read(OUT/'traces'/f'B0_{g}_{f}.json');metrics.append(dict(dataset_id=g,frame_id=f,kind='stateless_probe',B0_segments=len(orig['segments']),probe_segments=len(t['segments']),B0_candidates=len(orig['candidates']),probe_candidates=len(t['candidates']),B0_incomplete=orig['search_incomplete'],probe_incomplete=t['search_incomplete'],B0_ms=orig['api_ms'],probe_ms=t['api_ms']))
  print('S1 x8 diagnostic',g,f,len(t['segments']),flush=True)
 save(dest/'capacity_intervention.csv',metrics)
 write(dest/'complete.json',dict(frames=len(metrics),annotations_opened=0,validation_images_opened=0,excluded_images_opened=0,not_causal_replay=True))
if __name__=='__main__':main()
