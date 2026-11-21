"""Post-freeze intervention: change only S4's upstream reference map on labelled frames."""
import json
import numpy as np
from .batch import OLD,OUT,GROUPS,old,run_mode,read,read_csv
from research.v3_labelme_comparison.compare import write_csv

def main():
    rows=[];old.warm()
    for group in GROUPS:
        selected={int(r['frame']) for r in read_csv(OUT/(group+'_scores.csv'))}
        for record in map(json.loads,(OUT/(group+'.jsonl')).open()):
            i=record['frame']
            if i not in selected:continue
            l,t,r,b=record['box']; folder=OLD/'evidence'/group/str(i)
            meta=read(folder/'metadata.json');info=meta['input']
            ox,oy=meta['evidence']['scene']['bounds'][:2]
            fixed=old.read_fixed(info['reference'],info['ref_sha'])[t:b,l:r]
            with np.load(folder/'arrays.npz') as z:
                raw=z['raw'][t-oy:b-oy,l-ox:r-ox]; historic=z['fixed__aligned'][t-oy:b-oy,l-ox:r-ox]
            for place,models in record['placements'].items():
                cp,rp=(meta['current_points'],meta['fixed_points']) if place=='original' else (record['geometry']['cur_points'],record['geometry']['ref_points'])
                counter,_=run_mode(raw,fixed,np.array(cp),np.array(rp),np.array([l,t]),'S4','full',aligned=historic,locked_warp=True)
                before=models['S3']['full'];after=models['S4']['full']
                rows.append(dict(group=group,frame=i,placement=place,S3=before['tip'],S4=after['tip'],S4_legacy_map=counter['tip'],
                    restores_S3=before['tip']==counter['tip'],matches_S4=after['tip']==counter['tip']))
    write_csv(OUT/'reference_intervention.csv',rows)

if __name__=='__main__':main()
