"""Offline MT development replay: cross the reference locator with the two frozen gate versions."""
from unittest.mock import patch
import json
import numpy as np
from research.notch_identity_v61 import batch as old,geometry as old_geom
from research.v3_labelme_comparison.compare import PACKAGE,evaluate,write_csv
from . import batch as b,geometry,domain,inputs
from .run import frozen,workers


def old_locator(im,hint,scale,edge):
    return old_geom.apex_with_center_fallback(im,hint,scale,edge,with_mode=True)


def main():
    frozen();workers()
    group='group_h'
    chosen={int(r['frame_id']):r for r in b.read_csv(b.SELECT) if r['dataset_id']==group}
    original={}
    for version,backend in [('6.1',old),('6.2',b)]:
        file=backend.OUT/'group_h.jsonl'
        assert backend.sha(file)==backend.read(backend.OUT/'group_h_seal.json')['predictions']
        original[version]={rec['frame']:rec for rec in map(json.loads,file.open(encoding='utf8')) if rec['frame'] in chosen}
    rows=[]
    locator=geometry.locate_reference_notch
    quiet=geometry.quiet_mouth
    for i,original_rec in original['6.2'].items():
        src=inputs.metadata(group,i)['input']
        assert src['image_sha']==chosen[i]['sha256']
        raw=b.old.current(src['current'],src['image_sha']);ref=b.old.read_fixed(src['reference'],src['ref_sha'])
        maps=original_rec['mappings']['original']['S2']
        cp,rp=map(np.asarray,(maps['cur'],maps['ref']))
        box=original_rec['box'];l,t,r,bot=box;origin=np.array([l,t])
        im,fixed=raw[t:bot,l:r],ref[t:bot,l:r]
        for loc,fn in [('6.1',old_locator),('6.2',locator)]:
            for gate,backend,floor in [('6.1',old,old_geom.quiet_mouth),('6.2',b,quiet)]:
                with patch.object(geometry,'locate_reference_notch',fn),patch.object(geometry,'quiet_mouth',floor):
                    prep=b.terminal.prepare(im,cp.mean(0)-origin,b.SCALE,'S2',fixed,rp.mean(0)-origin)
                mapped=domain.ReferenceMap(raw,ref,cp,rp,box,prep,'S2')
                model,_=backend.run_mode(im,fixed,cp,rp,origin,'S2','full',aligned=mapped,prepared=prep)
                if loc==gate:
                    baseline=original[loc][i]['placements']['original']['S2']['full']
                    assert model['points']==baseline['points'] and model['tip']==baseline['tip'] and model['status']==baseline['status']
                rows.append(dict(frame=i,locator=loc,gates=gate,status=model['status'],points=model['points'],tip=model['tip']))
    path=b.OUT/'group_h_factorial_predictions.json';b.save(path,b.old.clean(rows))
    b.save(b.OUT/'group_h_factorial_seal.json',dict(sha=b.sha(path),official_freeze=b.sha(b.OUT/'freeze.json')))
    scores=[]
    for row in b.read(path):
        shapes=b.read(PACKAGE/chosen[row['frame']]['selected_json'])['shapes']
        tip=next((s['points'][0] for s in shapes if s['label']=='crack_tip'),None)
        if tip is None:continue
        paths=[np.array(s['points']) for s in shapes if s['label']=='crack_path']
        scores.append(dict(frame=row['frame'],locator=row['locator'],gates=row['gates'],**evaluate(row,paths,tip)))
    write_csv(b.OUT/'group_h_factorial_scores.csv',scores)

if __name__=='__main__':
    main()
