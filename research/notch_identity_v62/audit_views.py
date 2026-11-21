"""Pair failure-frame evidence with each reachable branch's signed V(x)."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
from . import batch as b, difference_views as views
from .reference_views import font

TARGETS={'group_h':{41,74,78,96,216,221,397},'group_a':{113,299,366,398,504},'three_point_bend':{84,144,215,248,335,381,413,435,503},'group_c':{7,38,54,324,335,345,510}}


from research.notch_identity_v60.audit_views import draw

def group(g):
    dst=b.OUT/'audit_views'; dst.mkdir(parents=True,exist_ok=True)
    stage=b.read(b.OUT/'selection.json')['stage']
    for pl in (('original','bright') if g=='group_c' else ('original',)):
        scored={int(r['frame']):r for r in b.read_csv(b.OUT/(g+'_scores.csv')) if r['stage']==stage and r['placement']==pl and r['state']=='VISIBLE'}
        ids={i for i,r in scored.items() if r['joint']!='True' or i in TARGETS[g]}
        records={r['frame']:r for r in map(json.loads,(b.OUT/(g+'.jsonl')).open()) if r['frame'] in ids}
        for card,delta,row in views.source_frames(g,ids,placement=pl):
            i=row['frame']
            m=records[i]['placements'][pl][stage]['full']
            draw(card,m,json.loads(scored[i]['gt'])).save(dst/f'{g}_{pl}_{i:04d}.jpg',quality=92)
    print(g,'audit views complete',flush=True)


if __name__=='__main__':
    for group_id in b.GROUPS:group(group_id)
