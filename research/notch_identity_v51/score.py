"""Open only this group's annotations after its prediction file is sealed."""
import json
import cv2
import numpy as np
from .batch import OUT,SELECT,read,sha,save,GROUPS,ALGS
from research.v3_labelme_comparison.infer import read_csv,current
from research.v3_labelme_comparison.compare import evaluate,draw,write_csv,PACKAGE


def reason(r):
    if r['state']=='UNCERTAIN':return 'UNCERTAIN_LABEL'
    if r['status']!='VALID':return r['status']
    if r['joint']:return 'JOINT_HIT'
    if r['hit10']:return 'PATH_MISMATCH'
    if abs(r['dx'])<abs(r['dy']):return 'LATERAL_TIP_ERROR'
    return 'TIP_SHORT' if r['dx']<0 else 'TIP_OVERSHOOT'

def score(g):
    path=OUT/(g+'.jsonl')
    assert sha(path)==read(OUT/(g+'_seal.json'))['predictions']
    sel={int(r['frame_id']):r for r in read_csv(SELECT) if r['dataset_id']==g}
    records=[]
    for line in path.open():
        rec=json.loads(line);f=rec['frame']
        if f not in sel:continue
        row=sel[f]; assert rec['source_sha']==row['sha256']
        label=read(PACKAGE/row['selected_json']);shapes=label['shapes']
        tips=[s['points'][0] for s in shapes if s['label']=='crack_tip']
        paths=[np.asarray(s['points']) for s in shapes if s['label']=='crack_path']
        unc=[np.asarray(s['points']) for s in shapes if s['label']=='uncertain_region']
        assert (len(tips)==1 and paths and not unc) or (not tips and unc)
        gt=tips[0] if tips else None
        for alg,results in rec['models'].items():
            for mode in ('full','raw_only'):
                res=results[mode]
                metrics=evaluate(res,paths,gt)
                d=res['diagnostics'];ch=d.get('selected')
                a=d['candidates'][ch].get('trace',{}) if ch is not None else {}
                r=dict(group=g,frame=f,stage=alg,mode=mode,state='VISIBLE' if gt else 'UNCERTAIN',gt=gt,
                       **metrics,gate=a.get('gate'),first_loss=a.get('first_loss'),reconnections=a.get('reconnections'),
                       stop=a.get('stop'),body=a.get('body'),tail=a.get('tail'),front=a.get('front'))
                r['hit5']=None if gt is None else r['error_px'] is not None and r['error_px']<=5
                r['failure']=reason(r)
                records.append(r)
    assert len(records)==20*len(ALGS)*2
    write_csv(OUT/(g+'_scores.csv'),records)

if __name__=='__main__':
    import sys
    assert sys.argv[1] in GROUPS
    score(sys.argv[1])
