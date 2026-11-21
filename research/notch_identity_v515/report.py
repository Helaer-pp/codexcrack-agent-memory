"""Publish the sealed validation, performance and failure evidence."""
import ast
import math
import os
from pathlib import Path
from statistics import mean, median
from collections import Counter
import numpy as np
from research.notch_identity_v512.report import table, f
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b, gates
from .run import frozen

OUT=b.OUT
DOC=OUT/'pilot_report'
OLD=OUT.parent/'v514_roi_decouple_r01'
GROUPS=[('group_a','original','开发组A'),('three_point_bend','original','三点弯'),('group_c','original','验证组C原点'),('group_c','bright','验证组C亮区')]
STAGES=b.ALGS

def link(path,title):
    return f"[{title}]({Path(os.path.relpath(path,DOC)).as_posix()})"

def get(name):return b.read_csv(OUT/name)
def filt(data,**criteria):return [r for r in data if all(r[k]==str(v) for k,v in criteria.items())]
def n(rows,k):return sum(r[k]=='True' for r in rows)
def bygroup(suffix):return [r for g in b.GROUPS for r in get(g+'_'+suffix+'.csv')]
def txt(path,parts):path.write_text('\n\n'.join(parts)+'\n',encoding='utf8')
def val(row,k):return float(row[k]) if row[k] else math.inf
def rate(rows,k):return len(rows)/sum(float(r[k]) for r in rows)

def performance():
    speed={s:[] for s in STAGES};timing=[];modules=[];blocks=[]
    for st in STAGES:
        for workers in (1,4):
            key=f'bench_{st}_{workers}';rows=get(key+'.csv');bench=b.read(OUT/(key+'.json'))
            assert [int(r['frame']) for r in rows]==list(range(1,521))
            total=rate(rows,'seconds');det=rate(rows,'detector_seconds')
            periods=[rows[i:i+52] for i in range(0,520,52)]
            bound=[min(rate(p,k) for p in periods) for k in ('seconds','detector_seconds')]
            speed[st].extend([total,det,*bound])
            timing.append([st,workers,f(total),f(det),f(520/bench['wall_seconds']),*map(f,bound)])
            modules.append([st,workers,*[f(mean(float(r[k]) for r in rows)) for k in
                ('upstream_ms','registration_ms','fields_ms','normal_ms','lattice_ms')],round(median(float(r['field_pixels']) for r in rows))])
            for i,p in enumerate(periods):
                blocks.append(dict(stage=st,workers=workers,first=i*52+1,last=(i+1)*52,upstream_inclusive_fps=rate(p,'seconds'),detector_fps=rate(p,'detector_seconds')))
    write_csv(OUT/'benchmark_blocks.csv',blocks)
    return speed,table(['阶段','进程数','每进程含映射 FPS','每进程检测 FPS','整池 FPS','最慢 52 帧含映射','最慢 52 帧检测'],timing),table(['阶段','进程数','上游 ms','局部配准 ms','其余证据场 ms','法向证据 ms','DP ms','证据场像素中位数'],modules)

def simulation():
    rows=get('paired_probes.csv')
    assert b.sha(OUT/'paired_probes.csv')==b.read(OUT/'probe_seal.json')['csv']
    stats={};summary=[];full=[]
    for st in STAGES:
        a=filt(rows,stage=st);neg=filt(a,negative='True');assert len(a)==1404 and len(neg)==468
        def passed(case):return n(filt(a,case=case),'passed')
        stats[st]=d=dict(fp=n(neg,'valid'),bridge=passed('weak_material_bridge'),glare=passed('mouth_glare_arc_only'))
        for k in gates.P6:
            d[k]=[n(filt(a,case=k,zoom=z),'passed') for z in (.5,1.,2.)]
        summary.append([st,str(d['fp'])+'/468',passed('P4_open'),d['glare'],d['bridge'],*[' / '.join(map(str,d[k])) for k in gates.P6]])
    cases=sorted({(r['case'],int(r['width']),float(r['contrast'])) for r in rows})
    for case,width,c in cases:
        a=[r for r in rows if r['case']==case and int(r['width'])==width and float(r['contrast'])==c]
        full.append([case,width,c,'负' if a[0]['negative']=='True' else '正',*[' · '.join(str(n(filt(a,stage=s,zoom=z),'passed'))+'/12' for z in (.5,1.,2.)) for s in STAGES]])
    return stats,table(['阶段','负样本误报','P4_open /36','口门反光弧 /36','弱材料桥 /36','孤立划痕 各 /12','变形划痕 各 /12'],summary),table(['合成场景','间断宽度','对比度','类别',*STAGES],full)

def stress():
    rows=bygroup('stress');out=[];more=[]
    for g,pl,name in GROUPS:
        if g=='group_c' and pl=='original':continue
        for stage in STAGES:
            r=filt(rows,group=g,stage=stage,direction='left')
            for dx in (-50,-100,-150):
                base={(a['frame'],a['repeat']):a for a in filt(r,delta=0)}
                sub=filt(r,delta=dx);ratios=[];pixels=[]
                for a in sub:
                    orig=base[a['frame'],a['repeat']]
                    ratios.append(float(a['seconds'])/float(orig['seconds']))
                    if int(orig['field_pixels']):pixels.append(float(a['field_pixels'])/float(orig['field_pixels']))
                delta=[float(a['actual_dx']) for a in sub]
                drift=[float(a['drift']) for a in sub if a['drift']]
                out.append([name,stage,dx,len(sub),f(min(delta))+' 至 '+f(max(delta)),f(median(pixels)),f(median(ratios)),f(np.percentile(ratios,95)),f(max(drift,default=0)),n(sub,'status_change')])
            extra=[a for a in filt(rows,group=g,stage=stage) if a['direction']!='left']
            if extra:more.append([name,stage,len(extra),f(max((float(a['drift']) for a in extra if a['drift']),default=0)),n(extra,'status_change')])
    return table(['点位','阶段','请求 dx','配对试次','实际 dx 范围','证据场像素比中位','时间比中位','时间比 P95','最大可比漂移 px','状态改变'],out),table(['验证组','阶段','额外扰动试次','最大可比漂移 px','状态改变'],more)

def main():
    frozen();DOC.mkdir(parents=True,exist_ok=True)
    for g in b.GROUPS:assert b.sha(OUT/(g+'.jsonl'))==b.read(OUT/(g+'_seal.json'))['predictions']
    scores=bygroup('scores');curves=bygroup('curves')
    visible=filt(scores,state='VISIBLE');stats,syntab,full=simulation()
    speed,times,modules=performance();shift,jitter=stress()
    accuracy=[];real={};anchors={}
    for st in STAGES:
        subset=filt(visible,stage=st)
        real[st]={(r['group'],r['placement'],r['frame'],k):r[k]=='True' for r in subset for k in ('hit10','joint')}
        anchors[st]={(r['group'],r['placement'],r['frame']):val(r,'error_px') for r in subset if (r['group']=='group_c' and int(r['frame']) in (38,54)) or (r['group']=='three_point_bend' and int(r['frame']) in (215,248))}
    chosen,eligible=gates.select(stats,real,speed,anchors)
    b.save(OUT/'selection.json',dict(stage=chosen,promotion_from_s1=eligible,synthetic=stats,comparison=dict(target_fps=gates.LATENCY_TARGET,anchor_tolerance_px=.05),freeze_sha=b.sha(OUT/'freeze.json')))
    winners=filt(visible,stage=chosen)
    lengths=filt(bygroup('lengths'),stage=chosen)
    assert len(lengths)==2195
    write_csv(OUT/'crack_lengths.csv',lengths)
    for g,pl,name in GROUPS:
        prior=b.read_csv(OLD/(g+'_scores.csv'))
        for st,data in [('V5.14 S1',filt(prior,stage='S1')),('V5.14 S4',filt(prior,stage='S4'))]+[(s,filt(scores,stage=s)) for s in STAGES]:
            a=filt(data,group=g,placement=pl,state='VISIBLE')
            accuracy.append([name,st,len(a),*[n(a,k) for k in ('hit5','hit10','joint','severe')],sum(not r['error_px'] for r in a)])
    acctab=table(['组与点位','阶段','可见帧','Hit@5','Hit@10','Joint','Severe','无预测'],accuracy)
    summary='，'.join(name+' '+str(n(filt(winners,group=g,placement=pl),'joint'))+'/'+str(len(filt(winners,group=g,placement=pl))) for g,pl,name in GROUPS)
    head=f'交付研究阶段为 **{chosen}**。Joint 命中为{summary}。负样本误报为 {stats[chosen]["fp"]}/468。'
    rules='开发组A用于开发。三点弯与验证组C只在代码、算子与验收规则冻结后验证。排除组X排除。人工标注只作预测封存后的离线对照。实际运行 1,633 张不同当前帧，验证组C原点与亮区使用同一组图像，两种点位共得到 2,195 帧次。命中率只统计有可见尖端标注的帧。Joint 要求端点误差 ≤10 px、路径覆盖率及精确率均 ≥80%。Severe 为有预测且误差 >100 px，无预测单列。'
    details='S1 保留缺口裁剪、融合算子与原端点评分。撤掉 V5.14 末端暗谷扣分和反光弧门控。当仅有轮廓回退、局部 NCC 未通过、路径跨度 ≤0.25 倍特征尺度时，即便入口得分通过，也必须连续 8 列双一致。S2 对超过 250,000 像素的证据域切换为原像素窄走廊，按入口中位行取两侧约 0.085 倍特征尺度，保留全部入口。上游映射增加配准边缘。粗尖端在原图同列 3 像素用灰度暗谷和配准差分作抛物线横向精修，位移 ≤0.5 px，纵向追踪距离仍由 DP 决定。S3 独立增加按特征尺度归一的转移代价，用缺口后的亮化证据、无支持跨度、横向偏移和方向变化约束跨跳。'
    decisions=[]
    for s,base in [('S2','S1'),('S3','S2')]:
        lost=sum(real[base][k] and not real[s][k] for k in real[s] if k[-1]=='joint')
        regress=[f'{g}/{pl}/{i}' for (g,pl,i),v in anchors[s].items() if v>anchors[base][g,pl,i]+.05]
        decisions.append([s,base,lost,', '.join(regress) or '无',f(min(speed[s])),str(eligible[s])])
    dec=table(['候选','对照','失去的逐帧 Joint','关键帧误差增加 >0.05 px','最小考核 FPS','通过升级门槛'],decisions)
    perf_note='三点弯每个阶段及进程配置独立回放全部 520 帧并预热。每进程速度为帧数除以所有帧相应耗时之和。检测含缺口定位，含映射在此基础上计入上游参考图配准。整池按实际墙钟计时，包含读图、哈希、序列化、工作进程调度。另列每 52 个连续帧的最低速度，检验“稳定达标”。模块时间为逐帧均值，未单列的定位、候选生成和精修等开销计入总时长。'
    benchlinks=link(OUT/'benchmark_blocks.csv','每 52 帧速度')+' · '+link(OUT/'bench_S2_4.csv','S2 四进程逐帧计时与细分算子')
    sensnote='三组对全部选定标注帧重算定位、映射和检测。时间比采用同帧同轮偏移与原点的比值。漂移仅对双方均有尖端的帧次统计。验证组C按亮区约束投影后运行，实际位移见表。'
    keyrows=[];failrows=[];audit=[];cross=get('mapping_cross.csv')
    for g,pl,name in GROUPS:
        prev=b.read_csv(OLD/(g+'_scores.csv'))
        for r in filt(winners,group=g,placement=pl):
            i=r['frame'];point=ast.literal_eval(r['gt'])
            series=[filt(visible,group=g,placement=pl,frame=i,stage=s)[0] for s in STAGES]
            if len({a['joint'] for a in series})>1 or r['joint']!='True' or int(i) in {'group_a':{113,299,366},'three_point_bend':{215,248,381},'group_c':{38,54}}[g]:
                old=filt(prev,stage='S4',placement=pl,frame=i)[0]
                keyrows.append([name,i,f(old['error_px']),*[f(a['error_px']) for a in series],*(a['joint'] for a in series)])
            if r['joint']=='True':continue
            bs=filt(curves,group=g,placement=pl,frame=i,stage=chosen)
            candidates=[(math.dist(ast.literal_eval(a['tip']),point),a) for a in bs if a['tip']]
            best=min(candidates,key=lambda a:a[0],default=None)
            if not r['error_px']:why='未输出尖端，终止于 '+r['stop']
            elif r['hit10']=='True':why='端点已命中，路径覆盖或精确率低于 80%'
            elif best and best[0]<=10:why='存在命中候选，排序或门控未选中'
            elif float(r['dx'])>0:why='全部候选均未命中，选中端点沿 x 越过人工尖端'
            else:why='全部候选均未命中，选中路径在人工尖端前终止'
            failrows.append(dict(group=g,placement=pl,frame=i,stage=chosen,reason=why,dx=r['dx'],dy=r['dy'],error=r['error_px'],source=r['source'],stop=r['stop']))
            pic=OUT/'audit_views'/f'{g}_{pl}_{int(i):04d}.jpg'
            audit.append([name,i,f(r['error_px']),f(r['dx']),f(r['dy']),f(r['coverage']),f(r['precision']),why,link(pic,'图与分支曲线')])
    write_csv(OUT/'failure_index.csv',failrows)
    keys=table(['点位','帧','V5.14 S4 误差','S1 px','S2 px','S3 px','S1 Joint','S2 Joint','S3 Joint'],keyrows)
    failure=table(['点位','帧','误差 px','dx','dy','覆盖率','精确率','首次可见的问题','对照'],audit)
    counter=[]
    for i in sorted({int(r['frame']) for r in cross}):
        a=filt(cross,frame=i)
        def sample(m,e):return filt(a,mapping=m,engine=e)[0]
        counter.append([i,*[f(sample(m,e)['error']) for m,e in [('S1','S1'),('S2','S1'),('S1','S2'),('S2','S2')]],sample('S1','S1')['source'],sample('S2','S2')['source']])
    cross_table=table(['三点弯帧','宽映射＋宽场','窄映射＋宽场','宽映射＋窄场精修','窄映射＋窄场精修','S1 证据','S2 证据'],counter)
    p6=table(['样例','倍率','阶段','注册来源','终止','尖端','人工端点','归一化 dx','连续双列','几何代价'],[[r[k] if k not in ('dx','cost') else f(r[k]) for k in ('case','zoom','stage','registration','reason','tip','gt','dx','dual_run','cost')] for r in get('synthetic_replay.csv') if r['stage'] in ('S2','S3') and r['case'] in gates.P6])
    ratios='；'.join(s+' '+str(stats[s]['P6_isolated'])+' / '+str(stats[s]['P6_deformed_scratch']) for s in STAGES)
    p6_note='P6 孤立划痕和变形划痕按 0.5×、1×、2× 列出通过数，各倍率 12 次。'+ratios+'。三倍率均为零不构成有效抑制。'
    files=' · '.join([link(OUT/'difference_views/index.html','逐帧四联图、差分与分组视频'),link(OUT/'crack_lengths.csv','逐帧裂纹弧长与锚点投影（px）'),link(OUT/'failure_index.csv','失败帧清单'),link(OUT/'freeze.json','冻结清单'),link(OUT/'paired_probes.csv','全量合成逐次结果')])
    txt(DOC/'REPORT.md',['# V5.15 裂纹尖端开发验证报告',head,dec,rules,details,'## 实帧消融',acctab,'## 三点弯 520 帧速度',perf_note,times,modules,benchlinks,'## 基准点敏感性',sensnote,shift,jitter,'## 合成消融与完整矩阵',syntab,p6_note,'下表每格依次为 0.5×、1×、2× 的通过数。每个倍率包含两种噪声、两枚随机种子和三种曝光。',full,'## 逐帧证据',files,link(DOC/'FAILURES_AUDIT.md','失败与原因审计')])
    txt(DOC/'FAILURES_AUDIT.md',['# V5.15 失败帧与速度审计',head,dec,'## 实帧与合成消融',acctab,syntab,'## 重点帧与改变命中的帧',keys,'## 最终研究阶段的所有可见失败',failure,'## 三点弯窄带的原因排查','诊断时固定输入点与缺口，交叉互换上游映射和下游检测。每个数值是端点误差 px，空值表示无可评分端点。此交叉重放仅解释已冻结输出。',cross_table,link(OUT/'mapping_cross.csv','交叉重放的尖端、证据源与配准位移'),'## 合成划痕',p6_note,'下表抽取低噪声、种子 17、标称曝光，完整矩阵见报告。',p6,'## 耗时与点位',times,modules,shift,files])
    print(head,flush=True)

if __name__=='__main__':main()
