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
    labels={int(r["frame_id"]):r for r in read_csv(b.SELECT) if r["dataset_id"]==group}
    for i in (144,178,215):
        folder=b.OLD/'evidence'/group/str(i)
        scene=b.read(folder/'metadata.json')['evidence']['scene']
        off=np.asarray(scene['bounds'][:2])
        hint=np.rint(np.asarray(scene['root'] or scene['center'])-off).astype(int)
        with np.load(folder/'arrays.npz') as z:
            p=t.prepare(z['raw'],hint,scene['scale'])
            fixed=z['fixed__aligned']
            score,seeds,_,reg,source,_=t.fields(p,fixed)
        origin=off+np.asarray(p.origin)+[p.front,0]
        _,maximum,V,back,ds=t.lattice(score,seeds,p.scale,source=='JOINT')
        r=scores[group,i,'v5_4','full']
        gt=json.loads(r['gt'])
        m=records[group,i]['models']['v5_4']['full']
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
        '下表逐项列出通过远端准入的候选，并离线假设选择该峰，使用原版另唇接续后计算其整条路径的覆盖与精度。算法实际按累计峰分排序；假设选峰结果仅用于诊断。',
        table(['帧','合格候选','峰 V','谷底 V','独立爬升','尖端误差','候选覆盖','候选精度','候选联合','实际选中'],alternatives)]
