"""Resample signed evidence onto labels after inference; labels never enter the detector."""
from unittest.mock import patch
import numpy as np
from .run import frozen,frame
from . import terminal,batch as b
from research.v3_labelme_comparison.compare import PACKAGE,write_csv

TARGETS={'group_a':(398,), 'three_point_bend':(215,248), 'group_c':(38,324,335,345,510)}


def measure(g,i,pl,src,p,f):
    field,red,blue,reflection=f
    if len(p)<2:return None
    p=np.asarray(p)
    order=np.argsort(p[:,0],kind='stable')
    x0,idx=np.unique(p[order,0],return_index=True)
    x=np.arange(max(0,int(np.ceil(x0[0]))),min(len(field)-1,int(np.floor(x0[-1])))+1)
    if not len(x):return None
    y=np.rint(np.interp(x,x0,p[order[idx],1])).astype(int)
    good=(y>=0)&(y<field.shape[1])
    x,y=x[good],y[good]
    valid=np.isfinite(field[x,y])
    if not valid.any():return None
    y=y[valid];x=x[valid];v=field[x,y]
    blank=np.flatnonzero(np.diff(np.r_[False,v<=0,False])).reshape(-1,2)
    a,z=max(blank,key=lambda q:q[1]-q[0]) if len(blank) else (0,0)
    return dict(group=g,frame=i,placement=pl,trace=src,finite_columns=len(x),net_sum=float(v.sum()),
        mean_red=float(red[x,y].mean()),mean_blue=float(blue[x,y].mean()),max_nonpositive_columns=int(z-a),
        gap_reflection=float(reflection[x[a:z],y[a:z]].mean()) if z>a else None,
        tail12_mean=float(v[-12:].mean()))


def main():
    frozen(); rows=[]
    for g,ids in TARGETS.items():
        dst=b.OUT/(g+'.jsonl')
        assert b.read(b.OUT/(g+'_seal.json'))['predictions']==b.sha(dst)
        roster={int(r['frame_id']):r for r in b.read_csv(b.SELECT) if r['dataset_id']==g}
        for i in ids:
            observed=[]; build=terminal.curve.evidence
            def capture(scene,*args):
                fields=build(scene,*args)
                observed.append((np.array(scene.origin)+[scene.front,0],fields))
                return fields
            with patch.object(terminal.curve,'evidence',capture):
                rec=frame((g,i,False,('S3',),False))
            shapes=b.read(PACKAGE/roster[i]['selected_json'])['shapes']
            truth=max((s['points'] for s in shapes if s['label']=='crack_path'),key=lambda q:np.ptp(np.asarray(q)[:,0]))
            for pl,models in rec['placements'].items():
                pred=models['S3']['full']
                if pred['diagnostics']['dual']['decision']!='JOINT':continue
                off,f=observed.pop(0)
                off=off+rec['box'][:2]
                for tag,pts in [('algorithm',pred['points']),('label',truth)]:
                    if len(pts)>1:
                        result=measure(g,i,pl,tag,np.asarray(pts)-off,f)
                        if result:rows.append(result)
    write_csv(b.OUT/'target_field_audit.csv',rows)


if __name__=='__main__':main()
