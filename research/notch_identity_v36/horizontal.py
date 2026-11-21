"""Post-seal measurements along the published horizontal overrun beyond the manual tip."""
from ast import literal_eval
import numpy as np
from .batch import OLD,OUT,read,sha
from research.notch_identity_v31.detector import exposure,px
from research.notch_identity_v34.reference import profiles
from research.notch_identity_v32.audit import selected
from research.v3_labelme_comparison.compare import write_csv

def measure(records,scores):
    result=[]
    for i in (195,456,510,528):
        g='group_c';rec=records[g,i]
        m=read(OLD/'evidence'/g/str(i)/'metadata.json')
        scene=m['evidence']['scene'];off=np.array(scene['bounds'][:2]);s=scene['scale']
        hint=np.rint(np.array(scene['root'] or scene['center'])-off).astype(int)
        gt=literal_eval(scores[g,i,'v3_6','full']['gt'])
        with np.load(OLD/'evidence'/g/str(i)/'arrays.npz') as z:
            raw=z['raw'];fixed=z['fixed__aligned']
        _,contrast=exposure(raw,hint,s)
        for stage in ('v3_5','v3_6'):
            model=rec['models'][stage]['full'];t=selected(model);q=t.get('reference',{})
            p=np.array(model['points']);shift=q.get('shift')
            cell=dict(group=g,frame=i,stage=stage,tip=model['tip'],gt=gt,columns=0,net=None,neg_pos=None,duplicate=None,low_run=None,needed=px(s,.020),floor=None,waived=t.get('waived'))
            if len(p) and shift is not None:
                xx=np.arange(p[0,0],p[-1,0]+1);yy=np.rint(np.interp(xx,p[:,0],p[:,1])).astype(int)
                noise=t['noise'];floor=max(2*noise,.012*contrast)
                vals=profiles(raw,fixed,np.c_[xx,yy]-off,*shift,px(s,.014),px(s,.010),px(s,.010),max(noise,.008*contrast))
                a=vals[(xx>gt[0])&np.isfinite(vals).all(axis=1)]
                if len(a):
                    pos,neg,net,dc,df=a.T
                    pairs=np.flatnonzero(np.diff(np.r_[False,net<=floor,False])).reshape(-1,2)
                    dup=(df>=.55*np.maximum(dc,noise))&(df>=max(3.5*max(noise,.008*contrast),.04*contrast))
                    cell.update(columns=len(a),net=float(np.mean(net)),neg_pos=float(neg.sum()/max(pos.sum(),noise)),duplicate=float(dup.mean()),low_run=max((int(b-a) for a,b in pairs),default=0),floor=floor)
            result.append(cell)
    write_csv(OUT/'horizontal_tail.csv',result);return result
