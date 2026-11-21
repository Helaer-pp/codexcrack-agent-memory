import ctypes as C,csv,json,time,hashlib,subprocess
import numpy as np
from common import *
def main():
 a0=lib(BUILD/'Release/B0_R02_A0.dll');a1=lib(BUILD/'Release/B1_DIAGNOSTIC.dll')
 a1.R04Process.argtypes=a1.CrackV4Process.argtypes;a1.R04Observe.argtypes=[C.c_void_p,C.POINTER(api.Image),C.c_int];a1.R04Observe.restype=C.c_char_p
 a1.R04Map.argtypes=[C.c_void_p,C.c_int,*([C.POINTER(C.c_int)]*4)];a1.R04Map.restype=C.c_void_p
 a1.CrackV4ProfileMilliseconds.restype=C.POINTER(C.c_double)
 r=subprocess.run([str(BUILD/'Release/R03Reproduce.exe'),str(R03/'fault_seed.txt')],capture_output=True,text=True)
 (OUT/'r03_fault_reproduction.csv').write_text(r.stdout,encoding='utf-8-sig');assert r.returncode==2
 expected_fault=list(csv.DictReader((R03/'fault_injection_results.csv').open(encoding='utf-8-sig')));current_fault=list(csv.DictReader(r.stdout.splitlines()));assert current_fault==expected_fault
 write('gate0_fault.json',dict(reproduced=True,rows=len(current_fault),failed=[x['case_id'] for x in current_fault if x['pass']=='0']))
 variants=list(csv.DictReader((ROOT/'output/runs/phase1_acceptance_r02/t2_variants.csv').open(encoding='utf-8-sig')))
 lookup={(r['dataset_id'],r['variant_id']):[[float(r[f'init_p{k}_x']),float(r[f'init_p{k}_y'])] for k in [1,2]] for r in variants}
 with (R03/'snapshots.jsonl').open(encoding='utf8') as f:old={(r['dataset_id'],r['variant_id'],r['frame_id']):r['raw'] for r in map(json.loads,f)}
 roles=json.loads((OUT/'selection.json').read_text())['roles'];rows=[];checks=[];perf=[];frames=[];candidates=[];maps=[];inits=[]
 (OUT/'maps').mkdir(exist_ok=True)
 def getmap(d,kind):
  h,w,typ,stride=[C.c_int() for _ in range(4)];ptr=a1.R04Map(d.handle,kind,C.byref(h),C.byref(w),C.byref(typ),C.byref(stride))
  if not ptr or not h.value:return None
  dtype=np.float32 if typ.value==5 else np.uint8
  raw=np.ctypeslib.as_array((C.c_ubyte*(h.value*stride.value)).from_address(ptr));return np.ndarray((h.value,w.value),dtype=dtype,buffer=raw,strides=(stride.value,np.dtype(dtype).itemsize)).copy()
 with (OUT/'candidate_paths.jsonl').open('w',encoding='utf8') as log:
  for g,(mode,seq) in inventory().items():
   seq=seq[:max(b for a,b in WINDOWS[g])];ref=api.read(seq[0][0]);refhash=sha(seq[0][0]);names=['measured']+([VARIANTS[g]] if g in VARIANTS else [])
   engines={v:(create(a0,ref,lookup[g,v],mode),create(a1,ref,lookup[g,v],mode)) for v in names}
   for v,ds in engines.items():
    for version,d in zip(['B0_R02_A0','B1_DIAGNOSTIC'],ds):inits.append(dict(dataset_id=g,variant_id=v,version=version,initialization_ms=d.init_ms.value))
   try:
    for i,(p,cp,digest) in enumerate(seq,1):
     im=api.read(p);h=sha(p);assert digest is None or h==digest;sel=selected(g,i)
     frames.append(dict(dataset_id=g,frame_id=i,image_path=str(p),image_sha256=h,width=im.shape[1],height=im.shape[0],reference_hash=refhash,source_kind='real_original',role=roles[g],selected_for_review=sel,anchor_variants=names,GT='GT_UNAVAILABLE'))
     for v,(d0,d1) in engines.items():
      natives=[];times=[];rrs=[];dbg=None;side=None;values=None
      for k,d in enumerate([d0,d1]):
       l=d.lib;r=api.Result();r.struct_size=C.sizeof(r);ii=api.image(im);pp=api.points(cp)
       start=time.perf_counter()
       if i==1:
        rc=l.CrackV4GetBaseline(d.handle,C.byref(r))
        if k:a1.R04Observe(d.handle,C.byref(ii),1)
       else:rc=(a1.R04Process if k else a0.CrackV4Process)(d.handle,C.byref(ii),pp,C.byref(r))
       ms=(time.perf_counter()-start)*1000;assert rc==0,(g,v,i,k,rc)
       times.append(ms);rrs.append(r);natives.append(json.loads(l.CrackV4LastJson(d.handle)))
       if k:
        before=natives[-1];side=json.loads(a1.R04Observe(d.handle,C.byref(ii),i==1));after=json.loads(l.CrackV4LastJson(d.handle));assert before==after
        values=list(a1.CrackV4ProfileMilliseconds()[:24]);dbg=json.loads(l.CrackV4LastDebugJson(d.handle))
      checks.append(dict(dataset_id=g,variant_id=v,frame_id=i,R03_equivalent=normalized(natives[0])==normalized(old[g,v,i]),shadow_equal=normalized(natives[0])==normalized(natives[1]),cached_observe_readonly=before==after))
      basic=dict(run_id=OUT.name,dataset_id=g,variant_id=v,frame_id=i,image_sha256=h,trial_role=roles[g],selected_for_review=sel,image_w=im.shape[1],image_h=im.shape[0],initial_points=lookup[g,v],current_points=cp,reference_query=i==1,roi=dbg['tip_roi_xywh'])
      for k,version in enumerate(['B0_R02_A0','B1_DIAGNOSTIC','B2_D1_STRUCTURE','B2_D2_PREFIX']):
       raw=natives[0];r=rrs[0];state=side['states'][k-2] if k>=2 else None
       observed=bool(state['valid']) if state else bool(r.tip_confirmed);pt=state['output'] if state else ([r.tip.x,r.tip.y] if observed else None)
       rows.append(dict(basic,version=version,visual_confirmed=observed,tip_x=pt[0] if observed else None,tip_y=pt[1] if observed else None,output_x=pt[0] if pt else None,output_y=pt[1] if pt else None,source_type=state['source'] if state else ('observed' if observed else 'legacy_unconfirmed'),source_verified=side['audit']['D2_prefix_connected'] if k==3 else None,endpoint_verified=raw['terminal_audit']['verified'],lock_committed=state['history_written'] if state else None,reject_reason=side['audit']['reason'] if k>=2 else None,raw_status=raw['status'],roi_cutoff=side['audit']['edge'],reference_usable=None,processing_ms=times[k] if k<2 else None,performance_scope='full_native_diagnostic_wrapper' if k==1 else 'full_native_baseline' if k==0 else 'jointly_evaluated_inside_B1_not_separate_timing'))
      for candidate_id,path,a in [(-1,natives[0]['observed_original_px'],side['audit'])]+[(b['candidate_id'],b['path'],b['audit']) for b in side['branches']]:
       candidates.append(dict(basic,candidate_id=candidate_id,branch_id=candidate_id,source_type='selected_raw' if candidate_id==-1 else 'examined_DP_branch',tip_x=path[-1][0] if path else None,tip_y=path[-1][1] if path else None,path_points=len(path),prefix_root_supported_proxy=side['prefix_root_supported_proxy'],physical_source_verified=None,**a))
      if i>1:
       perf.append(dict(basic,B0_api_ms=times[0],B1_api_ms=times[1],main_total_ms=values[20],tip_total_ms=values[17],main_motion_ms=values[0],tip_motion_ms=values[16],main_other_ms=values[20]-values[0]-values[16],local_reference_ms=values[18],distal_path_ms=values[19],tip_other_and_trace_ms=values[17]-values[18]-values[19],new_audit_ms=side['audit_ms'],json_and_api_residual_ms=times[1]-values[20]-values[17]-side['audit_ms'],B2_source=side['states'][1]['source']))
      maprecord={}
      if sel:
       arrays={}
       for kind,key in enumerate(['current_oriented','score_oriented','registered_oriented','prior_oriented','baseline_mask_original']):
        a=getmap(d1,kind)
        if a is not None:maprecord[key]=dict(shape=a.shape,dtype=str(a.dtype),sha256=hashlib.sha256(a.tobytes()).hexdigest());arrays[key]=a
       # Array archive for exact supplied causal case frames; other hashes retained.
       if i in {'ct2':[6,7,8,9],'group_h':[1,2,5,78],'group_c':[38,69],'group_x':[1,2],'ct3':[1,20],'group_a':[241],'three_point_bend':[1,20]}.get(g,[]):
        name=f'maps/{g}_{v}_{i}.npz';np.savez_compressed(OUT/name,**arrays);maprecord['archive']=name
       maps.append(dict(dataset_id=g,variant_id=v,frame_id=i,roi=dbg['tip_roi_xywh'],quarter_turn='derived from forward; arrays are oriented ROI except baseline_mask',arrays=maprecord))
      log.write(json.dumps(dict(**basic,input=frames[-1],raw=natives[0],debug=dbg,sidecar=side,arrays=maprecord),ensure_ascii=False)+'\n')
     if i%40==0:print(g,i,'/',len(seq),flush=True)
   finally:
    for ds in engines.values():
     for d in ds:d.close()
   for name,data in [('comparison_results.csv',rows),('baseline_checks.csv',checks),('performance_scopes.csv',perf),('frame_manifest.csv',frames),('candidate_evidence.csv',candidates),('initialization_timings.csv',inits)]:save(name,data)
   print('completed',g,flush=True)
 write('map_manifest.json',maps);write('gate0_shadow.json',dict(cases=len(checks),unique_group_frames=len(frames),selected_cases=sum(r['selected_for_review'] for r in rows if r['version']=='B0_R02_A0'),R03_mismatches=sum(not r['R03_equivalent'] for r in checks),shadow_mismatches=sum(not r['shadow_equal'] for r in checks)))
 write('build_identity.json',{p.name:sha(p) for p in (BUILD/'Release').glob('*') if p.suffix in ['.dll','.exe']})
if __name__=='__main__':main()
