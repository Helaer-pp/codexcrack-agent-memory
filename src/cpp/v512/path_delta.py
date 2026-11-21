"""Quantify nonidentical polylines using the release DLL and the exact sealed input."""
import csv
import os
import sys
import numpy as np
from .verify_abi import BUILD,DEST,batch,load,create,image,pair,pathof,Result,C

def main(g):
    if g=='group_c':os.environ['CRACKV4_V512_MATERIAL_POLICY']=str(batch.POLICY)
    else:os.environ.pop('CRACKV4_V512_MATERIAL_POLICY',None)
    assert batch.sha(BUILD/'CrackV4.dll')==batch.read(DEST/'freeze.json')['dll']
    wanted={int(r['frame']) for r in batch.read_csv(DEST/(g+'_all.csv')) if r['same_path']=='False'}
    lib=load();h=None;rows=[]
    try:
        for rec in map(__import__('json').loads,(batch.OUT/(g+'.jsonl')).open()):
            i=rec['frame']
            if i not in wanted:continue
            meta=batch.read(batch.OLD/'evidence'/g/str(i)/'metadata.json');info=meta['input']
            if not h:
                ref=batch.old.read_fixed(info['reference'],info['ref_sha']);h=create(lib,ref,meta['fixed_points'])
            cur=batch.old.current(info['current'],info['image_sha']);o=Result(size=C.sizeof(Result))
            assert not lib.CrackV4Process(h,C.byref(image(cur)),pair(meta['current_points']),C.byref(o))
            path=np.array(pathof(lib,h,0))
            m=rec['placements']['bright' if g=='group_c' else 'original']['S4']['full']
            expected=np.array(m['points'])
            same_x=path.shape==expected.shape and np.array_equal(path[:,0],expected[:,0]) if len(path) and len(expected) else False
            rows.append(dict(frame=i,same_columns=same_x,max_y=int(np.abs(path[:,1]-expected[:,1]).max()) if same_x else '',
                arc_delta=o.length-(m['path_length_px'] or 0),expected_points=len(expected),actual_points=len(path)))
    finally:
        if h:lib.CrackV4Destroy(h)
    dest=DEST/(g+'_path_delta.csv')
    with dest.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,['frame','same_columns','max_y','arc_delta','expected_points','actual_points']);w.writeheader();w.writerows(rows)
if __name__=='__main__':main(sys.argv[1])
