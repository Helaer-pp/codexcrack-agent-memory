"""Offline localization of the remaining failed synthetic cases on the frozen model."""
import json
from pathlib import Path
import numpy as np
from . import probes, terminal, batch as b
from .run import frozen
from research.v3_labelme_comparison.compare import write_csv


def main():
    frozen()
    out=[]
    rows=b.read_csv(b.OUT/'paired_probes.csv')
    for r in rows:
        if r['stage']!='S3' or r['passed']=='True':continue
        job=(r['case'],int(r['width']),float(r['contrast']),float(r['zoom']),int(r['noise']),int(r['seed']))
        a,f,h,s,gt=probes.images(job)
        gain,bias={'nominal':(1.,0),'dim':(.65,9),'bright':(1.16,15)}[r['photo']]
        raw=np.clip(gain*a+bias,0,255).astype('uint8')
        fixed=np.clip(gain*f+bias,0,255).astype('float32')
        m=terminal.predict(terminal.prepare(raw,h,s,'S3',reference=fixed),fixed=fixed,archive={})
        d=m['diagnostics']['dual']
        assert str(m['tip'])==(r['tip'] or 'None')
        win=next((a for a in d['branches'] if d['pick']==f"BRANCH_{a['id']}"),{})
        v=win.get('V',[]); net=None; dx=None
        if len(gt) and v:
            pos=int(round(gt[-1,0]-win['root'][0]))
            peak=int(round(win['tip'][0]-win['root'][0]))
            dx=(win['tip'][0]-gt[-1,0])/float(r['zoom'])
            if 0<=pos<len(v):net=v[peak]-v[pos]
        out.append(dict(case=r['case'],photo=r['photo'],width=r['width'],contrast=r['contrast'],zoom=r['zoom'],seed=r['seed'],noise=r['noise'],
            error=r['error'],coverage=r['coverage'],precision=r['precision'],tip=m['tip'],gt=gt[-1].tolist() if len(gt) else None,
            dx_normalized=dx,V_change_from_gt_column=net,pick=d['pick'],stop=d['stop'],
            candidates=json.dumps(b.old.clean(d['branches']),separators=(',',':'))))
    write_csv(b.OUT/'synthetic_failures.csv',out)


if __name__=='__main__':main()
