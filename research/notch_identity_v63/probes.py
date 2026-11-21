"""Use identical paired probes for longitudinal comparison and additional isolated controls."""
from concurrent.futures import ProcessPoolExecutor
from itertools import product
import time
import cv2
import numpy as np
from scipy.spatial import cKDTree
from research.notch_identity_v40.probes import original,sample,stress
from research.v3_labelme_comparison.compare import write_csv
from research.v3_labelme_comparison.infer import read_csv
from . import terminal, domain
from .batch import OUT,sha,sources,save,read

from research.notch_identity_v59.probes import images as previous_images


def images(job):
    case,width,contrast,z,noise,seed=job
    if case!='active_fork':return previous_images(job)
    cur,fixed,h,s,_=previous_images(('control_noise_blank',width,contrast,z,noise,seed))
    yy,xx=np.indices(cur.shape);x=xx/z;y=yy/z
    # Competing old straight dark lip and new divergent, weaker dark lip.
    # Swap upper/lower lips between seeds; the old trace has negative signed change.
    sign=1 if seed==17 else -1
    old_y=80+sign*(4+.035*np.maximum(x-70,0))
    new_y=80-sign*(4+.12*np.maximum(x-70,0))
    old=np.exp(-.5*((y-old_y)/1.05)**2)*((x>=69)&(x<=151))
    fresh=np.exp(-.5*((y-new_y)/.90)**2)*((x>=69)&(x<=132))
    fixed=np.clip(fixed.astype(float)-98*old,0,255).astype('uint8')
    cur=np.clip(cur.astype(float)-78*old-48*fresh,0,255).astype('uint8')
    xs=np.arange(70,133)
    gt=np.column_stack((xs,80-sign*(4+.12*(xs-70))))*z
    return cur,fixed,h,s,gt


def trial_stage(job,stage):
    case,width,contrast,z,noise,seed=job
    a,f,h,s,gt=images(job)
    rows=[]
    for photo,g,bias in [('nominal',1.,0),('dim',.65,9),('bright',1.16,15)]:
        raw=np.clip(g*a+bias,0,255).astype('uint8')
        fixed=np.clip(g*f+bias,0,255).astype('float32')
        start=time.perf_counter();p=terminal.prepare(raw,h,s,stage,reference=fixed);mapped=domain.ReferenceMap(raw,fixed,np.zeros((2,2)),np.zeros((2,2)),[0,0,raw.shape[1],len(raw)],p,stage);m=terminal.predict(p,None,mapped);elapsed=time.perf_counter()-start;tip=m['tip'];pts=np.asarray(m['points'])
        dual=m['diagnostics']['dual'];d=m['diagnostics'];j=d.get('selected')
        tr=d['candidates'][j]['trace'] if j is not None else {}
        err=np.linalg.norm(gt[-1]-tip)/z if tip and len(gt) else None
        coverage=(cKDTree(pts).query(gt)[0]/z<=2.5).mean() if tip and len(gt) else 0
        precision=(cKDTree(gt).query(pts)[0]/z<=2.5).mean() if tip and len(gt) else 0
        passed=not tip if not len(gt) else err is not None and err<=10 and (not case.startswith('P1') or coverage==1.) and (not case.startswith('P6') or precision>=.95)
        acc=wrong=0
        if width and tip:
            # A dense DP path has no missing columns. Compare the post-gap segment with truth.
            band_end=(94+width)*z
            if pts[0,0]<=94*z and pts[-1,0]>=band_end+max(1,round(4*z)):
                post=pts[(pts[:,0]>=band_end)&(pts[:,0]<=band_end+max(1,round(8*z)))]
                acc=1;wrong=int((cKDTree(gt).query(post)[0]/z<=2.5).mean()<.8)
        baseline_error=width_error=baseline_valid=width_valid=None
        rows.append(dict(stage=stage,seconds=elapsed,joint=bool(err is not None and err<=10 and min(coverage,precision)>=.8),priority=dual.get('priority_applied',False),eligible=sum(b['reason']=='VALID' for b in dual['branches']),published_bridge=any('BRANCH_'+str(b['id'])==dual['pick'] and b['bridge']['accepted'] for b in dual['branches']),global_x=(dual['peak'][0]-dual['front'])/s if dual.get('peak') else None, mouth_review=dual.get('mouth_review'), baseline_error=baseline_error,width_error=width_error,baseline_valid=baseline_valid,width_valid=width_valid,pick=dual.get('pick'),lip_bridge=bool(dual.get('lip_bridge')),mapped_short_rejected=any(br['reason']=='MAPPED_SHORT_ISOLATED' for br in dual['branches']),clean_admitted=any(br.get('curve',{}).get('clean_primer_admitted') for br in dual['branches']),case=case,width=width,contrast=contrast,zoom=z,noise=noise,seed=seed,photo=photo,negative=not len(gt),valid=bool(tip),passed=bool(passed),error=err,tip=tip,coverage=coverage,precision=precision,registration=(dual.get('registration') or {}).get('status'),required_contour_run=max(10,round(.065*p[0].scale)) if p else None,longest_dual=max((r.get('curve',{}).get('longest_dual_run',0) for r in dual['branches']),default=0),track=dual['decision'],stop=dual.get('stop'),accepted=acc,wrong=wrong,background_raw=dual.get('background_raw'),background_diff=dual.get('background_diff')))
    return rows

def trial(job):
    return [r for stage in terminal.STAGES for r in trial_stage(job,stage)]

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    cases=[(c,0,1.) for c in (*original.CASES,'P5_plastic_zone','P5_plastic_zone_negative','P6_deformed_scratch','P6_deformed_scratch_negative','P2_isolated','P5_isolated','P6_isolated','control_glare','control_same_blank','control_noise_blank','control_preexisting','control_texture_tail','mouth_blob_branch','mouth_blob_only','mouth_blob_competing','mouth_thick_valley','mouth_glare_arc_only','mouth_glare_arc_branch','two_rise_bridge','weak_tail_attached','weak_tail_blank','dipole_edge','dipole_with_crack','material_edge_glare','weak_material_bridge','active_fork')]
    cases.extend(('P1_weak_gap',w,c) for w,c in product((4,9,16),(0.,.2)))
    jobs=[(*case,z,n,seed) for case,z,n,seed in product(cases,(.5,1.,2.),(1,5),(17,31))]
    with ProcessPoolExecutor(4,initializer=warm) as pool:rows=sum(pool.map(trial,jobs,chunksize=2),[])
    write_csv(OUT/'paired_probes.csv',rows);write_csv(OUT/'weak_events.csv',[r for r in rows if r['width']])
    save(OUT/'probe_seal.json',{'sources':sources(),'csv':sha(OUT/'paired_probes.csv')})
    assert len(rows)==len(terminal.STAGES)*1404
    print('Scored',len(rows),'synthetic probes',flush=True)
def warm():cv2.setNumThreads(1)
if __name__=='__main__':run()
