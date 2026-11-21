"""Post-score route isolation; never used for model selection or regular inference."""
import json
from dataclasses import replace
import numpy as np
import cv2
from . import batch as b, inputs, domain
from research.notch_identity_v60.batch import OUT as PREV
from research.v3_labelme_comparison.compare import evaluate,PACKAGE,write_csv

def main():
    cv2.setNumThreads(1)
    rows=[]
    for g in ('group_c','group_h'):
        path=b.OUT/(g+'.jsonl')
        assert b.sha(path)==b.read(b.OUT/(g+'_seal.json'))['predictions']
        prior={(r['frame'],r['placement']) for r in b.read_csv(PREV/(g+'_scores.csv')) if r['stage']=='S2' and r['joint']=='True'} if g=='group_c' else set()
        roster={r['frame_id']:r for r in b.read_csv(b.SELECT) if r['dataset_id']==g}
        ids={(int(r['frame']),r['placement']) for r in b.read_csv(b.OUT/(g+'_scores.csv'))
             if r['source']=='PREEXISTING_CHECK' and r['joint']=='False' and (g=='group_h' or (r['frame'],r['placement']) in prior)}
        # Quiet route for the two placements at frame 7 is explicitly requested in the brief.
        if g=='group_c':ids.update(((7,'bright'),(7,'original')))
        for rec in map(json.loads,path.open(encoding='utf8')):
            for pl in rec['placements']:
                i=rec['frame']
                if (i,pl) not in ids:continue
                meta=inputs.metadata(g,i);inp=meta['input']
                image=b.old.current(inp['current'],inp['image_sha']);ref=b.old.read_fixed(inp['reference'],inp['ref_sha'])
                x,y,r,bt=rec['box'];off=np.array([x,y]);raw=image[y:bt,x:r];fixed=ref[y:bt,x:r]
                mapping=rec['mappings'][pl]['S2'];cp,rp=map(np.asarray,(mapping['cur'],mapping['ref']))
                prep=b.terminal.prepare(raw,cp.mean(0)-off,b.SCALE,'S2',fixed,rp.mean(0)-off)
                p,band,stage=prep; changed=(replace(p,quiet=not p.quiet),band,stage)
                mapped=domain.ReferenceMap(image,ref,cp,rp,rec['box'],changed,stage)
                model,_=b.run_mode(raw,fixed,cp,rp,off,stage,'full',aligned=mapped,prepared=changed)
                a=roster[str(i)];assert a['sha256']==inp['image_sha']
                shapes=b.read(PACKAGE/a['selected_json'])['shapes']
                gt=next(s['points'][0] for s in shapes if s['label']=='crack_tip')
                paths=[np.array(s['points']) for s in shapes if s['label']=='crack_path']
                baseline=rec['placements'][pl][stage]['full']
                base_score=evaluate(baseline,paths,gt);alt=evaluate(model,paths,gt)
                rows.append(dict(group=g,placement=pl,frame=i,official_route=baseline['diagnostics']['dual']['decision'],
                                 diagnostic_route=model['diagnostics']['dual']['decision'],official_error=base_score['error_px'],
                                 replay_error=alt['error_px'],replay_joint=alt['joint'],replay_stop=model['diagnostics']['dual']['stop']))
    write_csv(b.OUT/'route_replay.csv',rows)

if __name__=='__main__':main()
