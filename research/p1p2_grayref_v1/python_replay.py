"""Execute the exact frozen main(), instrument returns only, stage unchanged bytes for Unicode I/O."""
from common import *
import argparse,contextlib,importlib.util,platform,shutil,time,traceback,subprocess,collections
import cv2,numpy as np,scipy,pandas,matplotlib

def load():
 assert sha(FROZEN)==EXPECTED_SHA
 spec=importlib.util.spec_from_file_location('grayref_frozen',FROZEN);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def freeze():
 m=load();path=OUT/'freeze_manifest.json'
 identity=dict(frozen_source=str(FROZEN),sha256=sha(FROZEN),batch_runner_sha256=sha(ROOT/'batch_validate_V1.py'),parameters={k:v for k,v in vars(m).items() if k.isupper() and isinstance(v,(str,float,int,tuple,list,type(None)))},versions=dict(python=sys.version,opencv=cv2.__version__,numpy=np.__version__,scipy=scipy.__version__,pandas=pandas.__version__,matplotlib=matplotlib.__version__,platform=platform.platform()),dev_manifest_sha256=sha(OUT/'inputs/manifest.csv'),adapter_sha256=sha(Path(__file__)),annotations_read=0,validation_new_images_read=0,regression_exception='Only the explicitly authorized already-explored group_c 1(1)/3(175) pair; not cross-specimen accuracy',status='V1_PYTHON_RULES_FROZEN_CPP_PENDING')
 if path.exists():
  previous=read(path);assert previous['sha256']==EXPECTED_SHA
  if previous['adapter_sha256']!=identity['adapter_sha256']:
   assert not (OUT/'py_runs').exists(),'Adapter changed after replay started'
   write(path,identity)
  return
 write(path,identity);folder=OUT/'source_snapshot';folder.mkdir(exist_ok=True);shutil.copy2(FROZEN,folder/FROZEN.name);shutil.copy2(ROOT/'batch_validate_V1.py',folder/'batch_validate_V1.py')
 (OUT/'source_diff.patch').write_text('',encoding='utf8')

def stage(source,dest,expected=None):
 start=time.perf_counter();data=Path(source).read_bytes();digest=hashlib.sha256(data).hexdigest()
 if expected:assert digest==expected,(source,'original hash mismatch')
 dest.write_bytes(data);assert sha(dest)==digest
 return digest,(time.perf_counter()-start)*1000

def argv(row,reference,current,folder):
 args=[str(FROZEN),'--reference',str(reference),'--current',str(current),'--output-dir',str(folder)]
 for name,prefix in [('p1-ref','p1_ref'),('p2-ref','p2_ref'),('p1-cur','p1_cur'),('p2-cur','p2_cur')]:
  if row.get(prefix+'_x','')!='':args+=['--'+name,f"{row[prefix+'_x']},{row[prefix+'_y']}"]
 return args

def execute(m,args,folder,debug=False):
 captured={};starts={};timings=collections.defaultdict(float)
 def profiler(frame,event,arg):
  code=frame.f_code;name=code.co_name
  if name in ('main','track','imread_gray') and code.co_filename==str(FROZEN) or name=='savefig' and code.co_filename.endswith('figure.py'):
   if event=='call':starts[id(frame)]=time.perf_counter()
   elif event=='return':
    timings[name]+=(time.perf_counter()-starts.pop(id(frame),time.perf_counter()))*1000
    if code is m.main.__code__:captured.update(frame.f_locals)
 oldargv=sys.argv;sys.argv=args;start=time.perf_counter();error=None
 try:
  with (folder/'stdout.txt').open('w',encoding='utf8') as output, (folder/'stderr.txt').open('w',encoding='utf8') as err:
   with contextlib.redirect_stdout(output),contextlib.redirect_stderr(err):
    sys.setprofile(profiler)
    try:m.main()
    except Exception as exc:error=f'{type(exc).__name__}: {exc}';traceback.print_exc()
    finally:sys.setprofile(None)
 finally:sys.argv=oldargv
 wall=(time.perf_counter()-start)*1000
 status='OK' if error is None else 'POINT_INVALID' if error and ('point' in error.lower() or 'P1/P2' in error or 'NCC' in error) else 'ROI_INVALID' if error and ('boundary' in error or 'ROI' in error or 'initialization' in error) else 'INPUT_ERROR'
 if debug and captured.get('valley') is not None:
  keys=['ca','reference_aligned','csm','rsm','valley','newdark','flank_low','valid_material','score','roi_mask'];data={k:captured[k] for k in keys};data['crop_xyxy']=np.array([captured[k] for k in ['xa','ya','xb','yb']]);np.savez_compressed(folder/'evidence_arrays.npz',**data)
 count=0
 if 'valley' in captured:
  v=captured['valley'];d=captured['newdark'];valid=captured['valid_material'];count={f'{mode}_{threshold}':int(np.sum(valid&(v>=threshold)&((d>=threshold) if mode=='joint' else True))) for mode in ['joint','current'] for threshold in [8,10,12]}
 metrics=dict(status=status,error=error,wall_ms=wall,decode_ms=timings['imread_gray'],tracking_ms=timings['track'],savefig_ms=timings['savefig'],main_including_io_export_render_ms=timings['main'],candidate_counts=count,source_sha256=sha(FROZEN),observer='return-only Python profile; all algorithm locals unmodified; includes profiling overhead')
 write(folder/'adapter_metrics.json',metrics);return metrics

def regression():
 freeze();m=load();folder=OUT/'regression';folder.mkdir(exist_ok=True);staging=OUT/'io_cache/regression';staging.mkdir(parents=True,exist_ok=True)
 src=Path('D:/datasets/1-引伸计/1-裂纹/2-验证组C/1');rsha,_=stage(src/'1 (1).bmp',staging/'reference.bmp');csha,_=stage(src/'3 (175).bmp',staging/'current.bmp')
 row=dict(p1_ref_x=m.P1_REFERENCE[0],p1_ref_y=m.P1_REFERENCE[1],p2_ref_x=m.P2_REFERENCE[0],p2_ref_y=m.P2_REFERENCE[1]);args=argv(row,staging/'reference.bmp',staging/'current.bmp',folder)
 # A true isolated CLI run measures startup-inclusive time and checks original execution.
 tick=time.perf_counter();run=subprocess.run([sys.executable,*args],capture_output=True,text=True,errors='replace');elapsed=(time.perf_counter()-tick)*1000;(folder/'cli_stdout.txt').write_text(run.stdout,encoding='utf8');(folder/'cli_stderr.txt').write_text(run.stderr,encoding='utf8');assert run.returncode==0,run.stderr
 actual=rows(folder/'summary_results.csv');given={('joint',8):(2424,2344),('joint',10):(2423,2344),('joint',12):(2418,2345),('current',10):(2285,2307)};checks=[]
 for row in actual:
  key=row['mode'],int(float(row['threshold']));tip=(int(float(row['tip_x'])),int(float(row['tip_y']))) if row['tip_x'] else None;expected=given.get(key);checks.append(dict(mode=key[0],threshold=key[1],actual=tip,expected=expected,passed=tip==expected if expected else None,expected_source='task_document' if expected else 'missing_expected_summary_csv'))
 instrumented=folder/'instrumented';instrumented.mkdir(exist_ok=True);args[args.index('--output-dir')+1]=str(instrumented);execute(m,args,instrumented,True)
 assert rows(instrumented/'summary_results.csv')==actual,'Observer changed output'
 passed=all(x['passed'] for x in checks if x['expected'] is not None);write(folder/'regression_checks.json',dict(known_four_pass=passed,six_golden_complete=all(x['expected'] is not None for x in checks),checks=checks,reference_sha256=rsha,current_sha256=csha,cli_wall_ms=elapsed,observer_identical=True,regression_only=True));print(checks,flush=True)
 assert passed,'Regression mismatch: investigate environment; do not change golden'

def replay(group):
 require(group,'development');freeze();assert read(OUT/'regression/regression_checks.json')['known_four_pass'];m=load();inventory={(r['dataset_id'],int(r['frame_id'])):r for r in rows(F/'input_inventory_allowed.csv')};selections={(r['dataset_id'],int(r['frame_id'])) for r in rows(F/'selected_frames.csv') if r['dataset_id'] in DEV};seq=[r for r in rows(OUT/'inputs/manifest.csv') if r['group']==group];assert seq
 stagefolder=OUT/'io_cache'/group;stagefolder.mkdir(parents=True,exist_ok=True);ref=stagefolder/'reference.bmp';cur=stagefolder/'current.bmp';rsha,rio=stage(seq[0]['reference'],ref,inventory[group,int(seq[0]['frame_id'])]['sha256']);records=[]
 for i,row in enumerate(seq):
  require(group,'development');frame=int(row['frame_id']);assert frame==i+1;folder=OUT/'py_runs'/group/str(frame);folder.mkdir(parents=True,exist_ok=False);digest,io=stage(row['current'],cur,inventory[group,frame]['sha256']);args=argv(row,ref,cur,folder);metric=execute(m,args,folder,(group,frame) in selections);record=dict(group=group,frame_id=frame,reference_frame_id=1,reference=row['reference'],current=row['current'],current_sha256=digest,reference_sha256=rsha,staging_io_hash_ms=io+(rio if i==0 else 0),p1_source='provided_original_pixel_coordinates',**metric);records.append(record);write(folder/'input_provenance.json',record)
  if frame%25==0:print(group,frame,'/',len(seq),metric['status'],flush=True)
 save(OUT/'tables'/f'python_frames_{group}.csv',records);write(OUT/f'python_complete_{group}.json',dict(frames=len(records),ok=sum(r['status']=='OK' for r in records),failed=sum(r['status']!='OK' for r in records),annotations_read=0,validation_images_read=0,source_unchanged=sha(FROZEN)==EXPECTED_SHA));print('COMPLETE',group,len(records),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['regression','replay']);p.add_argument('--group',choices=DEV);a=p.parse_args();regression() if a.mode=='regression' else replay(a.group)
