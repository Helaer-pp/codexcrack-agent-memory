"""Identity-aware orchestration is outside image-only inference. Labels only in subprocess."""
import argparse,concurrent.futures,collections,json,os,platform,shutil,subprocess,sys,time,traceback
from pathlib import Path
import numpy as np
import cv2
from .algorithm import CONFIG,MODES,detect,evidence
from .common import *
from .baselines import load_baselines
from .render_all import render_frame
from .tests import run_tests
ARTIFACTS=None

def init_worker():
    global ARTIFACTS
    cv2.setNumThreads(1);ARTIFACTS=get(OLD/'artifact_manifest.json')['files']

def source_hashes():
    return {str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sorted(Path(__file__).parent.glob('*')) if p.is_file()}

def check_sources(run):
    if get(Path(run)/'source_hashes.json')['files']!=source_hashes():raise RuntimeError('Frozen source changed; cannot resume this experiment')

def input_check(run,data):
    run=Path(run);target=run/'g0_identity.json'
    if target.exists():return get(target)
    files={}
    for r in data:
        for key,hkey in [('current','image_sha'),('reference','ref_sha'),('point_source','point_source_sha')]:
            if r[key] in files and files[r[key]]!=r[hkey]:raise ValueError('Conflicting input identities')
            files[r[key]]=r[hkey]
    failures=[]
    def check(item):
        p,h=item
        return (p,Path(p).exists() and sha(p)==h)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for p,ok in pool.map(check,files.items()):
            if not ok:failures.append(p)
    baseline=get(OLD/'baseline_identity.json');protected=[]
    for rel,h in baseline['protected'].items():
        p=ROOT/rel
        if not p.exists() or sha(p)!=h:failures.append(str(p))
        else:protected.append(dict(path=rel,sha256=h))
    result=dict(utc=utc(),expected=2647,input_available=len(data) if not failures else None,unique_hashed_files=len(files),failures=failures,protected=protected,historical_source_hashes={rel:sha(ROOT/rel) for rel in ['paired_p1p2_roi_V1_FROZEN.py','research/p1p2_grayref_v2/algorithm.py','research/p1p2_grayref_v2/v2_detector.hpp']},old_manifest_sha=sha(OLD/'experiment_manifest.csv'),old_artifact_manifest_sha=sha(OLD/'artifact_manifest.json'),point_source_limit='CT3 original TXT unavailable; audited historical coordinate CSV retained',all_inputs=list(dict(path=p,sha256=h) for p,h in files.items()))
    put(target,result)
    if failures:raise RuntimeError('G0 failed: '+str(failures))
    csvwrite(run/'input_manifest.csv',data);return result

def write_frame_manifest(d):
    files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(d.iterdir()) if p.is_file() and p.name not in ['frame_manifest.json'] and not p.name.endswith('.partial')}
    r=readgz(d/'result.json.gz')
    put(d/'frame_manifest.json',dict(identity=r['identity'],roi=r['roi'],config_sha=r['config_sha'],git_hash='NOT_A_GIT_REPOSITORY',files=files,coordinate_convention='0-based original-image (x,y), y down; ROI xa:xb and ya:yb half-open; all lengths px',gt_free=True))

def process_frame(job):
    run,row=job;run=Path(run);d=frame_dir(run,row);d.mkdir(parents=True,exist_ok=True);tick=time.perf_counter()
    try:
        if (d/'frame_manifest.json').exists():
            manifest=get(d/'frame_manifest.json');missing=[]
            for name,v in manifest['files'].items():
                p=d/name
                if not p.exists():missing.append(name)
                elif sha(p)!=v['sha256']:raise RuntimeError('Corrupt sealed artifact: '+str(p))
            if not missing:return dict(group=row['group'],frame_id=row['frame_id'],resumed=True)
        else:manifest=None
        core=['result.json.gz','roi_gray.npz','roi_difference.npz','candidate_graphs.npz','roi_difference_metadata.json']
        if any(not(d/f).exists() for f in core):
            C=imread(row['current']);R=imread(row['reference'])
            if sha(row['current'])!=row['image_sha'] or sha(row['reference'])!=row['ref_sha']:raise ValueError('Original image changed')
            if C.shape!=(int(row['height']),int(row['width'])):raise ValueError('Image dimensions changed')
            rp=json.loads(row['reference_points']);cp=json.loads(row['current_points']);t=time.perf_counter()
            a,results,graphs=detect(current_uint8=C,reference_uint8=R,P_ref=rp,P_cur=cp,config=CONFIG);runtime=(time.perf_counter()-t)*1000
            global ARTIFACTS
            if ARTIFACTS is None:init_worker()
            base,oldroi=load_baselines(row,ARTIFACTS)
            if a['roi']!=oldroi:raise ValueError('Unexpected ROI change relative to controlled baseline')
            cfgsha=sha(run/'config_frozen.json');g=a['roi']
            identity={**row,'role':'DEVELOPMENT' if row['group'] in DEV else 'EXPOSED_REGRESSION','git_hash':'NOT_A_GIT_REPOSITORY'}
            record=dict(identity=identity,roi=g,config_sha=cfgsha,results=results,baselines=base,reference_status=a['reference_status'],reference_windows=a['reference_windows'],noise=a['noise'],threshold=a['threshold'],notch=a['notch'],inference_ms=runtime,reference_valid_fraction=float(np.mean(a['diff']['ref_quality_map']>0)),invalid_warp_fraction=float(np.mean(~a['diff']['valid_warp_mask'])),gt_accessed_at_inference=False)
            if (d/'result.json.gz').exists():
                previous=readgz(d/'result.json.gz')
                if previous['results']!=results or previous['roi']!=g:raise RuntimeError('Resume inference not deterministic')
            else:putgz(d/'result.json.gz',record)
            save_npz(d/'roi_gray.npz',raw=a['gray'][0],median3=a['gray'][1],gaussian_light=a['gray'][2],valley_raw=a['valley'][0],valley_median3=a['valley'][1],valley_gaussian_light=a['valley'][2],background=a['background'],reference_unaligned=R[g['ya']:g['yb'],g['xa']:g['xb']],roi=np.asarray([g[k] for k in ['xa','ya','xb','yb']],np.int32))
            save_npz(d/'roi_difference.npz',**a['diff'],roi=np.asarray([g[k] for k in ['xa','ya','xb','yb']],np.int32))
            save_npz(d/'candidate_graphs.npz',**{mode+'__'+key:arr for mode,graph in graphs.items() for key,arr in graph.items()})
            finite=a['diff']['signed_raw'][np.isfinite(a['diff']['signed_raw'])]
            put(d/'roi_difference_metadata.json',dict(identity=identity,roi=g,config_sha=cfgsha,reference_status=a['reference_status'],inference_reference_used=bool(a['diff']['ref_quality_map'].any()),alignment='P1/P2 vertical interpolation displacement; local +/-4 pixel NCC in upper/lower 16x64 material windows; two-sided trust; interpolate residual and median photometric bias',raw='P-only aligned reference float32 - raw current float32',corrected='local aligned reference - current - material-window median offset',invalid='NaN out-of-warp, never negative evidence',windows=a['reference_windows'],display_range=[-CONFIG['display_diff'],CONFIG['display_diff']],invalid_fraction=record['invalid_warp_fraction'],signed_percentiles=np.percentile(finite,[5,50,95]).tolist() if len(finite) else [],numeric_sha=sha(d/'roi_difference.npz'),node_columns=['local_x','local_y','raw_gray','background','raw_depth','half_depth_width_capped_33','noise_MAD','mode_evidence','valid_material'],reference_quality_not_physical_truth=True))
        render_frame(d)
        if manifest:
            for name,v in manifest['files'].items():
                if sha(d/name)!=v['sha256']:raise RuntimeError('Regenerated artifact differs from sealed '+name)
        else:write_frame_manifest(d)
        return dict(group=row['group'],frame_id=row['frame_id'],seconds=round(time.perf_counter()-tick,3))
    except Exception:
        return dict(group=row['group'],frame_id=row['frame_id'],error=traceback.format_exc())

def freeze(run):
    run=Path(run)
    if (run/'source_hashes.json').exists():check_sources(run);return
    put(run/'config_frozen.json',CONFIG)
    put(run/'experiment_plan.json',dict(utc=utc(),default_mode='C_FUSION_RAW',modes=MODES,baselines=['V1_LOCKED','V2_NUMERIC_CONTROL','V2_COMBINED'],counts=GROUPS,development=1565,exposed_regression=1082,visible_denominators=dict(development=76,exposed_regression=35),unknown_labels=9,sequence='all development inference sealed -> separate evaluation -> fixed exposed inference sealed -> separate evaluation',no_validation_tuning=True,no_GT_training=True,primary='public output tip<=10 and observed-only path coverage/precision>=0.8 at10px; all visible denominator',secondary=['tip3/5/10','errors100/500','raw candidate errors','output coverage','conditional error quantiles','path5/10','bridges','reference eligibility','filter preservation'],acceptance='GO only if default improves dev joint and tip10 vs both immutable baselines without increasing >100/500 tails; exposed must not regress joint or tip10; physical identity remains unverified; no production approval',array_resample_seed=73519,resample_per_group=2,display_range=[-40,40],no_visible_crack_FPR='N/A',temporal='OFF',git_hash='NOT_A_GIT_REPOSITORY',direction='+x only',unit_tests='tests/unit_test_results.json',source='source_hashes.json'))
    protocol='''# Frozen image-only protocol

Inputs are current/reference uint8 arrays, independent reference/current P1/P2, exact global config. Keyword/config injection rejected. No identity, label, history, training or GT dependencies. All modes share ROI, connector, rank and stop rules.

ROI geometry deliberately matches immutable V1/V2 including strict upper/lower P bounds and current midline dark-edge xr rule. CT3 outside-ROI labels stay in denominator. No old candidate/gate is reused.

Current V=max positive ((I[y-k]+I[y+k])/2-I), k=3,6,10. Full y/x scan, multiple local maxima, vertical spacing3 and per-column cap12; all pre-cap counts retained. Background uses maximizing flank pair; width measured to half-depth, capped33. Material min(I[y+-10])>100 inside strict ROI; noise=max(1,1.4826*MAD(current-median3) in material); weak=clip(2noise,2,8). No valley>=10 whole-path gate.

F0 raw; F1 median3; F2 Gaussian3x3 sigma0.6. F1/F2 evidence=.5raw+.5filtered (raw always retained). Equal filtering on warped local reference/current before differencing. Out-warp eroded for filtered evidence. Synthetic1px median loss => frozen default F0 regardless group results.

P warp interpolates P1/P2 displacement vertically. Raw signed=aligned reference-current float32; invalid NaN. Local +/-4 pixel translation in two peripheral16x64 material windows, each std>=2, jointly bright fraction>=.5, NCC>=.8, |median bias|<=20. Shift adopted only NCC improvement>.02. Require both windows. Interpolate shifts/bias vertically; q=min NCC, not calibrated probability or physical truth. Same image has no incremental reference use. Raw P-only difference and local corrected difference both saved. Untrusted q0 is unknown, never negative evidence.

Vnorm=clip(V/(3noise+6),0,4); Dnorm likewise positive corrected D. A=Vnorm; B=qDnorm with REF_UNAVAILABLE if no q; C=Vnorm+.35qDnorm, current eligible valleys preserved, explicit fallback when no q. B also uses common current-material and current-negative stop rules; B is evidence ablation, not a visible-crack guarantee.

Adjacent candidates match nearest-y within3 with deterministic tie-breaking; contiguous fragments retained. DAG bridges require supported >=2px fragment ends, gap<=clip(.02ROIwidth,8,24), bounded displacement/slope discrepancy; at most4 incoming links. Each node keeps best cumulative bounded utility for tractable hypothesis construction; final ranking uses length-normalized evidence, saturating support, gap penalty and bounded soft image-only notch hypothesis proximity. At most6 non-identical routes; discarded predecessor alternatives and per-column capacity are explicit limitations, not Oracle completeness. Scores do not certify physical main-crack identity. Automatic left-touch dark component is NOTCH_HYPOTHESIS only. Exact contained fragment routes suppressed, parallel/crossing routes compete; score difference<=.04 -> PATH_AMBIGUOUS.

Observed states inferred from source current/increment evidence; bridge pixels never observed. Independent stop candidates at gap onsets, ends and support drops. Current raw support along path and next24 columns within +/-2px predicted y; measurable fraction>=.65, observable negative>=.8, pre-valley>=weak. Otherwise material absence/occlusion is TIP_UNCERTAIN, not negative. Stop score=negative+relative decay+.2 bounded preceding support, ties>.10px within.08 uncertain. Trusted reference support is reported as separate corroboration; it cannot certify termination. No stop forces last-observed pixel; ROI boundary separately limited. Only PROVISIONAL_TIP publishes tip; raw candidates and paths always retained.

Rendering: actual raw grayscale Z0..255; original x/y coordinates. Max70x40 regular display grid; full-resolution arrays/2D exports and five complete y profiles retained. Signed fixed[-40,40], invalid green. No GT default overlays. All endpoints/array hashes sealed before independent label process. Old baselines replay checked native result+fulltrace, not new implementation executions.
'''
    write_bytes(run/'model_protocol.md',protocol.encode())
    files=source_hashes();put(run/'source_hashes.json',dict(utc=utc(),files=files))
    for rel in files:write_bytes(run/'source_snapshot'/Path(rel).name,(ROOT/rel).read_bytes())

def seal_role(run,data,role):
    run=Path(run);files={}
    for row in data:
        d=frame_dir(run,row)
        for name in ['result.json.gz','candidate_graphs.npz','frame_manifest.json']:
            p=d/name;files[str(p.relative_to(run)).replace('\\','/')]=sha(p)
    target=run/f'inference_frozen_{role}.json'
    if target.exists():
        if get(target)['files']!=files:raise RuntimeError('Frozen inference modified')
    else:put(target,dict(utc=utc(),role=role,frames=len(data),GT_read=False,config_sha=sha(run/'config_frozen.json'),source_hashes_sha=sha(run/'source_hashes.json'),files=files))

def run_role(run,data,workers,role):
    check_sources(run);completed=0;errors=[];tick=time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers,initializer=init_worker) as pool:
        futures=[pool.submit(process_frame,(str(run),r)) for r in data]
        for future in concurrent.futures.as_completed(futures):
            result=future.result();completed+=1
            with open(Path(run)/'progress.jsonl','a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=utc(),role=role,**result),ensure_ascii=False)+'\n')
            if 'error' in result:errors.append(result);print('FRAME_ERROR '+json.dumps(result,ensure_ascii=False),flush=True)
            if completed%20==0 or completed==len(data):print(f'{role}: {completed}/{len(data)}; errors={len(errors)}; elapsed={time.perf_counter()-tick:.1f}s',flush=True)
    if errors:put(Path(run)/f'failures_{role}.json',errors);raise RuntimeError(f'{len(errors)} frames failed')
    seal_role(run,data,role)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);parser.add_argument('--workers',type=int,default=5);parser.add_argument('--smoke-only',action='store_true');args=parser.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum():raise ValueError('Run id must be a simple directory name')
    run=ROOT/'output/experiments'/args.run_id;run.mkdir(parents=True,exist_ok=True);data=safe_manifest(OLD/'experiment_manifest.csv')
    if args.smoke_only:
        put(run/'config_frozen.json',CONFIG);init_worker()
        for g in sorted(DEV):
            group=[r for r in data if r['group']==g];result=process_frame((run,group[len(group)//2]));print(json.dumps(result,ensure_ascii=False),flush=True)
            if 'error' in result:raise RuntimeError('Smoke failed')
        return
    if not(run/'source_hashes.json').exists():
        run_tests(run/'tests');input_check(run,data);freeze(run)
        import scipy,matplotlib,PIL,psutil
        put(run/'environment.json',dict(utc=utc(),python=sys.version,platform=platform.platform(),processor=platform.processor(),cpus=os.cpu_count(),numpy=np.__version__,scipy=scipy.__version__,opencv=cv2.__version__,matplotlib=matplotlib.__version__,pillow=PIL.__version__,memory=psutil.virtual_memory().total,disk_free=shutil.disk_usage(ROOT).free,workers=args.workers))
        write_bytes(run/'reproduce.md',f'Run from project root: powershell -File research/grayref_simplified_evidence_v0/reproduce.ps1 -RunId NEW_RUN -Workers {args.workers}\nOriginal datasets read-only; requires frozen V2 baseline and read-only annotation snapshot for post-freeze evaluation. All dependencies recorded in environment.json. CT3 historical-coordinate limitation retained.\n'.encode())
    else:check_sources(run)
    for role,subset in [('development',[r for r in data if r['group'] in DEV]),('exposed_regression',[r for r in data if r['group'] not in DEV])]:
        run_role(run,subset,args.workers,role)
        subprocess.run([sys.executable,'-m','grayref_simplified_evidence_v0.offline_evaluate','--run',str(run),'--role',role],check=True,cwd=ROOT)
    subprocess.run([sys.executable,'-m','grayref_simplified_evidence_v0.validate_delivery','--run',str(run),'--workers',str(args.workers)],check=True,cwd=ROOT)
    subprocess.run([sys.executable,'-m','grayref_simplified_evidence_v0.reports','--run',str(run)],check=True,cwd=ROOT)
    print('COMPLETED '+str(run),flush=True)

if __name__=='__main__':main()
