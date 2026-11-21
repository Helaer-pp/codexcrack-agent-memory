"""Offline evaluation after the group prediction stream has been sealed."""
import json
import math
import numpy as np
from research.notch_identity_v58_strict.score import reason
from research.notch_identity_v58.lengths import measure
from research.v3_labelme_comparison.compare import evaluate,write_csv,PACKAGE
from .batch import OUT,SELECT,OLD,read,read_csv,sha


def main(g):
    src=OUT/(g+'.jsonl')
    assert sha(src)==read(OUT/(g+'_seal.json'))['predictions']
    selected={int(r['frame_id']):r for r in read_csv(SELECT) if r['dataset_id']==g}
    scores=[];lengths=[];jitter=[]
    for line in src.open():
        rec=json.loads(line);i=rec['frame']
        if i in selected:
            assert selected[i]['sha256']==rec['source_sha']
            shapes=read(PACKAGE/selected[i]['selected_json'])['shapes']
            gt=next((s['points'][0] for s in shapes if s['label']=='crack_tip'),None)
            paths=[np.array(s['points']) for s in shapes if s['label']=='crack_path']
        for placement,models in rec['placements'].items():
            meta=read(OLD/'evidence'/g/str(i)/'metadata.json')
            points=meta['current_points'] if placement=='original' else rec['geometry']['cur_points']
            for mode in ('full','raw_only'):
                m=models['S4'][mode]
                lengths.append(dict(group=g,frame=i,placement=placement,mode=mode,
                    **measure(m,dict(points_geometry=points,points_observed=True))))
            if i not in selected:continue
            for stage,bundle in models.items():
                for mode,clock in [('full','seconds'),('raw_only','raw_seconds')]:
                    m=bundle[mode];metric=evaluate(m,paths,gt)
                    d=m.get('diagnostics',{}).get('dual',{})
                    r=dict(group=g,frame=i,placement=placement,stage=stage,mode=mode,state='VISIBLE' if gt else 'UNCERTAIN',
                        gt=gt,**metric,stop=d.get('stop'),front=d.get('front'),pick=d.get('pick'),seconds=bundle[clock])
                    r['hit5']=None if gt is None else r['error_px'] is not None and r['error_px']<=5
                    r['failure']=reason(r);scores.append(r)
            if placement!=('bright' if rec['geometry'] else 'original'):continue
            m=models['S4']['full'];mjoint=evaluate(m,paths,gt)['joint']
            for alt in rec['sweeps']:
                if alt['placement']!=placement:continue
                j=evaluate(alt,paths,gt)
                jitter.append(dict(group=g,frame=i,direction=alt['direction'],delta=alt['delta'],
                    requested=alt['requested'],actual=alt['actual'],current=alt['current'],
                    correction=np.linalg.norm(np.subtract(alt['requested'],alt['actual']),axis=1).max(),
                    baseline_tip=m['tip'],tip=alt['tip'],baseline_joint=mjoint,joint=j['joint'],
                    drift=math.dist(m['tip'],alt['tip']) if m['tip'] and alt['tip'] else None))
    assert len(selected)==20
    write_csv(OUT/(g+'_scores.csv'),scores);write_csv(OUT/(g+'_lengths.csv'),lengths)
    if jitter:
        assert len(jitter)==200
        write_csv(OUT/(g+'_jitter.csv'),jitter)


if __name__=='__main__':
    import sys
    main(sys.argv[1])
