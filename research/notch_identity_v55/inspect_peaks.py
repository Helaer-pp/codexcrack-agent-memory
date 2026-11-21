"""Reconstruct exact valley scores for spatial peaks on the sealed validation images."""
import json
import math
import cv2
import numpy as np
from . import batch as b, terminal as t
from research.notch_identity_v42.reporting import table, num
from research.v3_labelme_comparison.compare import write_csv, evaluate, PACKAGE
from research.v3_labelme_comparison.infer import read_csv

def inspect_focus(scores,records):
    group='three_point_bend'
    summary=[]
    every=[]
    alternatives=[]
    gate_rows=[]
    links=[]
    bridge_audit=[]
    column_audit=[]
    labels={int(r["frame_id"]):r for r in read_csv(b.SELECT) if r["dataset_id"]==group}
    for i in (144,178,215):
        folder=b.OLD/'evidence'/group/str(i)
        scene=b.read(folder/'metadata.json')['evidence']['scene']
        off=np.asarray(scene['bounds'][:2])
        hint=np.rint(np.asarray(scene['root'] or scene['center'])-off).astype(int)
        with np.load(folder/'arrays.npz') as z:
            p=t.prepare(z['raw'],hint,scene['scale'])
            fixed=z['fixed__aligned']
            score,seeds,_,reg,source,stats=t.fields(p,fixed)
            old_score,*_=t.prior.fields(p,fixed)
        origin=off+np.asarray(p.origin)+[p.front,0]
        _,maximum,V,back,ds=t.lattice(score,seeds,p.scale,source=='JOINT')
        r=scores[group,i,'v5_5','full']
        gt=json.loads(r['gt'])
        m=records[group,i]['models']['v5_5']['full']
        d=m['diagnostics']['dual']
        assert abs(maximum-d['global_score'])<1e-4
        ap=(V>=cv2.dilate(V,np.ones((3,3),np.uint8)))&(V>0)
        ap[:int(.20*p.scale)+1]=False
        candidates=[]
        ann=b.read(PACKAGE/labels[i]['selected_json'])
        manual=[np.asarray(shape['points']) for shape in ann['shapes'] if shape['label']=='crack_path']
        for x,y in zip(*np.where(ap)):
            tr=t.unwind(back,x,y,ds[x,y])
            e=t.extension_evidence(score,tr,p.scale)
            assert abs(V[x,y]-e['peak_value'])<.003
            why=[]
            if V[x,y]<=.052*p.scale:why.append('累计分低')
            if score[x,y]<=.08:why.append('末列弱')
            if e['tail_length']<t.px(p.scale,.030):why.append('爬升过短')
            if e['valley_gain']<max(1.,.010*p.scale):why.append('总爬升不足')
            if (e['net_mean'] or 0)<=.075:why.append('平均净分低')
            if (e['support'] or 0)<.54:why.append('正支撑不足')
            if e['longest_run']<t.px(p.scale,.012):why.append('连续支撑不足')
            if (e['ending_mean'] or 0)<=.06 or t.increments(score,tr)[-1]<=0:why.append('末窗或末步未上升')
            if t.topology.check(p.local,tr+[p.front,0],p.front,p.scale,True)=='CLOSED_RIM':why.append('闭环')
            pt=[int(x+origin[0]),int(y+origin[1])]
            if not why:
                oldtip=records[group,i]['models']['v5_4']['full']['tip']
                if oldtip and oldtip[0]<pt[0]:
                    segment=tr[tr[:,0]+origin[0]>oldtip[0]]
                    sx,sy=segment.T
                    if len(segment):
                        if i==215 and math.dist(pt,gt)<=10 and not column_audit:
                            from .bridge_audit import audit as audit_columns
                            column_audit.append(audit_columns(p,reg,fixed,segment,origin,stats['_ridge'],old_score,score,t.increments(score,tr)[-len(segment):]))
                        gains=t.increments(score,tr)[-len(segment):]
                        old_net=t.increments(old_score,tr)[-len(segment):]
                        base_curve=np.r_[0.,np.cumsum(old_net)];new_curve=np.r_[0.,np.cumsum(gains)]
                        bridge_audit.append([i,oldtip[0],pt,len(segment),num(np.mean(stats['_ridge'][sx,sy])),
                            int((score[sx,sy]>old_score[sx,sy]+1e-5).sum()),num(base_curve.min()),num(new_curve.min()),
                            num(base_curve[-1]),num(new_curve[-1])])
                revised,bridge=t.continuous_lip(tr,score,seeds,p,fixed,reg)
                if bridge and t.topology.check(p.local,revised+[p.front,0],p.front,p.scale,True)!='CLOSED_RIM':
                    tr=revised
                metric=evaluate(dict(tip=pt,points=(tr+origin).tolist(),status='VALID'),manual,gt)
                alternatives.append([i,pt,num(V[x,y]),num(e['valley_value']),num(e['valley_gain']),num(metric['error_px']),
                    num(metric['coverage']),num(metric['precision']),metric['joint'],pt==m['tip']])
            candidates.append(dict(frame=i,x=pt[0],y=pt[1],error=math.dist(pt,gt),peak=float(V[x,y]),
                valley_x=int(e['valley_x']+origin[0]),valley=e['valley_value'],gain=e['valley_gain'],
                span=e['tail_length'],net=e['net_mean'],support=e['support'],verdict='、'.join(why) or '合格'))
        every.extend(candidates)
        near=min(candidates,key=lambda item:item['error']) if candidates else {}
        review=d.get('mouth_review') or {}
        audit=d.get('branch_review') or {}
        for link in audit.get('links',[]):
            links.append([i,(np.asarray(audit['early'])+origin).tolist(),(np.asarray(link['point'])+origin).tolist(),
                num(link.get('fine')),num(link.get('support')),num(link.get('mean')),num(link.get('ratio')),
                link.get('deepest_gap','—'),link.get('separation','—'),link['reason']])
        gate_rows.append([i,num(review.get('dark_fraction')),num(review.get('new_dark_fraction')),
            num(review.get('glare_fraction')),num(review.get('diff_fraction')),review.get('cliff'),review.get('dead')])
        summary.append([i,[near['x'],near['y']] if near else '—',num(near.get('error')),num(near.get('valley_x')),
            num(near.get('valley')),num(near.get('peak')),num(near.get('gain')),num(near.get('support')),near.get('verdict','无'),
            str(review.get('dead','未触发')),d['pick'],m['tip'],num(r['coverage']),num(r['precision'])])
    if every:write_csv(b.OUT/'focus_peak_audit.csv',every)
    return ['## 三点弯候选逐项核查','对每帧最靠近人工端点的正分远端局部峰核查。谷底累计分与峰分均沿同一前驱状态链重建，已核对峰分与 DP 的存档值。人工坐标只用于离线排列距离。最后两列为最终输出路径。',
        table(['帧','最近局部峰','距标注 px','谷底原图 x','谷底 V','峰 V','独立爬升','正支撑','候选检查','近口死胡同','裁决','输出尖端','覆盖','精度'],summary),
        '近口复核的增量差分列门槛为 48%。下表给出全局峰末窗的实测比例。',
        table(['帧','暗谷列比例','新增暗谷列比例','亮邻接比例','强增量列比例','前方断崖','死胡同'],gate_rows),
        '下表逐项列出通过远端准入的候选，并离线假设选择该峰，使用原版另唇接续后计算其整条路径的覆盖与精度。最高累计分合格峰作为早峰，再执行同枝连接检查。假设选峰结果仅用于诊断。',
        table(['帧','合格候选','峰 V','谷底 V','独立爬升','尖端误差','候选覆盖','候选精度','候选联合','实际选中'],alternatives),
        '## 连接段差分与净分核查','从 V5.4 实际终点的下一列到本轮的合格峰，沿本轮精确前驱路径比较两版融合场。最低相对累计分以连接段入口为零，可直接检查中段是否仍有掉分。细脊列与实际提权列分开统计。',
        table(['帧','V5.4 终点 x','V5.5 候选','连接列数','细脊比例','实际提权列','旧场最低','新场最低','旧场净增','新场净增'],bridge_audit),
        '第 215 帧合格近标注候选的连接段，前四项计数分别表示各单项通过列数，允许重叠。联合与持续筛选另列。[逐列像素与得分](frame215_bridge_columns.csv)',
        table(['总列','差分强度','侧翼净强度','侧翼比值','低静态风险','四项同时通过','连续细脊','实际提权'],column_audit),
        '下表为运行时实际测试的同枝连接。分离量是早峰前短窗两条路径的最大纵向间距。GAP、MEAN、RATIO 分别表示最长空白、连接均分、累计峰分比例未达门槛。',
        table(['帧','早峰','晚峰','细脊比例','合并支撑比例','净均分','峰分比','最长空白','分离 px','判定'],links)]
