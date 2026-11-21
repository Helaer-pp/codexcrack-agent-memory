"""Score only sealed predictions and verify that displaced point patches stay illuminated."""
import json,math
import numpy as np
from research.v3_labelme_comparison.compare import PACKAGE,evaluate,write_csv
from research.notch_identity_v58 import batch as v58
from .run import OUT,OLD,SELECT,GROUP,N,read,read_csv,sha,save,base


def annotations():
    return {int(r['frame_id']):r for r in read_csv(SELECT) if r['dataset_id']==GROUP}


def load_truth(row):
    shapes=read(PACKAGE/row['selected_json'])['shapes']
    gt=next((s['points'][0] for s in shapes if s['label']=='crack_tip'),None)
    return gt,[np.array(s['points']) for s in shapes if s['label']=='crack_path']


def patch_min(image,origin,p):
    x,y=np.asarray(p,int)-origin
    patch=image[y-4:y+5,x-4:x+5]
    assert patch.shape==(9,9)
    return int(patch.min())


def main(out=OUT):
    series=out/'group_c.jsonl'
    assert sha(series)==read(out/'seal.json')['predictions']
    sel=annotations();scores=[];points=[];lengths=[];jitter=[]
    old_by_key={(int(r['frame']),r['stage'],r['mode']):r for r in read_csv(v58.OUT/'group_c_scores.csv')}
    for line in series.open():
        row=json.loads(line);i=row['frame'];geo=row['geometry']
        folder=OLD/'evidence'/GROUP/str(i);meta=read(folder/'metadata.json');info=meta['input']
        off=np.array(meta['evidence']['scene']['bounds'][:2])
        ref=base.read_fixed(info['reference'],info['ref_sha'])
        with np.load(folder/'arrays.npz') as z:raw=z['raw']
        for target in ('ref','cur'):
            pts=geo[target+'_points'] if geo else []
            image,origin=(ref,np.zeros(2,int)) if target=='ref' else (raw,off)
            for j,p in enumerate(pts):
                low=patch_min(image,origin,p)
                floor=geo['floors'][int(target=='cur')]
                assert low>=floor
                prev=geo['original_'+target][j]
                points.append(dict(frame=i,image=target,point='P'+str(j+1),old_x=prev[0],old_y=prev[1],
                    x=p[0],y=p[1],patch_min=low,floor=floor,box=geo['box']))
        m=row['models']['bright']
        for mode in ('full','raw_only'):
            d=m[mode]
            if d['points']:
                a=np.asarray(d['points']);l,t,r,b=geo['box']
                assert ((a>=[l,t])&(a<[r,b])).all()
                assert abs(np.linalg.norm(np.diff(a,axis=0),axis=1).sum()-d['path_length_px'])<1e-6
            lengths.append(dict(frame=i,mode=mode,status=d['status'],root=d['root'],tip=d['tip'],
                                path_length_px=d['path_length_px'],projected_length_px=d['projected_length_px']))
        if i not in sel:continue
        assert sel[i]['sha256']==row['source_sha']
        gt,paths=load_truth(sel[i]);nominal=evaluate(m['full'],paths,gt)
        for alg,models in row['models'].items():
            for mode in ('full','raw_only'):
                result=models[mode];metric=evaluate(result,paths,gt)
                scores.append(dict(frame=i,stage=alg,mode=mode,gt=gt,**metric,root=result['root'],tip=result['tip'],
                      stop=result['diagnostics']['dual']['stop'],r04_error=old_by_key[i,'v5_8',mode]['error_px'],
                      v57_error=old_by_key[i,'v5_7',mode]['error_px']))
        for j in row['sweeps']:
            alt=j['geo'];metric=evaluate(j,paths,gt);tip=m['full']['tip']
            drift=math.dist(j['tip'],tip) if j['tip'] and tip else None
            corr=None
            if alt:
                for k,image,orig,floor in [('ref',ref,[0,0],alt['floors'][0]),('cur',raw,off,alt['floors'][1])]:
                    for pt in alt[k+'_points']:assert patch_min(image,orig,pt)>=floor
                corr=float(np.linalg.norm(np.subtract(alt['requested_ref'],alt['ref_points']),axis=1).max())
            jitter.append(dict(frame=i,kind=j['kind'],requested=j['delta'],max_clip_px=corr,
                ref_points=alt['ref_points'] if alt else None,cur_points=alt['cur_points'] if alt else None,
                nominal_tip=tip,tip=j['tip'],drift_px=drift,base_joint=nominal['joint'],joint=metric['joint'],
                base_valid=tip is not None,valid=j['tip'] is not None))
    assert len(lengths)==2*N and len(scores)==80 and len(jitter)==200
    for name,rows in [('crack_lengths',lengths),('anchor_audit',points),('scores',scores),('jitter',jitter)]:
        write_csv(out/(name+'.csv'),rows)
    print('Validated points, paths and',len(jitter),'additional paired perturbations.')


if __name__=='__main__':main()
