"""Measure identity on the actual DP coordinates presented to the geometry guard."""
from unittest.mock import patch
import numpy as np
from scipy.spatial import cKDTree
from .paired_probes import sample,original,terminal,OUT,write_csv
from research.v3_labelme_comparison.infer import read_csv

def main(previous=False):
    from .batch import BASE
    from . import terminal
    if previous:
        from research.notch_identity_v33 import terminal
    from ast import literal_eval
    cases=[r for r in read_csv((BASE if previous else OUT)/'paired_probes.csv') if r['case']=='P1_weak_gap']
    follow=terminal.follow
    inspect=terminal.guards.inspect_track
    rows=[]
    for r in cases:
        z,w,v=float(r['zoom']),int(r['width']),float(r['contrast'])
        n,seed=int(r['noise']),int(r['seed'])
        raw,h,s,gt=sample(r['case'],z,n,seed,w,v)
        fixed=original.scene('UNLOADED',z,n,seed+101)[0]
        g,b={'nominal':(1.,0),'dim':(.65,9),'bright':(1.16,15)}[r['photo']]
        a=np.clip(g*raw+b,0,255).astype(np.uint8)
        ref=np.clip(g*fixed+b,0,255).astype(np.float32)
        p=terminal.prepare(a,h,s)
        bonus=None if p is None else .04*np.clip((ref[p[0]]-a[p[0]])/max(.12*p[-1],1e-6),0,1)
        tracks={}
        def capture(*args,**kwargs):
            def observe(arr,*more):
                tracks[tuple(args[3])]=arr[:,:2].copy()
                return inspect(arr,*more)
            with patch.object(terminal.guards,'inspect_track',observe):
                return follow(*args,**kwargs)
        with patch.object(terminal,'follow',capture):
            result=terminal.predict(p,bonus,ref)
        assert result['tip']==(literal_eval(r['tip']) if r['tip'] else None)
        accepted=wrong=rejected=waived_wrong=0
        if result['tip']:
            i=result['diagnostics']['selected']
            cand=result['diagnostics']['candidates'][i]
            arr=tracks[tuple(p[2][i])]+p[1]
            for first,left,right,_,_,ok in cand['trace']['events']:
                if first/z>=94+w or right/z<94:continue
                if not ok:
                    rejected+=1
                    continue
                pts=arr[(arr[:,0]>=left)&(arr[:,0]<=right)]
                assert len(pts)
                accepted+=1
                bad=(cKDTree(gt).query(pts)[0]/z<=2.5).mean()<.8
                wrong+=int(bad)
                waived_wrong+=int(bad and first in cand['trace'].get('waived_lip',[]))
        rows.append({**r,'accepted':accepted,'wrong':wrong,'rejected':rejected,'wrong_lip_waivers':waived_wrong})
    write_csv(OUT/('previous_paired_events.csv' if previous else 'paired_events.csv'),rows)

if __name__=='__main__':
    main(True)
    main()
