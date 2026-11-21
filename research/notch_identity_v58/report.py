"""Publish the frozen ablation, perturbations, per-branch decisions and failure curves."""
import json,math,os
from collections import Counter
import numpy as np
from . import batch as b
from .audit import bridges, jitter_results, development_and_speed
from .difference_views import source_frames
from research.notch_identity_v42.reporting import collect,metric_tables,pack,table,read_csv,NAMES,num,aggregate,failure_list

STAGE='v5_8'

def main():
    scores,records,metrics=collect(b);lengths=read_csv(b.OUT/'crack_lengths.csv')
    assert len(lengths)==sum(b.GROUPS.values())
    scope=['## 数据与计量','仅开发组A及合成用于开发。冻结后依次运行三点弯与验证组C，每组一次。三组均有历史曝光。人工标注用于封存后比较，排除组X排除。每帧输出实际起追点至尖端的折线弧长及当前点对中点沿右法向的投影，单位均为原图 px。无有效路径时留空。']
    methods=['## 分支内谷底检索与桥接',
            'S1 在 V5.7 原配准、光度尺度、五斜率 DP 和原桥接准入上恢复分支内谷底检索。完整模式进一步使用图像尺度、按需法向测量及解锁后的桥接。表内历史算法点位和计时来自同帧封存记录。全序列 V5.8 计时涵盖准备、图像粗配准、材料窗配准、所有分支建表和必要的搜索扩展，不含读盘、标注、绘图、视频编码。S1 实跑全部 60 个标注帧的双模式。',
            '以合法种子行跨度和接触带宽界定近口区。对独立入口中的早峰，从其后所有可达局部极大值按累计分从高到低回溯。沿候选自身的五斜率前驱路径，在早峰所在列至晚峰间寻找累计净分最低列。要求谷底后至少 5 列、净爬升至少 2.5、连续正支持至少 3 列、正支持占比至少 52%、末端短窗净增为正，并通过闭环检查。谷底后的细脊占比至少 30%，实际提权平均净分严格为正。远离缺口的峰若要发起替换，另需与原路径共享到早峰的前缀，并检查完整新增段的细脊占比及提权净分。每支采用首个通过的晚峰。这里不以锚距的 0.19 或 0.20 切分候选。',
            '随后固定前缀，从胜出峰尝试单向桥接。已配准参考上存在强暗线或红蓝偶极子的像素不能提供高置信差分支撑。新增段净分对实际桥接场扣除 0.13|斜率| 和 0.19|转向|，其均值须大于零，且高置信列至少占 30%。保留近根部联合证据和首末列连续性检查。未提权场净分仅记录，不作为完整模式的拒绝条件。',
            '完整模式只从锚点确定上游粗搜索框、粗起点和后处理投影。以初始 288 px 光学尺度定位缺口，检查前缘后方 22、24、26 px 三个灰度截面，取厚度中位数选择 144、288、576 px 光学尺度。由缺口纹理初定位，并尽可能利用两侧材料纹理的亚像素平移随行线性插值，再进行前向材料窗细配准。法向证据仅在有正差分候选的像素计算，沿五个局部斜率自适应比较 1、2、4、7 px 半径，采用突出度、负侧边和原图暗谷判决。每帧各分支共享得分阵列，入口临时屏蔽其他分支的种子区域后恢复。',
            '[检测源码](../../../research/notch_identity_v58/terminal.py) · [图像尺度与按需测量](../../../research/notch_identity_v58/optics.py) · [消融指标](ablation.csv) · [逐例合成数据](paired_probes.csv)']
    probes=read_csv(b.OUT/'paired_probes.csv');weak=[r for r in probes if r['case']=='P1_weak_gap']
    negatives=[r for r in probes if r['negative']=='True'];fps=sum(r['valid']=='True' for r in negatives)
    matrix=[]
    for case in dict.fromkeys(r['case'] for r in probes):
        cells=[]
        for zoom in (.5,1.,2.):
            for photo in ('nominal','dim','bright'):
                a=[r for r in probes if r['case']==case and float(r['zoom'])==zoom and r['photo']==photo]
                if a[0]['negative']=='True':cells.append(f"FP {sum(r['valid']=='True' for r in a)}/{len(a)}")
                else:cells.append(f"{sum(r['passed']=='True' for r in a)}/{sum(bool(r['error']) and float(r['error'])<=10 and min(float(r[k]) for k in ('coverage','precision'))>=.8 for r in a)}/{len(a)}")
        matrix.append([case,*cells])
    count=lambda a:sum(r['passed']=='True' for r in a)
    by_case=Counter(r['case'] for r in negatives if r['valid']=='True')
    synthetic=['## 全量合成矩阵',f"共 {len(probes)} 例，弱带通过 {count(weak)}/{len(weak)}，错接 {sum(int(r['wrong']) for r in weak)}。阴性误报 {fps}/{len(negatives)}，按类型分布 {dict(by_case)}。阳性格依次为原探针通过数、尖端与路径联合命中数、样本数；阴性格为误报/样本。联合要求原尺度端点≤10 px、2.5 px 容差下覆盖及精度均≥80%。",
        table(['探针']+[f'{s}× {p}' for s in (.5,1,2) for p in ('标准','暗','亮')],matrix)]
    weak_joint=sum(bool(r['error']) and float(r['error'])<=10 and min(float(r[k]) for k in ('coverage','precision'))>=.8 for r in weak)
    synthetic+=[f"弱带严格通过要求合成路径覆盖率为 100%；统一联合口径为 {weak_joint}/{len(weak)}。全矩阵包含三档曝光、三种倍率、两档噪声与两个随机种子。"]
    focus=[];details=[]
    targets={'group_a':(1,299,398),'three_point_bend':(144,178,215,248,407),'group_c':(221,324,456,510)}
    for g,ids in targets.items():
        for i in ids:
            result=records[g,i]['models'];rr=scores[g,i,STAGE,'full'];m=result[STAGE]['full'];d=m['diagnostics']['dual']
            focus.append([NAMES[g],f'[{i}](difference_views/frames/{g}/{i:04d}.jpg)',rr['gt'] or '不确定',
                *[num(scores[g,i,s,'full']['error_px']) for s in ('v5_4','v5_7','valley_recovery',STAGE)],m['tip'],num(rr['coverage']),num(rr['precision']),num(m['path_length_px']),d['pick'],d['stop']])
            for a in d['branches']:
                details.append([NAMES[g],i,a['id'],a['root'],a['tip'],num(a['value']),num(a['merit']),a['net_length'],num(a['joint_fraction']),a['reason'],a['base_tip'],str(a['bridge'])])
    frames=['## 指定帧独立分支比较',table(['组','帧','人工尖端','V5.4误差','V5.7误差','S1误差','V5.8误差','输出尖端','覆盖','精度','弧长 px','选择','状态'],focus),
            table(['组','帧','分支','实际根部','候选尖端','累计分','择优分','有效列','一致比例','条件','原峰','桥接判据'],details)]
    os.environ.setdefault('MPLCONFIGDIR',str(b.OUT/'plot_cache'))
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    raw={g:set() for g in b.GROUPS}
    from research.v3_labelme_comparison.compare import PACKAGE
    from research.v3_labelme_comparison.infer import current

    locations={(r["dataset_id"],int(r["frame_id"])):r for r in read_csv(b.SELECT)}
    reasons={}

    def explain(g,i,m,row,mode):
        d=m['diagnostics']['dual'];items=d['branches'];gt=np.asarray(json.loads(row['gt']))
        fig,ax=plt.subplots(figsize=(8.5,3.6),layout='constrained')
        path=b.OUT/'surfaces'/g/f'{i:04d}_{mode}.npz'
        if path.exists():
            with np.load(path) as z:
                if not len(z['branch_ids']):ax.text(.05,.85,'No reachable branch lattice',transform=ax.transAxes)
                for j,curve in zip(z['branch_ids'],z['curves']):
                    curve=curve.copy();curve[~np.isfinite(curve)]=np.nan
                    artist,=ax.plot(np.arange(len(curve))+z['origin'][0],curve,label=f'entry {j}',lw=1.25)
                    branch=next((a for a in items if a['id']==j),None)
                    if branch:
                        br=branch['bridge'];late=br.get('downstream_peak')
                        if late:
                            for field,shape in [('valley_x','v'),('late_x','^')]:
                                k=late[field]
                                if np.isfinite(curve[k]):
                                    ax.plot(k+z['origin'][0],curve[k],marker=shape,color=artist.get_color())
                        if d.get('pick')=='BRANCH_'+str(j) and br.get('accepted'):
                            ax.axvspan(branch['tip'][0]-br['columns'],branch['tip'][0],alpha=.10,color=artist.get_color(),label='published bridge')
        else:ax.text(.05,.85,'No reachable branch lattice',transform=ax.transAxes)
        ax.axvline(gt[0],ls='--',color='black',label='manual tip')
        if 'front' in d:ax.axvline(d['front'],ls=':',color='grey',label='notch front')
        if m['tip']:ax.axvline(m['tip'][0],color='orangered',ls=':',label='published tip')
        ax.legend(fontsize=8);ax.grid(alpha=.2);ax.set(xlabel='Original image x (px)',ylabel='Max reachable cumulative score',title=f'{g} / {i} / {mode}')
        target=b.OUT/'curves'/g/f'{i:04d}_{mode}.png';target.parent.mkdir(exist_ok=True,parents=True);fig.savefig(target,dpi=125);plt.close(fig)
        valid=[a for a in items if a['reason']=='VALID']
        if not items:why=f"未形成可竞争分支；终止状态 {d['stop']}。"
        elif not valid:why='入口已产生候选，全部被拒绝。'+str(dict(Counter(a['reason'] for a in items)))+'。'
        else:
            chosen=next(a for a in valid if d['pick']=='BRANCH_'+str(a['id']))
            near=min(items,key=lambda a:math.dist(gt,a['tip']))
            why=f"选中入口 {chosen['id']}，有效支撑 {chosen['net_length']} 列、全路双通道一致比例 {chosen['joint_fraction']:.2f}。"
            if math.dist(gt,near['tip'])<=10 and near['id']!=chosen['id']:why+=f"另一个入口 {near['id']} 的端点已进入容差，状态 {near['reason']}，其择优分 {near['merit']:.2f}，获胜分 {chosen['merit']:.2f}。"
            elif float(row['error_px'] or 0)>10:why+=f"全部入口的最终候选中最近者仍离人工端点 {math.dist(gt,near['tip']):.2f} px，误差已出现在分支内选峰或支撑构造阶段。"
            elif row['joint']!='True':why+='端点已命中，但覆盖或路径精度低于 80%。'
        if valid:
            bridge=chosen['bridge']
            why+=f" 原始峰 {chosen['base_tip']}，前向延伸记录 {bridge}。"
            if path.is_file():
                with np.load(path) as z:
                    col=round(gt[0])-z['origin'][0]
                    if len(z['branch_ids']) and 0<=col<z['curves'].shape[1]:
                        cc=z['curves'][:,col];finite=cc[np.isfinite(cc)]
                        why+=f" 人工端点所在列有 {len(finite)}/{len(cc)} 支可达"
                        why+=f"，该列最高累计分 {float(finite.max()):.2f}。" if len(finite) else "。"
                        why+="列可达仅表示横坐标被覆盖，实际候选仍按二维误差判定。" 
        if m['root']:
            ann=b.read(PACKAGE/locations[g,i]['selected_json'])
            annotated=[np.asarray(sh['points']) for sh in ann['shapes'] if sh['label']=='crack_path']
            if annotated:
                pts=np.vstack(annotated);start=pts[np.argmin(pts[:,0])]
                why+=f" 实际起追 {m['root']}，与人工路径最左点相距 {math.dist(m['root'],start):.2f} px。"
        why+=f" [独立累计分曲线]({target.relative_to(b.OUT).as_posix()})"
        if mode=='raw_only':
            raw[g].add(i);why+=f' [纯灰度四栏图](raw_failures/{g}/{i:04d}.jpg)'
        return why
    jitter_gates,jitter=jitter_results()
    checks=bridges()
    findings=['## 验证结论与修正版本',
        '下表和三个验证视频均属 r04。r04 完成三组全序列及同步扰动，但其前向桥接仍有沿用自 V5.7 的首末列和最短长度限制。随后按任务书清理这些限制并显式屏蔽静态暗线，另冻结为 r05。r05 仅运行合成、开发组A及其同步扰动。三点弯、验证组C已完成本轮唯一一次冻结验证，尚没有 r05 验证精度。 [r05 修正与开发组复验](../v58_strict_dev_20261120_r05/STRICT_DEV.md)',
        '开发组A从 18/19 降到 17/19。第 299 帧的发布端点为 [1228,1162]，误差 19.84 px。开发组回放发现，约 [1248,1160] 的下游候选确实可达，但自早峰往后仅约 20% 列满足参考静态排除后的细脊条件，低于 30%。第 398 帧误差 12.10 px。第 1 帧继续输出 no_tip。',
        '三点弯从 7/15 升到 9/15，第 248 帧由 111.20 降到 3.02 px。S1 单独恢复谷底检索已可从 [1519,2733] 替换至 [1632,2723]。第 215 帧 S1 同样从 [1520,2730] 找到 [1566,2708]；r04 已发布的完整模式停在 [1565,2710]，误差 40.91 px。其 46 列桥接候选中细脊占比 41.3%，提权净分 +0.315，未提权净分 −0.219。记录显示候选长度、占比和提权净分均已达标，剩余拒绝条件是 r04 的首四列或末列检查。日志没有保存是哪一项失败。r05 能否命中此帧尚未验证。第 407 帧误差 21.09 px，其发布分支有近根部证据，但没有可验收长度的桥接尾段。',
        '验证组C 20 个可见标注帧均出现超过 100 px 的误差。S1 在同组仍为 17/20，完整模式首先在确定缺口前缘时发生偏移。20 帧的前缘 x 相对 V5.7 向右移动 131–136 px，实际起追点的二维位移中位数为 165.70 px。第 221 帧从 [2252,2329] 改在 [2383,2234] 起追，误差由 7.43 增至 134.67 px。562 帧均取 576 px 光学尺度，全组发布前向桥接为 0。该组主要故障发生在桥接前，应优先在开发图上验证光学尺度切换是否选中了另一条暗边。同步移动输入坐标后的稳定不能证明缺口选对。',
        '[三点弯 215 图](difference_views/frames/three_point_bend/0215.jpg) · [三点弯 248 图](difference_views/frames/three_point_bend/0248.jpg) · [验证组C 221 图](difference_views/frames/group_c/0221.jpg)']
    dev=development_and_speed(metrics)
    failed,_=failure_list(b,scores,records,['v5_4','v5_7'],explain,('full','raw_only'))
    for g,ids in raw.items():
        dest=b.OUT/'raw_failures'/g;dest.mkdir(exist_ok=True,parents=True)
        for card,_,row in source_frames(g,ids,'raw_only'):card.save(dest/f"{row['frame']:04d}.jpg",quality=91)
    failed.insert(2,'累计曲线为每条独立入口在各原图 x 列上可达的最大 V 值。上下三角标出通过谷底检验的两个横坐标；阴影为已发布的前向桥接区间。它包括候选分支基础 DP 的所有终点行；虚线标出人工或发布尖端的横坐标。桥接是否实际采用及净分另列在逐帧文字中。')
    pack(b,'FAILURES_AUDIT.md',failed+findings+frames)
    group_metrics=[r for r in metrics if r['stage']==STAGE and r['mode']=='full']
    total=aggregate([r for (g,i,s,m),r in scores.items() if s==STAGE and m=='full'])
    gates={r['group']:r['joint']>=dict(group_a=18,three_point_bend=10,group_c=17)[r['group']] and r['severe']==0 for r in group_metrics}
    focus_gates={
        'three_215':scores['three_point_bend',215,STAGE,'full']['joint']=='True' and float(scores['three_point_bend',215,STAGE,'full']['error_px'] or 999)<=2.085,
        'three_407':scores['three_point_bend',407,STAGE,'full']['joint']=='True',
        'three_248':float(scores['three_point_bend',248,STAGE,'full']['error_px'] or 999)<=10,
        'group_c_221':float(scores['group_c',221,STAGE,'full']['error_px'] or 999)<=float(scores['group_c',221,'v5_7','full']['error_px'])+1e-6,
        'group_a_1':records['group_a',1]['models'][STAGE]['full']['status']=='no_tip'}
    success=all(gates.values()) and all(focus_gates.values()) and not fps and count(weak)==216 and all(r['fps']>=4. for r in group_metrics if r['group']!='group_a') and all(jitter_gates.values())
    res=dict(primary=STAGE,run=b.OUT.relative_to(b.ROOT).as_posix(),overall_full=total,groups=group_metrics,gates=gates,jitter=jitter_gates,focus=focus_gates,
             negative_fp=fps,negatives=len(negatives),weak_pass=count(weak),weak_wrong=sum(int(r['wrong']) for r in weak),validated_revision='r04',corrected_revision='r05_development_only',decision='RESEARCH_GATES_PASSED' if success else 'PRODUCTION_NO_GO')
    header=['# V5.8 分支内谷底爬升与桥接解锁验证报告',f"完整模式联合 {total['joint']}/{total['visible']}，尖端命中 {total['hit']}/{total['visible']}，严重误差 {total['severe']}。结论 {res['decision']}。",
            '[逐帧四栏图、独立差分与视频](difference_views/index.html) · [逐帧裂纹长度](crack_lengths.csv) · [失败与退化帧](FAILURES_AUDIT.md) · [冻结记录](freeze.json)']
    usage=[]
    for g,n in b.GROUPS.items():
        rr=[x for x in lengths if x['group']==g]
        with (b.OUT/(g+'.jsonl')).open() as stream:
            ms=[json.loads(line)['models'][STAGE]['full'] for line in stream]
        cc=Counter(m['diagnostics']['dual']['stop'] for m in ms)
        usage.append([NAMES[g],n,sum(bool(x['full_path_length_px']) for x in rr),sum(len(m['diagnostics']['dual']['branches'])>1 for m in ms),str(dict(cc))])
    scope+=['## 全序列覆盖','所有没有有效尖端的帧保留在视频、图册和 CSV，弧长与投影均留空。分支数统计有可回溯路径的入口数。',table(['组','总帧','有实际弧长','多入口有路径','输出/停止分布'],usage)]
    pack(b,'REPORT.md',header+findings+scope+methods+dev+jitter+checks+metric_tables(b,metrics)+frames+synthetic)
    for dest in (b.OUT,b.ROOT/'evidence'/STAGE,b.ROOT/'evidence'):b.save(dest/'latest_metrics.json',res)
    print(res)
if __name__=='__main__':main()
