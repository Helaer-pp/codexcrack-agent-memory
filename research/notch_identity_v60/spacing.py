"""Isolate anchor spacing from the front-end crop and measured coarse motion."""
import json
import math
import cv2
import numpy as np
from . import batch as b,domain
from .run import frozen
from research.v3_labelme_comparison.compare import write_csv


def main():
    frozen()
    cv2.setNumThreads(1)
    rows=[]
    for group in ('group_a','three_point_bend'):
        selected={int(r['frame_id']) for r in b.read_csv(b.SELECT) if r['dataset_id']==group}
        stream=b.OUT/(group+'.jsonl')
        assert b.sha(stream)==b.read(b.OUT/(group+'_seal.json'))['predictions']
        for rec in map(json.loads, stream.open(encoding='utf8')):
            if rec['frame'] not in selected:continue
            i=rec['frame']
            meta=b.read(b.OLD/'evidence'/group/str(i)/'metadata.json')
            inp=meta['input']
            current=b.old.current(inp['current'],inp['image_sha'])
            fixed=b.old.read_fixed(inp['reference'],inp['ref_sha'])
            x,y,r,bt=rec['box'];origin=np.array([x,y])
            cp,rp=np.asarray(meta['current_points']),np.asarray(meta['fixed_points'])
            nominal=rec['placements']['original']['S2']['full']
            raw=current[y:bt,x:r];ref=fixed[y:bt,x:r]
            for factor in (.8,1.2):
                def stretch(pair):return pair.mean(0)+(pair-pair.mean(0))*factor
                ac,ar=stretch(cp),stretch(rp)
                prep=b.terminal.prepare(raw,ac.mean(0)-origin,b.SCALE,'S2',ref,ar.mean(0)-origin)
                mapped=domain.ReferenceMap(current,fixed,ac,ar,rec['box'],prep,'S2')
                m,_=b.run_mode(raw,ref,ac,ar,origin,'S2','full',aligned=mapped,prepared=prep)
                a,d=m['diagnostics']['dual'],nominal['diagnostics']['dual']
                rows.append(dict(group=group,frame=i,factor=factor,changed_status=m['status']!=nominal['status'],
                         changed_route=a['decision']!=d['decision'],changed_scale=a.get('scale')!=d.get('scale'),
                         changed_path=m['points']!=nominal['points'],
                         drift_px=math.dist(m['tip'],nominal['tip']) if m['tip'] and nominal['tip'] else None))
    write_csv(b.OUT/'spacing.csv',rows)

if __name__=='__main__':main()
