"""Check sealed identities; rerun existing stateless B0 on the same 80 inputs."""
from common import *
import importlib.util,cv2,numpy as np
def main():
 protected=read(OUT/'source_hash_before.json');protected=protected.get('files',protected.get('protected',protected))
 checked=[]
 for rel,expected in read(OUT/'baseline_manifest.json')['protected'].items():
  actual=sha(ROOT/rel);checked.append(dict(path=rel,expected=expected,actual=actual,equal=actual==expected));assert actual==expected,rel
 oldmanifest=read(F/'artifact_manifest.json')['files']
 for rel,v in oldmanifest.items():
  actual=sha(F/rel);assert actual==v['sha256'],rel
 spec=importlib.util.spec_from_file_location('f_replay',ROOT/'research/uctt_r05f/replay.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.BUILD=ROOT/'output/build/uctt_r05f';n=m.Native();result=[];cv2.setNumThreads(1)
 for row in rows(OUT/'selection.csv'):
  g=row['dataset_id'];f=int(row['frame_id']);require(g,'development');raw=Path(row['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=json.loads(row['points']);h=n.create(im,pp)
  try:r=n.process(h,im,pp,True)
  finally:n.close(h)
  old=read(F/'traces'/f'B0_{g}_{f}.json');same=stable(old)==stable(r)
  result.append(dict(dataset_id=g,frame_id=f,non_timing_exact=same,raw_candidates=r['raw_candidates'],retained=r['retained_candidates']))
  if not same:write(OUT/'tests'/f'B0_mismatch_{g}_{f}.json',dict(old=stable(old),new=stable(r)))
 save(OUT/'experiments/B0_reproduction.csv',result);write(OUT/'G0_check.json',dict(status='PASS' if all(r['non_timing_exact'] for r in result) else 'FAIL',protected_files=len(checked),sealed_R05F_files=len(oldmanifest),B0_stateless_selected_replay=80,B0_matching=sum(r['non_timing_exact'] for r in result),B0_full1565='existing sealed full replay preserved and hashed; not rerun',A_full1565='existing sealed exact A/source-clone outputs retained as frozen comparison; source and binaries unchanged',new_validation_images=0,new_validation_annotations=0,excluded_image_annotation_reads=0))
 print(read(OUT/'G0_check.json'),flush=True)
if __name__=='__main__':main()
