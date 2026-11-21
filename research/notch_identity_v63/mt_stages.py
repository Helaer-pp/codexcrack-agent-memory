"""Offline MT mechanism check. Cross the new geometry with the frozen mapping and terminal gates."""
import json
import numpy as np
from research.notch_identity_v62 import batch as old,domain as old_map
from research.v3_labelme_comparison.compare import PACKAGE,evaluate,write_csv
from . import inputs,domain,batch as b
from .run import frozen,workers


def main():
    frozen();workers()
    roster={int(r['frame_id']):r for r in b.read_csv(b.SELECT) if r['dataset_id']=='group_h'}
    captures={}
    for version,backend in [('V62',old),('V63',b)]:
        src=backend.OUT/'group_h.jsonl'
        assert backend.sha(src)==backend.read(backend.OUT/'group_h_seal.json')['predictions']
        captures[version]={rec['frame']:rec for rec in map(json.loads,src.open(encoding='utf8')) if rec['frame'] in roster}
    predictions=[]
    for i in sorted(roster):
        rec=captures['V63'][i]
        meta=inputs.metadata('group_h',i)['input']
        assert rec['source_sha']==roster[i]['sha256']==meta['image_sha']
        im=b.old.current(meta['current'],meta['image_sha']);fixed=b.old.read_fixed(meta['reference'],meta['ref_sha'])
        box=rec['box'];l,t,r,bot=box;origin=np.array([l,t])
        raw=im[t:bot,l:r];ref=fixed[t:bot,l:r]
        mapping=rec['mappings']['original']['S2']
        cp,rp=map(np.array,(mapping['cur'],mapping['ref']))
        prep=b.terminal.prepare(raw,cp.mean(0)-origin,b.SCALE,'S2',ref,rp.mean(0)-origin)
        for key in ('V62','geometry','geometry_mask','V63'):
            if key in captures:
                model=captures[key][i]['placements']['original']['S2']['full']
            else:
                mapper=old_map if key=='geometry' else domain
                mapped=mapper.ReferenceMap(im,fixed,cp,rp,box,prep,'S2')
                model,_=old.run_mode(raw,ref,cp,rp,origin,'S2','full',aligned=mapped,prepared=prep)
            predictions.append(dict(frame=i,variant=key,stop=model['diagnostics']['dual']['stop'],
                                     **{k:model[k] for k in ('status','tip','points')}))
    path=b.OUT/'group_h_stage_predictions.json'
    b.save(path,b.old.clean(predictions));b.save(b.OUT/'group_h_stage_seal.json',dict(sha=b.sha(path)))
    scores=[]
    for row in b.read(path):
        shapes=b.read(PACKAGE/roster[row['frame']]['selected_json'])['shapes']
        gt=next((s['points'][0] for s in shapes if s['label']=='crack_tip'),None)
        if gt is None:continue
        paths=[np.array(s['points']) for s in shapes if s['label']=='crack_path']
        scores.append(dict(frame=row['frame'],variant=row['variant'],stop=row['stop'],**evaluate(row,paths,gt)))
    write_csv(b.OUT/'group_h_stages.csv',scores)

if __name__=='__main__':main()
