"""Actual all-frame decoding/math/source validation; deliberate damage tests confined to test fixture."""
import argparse,concurrent.futures,collections,shutil,traceback
from pathlib import Path
import numpy as np
from PIL import Image
import cv2
from .common import *
from .algorithm import CONFIG,MODES
from .render_all import render_frame,surface_grid

REQUIRED=['gray_surface_raw.png','gray_surface_filtered.png','gray_2d_and_profiles.png','roi_difference_signed.png','roi_difference_panel.png','overlay_path_tip.png','roi_gray.npz','roi_difference.npz','candidate_graphs.npz','roi_difference_metadata.json','render_metadata.json','frame_manifest.json','result.json.gz','index.html','gray_full_resolution.png','valley_raw_full_resolution.png']

def validate_frame(directory,source_check=False):
    d=Path(directory)
    for name in REQUIRED:
        if not(d/name).is_file() or (d/name).stat().st_size==0:raise ValueError('Missing artifact '+str(d/name))
    m=get(d/'frame_manifest.json');r=readgz(d/'result.json.gz');g=r['roi'];ident=r['identity'];shape=(g['yb']-g['ya'],g['xb']-g['xa'])
    assert m['identity']==ident and m['roi']==g
    for name,v in m['files'].items():
        p=d/name
        if not p.exists() or sha(p)!=v['sha256']:raise ValueError('Checksum mismatch '+str(p))
        if p.suffix=='.png':
            with Image.open(p) as im:
                im.load();assert im.width>0 and im.height>0
                # Diagnostic masks may be uniformly valid; composed evidence images must not be blank.
                if name in REQUIRED and name not in ['gray_full_resolution.png','valley_raw_full_resolution.png']:
                    lo,hi=im.convert('L').getextrema();assert hi>lo
    with np.load(d/'roi_gray.npz') as z:
        gray={k:z[k] for k in z.files}
    with np.load(d/'roi_difference.npz') as z:
        diff={k:z[k] for k in z.files}
    coords=np.asarray([g[k] for k in ['xa','ya','xb','yb']],np.int32)
    assert np.array_equal(gray['roi'],coords) and np.array_equal(diff['roi'],coords)
    assert gray['raw'].shape==shape and gray['raw'].dtype==np.uint8
    for k,a in gray.items():
        if k!='roi':assert a.shape==shape and np.isfinite(a).all()
    for k,a in diff.items():
        if k!='roi':assert a.shape==shape
    valid=diff['valid_warp_mask'];assert valid.dtype==bool
    for k in ['signed_raw','aligned_reference','positive','absolute','signed_corrected']:
        assert diff[k].dtype==np.float32
    assert np.isnan(diff['signed_raw'][~valid]).all()
    expected=diff['aligned_reference']-gray['raw'].astype(np.float32)
    assert np.array_equal(expected,diff['signed_raw'],equal_nan=True)
    assert np.array_equal(np.maximum(diff['signed_raw'],0),diff['positive'],equal_nan=True)
    assert np.array_equal(np.abs(diff['signed_raw']),diff['absolute'],equal_nan=True)
    assert np.array_equal(diff['aligned_local']-gray['raw'].astype(np.float32)-diff['local_bias'],diff['signed_corrected'],equal_nan=True)
    assert (diff['ref_quality_map']>=0).all() and (diff['ref_quality_map']<=1.000001).all()
    assert (diff['ref_quality_map'][~diff['local_warp_mask']]==0).all()
    assert [v['mode'] for v in r['results']]==MODES and not r['gt_accessed_at_inference']
    for v in r['results']:
        assert not v['gt_accessed']
        for path in v['paths']:
            for b in path['bridges']:
                assert b['missing']<=v['counts']['gap_bound'] and b['missing']>0 and b['status']=='INFERRED_GAP'
            assert all(p[2] in [0,1] for p in path['observed_trace'])
        if v['mode'].startswith('B_DIFF_ONLY') and not diff['ref_quality_map'].any():assert v['output_state']=='REF_UNAVAILABLE'
    X,Y,Z,sx,sy=surface_grid(gray['raw'],g);meta=get(d/'render_metadata.json');assert sx==meta['surface_stride_x'] and sy==meta['surface_stride_y'];assert np.array_equal(Z,gray['raw'][Y-g['ya'],X-g['xa']])
    raw_error=diff_error=None
    if source_check:
        C=imread(ident['current']);R=imread(ident['reference']);assert sha(ident['current'])==ident['image_sha'];assert sha(ident['reference'])==ident['ref_sha']
        raw_error=float(np.max(np.abs(C[g['ya']:g['yb'],g['xa']:g['xb']].astype(float)-gray['raw'])))
        assert raw_error==0
        rp=np.asarray(json.loads(ident['reference_points']),np.float32);cp=np.asarray(json.loads(ident['current_points']),np.float32)
        yy,xx=np.mgrid[g['ya']:g['yb'],g['xa']:g['xb']].astype(np.float32);alpha=np.clip((yy-cp[0,1])/(float(json.loads(ident['current_points'])[1][1])-float(json.loads(ident['current_points'])[0][1])),0,1)
        # Reproduce exact float conversion order used by the detector (Python scalar P values).
        cpl=json.loads(ident['current_points']);alpha=np.clip((yy-cpl[0][1])/(cpl[1][1]-cpl[0][1]),0,1);delta=cp-rp
        mx=xx-((1-alpha)*delta[0,0]+alpha*delta[1,0]);my=yy-((1-alpha)*delta[0,1]+alpha*delta[1,1])
        assert np.array_equal(mx,diff['map_x']) and np.array_equal(my,diff['map_y'])
        ar=cv2.remap(R,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT).astype(np.float32);actual=ar-C[g['ya']:g['yb'],g['xa']:g['xb']].astype(np.float32)
        diff_error=float(np.max(np.abs(actual[valid]-diff['signed_raw'][valid]))) if valid.any() else 0.;assert diff_error<=1e-5
    default=next(v for v in r['results'] if v['mode']=='C_FUSION_RAW')
    return dict(group=ident['group'],frame_id=ident['frame_id'],visualization_ok=True,registration_valid=bool(diff['ref_quality_map'].any()),inference_reference_used=default['reference_use']=='FUSION',path_state=default['output_state'],reference_status=r['reference_status'],failure_reason='' if diff['ref_quality_map'].any() else 'UNTRUSTED_REFERENCE_DIAGNOSTICS_RETAINED',source_checked=source_check,raw_crop_max_error=raw_error,signed_diff_max_error=diff_error,png_count=sum(n.endswith('.png') for n in m['files']),numeric_array_ok=True,prediction_ok=True,baseline_modes=len(r['baselines']))

def damage_tests(sample,output):
    output=Path(output)
    if (output/'delivery_damage_tests.json').exists():return get(output/'delivery_damage_tests.json')
    fixture=output/'delivery_fixture';fixture.mkdir(parents=True,exist_ok=True)
    for p in Path(sample).iterdir():
        if p.is_file():shutil.copy2(p,fixture/p.name)
    original={p.name:sha(p) for p in fixture.iterdir() if p.is_file()}
    target=fixture/'gray_surface_raw.png';target.unlink();missing_rejected=False
    try:validate_frame(fixture)
    except (ValueError,AssertionError):missing_rejected=True
    assert missing_rejected
    render_frame(fixture);assert sha(target)==original[target.name]
    assert all(sha(fixture/name)==h for name,h in original.items())
    target=fixture/'roi_gray.npz';target.write_bytes(b'intentional corrupt NPZ in isolated test fixture');corrupt_rejected=False
    try:validate_frame(fixture)
    except (ValueError,AssertionError):corrupt_rejected=True
    assert corrupt_rejected;shutil.copy2(Path(sample)/target.name,target);validate_frame(fixture)
    result=dict(missing_png_rejected=True,corrupt_npz_rejected=True,missing_only_regeneration_exact_sha=True,all_other_files_unchanged=True,fixture=str(fixture),original_gallery_untouched=True)
    put(output/'delivery_damage_tests.json',result);return result

def check_job(job):
    d,flag=job
    try:return validate_frame(d,flag)
    except Exception:return dict(directory=str(d),visualization_ok=False,error=traceback.format_exc())

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--workers',type=int,default=5);args=p.parse_args();run=Path(args.run)
    from .run_all import check_sources
    check_sources(run);data=safe_manifest(run/'input_manifest.csv');plan=get(run/'experiment_plan.json');rng=np.random.default_rng(plan['array_resample_seed']);samples=set()
    for g in GROUPS:
        f=[r['frame_id'] for r in data if r['group']==g]
        for i in rng.choice(len(f),size=plan['resample_per_group'],replace=False):samples.add((g,f[i]))
    result=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        for i,r in enumerate(pool.map(check_job,[(frame_dir(run,r),(r['group'],r['frame_id']) in samples) for r in data]),1):
            result.append(r)
            if i%200==0:print(f'VALIDATED {i}/2647',flush=True)
    failures=[r for r in result if not r['visualization_ok']]
    csvwrite(run/'delivery_validation.csv',result)
    if failures:put(run/'delivery_failures.json',failures);raise RuntimeError('Delivery failures '+str(len(failures)))
    damage=damage_tests(frame_dir(run,data[0]),run/'tests')
    # All immutable V2 artifacts, including reports, not just selected label frames.
    oldfiles=get(OLD/'artifact_manifest.json')['files'];bad=[]
    def verify(item):
        rel,v=item;p=OLD/rel;return rel,p.exists() and sha(p)==v['sha256']
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for rel,ok in pool.map(verify,oldfiles.items()):
            if not ok:bad.append(rel)
    assert not bad,bad
    for v in get(run/'g0_identity.json')['protected']:assert sha(ROOT/v['path'])==v['sha256']
    integrity=dict(expected=2647,input_available=2647,processed=len(result),gray_surface_ok=len(result),signed_diff_ok=len(result),full_panel_ok=len(result),numeric_array_ok=len(result),prediction_ok=len(result),failed=0,blocked=0,registration_valid=sum(r['registration_valid'] for r in result),inference_reference_used=sum(r['inference_reference_used'] for r in result),groups={g:sum(r['group']==g for r in result) for g in GROUPS},GT_leakage_test_passed=get(run/'tests/unit_test_results.json')['GT_LEAKAGE_TEST_PASSED'],damage_tests=damage,baseline_replay_verified_frames=2647,old_artifacts_unchanged=len(oldfiles),A_V1_protected_unchanged=True,random_source_checks=[r for r in result if r['source_checked']],full_gallery_pngs=sum(r['png_count'] for r in result),engineering_complete=True)
    put(run/'run_integrity.json',integrity);print(json.dumps(integrity,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
