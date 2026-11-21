from v2common import *
from algorithm import detect,PARAMS,FIELDS
from frozen_adapter import compute
import numpy as np,cv2,time,psutil,concurrent.futures,argparse,shutil,traceback
def locked():
 lock=read(OUT/'config_v2_locked.json')
 for name,digest in lock['algorithm_sources'].items():assert sha(Path(__file__).parent/name)==digest,name
 assert lock['parameters']==PARAMS;return lock
def freeze():
 assert read(OUT/'gate1_complete.json')['passed'];assert not (OUT/'config_v2_locked.json').exists()
 source=Path(__file__).parent;shutil.copyfile(source/'V2_EXPERIMENT_PLAN.md',OUT/'V2_EXPERIMENT_PLAN.md')
 write(OUT/'config_v2_locked.json',dict(config_id='V2_R01_GLOBAL',utc=utc(),parameters=PARAMS,modes=MODES,default_mode='V2_COMBINED',algorithm_sources={p:sha(source/p) for p in ['algorithm.py','frozen_adapter.py']},experiment_plan_sha=sha(OUT/'V2_EXPERIMENT_PLAN.md'),labels_read=0,validation_v2_inference_before_lock=0,temporal='NOT_IMPLEMENTED',new_registration='NOT_IMPLEMENTED',native_port_must_follow_frozen_python=True))
 print('GATE2 LOCKED',flush=True)
def read_image(path,expected):
 b=Path(path).read_bytes();assert hashlib.sha256(b).hexdigest()==expected,path;a=cv2.imdecode(np.frombuffer(b,np.uint8),0)
 if a is None:raise ValueError('Cannot decode '+path)
 return a
def material_audit(R,C,rp,cp,g):
 out=[]
 for side,y in [('upper',g['upper']+22),('lower',g['lower']-22)]:
  x=min(g['xr']-40,g['xleft']+96);alpha=min(1,max(0,(y-cp[0][1])/(cp[1][1]-cp[0][1])));d=[(1-alpha)*(cp[0][k]-rp[0][k])+alpha*(cp[1][k]-rp[1][k]) for k in [0,1]];rx=round(x-d[0]);ry=round(y-d[1]);h,w=C.shape
  if not (40<=x<w-40 and 16<=y<h-16 and 32<=rx<w-32 and 8<=ry<h-8):out.append(dict(side=side,status='UNAVAILABLE_BOUNDARY',applied_to_inference=False));continue
  tpl=R[ry-8:ry+8,rx-32:rx+32];search=C[y-16:y+16,x-40:x+40];match=cv2.matchTemplate(search,tpl,cv2.TM_CCOEFF_NORMED);_,q,_,loc=cv2.minMaxLoc(match)
  out.append(dict(side=side,reference_center=[rx,ry],current_search_center=[x,y],predicted_displacement=d,independent_displacement=[x+loc[0]-8-rx,y+loc[1]-8-ry],ncc=float(q),status='TEXTURE_MATCH_ONLY' if float(tpl.std())>=2 and q>=.8 else 'LOW_QUALITY',applied_to_inference=False))
 return out
def baseline_result(v):
 rr,obs,tip=v['traces']['joint',10.];trace=[[int(r[0]),int(r[1]),bool(r[5]),int(r[6]),int(round(r[7]*1024)),0,0,float(r[2]),float(r[3]),-1,int(round(r[4]*1e6)),0] for r in rr]
 return dict(mode='V1_LOCKED',output_state='PROVISIONAL_OBSERVED' if tip else 'NO_TIP',tip=list(tip) if tip else None,candidate_tip=list(tip) if tip else None,roi=v['roi'],seeds=[],paths=[],trace=trace,chosen_seed=[rr[0][0],rr[0][7]] if rr else None,chosen_path_id=0,terminal_candidates=[],seed_candidates_count=1,observed_path_count=len(obs),predicted_gap_count=sum(not r[5] for r in rr),last_visited_x=rr[-1][0] if rr else None,stop_reason='GAP_LIMIT' if rr and rr[-1][6]>20 else 'RIGHT_BOUNDARY',reference_status_counts={},gt_accessed_at_inference=False,runtime_ms=v['runtime_ms'])
def execute_case(row,root,baseline=True):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);group=row['group'];require(group,'development' if group in DEV else 'validation');tick=time.perf_counter();R=read_image(row['reference'],row['ref_sha']);C=read_image(row['current'],row['image_sha']);decode_ms=(time.perf_counter()-tick)*1000;rp=row['reference_points'];cp=row['current_points']
 original=compute(R,C,rp,cp,root/'v1') if baseline else None;tick=time.perf_counter();v,a=detect(R,C,rp,cp);wall=(time.perf_counter()-tick)*1000
 if a is not None and original:
  assert v['roi']==original['roi'];assert all(np.array_equal(a[k],original['arrays'][k]) for k in FIELDS),'V2 preprocessing silently changed V1 evidence'
 if original:v['baseline']=baseline_result(original)
 v['input']={k:row[k] for k in ['group','frame_id','reference','current','image_sha','ref_sha','reference_points','current_points','point_source']};v['config_id']='V2_R01_GLOBAL';v['decode_hash_ms']=decode_ms;v['v2_total_wall_ms']=wall;v['process_peak_rss_bytes']=psutil.Process().memory_info().peak_wset;v['gt_accessed_at_inference']=False;v['utc']=utc()
 if a is not None:
  v['array_identity']={k:dict(shape=list(a[k].shape),float32_sha=hashlib.sha256(np.ascontiguousarray(a[k],dtype=np.float32).tobytes()).hexdigest()) for k in FIELDS};v['independent_material_audit']=material_audit(R,C,rp,cp,v['roi'])
 packed(root/'result.json.gz',v)
 return v,a
def parse_manifest():
 seq=rows(OUT/'experiment_manifest.csv')
 for r in seq:
  r['frame_id']=int(r['frame_id']);r['reference_points']=json.loads(r['reference_points']);r['current_points']=json.loads(r['current_points'])
 return seq
def worker(group):
 locked();cv2.setNumThreads(1);seq=[r for r in parse_manifest() if r['group']==group];records=[];compare=[]
 selected={int(r['frame_id']) for r in rows(ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv') if r['dataset_id']==group}
 for row in seq:
  fid=row['frame_id'];folder=OUT/'frames'/group/str(fid)
  try:
   result,a=execute_case(row,folder)
   old=OLD/'py_runs'/group/str(fid);equal=all(sha(p)==sha(old/p.name) for p in (folder/'v1').glob('trace_*.csv'));assert equal,(group,fid,'Original V1 replay divergence')
   compare.append(dict(group=group,frame_id=fid,six_original_traces_equal=equal))
   if fid in selected and a is not None:np.savez_compressed(folder/'evidence.npz',**a)
   for v in [result['baseline']]+result['results']:
    fields=['mode','output_state','tip','candidate_tip','roi','seed_candidates_count','chosen_seed','chosen_path_id','reference_status_counts','observed_path_count','predicted_gap_count','last_visited_x','stop_reason','runtime_ms'];records.append(dict(group=group,frame_id=fid,image_sha=row['image_sha'],ref_sha=row['ref_sha'],reference_points=row['reference_points'],current_points=row['current_points'],config_id='V2_R01_GLOBAL',gt_accessed_at_inference=False,**{k:v.get(k) for k in fields}))
  except Exception:
   folder.mkdir(parents=True,exist_ok=True);(folder/'execution_error.txt').write_text(traceback.format_exc(),encoding='utf8');raise
  if fid%25==0:print(group,fid,'/',len(seq),flush=True)
 save(OUT/'tables'/f'results_{group}.csv',records);save(OUT/'tables'/f'v1_replay_{group}.csv',compare);write(OUT/f'python_complete_{group}.json',dict(frames=len(seq),mode_rows=len(records),v2_modes=5,v1_six_traces_exact=True,utc=utc(),labels_read=0));print('COMPLETE',group,len(seq),flush=True)
def batch(validation=False):
 locked();groups=VAL if validation else DEV
 if validation:
  assert (OUT/'development_evaluation_complete.json').exists();assert (OUT/'sentinels_complete.json').exists();write(OUT/'validation_entry_lock.json',dict(utc=utc(),algorithm=read(OUT/'config_v2_locked.json'),dev_summary_sha=sha(OUT/'group_summary_dev.csv'),no_adaptation=True))
 with concurrent.futures.ProcessPoolExecutor(max_workers=min(4,len(groups))) as pool:
  futures={pool.submit(worker,g):g for g in groups}
  for f in concurrent.futures.as_completed(futures):f.result()
 write(OUT/('validation_inference_complete.json' if validation else 'development_inference_complete.json'),dict(groups=groups,frames=sum(COUNTS[g] for g in groups),utc=utc(),passed=True))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','development','validation']);a=p.parse_args();freeze() if a.mode=='freeze' else batch(a.mode=='validation')
