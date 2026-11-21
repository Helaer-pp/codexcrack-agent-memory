"""Isolate version effects on 520 frames with identical four-worker settings."""
import json
from concurrent.futures import ProcessPoolExecutor
from time import perf_counter
import cv2
import numpy as np
from research.notch_identity_v511 import batch as previous
from research.v3_labelme_comparison.compare import write_csv
from . import batch


def pair(i):
    folder=batch.OLD/'evidence'/'three_point_bend'/str(i)
    meta=batch.read(folder/'metadata.json')
    l,t,r,b=meta['evidence']['scene']['bounds']
    cp,rp=map(np.asarray,(meta['current_points'],meta['fixed_points']))
    fixed=batch.old.read_fixed(meta['input']['reference'],meta['input']['ref_sha'])[t:b,l:r]
    with np.load(folder/'arrays.npz') as z:raw=z['raw'];aligned=z['fixed__aligned']
    versions=[('V5.11',previous),('V5.12',batch)]
    if i%2:versions.reverse()
    rows=[]
    for name,mod in versions:
        model,dt=mod.run_mode(raw,fixed,cp,rp,np.array([l,t]),'S4','full',aligned=aligned)
        rows.append(dict(frame=i,version=name,seconds=dt,tip=model['tip'],status=model['status']))
    return rows


def main():
    g='three_point_bend'
    assert batch.read(batch.OUT/'freeze.json')['sources']==batch.sources()
    assert (batch.OUT/(g+'_seal.json')).is_file()
    with ProcessPoolExecutor(4,initializer=batch.old.warm) as pool:
        rows=[r for pair_rows in pool.map(pair,range(1,batch.GROUPS[g]+1),chunksize=2) for r in pair_rows]
    for name,dst in [('V5.11',previous.OUT),('V5.12',batch.OUT)]:
        refs={x['frame']:x['placements']['original']['S4']['full'] for x in map(json.loads,(dst/(g+'.jsonl')).open())}
        for row in rows:
            if row['version']==name:
                m=refs[row['frame']];row['identical_endpoint']=row['tip']==m['tip'] and row['status']==m['status']
    write_csv(batch.OUT/'paired_four_worker_tpb.csv',rows)


if __name__=='__main__':main()
