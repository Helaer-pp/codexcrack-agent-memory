"""Gate 0/1 pilot; independent A0 and A1 detectors, A2 sidecar with no ROI feedback."""
import ctypes as C,csv,json,sys,time,hashlib
from pathlib import Path
import numpy as np
from prepare import ROOT,OUT,BUILD,sha,write
sys.path.insert(0,str(ROOT/'src/python'));sys.path.insert(0,str(ROOT/'research/gate_adapt'))
from crackv4 import frozen_a as api
from all_groups import inventory
LIMITS=dict(group_a=252,group_c=80,ct2=120,group_h=120,group_x=120,three_point_bend=160,ct3=136)
EXTRA=dict(ct2='shift_x_plus_2pct',group_h='shift_y_plus_10pct',group_x='shift_y_plus_10pct',group_c='p1_plus_5pct_x')
def lib(path):
    api.BASE=path;api.EXPECTED_BASE=sha(path);api._base=None
    x=api.base_library()
    x.CrackV4LastDebugJson.argtypes=[C.c_void_p];x.CrackV4LastDebugJson.restype=C.c_char_p
    return x
def create(l,ref,p,mode):
    api._base=l
    return api.Baseline(ref,p,mode=mode)
def run(det,im,p,isref):
    l=det.lib;r=api.Result();r.struct_size=C.sizeof(r);ii=api.image(im);pp=api.points(p)
    t=time.perf_counter();rc=l.CrackV4GetBaseline(det.handle,C.byref(r)) if isref else l.CrackV4Process(det.handle,C.byref(ii),pp,C.byref(r));ms=(time.perf_counter()-t)*1000
    n=json.loads(l.CrackV4LastJson(det.handle));debug=json.loads(l.CrackV4LastDebugJson(det.handle))
    return r,rc,ms,n,debug
def normalized(x):
    if isinstance(x,dict):return {k:normalized(v) for k,v in x.items() if k not in ['detector_ms','api_ms']}
    if isinstance(x,list):return [normalized(v) for v in x]
    return x
def main():
    a0=lib(BUILD/'Release/A0_R02.dll');a1=lib(BUILD/'Release/A1_SHADOW.dll')
    a1.R03CreateState.restype=C.c_void_p;a1.R03DestroyState.argtypes=[C.c_void_p]
    a1.R03Observe.argtypes=[C.c_void_p,C.c_void_p,C.c_int];a1.R03Observe.restype=C.c_char_p
    old=list(csv.DictReader((ROOT/'output/runs/phase1_acceptance_r02/t2_reinit_results.csv').open(encoding='utf-8-sig')))
    expected={(r['dataset_id'],r['variant_id'],int(r['frame_id'])):r for r in old}
    variants=list(csv.DictReader((ROOT/'output/runs/phase1_acceptance_r02/t2_variants.csv').open(encoding='utf-8-sig')))
    lookup={(r['dataset_id'],r['variant_id']):[[float(r['init_p1_x']),float(r['init_p1_y'])],[float(r['init_p2_x']),float(r['init_p2_y'])]] for r in variants}
    write('build_identity.json',dict(A0=sha(BUILD/'Release/A0_R02.dll'),A1=sha(BUILD/'Release/A1_SHADOW.dll')))
    rows=[];checks=[];inputs=[];inits=[]
    with (OUT/'snapshots.jsonl').open('w',encoding='utf8') as snaps:
      for g,(mode,seq) in inventory().items():
        seq=seq[:LIMITS[g]];ref=api.read(seq[0][0])
        names=['measured']+([EXTRA[g]] if g in EXTRA else [])
        engines={v:(create(a0,ref,lookup[g,v],mode),create(a1,ref,lookup[g,v],mode),a1.R03CreateState(),a1.R03CreateState()) for v in names}
        for v,eng in engines.items():
            for k,d in enumerate(eng[:2]):inits.append(dict(dataset_id=g,variant_id=v,group=['A0_R02','A1_SHADOW'][k],initialization_ms=d.init_ms.value))
        try:
          for i,(p,cp,digest) in enumerate(seq):
            im=api.read(p);h=sha(p);assert digest is None or digest==h
            inputs.append(dict(dataset_id=g,frame_id=i+1,path=str(p),sha256=h,width=im.shape[1],height=im.shape[0]))
            for v,(d0,d1,s1,s2) in engines.items():
                x=run(d0,im,cp,i==0);y=run(d1,im,cp,i==0)
                before=y[3];t=time.perf_counter();shadow=json.loads(a1.R03Observe(d1.handle,s1,i==0));stateonly=json.loads(a1.R03Observe(d1.handle,s2,i==0));diag_ms=(time.perf_counter()-t)*1000
                after=json.loads(a1.CrackV4LastJson(d1.handle))
                oldr=expected[g,v,i+1];r=x[0]
                tip=(r.tip.x,r.tip.y) if r.tip_confirmed else None
                oldtip=(float(oldr['tip_x']),float(oldr['tip_y'])) if oldr['tip_valid']=='1' else None
                check=dict(dataset_id=g,variant_id=v,frame_id=i+1,baseline_reproduced=tip==oldtip and x[3]['status']==oldr['tracking_state'],shadow_equal=normalized(x[3])==normalized(y[3]),shadow_readonly=before==after,sidecars_equal=normalized({k:v for k,v in shadow.items() if k not in ['state_ms','diagnostic_ms']})==normalized({k:v for k,v in stateonly.items() if k not in ['state_ms','diagnostic_ms']}))
                checks.append(check)
                for group,result,side in [('A0_R02',x,None),('A1_SHADOW',y,shadow),('A2_STATE_ONLY',y,stateonly)]:
                    rr,rc,ms,raw,dbg=result;ip=lookup[g,v]
                    coord=[rr.tip.x,rr.tip.y] if rr.tip_confirmed else [None,None]
                    outcoord=side['output'] if group=='A2_STATE_ONLY' else coord
                    row=dict(run_id=OUT.name,group=group,dataset_id=g,variant_id=v,frame_id=i+1,image_sha256=h,image_path=str(p),image_w=im.shape[1],image_h=im.shape[0],build_hash=sha(BUILD/('Release/A0_R02.dll' if group=='A0_R02' else 'Release/A1_SHADOW.dll')),init_p1_x=ip[0][0],init_p1_y=ip[0][1],init_p2_x=ip[1][0],init_p2_y=ip[1][1],current_p1_x=cp[0][0],current_p1_y=cp[0][1],current_p2_x=cp[1][0],current_p2_y=cp[1][1],raw_tip_x=coord[0],raw_tip_y=coord[1],raw_confirmed=rr.tip_confirmed,output_x=outcoord[0],output_y=outcoord[1],source=side['source'] if group=='A2_STATE_ONLY' else ('observed' if rr.tip_confirmed else 'legacy_unconfirmed'),visual_confirmed=int(side['visual_confirmed']) if group=='A2_STATE_ONLY' else rr.tip_confirmed,valid=int(side['valid']) if group=='A2_STATE_ONLY' else rr.tip_confirmed,raw_status=raw['status'],complete_length_valid=rr.length_confirmed,terminal_status=raw['terminal_audit'],processing_ms=ms+(side['state_ms'] if group=='A2_STATE_ONLY' else 0),diagnostic_overhead_ms=diag_ms,roi_mode='SEARCH_ROI',reference_query=int(i==0),return_code=rc)
                    roi=dbg['tip_roi_xywh']
                    for k,val in zip(['x','y','w','h'],roi):row['search_roi_'+k]=val
                    for key in ['state_before','state_after','transition_reason','lock_attempted','lock_accepted','history_written','roi_edge_risk','tip_motion_valid','tip_transform','last_confirmed','last_confirmed_frame','predicted','track_roi','track_roi_unclipped','track_clipped']:
                        row[key]=side.get(key) if side else None
                    rows.append(row)
                snaps.write(json.dumps(dict(dataset_id=g,variant_id=v,frame_id=i+1,input=inputs[-1],init=lookup[g,v],current_points=cp,raw=x[3],raw_debug=x[4],shadow=shadow,stateonly=stateonly),ensure_ascii=False)+'\n')
            if (i+1)%40==0:print(g,i+1,'/',len(seq),flush=True)
          print('completed',g,flush=True)
        finally:
          for d0,d1,s1,s2 in engines.values():d0.close();d1.close();a1.R03DestroyState(s1);a1.R03DestroyState(s2)
        for name,data in [('r03_frame_results.csv',rows),('baseline_shadow_checks.csv',checks),('input_manifest.csv',inputs),('initialization_timings.csv',inits)]:api.csvout(OUT/name,data)
    write('gate01.json',dict(frames=len(checks),baseline_mismatches=sum(not r['baseline_reproduced'] for r in checks),shadow_mismatches=sum(not r['shadow_equal'] for r in checks),mutation_failures=sum(not r['shadow_readonly'] for r in checks),independent_sidecar_failures=sum(not r['sidecars_equal'] for r in checks),scope='pilot continuous R02 windows; not full perturbation acceptance'))
if __name__=='__main__':main()
