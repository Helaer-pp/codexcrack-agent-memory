"""Collect publication evidence for every failed visible test frame after scoring."""
import json
import os
from pathlib import Path
import numpy as np
from .batch import OUT,GROUPS,read_csv
from .difference_views import source_frames


def main():
    os.environ.setdefault('MPLCONFIGDIR',str(OUT/'plot_cache'))
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    dest=OUT/'failures';dest.mkdir(parents=True,exist_ok=True)
    entries=[]
    for group in GROUPS:
        scores=[r for r in read_csv(OUT/(group+'_scores.csv')) if r['stage']=='S4' and r['joint']=='False']
        records={r['frame']:r for r in map(json.loads,(OUT/(group+'.jsonl')).open())}
        for placement,mode in dict.fromkeys((r['placement'],r['mode']) for r in scores):
            sub=dest/group/placement/mode;sub.mkdir(exist_ok=True,parents=True)
            picked={int(r['frame']):r for r in scores if (r['placement'],r['mode'])==(placement,mode)}
            for card,diff,row in source_frames(group,picked,mode,placement):
                i=row['frame'];key=f'{i:04d}';rec=records[i]
                card.save(sub/(key+'.jpg'),quality=91)
                result=rec['placements'][placement]['S4'][mode];dual=result['diagnostics']['dual']
                q=picked[i];gt=json.loads(q['gt']);path=OUT/'surfaces'/group/placement/(key+'_'+mode+'.npz')
                fig,ax=plt.subplots(figsize=(6.6,2.8),layout='constrained')
                with np.load(path) as z:
                    for branch,curve in zip(z['branch_ids'],z['curves']):
                        vals=curve.astype(float);vals[~np.isfinite(vals)|(vals<-1e8)]=np.nan
                        ax.plot(z['origin'][0]+np.arange(len(vals)),vals,lw=1,label=f'entry {branch}')
                    if not len(z['branch_ids']):ax.text(.03,.8,'No reachable entrance',transform=ax.transAxes)
                ax.axvline(gt[0],color='black',ls='--',label='manual tip')
                if result['tip']:ax.axvline(result['tip'][0],color='#b43125',ls=':',label='published tip')
                ax.set(xlabel='Original image x (px)',ylabel='Cumulative DP score',title=f'{group} / {i} / {placement} / {mode}')
                ax.legend(fontsize=7,ncol=3);fig.savefig(sub/(key+'.png'),dpi=120);plt.close(fig)
                winner=next((e for e in dual['branches'] if 'BRANCH_'+str(e['id'])==dual['pick']),None)
                if not winner:
                    why=f"无有效尖端，终止于 {dual['stop']}，记录分支 {len(dual['branches'])} 个。"
                else:
                    dx,dy=float(q['dx']),float(q['dy'])
                    why=f"分支 {winner['id']}。端点相对标注横向 {dx:+.1f}、纵向 {dy:+.1f} px。"
                    bridge=winner['bridge']
                    if bridge['accepted']:
                        why+=f"采用 {bridge['columns']} 列前向桥接，细脊占 {bridge['fine_fraction']:.0%}。"
                    elif bridge.get('raw_extension'):
                        why+=f"原图支持的末段延伸 {bridge['raw_extension']['columns']} 列。"
                    elif bridge.get('downstream_peak'):
                        why+='采用下游局部峰。'
                    else:why+='终点由本分支累计得分峰给出。'
                    why+=f" 初始峰 {winner['base_tip']}，最终 {winner['tip']}。"
                entries.append(dict(group=group,frame=i,placement=placement,mode=mode,error=q['error_px'],
                    coverage=q['coverage'],precision=q['precision'],cause=why,card=str(sub/(key+'.jpg')),curve=str(sub/(key+'.png'))))
    from research.v3_labelme_comparison.compare import write_csv
    if entries:write_csv(OUT/'failure_index.csv',entries)
    print('Failure cases rendered:',len(entries))


if __name__=='__main__':main()
