from native import *
import cv2,numpy as np,shutil
def main():
 n=Native();cv2.setNumThreads(1);seeds={(r['dataset_id'],r['frame_id']):r for r in read(OUT/'seeds/diagnostic_seeds.json')};rr=[]
 assert sha(OUT/'seeds/diagnostic_seeds.json')==read(OUT/'seeds/provenance_lock.json')['seed_sha256']
 write(OUT/'G1_seeded_pre_run_lock.json',dict(source={p.name:sha(p) for p in [ROOT/'research/uctt_r05g/tracker.hpp',ROOT/'research/uctt_r05g/runtime.cpp',BUILD/'Release/R05G.dll']},change='root seed no longer masquerades as a visible observation; raw candidates and physical scan polygons recorded; no threshold changes',labels_opened=0))
 for row in rows(OUT/'selection.csv'):
  g=row['dataset_id'];f=int(row['frame_id']);require(g,'development');raw=Path(row['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=json.loads(row['points']);h=n.create(im)
  try:t=n.diagnostic(h,im,pp,seeds[g,f]['seed'],0,2)
  finally:n.close(h)
  t.update(dataset_id=g,frame_id=f,variant='G1_SEEDED');write(OUT/'traces'/f'G1_SEEDED_{g}_{f}.json',t)
  vis=[p for p in t['selected_path'] if p['visible']];travel=sum(float(np.linalg.norm(np.array(b['xy'])-a['xy'])) for a,b in zip(vis[:-1],vis[1:]));dependent=0
  for s in t['scans']:
   if s['phase']=='tracking':
    parent=t['nodes'][s['parent']];delta=np.array(s['predicted_point'])-parent['xy'];tan=np.array(parent['tangent']);assert np.linalg.norm(delta-np.dot(delta,tan)*tan)<1e-6 and np.dot(delta,tan)>0;dependent+=1
  rr.append(dict(dataset_id=g,frame_id=f,seed_quality=seeds[g,f]['quality'],visible_centers=len(vis),visible_travel=travel,dependent_scanlines=dependent,reason=t['reason'],ms=t['time_total_native_ms']))
 save(OUT/'experiments/G1_seeded_mechanism.csv',rr)
 passed=all(any(r['dataset_id']==g and r['visible_centers']>=20 and r['visible_travel']>=30 for r in rr) for g in DEV)
 prior=read(OUT/'G1_auto_initial_gate.json') if (OUT/'G1_auto_initial_gate.json').exists() else read(OUT/'G1_gate.json')
 if not (OUT/'G1_auto_initial_gate.json').exists():write(OUT/'G1_auto_initial_gate.json',prior)
 write(OUT/'G1_gate.json',dict(status='PASS' if passed else 'FAIL',scope='dependent current-image tracking only, NOT automatic initialization, main-crack identity or endpoint accuracy',auto_initial=prior['status'],auto_ct3_seed_missing=20,seeded_supported=sum(r['visible_centers']>=20 and r['visible_travel']>=30 for r in rr),labels_opened=0,root_seed_is_current_observation=False))
 dest=OUT/'g1_final_build';dest.mkdir(exist_ok=True)
 for p in [ROOT/'research/uctt_r05g/tracker.hpp',ROOT/'research/uctt_r05g/runtime.cpp',BUILD/'Release/R05G.dll']:shutil.copy2(p,dest/p.name)
 print(read(OUT/'G1_gate.json'));print([r for r in rr if r['dataset_id']=='ct3'])
if __name__=='__main__':main()
