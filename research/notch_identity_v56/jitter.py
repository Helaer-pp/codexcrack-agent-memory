"""Sealed full-resolution perturbation sweeps; GT opened only during GROUP_A scoring."""
import csv,json,math
from concurrent.futures import ProcessPoolExecutor
import cv2
import numpy as np
from scipy.spatial import cKDTree
from . import terminal,native,batch as b
from .probes import images
from research.notch_identity_v54 import terminal as v54
from research.unified_crack_tip_60q.features import scene_geometry,register_reference,CONFIG
from research.v3_labelme_comparison.infer import current,read_csv
from research.v3_labelme_comparison.compare import write_csv,evaluate,PACKAGE

SYN=('P1_upper','P1_lower','P2_fade','P3_parallel','P4_ring','P1_weak_gap','P5_isolated','P6_isolated',
     'mouth_blob_competing','mouth_thick_valley','two_rise_bridge','weak_tail_blank','dipole_edge','dipole_with_crack')

def baseline(raw,fixed,points,fixed_points):
    scene=scene_geometry(raw,points,fixed,fixed_points,None,CONFIG)
    l,t,r,bottom=scene['bounds'];origin=np.array([l,t])
    ref,_=register_reference(fixed,raw,fixed_points,points,scene,CONFIG)
    hint=np.rint(np.asarray(scene['root'] or scene['center'])-origin).astype(int)
    m=v54.predict(v54.prepare(raw[t:bottom,l:r],hint,scene['scale']),None,ref['aligned'])
    pts=(np.array(m['points'])+origin).tolist() if m['points'] else []
    return dict(tip=pts[-1] if pts else None,points=pts,status=m['status'])

def shifts(points):
    axis=points[1]-points[0];axis=axis/np.linalg.norm(axis)
    normal=np.array([axis[1],-axis[0]])
    yield 'original','none',0,points
    for target in ('both','p1','p2'):
        for name,vec in (('axis',axis),('normal',normal)):
            for delta in (-20,-10,10,20):
                change=points.copy()
                if target!='p2':change[0]+=delta*vec
                if target!='p1':change[1]+=delta*vec
                yield target,name,delta,change

def work(job):
    source,key=job
    if source=='group_a':
        meta=b.read(b.OLD/'evidence/group_a'/str(key)/'metadata.json')
        info=meta['input'];raw=current(info['current'],info['image_sha']);fixed=native.reference(info['reference'],info['ref_sha'])
        points=np.array(meta['current_points'],float);rp=meta['fixed_points'];gt=[]
    else:
        raw,fixed,h,_,gt=images((key,9 if key=='P1_weak_gap' else 0,0.,1.,1,17))
        points=np.float64([h+[-22,-44],h+[-22,44]]);rp=points
    rows=[]
    for target,direction,delta,pair in shifts(points):
        for version in ('v5_4','v5_6'):
            if version=='v5_4':m=baseline(raw,fixed,pair,rp)
            else:m=terminal.predict(native.prepare(raw,pair,'v5_6'),None,fixed)
            rows.append(dict(source=source,key=key,target=target,direction=direction,delta=delta,version=version,
                             status=m['status'],points=m['points'],tip=m['tip']))
    return rows

def warm():cv2.setNumThreads(1)

def main():
    sel={int(r['frame_id']):r for r in read_csv(b.SELECT) if r['dataset_id']=='group_a'}
    jobs=[('group_a',i) for i in sel]+[('synthetic',k) for k in SYN]
    path=b.OUT/'jitter_predictions.jsonl'
    if not path.exists():
        with ProcessPoolExecutor(6,initializer=warm) as pool,path.with_suffix('.partial').open('w') as stream:
            for rows in pool.map(work,jobs):
                for row in rows:stream.write(json.dumps(row,separators=(',',':'))+'\n')
        path.with_suffix('.partial').rename(path)
        b.save(b.OUT/'jitter_seal.json',dict(predictions=b.sha(path),sources=b.sources()))
    assert b.read(b.OUT/'jitter_seal.json')==dict(predictions=b.sha(path),sources=b.sources())
    rows=[];orig={};labels={}
    for line in path.open():
        m=json.loads(line);source,key=m['source'],m['key'];v=m['version']
        if (source,key) not in labels:
            if source=='group_a':
                shapes=b.read(PACKAGE/sel[key]['selected_json'])['shapes']
                truth=next((s['points'][0] for s in shapes if s['label']=='crack_tip'),None)
                curves=[np.array(s['points']) for s in shapes if s['label']=='crack_path']
            else:
                _,_,_,_,curve=images((key,9 if key=='P1_weak_gap' else 0,0.,1.,1,17))
                truth=curve[-1] if len(curve) else None;curves=[curve]
            labels[source,key]=truth,curves
        truth,curves=labels[source,key]
        if source=='group_a':joint=evaluate(m,curves,truth)['joint']
        elif truth is None:joint=None
        elif m['tip']:
            line=curves[0];pts=m['points']
            joint=bool(math.dist(truth,m['tip'])<=10 and min((cKDTree(pts).query(line)[0]<=2.5).mean(),(cKDTree(line).query(pts)[0]<=2.5).mean())>=.8)
        else:joint=False
        if not m['delta']:orig[source,key,v]=m['tip'],joint
        ref,j0=orig[source,key,v];pred=m['tip']
        rows.append(dict(source=source,key=key,version=v,target=m['target'],direction=m['direction'],delta=m['delta'],
            drift=math.dist(pred,ref) if ref and pred else None,base_valid=bool(ref),valid=bool(pred),base_joint=j0,joint=joint))
    write_csv(b.OUT/'jitter_rows.csv',rows)
    keys=['source','version','target','direction','delta'];summary=[]
    for signature in dict.fromkeys(tuple(r[k] for k in keys) for r in rows):
        a=[r for r in rows if tuple(r[k] for k in keys)==signature]
        d=[r['drift'] for r in a if r['drift'] is not None]
        summary.append(dict(zip(keys,signature),total=len(a),paired=len(d),median=float(np.median(d)) if d else None,
            maximum=max(d,default=None),lost=sum(r['base_valid'] and not r['valid'] for r in a),
            gained=sum(r['valid'] and not r['base_valid'] for r in a),visible=sum(r['joint'] is not None for r in a),
            base_joint=sum(r['base_joint'] is True for r in a),joint=sum(r['joint'] is True for r in a)))
    write_csv(b.OUT/'jitter_summary.csv',summary)
    print('Completed',len(rows),'native-input jitter predictions.')
if __name__=='__main__':main()
