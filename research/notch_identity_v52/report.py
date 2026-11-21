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
    audit,entries=failure_list(b,scores,records,['v5_1'],explain,('full','raw_only'))
    for g,ids in raw_cards.items():
        folder=b.OUT/'raw_failures'/g;folder.mkdir(exist_ok=True,parents=True)
        for card,_,r in source_frames(g,ids,'raw_only'):card.save(folder/f"{r['frame']:04d}.jpg",quality=91)
    audit.insert(1,'蓝线为每列全部可达方向状态的最大累计分，金线取人工路径所在像素。虚线标示人工端点与裁决端点，两种候选另以点标明。下图给出两条路径的局部净证据。反事实检验每次只放宽一项约束，仅用于封存后的归因。未标注及尖端不确定帧不纳入数值失败判定。')
    pack(b,'FAILURES_AUDIT.md',audit)

    stage='v5_2'
    final=[r for r in metrics if r['stage']==stage and r['mode']=='full']
    gates={r['group']:r['joint']>={'group_a':18,'three_point_bend':11,'group_c':17}[r['group']] and r['severe']==0 and (r['group']!='group_c' or r['median']<3.) for r in final}
    probes=read_csv(b.OUT/'paired_probes.csv')
    legacy_neg=[x for x in probes if x['negative']=='True' and not x['case'].startswith('mouth_')]
    weak=[x for x in probes if x['width']!='0']
    ctr=[x for x in probes if x['case'].startswith('control_')]
    count=lambda seq:sum(x['passed']=='True' for x in seq)
    lengths=read_csv(b.OUT/'crack_lengths.csv')
    assert len(lengths)==sum(b.GROUPS.values())
    first=records['group_a',1]['models'][stage]['full']
    res=dict(primary=stage,run=b.OUT.relative_to(b.ROOT).as_posix(),report='evidence/v5_2/REPORT.md',failures='evidence/v5_2/FAILURES_AUDIT.md',
        lengths=(b.OUT/'crack_lengths.csv').relative_to(b.ROOT).as_posix(),groups=final,
        overall_full=aggregate([x for (g,i,s,m),x in scores.items() if s==stage and m=='full']),
        accuracy_gate=gates,group_a_first=first['status'],weak_pass=count(weak),weak_wrong=sum(int(x['wrong']) for x in weak),
        negative_fp=sum(x['valid']=='True' for x in legacy_neg),negative_count=len(legacy_neg),controls_pass=count(ctr),controls_count=len(ctr))
    res['decision']='PRODUCTION_NO_GO' if not all(gates.values()) or first['status']!='no_tip' or count(weak)!=216 or res['weak_wrong'] or res['negative_fp'] or count(ctr)!=len(ctr) else 'RESEARCH_GATES_PASSED'
    header=['# V5.2 远端延伸与口门团块抑制验证报告',
        '、'.join(f"{NAMES[r['group']]} 联合 {r['joint']}/{r['visible']}，中位 {num(r['median'])} px" for r in final)+f"。完整模式严重误差 {res['overall_full']['severe']} 帧。结论 {res['decision']}。",
        '[逐帧裂纹长度 CSV](crack_lengths.csv) · [逐帧四栏图、差分与视频](difference_views/index.html) · [失败帧与累计分曲线](FAILURES_AUDIT.md) · [冻结记录](freeze.json)',
        '## 开发与测量约定',
        '先在合成与开发组A开发组封存预测和评分，锁定代码与参数后，依次在三点弯及验证组C各执行一次冻结验证。标注只用于封存后的离线比较，排除组X排除。两验证组已有历史暴露。',
        'path_length_px 是算法从实际起追点到预测尖端的逐段欧氏距离之和。它包含 DP 跨越弱带时推断的路径段。projected_length_px 是从当帧两锚点中点到尖端的有符号右法向投影。起点与测量方向不同，数值需独立解读。所有坐标与长度均在当前原图像素系中计算。缺少尖端时长度空缺，缺少有效实测锚点时投影空缺。没有本组 mm/px 标定。CSV 每个原图序号一行，分别包含完整与纯灰度模式的根点、尖端、状态和两项长度。',
        '## 两项公式',
        '沿用 V5.1 的定位、净证据与有斜率状态的全局 DP。在可靠联合证据模式，取前缘之后 0.25s 的配准差分 D=fixed−current，s 为锚距。微平滑后逐列求 D>max(3σ,0.038L) 的垂直连续宽度 W，σ 为噪声、L 为曝光跨度。在上下各 0.012s 的侧翼，取中心相对较强侧翼的正突出度，再在 D 与反相原图上取较大者，以 max(D,阈值) 归一化为 C。',
        '令 clip 为截断至 [0,1]。团块权重 B=clip((W/s−0.024)/0.015) × clip((0.56−C)/0.36) × clip((0.25−x/s)/0.05)，x 为相对前缘位置。修正得分 S′=S−B max(0,S−0.015)。薄带、中心突出或远离口门时折减趋于零；近口平宽正带的单列正分上限可降到 0.015。原图单通道与零增量预存门沿用 V5.1。',
        '一次 DP 保存同一前驱表，分别回溯全局最高峰 G 和 x>0.20s 区域最高峰 D。仅在联合模式、G 通过基础得分门、xG≤0.19s、xD−xG≥0.045s、VD>0.052s 时允许挑战。D 回溯路径在 x>0.19s 后须至少覆盖 0.035s，扣除原有步长/转弯代价后平均净分>0.075，S′>0.08 的列至少占 54%，连续支撑至少 0.012s，并通过闭环检查。其余使用全局峰。mouth_width 仅做团块折减，v5_2 启用两项。 [实现](../../../research/notch_identity_v52/terminal.py)']
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
        usage.append([NAMES[g],n,sum(x['diagnostics']['dual'].get('pick')=='DISTAL' for x in recs),len(vals),num(median(vals) if vals else None),num(max(vals,default=None)),num(n/wall)])
    header+=['## 全序列输出',table(['组','总帧','选远端峰','有长度帧','弧长中位 px','最大弧长 px','批处理帧/s'],usage),'批处理为六进程，含两种模式、标注帧的逐项消融、校验和存盘。消融表的 FPS 是平均单帧推理耗时的倒数。']
    for g,frames in [('three_point_bend',[144,178,215]),('group_a',[1,398]),('group_c',[324,456,510])]:
        for i in frames:
            m=records[g,i]['models'][stage]['full'];d=m['diagnostics']['dual'];row=scores[g,i,stage,'full']
            gt=json.loads(row['gt']) if row['gt'] else None
            def peak(label):
                pt=d.get(label+'_tip')
                if not pt:return '无可达正峰'
                return f"{pt} / {num(d.get(label+'_score'))} / {num(math.dist(pt,gt) if gt else None)}"
            sheet.append([NAMES[g],f'[{i}](difference_views/frames/{g}/{i:04d}.jpg)',gt or '不确定',peak('global'),peak('distal'),num(d.get('net_mean')),num(d.get('support')),d.get('pick'),m['status'],num(scores[g,i,'v5_1','full']['error_px']),num(row['error_px']),num(m['path_length_px']),num(m['projected_length_px'])])
    header+=['## 指定帧双峰裁决','候选栏依次为原图坐标、累计分、对人工端点的误差（px）。远端区域与全局区域可以选中同一点。',table(['组','帧','人工','全局峰','远端峰','远段净分/列','支撑比例','选择','输出','V5.1 误差','V5.2 误差','路径弧长','锚点投影'],sheet)]
    header+=['三点弯三个目标帧均保留了口门全局峰。第 144、178、215 帧的远端最高分都落在 x=1532 的搜索区左边界，脱离口门后各仅积累 4 列。其净增量均值分别为 −0.93、−1.18、−0.05。第 215 帧在 x=1603 仍有较低的局部峰 V=22.49，低于边界峰 V=46.55，因此没有进入最终两候选比较。下一轮应在独立开发探针上检验“先确认远端段具有正增量，再比较多个局部峰”，同时核验所选路径的唇缘归属。']
    header+=['三点弯第 250、251、252 帧的识别弧长分别为 191.25、48.31、190.60 px。这种前后反向跳变说明长度对端点和路径选择敏感，这三帧没有可见人工尖端评分，不能据此判定试件开裂或闭合了约 143 px。']
    header+=focus_tables(b,scores,records,['v3_6','v4_2','v5_0','v5_1',stage])
    header+=['## 合成与对照',f"原有阴性误报 {res['negative_fp']}/{len(legacy_neg)}，弱带通过 {count(weak)}/216，错接 {res['weak_wrong']} 次。已有 control 探针通过 {count(ctr)}/{len(ctr)}。以下保留附加团块阴性分母。"]
    body=[]
    for case in dict.fromkeys(x['case'] for x in probes if x['case'].startswith('mouth_')):
        a=[x for x in probes if x['case']==case];negative=a[0]['negative']=='True'
        totals=[sum(x[m+'_valid']=='False' if negative else bool(x[m+'_error']) and float(x[m+'_error'])<=10 for x in a) for m in ('baseline','width')]
        body.append([case,len(a),*totals,count(a),sum(x['pick']=='DISTAL' for x in a),sum(x['passed']=='True' and float(x['coverage'])>=.80 and float(x['precision'])>=.80 for x in a) if not negative else '—'])
    header+=[table(['新增探针','样本','V5.1 端点/拒绝','仅宽带','V5.2 端点/拒绝','远端裁决次数','同时满足路径覆盖/精度≥80%'],body),'宽团块干扰、宽团块加真实分支、存在窄折痕且真分支中段几乎不可见，以及具有突出中心的较粗真裂纹，覆盖三种倍率与三档曝光。新增阳性单列端点通过，路径完整性另列。']
    header+=['新增竞争分支中，完整模式尖端命中 33/36，但按 2.5 个原尺度像素容差计算，36 次均未同时达到 80% 路径覆盖和精度。低对比段内回溯可以经过另一唇缘，再接上同一远端。此类帧的弧长是实际输出路径的几何长度，不能据端点命中判为真实裂纹长度合格。']
    header+=probe_tables([('V5.1',read_csv(b.BASE/'paired_probes.csv')),('V5.2',probes)])
    pack(b,'REPORT.md',header)
    for dest in (b.OUT,b.ROOT/'evidence'/stage,b.ROOT/'evidence'):b.save(dest/'latest_metrics.json',res)
    print(res)
if __name__=='__main__':main()
