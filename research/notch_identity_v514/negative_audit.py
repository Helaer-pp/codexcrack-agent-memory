"""Replay every final false positive and inspect the decision before/after S1."""
from . import batch as b,probes,terminal
from research.notch_identity_v513 import terminal as prior
from research.v3_labelme_comparison.compare import write_csv
import numpy as np


def main():
    rows=[]
    for r in b.read_csv(b.OUT/'paired_probes.csv'):
        if r['stage']!='S4' or r['negative']!='True' or r['valid']!='True':continue
        job=(r['case'],int(r['width']),float(r['contrast']),float(r['zoom']),int(r['noise']),int(r['seed']))
        im,ref,h,s,_=probes.images(job)
        gain,bias={'nominal':(1.,0),'dim':(.65,9),'bright':(1.16,15)}[r['photo']]
        raw=np.clip(im*gain+bias,0,255).astype('uint8')
        f=np.clip(ref*gain+bias,0,255).astype('float32')
        for mod,stage,name in [(prior,'S3','V5.13'),(terminal,'S1','S1'),(terminal,'S4','S4')]:
            m=mod.predict(mod.prepare(raw,h,s,stage,reference=f),fixed=f)
            diag=m['diagnostics']['dual']
            local=diag.get('registration') or {};coarse=m['diagnostics'].get('coarse') or {}
            winner=next((a for a in diag['branches'] if diag['pick']==f"BRANCH_{a['id']}"),{})
            rows.append(dict(case=r['case'],zoom=r['zoom'],noise=r['noise'],seed=r['seed'],photo=r['photo'],stage=name,
                    tip=m['tip'],stop=diag['stop'],reference=coarse.get('anchor'),shift=local.get('shift'),source=diag['decision'],
                    initial=winner.get('initial_total'),dual=winner.get('curve',{}).get('dual_columns'),merit=winner.get('merit')))
    write_csv(b.OUT/'negative_replay.csv',rows)
