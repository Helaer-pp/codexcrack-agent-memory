"""Role-gated IO and deterministic sequence jobs. No annotation imports."""
import argparse,concurrent.futures as cf,time,traceback,json,os
from functools import lru_cache
from pathlib import Path
import cv2,numpy as np
from .common import *
from .config import CONFIG,ARMS,digest
from .features import prepare,ordered_points
from .graph import build_graph
from .engine_fast import Engine

def algorithm_hashes():
    return {n:sha(SOURCE/n) for n in ['config.py','features.py','graph.py','engine.py','engine_fast.py']}

def compatible_algorithm_hashes(record):
    current=algorithm_hashes()
    original={k:v for k,v in current.items() if k!='engine_fast.py'}
    # Preserve original scalar results and their exact source provenance. The new
    # backend only batches identical Boolean history-support queries; its full
    # native parity audit is registered before any new predictions are written.
    return record==current or record==original

@lru_cache(4)
def pointfile(path):return parse_points(path)
@lru_cache(2)
def reference(path):return imread(path)

def save_evidence(folder,e,extra):
    folder.mkdir(parents=True,exist_ok=True);arrays={};meta={}
    for k,v in e.items():
        if isinstance(v,np.ndarray):arrays[k]=v
        elif k in ['fixed','prev']:
            for key,value in v.items():arrays[k+'__'+key]=value
        else:meta[k]=v
    arrays['cyclic']=np.asarray(meta.pop('cyclic'),bool)
    assert not (folder/'arrays.npz').exists()
    np.savez_compressed(folder/'arrays.npz',**arrays)
    put(folder/'metadata.json',dict(evidence=meta,**extra,arrays_sha=sha(folder/'arrays.npz')))

def load_evidence(folder):
    m=get(folder/'metadata.json');e=m['evidence'];e['fixed']={};e['prev']={}
    with np.load(folder/'arrays.npz',allow_pickle=False) as z:
        for k in z.files:
            if '__' in k:a,b=k.split('__');e[a][b]=z[k]
            else:e[k]=z[k]
    return e,m

def prepare_one(args):
    run,row=args;cv2.setNumThreads(1);folder=framedir(run,row)
    if (folder/'metadata.json').exists():
        m=get(folder/'metadata.json');assert compatible_algorithm_hashes(m['algorithm']);return row['group'],row['frame_id'],'CACHED'
    p=pointfile(row['point_source']);k=int(row['tracking_num']);t=time.perf_counter()
    assert sha(row['point_source'])==row['point_source_sha']
    assert sha(row['current'])==row['image_sha'];assert sha(row['reference'])==row['ref_sha']
    current=imread(row['current']);assert current.shape==(int(row['height']),int(row['width']))
    assert ordered_points(p[k],current.shape) is not None,'Invalid real P points: explicit degraded adapter required'
    previous=imread(row['previous_actual']) if row['previous_actual'] else None
    e=prepare(current,p[k],reference(row['reference']),p[0],previous,p[k-1] if k else None,config=CONFIG)
    e['edges'],e['graph_eligible'],e['graph_info']=build_graph(e,CONFIG)
    elapsed=time.perf_counter()-t
    save_evidence(folder,e,dict(input=row,current_points=p[k],fixed_points=p[0],previous_points=p[k-1] if k else None,algorithm=algorithm_hashes(),prepare_seconds=elapsed,created=utc()))
    return row['group'],row['frame_id'],'CREATED'

def resultdir(run,arm,group):return Path(run)/'raw_inference'/arm/group

def sequence(args):
    run,arm,group,rs=args;cv2.setNumThreads(1);engine=Engine(arm=arm);out=resultdir(run,arm,group);out.mkdir(parents=True,exist_ok=True);summary=[]
    if (out/'seal.json').exists():
        seal=get(out/'seal.json');assert compatible_algorithm_hashes(seal['algorithm']) and seal['frames']==len(rs)
        return arm,group,len(rs)
    for idx,row in enumerate(rs):
        target=out/(row['frame_id']+'.json.gz')
        if target.exists():
            existing=readgz(target);assert compatible_algorithm_hashes(existing['algorithm']);engine.state=existing['state_after'];r=existing['result'];elapsed=existing['engine_seconds'];prep=existing['prepare_seconds'];frame_algorithm=existing['algorithm']
        else:
            e,m=load_evidence(framedir(run,row));assert compatible_algorithm_hashes(m['algorithm']);t=time.perf_counter();r,d=engine.process_evidence(e);elapsed=time.perf_counter()-t;prep=m['prepare_seconds'];frame_algorithm=algorithm_hashes()
            np.savez_compressed(out/(row['frame_id']+'_debug.npz'),mask=d['mask'],segment_outcomes=d['segment_outcomes'])
            putgz(out/(row['frame_id']+'_lineage.json.gz'),d['lineage'])
            putgz(target,dict(input=row,algorithm=frame_algorithm,result=r,state_after=engine.state,engine_seconds=elapsed,prepare_seconds=prep,evidence=str(framedir(run,row).relative_to(run)).replace('\\','/')))
        summary.append(dict(group=group,frame_id=row['frame_id'],tracking_num=row['tracking_num'],role=row['role'],arm=arm,status=r['status'],tip_x=r['tip'][0] if r['tip'] else None,tip_y=r['tip'][1] if r['tip'] else None,failure=r['failure_reason'],budget=r['budget']['exhausted'],candidates=len(r['candidates']),valid_candidates=sum(p['verified'] for p in r['candidates']),tracks=len(r['tracks']),main_track=r['main_track_id'],selected_track=r['selected_track_id'],fixed_valid_fraction=r['reference_info']['fixed']['valid_fraction'],prev_valid_fraction=r['reference_info']['prev']['valid_fraction'],jump_rechecks=len(r['rechecks']),engine_seconds=elapsed,prepare_seconds=prep))
        summary[-1]['engine_backend']='BATCH_EQUIVALENT' if 'engine_fast.py' in frame_algorithm else 'ORIGINAL_SCALAR'
        if (idx+1)%100==0:print(f'{arm} {group} {idx+1}/{len(rs)}',flush=True)
    csvwrite(out/'summary.csv',summary)
    files={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='seal.json'}
    put(out/'seal.json',dict(algorithm=algorithm_hashes(),frames=len(rs),files=files))
    return arm,group,len(rs)

def gate(run,split):
    if split=='LOCKED':
        check_freeze(run)
        assert (Path(run)/'manifests/DEV_inference_seal.json').exists()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','infer','freeze']);ap.add_argument('--run',required=True);ap.add_argument('--split',choices=['DEV','LOCKED'],default='DEV');ap.add_argument('--group',choices=list(GROUPS));ap.add_argument('--arms',choices=list(ARMS),nargs='+');ap.add_argument('--workers',type=int,default=6);a=ap.parse_args();run=Path(a.run).resolve();assert run.is_relative_to(ROOT/'output')
    if a.action=='freeze':
        dev=get(run/'manifests/DEV_inference_seal.json');assert len(dev['jobs'])==22
        assert (run/'offline_evaluation/DEV_metrics.csv').exists()
        assert (run/'galleries/DEV_render_seal.json').exists()
        assert get(run/'galleries/DEV_render_seal.json')['frames']==1071
        assert get(run/'galleries/DEV_identity_audit_seal.json')['frames']==1071
        assert get(run/'reports/engineering_preflight.json')['failures']==0
        assert len(rows(run/'diagnostics/DEV_determinism_and_source.csv'))==26
        assert (run/'reports/DEVELOPMENT_REPORT.md').exists() and (run/'reports/ABLATION_REPORT.md').exists()
        backend=get(run/'manifests/DEV_execution_backend_registration.json');assert backend['batch']==algorithm_hashes() and not backend['parameter_changes']
        assert sha(run/'qa/batch_backend_contract.json')==backend['contract_sha']
        assert sha(run/'qa/batch_backend_native_parity.csv')==backend['parity_csv_sha']
        assert backend['native_parity_cases']==133
        put(run/'manifests/prevalidation_freeze.json',dict(time=utc(),source=source_hashes(),execution_backend=sha(run/'manifests/DEV_execution_backend_registration.json'),config=CONFIG,config_sha=digest(CONFIG),arms=ARMS,DEV_seal=sha(run/'manifests/DEV_inference_seal.json'),DEV_evidence=sha(run/'manifests/DEV_evidence_seal.json'),DEV_viewer=sha(run/'galleries/DEV_identity_audit_seal.json'),environment=sha(run/'manifests/environment.json'),dependencies=sha(run/'manifests/dependency_versions.json'),video_toolchain=sha(run/'manifests/video_toolchain.json'),protocol=sha(run/'manifests/task_protocol.json'),development_metrics=sha(run/'offline_evaluation/DEV_metrics.csv'),locked_runs_allowed=1,protocol_deviation=sha(run/'manifests/protocol_deviation_legacy_project_check.json'),data_isolation_audit='FAIL_WITH_DISCLOSED_DEVIATION',validation_interpretation='POST_FREEZE_EXPOSED_REGRESSION_WITH_PRE_FREEZE_LEGACY_CHECK_DEVIATION'))
        print('PREVALIDATION FROZEN',flush=True);return
    gate(run,a.split);rs=inventory(run,a.split)
    if a.group:
        assert a.split=='DEV' and a.action=='infer';rs=[r for r in rs if r['group']==a.group];assert rs
    if a.arms:assert a.split=='DEV' and a.action=='infer' and a.group and len(a.arms)==len(set(a.arms))
    if a.action=='prepare':
        put(run/'manifests'/f'{a.split}_algorithm_registration.json',dict(algorithm=algorithm_hashes(),config=CONFIG,arms=ARMS,policy='NO_LABEL_PARAMETER_SEARCH; annotations offline comparison only'))
        with cf.ProcessPoolExecutor(a.workers) as pool:
            for i,item in enumerate(pool.map(prepare_one,[(run,r) for r in rs],chunksize=1)):
                if (i+1)%25==0:print('PREPARE',a.split,i+1,len(rs),item,flush=True)
        put(run/'manifests'/f'{a.split}_evidence_seal.json',dict(algorithm=algorithm_hashes(),frames=len(rs),metadata={str(framedir(run,r).relative_to(run)):sha(framedir(run,r)/'metadata.json') for r in rs}))
    else:
        if a.split=='LOCKED':
            assert not (run/'manifests/LOCKED_inference_seal.json').exists(),'One locked sequence only'
            if not (run/'manifests/LOCKED_started.json').exists():put(run/'manifests/LOCKED_started.json',dict(time=utc(),freeze=sha(run/'manifests/prevalidation_freeze.json')))
        arms=(a.arms or list(ARMS)) if a.split=='DEV' else ['FULL'];jobs=[(run,arm,g,[r for r in rs if r['group']==g]) for arm in arms for g in dict.fromkeys(r['group'] for r in rs)]
        with cf.ProcessPoolExecutor(a.workers) as pool:
            for result in pool.map(sequence,jobs):print('FINISHED',result,flush=True)
        sealname=a.split+('_'+a.group if a.group else '')+('_subset_'+'_'.join(arms) if a.arms else '')+'_inference_seal.json'
        put(run/'manifests'/sealname,dict(algorithm=algorithm_hashes(),jobs={arm+'/'+g:sha(resultdir(run,arm,g)/'seal.json') for _,arm,g,_ in jobs},frames=len(rs),predictions=len(rs)*len(arms)))

if __name__=='__main__':main()
