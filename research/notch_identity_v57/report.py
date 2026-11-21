"""Publish the frozen ablation, perturbations, per-branch decisions and failure curves."""
import json,math,os
from collections import Counter
import numpy as np
from . import batch as b
from .audit import geometry_and_bridges, development_results
from .difference_views import source_frames
from research.notch_identity_v42.reporting import collect,metric_tables,pack,table,read_csv,NAMES,num,aggregate,failure_list

STAGE='v5_7'

def main():
    scores,records,metrics=collect(b);lengths=read_csv(b.OUT/'crack_lengths.csv')
    assert len(lengths)==sum(b.GROUPS.values())
    scope=['## 数据与计量','仅开发组A及合成用于开发。冻结后依次运行三点弯与验证组C，每组一次。三组均有历史曝光。人工标注用于封存后比较，排除组X排除。每帧输出实际起追点至尖端的折线弧长及当前点对中点沿右法向的投影，单位均为原图 px。无有效路径时留空。']
    methods=['## 算法与计量约定',
        '从 V5.4 的原尺度、缺口前缘、材料窗配准、基础得分与合法种子开始。前缘左侧的一小段缺口本体为 V5.4 的原始接触关系提供上下文。所有可用种子、独立前驱表和新增法向测量的定义域均从实际前缘 x_f 向右。在截取后的数组内取边界重复值。新阶段没有全图暗连通体重建、16w 尺度或 OPEN_FORK 计票。P1/P2 继续参与原始粗 ROI、参考几何对齐与长度投影。没有进行坐标扰动试验。',
        '令 s 为 V5.4 的尺度，按有效种子行的间距聚类，间隔超过 max(1,round(0.008s)) 时分组，再合并最近两簇至最多三簇。连续宽种子带允许二分，单窄入口保留一支。入口保护段按分支中心间隔计算，各支只能进入所属行。每个入口分配独立的五斜率前驱表。V(x,y,k)=S(x,y)+max_j[V(x−1,y−k,j)−0.13|k|−0.19|k−j|]，k∈{−2,−1,0,1,2}。分支择优分为原路径峰值加 0.65 倍有效细脊列数，再加 0.70 倍原图与差分一致列数。仲裁不要求跨过 0.19s 或 0.20s。V5.4 的零增量检查仍保留其原始前段观察窗。',
        'D=固定参考灰度−当前灰度。沿五个切线斜率 −0.70、−0.34、0、0.34、0.70 求法向，在 0.008s 和 0.016s 两个半径取样。平滑中心值 D₀ 与双侧比较，P=D₀−max(D左,D右)。T=max(1,2.7σ,0.030L)，L 为当前曝光灰度跨度。要求 D₀>1.25T、P>T、P>0.28D₀，检查轴向持续性及宽带。若 D₀>T，相邻两倍法向半径内发现负边 B<−T 且 −B>0.48D₀，当前又缺乏持续原图暗谷，则得分压至最多 −0.70，并排除该处细脊。',
        'S1 启用独立分支与偶极子过滤。完整模式从每支原始峰固定整个已观测前缀，近根部至少有两列同时满足原图与差分支撑，才尝试单向延伸。先在同一前驱表中寻找更靠前的局部峰，比较新增列细脊占比、净分和分支择优分；通过时可以更新峰。以胜出峰为起点的第二次单向搜索固定整个前缀，在原尖端后检查连续差分细脊，末端原图暗谷不作要求。参考图中已有的邻近强暗线会剔除差分细脊。新增段至少 30% 为高置信细脊，且实际桥接场与未提权场在扣除步长及转角后的平均净分都必须严格为正。净分包含与原路径最后一个斜率的接续代价。候选未获准时保留原始峰。',
        '逐组 FPS 为已记录算法耗时平均值的倒数，完整模式与纯灰度分别计时，历史版本引用同帧封存记录。播放视频为 10 fps。三组均为历史已曝光序列，人工标注只参与封存后评价。',
        '[V5.7 源码](../../../research/notch_identity_v57/terminal.py) · [逐阶段指标 CSV](ablation.csv) · [合成逐例](paired_probes.csv)']
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
    targets={'group_a':(1,299,398),'three_point_bend':(144,178,215),'group_c':(221,324,456,510)}
    for g,ids in targets.items():
        for i in ids:
            result=records[g,i]['models'];rr=scores[g,i,STAGE,'full'];m=result[STAGE]['full'];d=m['diagnostics']['dual']
            focus.append([NAMES[g],f'[{i}](difference_views/frames/{g}/{i:04d}.jpg)',rr['gt'] or '不确定',
                *[num(scores[g,i,s,'full']['error_px']) for s in ('v5_4','v5_5','branch_dipole',STAGE)],m['tip'],num(rr['coverage']),num(rr['precision']),num(m['path_length_px']),d['pick'],d['stop']])
            for a in d['branches']:
                details.append([NAMES[g],i,a['id'],a['root'],a['tip'],num(a['value']),num(a['merit']),a['net_length'],num(a['joint_fraction']),a['reason'],a['base_tip'],str(a['bridge'])])
    frames=['## 指定帧独立分支比较',table(['组','帧','人工尖端','V5.4误差','V5.5误差','S1误差','V5.6误差','输出尖端','覆盖','精度','弧长 px','选择','状态'],focus),
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
                    ax.plot(np.arange(len(curve))+z['origin'][0],curve,label=f'entry {j}',lw=1.25)
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
    findings=['## 冻结验证的关键变化',
        '开发组A第 1 帧继续报告 no_tip，第 299 帧误差为 0.44 px，第 398 帧仍为 12.10 px。验证组C第 221 帧的三个独立入口最终到达同一点 [2413,2345]，均未接出新尾段。误差为 7.43 px，恢复至 V5.4 水平。',
        '三点弯第 144、178 帧实际误差为 22.75 和 25.38 px。第 215 帧下方分支从 [1474,2729] 到 [1520,2730] 的峰值仍为 54.60。该分支在 x=1566、1603 的列最高累计分分别降到 20.2、11.7，其他两个分支在这两列均已不可达。近根部有 13 列联合支撑，前向搜索没有形成达到长度门槛的尾段。V5.4 曾选用 [1566,2708]，V5.7 实际误差由 40.41 增至 85.76 px。独立建表保留了各入口的得分，但没有压低同一分支里的近口高峰。',
        '新增严重误差出现在三点弯第 248 帧。V5.4 输出 [1637,2723]，误差 7.41 px；V5.7 上、中、下三支分别以口门死端、累计分不足、合法峰结束，唯一通过的下支停在 [1519,2733]，误差 111.20 px。S1 与完整模式给出相同端点，退化在单向桥接前已经发生。',
        '三个真实序列最终选用的单向差分桥接均为 0 次，三点弯有 3 个未必带人工标注的帧选用了同分支下游峰。合成竞争唇缘探针仍有 29/36 个端点未过。下一轮宜在开发数据中构造短近口强峰与斜向弱远峰同时存在的样例，对照各分支在逐列传播中失去可达性的第一列。三点弯、验证组C继续保留作冻结验证。',
        '[三点弯 215 四栏图](difference_views/frames/three_point_bend/0215.jpg) · [215 分支累计分](curves/three_point_bend/0215_full.png) · [248 分支累计分](curves/three_point_bend/0248_full.png)']
    checks=geometry_and_bridges()
    dev=development_results()
    failed,_=failure_list(b,scores,records,['v5_4','v5_5'],explain,('full','raw_only'))
    for g,ids in raw.items():
        dest=b.OUT/'raw_failures'/g;dest.mkdir(exist_ok=True,parents=True)
        for card,_,row in source_frames(g,ids,'raw_only'):card.save(dest/f"{row['frame']:04d}.jpg",quality=91)
    failed.insert(2,'累计曲线为每条独立入口在各原图 x 列上可达的最大 V 值。它包括候选分支基础 DP 的所有终点行；虚线标出人工或发布尖端的横坐标。桥接是否实际采用及净分另列在逐帧文字中。')
    pack(b,'FAILURES_AUDIT.md',failed+findings+frames)
    group_metrics=[r for r in metrics if r['stage']==STAGE and r['mode']=='full']
    total=aggregate([r for (g,i,s,m),r in scores.items() if s==STAGE and m=='full'])
    gates={r['group']:r['joint']>=dict(group_a=18,three_point_bend=10,group_c=17)[r['group']] and r['severe']==0 for r in group_metrics}
    success=all(gates.values()) and not fps and count(weak)==216 and all(r['fps']>=4. for r in group_metrics) and all(scores['three_point_bend',i,STAGE,'full']['joint']=='True' for i in (144,178)) and float(scores['three_point_bend',215,STAGE,'full']['error_px'] or 999)<=2.085 and float(scores['group_a',299,STAGE,'full']['error_px'] or 999)<=float(scores['group_a',299,'v5_4','full']['error_px'])+1e-6 and scores['three_point_bend',215,STAGE,'full']['joint']=='True' and scores['group_c',221,STAGE,'full']['joint']=='True' and records['group_a',1]['models'][STAGE]['full']['status']=='no_tip'
    res=dict(primary=STAGE,run=b.OUT.relative_to(b.ROOT).as_posix(),overall_full=total,groups=group_metrics,gates=gates,
             negative_fp=fps,negatives=len(negatives),weak_pass=count(weak),weak_wrong=sum(int(r['wrong']) for r in weak),decision='RESEARCH_GATES_PASSED' if success else 'PRODUCTION_NO_GO')
    header=['# V5.7 干净基座多分支独立 DP 与法向细脊验证报告',f"完整模式联合 {total['joint']}/{total['visible']}，尖端命中 {total['hit']}/{total['visible']}，严重误差 {total['severe']}。结论 {res['decision']}。",
            '[逐帧四栏图、独立差分与视频](difference_views/index.html) · [逐帧裂纹长度](crack_lengths.csv) · [失败与退化帧](FAILURES_AUDIT.md) · [冻结记录](freeze.json)']
    usage=[]
    for g,n in b.GROUPS.items():
        rr=[x for x in lengths if x['group']==g]
        with (b.OUT/(g+'.jsonl')).open() as stream:
            ms=[json.loads(line)['models'][STAGE]['full'] for line in stream]
        cc=Counter(m['diagnostics']['dual']['stop'] for m in ms)
        usage.append([NAMES[g],n,sum(bool(x['full_path_length_px']) for x in rr),sum(len(m['diagnostics']['dual']['branches'])>1 for m in ms),str(dict(cc))])
    scope+=['## 全序列覆盖','所有没有有效尖端的帧保留在视频、图册和 CSV，弧长与投影均留空。分支数统计有可回溯路径的入口数。',table(['组','总帧','有实际弧长','多入口有路径','输出/停止分布'],usage)]
    pack(b,'REPORT.md',header+findings+scope+methods+dev+checks+metric_tables(b,metrics)+frames+synthetic)
    for dest in (b.OUT,b.ROOT/'evidence'/STAGE,b.ROOT/'evidence'):b.save(dest/'latest_metrics.json',res)
    print(res)
if __name__=='__main__':main()
