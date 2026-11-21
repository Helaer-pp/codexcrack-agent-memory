"""Development-only correction supplement. Both validation groups remain closed."""
import json,os
from statistics import mean
import numpy as np
from . import batch as b
from research.notch_identity_v42.reporting import pack,table,read_csv,num


def main():
    assert b.read(b.OUT/'freeze.json')['sources']==b.sources()
    assert b.sha(b.OUT/'group_a.jsonl')==b.read(b.OUT/'group_a_seal.json')['predictions']
    assert b.sha(b.OUT/'jitter_predictions.jsonl')==b.read(b.OUT/'jitter_seal.json')['predictions']
    for g in ('three_point_bend','group_c'):
        assert not (b.OUT/(g+'.jsonl')).exists()
    os.environ.setdefault('MPLCONFIGDIR',str(b.OUT/'plot_cache'))
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    scores=read_csv(b.OUT/'group_a_scores.csv')
    predictions=[json.loads(line) for line in (b.OUT/'group_a.jsonl').open()]
    selected=[r for r in scores if r['stage']=='v5_8' and r['state']=='VISIBLE']
    details=[]
    for r in selected:
        if r['joint']=='True':continue
        i=int(r['frame']);mode=r['mode'];m=predictions[i-1]['models']['v5_8'][mode]
        data=b.OUT/'surfaces'/'group_a'/f'{i:04d}_{mode}.npz'
        dest=b.OUT/'curves'/'group_a'/f'{i:04d}_{mode}.png';dest.parent.mkdir(exist_ok=True,parents=True)
        fig,ax=plt.subplots(figsize=(8,3.4),layout='constrained')
        with np.load(data) as z:
            for j,vals in zip(z['branch_ids'],z['curves']):
                vals=vals.copy();vals[~np.isfinite(vals)]=np.nan
                ax.plot(z['origin'][0]+np.arange(len(vals)),vals,label=f'entry {j}')
        ax.axvline(json.loads(r['gt'])[0],ls='--',color='black',label='manual tip')
        if m['tip']:ax.axvline(m['tip'][0],ls=':',color='red',label='published tip')
        ax.set(xlabel='Original x (px)',ylabel='Max reachable score',title=f'GROUP_A / {i} / {mode} / r05')
        ax.legend();fig.savefig(dest,dpi=120);plt.close(fig)
        details.append([f'[{i}](difference_views/frames/group_a/{i:04d}.jpg)',mode,num(r['error_px']),num(r['coverage']),num(r['precision']),m['tip'],f'[分支得分]({dest.relative_to(b.OUT).as_posix()})'])
    stats=read_csv(b.OUT/'jitter_summary.csv')
    probes=read_csv(b.OUT/'paired_probes.csv')
    chosen=[next((a for a in d['branches'] if d['pick']=='BRANCH_'+str(a['id'])),{}) for d in
            [p['models']['v5_8']['full']['diagnostics']['dual'] for p in predictions]]
    rr=[r for r in selected if r['mode']=='full']
    res=dict(full_joint=sum(r['joint']=='True' for r in rr),visible=len(rr),
        negative_fp=sum(r['negative']=='True' and r['valid']=='True' for r in probes),
        weak_pass=sum(r['case']=='P1_weak_gap' and r['passed']=='True' for r in probes),
        published_bridges=sum(a.get('bridge',{}).get('accepted',False) for a in chosen),
        jitter_max=max(float(r['maximum'] or 0) for r in stats),validation='NOT_RUN')
    b.save(b.OUT/'development_metrics.json',res)
    pack(b,'STRICT_DEV.md',['# V5.8 r05 三项桥接护栏修正与开发组复验',
        'r04 已按冻结顺序各验证一次。其前向桥接除占比、桥接场净分和参考静态排除，还继承了首四列至少一次命中、最后一列也须命中以及最短尾段。这会拒绝已达任务书三项要求的候选。r05 删除这三项附加判定；候选仍从已有联合证据的固定前缀出发，有新增像素才能定义净分。被参考强暗线解释的差分细脊在桥接表中直接屏蔽。每步保留转向和步长代价。完整算法和校验哈希已单独冻结。',
        f"开发组A联合命中 {res['full_joint']}/{len(rr)}，全 551 帧选用桥接 {res['published_bridges']} 次。全合成矩阵 {len(probes)} 例，432 个阴性误报 {res['negative_fp']}，弱带严格通过 {res['weak_pass']}/216。全部同步扰动的有效端点最大漂移 {res['jitter_max']:.2f} px。三点弯、验证组C没有在 r05 重跑，因此 r04 的验证结果不能用于判定此修正版的验证精度。",
        '[r05 核心源码](../../../research/notch_identity_v58_strict/terminal.py) · [冻结记录](freeze.json) · [开发组A四栏图与视频](difference_views/index.html) · [逐帧长度](crack_lengths.csv) · [合成矩阵](paired_probes.csv) · [同步扰动](jitter_summary.csv)',
        '## 开发组A失败帧', '图像链接为完整模式，曲线按所列模式读取。',table(['帧','模式','尖端误差 px','覆盖率','精度','输出端点','曲线'],details)])
    print(res)

if __name__=='__main__':main()
