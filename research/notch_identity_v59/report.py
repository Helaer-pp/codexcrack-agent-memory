"""Summarize the complete sealed run, its matched controls and individual failures."""
import hashlib
import json
import math
import os
import statistics
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from research.v3_labelme_comparison.compare import write_csv
from research.unified_crack_tip_60q.common import clean
from .batch import ROOT,OUT,BASELINE,GROUPS,read,read_csv,save,sha,sources

EVIDENCE=ROOT/'evidence/v5_9'
NAMES={'group_a':'开发组A','three_point_bend':'三点弯','group_c':'验证组C'}
MODES=['full','raw_only']
PRIOR=['v3_6','v4_2','v5_4','v5_7','valley_recovery','v5_8']
LABEL={'v3_6':'V3.6','v4_2':'V4.2','v5_4':'V5.4','v5_7':'V5.7','valley_recovery':'V5.8-S1','v5_8':'V5.8','apex_only':'仅顶点吸附','v5_9':'V5.9'}
def table(headers,rows):
    def row(values):return '| '+' | '.join(map(str,values))+' |'
    return '\n'.join([row(headers),row(['---']*len(headers)),*[row(r) for r in rows]])

def link(label,p):
    return '['+str(label)+']('+Path(os.path.relpath(p,EVIDENCE)).as_posix()+')'

def num(value):
    return f'{float(value):.2f}' if value not in ('',None) else '—'

def summary(rs):
    visible=[r for r in rs if r['state']=='VISIBLE']
    errors=[float(r['error_px']) for r in visible if r['error_px']]
    return [len(visible),len(errors),sum(x<=5 for x in errors),sum(x<=10 for x in errors),sum(r['joint']=='True' for r in visible),sum(x>100 for x in errors),num(statistics.median(errors) if errors else None),num(max(errors,default=None))]

def main():
    EVIDENCE.mkdir(exist_ok=True,parents=True)
    lock=read(OUT/'freeze.json')
    assert lock['sources']==sources()
    ab=read_csv(BASELINE/'ablation.csv')
    full={};scores={};rates={};comparison=[];all_lengths=[];primary=[];media=[];special=[];case_notes=[]
    for g,n in GROUPS.items():
        src=OUT/(g+'.jsonl')
        seal=read(OUT/(g+'_seal.json'))
        assert seal['sources']==lock['sources'] and seal['predictions']==sha(src)
        recs=[json.loads(line) for line in src.open()]
        assert len(recs)==n and [r['frame'] for r in recs]==list(range(1,n+1))
        scores[g]=read_csv(OUT/(g+'_scores.csv'))
        full[g]={r['frame']:r for r in recs}
        all_lengths.extend(read_csv(OUT/(g+'_lengths.csv')))
        placement_names=list(recs[0]['placements'])
        for placement in placement_names:
            a=[r for r in scores[g] if r['placement']==placement]
            for mode,field in [('full','seconds'),('raw_only','raw_seconds')]:
                rates[g,placement,mode]=n/sum(r['placements'][placement]['v5_9'][field] for r in recs)
                for stage in PRIOR+['apex_only','v5_9']:
                    rs=[r for r in a if r['stage']==stage and r['mode']==mode]
                    if rs:
                        stat=summary(rs)
                        fps=rates[g,placement,mode] if stage=='v5_9' else len(rs)/sum(float(r['seconds']) for r in rs)
                        timed=n if stage=='v5_9' else len(rs)
                    else:
                        prev=next(r for r in ab if (r['group'],r['mode'],r['stage'])==(g,mode,stage))
                        stat=[int(prev[k]) for k in ('visible','valid','hit5','hit','joint','severe')]+[num(prev['median']),num(prev['max'])]
                        fps=float(prev['fps']);timed=int(prev['timed'])
                    comparison.append([NAMES[g],placement,LABEL[stage],mode,*stat,num(fps),timed])
                if mode=='full':
                    rs=[r for r in a if r['stage']=='v5_9' and r['mode']==mode]
                    stat=summary(rs);target={'group_a':18,'three_point_bend':10,'group_c':17}[g]
                    primary.append([NAMES[g],placement,n,stat[1],f'{stat[3]}/{stat[0]}',f'{stat[4]}/{stat[0]}',stat[5],stat[6],stat[7],num(rates[g,placement,mode]),'通过' if stat[4]>=target and stat[3]>=target and stat[5]==0 and rates[g,placement,mode]>=4 and (g!='group_a' or next(x for x in rs if x['frame']=='1')['status']!='VALID') else '未通过'])
            keyframes={'group_a':[1,299,398],'three_point_bend':[144,178,215,248,407],'group_c':[1,7,38,54,221,324,335,345,456,510]}[g]
            for i in keyframes:
                rec=recs[i-1];m=rec['placements'][placement]['v5_9']['full'];diag=m['diagnostics']['dual']
                row=next(r for r in a if (r['stage'],r['mode'],int(r['frame']))==('v5_9','full',i))
                s=next(r for r in a if (r['stage'],r['mode'],int(r['frame']))==('apex_only','full',i))
                winner=next((b for b in diag['branches'] if diag['pick']=='BRANCH_'+str(b['id'])),{})
                bridge=winner.get('bridge',{})
                kind='差分桥接' if bridge.get('accepted') else '灰度尾段' if bridge.get('raw_extension') else '谷底后远峰' if bridge.get('downstream_peak') else diag.get('stop','—')
                special.append([NAMES[g],placement,i,num(s['error_px']),num(row['error_px']),m['tip'] or '—',num(m['path_length_px']),kind])
                if i in (215,299,345) and placement==placement_names[-1]:
                    case_notes.append(f"{NAMES[g]}第 {i} 帧，最终端点 {m['tip']}，距标注 {num(row['error_px'])} px，分支选择 {diag['pick']}，判定 {kind}。")
        media.append([NAMES[g],placement_names[-1],link('完整视频',OUT/'difference_views'/(g+'.mp4')),link('长度和坐标',OUT/(g+'_lengths.csv')),link('标注帧评分',OUT/(g+'_scores.csv'))])
    write_csv(OUT/'crack_lengths.csv',all_lengths)
    placement_comparison=[]
    for i,rec in full['group_c'].items():
        for mode in MODES:
            a,b=[rec['placements'][k]['v5_9'][mode] for k in ('original','bright')]
            drift=math.dist(a['tip'],b['tip']) if a['tip'] and b['tip'] else None
            placement_comparison.append(dict(frame=i,mode=mode,original_tip=a['tip'],bright_tip=b['tip'],drift=drift,
                path_equal=a['points']==b['points'],valid_changed=bool(a['tip'])!=bool(b['tip']),
                arc_original=a['path_length_px'],arc_bright=b['path_length_px'],
                projection_original=a['projected_length_px'],projection_bright=b['projected_length_px']))
    write_csv(OUT/'placement_comparison.csv',placement_comparison)
    probes=read_csv(OUT/'paired_probes.csv');negative=[r for r in probes if r['negative']=='True']
    syn=read(OUT/'synthetic_jitter.json')
    def syn_joint(r):
        pts=np.asarray(r['points']);gt=np.asarray(r['truth'])
        if not len(gt):return None
        if not len(pts):return False
        return (math.dist(r['tip'],gt[-1])<=10 and min((cKDTree(pts).query(gt)[0]<=2.5).mean(),(cKDTree(gt).query(pts)[0]<=2.5).mean())>=.8)
    jitter=[]
    for g in ('group_a','group_c'):
        for r in read_csv(OUT/(g+'_jitter.csv')):
            jitter.append(dict(group=g,key=r['frame'],axis=r['direction'],delta=r['delta'],correction=float(r['correction']),drift=float(r['drift']) if r['drift'] else None,
                valid=bool(r['tip']),base_valid=bool(r['baseline_tip']),joint=r['joint'],base_joint=r['baseline_joint']))
    nominal={r['key']:r for r in syn if not r['delta']}
    for r in syn:
        if not r['delta']:continue
        n=nominal[r['key']]
        jitter.append(dict(group='synthetic',key=r['key'],axis=r['direction'],delta=r['delta'],correction=0.,
            drift=math.dist(r['tip'],n['tip']) if r['tip'] and n['tip'] else None,valid=bool(r['tip']),base_valid=bool(n['tip']),joint=syn_joint(r),base_joint=syn_joint(n)))
    write_csv(OUT/'jitter_all.csv',jitter)
    js=[];worst={}
    for g in ('synthetic','group_a','group_c'):
        a=[r for r in jitter if r['group']==g]
        for axis,delta in [('全部','全部')]+list(dict.fromkeys((r['axis'],r['delta']) for r in a)):
            rs=a if axis=='全部' else [r for r in a if (r['axis'],r['delta'])==(axis,delta)]
            d=[r['drift'] for r in rs if r['drift'] is not None]
            js.append([NAMES.get(g,'合成'),axis,delta,len(rs),len(d),num(statistics.median(d) if d else None),num(max(d,default=None)),sum(r['base_joint']!=r['joint'] for r in rs),sum(r['base_valid']!=r['valid'] for r in rs),sum(r['correction']>.70711 for r in rs)])
        worst[g]=max((r for r in a if r['drift'] is not None),key=lambda r:r['drift'],default=None)
    def pstats(rows):
        pos=[r for r in rows if r['negative']=='False'];neg=[r for r in rows if r['negative']=='True']
        return [len(rows),f"{sum(r['passed']=='True' for r in rows)}/{len(rows)}",f"{sum(r['valid']=='True' for r in neg)}/{len(neg)}",f"{sum(r['error']!='' and float(r['error'])<=10 and min(float(r['coverage']),float(r['precision']))>=.8 for r in pos)}/{len(pos)}"]
    probes_table=[[z,photo,*pstats([r for r in probes if r['zoom']==z and r['photo']==photo])] for z in ('0.5','1.0','2.0') for photo in ('dim','nominal','bright')]
    spec=['P1_weak_gap','P6_isolated','material_edge_glare','weak_material_bridge']
    focus=[[case,*pstats([r for r in probes if r['case']==case])] for case in spec]
    fails=read_csv(OUT/'failure_index.csv') if (OUT/'failure_index.csv').exists() else []
    fail_report=['# V5.9 失败与退化帧专项分析','真实图像纳入可见标注里尖端超出 10 px 或路径联合失败的每一帧，逐一列出完整与纯灰度模式。曲线记录各入口的累计得分，虚线标出人工尖端横坐标。没有可达入口时保留空图并注明原因。']
    for g in GROUPS:
        rs=[r for r in fails if r['group']==g]
        if not rs:continue
        fail_report+=['## '+NAMES[g],table(['位置','模式','帧','误差 px','覆盖','精度','失效证据','图像 / 曲线'],[
            [r['placement'],r['mode'],r['frame'],num(r['error']),num(r['coverage']),num(r['precision']),r['cause'],link('四栏图',Path(r['card']))+' · '+link('分支曲线',Path(r['curve']))] for r in rs])]
    fail_report+=['## 重点退化发生在哪一步',
        '开发组A 398 的已发布路径到达人工尖端附近却继续延长，误差 12.10 px。验证组C两种点位的失败集中在同三帧：38、54 帧在标注前停止，510 帧越过标注。三点弯 215、248 均从下唇缘分支出发，在完整模式的原始峰停止，没有批准远峰或桥接。仅顶点吸附模式在相同帧可到达更远位置。',
        '下表统计完整模式失败帧在人工尖端所在 x 列是否仍有可达 DP 路径，以及所有分支的最近候选端点误差。该列可达只说明横向搜索范围覆盖该位置，无法证明路径与真实裂纹重合。']
    diag_rows=[]
    for e in fails:
        if e['mode']!='full':continue
        g=e['group'];i=int(e['frame']);pl=e['placement']
        q=next(r for r in scores[g] if (int(r['frame']),r['mode'],r['placement'],r['stage'])==(i,'full',pl,'v5_9'))
        gt=json.loads(q['gt'])
        d=full[g][i]['placements'][pl]['v5_9']['full']['diagnostics']['dual']
        candidates=[math.dist(c['tip'],gt) for c in d['branches']]
        with np.load(OUT/'surfaces'/g/pl/f'{i:04d}_full.npz') as surf:
            k=round(gt[0]-surf['origin'][0]);curves=surf['curves']
            finite=(np.isfinite(curves[:,k])&(curves[:,k]>-1e8)) if curves.ndim==2 and 0<=k<curves.shape[1] else np.array([],bool)
            diag_rows.append([NAMES[g],pl,i,len(d['branches']),num(min(candidates,default=None)),int(finite.sum()),num(max(curves[finite,k]) if finite.any() else None)])
    fail_report.append(table(['组','点位','帧','候选分支数','最近候选误差 px','到达人工 x 列的分支数','该列最高累计分'],diag_rows))
    save_text=lambda path,parts:path.write_text('\n\n'.join(parts)+'\n','utf8')
    save_text(EVIDENCE/'FAILURES_AUDIT.md',fail_report)
    visible_fails=sum(r['stage']=='v5_9' and r['joint']=='False' for a in scores.values() for r in a)
    assert visible_fails==len(fails)
    hdr=['组','点位','版本','模式','可见','有尖端','≤5','≤10','联合','严重','中位 px','最大 px','FPS','计时帧数']
    w=worst['group_c']
    native=[r for r in read_csv(OUT/'group_a_native_jitter.csv') if float(r['delta'])]
    native_d=[float(r['drift']) for r in native if r['drift']]
    cp=[r for r in placement_comparison if r['mode']=='full']
    snapshots=[]
    for rr in range(1,5):
        folder=OUT.with_name('v59_converged_r0'+str(rr))
        p=read_csv(folder/'paired_probes.csv');ss=[r for r in read_csv(folder/'group_a_scores.csv') if r['stage']=='v5_9' and r['mode']=='full']
        snapshots.append([f'r0{rr}',sum(r['joint']=='True' for r in ss),sum(r['valid']==r['negative']=='True' for r in p),*[sum(r['passed']=='True' and r['case']==k for r in p) for k in ('P6_isolated','weak_material_bridge')]])
    report=['# V5.9 材料带内缺口吸附与边界防爬验证报告',
      '使用 r04 同一冻结代码按开发组A开发、三点弯验证、验证组C验证的顺序完成。验证组C的原点位与亮区点位共用用户指定的材料带和同一个检测器。人工标注仅用于封存后的比较；排除组X排除。三点弯与验证组C均有历史曝光。',
      '**总验收未通过。** 三组完整模式联合命中 39/54，出现 1 帧超过 100 px 的严重误差。各组按任务书选用一个输入条件，验证组C以亮区点位计入一次。V5.8 r04 同口径为 26/54，V5.7 为 42/54。主要收益在验证组C，主要损失在三点弯。',
      '## 同一冻结版的验收结果',
      table(['组','点位','全序列','可见标注有尖端','Hit@10','联合','严重','中位 px','最大 px','FPS','精度与速度门'],primary),
      '各组联合命中目标为开发组A 18/19、三点弯 10/15、验证组C两种点位各 17/20，同时要求严重误差为零、开发组A第一帧无输出、速度至少 4 FPS。同批每组 20 个标注帧，仅可见端点参与命中分母。Joint 同时要求端点误差 ≤10 px、在 10 px 容差下路径覆盖率和精确率均 ≥80%。误差 >100 px 为严重。无输出计作未命中，中位数和最大值只在有效输出上计算。',
      '## 算法、坐标与数据隔离',
      '在固定参考粗搜索区，取点对前方材料的逐行灰度中位数。阈值为低分位灰度加 0.43 倍参考灰度跨度，选择与粗定位最近的连续材料带。将外边界按点对中点相对位移传递至当前图，取两帧交集。验证组C外层输入遵循用户登记的亮材料窗口；两种点位条件都使用该窗口。亮区替代点要求参考和当前的 9×9 邻域均满足亮度条件，再选择距请求最近的合法位置。',
      '在材料带内对低于局部第 3 百分位加 0.29 倍跨度的区域做 5×5 椭圆开运算。选取与上游边缘相连、未顶到搜索右边界的缺口轮廓，按纵向邻近度筛选。轮廓最右列为顶点估计，同列像素纵坐标中位数为顶点高度。固定参考提供初始位置，再在当前图吸附并沿多唇缘生成 DP 入口。P1/P2 用于粗定位、材料带平移和长度投影。真实原图统一使用 288 px 搜索尺度；合成实验按已知图像采样倍率同步换算。没有根据暗区厚度重选 576 px 前缘。',
      '外边界内侧留出 max(3, round(0.035×尺度)) px 安全带。在联合得分场屏蔽该区域的种子、DP 支撑和桥接。桥接和远峰延伸须落在前缀末 13 点估算的切向走廊，允许纵向偏离 3+0.32×前进距离 px。差分桥接保留细脊占比 ≥30%、扣除步长和转向后平均净分为正、已配准参考静态暗线屏蔽。常规二次配准失败时，仅强缺口匹配（NCC ≥0.95）且根部至少四列同时有细脊和灰度支持时使用光学对齐的局部差分。',
      '第 299 帧开发对照显示，直接放宽静态排除会错接独立划痕。正式版保留 r05 的静态暗线阈值。若差分桥接未通过、根部已证实且纯灰度路径仍有短延伸，额外要求切向一致、灰度净分均值 ≥0.10、逐点当前谷深比参考更强的列占至少 33%、保留差分细脊的列占至少 15%、两种支撑并集至少 60%。该尾段单独记录为 raw_extension。',
      table(['开发轮次','开发组A联合 /19','阴性误报 /468','独立划痕 /36','材料带弱桥 /36'],snapshots),
      '最后一次开发轮保留独立的 S1 消融通道和与 S1 相同的参考预对齐方式。冻结清单覆盖推理、点位和开发探针源码，并记录验证组C操作员窗口的哈希。'+link('冻结记录',OUT/'freeze.json')+' · '+link('检测实现',ROOT/'research/notch_identity_v59/terminal.py')+' · '+link('缺口与材料带',ROOT/'research/notch_identity_v59/geometry.py'),
      '## 普适性与失效位置',
      ' '.join(case_notes),
      '三点弯的仅顶点吸附消融联合通过 10/15、严重误差为零。完整模式降至 4/15。第 215 帧两者分别停在 (1566,2708) 和 (1520,2730)；第 248 帧分别停在 (1634,2723) 和 (1505,2728)，完整模式误差达 124.95 px。完整模式两帧都从下唇缘附近起追，有 13 个根部证据像素，未发布下游峰、差分桥接或灰度续接。直接观察到的是同根附近路径的远端候选未获得最终采用；仅依据这两组消融无法区分重新配准、静态排除和切向规则各自的贡献。',
      '验证组C早期 1、7、38、54 帧现在均有端点。1、7 帧命中，38、54 帧分别短估约 18、29 px。V5.8 r07 的 5 个严重错接帧（345、363、456、469、480）在亮区点位下全部联合通过。第 510 帧仍向右越过尖端约 16 px。开发组A第 299 帧消融误差约 0.44 px，完整模式经原图末段续接为 5.25 px；第 398 帧误差 12.10 px。',
      '各组仅吸附的标注帧联合通过分别为 18/19、10/15、18/20，共 46/54。这个预先设置的消融保留了 S1 的参考处理，在三点弯尤其有优势。后续最值得用开发组和合成的双唇缘样例，分别替换配准、远峰检索和切向限制，定位哪一步失去远端路径。各验证组继续沿用冻结后比较的规则。',
      '三组图像都沿用同一套阈值。验证组C用户指定的材料窗口是采集输入，不能从本次结果推出无窗口、未知倍率或其他试件也能达到相同精度。未经标注的帧只验证了输出连续性和覆盖情况。',
      link('所有失败帧与分支曲线',EVIDENCE/'FAILURES_AUDIT.md'),
      '## 同步基准点敏感性',
      f'在同一帧上改变参考和当前点，然后重新进行顶点定位、配准和路径检测。轴向及法向分别测试 ±10/±20 px，点距缩放 ±20%。开发组A及验证组C各 200 次扰动；另有 16 种合成场景各 10 次。试验以相同采集视野为条件，点位变化会改变粗定位输入。验证组C亮区会把不可行的请求投影到合法点，修正列统计超出像素取整上限 0.70711 px 的次数。验证组C有效成对尖端的最大漂移 {num(w["drift"] if w else None)} px。中位及最大漂移只统计前后均有端点的情况，另列状态变化。',
      table(['组','方向','幅度','扰动数','成对尖端','中位 px','最大 px','联合改变','有无端点改变','位置修正'],js),link('全部扰动明细',OUT/'jitter_all.csv')+' · '+link('验证组C请求点与实际点',OUT/'group_c_jitter.csv'),
      f'开发组A另从完整原始图像重建粗 ROI，重新计算全部 20 个名义位置和 200 次扰动。20 个名义预测的整条折线逐点复现正式输出。{len(native_d)} 次扰动有成对端点，最大漂移 {max(native_d):.2f} px，联合命中变化 {sum(r["joint"]!=r["base_joint"] for r in native)} 次。'+link('整图重新裁剪的点位测试',OUT/'group_a_native_jitter.csv'),
      f'验证组C 562 帧另做原点位与亮区点位全序列配对。两者有 {sum(a["original_tip"]!=a["bright_tip"] for a in cp)} 帧端点不同，{sum(not a["path_equal"] for a in cp)} 帧整条路径不同，有无尖端状态改变 {sum(a["valid_changed"] for a in cp)} 帧。第 494 帧原点位 (2506,2345)、亮区点位 (2502,2345)，相差 4 px，超过 2 px。该帧没有人工尖端，无法据此判定哪种点位更准。20 个标注帧的 200 次受限扰动最大漂移为 0 px，不能据此承诺全序列任意换点都在 2 px 内。'+link('原点与亮区点逐帧配对',OUT/'placement_comparison.csv'),
      '验证组C名义点位在参考图和当前图共 2,248 个 9×9 邻域通过亮度复核。'+link('原点、实际亮区点及逐点亮度',OUT/'bright_anchor_audit.csv'),
      '## 合成矩阵',
      f'共 {len(probes)} 例，阴性误报 {sum(r["valid"]=="True" for r in negative)}/{len(negative)}。每种倍率与曝光均覆盖两档噪声及两个种子。严格通过沿用各探针自己的判据；阳性联合要求归一化尖端误差 ≤10 px、2.5 px 路径容差下覆盖和精确率均 ≥80%。',
      table(['倍率','曝光','样本','严格通过','误报/阴性','联合/阳性'],probes_table),table(['重点探针','样本','严格通过','误报/阴性','联合/阳性'],focus),link('完整逐例数据',OUT/'paired_probes.csv'),
      '合成中的渐隐裂纹 P2_fade 和变形划痕 P6_deformed_scratch 各有 12 个严格失败，缺口多分支竞争 mouth_blob_competing 有 29 个严格失败。零阴性误报和弱带通过率不能替代多入口下路径归属的检验。',
      '## 双模式与消融对照',
      '原点位历史各版及 S1 读取同帧历史封存记录，沿用当时输入范围和计时。验证组C亮区的各历史算法以同一材料窗口和亮区点位实跑 20 张标注图；V5.8 行这里使用 r05 检测器。仅顶点吸附在 S1 的登记参考和路径规则上换用 V5.9 的几何准备，最终版本再加入多尺度差分、边界与切向限制、灰度续接。raw_only 共享参考定义的搜索几何，路径识别仅使用当前灰度。V5.9 FPS 取整组单帧推理时间均值的倒数，验证组C计入亮区几何准备；排除读盘、人工比较、图像渲染与编码。历史与现版计时负载及计时帧数见表。',
      *[table(hdr,[r for r in comparison if r[0]==nm]) for nm in NAMES.values()],
      '## 指定帧与图像交付',
      table(['组','点位','帧','仅吸附误差 px','最终误差 px','发布端点','实际弧长 px','终止或延伸'],special),
      '全序列保留当前灰度、参考图对应位置、路径与尖端、配准有符号差分和局部放大。弧长沿实际起追点至最终尖端逐段求和；投影长度沿点对右法向，以本帧实际中点为零点。无端点留空。验证组C视频展示亮区点位，原点位逐帧数值及失败图另存。',
      table(['组','点位','全序列','有实际弧长','无有效端点'],[[NAMES[g],pl,GROUPS[g],sum(bool(r['path_length_px']) for r in all_lengths if (r['group'],r['placement'],r['mode'])==(g,pl,'full')),sum(not r['path_length_px'] for r in all_lengths if (r['group'],r['placement'],r['mode'])==(g,pl,'full'))] for g in GROUPS for pl in full[g][1]['placements']]),
      table(['组','视频中的点位','视频','长度','标注对照'],media),link('三组逐帧图册及独立差分图',OUT/'difference_views/index.html')+' · '+link('所有长度',OUT/'crack_lengths.csv')]
    save_text(EVIDENCE/'REPORT.md',report)
    save(EVIDENCE/'latest_metrics.json',clean(dict(freeze=sha(OUT/'freeze.json'),primary=primary,jitter_overall=[r for r in js if r[1]=='全部'],synthetic=pstats(probes),failures=len(fails))))


if __name__=='__main__':main()
