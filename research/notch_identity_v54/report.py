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
    audit,entries=failure_list(b,scores,records,['local_peaks','v5_3'],explain,('full','raw_only'))
    for g,ids in raw_cards.items():
        folder=b.OUT/'raw_failures'/g;folder.mkdir(exist_ok=True,parents=True)
        for card,_,r in source_frames(g,ids,'raw_only'):card.save(folder/f"{r['frame']:04d}.jpg",quality=91)
    audit.insert(1,'蓝线为每列全部可达方向状态的最大累计分，金线取人工路径所在像素。虚线标示人工端点与裁决端点，两种候选另以点标明。下图给出两条路径的局部净证据。反事实检验每次只放宽一项约束，仅用于封存后的归因。未标注及尖端不确定帧不纳入数值失败判定。')
    from .inspect_peaks import inspect_focus
    focus_review=inspect_focus(scores,records)
    group='three_point_bend'
    def scored(i,name):return scores[group,i,name,'full']
    original_hits=[i for (g,i,stage,mode),r in scores.items() if g==group and stage=='local_peaks' and mode=='full' and r['joint']=='True']
    recovered=[i for i in sorted(original_hits) if scored(i,'v5_4')['joint']=='True']
    conclusion=f"V5.3 净得分场消融 local_peaks 曾有 {len(original_hits)} 帧联合命中，V5.4 恢复其中 {len(recovered)} 帧，原序号为 {recovered}。"
    conclusion+=' 第 144 帧没有合格远端峰，末窗强增量差分列为零，口门后验没有否决原峰。第 178 帧切换到更靠右的分支，离人工端点 25.48 px。第 215 帧的 [1603,2718] 已满足谷底爬升和闭环要求，误差 2.08 px、候选路径覆盖 90%、精度 89%；累计分 22.49 低于 [1566,2708] 的 30.84。后者也有更大的独立增益（5.30 对 3.61），单纯改按增益排序仍会错选。实际误差从 85.76 px 降到 40.41 px。'
    conclusion+=' 下一轮可只在开发数据上构造两段相继爬升的分叉探针，分别测试候选之间的路径延续性、第二段原图暗谷及端点后证据衰减，锁定规则后再作验证。'
    stability=[]
    for i in sorted(original_hits):
        old=scored(i,'local_peaks');new=scored(i,'v5_4')
        a=records[group,i]['models']['local_peaks']['full'];m=records[group,i]['models']['v5_4']['full']
        stability.append([i,a['root'],m['root'],a['points']==m['points'],num(old['coverage']),num(new['coverage']),num(old['precision']),num(new['precision']),new['joint']])
    focus_review+=['## 三点弯根部恢复',table(['帧','干净场原起点','本轮起点','整条路径相同','原覆盖','新覆盖','原精度','新精度','本轮联合'],stability)]
    pack(b,'FAILURES_AUDIT.md',audit+[conclusion]+focus_review)

    stage='v5_4'
    final=[r for r in metrics if r['stage']==stage and r['mode']=='full']
    gates={r['group']:r['joint']>={'group_a':18,'three_point_bend':9,'group_c':17}[r['group']] and r['hit']>={'group_a':18,'three_point_bend':9,'group_c':17}[r['group']] and r['severe']==0 and (r['group']!='group_c' or r['median']<3.) for r in final}
    probes=read_csv(b.OUT/'paired_probes.csv')
    legacy_neg=[x for x in probes if x['negative']=='True' and not x['case'].startswith('mouth_glare_arc')]
    weak=[x for x in probes if x['width']!='0']
    ctr=[x for x in probes if x['case'].startswith('control_')]
    count=lambda seq:sum(x['passed']=='True' for x in seq)
    lengths=read_csv(b.OUT/'crack_lengths.csv')
    assert len(lengths)==sum(b.GROUPS.values())
    first=records['group_a',1]['models'][stage]['full']
    res=dict(primary=stage,run=b.OUT.relative_to(b.ROOT).as_posix(),report='evidence/v5_4/REPORT.md',failures='evidence/v5_4/FAILURES_AUDIT.md',
        lengths=(b.OUT/'crack_lengths.csv').relative_to(b.ROOT).as_posix(),groups=final,
        overall_full=aggregate([x for (g,i,s,m),x in scores.items() if s==stage and m=='full']),
        accuracy_gate=gates,group_a_first=first['status'],weak_pass=count(weak),weak_wrong=sum(int(x['wrong']) for x in weak),
        negative_fp=sum(x['valid']=='True' for x in legacy_neg),negative_count=len(legacy_neg),controls_pass=count(ctr),controls_count=len(ctr))
    all_neg=[x for x in probes if x['negative']=='True']
    res['all_negative_fp']=sum(x['valid']=='True' for x in all_neg)
    res['all_negative_count']=len(all_neg)
    res['decision']='PRODUCTION_NO_GO' if not all(gates.values()) or len(recovered)!=len(original_hits) or scored(215,'v5_4')['joint']!='True' or first['status']!='no_tip' or count(weak)!=216 or res['weak_wrong'] or res['all_negative_fp'] or count(ctr)!=len(ctr) else 'RESEARCH_GATES_PASSED'
    header=['# V5.4 谷底爬升度量与无扣分口门复核验证报告',
        '、'.join(f"{NAMES[r['group']]} 联合 {r['joint']}/{r['visible']}，中位 {num(r['median'])} px" for r in final)+f"。完整模式严重误差 {res['overall_full']['severe']} 帧。结论 {res['decision']}。",
        '[逐帧裂纹长度 CSV](crack_lengths.csv) · [逐帧四栏图、差分与视频](difference_views/index.html) · [失败帧与累计分曲线](FAILURES_AUDIT.md) · [冻结记录](freeze.json)',
        '## 开发与测量约定',
        '先在合成与开发组A开发组封存预测和评分，锁定代码与参数后，依次在三点弯及验证组C各执行一次冻结验证。标注只用于封存后的离线比较，排除组X排除。两验证组已有历史暴露。',
        'path_length_px 是算法从实际起追点到预测尖端的逐段欧氏距离之和。它包含 DP 跨越弱带时推断的路径段。projected_length_px 是从当帧两锚点中点到尖端的有符号右法向投影。起点与测量方向不同，数值需独立解读。所有坐标与长度均在当前原图像素系中计算。缺少尖端时长度空缺，缺少有效实测锚点时投影空缺。没有本组 mm/px 标定。CSV 每个原图序号一行，分别包含完整与纯灰度模式的根点、尖端、状态和两项长度。inferred_bridge_columns 给出另唇接续插值列数，可用来筛选含插值的测量。',
        '## 谷底爬升与近口终点复核',
        '两个新阶段均直接复用 V5.3 local_peaks 的干净场，仅含 V5.2 温和宽带折减。valley 为 S1，v5_4 再启用近口复核。五种到达斜率、根部种子与 DP 负分规则沿用冻结实现。回溯路径上首列取 max(0,S)，之后每列的净增量为 S − 0.13|dy| − 0.19|dy−dy_prev|。',
        '对 x>0.20s、V>0.052s、S>0.08 的 3×3 局部峰沿前驱链重建逐列累计分。在 x>0.19s 的首个像素至峰顶间取累计分最低点 k，独立爬升 G=V_peak−V_k。仅用 k 之后的步长计算均值与占比。上升跨度至少 0.030s，G≥max(1,0.010s)，净分均值>0.075，正支撑比例≥54%，持续支撑≥0.012s。末 0.014s 平均净分>0.06、末步正分且通过闭环复核。在合格候选中按累计峰分降序选择。全局峰停在 0.19s 内时，默认要求额外延伸≥0.045s；已确认死胡同时也允许更近的合格远端峰。',
        '仅对完整联合证据且全局峰 x≤0.19s 的结果启动口门后验复核。末 0.025s 统计当前细暗谷、相对于参考新出现的暗谷、邻接反光、差分强度及前方负分断崖。若增量差分列≥48%，且细谷列<36%并伴反光或断崖，则判死胡同；强反光与断崖并存时亦检查固定参考中已有的短趾，以及长度≤0.055s、前方强差分与平灰同时出现的短边缘。优先采用合格远端峰，或检查 0.10s～0.22s 之间另一根部的独立峰（末段至少 60% 的列同时具有细暗谷与差分细脊）；没有合格替代则输出 no_tip。此步骤只裁决端点，不改变 DP 像素得分。',
        '保留另唇接续与限幅三次插值。用后段短窗内跨半窗斜率的中位数估计切向，减少单个边缘像素对插值曲线的影响。插值列单独计数。 [核心实现](../../../research/notch_identity_v54/terminal.py)']
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
    header+=['## 全序列输出','全序列中的选峰次数仅反映裁决变化。只有可见人工尖端帧可用于计算误差。',table(['组','总帧','选远端峰','另唇接续','有长度帧','弧长中位 px','最大弧长 px','批处理帧/s'],usage),'批处理为六进程，含两种模式、标注帧的逐项消融、校验和存盘。消融表的 FPS 是平均单帧推理耗时的倒数。']
    for g,frames in [('three_point_bend',[144,178,215]),('group_a',[1,398]),('group_c',[324,456,510])]:
        for i in frames:
            m=records[g,i]['models'][stage]['full'];d=m['diagnostics']['dual'];row=scores[g,i,stage,'full']
            gt=json.loads(row['gt']) if row['gt'] else None
            def peak(label):
                pt=d.get(label+'_tip')
                if not pt:return '无合格候选'
                return f"{pt} / {num(d.get(label+'_score'))} / {num(math.dist(pt,gt) if gt else None)}"
            sheet.append([NAMES[g],f'[{i}](difference_views/frames/{g}/{i:04d}.jpg)',gt or '不确定',peak('global'),peak('distal'),num(d.get('valley_value')),num(d.get('valley_gain')),num(d.get('net_mean')),num(d.get('support')),d.get('pick'),m['status'],num(scores[g,i,'v5_3','full']['error_px']),num(row['error_px']),num(row['coverage']),num(row['precision']),num(m['path_length_px']),num(m['projected_length_px'])])
    header+=['## 指定帧双峰裁决','候选栏依次为原图坐标、累计分、对人工端点的误差（px）。远端区域与全局区域可以选中同一点。',table(['组','帧','人工','全局峰','远端峰','谷底 V','峰减谷底','远段净分/列','支撑比例','选择','输出','V5.3 误差','V5.4 误差','覆盖','精度','路径弧长','锚点投影'],sheet)]
    header+=[conclusion]+focus_review
    header+=focus_tables(b,scores,records,['v3_6','v4_2','v5_0','v5_1','v5_2','v5_3','valley',stage])
    header+=['## 合成与对照',f"原有阴性误报 {res['negative_fp']}/{len(legacy_neg)}，弱带通过 {count(weak)}/216，错接 {res['weak_wrong']} 次。已有 control 探针通过 {count(ctr)}/{len(ctr)}。以下保留附加团块阴性分母。"]
    body=[]
    for case in dict.fromkeys(x['case'] for x in probes if x['case'].startswith('mouth_')):
        a=[x for x in probes if x['case']==case];negative=a[0]['negative']=='True'
        totals=[sum(x[m+'_valid']=='False' if negative else bool(x[m+'_error']) and float(x[m+'_error'])<=10 for x in a) for m in ('baseline','width')]
        body.append([case,len(a),*totals,count(a),sum(x['pick']=='DISTAL' for x in a),sum(x['passed']=='True' and float(x['coverage'])>=.80 and float(x['precision'])>=.80 for x in a) if not negative else '—'])
    header+=[table(['口门探针','样本','V5.3 端点/拒绝','S1 谷底爬升','V5.4 端点/拒绝','远端裁决次数','同时满足路径覆盖/精度≥80%'],body),
        f"全部合成阴性误报 {res['all_negative_fp']}/{len(all_neg)}。沿用的红弧对照通过移动固定参考中的亮反射带产生单侧强差分，当前图保留邻接亮斑与短缺口趾。另有带真实细分支的配对阳性。"]
    prev=read_csv(b.BASE/'paired_probes.csv')
    for version,source in [('V5.3',prev),('V5.4',probes)]:
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
