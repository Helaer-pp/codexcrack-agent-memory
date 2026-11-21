"""Post-freeze manual-path evidence counts for the three requested regression frames."""
import json
import numpy as np
from research.v3_labelme_comparison.compare import PACKAGE,write_csv
from .batch import OUT,OLD,SELECT,read,read_csv,sha,old,SCALE
from .terminal import prepare,base,prior
from .ridge import signed_difference,longest


def main():
    rows=[]
    for group,frames,place in [('three_point_bend',[215],'original'),('group_c',[38,54],'bright')]:
        records={r['frame']:r for r in map(json.loads,(OUT/(group+'.jsonl')).open()) if r['frame'] in frames}
        for label in read_csv(SELECT):
            i=int(label['frame_id'])
            if label['dataset_id']!=group or i not in records:continue
            row=records[i];folder=OLD/'evidence'/group/str(i);meta=read(folder/'metadata.json');info=meta['input']
            assert label['sha256']==row['source_sha']
            geo=row['geometry'];l,t,r,b=row['box'];ox,oy=meta['evidence']['scene']['bounds'][:2]
            cp,rp=(meta['current_points'],meta['fixed_points']) if not geo else (geo['cur_points'],geo['ref_points'])
            fixed=old.read_fixed(info['reference'],info['ref_sha'])
            with np.load(folder/'arrays.npz') as z:
                raw=z['raw'][t-oy:b-oy,l-ox:r-ox];registered=z['fixed__aligned'][t-oy:b-oy,l-ox:r-ox]
            scene,band,_=prepare(raw,np.mean(cp,axis=0)-[l,t],SCALE,reference=fixed[t:b,l:r],reference_hint=np.mean(rp,axis=0)-[l,t])
            score,seeds,coarse,reg,source,stats=base.fields(scene,registered)
            fine,core,dip,strength,ready=prior.normal_evidence(scene,registered,reg['shift'],score)
            delta=signed_difference(scene,registered,reg['shift']);th=max(1.,2.7*scene.noise,.030*scene.span)
            m=row['placements'][place]['v5_10']['full'];tip=m['tip'];ox,oy=np.asarray(scene.origin)+[scene.front+l,t]
            shapes=read(PACKAGE/label['selected_json'])['shapes'];gt=next(s['points'][0] for s in shapes if s['label']=='crack_tip')
            paths=[np.array(s['points']) for s in shapes if s['label']=='crack_path']
            path=min(paths,key=lambda p:np.min(np.linalg.norm(p-gt,axis=1)))
            ordered=path[np.argsort(path[:,0])]
            xs=np.arange(max(int(np.ceil(ordered[0,0])),tip[0]+1),min(int(np.floor(gt[0])),int(np.floor(ordered[-1,0])))+1)
            ys=np.rint(np.interp(xs,ordered[:,0],ordered[:,1])).astype(int)
            x=xs-ox;y=ys-oy
            ix=x[:,None];iy=np.clip(y[:,None]+np.arange(-2,3),0,score.shape[1]-1)
            signed=(delta[ix,iy]>th).any(1);f=fine[ix,iy].any(1);ok=(ready[ix,iy]&(delta[ix,iy]>th)).any(1)
            rows.append(dict(group=group,frame=i,from_x=int(xs[0]),to_x=int(xs[-1]),columns=len(xs),threshold=th,
                positive=int(signed.sum()),fine=int(f.sum()),filtered_red=int(ok.sum()),longest=longest(ok),
                raw_dark=int(core[ix,iy].any(1).sum()),dipole=int(dip[ix,iy].any(1).sum())))
    write_csv(OUT/'posthoc_path_evidence.csv',rows)
    print(rows)

if __name__=='__main__':main()
