"""Reproducible engineering checks, with separately gated real-data replay."""
import argparse,ast,io,unittest,collections
from .common import *
from .pipeline import load_evidence,resultdir,algorithm_hashes,compatible_algorithm_hashes,pointfile,reference
from .engine import Engine
from .features import prepare
from .graph import build_graph
from .config import CONFIG

def engineering(run):
    from . import tests
    cv2.setNumThreads(1);stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    write(run/'reports/synthetic_tests.txt',stream.getvalue());assert result.wasSuccessful()
    forbidden={'open','Path','read_csv','read_text','frame_id','specimen_id','dataset_id','gt','label','filename'};audit=[]
    for name in ['engine.py','features.py','graph.py','config.py']:
        tree=ast.parse((SOURCE/name).read_text(encoding='utf-8'));names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)};args={n.arg for n in ast.walk(tree) if isinstance(n,ast.arg)}
        violation=sorted((names|args)&forbidden);assert not violation,(name,violation);audit.append(dict(file=name,sha=sha(SOURCE/name),forbidden_runtime_names=violation))
    put(run/'reports/engineering_preflight.json',dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),runtime_AST=audit,language='Python only; C++ parity NOT_APPLICABLE',process_interface='image arrays + P1/P2 + prior trusted state; no sample metadata or annotation argument'))
    print('ENGINEERING',result.testsRun,'PASS')

def replay(run,split):
    if split=='LOCKED':check_freeze(run)
    cv2.setNumThreads(1);rs=inventory(run,split);checks=[]
    for group in dict.fromkeys(r['group'] for r in rs):
        group_rows=[r for r in rs if r['group']==group];engine=Engine()
        # Sequential first three frames preserve actual state; compare all native diagnostics.
        for row in group_rows[:3]:
            e,m=load_evidence(framedir(run,row));actual,debug=engine.process_evidence(e);original=readgz(resultdir(run,'FULL',group)/(row['frame_id']+'.json.gz'))
            assert clean(actual)==original['result'];assert clean(engine.state)==original['state_after'];checks.append(dict(group=group,frame_id=row['frame_id'],check='SEQUENCE_REPLAY_ALL_NATIVE_FIELDS',passed=True))
        for index in np.linspace(0,len(group_rows)-1,10,dtype=int):
            row=group_rows[index];e,m=load_evidence(framedir(run,row));p=parse_points(row['point_source']);k=int(row['tracking_num']);fresh=prepare(imread(row['current']),p[k],imread(row['reference']),p[0],imread(row['previous_actual']) if k else None,p[k-1] if k else None,config=CONFIG)
            fresh['edges'],fresh['graph_eligible'],fresh['graph_info']=build_graph(fresh,CONFIG)
            layers=0
            for name,value in fresh.items():
                if isinstance(value,np.ndarray):assert np.array_equal(value,e[name],equal_nan=True),name;layers+=1
                elif name in ['fixed','prev']:
                    for q,a in value.items():assert np.array_equal(a,e[name][q],equal_nan=True),(name,q);layers+=1
                else:assert clean(value)==clean(e[name]),name
            checks.append(dict(group=group,frame_id=row['frame_id'],check='ORIGINAL_SOURCE_ALL_FEATURES_EXACT',layers=layers,passed=True))
    csvwrite(run/'diagnostics'/f'{split}_determinism_and_source.csv',checks);print('REPLAY',split,len(checks),'PASS')

def backend(run):
    """Reproducible pre-label equivalence gate for scalar and batch execution."""
    registry=run/'manifests/DEV_execution_backend_registration.json'
    if registry.exists():
        registered=get(registry)
        assert registered['batch']==algorithm_hashes()
        assert sha(run/'qa/batch_backend_contract.json')==registered['contract_sha']
        assert sha(run/'qa/batch_backend_native_parity.csv')==registered['parity_csv_sha']
        print('BACKEND EQUIVALENCE ALREADY REGISTERED',registered['native_parity_cases']);return
    assert not (run/'offline_evaluation/DEV_label_access_begin.json').exists()
    from .engine_fast import Engine as BatchEngine
    from .config import ARMS
    from . import tests
    import time,copy
    cv2.setNumThreads(1);previous_engine=tests.Engine;tests.Engine=BatchEngine;stream=io.StringIO()
    try:test_result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    finally:tests.Engine=previous_engine
    write(run/'qa/batch_backend_synthetic_tests.txt',stream.getvalue());assert test_result.wasSuccessful()
    tree=ast.parse((SOURCE/'engine_fast.py').read_text(encoding='utf-8'))
    names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)}|{n.arg for n in ast.walk(tree) if isinstance(n,ast.arg)}
    assert not names&{'open','Path','read_csv','read_text','frame_id','specimen_id','dataset_id','gt','label','filename'}
    jobs=[(arm,group,fid) for arm in ARMS for group,ids in [('group_a',[1,2,3,100,230,300]),('three_point_bend',[1,2,3,50,260,520])] for fid in ids]+[('FULL','group_a',345)]
    records=[]
    for arm,group,fid in jobs:
        folder=resultdir(run,arm,group);old=readgz(folder/(str(fid)+'.json.gz'));e,_=load_evidence(run/'evidence'/group/str(fid))
        state=readgz(folder/(str(fid-1)+'.json.gz'))['state_after'] if fid>1 else Engine().state
        batch=BatchEngine(arm=arm);batch.state=copy.deepcopy(state)
        started=time.perf_counter();actual,debug=batch.process_evidence(e);elapsed=time.perf_counter()-started
        assert clean(actual)==old['result'] and clean(batch.state)==old['state_after']
        with np.load(folder/(str(fid)+'_debug.npz')) as z:
            assert np.array_equal(debug['mask'],z['mask']) and np.array_equal(debug['segment_outcomes'],z['segment_outcomes'])
        assert clean(debug['lineage'])==readgz(folder/(str(fid)+'_lineage.json.gz'))
        original_seconds=old['engine_seconds']
        if 'engine_fast.py' in old['algorithm']:
            scalar=Engine(arm=arm);scalar.state=copy.deepcopy(state);started=time.perf_counter();expected,scalar_debug=scalar.process_evidence(e);original_seconds=time.perf_counter()-started
            assert clean(expected)==clean(actual) and clean(scalar.state)==clean(batch.state)
            assert clean(scalar_debug['lineage'])==clean(debug['lineage'])
            assert np.array_equal(scalar_debug['mask'],debug['mask']) and np.array_equal(scalar_debug['segment_outcomes'],debug['segment_outcomes'])
        records.append(dict(arm=arm,group=group,frame_id=fid,all_native_result_state_debug_lineage_exact=True,original_seconds=original_seconds,batch_seconds=elapsed,labels_used=False))
        if len(records)%10==0:print('BACKEND PARITY',len(records),len(jobs),flush=True)
    csvwrite(run/'qa/batch_backend_native_parity.csv',records)
    put(run/'qa/batch_backend_contract.json',dict(native_cases=len(records),synthetic_tests=test_result.testsRun,failures=0,errors=0,labels_used=False,source_sha=sha(SOURCE/'engine_fast.py'),original_source_sha=sha(SOURCE/'engine.py'),all_native_fields_and_lineage_exact=True,bounds='At most max_candidates * 63 sampled points, one KD-tree queried at a time; no pairwise distance matrix'))
    current=algorithm_hashes()
    put(registry,dict(time=utc(),original={k:v for k,v in current.items() if k!='engine_fast.py'},batch=current,contract_sha=sha(run/'qa/batch_backend_contract.json'),parity_csv_sha=sha(run/'qa/batch_backend_native_parity.csv'),native_parity_cases=len(records),synthetic_tests=test_result.testsRun,parameter_changes=False,original_modules_changed=False,labels_opened=False,semantics='Identical sampled integer pixels, KDTree k1 distances, Boolean mean threshold and OR; batched independent queries'))
    print('BACKEND EQUIVALENCE PASS',len(records),flush=True)

def integrity(run):
    check_freeze(run);rs=inventory(run);checks=[]
    evidence_seals={**get(run/'manifests/DEV_evidence_seal.json')['metadata'],**get(run/'manifests/LOCKED_evidence_seal.json')['metadata']}
    for i,row in enumerate(rs):
        folder=framedir(run,row);e,m=load_evidence(folder);assert sha(folder/'arrays.npz')==m['arrays_sha'];assert compatible_algorithm_hashes(m['algorithm'])
        assert sha(folder/'metadata.json')==evidence_seals[str(folder.relative_to(run))]
        native=readgz(resultdir(run,'FULL',row['group'])/(row['frame_id']+'.json.gz'));r=native['result'];assert compatible_algorithm_hashes(native['algorithm'])
        if row['role']=='LOCKED':assert native['algorithm']==algorithm_hashes() and m['algorithm']==algorithm_hashes()
        assert (r['status']=='VALID')==(r['tip'] is not None)
        if r['tip']:
            assert r['tip'][0]==max(p['endpoint'][0] for p in r['candidates'] if p['verified']);assert not r['budget']['exhausted']
        for channel in ['fixed','prev']:
            d=e[channel];finite=np.isfinite(d['aligned']);assert np.array_equal(d['signed'][finite],(d['aligned']-e['raw'])[finite]);assert np.isfinite(d['signed'][d['valid']]).all()
        view=run/'galleries/frames'/row['group']/row['frame_id'];assert (view/'done.json').exists()
        for p in view.glob('*.png'):
            from PIL import Image
            with Image.open(p) as im:im.verify()
        with Image.open(view/'raw.png') as im:assert np.array_equal(np.asarray(im),e['raw'])
        for channel in ['fixed','prev']:
            with Image.open(view/(channel+'_valid.png')) as im:assert np.array_equal(np.asarray(im),e[channel]['valid'].astype(np.uint8)*255)
        assert (view/'audit.js').exists()
        checks.append(dict(group=row['group'],frame_id=row['frame_id'],arrays_sha_ok=True,output_invariant=True,signed_masks_ok=True,viewer_pngs_ok=True))
        if (i+1)%100==0:print('INTEGRITY',i+1,len(rs),flush=True)
    csvwrite(run/'diagnostics/all_frame_integrity.csv',checks)
    protected=get(run/'manifests/baseline_protection_manifest.json');print('PROTECTION_SCHEMA',list(protected)[:10],flush=True)
    # Manifest may contain a wrapped file map; inventory module defines its exact schema.
    files=protected.get('files',protected);changed=[]
    for rel,h in files.items():
        expected=h['sha256'] if isinstance(h,dict) and 'sha256' in h else h
        p=ROOT/rel
        if not p.is_file() or sha(p)!=expected:changed.append(rel)
    put(run/'reports/final_integrity.json',dict(frames=len(checks),protected_files=len(files),protected_changed=changed,source_frozen=check_freeze(run)['source']==source_hashes(),production_replaced=False,data_isolation_audit='FAIL_WITH_DISCLOSED_DEVIATION',protocol_deviation=sha(run/'manifests/protocol_deviation_legacy_project_check.json')))
    assert not changed;print('FINAL INTEGRITY PASS',len(checks),len(files),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['engineering','backend','replay','integrity']);ap.add_argument('--run',required=True);ap.add_argument('--split',choices=['DEV','LOCKED'],default='DEV');a=ap.parse_args();run=Path(a.run).resolve()
    if a.action=='engineering':engineering(run)
    elif a.action=='backend':backend(run)
    elif a.action=='replay':replay(run,a.split)
    else:integrity(run)
