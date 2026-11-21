"""Trace every supplemental false positive against the identical frozen baseline input."""
import cv2
import numpy as np
from . import batch as b, probes, domain, terminal
from research.notch_identity_v515_budget import terminal as baseline
from research.v3_labelme_comparison.compare import write_csv


def main():
    cv2.setNumThreads(1)
    rows=[]
    for r in b.read_csv(b.OUT/'paired_probes.csv'):
        if r['negative']!='True' or r['valid']!='True':continue
        s=r['stage']
        job=(r['case'],int(r['width']),float(r['contrast']),float(r['zoom']),int(r['noise']),int(r['seed']))
        cur,fixed,h,scale,_=probes.images(job)
        g,bias={'nominal':(1,0),'dim':(.65,9),'bright':(1.16,15)}[r['photo']]
        cur=np.clip(g*cur+bias,0,255).astype('uint8')
        fixed=np.clip(g*fixed+bias,0,255).astype('float32')
        prev=baseline.predict(baseline.prepare(cur,h,scale,'S2',fixed),None,fixed)['diagnostics']['dual']
        p=terminal.prepare(cur,h,scale,s,fixed)
        points=np.zeros((2,2))
        mapping=domain.ReferenceMap(cur,fixed,points,points,[0,0,cur.shape[1],len(cur)],p,s)
        new=terminal.predict(p,None,mapping)['diagnostics']['dual']
        assert new['stop']=='ACCEPTED_PEAK'
        win=next(w for w in new['branches'] if new['pick']=='BRANCH_'+str(w['id']))
        rows.append(dict(stage=s,case=r['case'],zoom=r['zoom'],noise=r['noise'],seed=r['seed'],photo=r['photo'],
                    previous_source=prev['decision'],previous_stop=prev['stop'],source=new['decision'],stop=new['stop'],
                    net=win['value'],longest_dual=win['curve'].get('longest_dual_run'),scale=new.get('scale'),
                    zero_only=all(w['up_mode']==w['down_mode']=='zero' for w in mapping.info['windows'])))
    write_csv(b.OUT/'negative_audit.csv',rows)

if __name__=='__main__':main()
