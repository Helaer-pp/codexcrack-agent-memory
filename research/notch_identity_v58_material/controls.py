"""Midpoint-matched 2 × 2 input controls. The unconstrained placements are diagnostic only."""
from pathlib import Path
import numpy as np
from .run import OUT, OLD, SELECT, GROUP, base, model, region, read, read_csv, save, sha, sources


def main():
    config=read(OUT/'freeze.json')
    assert sources()==config['sources']
    selected=sorted(int(r['frame_id']) for r in read_csv(SELECT) if r['dataset_id']==GROUP)
    records=[]
    for frame in selected:
        folder=OLD/'evidence'/GROUP/str(frame)
        meta=read(folder/'metadata.json')
        info=meta['input']
        fixed=base.read_fixed(info['reference'],info['ref_sha'])
        assert sha(folder/'arrays.npz')==meta['arrays_sha']
        with np.load(folder/'arrays.npz') as z:
            raw=z['raw']
        bounds=meta['evidence']['scene']['bounds']
        ox,oy=bounds[:2]
        geometry=region.geometry(raw,[ox,oy],fixed,meta,config)
        for area,box in [('original',bounds),('material',geometry['box'])]:
            l,t,r,b=box
            for anchors in ('original_cur','cur_points'):
                pair=np.array(geometry[anchors])
                hint=np.rint(pair.mean(0)-[l,t]).astype(int)
                m,_=model(raw[t-oy:b-oy,l-ox:r-ox],fixed[t:b,l:r],hint,np.linalg.norm(pair[1]-pair[0]),[l,t],pair,'full',None)
                records.append(dict(frame=frame,area=area,anchors=anchors,points=m['points'],tip=m['tip']))
    path=OUT/'control_predictions.json'
    save(path,records)
    save(OUT/'control_seal.json',dict(source=sha(Path(__file__)),predictions=sha(path),freeze=sha(OUT/'freeze.json')))


if __name__=='__main__':
    main()
