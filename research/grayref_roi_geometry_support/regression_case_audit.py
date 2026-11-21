"""Read-only, post-seal descriptive checks; never used to change inference."""
import argparse
import numpy as np
from grayref_roi_geometry_ablation.common import *
from grayref_roi_geometry_ablation.geometry import MODES

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    run = Path(parser.parse_args().run)
    assert (run/'evaluation_complete_exposed.json').exists()
    check_sources(run)
    seal = get(run/'frozen_exposed.json')
    pool = rows(run/'candidate_pool_exposed.csv')
    records = []
    # These are posthoc lost-pool cases, not runtime frame-specific rules.
    for group, fid in [('group_c', '232'), ('three_point_bend', '1')]:
        d = run/'frames'/group/fid
        for name in ['result.json.gz', 'evidence_arrays.npz', 'route_lineage.json.gz']:
            assert sha(d/name) == seal['files'][str((d/name).relative_to(run)).replace('\\', '/')]
        r = readgz(d/'result.json.gz')
        g = r['roi']
        with np.load(d/'evidence_arrays.npz') as q:
            nodes = {m: {(int(x)+g['xa'], int(y)+g['ya']) for x,y,*_ in q[m+'__nodes']} for m in MODES}
            segs = {m: {(int(x),int(y)): int(k) for k,x,y in q[m+'__segments']} for m in MODES}
            for v in pool:
                if (v['group'],v['frame_id'],v['mode'],v['path_good']) != (group,fid,MODES[0],'True'):
                    continue
                rank = int(v['rank'])
                obs = [(int(x),int(y)) for x,y,hit in r['results'][0]['paths'][rank]['observed_trace'] if hit]
                for m in MODES[1:]:
                    excluded = [p for p in obs if not q[m][p[1]-g['ya'],p[0]-g['xa']]]
                    missing = [p for p in obs if p not in nodes[m]]
                    split = [(p1,p2) for p1,p2 in zip(obs,obs[1:]) if p2[0]-p1[0]==1 and segs[MODES[0]].get(p1)==segs[MODES[0]].get(p2) and p1 in nodes[m] and p2 in nodes[m] and segs[m][p1]!=segs[m][p2]]
                    records.append(dict(group=group,frame_id=fid,rank=rank,mode=m,observed=len(obs),outside_search=len(excluded),missing_nodes=len(missing),split_links=len(split),first_excluded=excluded[:1],first_missing=missing[:1],first_split=split[:1]))
    csvwrite(run/'case_audit/exposed_good_path_survival.csv', records)
    d = run/'frames/three_point_bend/1'
    r = readgz(d/'result.json.gz')
    lineage = readgz(d/'route_lineage.json.gz')
    obs = {(int(x),int(y)) for x,y,hit in r['results'][0]['paths'][1]['observed_trace'] if hit}
    detail = {}
    with np.load(d/'evidence_arrays.npz') as q:
        for m in MODES:
            fragments = {}
            for k,x,y in q[m+'__segments']:
                fragments.setdefault(int(k),set()).add((int(x),int(y)))
            ids = [k for k,pts in fragments.items() if obs & pts]
            detail[m] = dict(original_observed=sorted(obs),fragment_ids=ids,fragments={k:sorted(fragments[k]) for k in ids},routes=[v for v in lineage[m] if set(ids)&set(v['fragment_ids'])])
    put(run/'case_audit/three_point_1_fragment_routes.json', detail)
    print('Post-seal regression case audit complete; detector unchanged.')

if __name__ == '__main__':
    main()
