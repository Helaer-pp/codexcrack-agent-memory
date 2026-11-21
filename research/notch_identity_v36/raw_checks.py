"""Independent frozen grayscale check on every crossed synthetic case."""
from ast import literal_eval
import numpy as np
from scipy.spatial import cKDTree
from research.notch_identity_v31.probes import sample
from research.notch_identity_v32.probes import gap_events
from research.v3_labelme_comparison.infer import read_csv
from research.v3_labelme_comparison.compare import write_csv
from . import terminal
from .batch import BASE,OUT

def main():
    rows=[]
    for r in read_csv(BASE/'raw_probes.csv'):
        if r['stage']!='v3_5':continue
        z=float(r['zoom']);width=int(r['width'])
        gray,h,s,gt=sample(r['case'],z,int(r['noise']),int(r['seed']),width,float(r['contrast']))
        gain,bias={'nominal':(1.,0),'dim':(.65,9),'bright':(1.16,15)}[r['photo']]
        p=terminal.prepare(np.clip(gain*gray+bias,0,255).astype('uint8'),h,s)
        m=terminal.predict(p,None);tip=m['tip']
        assert tip==(literal_eval(r['tip']) if r['tip'] else None)
        if len(gt) and tip:
            err=float(np.linalg.norm(gt[-1]-tip)/z)
            coverage=float(np.mean(cKDTree(m['points']).query(gt)[0]/z<=2.5))
            assert np.isclose(err,float(r['error'])) and np.isclose(coverage,float(r['coverage']))
        accepted=wrong=None
        if width and r['photo']=='nominal':
            accepted,wrong,rejected=gap_events(p,m,'v3_6',gt,width,z)
            assert (accepted,wrong,rejected)==tuple(int(r[k]) for k in ('accepted','wrong','rejected'))
        rows.append({**r,'stage':'v3_6','accepted':accepted,'wrong':wrong})
    assert len(rows)==468
    write_csv(OUT/'raw_probes.csv',rows)
if __name__=='__main__':main()
