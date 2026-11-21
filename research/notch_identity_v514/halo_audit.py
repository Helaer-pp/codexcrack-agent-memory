"""Compare terminal curve changes at identical image columns after sealing S1 and S2."""
import json
import numpy as np
from . import batch as b
from research.v3_labelme_comparison.compare import write_csv


def main():
    rows=[]
    for g in b.GROUPS:
        assert b.read(b.OUT/(g+'_seal.json'))['predictions']==b.sha(b.OUT/(g+'.jsonl'))
        scores=b.read_csv(b.OUT/(g+'_scores.csv'))
        picked={(int(r['frame']),r['placement']):r for r in scores if r['stage']=='S2' and r['state']=='VISIBLE'}
        for rec in map(json.loads,(b.OUT/(g+'.jsonl')).open()):
            for pl,models in rec['placements'].items():
                i=rec['frame']
                if (i,pl) not in picked:continue
                gt=json.loads(picked[i,pl]['gt'])
                d1,d2=(models[s]['full']['diagnostics']['dual'] for s in ('S1','S2'))
                prior={v['id']:v for v in d1['branches']}
                for cur in d2['branches']:
                    before=prior.get(cur['id'])
                    if not before or not before.get('V') or not cur.get('V'):continue
                    common=before['root']==cur['root'] and len(before['V'])==len(cur['V'])
                    p=np.array(before['V']);q=np.array(cur['V']);col=int(round(gt[0]-cur['root'][0]))
                    terminal=cur['tip'][0]-cur['root'][0]
                    original=before['tip'][0]-before['root'][0]
                    eligible=common and 0<=col<len(q)
                    rows.append(dict(group=g,frame=i,placement=pl,branch=cur['id'],winner=d2['pick']==f"BRANCH_{cur['id']}",
                       same_proposal=common,columns=len(q),reaches_gt_x=eligible,gt_x=gt[0],start_x=cur['root'][0],proposal_end_x=cur['root'][0]+len(q)-1,
                       old_tip=before['tip'],new_tip=cur['tip'],old_tip_x_minus_gt=before['tip'][0]-gt[0],new_tip_x_minus_gt=cur['tip'][0]-gt[0],
                       old_peak_charge=p[original]-q[original] if common else None,
                       gt_column_charge=p[col]-q[col] if eligible else None,
                       charge_at_new_tip=p[terminal]-q[terminal] if common else None,
                       old_peak_over_gt=p[original]-p[col] if eligible else None,
                       new_peak_over_gt=q[terminal]-q[col] if eligible else None))
    write_csv(b.OUT/'halo_curve_audit.csv',rows)

if __name__=='__main__':main()
