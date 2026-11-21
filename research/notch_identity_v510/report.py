"""Generate the report from sealed predictions, per-frame scores and rendered evidence."""
from collections import Counter, defaultdict
from pathlib import Path
import json
import math
import os
import statistics

import numpy as np
from research.notch_identity_v59.report import summary, table, num, NAMES
from research.v3_labelme_comparison.compare import write_csv
from .batch import ROOT, OUT, BASELINE, GROUPS, read_csv, read, sha, save, sources

DOC = ROOT/'evidence/v5_10'
PREV = OUT.parent/'v59_converged_r04'
VERSIONS = dict(v3_6='V3.6',v4_2='V4.2',v5_4='V5.4',apex_only='V5.9 仅顶点吸附',red_priority='V5.10-S1 红脊择优',v5_10='V5.10 完整')
SPECIAL = dict(group_a=[1,299,398],three_point_bend=[144,178,215,248,306,335,407,413,435,503],group_c=[1,7,38,54,221,324,456,510])
def link(name,path):
    return f'[{name}]({Path(os.path.relpath(path,DOC)).as_posix()})'

def group_rows(group):
    return list(map(json.loads,(OUT/(group+'.jsonl')).read_text('utf8').splitlines()))

def branch_text(dual):
    valid=[b for b in dual['branches'] if b['reason']=='VALID']
    winner=next((b for b in valid if dual['pick']==f"BRANCH_{b['id']}"),{})
    br=winner.get('bridge',{})
    return valid,winner,br

def native_stats(group):
    allrows=read_csv(OUT/(group+'_native_jitter.csv'))
    rows=[r for r in allrows if int(r['delta'])]
    valid=[r for r in rows if r['drift']]
    worst=max(valid,key=lambda r:float(r['drift']),default={})
    return [NAMES[group],len(rows),len(valid),sum(float(r['drift'])>0 for r in valid),sum(r['status_change']=='True' for r in rows),
            num(worst.get('drift')),f"{worst.get('frame')} / {worst.get('direction')} {worst.get('delta')}"]

def main():
    DOC.mkdir(exist_ok=True,parents=True)
    lock=read(OUT/'freeze.json')
    assert lock['sources']==sources()
    hist=read_csv(BASELINE/'ablation.csv')
    full={};scores={};lengths=[];metrics=[];cases=[];activity=[];placement_stats=[]
    comparisons=[];ablation=[];jitter=[];native=[];s1_equal=0
    for g,n in GROUPS.items():
        seal=read(OUT/(g+'_seal.json'));stream=OUT/(g+'.jsonl')
        assert seal['sources']==lock['sources'] and sha(stream)==seal['predictions']
        records=group_rows(g);assert [r['frame'] for r in records]==list(range(1,n+1))
        full[g]={r['frame']:r for r in records}
        prev_records={r['frame']:r for r in map(json.loads,(PREV/(g+'.jsonl')).open())}
        old_scores=read_csv(PREV/(g+'_scores.csv'));lengths+=read_csv(OUT/(g+'_lengths.csv'))
        data=read_csv(OUT/(g+'_scores.csv'))
        scores[g]={(r['placement'],r['stage'],r['mode'],int(r['frame'])):r for r in data}
        for place in records[0]['placements']:
            caption=NAMES[g]+(' 原点' if place=='original' and g=='group_c' else ' 亮区' if place=='bright' else '')
            for mode,timer in [('full','seconds'),('raw_only','raw_seconds')]:
                for ver,label in VERSIONS.items():
                    rows=[r for r in data if (r['placement'],r['stage'],r['mode'])==(place,ver,mode)]
                    if not rows:
                        rows=[r for r in old_scores if (r['placement'],r['stage'],r['mode'])==(place,ver,mode)]
                    if rows:
                        stat=summary(rows);timed=len(rows);sec=sum(float(r['seconds']) for r in rows)
                        if ver=='v5_10':
                            timed=n;sec=sum(r['placements'][place][ver][timer] for r in records)
                        fps=timed/sec
                    else:
                        h=next(a for a in hist if (a['group'],a['stage'],a['mode'])==(g,ver,mode))
                        assert place=='original'
                        stat=[int(h[k]) for k in ('visible','valid','hit5','hit','joint','severe')]+[num(h['median']),num(h['max'])]
                        timed=int(h['timed']);fps=float(h['fps'])
                    comparisons.append([caption,label,mode,*stat,num(fps),timed])
                    if mode=='full' and ver=='v5_10':
                        metrics.append(dict(group=g,placement=place,frames=n,visible=stat[0],hit5=stat[2],hit10=stat[3],joint=stat[4],severe=stat[5],median=stat[6],max_error=stat[7],fps=round(fps,2)))
                    if mode=='full' and ver in ('apex_only','red_priority','v5_10'):
                        ablation.append([caption,label,stat[3],stat[4],stat[5],stat[6],stat[7]])
            for i in SPECIAL[g]:
                k=scores[g]
                rr=[k[place,v,'full',i] for v in ('apex_only','red_priority','v5_10')]
                m=records[i-1]['placements'][place]['v5_10']['full'];d=m['diagnostics']['dual'];valid,win,br=branch_text(d)
                cases.append([caption,i,*[num(a['error_px']) for a in rr],m['tip'] or m['status'],num(m['path_length_px']),len(valid),('是' if d.get('priority_applied') else '否'),br.get('reason') or d['stop'],rr[-1]['joint'] or '无尖端标注'])
            picked=[r for r in records if 'apex_only' in r['placements'][place]]
            for r in picked:
                for mode in ('full','raw_only'):
                    a=r['placements'][place]['apex_only'][mode];b=prev_records[r['frame']]['placements'][place]['apex_only'][mode]
                    assert (a['status'],a['points'],a['tip'])==(b['status'],b['points'],b['tip'])
                    s1_equal+=1
            priority=flips=bridges=multi=0;spans=[]
            for r in records:
                d=r['placements'][place]['v5_10']['full']['diagnostics']['dual'];valid,win,br=branch_text(d)
                multi+=int(len(valid)>1);priority+=int(d.get('priority_applied',False))
                if d.get('priority_applied'):flips+=int(max(valid,key=lambda b:b['original_merit'])['id']!=win['id'])
                if br.get('accepted'):
                    bridges+=1;spans.append(br['columns']);assert br['columns']>=15
            activity.append([caption,n,multi,priority,flips,bridges,f"{min(spans)}–{max(spans)}" if spans else '—'])
        if g=='group_c':
            dist=[];changed=0;states=0
            for r in records:
                orig,bright=[r['placements'][p]['v5_10']['full'] for p in ('original','bright')]
                states+=int(orig['status']!=bright['status'])
                if orig['tip'] and bright['tip']:
                    drift=math.dist(orig['tip'],bright['tip']);dist.append((drift,r['frame']));changed+=int(drift>0)
            placement_stats=[changed,states,max(dist)]
        sweep=OUT/(g+'_jitter.csv')
        if sweep.exists():
            j=read_csv(sweep);v=[float(r['drift']) for r in j if r['drift']]
            jitter.append([NAMES[g],len(j),len(v),num(max(v)),sum(r['joint']!=r['baseline_joint'] for r in j),num(max(float(r['correction']) for r in j))])
        native.append(native_stats(g))
    write_csv(OUT/'crack_lengths.csv',lengths)
    neg=read_csv(OUT/'paired_probes.csv');ct=defaultdict(list)
    for r in neg:ct[r['case']].append(r)
    matrix=[[c,len(rows),sum(r['passed']=='True' for r in rows),sum(r['valid']=='True' for r in rows),sum(r['priority']=='True' for r in rows),sum(r['published_bridge']=='True' for r in rows)] for c,rows in sorted(ct.items())]
    synth=read(OUT/'synthetic_jitter.json');nom={r['key']:r for r in synth if not r['delta']}
    pairs=[(r,nom[r['key']]) for r in synth if r['delta']]
    drifts=[math.dist(r['tip'],q['tip']) for r,q in pairs if r['tip'] and q['tip']]
    syn_switch=sum(bool(r['tip'])!=bool(q['tip']) for r,q in pairs)
    total=sum(r['joint'] for r in metrics if r['placement']=='original')
    save(DOC/'latest_metrics.json',dict(run=OUT.name,full=metrics,joint_unique=total,replicated_s1=s1_equal,freeze=sha(OUT/'freeze.json')))
    header=['组别','版本','模式','可见','有尖端','Hit@5','Hit@10','Joint','严重','中位 px','最大 px','FPS','计时帧数']
    body=[
        '# V5.10 红脊分支优先与无过冲桥接验证报告',
        f"冻结运行 `{OUT.name}`。三组 full 联合命中 **{total}/54**，验证组C两种点位只计一次。复核了 {s1_equal} 份本轮与 V5.9 r04 的基座预测，逐点路径、端点和状态全部相同。",
        table(['组别','点位','序列帧','Hit@5','Hit@10','Joint','严重','中位 px','最大 px','FPS'],[[NAMES[r['group']],r['placement'],r['frames'],r['hit5'],f"{r['hit10']}/{r['visible']}",f"{r['joint']}/{r['visible']}",r['severe'],r['median'],r['max_error'],r['fps']] for r in metrics]),
        '## 数据和计分',
        '仅开发组A和合成图参与开发。合成双分支在 r01 的连续活跃规则触发 0/36，r02 允许较短的独立连续支撑后触发 23/36；两轮均保留开发预测。冻结后依次运行三点弯、验证组C原点与亮区。排除组X排除。LabelMe 仅在预测封存后读取作比较。验证组在项目往轮已被评测，当前数据支持同协议的跨组回归，独立新材料泛化能力仍待检验。',
        '共 60 个标注帧，其中 54 帧有可见尖端。Hit@5/10 为原图像素欧氏误差门槛。Joint 还要求路径覆盖率与精确率均 ≥80%（10 px 邻域）。严重为有预测且误差 >100 px。无预测计入可见分母；中位与最大误差仅取有定位结果的帧。长度为预测根点到尖端的折线弧长，单位 px，另存相对点对中点的轴向投影。无路径时长度空缺。',
        '## 两项改动与消融',
        '从固定参考材料带吸附缺口顶点。沿用 S1 累计 DP 峰与谷底后的远峰搜索。择优只作用于合格的不同入口候选。初分 B = 累计峰值 + 0.65 × 细脊列数 + 0.70 × 同时有暗谷和细脊的列数。去掉与其他路径同列相距 ≤2 px 的共有部分，再剔除参考静态暗线与偶极。以 T=max(1,2.7×噪声,0.030×灰度跨度) 计算正差，L 为通过形态门槛且 D>T 的独有列数，G=Σclip(D/T−1,0,3)。L≥4、最长连续段≥3、G≥6 且独有列平均差为正定义为活跃；有独有列且满足 L≤2、均值≤0 两者之一时定义为不活跃。在两类同时出现时活跃分加 2L+0.65G，不活跃分乘 0.35。其他情形沿用 B，保留无新增时的原图预存分支判据。',
        'V5.10-S1 保留原基座桥接，仅改变分支排序。完整版本替换桥接器，入口附近须至少两列同时有细脊和原图暗谷，限在材料带内侧 max(3, round(0.035×尺度)) px。延伸至少 15 列、细脊占比 ≥30% 且至少连续 6 列。原累计场在谷底后至少隔 4 列上升 ≥2，最近三列均值 >0.08，峰后还须有三列更弱证据，桥接平均净收益须为正。沿用 S1 无切向走廊的远峰，取消灰度尾段续接。',
        table(['组别','阶段','Hit@10','Joint','严重','中位 px','最大 px'],ablation),
        '## 跨版本比较',
        '当前 full 和 raw_only 的 FPS 按全序列单次推理耗时求和，含缺口几何和验证组C亮区选择，输入为已缓存的原图 ROI 与上游参考配准结果。视频帧率为 10，仅用于回看。历史算法与本轮消融在表末列给出实际计时样本数，机器负载与历史运行环境可影响横向速度比较。',
        table(header,comparisons),
        '## 分支机会与桥接实际使用',
        table(['组别','全序列','多合格候选','触发红脊择优','更换初选分支','发布中段桥接','跨度 px'],activity),
        '## 关键帧',
        table(['组别','帧','基座误差','加红脊误差','完整误差','完整尖端','弧长 px','合格分支','重加权','桥接判据或停止原因','Joint'],cases),
        'SHORT_RIDGE 表示返回的正累计收益最优延伸短于长度门槛，NO_INDEPENDENT_RISE 表示提出的延伸未同时通过独立峰、支撑与收益检查。NO_ATTACHED_SUPPORT 表示根部联合支撑不足。预存模式只按原图判断。各失败帧的候选端点、分支得分及原图见专项分析。',
        '## 同步基准点敏感性',
        '扰动同时施加于当前图与参考图。沿点对轴向和法向各平移 ±10、±20 px，另将点距缩放 ±20%。下表保持同帧已配准参考和输入裁框，重新评估检测器。验证组C逐点检查当前和参考的 9×9 亮度窗口，必要时投影回亮区。',
        table(['组别','扰动次数','成对可定位','最大漂移 px','Joint 改变','最大亮区修正 px'],jitter),
        f'验证组C全 562 帧直接交换两种名义点位，{placement_stats[0]} 帧有效尖端变化、{placement_stats[1]} 帧状态变化，最大漂移 {num(placement_stats[2][0])} px。合成图共有 {len(pairs)} 次扰动，{len(drifts)} 次有成对尖端，最大漂移 {num(max(drifts,default=None))} px，状态改变 {syn_switch} 次。',
        '以下补测从两张原始 BMP 开始，重新生成当前裁框和参考配准场。验证组C按亮区材料框及实际允许的点位重新配准，名义基线也在同一流程重算。最大漂移相对于各自名义点位。此测试包含了采样窗口及上游配准变化，可以检验更换基准点时实际会看到的漂移。',
        table(['组别','扰动次数','成对可定位','成对尖端变化','状态变化','最大漂移 px','最大值帧/方向/幅度'],native),
        '开发组A第 299 帧沿轴正移 10 或 20 px 后，尖端误差从 0.44 增至 18.01 px。三点弯的 93.38 px 发生在无可见尖端标注的第 84 帧，表示输出不稳定；仅看可见标注帧，最大漂移为 3.00 px，第 381 帧有两种扰动使误差从 8.18 增至 11.18 px。验证组C亮区直接参与上游重配准时，名义尖端与主实验复用配准场的结果最多相差 14.04 px（第 54 帧）；此补测内部再扰动最大为 4.00 px。',
        '## 合成探针',
        '同一物理构型的亮度、尺度、噪声或入口上下镜像属于相关变体。阴性 0/468，P1_weak_gap 216/216。新双分支各 36 个变体中，30 个定位通过。6 个失误均在 0.5 倍尺度、低噪声时，与基座给出相同端点，归一化误差略超 10 px。重加权可以改变入口优先级，但候选在下游汇合时仍可能给出相同尖端。weak_material_bridge 0/36，限制桥接以保护尾端同时会漏掉部分弱连接。',
        table(['探针','样本数','通过','发布尖端','触发择优','发布新桥接'],matrix),
        '## 逐帧交付',
        ' · '.join([link('三组逐帧图册、视频与对应差分',OUT/'difference_views/index.html'),link('所有帧两种模式的长度表',OUT/'crack_lengths.csv'),link('失败帧与分支评分曲线',DOC/'FAILURES_AUDIT.md'),link('合成逐例 CSV',OUT/'paired_probes.csv'),link('冻结清单',OUT/'freeze.json'),link('推理源码',ROOT/'research/notch_identity_v510/terminal.py')]),
    ]
    return body,full,scores,metrics


def finish():
    report,full,scores,metrics=main()
    indexed=read_csv(OUT/'failure_index.csv');cards=[]
    report.insert(3,'**验收结论**　开发组A满足精度、首帧和第 299 帧要求；三点弯保住 10/15，第 215 帧未修复，全序列 2.53 FPS 低于 4 FPS；验证组C两种点位均 18/20，未达到 19/20。同步扰动在固定配准输入下通过，重跑原图预处理后未达到 0 px。保留 V5.9 仅顶点吸附作为当前精度基线。')
    expected={(g,p,m,i) for g,rs in scores.items() for (p,stage,m,i),r in rs.items() if stage=='v5_10' and r['state']=='VISIBLE' and (r['hit10']!='True' or r['joint']!='True')}
    assert expected=={(r['group'],r['placement'],r['mode'],int(r['frame'])) for r in indexed}
    failures=[
        '# V5.10 失败与退化帧专项分析',
        f'共 {len(expected)} 条可见帧失败记录，含两种模式及验证组C两种点位。三组主结果 full 去除重复点位后，失败为开发组A 398，三点弯 144、178、215、407、503，验证组C 38、54。其余无明确人工尖端的帧单列在逐帧计分中。四栏图从左至右为固定参考、当前图、识别及人工路径叠图、有符号差分。每个曲线图画出各入口在每个横坐标上的最大累计 DP 得分，峰值纵坐标可能来自不同路径。',
        '## 三帧的失败环节',
        '验证组C 38 的低位暗线在固定参考中已存在，当前图上方有新增红色弯线。最终唯一合格候选停在 (2273, 2339)，距标注 18.15 px。另一路累计分不足。验证组C 54 仍只有一路合格，其他入口分别因总分不足及缺口死端被拒绝。预测路径起段先走下侧旧线，后折向上方新线，但仍提前约 12.5 px。两帧均在排序前失去独立的新分支；继续放大红脊排序权重无法改变此次输出。',
        '三点弯 215 仅下入口合格，S1 谷后峰到达 (1566, 2708)，保住了相邻第 248 帧的远峰。第 215 帧的中段桥接搜索未找到正累计净收益的延伸，停止于原端点，横向少追 39.0 px、纵向少追 10.6 px。下表为独立的事后检查：从预测端点后一列沿人工折线直到标注路径最后一列，在上下各 2 px 的窗口计数。窗口里有红色像素，仍可能缺少由预测端点出发、连续且净得分为正的同一条轨迹。三点弯最后两列人工尖端与路径的横坐标略有差别，故实际扫描 37 列。',
        table(['组别','帧','原图 x 范围','列数','D>T','形态细脊','剔除静态与偶极后','最长连续','原图暗谷'],[[NAMES[r['group']],r['frame'],r['from_x']+'–'+r['to_x'],r['columns'],r['positive'],r['fine'],r['filtered_red'],r['longest'],r['raw_dark']] for r in read_csv(OUT/'posthoc_path_evidence.csv')]),
        '三点弯 306、413、435 的最终误差依次为 2.49、6.43、5.49 px，均未发布短延伸。503 的两个有效候选已经汇合在 (1801, 2725)，基座即已超过人工尖端，完整版本维持 14.91 px。开发组A 398 的初始峰与发布尖端同为 (1337, 1164)，预测越过标注 11.85 px，路径整体仍能覆盖标注。两者的误差都发生在初始峰选择环节。',
        '## 每条失败记录',
    ]
    for row in indexed:
        g,p,m,i=row['group'],row['placement'],row['mode'],int(row['frame'])
        pred=full[g][i]['placements'][p]['v5_10'][m]
        d=pred['diagnostics']['dual'];valid,w,b=branch_text(d)
        score=scores[g][p,'v5_10',m,i];gt=json.loads(score['gt']);other=scores[g][p,'apex_only',m,i]
        candidates='；'.join(f"{z['id']}→{z['tip']}，{z['reason']}，{num(z['merit'])}" for z in d['branches']) or '无'
        oracle=min((math.dist(z['tip'],gt) for z in valid),default=None)
        if not valid:reason='全部入口止于门槛，未发布尖端。'
        elif oracle>10:reason='所有合格分支端点均在 10 px 外。'
        elif score['hit10']=='False':reason='存在 10 px 内的合格端点，排序选择失误。'
        else:reason='尖端已达 10 px 门槛，路径覆盖率或精确率不足。'
        surf=OUT/'surfaces'/g/p/f'{i:04d}_{m}.npz'
        with np.load(surf) as z:
            xgt=round(gt[0])-int(z['origin'][0]);cv=[]
            for k,c in zip(z['branch_ids'],z['curves']):
                ok=c[np.isfinite(c)&(c>-1e8)]
                v=c[xgt] if 0<=xgt<len(c) else -np.inf
                cv.append(f"{k}：{num(max(ok,default=None))} / {num(v) if np.isfinite(v) and v>-1e8 else '不可达'}")
        failures+= [f"### {NAMES[g]} {i} · {p} · {m}",
            f"尖端误差 {num(score['error_px'])} px，S1 基座 {num(other['error_px'])} px。路径覆盖率 {num(score['coverage'])}，精确率 {num(score['precision'])}。{row['cause']} {reason} 最接近标注的合格端点误差 {num(oracle)} px。",
            f"分支编号、端点、门控与择优分依次为 {candidates}。各分支曲线的全局峰值 / 人工尖端所在列最大值为 {'；'.join(cv) or '无'}。桥接诊断 {b.get('reason') or '无差分桥接'}。",
            link('四栏图',row['card'])+' · '+link('分支累计得分曲线',row['curve'])]
    failures+=['## 下一轮可验证的假设',
            '在合成图或开发组A中构造同一入口内部分叉，并检查截断前能否同时生成两个不同端点。对弱中段记录从当前峰到下游峰的可达曲面、掩膜断点和累计分首次转负的位置。用已有短尾与材料边界阴性探针同时回归，保留当前验证组作冻结后的测评。']
    (DOC/'FAILURES_AUDIT.md').write_text('\n\n'.join(failures)+'\n','utf8')
    report.insert(report.index('## 关键帧'),'验证组C 38/54 各仅有一个合格候选；三点弯 215 从预测端点往后 37 列均有正差，经过静态与偶极抑制后有 16 列具备合格红脊，最长连续 11 列。局部红脊在图像中可见，前向 DP 仍停于基座峰。'+link('查看标注路径采样与分支曲线',DOC/'FAILURES_AUDIT.md'))
    report.extend(['按组核查原始记录',*[' · '.join([NAMES[g],link('逐帧评分',OUT/(g+'_scores.csv')),link('全链路扰动',OUT/(g+'_native_jitter.csv')),link('视频',OUT/'difference_views'/(g+'.mp4'))]) for g in GROUPS]])
    (DOC/'REPORT.md').write_text('\n\n'.join(report)+'\n','utf8')

if __name__=='__main__':finish()
