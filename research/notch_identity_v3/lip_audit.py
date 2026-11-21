"""Offline DEV-B audit. Rebuild measured candidate prefixes at frozen Stage 1 settings."""
import numpy as np
from . import detector
from .run import RUN,OLD,baseline,read
from .report import rows,stream,write_csv


def audit():
    records=[]
    chosen={int(r['frame']) for r in rows(RUN/'three_point_lips.csv')}
    for row in stream(RUN/'s1/dev.jsonl'):
        fid=row['frame']
        if row['group']!='three_point_bend' or fid not in chosen:
            continue
        folder=OLD/'evidence/three_point_bend'/str(fid)
        scene=read(folder/'metadata.json')['evidence']['scene']
        offset=np.array(scene['bounds'][:2])
        hint=np.rint(np.array(scene['root'] or scene['center'])-offset).astype(int)
        scale=scene['scale']
        with np.load(folder/'arrays.npz') as data:
            raw=data['raw']
            legacy=[(np.array(p)+offset).tolist() for p in baseline.locate_root(raw,hint,scale)]
            sl,origin,starts,signal,response,_,_=detector.prepare(raw,hint,scale)
            bonus=np.zeros_like(signal)
            for k in ('fixed','prev'):
                bonus+=np.where(data[k+'__valid'][sl],.04*np.clip(data[k+'__signed'][sl]/20,0,1),0)
            bonus[signal<1]=0
        d=row['full']['diagnostics']
        for i,start in enumerate(starts):
            o=baseline.follow(signal,response,bonus,start)
            c=d['candidates'][i]
            base=np.array(origin)+offset
            assert c['start']==(base+start).tolist()
            assert c['tip']==((base+o['tip']).tolist() if o['tip'] else None)
            pairs=[p[2] for p in d['pairs'] if i in p[:2]]
            stop=c.get('near_end')
            if stop is None:
                stop=int(c['start'][0]+detector.px(scale,.25))
            pts=np.array(o['points']).reshape(-1,2)
            near=detector.features(pts,start,signal,response,scale,stop-base[0]+1) if len(pts) else {}
            if 'near' in c:
                assert np.isclose(c['near']['score'],near['score'])
            records.append(dict(frame=fid,candidate=i,start=c['start'],tip=c['tip'],status=c['status'],
                old_available_starts=legacy,selected=i==d['selected'],merge_x=pairs,near_end=stop,
                near_score=near.get('score'),strong_density=near.get('density'),depth=near.get('depth'),
                attachment=near.get('attachment'),roughness=near.get('roughness'),used_in_near_ranking='near' in c))
    write_csv('three_point_candidate_scores.csv',records)


if __name__=='__main__':
    audit()

