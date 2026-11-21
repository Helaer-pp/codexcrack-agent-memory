"""One frozen Python/native pass per validation frame, after development parity and scoring."""
from common import *
from python_replay import load,execute,argv,stage
from cpp_replay import Native,decode,compare
import argparse,time,numpy as np,datetime
def prepare():
 gate=read(OUT/'parity_gate.json');assert gate['passed'];assert read(OUT/'evaluation_dev_complete.json')['frames']==1565
 for p,digest in gate['files'].items():assert sha(ROOT/p)==digest
 assert not (OUT/'validation_lock.json').exists(),'Validation already locked; do not rerun'
 manifest=[];audit=[]
 for g in VAL:
  require(g,'validation');seq=sorted([r for r in rows(F/'input_inventory_allowed.csv') if r['dataset_id']==g],key=lambda r:int(r['frame_order']));first=seq[0];rp=json.loads(first['points'])
  for i,r in enumerate(seq):
   assert int(r['frame_order'])==i and int(r['frame_id'])==i+1;pp=json.loads(r['points']);manifest.append(dict(group=g,frame_id=i+1,split='VALIDATION_ONLY',reference=first['source_image'],current=r['source_image'],p1_ref_x=rp[0][0],p1_ref_y=rp[0][1],p2_ref_x=rp[1][0],p2_ref_y=rp[1][1],p1_cur_x=pp[0][0],p1_cur_y=pp[0][1],p2_cur_x=pp[1][0],p2_cur_y=pp[1][1]));audit.append(dict(group=g,frame_id=i+1,frame_order=i,reference_frame_id=1,point_source=r['p1p2_source'],mapping=r['mapping_source'],coordinates='original_image_pixels_xy',image_sha256=r['sha256']))
 save(OUT/'inputs/validation_manifest.csv',manifest);save(OUT/'inputs/validation_input_audit.csv',audit)
 files=dict(gate['files']);files.update({str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'research/p1p2_grayref_v1/python_replay.py',ROOT/'research/p1p2_grayref_v1/cpp_replay.py',ROOT/'research/p1p2_grayref_v1/evaluate.py']});write(OUT/'validation_lock.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=files,manifest_sha256=sha(OUT/'inputs/validation_manifest.csv'),development_accuracy='See fixed six-mode group_summary_dev; no threshold selection or parameter changes',frames=len(manifest),validation_new_images_read=0,exception='Previously-explored regression pair already read as explicitly requested; not a blind validation',labels_read=0))
 print('VALIDATION LOCKED',len(manifest),flush=True)
def verify_lock(lock):
 amendment=read(OUT/'validation_io_amendment.json') if (OUT/'validation_io_amendment.json').exists() else None
 for p,digest in lock['files'].items():
  if (ROOT/p).resolve()==Path(__file__).resolve() and amendment:
   assert digest==amendment['original_driver_sha256'];assert sha(ROOT/p)==amendment['amended_driver_sha256']
  else:assert sha(ROOT/p)==digest
 assert sha(OUT/'inputs/validation_manifest.csv')==lock['manifest_sha256']
def run(g,resume=False):
 require(g,'validation');lock=read(OUT/'validation_lock.json');verify_lock(lock);entry=OUT/f'validation_entry_{g}.json'
 if entry.exists():assert resume,'One-time validation already entered; explicit resume required'
 else:write(entry,dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frozen_hashes_verified=True))
 seq=[r for r in rows(OUT/'inputs/validation_manifest.csv') if r['group']==g];inv={(r['dataset_id'],int(r['frame_id'])):r for r in rows(F/'input_inventory_allowed.csv')};selected={(r['dataset_id'],int(r['frame_id'])) for r in rows(F/'selected_frames.csv') if r['dataset_id'] in VAL};staging=OUT/'io_cache'/g;staging.mkdir(parents=True,exist_ok=True);ref=staging/'reference.bmp';cur=staging/'current.bmp';digest,io=stage(seq[0]['reference'],ref,inv[g,1]['sha256']);pp=lambda r,s:[[float(r[f'p{k}_{s}_x']),float(r[f'p{k}_{s}_y'])] for k in [1,2]];m=load();n=Native();h=n.create(decode(ref),pp(seq[0],'ref'));metrics=[];timings=[];parity=[]
 try:
  for i,row in enumerate(seq):
   f=int(row['frame_id']);assert f==i+1;folder=OUT/'py_runs'/g/str(f);imagehash,stage_ms=stage(row['current'],cur,inv[g,f]['sha256']);reused=resume and (folder/'adapter_metrics.json').exists()
   if reused:
    metric=read(folder/'adapter_metrics.json');assert metric['source_sha256']==EXPECTED_SHA;assert len(rows(folder/'summary_results.csv'))==6
   else:
    folder.mkdir(parents=True,exist_ok=False);metric=execute(m,argv(row,ref,cur,folder),folder,(g,f) in selected)
   provenance=dict(group=g,frame_id=f,split='VALIDATION_ONLY',original_reference=row['reference'],original_current=row['current'],image_sha256=imagehash,reference_sha256=digest,p1_source='provided_original_pixel_coordinates',staging_io_hash_ms=stage_ms,reused_completed_python_result=reused,**metric);write(folder/'input_provenance.json',provenance);metrics.append(provenance)
   tick=time.perf_counter();image=decode(cur);decode_ms=(time.perf_counter()-tick)*1000;cppfolder=OUT/'cpp_runs'/g/str(f);cpp_reused=resume and (cppfolder/'result.json').exists()
   if cpp_reused:t=read(cppfolder/'result.json')
   else:t=n.process(h,image,pp(row,'cur'));write(cppfolder/'result.json',t)
   parity.extend(compare(t,folder,g,f));timings.append(dict(group=g,frame_id=f,decode_ms=decode_ms,reused_cpp_result=cpp_reused,**t['runtime'],export_ms=t['debug_export_ms']))
   if (g,f) in selected and not cpp_reused:np.savez_compressed(cppfolder/'evidence_arrays.npz',**n.arrays(h))
   if f%25==0:print('VALIDATION',g,f,'/',len(seq),metric['status'],flush=True)
 finally:n.close(h)
 save(OUT/'tables'/f'python_frames_{g}.csv',metrics);save(OUT/'tables'/f'cpp_timing_{g}.csv',timings);save(OUT/'tables'/f'parity_{g}.csv',parity);verify_lock(lock);write(OUT/f'validation_complete_{g}.json',dict(frames=len(seq),python_ok=sum(r['status']=='OK' for r in metrics),cases=len(parity),tip_exact=sum(r['tip_exact'] for r in parity),trace_structure_equal=sum(r['trace_structure_equal'] for r in parity),annotations_read=0,source_unchanged=True,reused_python_frames=sum(r['reused_completed_python_result'] for r in metrics)));print('VALIDATION COMPLETE',g,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','run']);p.add_argument('--group',choices=VAL);p.add_argument('--resume',action='store_true');a=p.parse_args();prepare() if a.mode=='prepare' else run(a.group,a.resume)
