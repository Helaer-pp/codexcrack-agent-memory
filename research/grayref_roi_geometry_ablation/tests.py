import copy,json,time
import numpy as np
from .geometry import CONFIG,MODES,detect,masks,MASKED_RUN,safe_mask,frozen
from .common import *

def synthetic():
    C=np.full((220,700),180,np.uint8);C[108:110,68:240]=65;C[108:110,246:410]=65;C[124:126,68:400]=80
    P=[[65,50],[65,170]];a=frozen.evidence(C,C,P,P,frozen.CONFIG)
    return a,P

def run_tests(run):
    a,P=synthetic();result,graphs,ms,branches,control,_=detect(evidence=a,P_cur=P,config=CONFIG)
    original,og=frozen.run_mode(a,'C_FUSION_RAW',frozen.CONFIG)
    assert native_result(result[0])==original
    full,fg=MASKED_RUN(a,'C_FUSION_RAW',frozen.CONFIG,safe_mask(a));assert full==original
    for k in og:assert np.array_equal(og[k],fg[k])
    assert all(np.all(m<=ms[0]) for m in ms) and ms[1].sum()<ms[0].sum() and 0<ms[2].sum()<ms[0].sum()
    assert ms[1].any(0).sum()==ms[0].any(0).sum() and np.array_equal(branches.any(0),ms[2])
    assert len(control['seed_centers'])>=2 and control['expansions']>0
    again=detect(evidence=a,P_cur=P,config=CONFIG);assert again[0]==result
    rejected=[]
    for key in ['gt_path','oracle_tip','manual_tip','label_file','frame_id','specimen']:
        try:detect(evidence=a,P_cur=P,config=CONFIG,**{key:[]})
        except TypeError:rejected.append(key)
    assert len(rejected)==6
    try:masks(evidence=a,P_cur=P,config={**CONFIG,'manual_tip':[1,1]})
    except ValueError:pass
    else:raise AssertionError('Config injection')
    np.testing.assert_array_equal(a['diff']['signed_raw'],np.zeros_like(a['gray'][0],dtype=np.float32))
    tests=dict(A_exact_synthetic=True,all_safe_mask_exact=True,deterministic=True,strict_injection_rejected=rejected,B_full_x_preserved=True,C_nonrectangular_branches_saved=True,mask_only_adapter_AST_exact=True,GT_read=False)
    # Predeclared GROUP_A middle input: image-only fresh evidence versus immutable cache.
    row=manifest()[275];assert row['group']=='group_a'
    cached_a,old,source=cached(row);C=imread(row['current']);R=imread(row['reference']);P=json.loads(row['current_points']);rp=json.loads(row['reference_points'])
    fresh=frozen.evidence(C,R,rp,P,frozen.CONFIG)
    assert fresh['roi']==cached_a['roi'] and fresh['threshold']==cached_a['threshold'] and fresh['notch']==cached_a['notch']
    for k in fresh['diff']:assert np.array_equal(fresh['diff'][k],cached_a['diff'][k],equal_nan=True),k
    for key in ['material','background']:assert np.array_equal(fresh[key],cached_a[key])
    assert np.array_equal(fresh['valley'][0],cached_a['valley'][0])
    rr,gg,mm,bb,cc,tt=detect(evidence=cached_a,P_cur=P,config=CONFIG)
    expected=next(r for r in old['results'] if r['mode']=='C_FUSION_RAW');assert native_result(rr[0])==expected
    rr2=detect(evidence=cached_a,P_cur=P,config=CONFIG)[0];assert rr2==rr
    tests.update(real_fresh_cache_arrays_exact=True,real_A_trace_exact=True,real_repeat_exact=True,real_no_GT_frame=dict(group=row['group'],frame_id=row['frame_id']),search_pixels=[int(m.sum()) for m in mm],states=[r['output_state'] for r in rr])
    put(Path(run)/'tests/results.json',tests);print('PRELABEL TESTS '+json.dumps(tests),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);run_tests(p.parse_args().run)
