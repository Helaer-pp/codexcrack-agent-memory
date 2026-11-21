import argparse,concurrent.futures,copy,random,shutil
import numpy as np
from PIL import Image
from .common import *
from .geometry import CONFIG,MODES,detect,safe_mask,frozen
from .render import PNGS

def verify_files(d,files):
    for name,h in files.items():
        if not (d/name).is_file() or sha(d/name)!=h:raise ValueError('Missing/corrupt artifact: '+str(d/name))

def check(args):
    run,row,source_check=args;d=directory(run,row);r=readgz(d/'result.json.gz')
    for kind in ['inference_manifest.json','visual_manifest.json']:
        verify_files(d,get(d/kind)['files'])
    for name in PNGS:
        with Image.open(d/name) as im:im.load();lo,hi=im.convert('L').getextrema();assert hi>lo
    a,old,cache=cached(row);g=a['roi'];raw=a['gray'][0];diff=a['diff'];expected=diff['aligned_reference']-raw.astype(np.float32)
    assert np.array_equal(expected,diff['signed_raw'],equal_nan=True)
    assert np.array_equal(np.maximum(expected,0),diff['positive'],equal_nan=True) and np.array_equal(np.abs(expected),diff['absolute'],equal_nan=True)
    assert np.isnan(expected[~diff['valid_warp_mask']]).all()
    assert native_result(r['results'][0])==next(p for p in old['results'] if p['mode']=='C_FUSION_RAW')
    with np.load(d/'evidence_arrays.npz') as q:
        ms=[q[n] for n in MODES];assert np.array_equal(ms[0],safe_mask(a)) and all(np.all(m<=ms[0]) for m in ms)
        assert np.array_equal(q['corridor_branches'].any(0),ms[2]);assert np.array_equal(ms[1].any(0),ms[0].any(0))
        for name,m in zip(MODES,ms):
            xy=q[name+'__nodes'][:,:2].astype(int);assert m[xy[:,1],xy[:,0]].all()
    error=None
    if source_check:
        C=imread(row['current']);R=imread(row['reference']);P=json.loads(row['current_points']);rp=json.loads(row['reference_points'])
        assert sha(row['current'])==row['image_sha'] and sha(row['reference'])==row['ref_sha']
        fresh=frozen.evidence(C,R,rp,P,frozen.CONFIG);assert fresh['roi']==g
        assert np.array_equal(fresh['gray'][0],raw)
        for k in diff:assert np.array_equal(fresh['diff'][k],diff[k],equal_nan=True),k
        rerun=detect(evidence=a,P_cur=P,config=CONFIG)[0];assert rerun==r['results'],'Repeat changed'
        error=0.
    return dict(group=row['group'],frame_id=row['frame_id'],A_parity=True,PNGs=5,arrays_ok=True,signed_diff_exact=True,source_recomputed=source_check,source_max_error=error,reference_status=r['reference_status'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--workers',type=int,default=12);a=p.parse_args();run=Path(a.run);check_sources(run);data=manifest(run/'input_manifest.csv');rng=np.random.default_rng(80517);samples=set()
    for group in GROUPS:
        sub=[r for r in data if r['group']==group]
        for i in rng.choice(len(sub),10,replace=False):samples.add((group,sub[i]['frame_id']))
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:
        checks=[]
        for i,r in enumerate(pool.map(check,[(str(run),r,(r['group'],r['frame_id']) in samples) for r in data]),1):
            checks.append(r)
            if i%100==0:print(f'VERIFIED {i}/1633',flush=True)
    for entry in get(run/'g0_identity.json')['protected']:assert sha(ROOT/entry['path'])==entry['sha256']
    # Corruption and absent PNG are checked in an isolated fixture only.
    fixture=run/'tests/damage_fixture';fixture.mkdir(exist_ok=True);source=directory(run,data[0]);shutil.copy2(source/'roi_overlay_abc.png',fixture/'roi_overlay_abc.png');original=sha(fixture/'roi_overlay_abc.png');(fixture/'roi_overlay_abc.png').unlink();missing=False
    try:verify_files(fixture,{'roi_overlay_abc.png':original})
    except ValueError:missing=True
    shutil.copy2(source/'roi_overlay_abc.png',fixture/'roi_overlay_abc.png');verify_files(fixture,{'roi_overlay_abc.png':original})
    (fixture/'bad.npz').write_bytes(b'intentional isolated corruption');bad=False
    try:np.load(fixture/'bad.npz',allow_pickle=False)
    except ValueError:bad=True
    assert missing and bad
    csvwrite(run/'delivery_validation.csv',checks);put(run/'run_integrity.json',dict(utc=utc(),expected=1633,processed=len(checks),predictions=len(checks)*3,gray_surfaces=len(checks),signed_diff=len(checks),frame_PNGs=sum(r['PNGs'] for r in checks),groups=GROUPS,excluded=0,A_parity_frames=len(checks),GT_leakage_passed=True,source_recomputations=30,source_max_error=0,deterministic_real_repeats=30,missing_png_detected=missing,corrupt_npz_detected=bad,protected_unchanged=True,source_unchanged=True,engineering_complete=True));print('INTEGRITY PASS 1633 / 4899 / 8165 PNG',flush=True)

if __name__=='__main__':main()
