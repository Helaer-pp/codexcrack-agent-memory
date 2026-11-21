"""Post-freeze tracing of actual gate arguments, with no changes to decisions."""
import json
from contextlib import ExitStack
from unittest.mock import patch
import numpy as np
from research.v3_labelme_comparison.compare import write_csv
from . import batch,rules

def main():
    assert batch.sources()==batch.read(batch.OUT/'freeze.json')['sources']
    rows=[]
    for group,frames in [('three_point_bend',{215,248}),('group_c',{38,54,232,324,335,345,510})]:
        assert (batch.OUT/(group+'_seal.json')).exists()
        for rec in map(json.loads,(batch.OUT/(group+'.jsonl')).open()):
            i=rec['frame']
            if i not in frames:continue
            folder=batch.OLD/'evidence'/group/str(i);meta=batch.read(folder/'metadata.json')
            info=meta['input'];l,t,r,b=rec['box'];ox,oy=meta['evidence']['scene']['bounds'][:2]
            fixed=batch.old.read_fixed(info['reference'],info['ref_sha'])[t:b,l:r]
            with np.load(folder/'arrays.npz') as z:
                raw=z['raw'][t-oy:b-oy,l-ox:r-ox];aligned=z['fixed__aligned'][t-oy:b-oy,l-ox:r-ox]
            pl='bright' if group=='group_c' else 'original'
            cp,rp=(rec['geometry']['cur_points'],rec['geometry']['ref_points']) if pl=='bright' else (meta['current_points'],meta['fixed_points'])
            blank=rules.blank_crossing;compete=rules.connected_competition
            def record(gate,**values):
                rows.append(dict(group=group,frame=i,placement=pl,gate=gate,**values))
            def trace_blank(old,new,dual):
                answer=blank(old,new,dual)
                tail=new[new[:,0]>old[-1,0]];x,y=tail.T
                if len(x):
                    witness=dual[x,y];dx,dy=new[-1]-old[-1]
                    record('proposed_extension',dx=int(dx),dy=int(dy),dual=int(witness.sum()),run=rules.longest(witness),gap=rules.longest(~witness),blocked=bool(answer))
                return answer
            def trace_compete(candidates,dual,delta,threshold,scale):
                out=compete(candidates,dual,delta,threshold,scale)
                for path,item in candidates:
                    x,y=path.T;w=dual[x,y]
                    record('competition',branch=item['id'],initial=item['initial_total'],merit=item['merit'],promoted=item['promoted'],reason=item['reason'],blue=int((delta[x,y]<-threshold).sum()),dual=int(w.sum()),run=rules.longest(w),gap=rules.longest(~w))
                return out
            with ExitStack() as patches:
                patches.enter_context(patch.object(rules,'blank_crossing',trace_blank))
                patches.enter_context(patch.object(rules,'connected_competition',trace_compete))
                pred,_=batch.run_mode(raw,fixed,np.array(cp),np.array(rp),np.array([l,t]),'S4','full',aligned=aligned)
            saved=rec['placements'][pl]['S4']['full']
            assert pred['points']==saved['points'] and pred['tip']==saved['tip']
    keys=dict.fromkeys(k for row in rows for k in row)
    write_csv(batch.OUT/'gate_replay.csv',[dict(keys,**row) for row in rows])

if __name__=='__main__':main()
