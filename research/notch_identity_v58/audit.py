"""Join sealed outcomes with nominal runs and verify every reported bridge."""
import json
import numpy as np
from collections import Counter
from statistics import mean
from research.notch_identity_v42.reporting import read_csv,table,NAMES,num
from . import batch as b


def jitter_results():
    pred=b.OUT/'jitter_predictions.jsonl'
    lock=b.read(b.OUT/'jitter_seal.json')
    assert b.sha(pred)==lock['predictions'] and b.sources()==lock['sources']
    assert b.sha(b.OUT/'jitter_summary.csv')==b.read(b.OUT/'freeze.json')['jitter']
    orig={};variants={}
    for line in pred.open():
        r=json.loads(line)
        key=(r['source'],r['key'])
        if r['delta']==0:orig[key]=r
        variants[key,r['direction'],r['delta']]=r
    rows=read_csv(b.OUT/'jitter_rows.csv')
    for line in (b.OUT/'group_a.jsonl').open():
        f=json.loads(line);k=('group_a',f['frame'])
        if k in orig:assert orig[k]['points']==f['models']['v5_8']['full']['points'],k
    stats=read_csv(b.OUT/'jitter_summary.csv')
    output=[];gates={}
    for src in ('group_a','synthetic'):
        grid=[];passes=[]
        for r in stats:
            if r['source']!=src:continue
            selected=[a for a in rows if (a['source'],a['direction'],a['delta'])==(src,r['direction'],r['delta'])]
            flips=sum(a['joint']!=a['base_joint'] for a in selected)
            changed=sum(variants[(src,int(a['key']) if src=='group_a' else a['key']),a['direction'],int(a['delta'])]['points']!=orig[src,int(a['key']) if src=='group_a' else a['key']]['points'] for a in selected)
            length_change=[];projection_change=[]
            for a in selected:
                key=(src,int(a['key']) if src=='group_a' else a['key'])
                current=variants[key,a['direction'],int(a['delta'])]
                nominal=orig[key]
                if current['tip'] and nominal['tip']:
                    def lengths(row):
                        pts=np.asarray(row['points'])
                        arc=np.linalg.norm(np.diff(pts,axis=0),axis=1).sum()
                        pair=np.asarray(row['current_pair'])
                        dx,dy=pair[1]-pair[0]
                        proj=np.dot(pts[-1]-pair.mean(axis=0),[dy,-dx])/np.hypot(dx,dy)
                        return arc,proj
                    dlength=np.abs(np.subtract(lengths(current),lengths(nominal)))
                    length_change.append(dlength[0]);projection_change.append(dlength[1])
            if int(r['delta']):
                passes.append(bool(r['median']) and float(r['median'])<=2 and int(r['joint'])==int(r['base_joint']))
            grid.append([r['direction'],r['delta'],r['paired'],num(r['median']),num(r['maximum']),r['lost'],r['gained'],
                         str(r['joint'])+'/'+r['visible'],flips,changed,num(max(length_change,default=None)),num(max(projection_change,default=None))])
        gates[src]=all(passes)
        output+=['### '+('开发组A' if src=='group_a' else '合成探针'),
                 table(['同步条件','偏移 px 或 %','两次均有尖端','中位漂移 px','最大漂移 px','失去尖端','新增尖端','联合命中','联合状态改变帧','整条折线改变帧','最大弧长变化 px','最大投影变化 px'],grid)]
    return gates,['## 同步基准点扰动','同一试件的参考帧和当前帧接受同一个轴向或法向平移向量。锚距缩放时，两帧各自保持中点固定，同步缩放到 80% 或 120%。每种条件均从原图重新计算粗搜索区域、前缘、图像配准与裂纹路径。20 个开发组A标注帧及 14 类单一倍率、标准曝光的合成样例各运行 11 种条件。合成扰动使用图内锚点，完整合成矩阵另按原版探针协议给出粗起点。未扰动开发组A折线逐点核对正式封存输出。每个条件仅在两次都有尖端时计算漂移，命中以全部可见端点为分母。',*output,
        '[同步坐标及逐条预测](jitter_predictions.jsonl) · [逐例命中与漂移](jitter_rows.csv)']


def bridges():
    grid=[];details=[]
    for g,n in b.GROUPS.items():
        counts=Counter()
        for line in (b.OUT/(g+'.jsonl')).open():
            r=json.loads(line)
            m=r['models']['v5_8']['full'];d=m['diagnostics']['dual']
            for a in d.get('branches',[]):
                br=a['bridge'];chosen=d['pick']=='BRANCH_'+str(a['id'])
                down=br.get('downstream_peak')
                if down:
                    assert down['mean_net']>0 and down['fine_fraction']>=.30
                    counts['valleys']+=1;counts['chosen_valley']+=int(chosen)
                if br.get('accepted'):
                    assert br['mean_net']>0 and br['fine_fraction']>=.30
                    counts['bridges']+=1;counts['chosen_bridge']+=int(chosen)
                    counts['unlocked']+=int(chosen and br['original_net']<=0)
                if g=='three_point_bend' and r['frame'] in (144,178,215,248,407) and chosen:
                    details.append([r['frame'],a['root'],a['base_tip'],a['tip'],str(down or '—'),str({k:v for k,v in br.items() if k!='downstream_peak'})])
        grid.append([NAMES[g],n,*[counts[k] for k in ('valleys','chosen_valley','bridges','chosen_bridge','unlocked')]])
    return ['## 谷底替换与桥接实际触发',table(['实验','帧数','分支通过谷底检验','发布谷底替换','分支通过桥接','发布前向桥接','其中未提权净分≤0'],grid),
            '下表在原图坐标给出根部、原峰、最终端点。判据字典中的 valley_x 和 late_x 是相对缺口前缘的像素列。',table(['三点弯帧','根部','原峰','最终尖端','谷底检验','前向桥接'],details)]


def development_and_speed(metrics):
    dev=[]
    for folder in sorted(b.OUT.parent.glob('v58_valley_bridge_20261120_r*')):
        if not (folder/'group_a_scores.csv').is_file():continue
        results=[r for r in read_csv(folder/'group_a_scores.csv') if r['stage']=='v5_8' and r['mode']=='full']
        probes=read_csv(folder/'paired_probes.csv')
        def passed(case):
            return sum(r['case']==case and r['passed']=='True' for r in probes)
        dev.append([folder.name.rsplit('_',1)[1],sum(r['joint']=='True' for r in results),passed('P1_weak_gap'),passed('P6_isolated'),
                    sum(r['negative']=='True' and r['valid']=='True' for r in probes)])
    speed=[]
    for g,n in b.GROUPS.items():
        old=b.BASE/(g+'.jsonl')
        assert b.sha(old)==b.read(b.BASE/(g+'_seal.json'))['predictions']
        with old.open() as stream:
            old_fps=1/mean(json.loads(line)['models']['v5_7']['seconds'] for line in stream)
        now=next(r for r in metrics if r['stage']=='v5_8' and r['group']==g and r['mode']=='full')
        speed.append([NAMES[g],n,num(old_fps),num(now['fps']),num(now['ms']),num(now['fps']/old_fps)])
    return ['## 开发组回归与全序列速度',
        'r01 采用整数纹理平移和短计算窗。r02 保留较长背景窗，恢复弱带覆盖。r03 用两侧材料纹理的亚像素位移配准，放宽静态暗线连续性后独立划痕出现退化。r04 恢复严格参考暗线排除，对全路共享前缀的晚峰继续检查。各轮均仅使用合成与开发组A，完整验证只运行 r04。',
        table(['轮次','开发组A联合 /19','弱带严格通过 /216','独立划痕通过 /36','阴性误报 /432'],dev),
        '两版均按各自全序列已记录推理时间计算，历史基线与本轮的并发进程数分别为 6 和 3。下表反映本次运行的实测帧率；两版并非同负载下的单算子基准测试。',
        table(['组','全序列帧数','V5.7 FPS','V5.8 FPS','V5.8 ms','帧率比'],speed)]
