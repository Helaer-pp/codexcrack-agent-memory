"""Post-seal pixel-column audit on manual and predicted curves. No inference input."""
import json
import numpy as np
from research.v3_labelme_comparison.compare import PACKAGE,write_csv
from research.notch_identity_v510 import terminal as prev
from research.notch_identity_v510 import ridge
from . import terminal,rules
from .registration import material_reference
from .batch import OUT,OLD,SELECT,read,read_csv,old,SCALE,sha,GROUPS


def inspect(group,frame,placement,stage,mode,rec,gt,path,reason):
    folder=OLD/'evidence'/group/str(frame);meta=read(folder/'metadata.json');info=meta['input']
    l,t,r,b=rec['box'];ox,oy=meta['evidence']['scene']['bounds'][:2]
    cp,rp=(meta['current_points'],meta['fixed_points']) if placement=='original' else (rec['geometry']['cur_points'],rec['geometry']['ref_points'])
    fixed=old.read_fixed(info['reference'],info['ref_sha'])[t:b,l:r]
    with np.load(folder/'arrays.npz') as z:
        raw=z['raw'][t-oy:b-oy,l-ox:r-ox];reg=z['fixed__aligned'][t-oy:b-oy,l-ox:r-ox]
    base_mode='v5_10' if stage=='V5.10' else stage
    bundle=rec['placements'][placement][base_mode];m=bundle[mode];fd=bundle['full']['diagnostics']['dual']
    d=m['diagnostics']['dual'];w=fd.get('sensor_warp')
    if w:reg=material_reference(fixed,np.array(cp),np.array(rp),w['center_y'],SCALE)[0]
    prep=prev.prepare(raw,np.mean(cp,0)-[l,t],SCALE,'v5_10',fixed,np.mean(rp,0)-[l,t])
    tip=m['tip'];manual=path[np.argsort(path[:,0],kind='stable')]
    guide=manual;start=int(np.ceil(manual[0,0]));stop=int(np.floor(manual[-1,0]))
    segment='人工全段'
    if reason=='matched':
        base_tip=rec['baseline_tip']
        start=max(start,int(base_tip[0])+1)
        segment='历史端点后人工段'
    elif tip and np.linalg.norm(np.asarray(tip)-gt)<=10:
        segment='端点命中但路径未通过，人工全段'
    elif tip and tip[0]+2<stop:
        start=max(start,tip[0]+1);segment='漏追人工段'
    elif tip and tip[0]>gt[0]+2:
        guide=np.array(m['points']);start=max(guide[0,0],int(np.floor(gt[0]))+1);stop=tip[0];segment='多追预测段'
    a=dict(group=group,frame=frame,placement=placement,stage=stage,mode=mode,reason=reason,segment=segment,
           source=fd['decision'],start=start,stop=stop,n=0,red=None,raw=None,morph=None,pre_dip=None,dip=None,dip_clear=None,retained=None,longest=None)
    if prep is None or stop<start:return a,[]
    scene=prep[0];shift=(fd.get('registration') or {}).get('shift') or [0,0]
    fine,core,dip,strength,allow,delta,dual,old_dip,morph=rules.normal(scene,reg,shift,'S1')
    th=max(1.,2.7*scene.noise,.030*scene.span)
    if stage=='V5.10':
        fine,core,dip,strength,allow=prev.prior.normal_evidence(scene,reg,shift,None)
    xs=np.arange(start,stop+1,dtype=int)
    yy=np.rint(np.interp(xs,guide[:,0],guide[:,1])).astype(int)
    x=xs-l-scene.origin[0]-scene.front;y=yy-t-scene.origin[1]
    ok=(x>=0)&(x<len(allow))&(y>=0)&(y<allow.shape[1])
    x=x[ok,None];y=np.clip(y[ok,None]+np.arange(-2,3),0,allow.shape[1]-1)
    flags=dict(red=delta>th,raw=core,morph=morph,pre_dip=old_dip,dip=dip,dip_clear=~dip,retained=allow&(delta>th))
    vals={k:v[x,y].any(1) for k,v in flags.items()}
    a.update(n=len(x),longest=ridge.longest(vals['retained']),**{k:int(v.sum()) for k,v in vals.items()})
    detail=[dict(group=group,frame=frame,placement=placement,stage=stage,mode=mode,reason=reason,x=int(k),y=int(v),**{key:int(flag[j]) for key,flag in vals.items()}) for j,(k,v) in enumerate(zip(xs[ok],yy[ok]))]
    return a,detail


def main():
    output=[];columns=[];sel={(r['dataset_id'],int(r['frame_id'])):r for r in read_csv(SELECT)}
    import pathlib
    previous=OUT.parent/'v510_vertex_r02'
    for g in GROUPS:
        recs={r['frame']:r for r in map(json.loads,(OUT/(g+'.jsonl')).open()) if (g,r['frame']) in sel}
        prior={r['frame']:r for r in map(json.loads,(previous/(g+'.jsonl')).open()) if (g,r['frame']) in sel}
        req=[(int(r['frame']),r['placement'],'S4',r['mode'],'failure') for r in read_csv(OUT/(g+'_scores.csv')) if r['stage']=='S4' and r['joint']=='False']
        if g in ('group_c','three_point_bend'):
            for frame in ([38,54] if g=='group_c' else [215]):
                for place in recs[frame]['placements']:
                    for st in ('V5.10',*terminal.STAGES):req.append((frame,place,st,'full','matched'))
        for i,place,st,mode,reason in req:
            rec=(prior if st=='V5.10' else recs)[i]
            label=sel[g,i];assert label['sha256']==rec['source_sha']
            shapes=read(PACKAGE/label['selected_json'])['shapes']
            gt=next(s['points'][0] for s in shapes if s['label']=='crack_tip')
            path=min([np.array(s['points']) for s in shapes if s['label']=='crack_path'],key=lambda v:np.min(np.linalg.norm(v-gt,axis=1)))
            rec['baseline_tip']=prior[i]['placements'][place]['v5_10']['full']['tip']
            a,detail=inspect(g,i,place,st,mode,rec,gt,path,reason);output.append(a);columns.extend(detail)
    write_csv(OUT/'failure_evidence.csv',output);write_csv(OUT/'individual_columns.csv',columns)


if __name__=='__main__':main()
