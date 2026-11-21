"""Secondary spacing check with a common bright envelope for nominal, 0.8x and 1.2x."""
import json
import cv2
import numpy as np
from . import batch as b,domain, inputs
from .run import frozen
from research.v3_labelme_comparison.compare import write_csv

def main():
    frozen();cv2.setNumThreads(1)
    g='group_c'
    ids={int(r['frame_id']) for r in b.read_csv(b.SELECT) if r['dataset_id']==g}
    p=b.OUT/(g+'.jsonl')
    assert b.sha(p)==b.read(b.OUT/(g+'_seal.json'))['predictions']
    rows=[]
    for rec in map(json.loads,p.open(encoding='utf8')):
        i=rec['frame']
        if i not in ids:continue
        meta=inputs.metadata(g,i)['input']
        im=b.old.current(meta['current'],meta['image_sha']);fixed=b.old.read_fixed(meta['reference'],meta['ref_sha'])
        x,y,r,bt=rec['box'];off=np.array([x,y]);geo=rec['geometry']
        cp,rp=map(np.asarray,(geo['cur_points'],geo['ref_points']))
        scale_factors=(1.,.8,1.2)
        # Shorter test pair leaves room for symmetric expansion; search illumination only.
        def pairs(pair,dx,factor):
            mid=pair.mean(0)
            return mid+[dx,0]+(pair-mid)*.65*factor
        for dx in range(0,r-x,2):
            trials=[(pairs(cp,dx,f),pairs(rp,dx,f)) for f in scale_factors]
            if all(x+4<=pt[0]<r-4 and y+4<=pt[1]<bt-4 and b.patch_min(img,[0,0],pt)>=floor
                   for ac,ar in trials for img,pp,floor in ((im,ac,geo['floors'][1]),(fixed,ar,geo['floors'][0])) for pt in pp):
                break
        else:continue
        raw=im[y:bt,x:r];ref=fixed[y:bt,x:r]
        for f,(ac,ar) in zip(scale_factors,trials):
            prep=b.terminal.prepare(raw,ac.mean(0)-off,b.SCALE,'S2',ref,ar.mean(0)-off)
            mapped=domain.ReferenceMap(im,fixed,ac,ar,rec['box'],prep,'S2')
            m,_=b.run_mode(raw,ref,ac,ar,off,'S2','full',aligned=mapped,prepared=prep)
            if f==1.:nominal=m
            rows.append(dict(frame=i,factor=f,reference_points=ar.tolist(),current_points=ac.tolist(),shift_x=dx,
                             status=m['status'],changed_path=m['points']!=nominal['points'],
                             changed_status=m['status']!=nominal['status'],
                             changed_route=m['diagnostics']['dual']['decision']!=nominal['diagnostics']['dual']['decision']))
    write_csv(b.OUT/'bright_spacing.csv',rows)

if __name__=='__main__':main()
