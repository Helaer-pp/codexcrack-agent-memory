"""Unmodified production A replay. Does not open any annotation JSON or shapes."""
from pathlib import Path
import sys,csv,json,hashlib,time,collections
import numpy as np
import cv2
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src/python'))
from crackv4 import frozen_a as api
from crackv4.dataset_policy import filter_rows,require,role,POLICY_PATH
OUT=ROOT/'output/runs/r05_annotation_validation_20261111_r01';BASE=ROOT/'output/runs/uctt_r05_prelabel_difference_20261111_r01'
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
def main():
 assert not (OUT/'production_replay_lock.json').exists()
 dll=ROOT/'output/build/src/cpp/a/Release/CrackV4.dll';prior=json.loads((BASE/'frozen_manifest.json').read_text(encoding='utf8'))['protected'];assert sha(dll)==prior[dll.relative_to(ROOT).as_posix()]
 inventory=filter_rows(rows(BASE/'input_inventory.csv'),'validation');selected=filter_rows(rows(OUT/'active_selection_manifest.csv'),'validation');targets={(r['dataset_id'],int(r['frame_id'])) for r in selected};assert len(targets)==120
 write(OUT/'production_replay_lock.json',dict(dll_sha256=sha(dll),inventory_sha256=sha(BASE/'input_inventory.csv'),selection_sha256=sha(OUT/'active_selection_manifest.csv'),policy_sha256=sha(POLICY_PATH),runtime_input='original images + original P1/P2 only; NO ANNOTATION JSON',flags=3572,decision_policy=1,terminal_validation=1,refine=True,native_threads=4,one_detector_per_sequence=True,reference_query='GetBaseline cached once at frame1',selected_targets=120,excluded=['group_x']))
 api.BASE=dll;api.EXPECTED_BASE=sha(dll);api._base=None;cv2.setNumThreads(1)
 modes={g['id']:g['mode'] for g in json.loads((ROOT/'config/datasets.json').read_text(encoding='utf8'))['groups']};modes['ct3']='auto'
 # CT3's baseline mode follows the frozen CT3 manifest/replay convention.
 groups=collections.defaultdict(list)
 for r in inventory:groups[r['dataset_id']].append(r)
 output=[];initial=[]
 with (OUT/'production_replay_all_frames.jsonl').open('w',encoding='utf8') as log:
  for g,seq in groups.items():
   require(g,'validation');last=max(f for gg,f in targets if gg==g);seq=[r for r in seq if int(r['frame_id'])<=last];engine=None
   try:
    for i,r in enumerate(seq):
     assert int(r['frame_order'])==i;start=time.perf_counter();b=Path(r['source_image']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'];im=cv2.imdecode(np.frombuffer(b,np.uint8),0);assert im is not None;io=(time.perf_counter()-start)*1000;points=json.loads(r['points'])
     if engine is None:engine=api.Baseline(im,points,mode=modes[g],flags=3572,refine=True);initial.append(dict(dataset_id=g,init_ms=engine.init_ms.value,mode=modes[g]))
     result=engine.run(im,points,is_reference=i==0);f=result['formal'];valid=f['confirmed_tip'];tip=f['tip'];assert not valid or np.isfinite(tip).all()
     record=dict(dataset_id=g,frame_id=i+1,frame_order=i,group_role=role(g),observed=valid,tip_x=tip[0] if valid else None,tip_y=tip[1] if valid else None,output_type='observed' if valid else 'no_observed_tip',terminal_reason=f['terminal_reason'],reference_state=f['reference_state'],process_ms=f['process_ms'],io_ms=io,source_sha256=r['sha256'],selected=(g,i+1) in targets)
     log.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n')
     if record['selected']:output.append(record)
     if (i+1)%50==0:log.flush();print(g,i+1,'/',last,flush=True)
   finally:
    if engine is not None:engine.close()
   print('finished',g,len(seq),flush=True)
 with (OUT/'production_selected_predictions.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
 assert len(output)==120;write(OUT/'production_replay_initializations.json',initial);write(OUT/'production_replay_complete.json',dict(status='PASS',selected_predictions=120,frames=sum(max(f for gg,f in targets if gg==g) for g in groups),annotation_json_reads=0,production_dll_unchanged=sha(dll)==api.EXPECTED_BASE))
 print('PRODUCTION REPLAY COMPLETE',flush=True)
if __name__=='__main__':main()
