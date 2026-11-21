"""Post-seal geometry, candidate acceptance and focal-frame diagnostics."""
import json
from collections import Counter
from pathlib import Path
from math import hypot
import numpy as np
from research.notch_identity_v42.reporting import NAMES, table, read_csv
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b


def geometry_and_bridges():
    rows=[]
    summary=[]
    parity=[]
    bridge_counts=[]
    timings=[]
    for group,n in b.GROUPS.items():
        dfile=b.OUT/(group+'.jsonl')
        assert b.sha(dfile)==b.read(b.OUT/(group+'_seal.json'))['predictions']
        baseline_file=b.BASE/(group+'.jsonl')
        assert b.sha(baseline_file)==b.read(b.BASE/(group+'_seal.json'))['predictions']
        with baseline_file.open(encoding='utf8') as stream:
            old=[json.loads(r)['models']['v5_4'] for r in stream]
        baseline=[r['full']['diagnostics']['dual'] for r in old]
        elapsed=[]
        counts=Counter()
        assert len(baseline)==n
        for line in dfile.open(encoding='utf-8'):
            rec=json.loads(line)
            elapsed.append(rec['models']['v5_7']['seconds'])
            meta=b.read(b.OLD/'evidence'/group/str(rec['frame'])/'metadata.json')
            points=meta['current_points'] if meta['evidence']['scene']['points_observed'] else []
            for mode in ('full','raw_only'):
                model=rec['models']['v5_7'][mode]
                diag=model['diagnostics']['dual']
                front=diag.get('front')
                ybounds=diag.get('roi_y')
                def clearance(pt):
                    x,y=pt
                    return hypot(max(front-x,0),max(ybounds[0]-y,0,y-ybounds[1]))
                distances=[clearance(p) for p in points] if ybounds else []
                h=meta['evidence']['scene']
                hint=np.rint(h['root'] or h['center'])
                radius=max(1,int(round(.23*h['scale'])))
                root_dist=[hypot(max(hint[0]-2*radius-x,0,x-hint[0]-radius),
                                 max(hint[1]-radius-y,0,y-hint[1]-radius)) for x,y in points]
                prev=baseline[rec['frame']-1]
                def registration_key(d):
                    reg=d.get('registration') or {}
                    return [reg.get('status'),reg.get('shift')]
                pts=model['points']
                if pts:
                    arr=np.asarray(pts)
                    assert arr[:,0].min()>=front and ybounds[0]<=arr[:,1].min()<=arr[:,1].max()<=ybounds[1]
                branches=diag.get('branches',[])
                chosen=next((a for a in branches if diag['pick']=='BRANCH_'+str(a['id'])),{})
                for branch in branches:
                    assert front<=branch['root'][0]<front+diag['seed_band']
                    br=branch['bridge']
                    if mode=='full':
                        if 'witness' not in br:key='未进入'
                        elif br['witness']<2:key='近根部证据不足'
                        elif 'columns' not in br:key='没有可验收的尾段'
                        elif br.get('accepted'):key='通过'
                        elif br['original_net']<=0:key='原场净分不足'
                        else:key='其余拒绝'
                        counts[key]+=1
                    if br.get('accepted'):
                        assert br['fine_fraction']>=.30 and min(br['mean_net'],br['original_net'])>0
                    down=br.get('downstream_peak')
                    if down:
                        assert down['fine_fraction']>=.30 and down['mean_net']>0
                bridge=chosen.get('bridge',{})
                rows.append(dict(group=group,frame=rec['frame'],mode=mode,front=front,
                    roi_y=ybounds,root_patch_margin=min(root_dist) if root_dist else None,
                    front_parity=(prev.get('front')==front) if mode=='full' else None,
                    registration_parity=(registration_key(prev)==registration_key(diag)) if mode=='full' else None,
                    p1_clearance=distances[0] if distances else None,
                    p2_clearance=distances[1] if distances else None,branches=len(branches),
                    endpoint=model['tip'],pick=diag['pick'],stop=diag['stop'],
                    selected_bridge=bool(bridge.get('accepted')),selected_peak=bool(bridge.get('downstream_peak'))))
        rr=[r for r in rows if r['group']==group and r['mode']=='full']
        vals=[min(r['p1_clearance'],r['p2_clearance']) for r in rr if r['p1_clearance'] is not None]
        early=[r['root_patch_margin'] for r in rr if r['root_patch_margin'] is not None]
        bridge_counts.append([NAMES[group]]+[counts[k] for k in ('未进入','近根部证据不足','没有可验收的尾段','原场净分不足','其余拒绝','通过')])
        timings.append([NAMES[group],n,round(n/sum(r['seconds'] for r in old),2),round(n/sum(elapsed),2)])
        parity.append([NAMES[group],sum(r['front_parity'] for r in rr),sum(r['registration_parity'] for r in rr),n,
                       round(min(early),2) if early else '—'])
        summary.append([NAMES[group],len(rr),len(vals),round(min(vals),2) if vals else '—',
            sum(x==0 for x in vals),sum(r['branches']>=2 for r in rr),
            sum(r['selected_peak'] for r in rr),sum(r['selected_bridge'] for r in rr)])
    write_csv(b.OUT/'geometry_bridge_audit.csv',rows)
    return ['## 前缘边界与实际分支选择','在冻结结果的 full 和 raw_only 两种模式下，逐点检查已发布路径和所有分支根部的边界，逐次核查被允许延伸的细脊占比及两类净分。对有实测 P1/P2 和有效搜索窗的帧，计算每个标记中心到右侧可搜索走廊的最短距离。此距离按点中心计算，实体标记的外轮廓没有人工分割。',
        table(['组','全帧','有实测点与前缘','两中心最小间隔 px','中心落入走廊的帧','多入口产生路径','选用下游峰','选用前向桥接'],summary),
        '另外对照 V5.4 封存输出，核对实际前缘 x 及前向配准状态、平移是否逐帧一致。两版采用同一份原始参考几何预对齐输入。最后一列给出实测标记中心与 V5.4 前缘定位小窗的最近距离。',
        table(['组','前缘相同','配准相同','全帧','标记中心至定位小窗最小距离 px'],parity),
        '逐分支统计桥接退出环节。没有可验收的尾段包含剩余图像不足或新的正向路径短于验收下限。原场净分不足包含可能同时违反其他规则的候选。',
        table(['组','未进入','近根部证据不足','无可验收尾段','原场净分不足','其余拒绝','通过'],bridge_counts),
        '下表使用两版各自整组全部帧的计时，每次计入新算法的准备和检测。速度目标下限为 4 FPS。',
        table(['组','相同帧数','V5.4 FPS','V5.7 FPS'],timings),
        '[逐帧边界与延伸检查](geometry_bridge_audit.csv)']


def development_results():
    lines=[]
    for folder in sorted(b.OUT.parent.glob('v57_clean_20261120_r*')):
        if not (folder/'group_a_scores.csv').is_file():
            continue
        rows=[r for r in read_csv(folder/'group_a_scores.csv') if r['stage']=='v5_7' and r['mode']=='full']
        probes=read_csv(folder/'paired_probes.csv')
        def passed(case):
            return sum(r['case']==case and r['passed']=='True' for r in probes)
        lines.append([folder.name.rsplit('_',1)[-1],sum(r['joint']=='True' for r in rows),
             passed('P1_weak_gap'),passed('P6_isolated'),passed('P6_deformed_scratch'),
             passed('mouth_blob_competing'),sum(r['valid']=='True' and r['negative']=='True' for r in probes)])
    return ['## 冻结前的开发记录',
        '首版在独立划痕探针上把发生位移的既有暗线误接到尖端。随后用已配准参考图排除已有强暗线，同时检查未提权场的新增段净分。最终版增加每个入口前驱表内的局部峰竞争，沿用相同的延伸验收条件。以下数据均来自合成与开发组A。',
        table(['轮次','开发组A联合 /19','弱带 /216','独立划痕 /36','形变划痕 /36','竞争唇缘端点 /36','阴性误报 /432'],lines)]
