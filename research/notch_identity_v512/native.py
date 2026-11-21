"""Repeat raw-frame cropping and local registration for synchronized anchor perturbations."""
from concurrent.futures import ProcessPoolExecutor
import math
import sys

import numpy as np
from research.unified_crack_tip_60q.features import CONFIG, scene_geometry, register_reference
from research.v3_labelme_comparison.compare import write_csv
from .batch import OUT, OLD, POLICY, SELECT, read, old, geometry, synchronized, run_mode, read_csv, sources, sha, save


def compare(job):
    group, frame = job
    folder = OLD/'evidence'/group/str(frame)
    meta = read(folder/'metadata.json')
    info = meta['input']
    current = old.current(info['current'], info['image_sha'])
    fixed = old.read_fixed(info['reference'], info['ref_sha'])
    cp, rp = (np.array(meta[k]) for k in ('current_points', 'fixed_points'))
    initial = meta['evidence']['scene']['bounds']
    x, y, r, b = initial
    small = current[y:b, x:r]
    settings = read(POLICY) if group == 'group_c' else None
    if settings:
        geo = geometry(small, [x,y], fixed, meta, settings)
        cp, rp = np.array(geo['cur_points']), np.array(geo['ref_points'])
    rows = []
    for _, direction, delta, cur, ref in synchronized(cp, rp):
        if settings:
            geo = geometry(small, [x,y], fixed, meta, settings, ref-np.array(settings['reference_virtual_points']))
            cur, ref = np.array(geo['cur_points']), np.array(geo['ref_points'])
        scene = scene_geometry(current, cur, fixed, ref, None, CONFIG)
        l,t,r,b = scene['bounds']
        if settings:
            # The material envelope is defined on the specimen, independent of the requested point pair.
            l,t,r,b = geo['box']
            scene = dict(scene, bounds=[l,t,r,b])
        aligned, _ = register_reference(fixed, current, ref, cur, scene, CONFIG)
        result,_ = run_mode(current[t:b,l:r], fixed[t:b,l:r], cur, ref, np.array([l,t]),
                            'S4','full',aligned=aligned['aligned'])
        tip = result['tip']
        if delta == 0:
            nominal, status = tip, result['status']
        rows.append(dict(group=group, frame=frame, direction=direction, delta=delta,
                         bounds=[l,t,r,b], reference_points=ref.tolist(), current_points=cur.tolist(),
                         nominal=nominal, tip=tip, status=result['status'], status_change=result['status']!=status,
                         drift=math.dist(tip,nominal) if nominal and tip else None))
    return rows


def main(group):
    if group != 'group_a':
        assert read(OUT/'freeze.json')['sources'] == sources()
        assert (OUT/(group+'_seal.json')).exists()
    ids = [int(r['frame_id']) for r in read_csv(SELECT) if r['dataset_id']==group]
    with ProcessPoolExecutor(4, initializer=old.warm) as pool:
        rows = sum(pool.map(compare,[(group,i) for i in ids]),[])
    path = OUT/(group+'_native_jitter.csv')
    write_csv(path,rows)
    save(OUT/(group+'_native_seal.json'),dict(rows=len(rows),csv=sha(path),sources=sources()))


if __name__=='__main__':main(sys.argv[1])
