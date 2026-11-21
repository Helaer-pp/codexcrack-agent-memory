"""Use identical paired probes for longitudinal comparison and additional isolated controls."""
from concurrent.futures import ProcessPoolExecutor
from itertools import product
import cv2
import numpy as np
from scipy.spatial import cKDTree
from research.notch_identity_v40.probes import original,sample,stress
from research.v3_labelme_comparison.compare import write_csv
from research.v3_labelme_comparison.infer import read_csv
from . import terminal
from .batch import OUT,sha,sources,save,read

def isolated(case,z,noise,seed):
    raw,h,s,_=original.scene('UNLOADED',z,noise,seed)
    y,x=np.indices(raw.shape);u=x/z;v=y/z
    gt=np.array([(j,80+round(.04*(j-70))) for j in range(70,200)])*z
    line=np.zeros((160,310),np.uint8)
    for j in range(70,200):line[80+round(.04*(j-70)),j]=80
    ink=cv2.resize(line,(raw.shape[1],raw.shape[0]),interpolation=cv2.INTER_AREA if z<1 else cv2.INTER_LINEAR)
    a=raw.astype(float)-ink
    f=original.scene('UNLOADED',z,noise,seed+101)[0].astype(float)
    if case=='P5_isolated':
        a-=(10 if seed==17 else 25)*np.exp(-.5*((u-208)/30)**2-.5*((v-85)/23)**2)
    if case=='P6_isolated':
        for im,off in ((a,0),(f,5 if seed==17 else -7)):
            im-=60*np.exp(-.5*((v-(85-.38*(u-200)+off))/.8)**2)*np.clip((u-193)/5,0,1)*np.clip((273-u)/5,0,1)
    return np.clip(a,0,255).astype('uint8'),np.clip(f,0,255).astype('uint8'),h,s,gt

def images(job):
    case,width,contrast,z,noise,seed=job
    if case in ('dipole_edge','dipole_with_crack'):
        blank,h,s,_=original.scene('UNLOADED',z,noise,seed)
        f=original.scene('UNLOADED',z,noise,seed+101)[0].astype(float)
        yy,xx=np.indices(blank.shape);u=xx/z;v=yy/z
        centre=84+3*np.sin((u-72)/15)
        support=np.clip((u-68)/4,0,1)*np.clip((117-u)/5,0,1)
        a=blank.astype(float)+58*np.exp(-.5*((v-centre-3)/1.65)**2)*support
        f+=58*np.exp(-.5*((v-centre)/1.65)**2)*support
        gt=np.empty((0,2))
        if case=='dipole_with_crack':
            curve=73-.06*np.maximum(0,u-70)
            a-=63*np.exp(-.5*((v-curve)/.9)**2)*((u>=69)&(u<=152))
            k=np.arange(70,153);gt=np.column_stack((k,73-.06*(k-70)))*z
        a=np.clip(a,0,255).astype('uint8');f=np.clip(f,0,255).astype('uint8')
    elif case.startswith('two_rise') or case.startswith('weak_tail'):
        blank,h,s,_=original.scene('UNLOADED',z,noise,seed)
        f=original.scene('UNLOADED',z,noise,seed+101)[0].astype(float)
        yy,xx=np.indices(blank.shape);u=xx/z;v=yy/z
        # Two observed dark segments joined by a distinct narrow positive differential ridge.
        split=132 if seed==17 else 145
        end=split+48 if seed==17 else split+56
        centre=80+.07*np.maximum(0,u-70)+1.3*np.sin((u-70)/18)
        line=np.exp(-.5*((v-centre)/1.00)**2)
        base=(u>=69)&(u<=end)
        gap=(u>split)&(u<end-15)
        a=blank.astype(float)
        gt=np.empty((0,2))
        if case=='two_rise_bridge':
            a-=line*base*np.where(gap,2.,61.)
            f+=line*gap*(42 if noise==1 else 52)
            endpoint=end
        else:
            endpoint=split if case=='weak_tail_attached' else None
            if endpoint is not None:a-=line*base*(u<=split)*61.
            tail=(u>split)&(u<=end)
            broad=np.exp(-.5*((v-centre)/3.6)**2)
            f+=broad*tail*5.
        if endpoint is not None:
            xx=np.arange(70,endpoint+1)
            gt=np.column_stack((xx,80+.07*(xx-70)+1.3*np.sin((xx-70)/18)))*z
        a=np.clip(a,0,255).astype('uint8');f=np.clip(f,0,255).astype('uint8')
    elif case.startswith('mouth_'):
        blank,h,s,_=original.scene('UNLOADED',z,noise,seed)
        f=original.scene('UNLOADED',z,noise,seed+101)[0]
        yy,xx=np.indices(blank.shape);u=xx/z;v=yy/z
        # Independent nuisance: a broad opening on the opposite lip, with a short thin edge.
        broad=65*np.clip((u-68)/3,0,1)*np.clip((116-u)/7,0,1)*np.clip((7-abs(v-86))/2,0,1)
        a=blank.astype(float)-broad
        gt=np.empty((0,2))
        if case in ('mouth_blob_branch','mouth_blob_competing'):
            if case=='mouth_blob_competing':
                end=142 if seed==17 else 151
                gap_end=126 if seed==17 else 132
                center=73-11*np.sin(np.clip((u-70)/43,0,1)*np.pi*.5)
                first,offset=73,11
                amp=14 if noise==1 else 26
                ink=amp*np.exp(-.5*((v-center)/.8)**2)*((u>=69)&(u<=end))
                ink*=np.where((u>80)&(u<gap_end),.015,1)
                nuisance=58*np.clip((u-68)/3,0,1)*np.clip((114-u)/6,0,1)*np.clip((7-abs(v-88))/2,0,1)
                crease=60*np.exp(-.5*((v-88)/.8)**2)*np.clip((u-70)/2,0,1)*np.clip((115-u)/2,0,1)
                a=blank-nuisance-crease-ink
                gt=np.array([(x,first-offset*np.sin(min((x-70)/43,1)*np.pi*.5)) for x in range(70,end+1)])*z
            else:
                end=139 if seed==17 else 162
                gt=np.array([(x,80-6*np.sin(min((x-70)/42,1)*np.pi*.5)) for x in range(70,end+1)])*z
                center=80-6*np.sin(np.clip((u-70)/42,0,1)*np.pi*.5)
                ink=(52 if noise==1 else 67)*np.exp(-.5*((v-center)/.85)**2)*((u>=69)&(u<=end))
                band=(u>87)&(u<98)
                f=np.clip(f+band*ink,0,255).astype('uint8')
                a-=ink*(~band)
        elif case.startswith('mouth_glare_arc'):
            # Motion of a bright reflection produces a red crescent on otherwise flat gray.
            center=83+3*np.sin(np.clip((u-70)/46,0,1)*np.pi)
            gate=np.clip((u-68)/3,0,1)*np.clip((115-u)/4,0,1)
            reflection=63*np.clip((v-(center-12))/2,0,1)*np.clip((center-v)/2,0,1)*gate
            shift=58*np.clip((v-center)/1.5,0,1)*np.clip((center+7-v)/1.5,0,1)*gate
            toe=48*np.exp(-.5*((v-(center+2))/.9)**2)*np.clip((u-68)/2,0,1)*np.clip((78-u)/3,0,1)
            a=blank.astype(float)+reflection-toe;f=np.clip(f+reflection+shift-toe,0,255).astype('uint8')
            if case=='mouth_glare_arc_branch':
                end=147 if seed==17 else 157
                line=73-6*np.sin(np.clip((u-70)/42,0,1)*np.pi*.5)
                a-=55*np.exp(-.5*((v-line)/.8)**2)*((u>=69)&(u<=end))
                gt=np.array([(x,73-6*np.sin(min((x-70)/42,1)*np.pi*.5)) for x in range(70,end+1)])*z
        elif case=='mouth_thick_valley':
            end=154;center=80+np.clip((u-70)*.06,0,5)
            gt=np.array([(x,80+min((x-70)*.06,5)) for x in range(70,end+1)])*z
            shape=38*np.exp(-.5*((v-center)/3.4)**2)+48*np.exp(-.5*((v-center)/.80)**2)
            a=blank-shape*((u>=69)&(u<=end))
        a=np.clip(a,0,255).astype('uint8')
    elif case.startswith('control_'):
        a,f,h,s,gt=isolated('P2_isolated',z,noise,seed)
        blank=original.scene('UNLOADED',z,noise,seed)[0]
        if case=='control_glare':
            yy,xx=np.indices(a.shape)
            u=xx/z;v=yy/z
            band=(u>=86)&(u<86+(10 if seed==17 else 15))
            a[band]=blank[band]
            # Bright reflective stripe in the fixed image; current gray in the gap matches its flanks.
            stripe=55*np.exp(-.5*((v-(80+.04*(u-70)))/.8)**2)*band
            f=np.clip(f+stripe,0,255).astype('uint8')
        elif case=='control_preexisting':f=a.copy()
        elif case=='control_texture_tail':
            # A short pre-existing crack abuts long shallow material texture in a same-image pair.
            yy,xx=np.indices(a.shape);u=xx/z;v=yy/z
            end=100 if seed==17 else 110
            gt=gt[gt[:,0]<=end*z]
            stripe=(6 if seed==17 else 9)*np.exp(-.5*((v-(81+.6*np.sin(u/15)))/.9)**2)
            a=np.where(u>end,np.clip(blank-stripe,0,255),a).astype('uint8')
            f=a.copy()
        else:
            a=blank;gt=np.empty((0,2))
            if case=='control_same_blank':f=a.copy()
    elif case.endswith('_isolated'):a,f,h,s,gt=isolated(case,z,noise,seed)
    elif case.startswith(('P5','P6')):a,f,h,s,gt=stress(case,z,noise,seed)
    else:
        a,h,s,gt=sample(case,z,noise,seed,width,contrast)
        f=original.scene('UNLOADED',z,noise,seed+101)[0]
    return a,f,h,s,gt

def trial(job):
    case,width,contrast,z,noise,seed=job
    a,f,h,s,gt=images(job)
    rows=[]
    for photo,g,bias in [('nominal',1.,0),('dim',.65,9),('bright',1.16,15)]:
        raw=np.clip(g*a+bias,0,255).astype('uint8')
        fixed=np.clip(g*f+bias,0,255).astype('float32')
        p=terminal.prepare(raw,h,s);m=terminal.predict(p,None,fixed);tip=m['tip'];pts=np.asarray(m['points'])
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
        rows.append(dict(global_x=(dual['peak'][0]-dual['front'])/s if dual.get('peak') else None, mouth_review=dual.get('mouth_review'), baseline_error=baseline_error,width_error=width_error,baseline_valid=baseline_valid,width_valid=width_valid,pick=dual.get('pick'),lip_bridge=bool(dual.get('lip_bridge')),case=case,width=width,contrast=contrast,zoom=z,noise=noise,seed=seed,photo=photo,negative=not len(gt),valid=bool(tip),passed=bool(passed),error=err,tip=tip,coverage=coverage,precision=precision,track=dual['decision'],stop=dual.get('stop'),accepted=acc,wrong=wrong,background_raw=dual.get('background_raw'),background_diff=dual.get('background_diff')))
    return rows

def synthetic_gate(folder):
    rows=read_csv(folder/'paired_probes.csv')
    if read(folder/'probe_seal.json')!={'sources':sources(),'csv':sha(folder/'paired_probes.csv')}:return False
    return len(rows)==1296 and len([x for x in rows if x['negative']=='True'])==432

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    cases=[(c,0,1.) for c in (*original.CASES,'P5_plastic_zone','P5_plastic_zone_negative','P6_deformed_scratch','P6_deformed_scratch_negative','P2_isolated','P5_isolated','P6_isolated','control_glare','control_same_blank','control_noise_blank','control_preexisting','control_texture_tail','mouth_blob_branch','mouth_blob_only','mouth_blob_competing','mouth_thick_valley','mouth_glare_arc_only','mouth_glare_arc_branch','two_rise_bridge','weak_tail_attached','weak_tail_blank','dipole_edge','dipole_with_crack')]
    cases.extend(('P1_weak_gap',w,c) for w,c in product((4,9,16),(0.,.2)))
    jobs=[(*case,z,n,seed) for case,z,n,seed in product(cases,(.5,1.,2.),(1,5),(17,31))]
    with ProcessPoolExecutor(6,initializer=warm) as pool:rows=sum(pool.map(trial,jobs,chunksize=2),[])
    write_csv(OUT/'paired_probes.csv',rows);write_csv(OUT/'weak_events.csv',[r for r in rows if r['width']])
    save(OUT/'probe_seal.json',{'sources':sources(),'csv':sha(OUT/'paired_probes.csv')})
    print('Synthetic gate:',synthetic_gate(OUT),flush=True)
def warm():cv2.setNumThreads(1)
if __name__=='__main__':run()
