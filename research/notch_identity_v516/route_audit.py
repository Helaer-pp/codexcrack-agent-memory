"""Post-freeze counterfactual for the predeclared group_c frame 7."""
from dataclasses import replace
import math
import numpy as np
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b, domain
from .run import jobs, frozen

def main():
    frozen()
    g='group_c';i=7
    roster=jobs(g,('S1',),False)
    assert roster[i-1][2]
    assert b.read(b.OUT/(g+'_seal.json'))['predictions']==b.sha(b.OUT/(g+'.jsonl'))
    meta=b.read(b.OLD/'evidence'/g/str(i)/'metadata.json')
    inp=meta['input'];cur=b.old.current(inp['current'],inp['image_sha'])
    fixed=b.old.read_fixed(inp['reference'],inp['ref_sha'])
    original=[np.array(meta[k]) for k in ('current_points','fixed_points')]
    x,y,r,bottom=meta['evidence']['scene']['bounds'];image=cur[y:bottom,x:r]
    bright=b.geometry(image,[x,y],fixed,meta,b.read(b.POLICY))
    box=bright['box'];l,t,r,bt=box
    raw=cur[t:bt,l:r];ref=fixed[t:bt,l:r];origin=np.array([l,t])
    rows=[]
    for pl,(cp,rp) in [('original',original),('bright',[np.array(bright[k]) for k in ('cur_points','ref_points')])]:
        prep=b.terminal.prepare(raw,cp.mean(0)-origin,b.SCALE,'S1',ref,rp.mean(0)-origin)
        for kind in ('native','quiet','changed'):
            scene,band,s=prep
            scene=scene if kind=='native' else replace(scene,quiet_notch=(kind=='quiet'))
            trial=(scene,band,s)
            mapped=domain.ReferenceMap(cur,fixed,cp,rp,box,trial,'S1')
            m,_=b.run_mode(raw,ref,cp,rp,origin,'S1','full',aligned=mapped,prepared=trial)
            d=m['diagnostics']['dual']
            rows.append(dict(placement=pl,mode=kind,native_change=scene.change_quantile,front=d['front'],
                             shift=(d.get('registration') or {}).get('shift'),source=d['decision'],tip=m['tip'],
                             stop=d['stop'],branches=[(v['id'],v['reason'],v.get('initial_total'),(v.get('curve') or {}).get('longest_dual_run')) for v in d['branches']]))
    write_csv(b.OUT/'route_counterfactual.csv',rows)
if __name__=='__main__':main()
