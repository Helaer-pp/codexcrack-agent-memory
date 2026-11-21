from v2common import *
from replay import parse_manifest,read_image,locked
from algorithm import FIELDS,evidence,detect
from native_v2 import Native,BUILD
import numpy as np,psutil,concurrent.futures,math,argparse
def difference(a,b,path=''):
 if isinstance(a,dict):
  if not isinstance(b,dict) or set(a)!=set(b):return dict(path=path,kind='KEYS',python=list(a),cpp=list(b) if isinstance(b,dict) else b)
  for k in a:
   d=difference(a[k],b[k],path+'/'+k)
   if d:return d
 elif isinstance(a,list):
  if not isinstance(b,list) or len(a)!=len(b):return dict(path=path,kind='LENGTH',python=len(a),cpp=len(b) if isinstance(b,list) else b)
  for i,(x,y) in enumerate(zip(a,b)):
   d=difference(x,y,path+f'/{i}')
   if d:return d
 elif isinstance(a,float):
  if b is None or not isinstance(b,(int,float)) or not math.isfinite(b) or abs(a-b)>1e-6:return dict(path=path,kind='FLOAT_GT_1E6',python=a,cpp=b)
 elif a!=b:return dict(path=path,kind='DISCRETE',python=a,cpp=b)
 return None
def compare(py,cpp,arrays,R,C,rp,cp,ident):
 checks=[];first=[];fresh=None
 def layer(name,a,b):
  d=difference(a,b);exact=a==b;checks.append(dict(**ident,layer=name,exact=exact,within_tolerance=d is None,first_difference=d))
  if d:first.append(dict(**ident,layer=name,**d))
 for key in ['status','roi','reference_points','current_points','reference_quality']:layer(key,py[key],cpp[key])
 for key in FIELDS:
  a=arrays[key];expected=py['array_identity'][key];digest=hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest();exact=list(a.shape)==expected['shape'] and digest==expected['float32_sha'];maximum=0.;above=0;coord=None
  if not exact:
   if fresh is None:fresh=evidence(R,C,rp,cp)[0]
   d=np.abs(fresh[key].astype(float)-a.astype(float));maximum=float(d.max());above=int((d>1e-5).sum());ids=np.argwhere(d>1e-5);coord=ids[0].tolist() if len(ids) else None
  checks.append(dict(**ident,layer='array_'+key,exact=exact,within_tolerance=above==0,max_abs=maximum,values=int(a.size),above_1e5=above,first_array_index=coord))
  if above:first.append(dict(**ident,layer='array_'+key,kind='ARRAY_GT_1E5',path=str(coord),python='see source array',cpp='see native array',max_abs=maximum))
 for p,c in zip(py['results'],cpp['results']):
  assert p['mode']==c['mode']
  for key in ['seeds','paths','trace','terminal_candidates','reference_status_counts']:
   layer(p['mode']+'/'+key,p[key],c[key])
  keys=['mode','output_state','tip','candidate_tip','chosen_seed','chosen_path_id','ambiguous','observed_path_count','predicted_gap_count','last_visited_x','stop_reason'];layer(p['mode']+'/outputs',{k:p[k] for k in keys},{k:c[k] for k in keys})
 return checks,first
def worker(group):
 locked();n=Native();seq=[r for r in parse_manifest() if r['group']==group] if group!='SENTINELS' else [dict(c['row'],case_name=c['name']) for c in read(OUT/'perturbation_plan.json')['cases']];checks=[];first=[];perf=[];R=None;refpath=None
 for row in seq:
  if refpath!=row['reference']:R=read_image(row['reference'],row['ref_sha']);refpath=row['reference']
  C=read_image(row['current'],row['image_sha']);rp=row['reference_points'];cp=row['current_points'];fid=row.get('case_name',row['frame_id']);src=OUT/'sentinels'/str(fid) if group=='SENTINELS' else OUT/'frames'/group/str(fid);py=unpack(src/'result.json.gz');cpp,arrays=n.run(R,C,rp,cp);ident=dict(group=group,frame_id=fid);part,fail=compare(py,cpp,arrays,R,C,rp,cp,ident);checks.extend(part);first.extend(fail);packed(OUT/'native'/group/str(fid)/'result.json.gz',cpp);perf.append(dict(**ident,native_ms=cpp['runtime_ms'],api_wall_ms=cpp['api_wall_ms'],peak_rss=psutil.Process().memory_info().peak_wset,decode_included=False,startup_included=False))
  if group=='SENTINELS' or int(fid)%50==0:print('NATIVE',group,fid,'differences',len(first),flush=True)
 save(OUT/'parity'/f'{group}.csv',checks);save(OUT/'parity'/f'{group}_first_differences.csv',first or [dict(group=group,kind='NONE')]);save(OUT/'parity'/f'{group}_runtime.csv',perf);write(OUT/'parity'/f'{group}_complete.json',dict(cases=len(seq),checks=len(checks),first_differences=len(first),passed=not first,utc=utc()));print('NATIVE COMPLETE',group,len(seq),len(first),flush=True)
def synthetic():
 from test_modules import image_fixture,line
 n=Native();R=image_fixture();rp=[[80.,40.],[80.,240.]];records=[]
 for variant in range(6):
  C=R.copy();line(C,159,86,350,140)
  if variant==1:line(C,90,86,89,20)
  if variant==2:C[158:161,170:178]=R[158:161,170:178]
  if variant==3:C[:]=200
  reference=C.copy() if variant in [3,4] else R
  cp=[[80.,240.],[80.,40.]] if variant==5 else rp
  py,a=detect(reference,C,rp,cp);cpp,b=n.run(reference,C,rp,cp)
  if py['status']=='INPUT_ERROR':ok=cpp['status']=='INPUT_ERROR' and all(r['output_state']=='INPUT_ERROR' for r in cpp['results']);diff=None
  else:
   py['array_identity']={k:dict(shape=list(v.shape),float32_sha=hashlib.sha256(np.ascontiguousarray(v,dtype=np.float32).tobytes()).hexdigest()) for k,v in a.items()};checks,diff=compare(py,cpp,b,reference,C,rp,cp,dict(group='SYNTHETIC',frame_id=variant));ok=not diff;save(OUT/'parity'/f'synthetic_{variant}.csv',checks)
  records.append(dict(variant=variant,passed=ok,difference=diff));assert ok,records[-1]
 save(OUT/'parity/synthetic_contracts.csv',records);print('NATIVE SYNTHETIC PASS',flush=True)
def main():
 assert (OUT/'validation_evaluation_complete.json').exists();synthetic();write(OUT/'native_port_identity.json',dict(utc=utc(),dll_sha=sha(BUILD/'GrayRefV2.dll'),source_sha={p.name:sha(p) for p in Path(__file__).parent.iterdir() if p.suffix in ['.hpp','.cpp','.h']},frozen_python=read(OUT/'config_v2_locked.json')['algorithm_sources'],no_cpp_calls_to_python=True,thread_count=1))
 with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
  for _ in pool.map(worker,DEV+VAL+['SENTINELS']):pass
 allchecks=[];first=[];perf=[]
 for g in DEV+VAL+['SENTINELS']:
  allchecks.extend(rows(OUT/'parity'/f'{g}.csv'));first.extend([r for r in rows(OUT/'parity'/f'{g}_first_differences.csv') if r['kind']!='NONE']);perf.extend(rows(OUT/'parity'/f'{g}_runtime.csv'))
 summary=[]
 for layer in sorted(set(r['layer'] for r in allchecks)):
  rr=[r for r in allchecks if r['layer']==layer];summary.append(dict(layer=layer,n=len(rr),exact=sum(r['exact']=='True' for r in rr),within_tolerance=sum(r['within_tolerance']=='True' for r in rr),max_abs=max(float(r.get('max_abs') or 0) for r in rr)))
 save(OUT/'numeric_parity_summary.csv',summary);save(OUT/'numeric_first_divergences.csv',first or [dict(kind='NONE')]);save(OUT/'native_runtime_frames.csv',[r for r in perf if r['group']!='SENTINELS']);write(OUT/'native_parity_complete.json',dict(passed=not first,full_frames=2647,sentinel_perturbation_cases=136,v2_modes=5,mode_cases=(2647+136)*5,checks=len(allchecks),failed_layers=len(first),utc=utc()));print('GATE6 PARITY',not first,'differences',len(first),flush=True)
if __name__=='__main__':main()
