"""Score a sealed GROUP_A-only pilot before committing to a new full development sweep."""
from concurrent.futures import ProcessPoolExecutor
from .batch import OUT,OLD,SELECT,run_one,warm,sources,save
from .probes import synthetic_gate
from research.v3_labelme_comparison.infer import read_csv
from research.v3_labelme_comparison.compare import PACKAGE,evaluate
from .batch import read
import numpy as np

def run():
    assert synthetic_gate(OUT)
    sel={int(r['frame_id']):r for r in read_csv(SELECT) if r['dataset_id']=='group_a'}
    image_rows=[r for r in read_csv(OLD/'manifests/input_inventory.csv') if r['group']=='group_a' and int(r['frame_id']) in sel]
    with ProcessPoolExecutor(6,initializer=warm) as pool:
        records=list(pool.map(run_one,[(r,False) for r in image_rows]))
    save(OUT/'group_a_pilot.json',dict(sources=sources(),records=records))
    errors=[]
    for rec in records:
        i=rec['frame'];shapes=read(PACKAGE/sel[i]['selected_json'])['shapes']
        gt=next((s['points'][0] for s in shapes if s['label']=='crack_tip'),None)
        paths=[s['points'] for s in shapes if s['label']=='crack_path']
        if gt is not None:
            m=rec['models']['v4_1']['full'];r=evaluate(m,paths,gt)
            errors.append(r['error_px']);print(i,m['tip'],m['diagnostics']['dual']['stop'],round(r['error_px'],2),r['joint'])
    print('median',np.median(errors),flush=True)
if __name__=='__main__':run()
