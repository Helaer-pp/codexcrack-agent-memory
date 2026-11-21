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
        review=m['diagnostics']['dual'].get('branch_review',{})
        if review.get('replaced') and review.get('links'):
            link=review['links'][-1]
            msg+=f" 下游替换跨 {link['span']} 列，其中细脊支撑 {link['fine']:.0%}、合并支撑 {link['support']:.0%}，平均净分 {link['mean']:.2f}，累计峰分比 {link['ratio']:.3f}。"
        return msg+f" 本帧识别路径弧长 {num(m['path_length_px'])} px，投影长度 {num(m['projected_length_px'])} px。"
    audit,entries=failure_list(b,scores,records,['v5_4'],explain,('full','raw_only'))
    for g,ids in raw_cards.items():
        folder=b.OUT/'raw_failures'/g;folder.mkdir(exist_ok=True,parents=True)
        for card,_,r in source_frames(g,ids,'raw_only'):card.save(folder/f"{r['frame']:04d}.jpg",quality=91)
    audit.insert(1,'蓝线为每列全部可达方向状态的最大累计分，金线取人工路径所在像素。虚线标示人工端点与裁决端点，两种候选另以点标明。下图给出两条路径的局部净证据。反事实检验每次只放宽一项约束，仅用于封存后的归因。未标注及尖端不确定帧不纳入数值失败判定。')
    from .inspect_peaks import inspect_focus
    focus_review=inspect_focus(scores,records)
    group='three_point_bend'
    def scored(i,name):return scores[group,i,name,'full']
    original_hits=[i for (g,i,stage,mode),r in scores.items() if g==group and stage=='v5_4' and mode=='full' and r['joint']=='True']
    recovered=[i for i in sorted(original_hits) if scored(i,'v5_5')['joint']=='True']
    old=scored(215,'v5_4');s1=scored(215,'ridge');new=scored(215,'v5_5')
    conclusion=(f"三点弯 V5.4 的 {len(original_hits)} 帧联合命中中，本轮保留 {len(recovered)} 帧。"
        f"第 215 帧尖端误差依次为 V5.4 {num(old['error_px'])} px、仅细脊提权 {num(s1['error_px'])} px、"
        f"完整模式 {num(new['error_px'])} px，完整模式路径覆盖 {num(new['coverage'])}、精度 {num(new['precision'])}。")
    conclusion+=' 第 215 帧的 37 列连接段全部满足中心差分强度，11 列满足细脊侧翼净强度，最终 5 列满足连续细脊，4 列实际提权。两条回溯路径在早峰处无纵向偏离。连接段合并支撑为 16/37，低于一半，算法保留 [1566,2708]。'
    conclusion+=' 验证组C 221 在单独提权时保持原尖端。加入下游裁决后，从 [2413,2345] 延伸至 [2418,2344]，误差由 7.43 升至 12.39 px。新增五列没有高置信细脊，仅靠三列融合支撑获准通过。开发组A 398 及验证组C 324、456、510 的误差持平。'
    focus_review+=['## 后续开发建议','在合成与开发组并列构造斜行、变宽但积分差分持续的真实桥接，以及只有三至五列零散融合支撑的假尾。比较沿局部法向测量的脊宽与方向连续性，并检验最小有效支撑长度，避免全局降低连接支撑比例。当前冻结验证组保留作对照。']
    stability=[]
    for i in sorted(original_hits):
        old=scored(i,'v5_4');new=scored(i,'v5_5')
        a=records[group,i]['models']['v5_4']['full'];m=records[group,i]['models']['v5_5']['full']
        stability.append([i,a['root'],m['root'],a['points']==m['points'],num(old['coverage']),num(new['coverage']),num(old['precision']),num(new['precision']),new['joint']])
    focus_review+=['## 三点弯根部恢复',table(['帧','干净场原起点','本轮起点','整条路径相同','原覆盖','新覆盖','原精度','新精度','本轮联合'],stability)]
    pack(b,'FAILURES_AUDIT.md',audit+[conclusion]+focus_review)

    stage='v5_5'
    final=[r for r in metrics if r['stage']==stage and r['mode']=='full']
    gates={r['group']:r['joint']>={'group_a':18,'three_point_bend':9,'group_c':17}[r['group']] and r['hit']>={'group_a':18,'three_point_bend':9,'group_c':17}[r['group']] and r['severe']==0 and (r['group']!='group_c' or r['median']<3.) for r in final}
    probes=read_csv(b.OUT/'paired_probes.csv')
    legacy_neg=[x for x in probes if x['negative']=='True' and x['case']!='weak_tail_blank']
    weak=[x for x in probes if x['width']!='0']
    ctr=[x for x in probes if x['case'].startswith('control_')]
    count=lambda seq:sum(x['passed']=='True' for x in seq)
    lengths=read_csv(b.OUT/'crack_lengths.csv')
    assert len(lengths)==sum(b.GROUPS.values())
    first=records['group_a',1]['models'][stage]['full']
    res=dict(primary=stage,run=b.OUT.relative_to(b.ROOT).as_posix(),report='evidence/v5_5/REPORT.md',failures='evidence/v5_5/FAILURES_AUDIT.md',
        lengths=(b.OUT/'crack_lengths.csv').relative_to(b.ROOT).as_posix(),groups=final,
        overall_full=aggregate([x for (g,i,s,m),x in scores.items() if s==stage and m=='full']),
        accuracy_gate=gates,group_a_first=first['status'],weak_pass=count(weak),weak_wrong=sum(int(x['wrong']) for x in weak),
        negative_fp=sum(x['valid']=='True' for x in legacy_neg),negative_count=len(legacy_neg),controls_pass=count(ctr),controls_count=len(ctr))
    all_neg=[x for x in probes if x['negative']=='True']
    res['all_negative_fp']=sum(x['valid']=='True' for x in all_neg)
    res['all_negative_count']=len(all_neg)
    protected=[('group_a',398),('group_c',324),('group_c',456),('group_c',510)]
    res['watch_frame_guard']=all(float(scores[g,i,stage,'full']['error_px'] or 'inf')<=float(scores[g,i,'v5_4','full']['error_px'])+1e-8 for g,i in protected)
    res['two_rise_pass']=count([x for x in probes if x['case']=='two_rise_bridge'])
    res['decision']='PRODUCTION_NO_GO' if not res['watch_frame_guard'] or res['two_rise_pass']!=36 or not all(gates.values()) or len(recovered)!=len(original_hits) or scored(215,'v5_5')['joint']!='True' or first['status']!='no_tip' or count(weak)!=216 or res['weak_wrong'] or res['all_negative_fp'] or count(ctr)!=len(ctr) else 'RESEARCH_GATES_PASSED'
    header=['# V5.5 细脊差分提权与同枝下游峰优先验证报告',
        '、'.join(f"{NAMES[r['group']]} 联合 {r['joint']}/{r['visible']}，中位 {num(r['median'])} px" for r in final)+f"。完整模式严重误差 {res['overall_full']['severe']} 帧。结论 {res['decision']}。",
        '[逐帧裂纹长度 CSV](crack_lengths.csv) · [逐帧四栏图、差分与视频](difference_views/index.html) · [失败帧与累计分曲线](FAILURES_AUDIT.md) · [冻结记录](freeze.json)',
        '## 开发与测量约定',
        '先在合成与开发组A开发组封存预测和评分，锁定代码与参数后，依次在三点弯及验证组C各执行一次冻结验证。标注只用于封存后的离线比较，排除组X排除。两验证组已有历史暴露。',
        'path_length_px 是算法从实际起追点到预测尖端的逐段欧氏距离之和。它包含 DP 跨越弱带时推断的路径段。projected_length_px 是从当帧两锚点中点到尖端的有符号右法向投影。起点与测量方向不同，数值需独立解读。所有坐标与长度均在当前原图像素系中计算。缺少尖端时长度空缺，缺少有效实测锚点时投影空缺。没有本组 mm/px 标定。CSV 每个原图序号一行，分别包含完整与纯灰度模式的根点、尖端、状态和两项长度。inferred_bridge_columns 给出另唇接续插值列数，可用来筛选含插值的测量。',
        '## 细脊提权与下游裁决',
        'ridge 是仅启用融合修正的 S1，v5_5 再启用同枝裁决。两阶段均保留 V5.4 的原始灰度得分、五斜率 DP、局部峰谷底爬升门、近口复核及另唇接续。纯灰度模式无差分修正。',
        '配准后 D=参考灰度−当前灰度。以 T=max(3σ,0.035L) 作灰度尺度，L 为材料灰度跨度。按 r≈0.0065s 测量中心相对于上下两侧较高值的正突出度 P(D)，令 A=P(D)/T，Cd=P(D)/max(D,T)。高置信列要求 D>1.15T、A>1、Cd>0.27、邻近参考暗谷与 max(T,P(D)) 之比低于 0.55；近口 0.25s 内排除宽于 0.024s 的红带，前 0.19s 禁止提权。允许细脊在列间轻微倾斜，沿轴向短窗至少 69% 列有支撑。',
        '当前暗谷突出度低于 max(1.4T,0.42P(D)) 时，在有前后联合实测核心的弱段令 S_new=max(S_old,0.10+0.92·clip((A−1)/2)·clip((Cd−0.27)/0.45))，clip 截至 [0,1]。两侧核心搜索的最大轴向距离为 0.11s、法向容差 0.025s。拖尾失去强、细、持续或双侧支撑中的任一项时，沿用原得分。',
        '选取 V5.4 已合格的最高分远端峰作为早峰，检查其下游 0.023s～0.24s 内同样通过谷底爬升与拓扑检验的峰。早峰前 0.032s 内要求路径纵向最大间距≤max(2,0.014s)。连接段正净分或细脊支撑≥50%，且细脊占比≥16%或强净分列≥58%；最长无支撑间断≤0.045s、连接段含转向代价的平均净分>−0.29、下游累计分≥早峰的 64%。合格者优先取最下游。原界限、无候选、异枝和断崖均有回退。 [核心实现](../../../research/notch_identity_v55/terminal.py)']
    header+=metric_tables(b,metrics)
    speed=[]
    for g,n in b.GROUPS.items():
        times=[]
        for folder,version in ((b.BASE,'v5_4'),(b.OUT,'v5_5')):
            with (folder/(g+'.jsonl')).open() as stream:
                ts=[json.loads(line)['models'][version]['seconds'] for line in stream]
            assert len(ts)==n
            times.append(sum(ts)/n)
        speed.append([NAMES[g],n,num(1/times[0]),num(1/times[1]),f'{(times[1]/times[0]-1)*100:+.1f}%'])
    header+=['### 全序列速度对照','分母为每组全部原图。两次冻结运行分别计时，六进程共享 CPU。单帧推理 FPS 与六进程端到端吞吐单列，视频播放固定 10 FPS。没有提供采集帧率或明确的实时截止时间。',
        table(['组','帧数','V5.4 推理 FPS','V5.5 推理 FPS','平均耗时变化'],speed)]

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
        usage.append([NAMES[g],n,sum(bool(x['diagnostics']['dual'].get('branch_review',{}).get('replaced')) for x in recs),sum(x['diagnostics']['dual'].get('pick')=='DISTAL' for x in recs),sum(bool(x['diagnostics']['dual'].get('lip_bridge')) for x in recs),len(vals),num(median(vals) if vals else None),num(max(vals,default=None)),num(n/wall)])
    header+=['## 全序列输出','全序列中的选峰次数仅反映裁决变化。只有可见人工尖端帧可用于计算误差。',table(['组','总帧','同枝替换','选远端峰','另唇接续','有长度帧','弧长中位 px','最大弧长 px','批处理帧/s'],usage),'批处理为六进程，含两种模式、标注帧的逐项消融、校验和存盘。消融表的 FPS 是平均单帧推理耗时的倒数。']
    for g,frames in [('three_point_bend',[144,178,215]),('group_a',[1,398]),('group_c',[324,456,510])]:
        for i in frames:
            m=records[g,i]['models'][stage]['full'];d=m['diagnostics']['dual'];row=scores[g,i,stage,'full']
            gt=json.loads(row['gt']) if row['gt'] else None
            def peak(label):
                pt=d.get(label+'_tip')
                if not pt:return '无合格候选'
                return f"{pt} / {num(d.get(label+'_score'))} / {num(math.dist(pt,gt) if gt else None)}"
            sheet.append([NAMES[g],f'[{i}](difference_views/frames/{g}/{i:04d}.jpg)',gt or '不确定',peak('global'),peak('distal'),num(d.get('valley_value')),num(d.get('valley_gain')),num(d.get('net_mean')),num(d.get('support')),d.get('pick'),m['status'],num(scores[g,i,'v5_4','full']['error_px']),num(row['error_px']),num(row['coverage']),num(row['precision']),num(m['path_length_px']),num(m['projected_length_px'])])
    header+=['## 指定帧双峰裁决','候选栏依次为原图坐标、累计分、对人工端点的误差（px）。远端区域与全局区域可以选中同一点。',table(['组','帧','人工','全局峰','远端峰','谷底 V','峰减谷底','远段净分/列','支撑比例','选择','输出','V5.4 误差','V5.5 误差','覆盖','精度','路径弧长','锚点投影'],sheet)]
    header+=[conclusion]+focus_review
    header+=focus_tables(b,scores,records,['v3_6','v4_2','v5_0','v5_1','v5_2','v5_3','v5_4','ridge',stage])
    header+=['## 合成与对照','two_rise_bridge 为连续强差分细脊贯穿弱原图的双段阳性；weak_tail_blank 为无裂纹的微弱弥散拖尾，统计误报。weak_tail_attached 带有真实短裂纹，另报告绝对 10 px 命中与相对 V5.4 的误差变化。',f"原有阴性误报 {res['negative_fp']}/{len(legacy_neg)}，弱带通过 {count(weak)}/216，错接 {res['weak_wrong']} 次。已有 control 探针通过 {count(ctr)}/{len(ctr)}。以下保留附加团块阴性分母。"]
    body=[]
    for case in dict.fromkeys(x['case'] for x in probes if x['case'].startswith(('mouth_','two_rise','weak_tail'))):
        a=[x for x in probes if x['case']==case];negative=a[0]['negative']=='True'
        totals=[sum(x[m+'_valid']=='False' if negative else bool(x[m+'_error']) and float(x[m+'_error'])<=10 for x in a) for m in ('baseline','width')]
        body.append([case,len(a),*totals,count(a),sum(x['pick']=='DISTAL' for x in a),sum(x['passed']=='True' and float(x['coverage'])>=.80 and float(x['precision'])>=.80 for x in a) if not negative else '—'])
    header+=[table(['口门探针','样本','V5.4 端点/拒绝','S1 细脊提权','V5.5 端点/拒绝','远端裁决次数','同时满足路径覆盖/精度≥80%'],body),
        f"全部合成阴性误报 {res['all_negative_fp']}/{len(all_neg)}。沿用的红弧对照通过移动固定参考中的亮反射带产生单侧强差分，当前图保留邻接亮斑与短缺口趾。另有带真实细分支的配对阳性。"]
    prev=read_csv(b.BASE/'paired_probes.csv')
    for version,source in [('V5.4',prev),('V5.5',probes)]:
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
    attached=[r for r in probes if r['case']=='weak_tail_attached']
    paired_n=sum(r['error']!='' and r['baseline_error']!='' and float(r['error'])<=float(r['baseline_error'])+1e-8 for r in attached)
    header+=[f"带真裂纹的附加弱拖尾对照有 {count(attached)}/{len(attached)} 达到绝对 10 px 要求；相对 V5.4 尖端误差持平或减小为 {paired_n}/{len(attached)}。半倍率下 6 个样例的误差为 10.0001 px，按未舍入的数值计为失败。开发时曾测试仅凭局部强红脊提权，孤立形变划痕探针降到 28/36；最终版加入前后实测核心及参考划痕搜索后恢复 36/36。"]
    pack(b,'REPORT.md',header)
    for dest in (b.OUT,b.ROOT/'evidence'/stage,b.ROOT/'evidence'):b.save(dest/'latest_metrics.json',res)
    print(res)
if __name__=='__main__':main()
