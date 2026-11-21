"""Operator/safety tests; synthetic examples never count as real accuracy."""
import copy,json,subprocess,sys
from pathlib import Path
import numpy as np
import cv2
from .algorithm import CONFIG,detect,evidence,run_mode,graph_paths,valley
from .common import put,save_npz
from .render_all import surface_grid

def run_tests(output):
    out=Path(output);out.mkdir(parents=True,exist_ok=True);c=CONFIG;p=[[40.,50.],[40.,200.]];base=np.full((256,512),180,np.uint8)
    cases=[];filters=[]
    for width in [1,2,3]:
        im=base.copy();im[120:120+width,100:300]=100
        a=evidence(im,base,p,p,c);values=[float(v[120-a['roi']['ya']:120-a['roi']['ya']+width,150-a['roi']['xa']].max()) for v in a['valley']]
        filters.append(dict(width=width,raw_depth=values[0],median_depth=values[1],gaussian_depth=values[2],median_retention=values[1]/values[0],gaussian_retention=values[2]/values[0]))
        X,Y,Z,sx,sy=surface_grid(a['gray'][0],a['roi']);assert np.array_equal(Z,im[Y,X]);assert a['gray'][0].dtype==np.uint8
        save_npz(out/f'fine_line_{width}.npz',current=im,median=a['gray'][1],gaussian=a['gray'][2])
    assert filters[0]['median_retention']==0
    cases.append(dict(name='1_2_3px_filter_and_surface',passed=True,measurements=filters,default='RAW because median destroys 1px line'))
    # Explicit fragment graph: supported ends, short gap, long gap and conflicting direction.
    g=dict(xa=0,ya=0,xleft=0,xr=400,upper=0,lower=200);E=np.ones((200,400),np.float32)*2;notch=dict(point=None)
    segs=[[[x,80] for x in range(20,61)],[[x,80] for x in range(66,120)]]
    paths,edges,counts=graph_paths(segs,E,g,notch,c);assert any(p['bridges'] for p in paths)
    bridge=next(p for p in paths if p['bridges']);assert sum(t[2] for t in bridge['trace_local'])==95;assert sum(not t[2] for t in bridge['trace_local'])==5
    for start,y in [(100,80),(66,120)]:
        ss=[segs[0],[[x,y] for x in range(start,start+40)]];_,e,_=graph_paths(ss,E,g,notch,c);assert len(e)==0
    cases.append(dict(name='short_gap_inferred_long_conflict_rejected',passed=True,observed=95,inferred=5))
    im=base.copy();im[110,100:300]=100;im[150,100:300]=100;im[90,350]=0
    a,res,graphs=detect(current_uint8=im,reference_uint8=im.copy(),P_ref=p,P_cur=p,config=c)
    ar=next(r for r in res if r['mode']=='A_VALLEY_ONLY_RAW');br=next(r for r in res if r['mode']=='B_DIFF_ONLY_RAW')
    assert ar['output_state']=='PATH_AMBIGUOUS';assert ar['physical_main_crack_identity']=='UNVERIFIED';assert br['output_state']=='REF_UNAVAILABLE';assert np.nanmax(abs(a['diff']['signed_raw']))==0;assert ar['counts']['retained_count']>0
    cases.append(dict(name='parallel_scratch_point_existing_line',passed=True,current=ar['output_state'],diff=br['output_state']))
    # Crossing / branches are retained and evaluated for ambiguity, not certified identities.
    for kind in ['crossing','branch','weak_gap','notch_invalid']:
        image=base.copy();image[128,90:300]=100
        if kind=='crossing':cv2.line(image,(90,90),(300,165),100,1)
        if kind=='branch':cv2.line(image,(180,128),(300,158),100,1)
        if kind=='weak_gap':image[128,180:185]=180
        if kind=='notch_invalid':image[100:160,280:340]=0
        aa,rr,gg=detect(current_uint8=image,reference_uint8=base,P_ref=p,P_cur=p,config=c)
        r=rr[0];assert r['physical_main_crack_identity']=='UNVERIFIED'
        if kind=='notch_invalid':assert not aa['material'][128-aa['roi']['ya'],300-aa['roi']['xa']]
        put(out/(kind+'.json'),r);save_npz(out/(kind+'.npz'),current=image)
        cases.append(dict(name=kind,passed=True,output=r['output_state'],candidate_count=len(r['paths']),interpretation='diagnostic ambiguity/identity limit; not synthetic accuracy'))
    lo=np.full_like(base,100);hi=np.full_like(base,150)
    a1=evidence(lo,hi,p,p,c);a2=evidence(hi,lo,p,p,c);assert np.nanmin(a1['diff']['signed_raw'])==50;assert np.nanmax(a2['diff']['signed_raw'])==-50
    assert not a1['diff']['ref_quality_map'].any()
    # Extreme P shift causes out-of-bounds warp: mask false and raw NaN, never zero.
    shifted=evidence(lo,hi,[[450.,50.],[450.,200.]],p,c);invalid=~shifted['diff']['valid_warp_mask'];assert invalid.any();assert np.isnan(shifted['diff']['signed_raw'][invalid]).all()
    rng=np.random.default_rng(4317);texture=rng.integers(130,230,base.shape,dtype=np.uint8);drift=np.roll(texture,18,1)
    drift_a=evidence(drift,texture,p,p,c);assert not drift_a['diff']['ref_quality_map'].any()
    illumination=np.clip(texture.astype(np.int16)-10,0,255).astype(np.uint8);illum=evidence(illumination,texture,p,p,c);assert illum['diff']['ref_quality_map'].any()
    assert np.max(np.abs(illum['diff']['signed_corrected'][illum['diff']['ref_quality_map']>0]))<1e-5
    cases.append(dict(name='signed_swap_untextured_drift_invalid_illumination',passed=True,positive=50,negative=-50,invalid_pixels=int(invalid.sum())))
    b,res2,gg2=detect(current_uint8=im,reference_uint8=im.copy(),P_ref=p,P_cur=p,config=c)
    assert json.dumps(res,sort_keys=True)==json.dumps(res2,sort_keys=True)
    for key in a['diff']:assert np.array_equal(a['diff'][key],b['diff'][key],equal_nan=True)
    for mode in graphs:
        for key in graphs[mode]:assert np.array_equal(graphs[mode][key],gg2[mode][key])
    rejected=[]
    for key in ['GT','gt_path','label_path','oracle_tip','tip_label','frame_id','specimen','history']:
        try:detect(current_uint8=im,reference_uint8=im,P_ref=p,P_cur=p,config=c,**{key:'forbidden'})
        except TypeError:rejected.append(key)
        else:raise AssertionError('Leakage accepted')
        bad=dict(c);bad[key]='forbidden'
        try:evidence(im,im,p,p,bad)
        except ValueError:pass
        else:raise AssertionError('Config leakage accepted')
    cases.append(dict(name='determinism_and_strict_schema',passed=True,rejected=rejected))
    cli=subprocess.run([sys.executable,'-m','grayref_simplified_evidence_v0.run_all','--run-id','forbidden_probe','--GT','forbidden'],capture_output=True,text=True)
    assert cli.returncode==2 and 'unrecognized arguments' in cli.stderr
    cases.append(dict(name='CLI_GT_injection_rejected_before_IO',passed=True,exit_code=cli.returncode))
    report=dict(tests=cases,passed=all(x['passed'] for x in cases),GT_LEAKAGE_TEST_PASSED=True,filter_preservation=filters)
    put(out/'unit_test_results.json',report);return report

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args();print(json.dumps(run_tests(args.output),indent=2))
