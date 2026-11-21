"""Open manual annotations only after sealing the group's path stream."""
import json
import math
import numpy as np
from research.v3_labelme_comparison.compare import evaluate, write_csv, PACKAGE
from . import batch as b


def score(g):
    dst=b.OUT/(g+'.jsonl')
    assert b.read(b.OUT/(g+'_seal.json'))['predictions']==b.sha(dst)
    roster={int(r['frame_id']):r for r in b.read_csv(b.SELECT) if r['dataset_id']==g}
    rows=[]; lengths=[]; jitter=[]; parity=[]; curves=[]
    for rec in map(json.loads,dst.open()):
        i=rec['frame']
        gt=None; paths=[]
        if i in roster:
            assert rec['source_sha']==roster[i]['sha256']
            shapes=b.read(PACKAGE/roster[i]['selected_json'])['shapes']
            gt=next((s['points'][0] for s in shapes if s['label']=='crack_tip'),None)
            paths=[np.array(s['points']) for s in shapes if s['label']=='crack_path']
        for pl,models in rec['placements'].items():
            left,right=[models[s]['full'] for s in ('S2','S3')]
            d,e=[m['diagnostics']['dual'] for m in (left,right)]
            parity.append(dict(frame=i,placement=pl,status=left['status']==right['status'],tip=left['tip']==right['tip'],
                path=left['points']==right['points'],field=d.get('field_sha')==e.get('field_sha'),
                registration=d.get('registration')==e.get('registration') and left['diagnostics'].get('coarse')==right['diagnostics'].get('coarse'),
                field_present='field_sha' in d,field_other='field_sha' in e))
            lengths.append(dict(group=g,frame=i,placement=pl,status=right['status'],tip=right['tip'],
                         root=right['root'],path_length_px=right['path_length_px'],projected_length_px=right['projected_length_px']))
            if i not in roster:continue
            for stage,bundle in models.items():
                m=bundle['full']; diag=m['diagnostics']['dual']; metric=evaluate(m,paths,gt)
                rows.append(dict(group=g,frame=i,placement=pl,stage=stage,mode='full',state='VISIBLE' if gt else 'UNCERTAIN',
                    gt=gt,**metric,hit5=metric['error_px'] is not None and metric['error_px']<=5,seconds=bundle['seconds'],
                    pick=diag['pick'],stop=diag['stop'],source=diag['decision']))
                for branch in diag['branches']:
                    curves.append(dict(group=g,frame=i,placement=pl,stage=stage,branch=branch['id'],
                        winner=diag['pick']=='BRANCH_'+str(branch['id']),tip=branch['tip'],reason=branch['reason'],
                        initial=branch.get('initial_total'),merit=branch['merit'],details=branch.get('curve'),V=branch.get('V')))
        for sweep in rec['sweeps']:
            m=rec['placements'][sweep['placement']][sweep['stage']]['full']
            jitter.append(dict(group=g,frame=i,**sweep,status_change=sweep['status']!=m['status'],
                         drift=math.dist(sweep['tip'],m['tip']) if sweep['tip'] and m['tip'] else None))
    for label,data in [('scores',rows),('lengths',lengths),('jitter',jitter),('parity',parity),('curves',curves)]:
        write_csv(b.OUT/(g+'_'+label+'.csv'),data)


if __name__=='__main__':
    import sys
    for g in sys.argv[1:] or b.GROUPS:score(g)
