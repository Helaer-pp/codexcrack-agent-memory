"""Frozen-source observational execution and explicitly separated motion counterfactuals."""
from pathlib import Path
import os,sys,json,csv,hashlib,ast,types,contextlib,time,traceback,subprocess,copy
import numpy as np
import cv2
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'paired_p1p2_roi_V1_FROZEN.py').is_file() and (p/'config/project.json').is_file())
sys.path.insert(0,str(ROOT/'src/python'))
from crackv4.dataset_policy import require
FROZEN=ROOT/'paired_p1p2_roi_V1_FROZEN.py'
SHA='2e2e5ebef80ab33e486c561b6dec09ee15d23033020cc1886a7de24c7ce2baf6'
OLD=ROOT/'output/runs/p1p2_grayref_v1_20261112_r01'
OUT=Path(os.environ.get('GROUP_C_AUDIT_OUTPUT',str(ROOT/'output/diagnostics/group_c_same_bmp_root_cause_v1_20261112_r01'))).resolve()
assert OUT.is_relative_to((ROOT/'output').resolve()) and str(OUT).isascii(),'Use a new ASCII directory inside project output/'
ARRAYS=['ca','reference_aligned','csm','rsm','valley','newdark','flank_low','roi_mask','valid_material','score','alpha','dx','dy']
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def array_sha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def save(p,records):
 assert records,'Do not write a misleading empty CSV'
 Path(p).parent.mkdir(parents=True,exist_ok=True)
 with Path(p).open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in records for k in r)));writer.writeheader()
  for r in records:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,tuple,dict)) else v for k,v in r.items()})
def stage(source,name):
 require('group_c','validation');dest=OUT/'staging'/name;dest.parent.mkdir(parents=True,exist_ok=True);b=Path(source).read_bytes();dest.write_bytes(b);assert sha(source)==sha(dest);return dest
def arguments(ref,cur,rp,cp,folder):
 argv=[str(FROZEN),'--reference',str(ref),'--current',str(cur),'--output-dir',str(folder)]
 for name,pts in [('ref',rp),('cur',cp)]:
  if pts is not None:
   for i,p in enumerate(pts,1):argv+=['--p'+str(i)+'-'+name,','.join(repr(float(v)) for v in p)]
 return argv
def module(donor=None):
 assert sha(FROZEN)==SHA;source=FROZEN.read_text(encoding='utf8');tree=ast.parse(source);filename=str(FROZEN)
 if donor is not None:
  # Change only alpha/dx/dy immediately before remap. All remaining frozen AST is retained.
  main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  idx=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='reference_aligned' for t in n.targets))
  hook=ast.parse('alpha,dx,dy=_diagnostic_motion(X,Y)').body[0];main.body.insert(idx,hook);ast.fix_missing_locations(tree)
  source=ast.unparse(tree);filename=str(OUT/'scripts/diagnostic_motion_copy.py');Path(filename).parent.mkdir(parents=True,exist_ok=True)
  if not Path(filename).exists():Path(filename).write_text(source,encoding='utf8')
  tree=ast.parse(source)
 m=types.ModuleType('v1_observed');m.__file__=str(FROZEN)
 if donor is not None:
  rp,cp=donor;reg=[dict(dx=float(q[0]-p[0]),dy=float(q[1]-p[1])) for p,q in zip(rp,cp)];P1,P2=cp
  def motion(X,Y):
   alpha=np.clip((Y-P1[1])/(P2[1]-P1[1]),0,1);dx=(1-alpha)*reg[0]['dx']+alpha*reg[1]['dx'];dy=(1-alpha)*reg[0]['dy']+alpha*reg[1]['dy'];return alpha,dx,dy
  m._diagnostic_motion=motion
 exec(compile(source,filename,'exec'),m.__dict__)
 track=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='track')
 initline=next(n.lineno for n in track.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='rows' for t in n.targets))
 appendline=next(n.lineno for n in ast.walk(track) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=='rows' and n.value.func.attr=='append')
 return m,filename,initline,appendline
def execute(name,ref,cur,rp,cp,*,detailed=False,donor=None):
 folder=OUT/'runs'/name;folder.mkdir(parents=True,exist_ok=False);m,filename,initline,appendline=module(donor);captured={};init=[];candidate=[];tracking=[];seen=set();args=arguments(ref,cur,rp,cp,folder)
 def hook(frame,event,arg):
  if frame.f_code.co_filename!=filename:return None
  local=frame.f_locals
  if frame.f_code.co_name=='main':
   if event=='return':captured.update(local)
   return hook
  if frame.f_code.co_name!='track':return None
  if event=='line' and frame.f_lineno==initline:
   y=local['init_ys'];score=local['init_score'];pri=local['pri'];weighted=score*pri;ranks=np.empty(len(y),int);ranks[np.argsort(-weighted,kind='stable')]=np.arange(1,len(y)+1);xs=local['xstart'];col=xs-local['xa'];kk=y-local['ya'];v=local['valley'][kk,col];d=local['newdark'][kk,col];mat=local['valid_material'][kk,col]
   tracking.append(dict(case=name,mode=local['method'],threshold=local['thr'],xstart=xs,ctr=local['ctr'],init_ymin=int(y.min()),init_ymax=int(y.max()),y0=local['y0'],all_scores_zero=bool(np.all(weighted==0)),nonzero_scores=int(np.count_nonzero(weighted)),material_candidates=int(mat.sum()),accepted_initial_joint10=int(np.sum(mat&(v>=10)&(d>=10))),accepted_initial_current10=int(np.sum(mat&(v>=10)))))
   if detailed and local['thr']==10:
    for i,yy in enumerate(y):init.append(dict(case=name,mode=local['method'],threshold=10,x=xs,y=int(yy),is_valid_material=bool(mat[i]),valley=float(v[i]),newdark=float(d[i]),score=float(local['score'][kk[i],col]),init_score=float(score[i]),prior=float(pri[i]),weighted_score=float(weighted[i]),rank=int(ranks[i]),selected=bool(yy==local['y0']),accept_joint_T10=bool(mat[i] and v[i]>=10 and d[i]>=10),accept_current_T10=bool(mat[i] and v[i]>=10)))
  if detailed and event=='line' and frame.f_lineno==appendline and local['thr']==10:
   key=local['method'],local['thr'],local['x']
   if key in seen:return hook
   seen.add(key)
   for i,yy in enumerate(local['ys']):candidate.append(dict(case=name,mode=local['method'],threshold=10,x=local['x'],y=int(yy),yp=float(local['yp']),valley=float(local['c'][i]),newdark=float(local['d'][i]),valid_material=bool(local['ok'][i]),accept=bool(local['accept'][i]),strength=float(local['strength'][i]),merit=float(local['merit'][i]),selected=i==local['best'],is_observed=local['hit'],missing_run=local['gap']))
  return hook
 previous=sys.argv;sys.argv=args;start=time.perf_counter();error=None
 try:
  with (folder/'stdout.txt').open('w',encoding='utf8') as stdout,(folder/'stderr.txt').open('w',encoding='utf8') as stderr:
   with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
    sys.settrace(hook)
    try:m.main()
    except Exception as e:error=f'{type(e).__name__}: {e}';traceback.print_exc()
    finally:sys.settrace(None)
 finally:sys.argv=previous
 info=dict(case=name,status='OK' if error is None else 'ERROR',error=error,wall_ms=(time.perf_counter()-start)*1000,source_sha256=sha(FROZEN),reference_points=rp,current_points=cp,current_input='NCC' if cp is None else 'provided',counterfactual=donor is not None,motion_donor=donor,gt_in_inference=False,argv=args)
 if error is None:
  info['geometry']={k:captured[k] for k in ['upper','lower','xleft','xr','xa','xb','ya','yb']};info['point_translations']=captured['reg'];info['fields']={k:dict(min=float(captured[k].min()),max=float(captured[k].max()),mean=float(captured[k].mean()),sha256=array_sha(captured[k])) for k in ARRAYS}
  if detailed:np.savez_compressed(folder/'arrays.npz',**{k:captured[k] for k in ARRAYS},crop=np.array([captured[k] for k in ['xa','ya','xb','yb']]))
  save(folder/'track_initialization.csv',tracking)
  if detailed:save(folder/'initial_candidates.csv',init);save(folder/'column_candidates.csv',candidate)
 write(folder/'observer.json',info);print('RUN',name,info['status'],flush=True);assert error is None,error
 return folder
def plain_cli(name,ref,cur,rp,cp):
 folder=OUT/'runs'/name;folder.mkdir(parents=True,exist_ok=False);argv=arguments(ref,cur,rp,cp,folder);start=time.perf_counter();r=subprocess.run([sys.executable,*argv],capture_output=True,text=True,errors='replace');(folder/'stdout.txt').write_text(r.stdout,encoding='utf8');(folder/'stderr.txt').write_text(r.stderr,encoding='utf8');write(folder/'cli_identity.json',dict(argv=argv,returncode=r.returncode,wall_ms=(time.perf_counter()-start)*1000,source_sha256=sha(FROZEN)));assert r.returncode==0,r.stderr;return folder
def compare_outputs(a,b):
 equal=rows(a/'summary_results.csv')==rows(b/'summary_results.csv');traces={p.name:sha(p)==sha(b/p.name) for p in a.glob('trace_*.csv')};return dict(summary_equal=equal,trace_files_equal=traces,passed=equal and all(traces.values()))
