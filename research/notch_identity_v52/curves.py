"""Post-seal inspection of exact cumulative values and single-factor counterfactuals."""
import json,os
from pathlib import Path
import cv2
import numpy as np
from . import batch as b,terminal
from research.v3_labelme_comparison.compare import PACKAGE
from research.v3_labelme_comparison.infer import read_csv

def free_turn(score,seeds,scale,neck_credit):
    w,h=score.shape
    prev=np.full(h,-np.inf);best=0.;peak=None
    for x in range(w):
        a=np.pad(prev,2,constant_values=-np.inf)
        v=score[x]+np.maximum.reduce([a[i:i+h] for i in range(5)])
        v[v<-(.105 if neck_credit and x<=.24*scale else .025)*scale]=-np.inf
        if x<len(seeds):v=np.where(seeds[x],np.maximum(v,np.maximum(0,score[x])),v)
        y=int(np.argmax(v))
        if v[y]>best:best=v[y];peak=np.array([x,y])
        prev=v
    return peak

def generate(group,frame,m,row,mode):
    os.environ.setdefault('MPLCONFIGDIR',str(b.OUT/'plot_cache'))
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    cv2.setNumThreads(1)
    folder=b.OLD/'evidence'/group/str(frame)
    meta=b.read(folder/'metadata.json');scene=meta['evidence']['scene']
    off=np.asarray(scene['bounds'][:2])
    hint=np.rint(np.asarray(scene['root'] or scene['center'])-off).astype(int)
    gt=np.array(json.loads(row['gt']));audit=m['diagnostics']['dual']
    surface=b.OUT/'surfaces'/group/f'{frame:04d}_{mode}.npz'
    target=b.OUT/'curves'/group/f'{frame:04d}_{mode}.png'
    target.parent.mkdir(parents=True,exist_ok=True)
    fig,(ax,bottom)=plt.subplots(2,1,figsize=(9,5.6),sharex=True,layout='constrained')
    fig.suptitle(f'{group}  /  frame {frame}  /  {mode}  /  {audit["stop"]}')
    if not surface.exists():
        assert audit['stop']=='NO_NOTCH'
        ax.text(.07,.5,'No notch detected. No reachable DP lattice.',transform=ax.transAxes)
        why='口门定位失败，未形成可达状态或有效累计曲线。'
    else:
        with np.load(surface) as z:
            org=z['origin'];v=z['value'];path=z['path']
        with np.load(folder/'arrays.npz') as z:
            p=terminal.prepare(z['raw'],hint,scene['scale'])
            score,seeds,*_=terminal.fields(p,z['fixed__aligned'] if mode=='full' else None)
        for name,style in [('global',':'),('distal','-.')]:
            pt=audit.get(name+'_tip')
            if pt:
                ax.scatter(pt[0],audit[name+'_score'],label=name+' candidate',s=36,marker='o' if name=='global' else 'D')
        peak=np.array(audit['peak'])-org if audit.get('peak') else None
        xx=org[0]+np.arange(len(v));mx=v.max(axis=1);mx[~np.isfinite(mx)]=np.nan
        ax.plot(xx,mx,label='Best reachable V in each column',color='#225f82')
        ref=next(r for r in read_csv(b.SELECT) if r['dataset_id']==group and int(r['frame_id'])==frame)
        truth=b.read(PACKAGE/ref['selected_json'])
        manual=[]
        for shape in truth['shapes']:
            if shape['label']!='crack_path':continue
            pts=np.array(shape['points']);pts=pts[np.argsort(pts[:,0],kind='stable')]
            xs=np.where((xx>=pts[0,0])&(xx<=pts[-1,0]))[0]
            ys=np.rint(np.interp(xx[xs],pts[:,0],pts[:,1])-org[1]).astype(int)
            ok=(ys>=0)&(ys<v.shape[1]);xs,ys=xs[ok],ys[ok]
            if len(xs):
                val=v[xs,ys].copy();val[~np.isfinite(val)]=np.nan
                ax.plot(xx[xs],val,color='#b57d19',alpha=.8,label='V at manual path')
                span=max(3,round(scene['scale']*.04));idx=xx[xs]>=gt[0]-span
                manual.extend(score[xs[idx],ys[idx]].tolist())
                bottom.plot(xx[xs],score[xs,ys],color='#b57d19',alpha=.75,label='S at manual path')
        if len(path):
            x,y=path.T
            bottom.plot(xx[x],score[x,y],label='S along winning traceback',color='#007c67',alpha=.75)
        loc=np.rint(gt-org).astype(int);in_roi=bool((loc>=0).all() and (loc<np.array(v.shape)).all())
        val=v[tuple(loc)] if in_roi else -np.inf
        cf_turn=free_turn(score,seeds,scene['scale'],audit['decision']=='JOINT')
        unbounded,_,_=terminal.global_free_end_dp(score,seeds,1e8)
        cf_debt=unbounded[-1] if len(unbounded) else None
        err=lambda pt:float(np.linalg.norm(gt-(pt+org))) if pt is not None else np.inf
        e1=err(cf_turn);e2=err(cf_debt);base=err(peak)
        def show(x):return f'{x:.2f}' if np.isfinite(x) else '不可达'
        stop=audit['stop']
        if stop=='NO_CONFIRMED_PREEXISTING':cause='可靠参考未见新增且缺口前强谷连续长度或总分不足。'
        elif stop=='CLOSED_RIM':cause='回溯后闭环校验拒绝全局峰。'
        elif not seeds.any():cause='口门无合法种子。'
        elif stop in ('SHORT_PATH','INSUFFICIENT_TOTAL'):cause='可达峰未通过输出长度或总分下限。'
        elif not in_roi:cause='人工尖端超出搜索窗。'
        elif base>10 and e1<=10:cause='取消转弯代价后峰值进入 10 px，转向惩罚影响尖端。'
        elif base>10 and e2<=10:cause='放开累计负分下限后峰值进入 10 px，前段证据损失切断可达路径。'
        elif base>10 and e2<.5*base:cause='放开累计负分下限后误差减少一半以上，仍超出端点容差。前段可达性与末端净证据均需排查。'
        elif base>10 and e1<.5*base:cause='取消转弯代价后误差减少一半以上，仍超出端点容差。转向代价影响路径选择。'
        elif not np.isfinite(val):cause='人工尖端不可达。种子连通性、连续负分或可允许的列间斜率限制了搜索。'
        elif base>10:cause='两项单因素放宽均未恢复尖端，错误峰主要来自净证据排序，或与路径几何共同作用。'
        else:cause='峰值位于端点容差内，需结合覆盖、精度及历史误差判断局部退化。'
        if audit.get('pick')=='DISTAL':
            cause='当前端点由远端段正分和连续支撑裁决。下述放宽实验测量各自的原始全局峰，在本帧不能单独归因于转弯或负分限制。'
        evidence=''
        if peak is not None and len(path) and peak[0]+org[0]>gt[0]+2:
            suffix=path[path[:,0]+org[0]>gt[0]]
            gain=score[suffix[:,0],suffix[:,1]]
            evidence=f'越过人工端点后，获胜路径又延伸 {len(suffix)} 列，平均 S={gain.mean():.2f}，正分占比 {np.mean(gain>0):.0%}。'
        elif peak is not None and in_roi and peak[0]+org[0]<gt[0]-2:
            evidence=f'峰值到人工端点之间仍有 {gt[0]-org[0]-peak[0]:.1f} 列，人工端点列全高度最佳 V={show(mx[loc[0]])}。'
        why=(f"{cause} 人工点 V={show(val)}，全局峰 V={audit['score']:.2f}，输出下限 {audit['minimum']:.2f}。"
             f"{evidence}人工路径末段平均 S={show(np.mean(manual) if manual else np.nan)}。单独取消转弯代价、单独解除累计负分下限，候选峰误差分别为 {show(e1)} 和 {show(e2)} px。")
        for axis in (ax,bottom):
            if peak is not None:axis.axvline(peak[0]+org[0],ls=':',color='#b34242',label='Selected peak')
            axis.axvline(gt[0],ls='--',color='#705ca5',label='Manual tip')
            axis.grid(alpha=.15)
        # Show the whole reachable domain and both terminals while preserving local readability.
        reached=np.where(np.isfinite(mx))[0]
        xmax=max(gt[0],xx[reached[-1]] if len(reached) else gt[0],peak[0]+org[0] if peak is not None else gt[0])
        ax.set_xlim(org[0]-2,min(xx[-1]+2,xmax+12))
    bottom.axhline(0,color='.45',lw=.7);ax.set_ylabel('Cumulative V');bottom.set_ylabel('Net evidence S');bottom.set_xlabel('Original image x (px)')
    for axis in (ax,bottom):
        h,l=axis.get_legend_handles_labels()
        if h:axis.legend(dict(zip(l,h)).values(),dict(zip(l,h)).keys(),fontsize=7,loc='best')
    fig.savefig(target,dpi=115);plt.close(fig)
    if audit.get('pick'):why+=f" 裁决 {audit['pick']}，全局峰 {audit.get('global_tip')}，远端峰 {audit.get('distal_tip')}。"
    return why+' [累计得分曲线]('+target.relative_to(b.OUT).as_posix()+')'
