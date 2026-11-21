"""Post-seal audit of the nearest distal local peak and its physical eligibility."""
import json,math
import cv2
import numpy as np
from . import batch as b,terminal as t
from research.notch_identity_v42.reporting import table,num
from research.v3_labelme_comparison.compare import write_csv

def inspect_focus(scores,records):
    group='three_point_bend';rows=[];all_peaks=[];changes=[]
    for i in (144,178,215):
        folder=b.OLD/'evidence'/group/str(i)
        scene=b.read(folder/'metadata.json')['evidence']['scene'];off=np.array(scene['bounds'][:2])
        hint=np.rint(np.array(scene['root'] or scene['center'])-off).astype(int)
        gt=np.array(json.loads(scores[group,i,'v5_3','full']['gt']))
        for stage in t.STAGES:
            with np.load(folder/'arrays.npz') as z:
                p=t.prepare(z['raw'],hint,scene['scale'],stage)
                score,seeds,_,_,source,_=t.fields(p,z['fixed__aligned'])
            origin=off+np.array(p.origin)+[p.front,0];s=p.scale
            path,maximum,V,back,ds=t.lattice(score,seeds,s,source=='JOINT')
            audit=records[group,i]['models'][stage]['full']['diagnostics']['dual']
            assert abs(maximum-audit['global_score'])<1e-4
            peaks=(V>=cv2.dilate(V,np.ones((3,3),np.uint8))) & (V>0)
            peaks[:int(.2*s)+1]=False
            candidates=[]
            for x,y in zip(*np.where(peaks)):
                tr=t.unwind(back,x,y,ds[x,y]);info=t.extension_evidence(score,tr,s)
                slope=np.diff(tr[:,1],prepend=tr[0,1])
                net=score[tr[:,0],tr[:,1]]-.13*abs(slope)-.19*abs(np.diff(slope,prepend=0))
                tail=net[-t.px(s,.014):].mean()
                reasons=[]
                if V[x,y]<=.052*s:reasons.append('累计分低')
                if score[x,y]<=.08:reasons.append('末列支撑不足')
                if info['tail_length']<t.px(s,.035):reasons.append('远段过短')
                if (info['net_mean'] or 0)<=.075:reasons.append('远段净增量不足')
                if (info['support'] or 0)<.54:reasons.append('正分列比例不足')
                if info['longest_run']<t.px(s,.012):reasons.append('持续支撑不足')
                if tail<=.06 or net[-1]<=0:reasons.append('末窗未上升')
                if not reasons and t.topology.check(p.local,tr+[p.front,0],p.front,s,True)=='CLOSED_RIM':reasons.append('闭环')
                pt=np.array([x,y])+origin
                candidates.append(dict(group=group,frame=i,stage=stage,x=pt[0],y=pt[1],error=math.dist(pt,gt),V=V[x,y],tail_net=info['net_mean'],support=info['support'],status='，'.join(reasons) or '合格'))
            all_peaks+=candidates
            near=min(candidates,key=lambda x:x['error']) if candidates else {}
            rows.append([i,stage,f"{audit['candidates_checked']}/{audit['local_maxima']}",[near['x'],near['y']] if near else '—',num(near.get('error')),num(near.get('V')),num(near.get('tail_net')),num(near.get('support')),near.get('status','无正分局部峰')])
    if all_peaks:write_csv(b.OUT/'focus_peak_audit.csv',all_peaks)
    for (g,i,stage,mode),r in scores.items():
        if (g,stage,mode)!=(group,'v5_3','full') or r['state']!='VISIBLE':continue
        old=scores[g,i,'v5_2',mode]
        if old['joint']==r['joint']:continue
        oldpath=np.array(records[g,i]['models']['v5_2'][mode]['points'])
        newpath=np.array(records[g,i]['models']['v5_3'][mode]['points'])
        delta='—'
        if len(oldpath) and len(newpath):
            xs,lo,ln=np.intersect1d(oldpath[:,0],newpath[:,0],return_indices=True)
            if len(xs):
                dy=np.abs(oldpath[lo,1]-newpath[ln,1]);k=int(dy.argmax());delta=f'{dy[k]} px @ x={xs[k]}'
        penalty=[]
        with np.load(b.BASE/'surfaces'/g/f'{i:04d}_full.npz') as z0,np.load(b.OUT/'surfaces'/g/f'{i:04d}_full.npz') as z1:
            assert np.array_equal(z0['origin'],z1['origin'])
            loss=z0['score'].astype(float)-z1['score']
            for z in (z0,z1):
                path=z['path'];penalty.append(num(loss[path[:,0],path[:,1]].sum()) if len(path) else '—')
        changes.append([i,old['joint'],r['joint'],num(old['coverage']),num(r['coverage']),num(old['precision']),num(r['precision']),delta,*penalty])
    return ['## 三点弯候选逐项核查','封存后重建两个消融阶段的得分场并核对全局最高分。下表取离人工尖端最近的远端正分局部极大值，列出它未通过的条件。人工端点只参与此处事后排名。检查数是正式推理中实际检查的候选与初筛候选总数。',
        table(['帧','阶段','检查/初筛','最近局部峰','误差 px','累计 V','远段净分','支撑比例','判定'],rows),
        '## 联合结果发生变化的标注帧',table(['帧','V5.2 Joint','V5.3 Joint','原覆盖','新覆盖','原精度','新精度','路径最大同列偏移','旧路径新增扣分','新路径新增扣分'],changes)]
