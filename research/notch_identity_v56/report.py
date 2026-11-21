"""Publish the frozen ablation, perturbations, per-branch decisions and failure curves."""
import json,math,os
from collections import Counter
import numpy as np
from . import batch as b
from .difference_views import source_frames
from research.notch_identity_v42.reporting import collect,metric_tables,pack,table,read_csv,NAMES,num,aggregate,failure_list

STAGE='v5_6'

def jitter_tables():
    rows=read_csv(b.OUT/'jitter_summary.csv')
    assert b.sha(b.OUT/'jitter_summary.csv')==b.read(b.OUT/'freeze.json')['jitter']
    data=read_csv(b.OUT/'jitter_rows.csv')
    def policy(row):
        return bool(row['median']) and float(row['median'])<=2 and int(row['joint'])>=int(row['base_joint'])
    short=[r for r in rows if r['version']==STAGE and abs(int(r['delta']))==10]
    head=['## 基准点扰动脱敏测试',
          '每幅原图重新运行 25 种输入：原始点对，以及同时移动双点、仅移动 P1、仅移动 P2；每种沿点对轴线或右法向移动 −20、−10、+10、+20 px。固定参考图与其原始点保持原样。仅 V5.4 按原版流程重做锚点参考映射；V5.6 从原始参考图做纹理配准。横移零点会改变投影长度，尖端漂移统一在当前原图坐标系计算。',
          '开发组A使用全部 20 个标注帧（19 个可见），合成使用 14 类各一个固定样例（1×、标准曝光、低噪声）。合成扰动试验使用位于图内的点对，独立于全量探针矩阵的历史提示接口。先封存 1,700 条路径预测，再对比标注。中位和最大漂移仅对原始与扰动均有尖端的样例计算；另计由有到无/由无到有。联合命中以所有可见尖端为分母。',
          '[全部扰动条件汇总](jitter_summary.csv) · [逐帧、逐方向及状态变化](jitter_rows.csv)']
    for source,label in [('group_a','开发组A'),('synthetic','合成')]:
        lines=[]
        for target,name in [('both','双点'),('p1','仅 P1'),('p2','仅 P2')]:
            for direction,dname in [('axis','轴向'),('normal','法向')]:
                for v in ('v5_4',STAGE):
                    text=[]
                    for delta in (-20,-10,10,20):
                        a=next(r for r in rows if (r['source'],r['target'],r['direction'],r['version'],int(r['delta']))==(source,target,direction,v,delta))
                        text.append(f"{num(a['median'])}/{num(a['maximum'])} · {a['joint']}/{a['visible']} · {a['lost']}/{a['gained']}")
                    lines.append([name,dname,v,*text])
        head+=['### '+label+'扰动结果','每格依次为中位/最大漂移（px）、联合命中/可见、丢失/新增有效坐标。',table(['移动点','方向','版本','−20 px','−10 px','+10 px','+20 px'],lines)]
    stats={}
    for src in ('group_a','synthetic'):
        a=[r for r in short if r['source']==src]
        ds=[float(r['drift']) for r in data if r['source']==src and r['version']==STAGE and abs(int(r['delta']))==10 and r['drift']]
        stats[src]=dict(conditions=len(a),passed=sum(policy(r) for r in a),median=float(np.median(ds)),maximum=max(ds),worst_joint=min(int(r['joint']) for r in a),base_joint=int(a[0]['base_joint']))
    # Count path changes even when the selected endpoint did not move.
    origins={};pairs={};nominal={}
    for line in (b.OUT/'jitter_predictions.jsonl').open():
        row=json.loads(line);key=(row['source'],row['key'],row['version']);mag=abs(row['delta'])
        if not mag:
            origins[key]=row['points']
            if row['source']=='group_a':nominal[row['key'],row['version']]=row['tip']
            continue
        agg=pairs.setdefault((row['source'],row['version'],mag),[0,0,0.])
        agg[0]+=1
        if row['points']!=origins[key]:
            agg[1]+=1
            if row['points'] and origins[key]:
                def arc(pts):return np.linalg.norm(np.diff(np.asarray(pts,float),axis=0),axis=1).sum()
                agg[2]=max(agg[2],abs(arc(row['points'])-arc(origins[key])))
    for line in (b.OUT/'group_a.jsonl').open():
        rec=json.loads(line)
        for v in ('v5_4',STAGE):
            if (rec['frame'],v) in nominal:assert nominal[rec['frame'],v]==rec['models'][v]['full']['tip']
    head+=['### 尖端与整条路径分别核验','在开发组A的 20 个未扰动输入上，两版重跑的尖端分别与各自原始预测一致。全路径逐点比较包括根部和中间点。下列弧长变化仅在两次都有预测时统计。',
        table(['数据','版本','位移幅度 px','扰动样例','路径发生变化','最大弧长变化 px'],[[k[0],k[1],k[2],v[0],v[1],num(v[2])] for k,v in sorted(pairs.items())])]
    return head,stats

def main():
    scores,records,metrics=collect(b);lengths=read_csv(b.OUT/'crack_lengths.csv')
    assert len(lengths)==sum(b.GROUPS.values())
    scope=['## 数据与计量','仅开发组A及合成用于开发。冻结后依次运行三点弯与验证组C，每组一次。三组均有历史曝光。人工标注用于封存后比较，排除组X排除。每帧输出实际起追点至尖端的折线弧长及当前点对中点沿右法向的投影，单位均为原图 px。无有效路径时留空。']
    methods=['## 从原图重建的解耦流程',
        '从 P1/P2 的中点和右法向生成宽走廊。当前灰度图中暗而连通的缺口轮廓给出根部和实测厚度 w；光学窗口尺度由夹限后的 16w 给定。种子来自与缺口接触的暗谷和差分增量。锚距仅用于粗走廊。推理输入为原始图像，固定图的起始平移由缺口纹理模板给出，随后使用图像侧翼配准；全流程不读取旧版的锚点对齐参考缓存。当前实验为向右扩展试件，DP 以原图 x 递增，右法向约束可搜索的带宽。',
        '种子按纵向间隔聚为最多三个通道，宽连续种子带按纵向拆分。每个通道各自分配 DP 状态和前驱表，入口接触段只允许该唇缘的种子和所属行。远处路径可以在同一物理裂纹上重合。V(x,y,k)=S(x,y)+max_j[V(x−1,y−k,j)−0.13|k|−0.19|k−j|]，k∈{−2,…,2}。保留 V5.4 的五斜率主干和原图证据。各分支比较 0.55 倍有效支撑列数、0.85 倍双通道一致列数、末窗清晰度加权长度及 0.85 倍累计净分之和。短裂纹可直接竞争，无 0.19/0.20 锚距分界。',
        '法向来自五个局部切向斜率（−0.70、−0.34、0、+0.34、+0.70）。在三个相对实测厚度的半径处测量 P=D_center−max(D_plus,D_minus)，D 为配准后参考减当前。T=max(2.7σ,0.030L,1)，要求 D_center>1.25T、P>T、P>0.28D_center，并检查纵向持续性、宽团块和参考静态暗线。近根部已有原图/差分联合支撑时，允许该分支仅凭前向细脊桥接。新增列至少 30% 有高置信细脊，含步长与转向代价后的平均净分严格大于零。',
        '同一局部法向上若中心红响应>T，邻侧蓝响应<−T 且蓝幅值>0.48 倍红幅值，则标为偶极子。在同位置有持续的原图细暗谷时豁免。完整模式对其余成对位移的像素把得分上限压到 −0.70，排除其细脊支撑。branches 为结构和入口解耦，normal_bridge 加入单向桥接，v5_6 再加入偶极子过滤。全阶段共用形态特征以便评价各分支；曝光和像素可用性仍会影响结构判别。',
        '[原图入口与配准](../../../research/notch_identity_v56/native.py) · [独立分支 DP 实现](../../../research/notch_identity_v56/terminal.py)']
    jitter,jstats=jitter_tables()
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
    synthetic+= [f"弱带探针的严格通过还要求人工合成路径覆盖率恰为 100%；按统一 80% 路径联合标准为 {weak_joint}/{len(weak)}。开放缺口阴性中的误报均形成了有效路径。纯位移偶极子与叠有真实细裂纹的配对控制分别为 36/36 正确拒绝、36/36 正确定位。入口相互竞争的 mouth_blob_competing 本轮只有 11/36 尖端落入容差，路径联合为 0/36，独立建表仍可能缺失正确入口或走入错误纹理。"]
    focus=[];details=[]
    targets={'group_a':(1,398),'three_point_bend':(144,178,215),'group_c':(221,324,456,510)}
    for g,ids in targets.items():
        for i in ids:
            result=records[g,i]['models'];rr=scores[g,i,STAGE,'full'];m=result[STAGE]['full'];d=m['diagnostics']['dual']
            focus.append([NAMES[g],f'[{i}](difference_views/frames/{g}/{i:04d}.jpg)',rr['gt'] or '不确定',
                *[num(scores[g,i,s,'full']['error_px']) for s in ('v5_4','v5_5','branches','normal_bridge',STAGE)],m['tip'],num(rr['coverage']),num(rr['precision']),num(m['path_length_px']),d['pick'],d['stop']])
            for a in d['branches']:
                details.append([NAMES[g],i,a['id'],a['root'],a['tip'],num(a['value']),num(a['merit']),a['net_length'],num(a['joint_fraction']),a['reason']])
    frames=['## 指定帧独立分支比较',table(['组','帧','人工尖端','V5.4误差','V5.5误差','S1误差','S2误差','V5.6误差','输出尖端','覆盖','精度','弧长 px','选择','状态'],focus),
            table(['组','帧','分支','实际根部','候选尖端','累计分','择优分','有效列','一致比例','条件'],details)]
    os.environ.setdefault('MPLCONFIGDIR',str(b.OUT/'plot_cache'))
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    raw={g:set() for g in b.GROUPS}
    from research.v3_labelme_comparison.compare import PACKAGE
    from research.v3_labelme_comparison.infer import current
    from .native import find_body
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
        if d['stop']=='NO_NOTCH':
            if (g,i) not in reasons:
                meta=b.read(b.OLD/'evidence'/g/str(i)/'metadata.json');info=meta['input']
                body=find_body(current(info['current'],info['image_sha']),meta['current_points'])
                reasons[g,i]='粗走廊未找到暗色缺口连通体' if body is None else f'粗走廊找到轮廓 {body[0].tolist()}，局部缺口前缘精定位失败'
            why+=reasons[g,i]+'。'
        elif d['stop']=='OPEN_FORK':why+='口门附近多个截面被识别成分离的厚暗壁，开口拓扑门提前拒绝。'
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
    from .marker_audit import audit as audit_markers
    marker_evidence=audit_markers()
    marker_evidence+=['三点弯 520 帧中 477 帧触发 OPEN_FORK。在 15 帧可见标注中仅 2 帧输出有效尖端。上述 P2 连通体归因已逐帧复核 144、178、215，验证组C全部 562 帧触发该门。验证组C 221、324、456、510 的正式票数均为 4，事后去掉接触 P1 中心的连通体后分别为 1、0、1、0。此操作也可能同时去掉与标记相连的试件暗部，不能直接当作修复方法。其他触发帧仅统计停止原因。三个新阶段共享口门定位与拓扑门，S1 同时变更配准、尺度与入口构造，因此不能将相对 V5.4 的全部变化归因于多分支 DP。']
    failed,_=failure_list(b,scores,records,['v5_4','v5_5'],explain,('full','raw_only'))
    for g,ids in raw.items():
        dest=b.OUT/'raw_failures'/g;dest.mkdir(exist_ok=True,parents=True)
        for card,_,row in source_frames(g,ids,'raw_only'):card.save(dest/f"{row['frame']:04d}.jpg",quality=91)
    pack(b,'FAILURES_AUDIT.md',failed+marker_evidence+frames)
    group_metrics=[r for r in metrics if r['stage']==STAGE and r['mode']=='full']
    total=aggregate([r for (g,i,s,m),r in scores.items() if s==STAGE and m=='full'])
    gates={r['group']:r['joint']>=dict(group_a=18,three_point_bend=10,group_c=17)[r['group']] and r['severe']==0 for r in group_metrics}
    success=all(gates.values()) and not fps and count(weak)==216 and all(r['passed']==r['conditions'] for r in jstats.values()) and scores['three_point_bend',215,STAGE,'full']['joint']=='True' and scores['group_c',221,STAGE,'full']['joint']=='True' and records['group_a',1]['models'][STAGE]['full']['status']=='no_tip'
    res=dict(primary=STAGE,run=b.OUT.relative_to(b.ROOT).as_posix(),overall_full=total,groups=group_metrics,gates=gates,jitter=jstats,
             negative_fp=fps,negatives=len(negatives),weak_pass=count(weak),weak_wrong=sum(int(r['wrong']) for r in weak),decision='RESEARCH_GATES_PASSED' if success else 'PRODUCTION_NO_GO')
    header=['# V5.6 基准点解耦与多分支独立 DP 验证报告',f"完整模式联合 {total['joint']}/{total['visible']}，尖端命中 {total['hit']}/{total['visible']}，严重误差 {total['severe']}。结论 {res['decision']}。",
            '[逐帧四栏图、独立差分与视频](difference_views/index.html) · [逐帧裂纹长度](crack_lengths.csv) · [失败与退化帧](FAILURES_AUDIT.md) · [冻结记录](freeze.json)']
    usage=[]
    for g,n in b.GROUPS.items():
        rr=[x for x in lengths if x['group']==g]
        with (b.OUT/(g+'.jsonl')).open() as stream:
            ms=[json.loads(line)['models'][STAGE]['full'] for line in stream]
        cc=Counter(m['diagnostics']['dual']['stop'] for m in ms)
        usage.append([NAMES[g],n,sum(bool(x['full_path_length_px']) for x in rr),sum(len(m['diagnostics']['dual']['branches'])>1 for m in ms),str(dict(cc))])
    scope+=['## 全序列覆盖','所有没有有效尖端的帧保留在视频、图册和 CSV，弧长与投影均留空。分支数统计有可回溯路径的入口数。',table(['组','总帧','有实际弧长','多入口有路径','输出/停止分布'],usage)]
    pack(b,'REPORT.md',header+scope+methods+jitter+marker_evidence+metric_tables(b,metrics)+frames+synthetic)
    for dest in (b.OUT,b.ROOT/'evidence'/STAGE,b.ROOT/'evidence'):b.save(dest/'latest_metrics.json',res)
    print(res)
if __name__=='__main__':main()
