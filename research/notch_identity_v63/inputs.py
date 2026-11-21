"""Read archived input geometry for the three benchmarks and raw manifest for MT."""
from functools import lru_cache
import numpy as np
from . import batch as b
from research.unified_crack_tip_60q.features import CONFIG,scene_geometry


@lru_cache(maxsize=1)
def mt_rows():
    assert b.read(b.ROOT/'config/dataset_usage_policy.json')['groups']['group_h']=='DEVELOPMENT'
    rows=[r for r in b.read_csv(b.ROOT/'data/inputs/six_groups_manifest.csv') if r['dataset_alias']=='group_h']
    assert [int(r['frame_id']) for r in rows]==list(range(410))
    return rows


def metadata(group,i):
    if group!='group_h':
        return b.read(b.OLD/'evidence'/group/str(i)/'metadata.json')
    import json
    rows=mt_rows()
    row,ref=rows[i-1],rows[0]
    cp,rp=[np.asarray(json.loads(r['points'])) for r in (row,ref)]
    return dict(current_points=cp.tolist(),fixed_points=rp.tolist(),input=dict(
        current=row['input_image'],reference=ref['input_image'],image_sha=row['input_sha256'],ref_sha=ref['input_sha256']))


def complete_meta(meta,im,fixed):
    if 'evidence' not in meta:
        cp,rp=map(np.asarray,(meta['current_points'],meta['fixed_points']))
        scene=scene_geometry(im,cp,fixed,rp,None,CONFIG)
        meta['input'].update(width=im.shape[1],height=len(im))
        meta['evidence']=dict(scene=scene,reference_info=dict(fixed={}))
    return meta
