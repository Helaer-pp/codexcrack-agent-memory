"""Compute stage acceptance from sealed predictions, probes and isolated block timings."""
import ast
import json
import math
import os
from pathlib import Path
from statistics import median
import numpy as np
from research.notch_identity_v512.report import table, f
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b, gate
from .run import frozen

DOC=b.ROOT/'evidence/v5_16'
OUT=b.OUT
BASE=OUT.parent/'v515_clean_fast_r02'
SETS=(('group_a','original','开发组A'),('three_point_bend','original','三点弯'),('group_c','original','验证组C原点'),('group_c','bright','验证组C亮区'))
ST=gate.STAGES
def link(path,title):
    return f"[{title}]({Path(os.path.relpath(path,DOC)).as_posix()})"
def both(loc,suffix):
    return [r for g in b.GROUPS for r in b.read_csv(loc/(g+'_'+suffix+'.csv'))]
def key(r):return r['group'],r['placement'],int(r['frame'])
def visible(rows,st):return {key(r):r for r in rows if r['stage']==st and r['state']=='VISIBLE'}
def count(rows,k):return sum(r[k]=='True' for r in rows)
def by(rows,**filters):return [r for r in rows if all(r[k]==str(v) for k,v in filters.items())]
def rate(rows,field):return len(rows)/sum(float(r[field]) for r in rows)
def md(name,parts):(DOC/name).write_text('\n\n'.join(parts)+'\n',encoding='utf8')

def synthetic():
    a=b.read_csv(OUT/'paired_probes.csv')
    seal=b.read(OUT/'probe_seal.json')
    assert seal['sources']==b.sources() and seal['csv']==b.sha(OUT/'paired_probes.csv')
    stats={};summary=[];full=[]
    for st in ST:
        rows=by(a,stage=st); neg=by(rows,negative='True')
        assert len(rows)==1404 and len(neg)==468
        d=dict(fp=count(neg,'valid')); stats[st]=d
        for k in ('active_fork','weak_material_bridge','P4_open','mouth_glare_arc_only'):
            d[k]=count(by(rows,case=k),'passed')
        for k in gate.P6:d[k]=[count(by(rows,case=k,zoom=z),'passed') for z in (.5,1.,2.)]
        summary.append([st,d['fp'],d['P4_open'],d['mouth_glare_arc_only'],d['weak_material_bridge'],d['active_fork'],*[' / '.join(map(str,d[k])) for k in gate.P6]])
    for case,width,c in sorted({(r['case'],r['width'],r['contrast']) for r in a}):
        rows=by(a,case=case,width=width,contrast=c)
        full.append([case,width,c,*[' / '.join(str(count(by(rows,stage=s,zoom=z),'passed')) for z in (.5,1.,2.)) for s in ST]])
    return stats,table(['阶段','误报 /468','P4 /36','反光弧 /36','弱桥 /36','分叉 /36','P6 孤立各 /12','P6 变形各 /12'],summary),table(['场景','间断宽度','对比度',*ST],full)

def bench():
    mins={};out=[];blocks=[];modules=[]
    for st,folder,label in [('S2',BASE,'V5.15 S2')]+[(s,OUT,s) for s in ST]:
        prefix=f'bench_{st}_4'
        rows=b.read_csv(folder/(prefix+'.csv'))
        assert [int(r['frame']) for r in rows]==list(range(1,521))
        modules.append([label,*[f(np.mean([float(r[k]) for r in rows])) for k in ('upstream_ms','registration_ms','fields_ms','normal_ms','lattice_ms')]])
        parts=[rows[j:j+52] for j in range(0,520,52)]
        slow=min(rate(p,'seconds') for p in parts)
        wall=b.read(folder/(prefix+'.json'))['wall_seconds']
        if folder==OUT:mins[st]=slow
        out.append([label,f(rate(rows,'seconds')),f(rate(rows,'detector_seconds')),f(520/wall),f(slow),round(median(float(r['field_pixels']) for r in rows))])
        blocks.extend(dict(stage=label,first=p[0]['frame'],last=p[-1]['frame'],fps=rate(p,'seconds')) for p in parts)
    write_csv(OUT/'benchmark_blocks.csv',blocks)
    return mins,table(['阶段','含映射 FPS/进程','检测 FPS/进程','整池 FPS','最慢 52 帧 FPS/进程','累计证据像素中位'],out),table(['阶段','上游映射 ms','局部配准 ms','其余证据场 ms','法向证据 ms','DP ms'],modules)

def sensitivity():
    out=[];summary={}
    for g,pl,name in SETS:
        if g=='group_c' and pl=='original':continue
        data=b.read_csv(OUT/(g+'_stress.csv'))
        for st in ST:
            normal={(r['frame'],r['repeat']):r for r in by(data,stage=st,direction='left',delta=0)}
            rows=by(data,stage=st,direction='left',delta=-150)
            ratios=[];pix=[];shifts=[];drift=[]
            for r in rows:
                n=normal[r['frame'],r['repeat']]
                ratios.append(float(r['seconds'])/float(n['seconds']))
                if float(n['field_pixels']):pix.append(float(r['field_pixels'])/float(n['field_pixels']))
                shifts.append(float(r['actual_dx']))
                if r['drift']:drift.append(float(r['drift']))
            point=dict(ratio=median(ratios),max_drift=max(drift,default=0),changed=count(rows,'status_change'),min_dx=min(shifts),max_dx=max(shifts))
            summary.setdefault(st,{})[g]=point
            out.append([name,st,len(rows),f(min(shifts))+' 至 '+f(max(shifts)),f(median(pix)),f(point['ratio']),f(np.percentile(ratios,95)),f(point['max_drift']),point['changed']])
    return summary,table(['组','阶段','配对试次','实际 dx（px）','像素比中位','时间比中位','时间比 P95','最大漂移 px','状态改变'],out)

def main():
    frozen();DOC.mkdir(exist_ok=True,parents=True)
    rows=both(OUT,'scores'); old=visible(both(BASE,'scores'),'S2')
    real={s:visible(rows,s) for s in ST}
    stats,syn,full=synthetic();mins,timing,modules=bench();shift,stress=sensitivity()
    times={}; models={}; near_cost=[]; recovered=0; branches=both(OUT,'curves')
    for g,n in b.GROUPS.items():
        path=OUT/(g+'.jsonl')
        assert b.sha(path)==b.read(OUT/(g+'_seal.json'))['predictions']
        for rec in map(json.loads,path.open(encoding='utf8')):
            for pl,stages in rec['placements'].items():
                k=(g,pl,rec['frame'])
                if g=='three_point_bend':
                    start=stages['S1']['full']; near_model=stages['S2']['full']
                    diag=near_model['diagnostics']['dual']
                    if diag.get('proximal_replay'):
                        near_cost.append(diag['field_pixels']-start['diagnostics']['dual']['field_pixels'])
                        recovered+=int(start['tip'] is None and near_model['tip'] is not None)
                for s,bundle in stages.items():
                    times.setdefault((g,pl,s),[]).append(bundle['seconds'])
                    if k in old:models[k,s]=bundle['full']
    reasons={}
    for i,s in enumerate(ST):
        reasons[s]=gate.eligible(s,real[s],old,real[ST[i-1]] if i else old,stats[s],stats[ST[i-1]],mins[s])
    accepted=gate.choose(reasons)
    stage=accepted or 'S3'
    b.save(OUT/'selection.json',dict(stage=stage,release=accepted,baseline='V5.15 S2',reasons=reasons,slowest=mins,stress=shift,synthetic=stats))
    write_csv(OUT/'crack_lengths.csv',by(both(OUT,'lengths'),stage=stage))
    summary=[];accuracy=[];fail=[];failure_table=[];targets=[];mouth=[];tail=[]
    for g,pl,name in SETS:
        selected={k:r for k,r in real[stage].items() if k[:2]==(g,pl)}
        summary.append(f"{name} {count(selected.values(),'joint')}/{len(selected)}")
        for s,rr in [('V5.15 S2',old),*real.items()]:
            group=[r for k,r in rr.items() if k[:2]==(g,pl)]
            speed=times.get((g,pl,s))
            accuracy.append([name,s,len(group),*[count(group,k) for k in ('hit5','hit10','joint','severe')],sum(not r['error_px'] for r in group),f(len(speed)/sum(speed)) if speed else '—'])
        for k,r in selected.items():
            i=k[2]
            if i in {'group_a':(113,299,366,398),'three_point_bend':(144,215,248,335,381,413,435,503),'group_c':(7,38,54,510)}[g]:
                targets.append([name,i,f(old[k]['error_px']),*[f(real[s][k]['error_px']) for s in ST],f(r['dx']),f(r['coverage']),f(r['precision']),link(OUT/'stage_views'/f'{g}_{pl}_{i:04d}.jpg','四阶段图')])
                for s in ST:
                    d=models[k,s]['diagnostics']['dual']
                    br=next((a for a in d['branches'] if d['pick']=='BRANCH_'+str(a['id'])),max(d['branches'],key=lambda a:a['merit'],default={}))
                    c=br.get('curve',{})
                    if (g=='group_c' and i==7) or (g=='three_point_bend' and i==144):
                        mouth.append([name,i,s,d['decision'],d['stop'],d.get('mouth_extent'),f(d.get('native_change')),d.get('proximal_replay',False),f(br.get('initial_total')),c.get('longest_dual_run','—')])
                    if s in ('S3','S4'):
                        tail.append([name,i,s,c.get('charged_columns',0),f(c.get('tail_charge',0)),c.get('scratch_cut','—'),f(real[s][k]['error_px'])])
            if r['joint']=='True':continue
            gt=ast.literal_eval(r['gt'])
            candidates=by(branches,group=g,placement=pl,frame=i,stage=stage)
            near=min((math.dist(ast.literal_eval(c['tip']),gt) for c in candidates if c['tip']),default=math.inf)
            if not r['error_px']:why='无尖端，最终裁决 '+r['stop']
            elif r['hit10']=='True':why='端点命中，路径精确率或覆盖率不足'
            elif near<=10:why='存在命中端点的候选，门控或排序未选择'
            elif float(r['dx'])>0:why='回溯候选均未命中，胜出路径越过标注尖端'
            else:why='回溯候选均未命中，胜出路径提前终止'
            fail.append(dict(group=g,placement=pl,frame=i,stage=stage,reason=why,error_px=r['error_px'],dx=r['dx'],dy=r['dy']))
            failure_table.append([name,i,f(r['error_px']),f(r['dx']),f(r['dy']),why,link(OUT/'audit_views'/f'{g}_{pl}_{i:04d}.jpg','图与曲线')])
    write_csv(OUT/'failure_index.csv',fail)
    heading=('本轮选定 **'+accepted+'**。' if accepted else '四个候选均触发交付底线，日常默认保留 V5.15 S2。本轮研究交付与逐帧展示采用 V5.16 S3。')+'联合命中为'+'，'.join(summary)+'。'
    acc=table(['组与点位','阶段','可见','Hit@5','Hit@10','Joint','Severe','无预测','整序列含映射 FPS/进程¹'],accuracy)
    def explain(reason):
        if reason.endswith(': lost Joint'):
            g,pl,i=ast.literal_eval(reason.split(':')[0])
            name=next(n for group,place,n in SETS if (group,place)==(g,pl))
            return f'{name}第 {i} 帧失去联合命中'
        return {'slowest TPB block below 8 FPS':'三点弯最慢区段低于 8 FPS','synthetic safety/control':'合成对照未过线'}.get(reason,reason)
    reason_table=table(['阶段','交付底线检查'],[[s,'，'.join(map(explain,reasons[s])) or '通过'] for s in ST])
    target=table(['组','帧','V5.15 S2 px',*ST,'展示阶段 dx','覆盖率','精确率','逐阶段局部图'],targets)
    modes=table(['组','帧','阶段','路由','终止','缺口窗宽 px','局部残差 P97','近端重算','入口分','连续双列'],mouth)
    tailtable=table(['组','帧','阶段','整候选受罚列','整候选锐度扣分','划痕截断索引','端点误差 px'],tail)
    rules='开发组A用于开发。人工标注仅在预测封存后用于对照。三点弯与验证组C冻结后验证，排除排除组X。验证组C原点和亮区复用同一批图像。Joint 要求端点误差 ≤10 px、路径覆盖率和精确率均 ≥80%。Severe 表示有预测时误差 >100 px，无预测单列。'
    method='S1 在两帧各自的缺口轮廓顶点测量开口，并检查顶点前方灰度残差。窗口随实测轮廓宽度变化，去除亮度偏置并容许 1 px 平移。安静且配准可用时走既有暗线分支，否则评估联合证据。紧贴缺口的极短联合路径允许连续 6 列原图窄谷与双通道证据，纯轮廓回退仍需 8 列。上游点位仍用于找到试件和参考映射。'
    near='S2 沿用 18 万像素远端预算。窄带无有效输出且候选触发口门死端时，在两侧入口各增加 0.055 倍尺度的近端余量，重算缺口前 0.20 倍尺度与滤波上下文。新候选的端点必须落在近端区内。累计像素包含重算开销。'
    near+=f' 三点弯全 520 帧中有 {len(near_cost)} 帧触发近端重算，新增有效尖端 {recovered} 帧。重算帧额外证据像素的中位数为 {round(median(near_cost)) if near_cost else 0}，每个输入帧平均新增 {sum(near_cost)/520:.0f} 像素。'
    local='S3 用原图中心 1–2 px 和两侧 4–6 px 的绝对灰度落差判定宽浅暗谷。仅在连续宽浅凹陷、邻近三列窗口存在加性对比度下降、差分微红时扣分。S4 另外惩罚低支持段的归一化侧移，检测切向改变后与路径平行的反号位移痕迹，并在满足条件时截去后续候选。'
    sign='¹ 各组速度取四阶段同批推理中每阶段的帧数除以累计耗时。下表的三点弯速度为各阶段独立启动四进程、预热、回放同一 520 帧所得；按连续 52 帧分 10 段，以最慢含上游映射速度验收。整池另计读盘、校验和调度。'
    links=' · '.join([link(OUT/'difference_views/index.html','逐帧四联图、差分和视频'),link(OUT/'crack_lengths.csv','逐帧尖端与长度'),link(OUT/'paired_probes.csv','合成逐次结果'),link(OUT/'freeze.json','冻结清单'),link(OUT/'selection.json','阶段准入记录')])
    goals=[]
    for g,pl,i in [('group_c','bright',7),('three_point_bend','original',144)]:
        s='S1' if i==7 else 'S2';r=real[s][g,pl,i]
        goals.append(f"{g} {pl} 第 {i} 帧在 {s} 的裁决为 {r['stop']}，误差 {f(r['error_px'])} px。")
    over=[(g,pl,i) for g,pl,name in SETS for i in {'group_a':(398,),'three_point_bend':(335,413,435,503),'group_c':(510,)}[g]]
    gained=sum(real['S3'][k]['joint']=='True' for k in over)
    goals.append(f'S3 收回指定过追帧次 {gained}/{len(over)}。三张受保护的开发组A细裂纹逐帧误差见表。')
    changes=[]
    for j,s in enumerate(ST):
        prev=real[ST[j-1]] if j else old
        for k,r in real[s].items():
            before=prev[k]
            if (before['joint'],before['status'])==(r['joint'],r['status']):continue
            d=models[k,s]['diagnostics']['dual']
            br=next((v for v in d['branches'] if d['pick']=='BRANCH_'+str(v['id'])),{})
            info=br.get('curve',{})
            changes.append([k[0],k[1],k[2],s,before['source']+' → '+r['source'],before['stop']+' → '+r['stop'],
                            before['joint']+' → '+r['joint'],f(before['error_px'])+' → '+f(r['error_px']),
                            info.get('scratch_cut','—'),f(info.get('geometry_cost'))])
    transitions=table(['组','点位','帧','阶段','证据路由','终止原因','Joint','误差 px','划痕截断列索引','转移代价'],changes) if changes else '四个阶段均保留前一阶段的全部可见帧状态与 Joint 判定。'
    from .tail_audit import measure
    sections=measure(models,real['S3'])
    profiles=table(['组','点位','帧','区域','列数','1–2 px 锐度中位','4–6 px 落差中位'],
                   [[r['group'],r['placement'],r['frame'],r['region'],r['columns'],f(r['narrow_median']),f(r['broad_median'])] for r in sections])
    gray_note='按 S3 输出路径在原图抽样。proximal_12 为标注尖端前 12 px，beyond_gt 为标注尖端之后。灰度落差越高代表该宽度上暗谷越深。标注仅用于离线划分区间。'
    route=b.read_csv(OUT/'route_counterfactual.csv')
    route_table=table(['点位','实验开关','物理窗残差','顶点前沿 x','配准位移','证据源','端点','裁决'],
                      [[r[k] or '—' for k in ('placement','mode','native_change','front','shift','source','tip','stop')] for r in route])
    faults=[]
    probes=b.read_csv(OUT/'paired_probes.csv')
    for k in gate.P6:
        for z in (.5,1.,2.):
            rr=by(probes,case=k,stage='S4',zoom=z)
            faults.append([k,z,count(rr,'passed'),sum(not v['error'] for v in rr),
                          sum(float(v['error'] or 0)>10 for v in rr),
                          sum(bool(v['error']) and float(v['error'])<=10 and float(v['precision'])<.95 for v in rr)])
    p6fail=table(['P6 场景','倍率','通过 /12','无预测','端点误差 >10','端点命中但路径精确率低'],faults)
    failed_keys=[k for k,base in old.items() if base['joint']=='True' and real[stage][k]['joint']!='True']
    newly=[k for k,base in old.items() if base['joint']!='True' and real[stage][k]['joint']=='True']
    trade='相对 V5.15 S2，展示阶段新增 Joint 的帧次为 '+('、'.join(f'{g}/{p}/{i}' for g,p,i in newly) or '无')+'。失去 Joint 的帧次为 '+('、'.join(f'{g}/{p}/{i}' for g,p,i in failed_keys) or '无')+'。'
    replay='日常入口保留脚本顶部的手动配置。在该处打开 use_validation_candidate，或使用 CrackTipRunner.exe --candidate，即可回放本轮研究候选并生成对应渲染。'+link(b.ROOT/'docs/CURRENT_CRACK_RUNNER.md','运行方法')
    case7='验证组C第 7 帧的两种点位都找到前沿 x=2248。原点与亮区的局部残差 P97 分别为 6.06 和 6.19，实际均走 JOINT。固定输入并强制走既有暗线分支后，两者都恢复 (2273, 2339)，与标注相差 0.84 px。该帧的错误可定位到对局部变化的判断。亮区路径累计到 6 列仍不足以同时通过原图窄谷及连续双证据要求。'
    tail_case='S3 在三点弯第 215 帧对两个主要候选均累计扣 53.2 分，新的端点截短后触发 CLOSED_RIM，两条路径均遭拒绝。第 435 帧从过追约 10 px 转为提前约 12 px。开发组A第 398 帧在人工端点后仍有 12 列，1–2 px 锐度中位数为 15.5 灰度级；验证组C第 510 帧的越界段也保有窄谷。宽浅暗晕不足以解释全部过追帧。'
    qa=b.ROOT/'output/verification/v516_public_runner/checks.csv'
    if qa.exists():replay+=' '+link(qa,'日常 EXE 七个帧次与封存路径、长度、渲染的对照记录')
    md('REPORT.md',['# V5.16 裂纹尖端验证报告',heading,trade,' '.join(goals),case7,reason_table,rules,'## 算法与消融',method,near,local,'## 实帧精度与速度',acc,sign,timing,modules,'## 端点误差逐帧对照',target,'## 基准点左移 150 px',stress,'验证组C亮区逐帧将请求的点位投影到参考与当前同时有效的材料区域。表内给出实际位移。漂移只统计两次均输出尖端的配对。','## 合成验证',syn,'每格依次为 0.5×、1×、2× 的通过数，各倍率每场景 12 次。',full,replay,links,link(DOC/'FAILURES_AUDIT.md','失败与阶段原因审计')])
    md('FAILURES_AUDIT.md',['# V5.16 失败帧与原因审计',heading,trade,reason_table,'## 阶段对照',acc,syn,'## 各阶段改变状态或命中的帧',transitions,'## 重点帧',target,modes,'### 验证组C第 7 帧路由反事实','固定同一输入图、测点与配准实现，单独强制缺口变化检测器返回静止或变化。该试验只作事后归因。native 为实际推理。',route_table,case7,'## P6 剩余错误',p6fail,'## 末端惩罚与划痕判定',tailtable,tail_case,gray_note,profiles,'列数与扣分来自胜出分支的完整回溯候选，可能包含最终尖端之后的列。','## 所有可见失败',table(['点位','帧','误差','dx','dy','诊断','证据'],failure_table),'## 速度与扰动',timing,modules,stress,links])
    print(heading,flush=True)

if __name__=='__main__':main()
