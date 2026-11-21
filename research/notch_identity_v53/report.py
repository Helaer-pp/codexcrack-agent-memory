"""Publish sealed scores, endpoint decisions, lengths, experimental controls, and failure curves."""
import json,math
from collections import Counter
from statistics import median
from . import batch as b
from .curves import generate
from .difference_views import source_frames
from research.notch_identity_v42.reporting import collect,pack,metric_tables,focus_tables,probe_tables,failure_list,read_csv,table,NAMES,num,aggregate

def main():
    scores,records,metrics=collect(b)
    from research.notch_identity_v36.batch import OUT as hist36
    from itertools import islice
    assert b.sha(hist36/'group_c.jsonl')==b.read(hist36/'group_c_seal.json')['predictions']
    with (hist36/'group_c.jsonl').open() as stream:old=json.loads(next(islice(stream,346,None)))
    target=records['group_c',347]
    assert old['source_sha']==target['source_sha']
    target['models']['v3_6']=old['models']['v3_6']
    raw_cards={g:set() for g in b.GROUPS}
    def explain(g,i,m,r,mode):
        msg=generate(g,i,m,r,mode)
        if mode=='raw_only':
            raw_cards[g].add(i)
            msg+=f' [纯灰度四栏图](raw_failures/{g}/{i:04d}.jpg)'
        return msg+f" 本帧识别路径弧长 {num(m['path_length_px'])} px，投影长度 {num(m['projected_length_px'])} px。"
    audit,entries=failure_list(b,scores,records,['v5_2'],explain,('full','raw_only'))
    for g,ids in raw_cards.items():
        folder=b.OUT/'raw_failures'/g;folder.mkdir(exist_ok=True,parents=True)
        for card,_,r in source_frames(g,ids,'raw_only'):card.save(folder/f"{r['frame']:04d}.jpg",quality=91)
    audit.insert(1,'蓝线为每列全部可达方向状态的最大累计分，金线取人工路径所在像素。虚线标示人工端点与裁决端点，两种候选另以点标明。下图给出两条路径的局部净证据。反事实检验每次只放宽一项约束，仅用于封存后的归因。未标注及尖端不确定帧不纳入数值失败判定。')
    from .inspect_peaks import inspect_focus
    focus_review=inspect_focus(scores,records)
    conclusion='三点弯只启用局部峰修复时联合仍为 8/15，加入红弧抑制后降到 0/15。第 248 帧的旧路径在新得分场损失约 21.10 分，而新路径仅损失 1.51 分；起点从 (1474,2729) 移至 (1476,2688)，尖端坐标相同。第 335 帧两条路径分别损失 28.66 与 2.13 分。长度和路径精度因此需要独立核查。'
    pack(b,'FAILURES_AUDIT.md',audit+[conclusion]+focus_review)

    stage='v5_3'
    final=[r for r in metrics if r['stage']==stage and r['mode']=='full']
    gates={r['group']:r['joint']>={'group_a':18,'three_point_bend':10,'group_c':17}[r['group']] and r['hit']>={'group_a':18,'three_point_bend':11,'group_c':17}[r['group']] and r['severe']==0 and (r['group']!='group_c' or r['median']<3.) for r in final}
    probes=read_csv(b.OUT/'paired_probes.csv')
    legacy_neg=[x for x in probes if x['negative']=='True' and not x['case'].startswith('mouth_glare_arc')]
    weak=[x for x in probes if x['width']!='0']
    ctr=[x for x in probes if x['case'].startswith('control_')]
    count=lambda seq:sum(x['passed']=='True' for x in seq)
    lengths=read_csv(b.OUT/'crack_lengths.csv')
    assert len(lengths)==sum(b.GROUPS.values())
    first=records['group_a',1]['models'][stage]['full']
    res=dict(primary=stage,run=b.OUT.relative_to(b.ROOT).as_posix(),report='evidence/v5_3/REPORT.md',failures='evidence/v5_3/FAILURES_AUDIT.md',
        lengths=(b.OUT/'crack_lengths.csv').relative_to(b.ROOT).as_posix(),groups=final,
        overall_full=aggregate([x for (g,i,s,m),x in scores.items() if s==stage and m=='full']),
        accuracy_gate=gates,group_a_first=first['status'],weak_pass=count(weak),weak_wrong=sum(int(x['wrong']) for x in weak),
        negative_fp=sum(x['valid']=='True' for x in legacy_neg),negative_count=len(legacy_neg),controls_pass=count(ctr),controls_count=len(ctr))
    all_neg=[x for x in probes if x['negative']=='True']
    res['all_negative_fp']=sum(x['valid']=='True' for x in all_neg)
    res['all_negative_count']=len(all_neg)
    res['decision']='PRODUCTION_NO_GO' if not all(gates.values()) or first['status']!='no_tip' or count(weak)!=216 or res['weak_wrong'] or res['all_negative_fp'] or count(ctr)!=len(ctr) else 'RESEARCH_GATES_PASSED'
    header=['# V5.3 远端正增量局部峰与近口红弧验证报告',
        '、'.join(f"{NAMES[r['group']]} 联合 {r['joint']}/{r['visible']}，中位 {num(r['median'])} px" for r in final)+f"。完整模式严重误差 {res['overall_full']['severe']} 帧。结论 {res['decision']}。",
        '[逐帧裂纹长度 CSV](crack_lengths.csv) · [逐帧四栏图、差分与视频](difference_views/index.html) · [失败帧与累计分曲线](FAILURES_AUDIT.md) · [冻结记录](freeze.json)',
        '## 开发与测量约定',
        '先在合成与开发组A开发组封存预测和评分，锁定代码与参数后，依次在三点弯及验证组C各执行一次冻结验证。标注只用于封存后的离线比较，排除组X排除。两验证组已有历史暴露。',
        'path_length_px 是算法从实际起追点到预测尖端的逐段欧氏距离之和。它包含 DP 跨越弱带时推断的路径段。projected_length_px 是从当帧两锚点中点到尖端的有符号右法向投影。起点与测量方向不同，数值需独立解读。所有坐标与长度均在当前原图像素系中计算。缺少尖端时长度空缺，缺少有效实测锚点时投影空缺。没有本组 mm/px 标定。CSV 每个原图序号一行，分别包含完整与纯灰度模式的根点、尖端、状态和两项长度。inferred_bridge_columns 给出另唇接续插值列数，可用来筛选含插值的测量。',
        '## 两项公式',
        'local_peaks 保留 V5.2 得分场，修复远端检索并复核前缘归属。v5_3 叠加红弧抑制。全部模式共享原有种子、五斜率 DP、负分与端点输出门。纯灰度对照独立计时。',
        '在每个像素保留最优到达方向，从三乘三邻域内的局部极大值构建候选集合。要求 x>0.20s、V>0.052s、末列 S>0.08。对每个候选按同一前驱表回溯，自 x>0.19s 后的长度至少 0.035s，扣除步长/转向罚分的净均值>0.075，正支撑列占比≥54%，连续支撑≥0.012s，末 0.014s 净分均值>0.06 且最后一步净分为正，并通过闭环校验。在符合全部条件的局部峰中选 V 最高者。实现按 V 降序检查，首个通过者等价于在合格集合中取最大值。仅当全局峰在 0.19s 内，完整模式有联合证据，且远端额外延伸≥0.045s 时允许替换。',
        'V5.2 宽团块权重保留。计算注册差分 D 的连续正带宽 W，T=max(3σ,0.038L)。在上下 0.0065s 处分别测量当前灰度的暗谷突出度和差分红脊突出度，除以 max(D,T) 得到 Cg、Cd。设 clip 截断至 [0,1]。M=clip((W/s−0.014)/0.013)，A=clip((Cg−0.11)/0.27)，F=clip((0.60−Cd)/0.44)，G 为 0.025s 法向窗内的亮度落差按 0.10L～0.25L 归一化。新权重 R=M(1−A)max(F,G)，乘以原有前缘渐消系数 t。取旧宽度权重与 tR 的较大值，将团块正分向 0.015 压低；在 D>T 时另减 0.42tR。明确的当前暗谷核心保留。',
        '当两个分离唇缘均有合法种子、弱证据过渡伴随超过 0.032s 的横向位移，检查另一唇缘与远段方向是否更相容。使用原图暗谷和差分红脊同时支持的短前缀，在两端均有观测且跨度小于 0.21s 时，按两端切向作限幅三次插值。复核列间步长和闭环。此项只影响路径与弧长，不移动已选尖端。插值列属于推断，不能作为观察到暗线的证据。 [实现](../../../research/notch_identity_v53/terminal.py)']
    header+=metric_tables(b,metrics)
    import os
    os.environ.setdefault('MPLCONFIGDIR',str(b.OUT/'plot_cache'))
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig,axes=plt.subplots(3,1,figsize=(10,7),layout='constrained')
    for axis,(group,n) in zip(axes,b.GROUPS.items()):
        rr=[r for r in lengths if r['group']==group];xs=[int(r['frame']) for r in rr]
        for field,label,color in [('full_path_length_px','Root to tip / arc','#086c77'),('full_projected_length_px','Anchor midpoint / projection','#bd613b')]:
            axis.plot(xs,[float(x[field]) if x[field] else float('nan') for x in rr],label=label,color=color,lw=1.2)
        failed=[r for r in rr if r['full_joint']=='False' and r['full_path_length_px']]
        axis.scatter([int(r['frame']) for r in failed],[float(r['full_path_length_px']) for r in failed],label='Labelled joint failure',s=20,marker='x',color='#a62940')
        axis.set_title({'group_a':'GROUP_A','three_point_bend':'Three-point bend','group_c':'group_c'}[group],loc='left',fontsize=10)
        axis.set_xlim(1,n);axis.set_ylabel('Length (px)');axis.grid(alpha=.18)
    axes[0].legend(loc='best',fontsize=8,ncol=3);axes[-1].set_xlabel('Original frame number')
    fig.savefig(b.OUT/'length_history.png',dpi=150);plt.close(fig)
    header+=['[三组完整模式逐帧长度曲线](length_history.png)。曲线保留原始逐帧波动，缺测处断开。叉号为可见标注帧的联合失败。']
    sheet=[];usage=[]
    for g,n in b.GROUPS.items():
        recs=[json.loads(line)['models'][stage]['full'] for line in (b.OUT/(g+'.jsonl')).open()]
        rr=[row for row in lengths if row['group']==g]
        vals=[float(row['full_path_length_px']) for row in rr if row['full_path_length_px']]
        wall=b.read(b.OUT/(g+'_seal.json'))['wall_seconds']
        usage.append([NAMES[g],n,sum(x['diagnostics']['dual'].get('pick')=='DISTAL' for x in recs),sum(bool(x['diagnostics']['dual'].get('lip_bridge')) for x in recs),len(vals),num(median(vals) if vals else None),num(max(vals,default=None)),num(n/wall)])
    header+=['## 全序列输出',table(['组','总帧','选远端峰','另唇接续','有长度帧','弧长中位 px','最大弧长 px','批处理帧/s'],usage),'批处理为六进程，含两种模式、标注帧的逐项消融、校验和存盘。消融表的 FPS 是平均单帧推理耗时的倒数。']
    for g,frames in [('three_point_bend',[144,178,215]),('group_a',[1,398]),('group_c',[324,456,510])]:
        for i in frames:
            m=records[g,i]['models'][stage]['full'];d=m['diagnostics']['dual'];row=scores[g,i,stage,'full']
            gt=json.loads(row['gt']) if row['gt'] else None
            def peak(label):
                pt=d.get(label+'_tip')
                if not pt:return '无合格候选'
                return f"{pt} / {num(d.get(label+'_score'))} / {num(math.dist(pt,gt) if gt else None)}"
            sheet.append([NAMES[g],f'[{i}](difference_views/frames/{g}/{i:04d}.jpg)',gt or '不确定',peak('global'),peak('distal'),num(d.get('net_mean')),num(d.get('support')),d.get('pick'),m['status'],num(scores[g,i,'v5_2','full']['error_px']),num(row['error_px']),num(m['path_length_px']),num(m['projected_length_px'])])
    header+=['## 指定帧双峰裁决','候选栏依次为原图坐标、累计分、对人工端点的误差（px）。远端区域与全局区域可以选中同一点。',table(['组','帧','人工','全局峰','远端峰','远段净分/列','支撑比例','选择','输出','V5.2 误差','V5.3 误差','路径弧长','锚点投影'],sheet)]
    header+=[conclusion]+focus_review
    header+=focus_tables(b,scores,records,['v3_6','v4_2','v5_0','v5_1','v5_2',stage])
    header+=['## 合成与对照',f"原有阴性误报 {res['negative_fp']}/{len(legacy_neg)}，弱带通过 {count(weak)}/216，错接 {res['weak_wrong']} 次。已有 control 探针通过 {count(ctr)}/{len(ctr)}。以下保留附加团块阴性分母。"]
    body=[]
    for case in dict.fromkeys(x['case'] for x in probes if x['case'].startswith('mouth_')):
        a=[x for x in probes if x['case']==case];negative=a[0]['negative']=='True'
        totals=[sum(x[m+'_valid']=='False' if negative else bool(x[m+'_error']) and float(x[m+'_error'])<=10 for x in a) for m in ('baseline','width')]
        body.append([case,len(a),*totals,count(a),sum(x['pick']=='DISTAL' for x in a),sum(x['passed']=='True' and float(x['coverage'])>=.80 and float(x['precision'])>=.80 for x in a) if not negative else '—'])
    header+=[table(['口门探针','样本','V5.2 端点/拒绝','仅任务一','V5.3 端点/拒绝','远端裁决次数','同时满足路径覆盖/精度≥80%'],body),
        f"全部合成阴性误报 {res['all_negative_fp']}/{len(all_neg)}。新增红弧对照通过移动固定参考中的亮反射带产生单侧强差分，当前图保留邻接亮斑与短缺口趾。另有带真实细分支的配对阳性。"]
    prev=read_csv(b.BASE/'paired_probes.csv')
    for version,source in [('V5.2',prev),('V5.3',probes)]:
        grid=[]
        for case in dict.fromkeys(x['case'] for x in source):
            row=[case]
            for zoom in (.5,1,2):
                for photo in ('nominal','dim','bright'):
                    subset=[x for x in source if x['case']==case and float(x['zoom'])==zoom and x['photo']==photo]
                    if subset[0]['negative']=='True':cell=f"FP {sum(x['valid']=='True' for x in subset)}/{len(subset)}"
                    else:
                        joint=sum(bool(x['error']) and float(x['error'])<=10 and float(x['coverage'])>=.80 and float(x['precision'])>=.80 for x in subset)
                        cell=f"{count(subset)}/{joint}/{len(subset)}"
                    row.append(cell)
            grid.append(row)
        header+=['### '+version+' 全量倍率与曝光矩阵','阳性格依次为探针原判据通过数、路径联合命中数、样本数。合成联合要求原尺度尖端误差≤10 px，2.5 px 容差下的覆盖和精度均≥80%。阴性格给出误报/分母。',table(['探针']+[f'{z}× {p}' for z in (.5,1,2) for p in ('标准','暗','亮')],grid)]
    pack(b,'REPORT.md',header)
    for dest in (b.OUT,b.ROOT/'evidence'/stage,b.ROOT/'evidence'):b.save(dest/'latest_metrics.json',res)
    print(res)
if __name__=='__main__':main()
