"""Publish the four-stage accuracy, left-shift, timing and failure audits."""
import ast
import json
import math
import os
from collections import Counter
from pathlib import Path
from statistics import median, mean
import numpy as np
from research.notch_identity_v512.report import table
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b
from .run import frozen

OUT=b.OUT
DOC=b.ROOT/'evidence/v5_14'
OLD=OUT.parent/'v513_unified_diff_r01'
SETS=[('group_a','original','开发组A'),('three_point_bend','original','三点弯'),
      ('group_c','original','验证组C原点'),('group_c','bright','验证组C亮区')]
def get(path):return b.read_csv(path)
def pick(rows,**keys):return [r for r in rows if all(r[k]==str(v) for k,v in keys.items())]
def count(rows,k):return sum(r[k]=='True' for r in rows)
def f(v):return '—' if v is None or v=='' else f'{float(v):.2f}'
def value(s):return ast.literal_eval(s) if s else None
def link(p,title):return f'[{title}]({Path(os.path.relpath(p,DOC)).as_posix()})'
def write(filename,text):(DOC/filename).write_text('\n\n'.join(text)+'\n',encoding='utf8')
def summary(rows):return [count(rows,k) for k in ['hit5','hit10','joint','severe']]
def rate(rows,key):return len(rows)/sum(float(r[key]) for r in rows)
def maxval(rows,key):return max((float(r[key]) for r in rows if r[key]),default=None)


def main():
    frozen();DOC.mkdir(exist_ok=True,parents=True)
    scores=[];old=[];curves=[];cross=[];lengths=[];eq=[];sweeps=[]
    for g in b.GROUPS:
        assert b.read(OUT/(g+'_seal.json'))['predictions']==b.sha(OUT/(g+'.jsonl'))
        scores+=get(OUT/(g+'_scores.csv'));old+=pick(get(OLD/(g+'_scores.csv')),stage='S3')
        curves+=get(OUT/(g+'_curves.csv'));cross+=get(OUT/(g+'_mapping_cross.csv'))
        lengths+=get(OUT/(g+'_lengths.csv')); sweeps+=get(OUT/(g+'_stress.csv'))
        for pl in ['original','bright'] if g=='group_c' else ['original']:
            a=pick(get(OUT/(g+'_parity.csv')),placement=pl)
            eq.append([g,pl,len(a),*[count(a,k) for k in ['field','path','tip','status','registration']]])
    write_csv(OUT/'crack_lengths.csv',lengths)
    a=get(OUT/'synthetic_parity.csv')
    eq.append(['合成','全矩阵',len(a),*[count(a,k) for k in ['field','path','tip','status']],'—'])
    real=[]
    for g,pl,name in SETS:
        a=pick(old,group=g,placement=pl,state='VISIBLE')
        real.append(['V5.13',name,len(a),*summary(a)])
        for stage in b.ALGS:
            a=pick(scores,group=g,placement=pl,stage=stage,state='VISIBLE')
            real.append([stage,name,len(a),*summary(a)])
    real_table=table(['阶段','数据','可见','Hit@5','Hit@10','Joint','Severe'],real)
    synth=get(OUT/'paired_probes.csv');baseline_synth=pick(get(OLD/'paired_probes.csv'),stage='S3')
    def syn_metrics(records,case):
        if case.startswith('全部'):a=pick(records,negative=case=='全部阴性')
        else:a=pick(records,case=case)
        neg=all(r['negative']=='True' for r in a)
        errs=[float(r['error']) for r in a if r['error']]
        return [len(a),*(['—']*4 if neg else [sum(n<=5 for n in errs),sum(n<=10 for n in errs),count(a,'joint'),sum(n>100 for n in errs)]),
                count(a,'passed'),count(a,'valid') if neg else '—']
    cases=sorted({r['case'] for r in synth});syn=[]
    for case in ['全部阴性','全部阳性',*cases]:
        for stage in b.ALGS:syn.append([case,stage,*syn_metrics(pick(synth,stage=stage),case)])
    syn_table=table(['场景','阶段','样本','Hit@5','Hit@10','Joint','Severe','场景通过','误报'],syn)
    focus=[]
    for stage,records in [('V5.13',baseline_synth)]+[(s,pick(synth,stage=s)) for s in b.ALGS]:
        focus.append([stage,*[f"{syn_metrics(records,c)[5]}/{syn_metrics(records,c)[0]}" for c in
            ('active_fork','weak_material_bridge','P1_weak_gap','P6_isolated','P6_deformed_scratch','mouth_glare_arc_only')],
            str(syn_metrics(records,'全部阴性')[-1])+'/468'])
    focus_table=table(['阶段','活动分叉','弱材料桥','弱间断','孤立划痕','变形划痕','反光弧正确拒绝','负样本误报'],focus)
    timings=[];parts=[];speeds={};blocks=[]
    stages=('S1','S2','S3','S4')
    for stage in stages:
        for n in (1,4):
            a=get(OUT/f'bench_{stage}_{n}.csv')
            clock=b.read(OUT/f'bench_{stage}_{n}.json')
            assert len(a)==clock['n']==520
            speeds[stage,n]=(rate(a,'seconds'),rate(a,'detector_seconds'))
            refs={}
            for rec in map(json.loads,(OUT/'three_point_bend.jsonl').open()):
                m=rec['placements']['original'][stage]['full']
                refs[str(rec['frame'])]=(m['tip'],m['status'])
            matched=sum((value(r['tip']),r['status'])==refs[r['frame']] for r in a)
            timings.append([stage,n,520,*map(f,speeds[stage,n]),f(520/clock['wall_seconds']),matched])
            if stage=='S4':
                parts52=[rate(a[j:j+52],'seconds') for j in range(0,520,52)]
                det52=[rate(a[j:j+52],'detector_seconds') for j in range(0,520,52)]
                blocks.append([n,len(parts52),f(min(parts52)),f(median(parts52)),f(max(parts52)),sum(v>=4 for v in parts52),
                    f(min(det52)),sum(v>=4 for v in det52)])
            if stage in ('S3','S4'):
                for k,key in [('原灰度纹理与暗谷','sub_gray_ridge'),('有效窗局部配准','sub_registration'),('差分脊与参考先验','sub_diff_ridge_prior'),
                              ('融合与背景','sub_fusion_background'),('桥接与纹理','sub_bridge_texture'),('末端场滤波','sub_tail_filters'),
                              ('种子与模式检查','sub_seeds_and_gate'),('证据场小计（不含局部配准）','fields_ms'),('有符号差分形态','normal_ms'),('上游映射','upstream_ms')]:
                    parts.append(dict(stage=stage,workers=n,part=k,ms=mean(float(r[key]) for r in a)))
    perf=table(['阶段','进程','实帧','含上游映射 FPS','按 V5.13 检测口径 FPS','整池墙钟吞吐 FPS','复现尖端及状态'],timings)
    block_table=table(['S4 进程','连续 52 帧区段','含上游最低 FPS','中位','最高','≥4 的区段','检测最低 FPS','检测 ≥4 的区段'],blocks)
    module_rows=[]
    for name in dict.fromkeys(r['part'] for r in parts):
        a=[next(r['ms'] for r in parts if r['part']==name and r['stage']==s and r['workers']==n) for n in (1,4) for s in ('S3','S4')]
        module_rows.append([name,f(a[0]),f(a[1]),f(a[1]-a[0]),f(a[2]),f(a[3]),f(a[3]-a[2])])
    module_table=table(['模块 ms/帧','单进程 S3','单进程 S4','变化','四进程 S3','四进程 S4','变化'],module_rows)
    write_csv(OUT/'module_times.csv',parts)
    stress=[];stress_short=[]
    for stage in stages:
        for g,pl,name in SETS:
            if g=='group_c' and pl=='original':continue
            rows=pick(sweeps,group=g,direction='left',stage=stage)
            for dx in (0,-50,-100,-150):
                a=pick(rows,delta=dx)
                # Compare per-frame medians with that same frame's unshifted median.
                frame_vals=[];nom_vals=[];hit=0;visible=0;actual=[]
                for i in sorted({r['frame'] for r in a}):
                    aa=pick(a,frame=i);nr=pick(rows,frame=i,delta=0)
                    frame_vals.append(median(float(r['seconds']) for r in aa));nom_vals.append(median(float(r['seconds']) for r in nr))
                    gt=value(pick(scores,group=g,placement=pl,stage=stage,frame=i)[0]['gt'])
                    prediction=value(aa[0]['tip'])
                    if gt:
                        visible+=1;hit+=int(prediction is not None and math.dist(prediction,gt)<=10)
                    actual.append(float(aa[0]['actual_dx']))
                dr=[float(r['drift']) for r in a if r['drift']]
                ms=1000*median(frame_vals);ratio=np.divide(frame_vals,nom_vals)
                item=[stage,name,dx,f(min(actual))+' … '+f(max(actual)),sum(pick(a,frame=i)[0]['exact_request']=='True' for i in {r['frame'] for r in a}),
                      len(frame_vals),f(np.median([float(r['map_pixels']) for r in a])),f(np.median([float(r['field_pixels']) for r in a])),
                      f(ms),f(1000/ms),f(median(ratio)),f(np.percentile(ratio,95)),f(max(dr,default=None)),len({r['frame'] for r in a if r['drift']}),
                      sum(any(r['status_change']=='True' for r in pick(a,frame=i)) for i in {r['frame'] for r in a}),f'{hit}/{visible}']
                stress.append(item)
                if stage=='S4' and dx in (0,-150):stress_short.append(item)
    stress_table=table(['阶段','组','请求 dx','实际平均 dx 范围','足额移动帧','抽样帧','映射像素中位数','证据场像素中位数','ms 中位数','对应 FPS','配对耗时比 P50','P95','最大漂移 px','两端有效帧','状态改变帧','Hit@10'],stress)
    shift_text='；'.join(item[1]+'足额移动 '+str(item[4])+'/'+str(item[5])+' 帧，耗时比中位数 '+item[10]+'，最大尖端漂移 '+item[12]+' px，状态变更 '+str(item[14])+' 帧' for item in stress_short if item[2]==-150)+'。'
    roi_links=' · '.join(link(OUT/'pressure_views'/f'{g}_{i}.jpg',name+'左移点位与计算窗') for g,i,name in [('group_a',398,'开发组A'),('three_point_bend',248,'三点弯'),('group_c',335,'验证组C亮区')])
    jitter=[]
    for i in ('84','248'):
        for st in stages:
            a=[r for r in pick(sweeps,group='three_point_bend',frame=i,stage=st) if r['direction']!='left']
            jitter.append([i,st,len({(r['delta'],r['direction']) for r in a}),f(maxval(a,'drift')),count(a,'status_change')])
    jitter_table=table(['三点弯帧','阶段','常规扰动数','最大漂移 px','状态改变次数'],jitter)
    historical=get(OUT/'v513_left.csv')
    source_comparison=[]
    for g,i in [('group_a',398),('three_point_bend',248),('group_c',335)]:
        for dx in (0,-50,-100,-150):
            prev=[r for r in pick(historical,group=g,frame=i,delta=dx) if r['repeat']!='0']
            new=pick(sweeps,group=g,stage='S4',frame=i,direction='left',delta=dx)
            source_comparison.append([g,i,dx,f(float(prev[0]['actual_dx'])),prev[0]['pixels'],new[0]['map_pixels'],
                f(median(float(r['total_ms']) for r in prev)),f(1000*median(float(r['seconds']) for r in new)),
                prev[0]['tip'],new[0]['tip']])
    legacy_table=table(['固定帧','序号','请求 dx','实际 dx','V5.13 映射像素','S4 映射像素','V5.13 整链 ms','S4 整链 ms','旧尖端','新尖端'],source_comparison)
    dll=[]
    for a in get(OUT/'v512_dll_left.csv'):
        if a['repeat']!='0':dll.append(a)
    dll_rows=[]
    for g in ('group_a','three_point_bend'):
        for dx in (0,-50,-100,-150):
            a=pick(dll,group=g,dx=dx)
            dll_rows.append([g,a[0]['frame'],dx,f(median(float(r['create_ms']) for r in a)),f(median(float(r['process_ms']) for r in a)),a[0]['tip']])
    dll_table=table(['已发布 V5.12 DLL','帧','左移 px','Create 中位 ms','Process 中位 ms','尖端'],dll_rows)
    dll_note='现有 V5.12 DLL 在三点弯 248 的 Process 中位耗时从 292.69 ms 变为 299.81 ms（左移 150 px），端点却从 (1519, 2733) 跳到 (1634, 2722)。开发组A 398 从 71.03 ms 变为 74.93 ms，端点相同。这两张固定帧没有复现明显的耗时跃升，现场卡顿的原因仍待现场帧及调用计时验证。'
    target=[];fail=[];audit=[];cross_rows=[]
    for g,pl,name in SETS:
        for a in pick(scores,stage='S4',group=g,placement=pl,state='VISIBLE'):
            i=a['frame'];gt=value(a['gt'])
            stagescores=[pick(old,frame=i,group=g,placement=pl)[0]]+[pick(scores,frame=i,group=g,placement=pl,stage=st)[0] for st in stages]
            notable=int(i) in {'group_a':(398,504),'three_point_bend':(84,215,248,335,413,435,503),'group_c':(38,324,335,345,510)}[g]
            if notable or a['joint']!=stagescores[0]['joint']:
                target.append([name,i,*[f(x['error_px']) for x in stagescores],f(a['dx']),f(a['coverage']),f(a['precision']),a['joint']])
            if a['joint']=='True':continue
            group=pick(curves,frame=i,group=g,placement=pl,stage='S4')
            branches=[];near=[]
            for c in group:
                tip=value(c['tip']);d=value(c['details']) or {};err=math.dist(tip,gt) if tip else None
                if err is not None:near.append((err,c['branch'],c['reason']))
                branches.append([c['branch'],c['winner'],c['reason'],f(err),f(c['initial']),f(c['merit']),d.get('dual_columns','—'),
                                 f(d.get('red')),f(d.get('blue')),f(d.get('tail_cost')),f(d.get('geometry_cost'))])
            cause='没有产生有效尖端，最终裁决为 '+a['stop']+'。' if not a['error_px'] else ('端点进入 10 px，路径覆盖率或精确率低于 80%。' if a['hit10']=='True' else
                ('存在端点命中的备选分支，最终排序或门控没有选择它。' if near and min(near)[0]<=10 else '各已回溯分支的端点均超出 10 px。'))
            progression=' → '.join(f(x['error_px']) for x in stagescores)
            if a['dx']:cause+=f" 横向偏移 {float(a['dx']):+.2f} px，纵向偏移 {float(a['dy']):+.2f} px。"
            combos=pick(cross,group=g,placement=pl,frame=i)
            ce=[]
            for c in combos:
                tip=value(c['tip']);ce.append([c['engine'],c['mapping'],c['source'],c['shift'],f(math.dist(gt,tip) if tip else None)])
            img=OUT/'audit_views'/f'{g}_{pl}_{int(i):04d}.jpg'
            audit+=['### '+name+' · 第 '+i+' 帧',cause+' V5.13、S1、S2、S3、S4 的尖端误差依次为 '+progression+' px。',
                    link(img,'四联对比与各分支 V(x) 曲线'),
                    table(['分支','胜出','裁决','尖端误差 px','入口静态分','最终分','双一致列','红证据','蓝证据','末端扣分','转移几何扣分'],branches) if branches else '没有可回溯候选。',
                    table(['局部算法','上游映射','证据源','局部平移','尖端误差 px'],ce)]
            fail.append(dict(group=g,placement=pl,frame=i,error_px=a['error_px'],reason=cause,trajectory=progression))
    write_csv(OUT/'failure_index.csv',fail)
    target_table=table(['组','帧','V5.13','S1','S2','S3','S4 误差 px','S4 dx','覆盖率','精确率','Joint'],target)
    for g,pl,name in SETS:
        a=pick(cross,group=g,placement=pl)
        keys={(r['frame'],r['engine'],r['mapping']):r['tip'] for r in a}
        ids=sorted({r['frame'] for r in a})
        left=lambda u,v:sum(keys[i,*u]!=keys[i,*v] for i in ids)
        cross_rows.append([name,len(ids),left(('V5.13','旧'),('V5.13','新')),left(('V5.13','旧'),('V5.14-S1','旧')),left(('V5.13','旧'),('V5.14-S1','新'))])
    cross_table=table(['组','标注帧','只换上游映射后端点变化','只换局部算法后变化','两者都换后变化'],cross_rows)
    fps='三点弯完整 520 帧，S4 单进程与四进程每进程速度分别为 '+f(speeds['S4',1][0])+'、'+f(speeds['S4',4][0])+' FPS。按 V5.13 仅检测的口径分别为 '+f(speeds['S4',1][1])+'、'+f(speeds['S4',4][1])+' FPS。'
    results='，'.join(name+' '+str(count(pick(scores,stage='S4',group=g,placement=pl,state='VISIBLE'),'joint'))+'/'+str(len(pick(scores,stage='S4',group=g,placement=pl,state='VISIBLE'))) for g,pl,name in SETS)
    halo=get(OUT/'halo_curve_audit.csv')
    halo_rows=[[r['group'],r['frame'],r['placement'],r['branch'],f(r['new_tip_x_minus_gt']),r['reaches_gt_x'],
        f(r['old_peak_charge']),f(r['gt_column_charge']),f(r['new_peak_over_gt'])] for r in halo if r['winner']=='True' and
        (int(r['frame']) in {'group_a':(113,299,366,398,504),'three_point_bend':(215,248,335,381,413,435,503),'group_c':(38,510)}[r['group']])]
    halo_table=table(['组','帧','点位','分支','S2 横向误差','曲线到达标注 x','旧终点扣分','标注列扣分','新峰超过标注列分值'],halo_rows)
    scratch_rows=[]
    for c in ('P6_isolated','P6_deformed_scratch','weak_material_bridge'):
        for n,src in [('V5.13',baseline_synth),('S4',pick(synth,stage='S4'))]:
            a=pick(src,case=c)
            scratch_rows.append([n,c,len(a),count(a,'passed'),f(median(float(r['error']) for r in a if r['error'])),
                f(median(float(r['precision']) for r in a)),f(median(float(r['coverage']) for r in a))])
    scratch=table(['阶段','场景','样本','场景通过','端点误差中位数','路径精确率中位数','覆盖率中位数'],scratch_rows)
    precision='S4 联合命中为'+results+'。验证组C两种点位属于同一组标注。'
    neg=pick(synth,stage='S4',negative=True,valid=True)
    fp='负样本误报 '+str(len(neg))+'/468，其中 '+', '.join(k+' '+str(v)+' 次' for k,v in Counter(r['case'] for r in neg).items())+'。'
    method='S1 保留 V5.13 的顶点定位和 288 px 特征尺度。点对距离继续用于上游几何，点对负责粗定位。顶点确定后，上游映射、纹理窗和特征左边界钳位在顶点前约 0.08 个特征尺度。局部 NCC 仅在有限的材料窗内计算，待搜索的参考邻域须通过亮度与有效性检查；匹配不足时使用有界缺口轮廓。S1 同时收紧纵向搜索带，这两项变化可能改变旧版输出。'
    algo='S2 在末段比较窄暗谷与宽暗谷、相对先前暗谷深度的衰减，将最近窗口的扣分从端点曲线中减去。S3 在每个方向状态保存入射切向、弱支撑长度和横向残差，转移发生在剪枝前，并对邻近蓝带的错位延伸增加扣分。短路径通过双一致豁免时再检查口门亮度和转角。S4 将部分逐像素融合限制在有效行、合并正负通道局部均值，并用未来得分上界安全剪枝。仍须在完整上下文计算分位数、滤波边缘及参考风险场。'
    protocol='开发组A用于开发；三点弯和验证组C仅作冻结后验证，排除组X排除。人工标注仅用于离线评分。Hit@5/10 表示端点误差不超过 5/10 px；Joint 还要求路径覆盖率和精确率均 ≥80%；Severe 为可见帧中有预测且误差 >100 px。无预测计入可见分母。合成误差按倍率归一，场景通过采用原探针的路径条件。'
    time_note='每个进程使用单线程 OpenCV、BLAS 与 OMP。各计时组合独立运行完整序列；首轮预热不计。含上游映射的 FPS 用帧数除以准备、上游和检测的累计秒数；检测口径排除上游，整池吞吐包含原图读入、校验和传输。各子步骤取全部 520 帧均值，未进入的分支计为零。S3 与 S4 按顺序各测一轮，耗时差还可能包含系统负载波动。4.0 FPS 为下限，4.5 FPS 为目标。'
    stress_note='从原始帧重新裁剪、配准与检测，参考和当前点对同步沿图像 x 轴平移。每组三个按序号预选的帧重复三次，其余一次，轮换位移测试顺序。耗时比按同一帧、同一阶段相对零位移计算，1.00 表示同速；每帧先取中位数。漂移只统计前后均有预测的帧，状态改变单列。验证组C亮区约束会修正请求位置，足额移动要求两点各坐标均与请求相差小于 0.01 px。'
    parity_table=table(['组','点位','对照数','净场哈希相同','路径逐点相同','端点相同','状态相同','局部映射参数相同'],eq)
    false_replay=get(OUT/'negative_replay.csv')
    fp_table=table(['场景','倍率','噪声','种子','光照','阶段','配准来源','平移','证据模式','裁决','入口分','双一致列','尖端'],
        [[r[k] or '—' for k in ('case','zoom','noise','seed','photo','stage','reference','shift','source','stop','initial','dual','tip')] for r in false_replay])
    core=['## S1–S4 真实帧消融',real_table,'## S1–S4 关键合成验收',focus_table]
    findings='验证组C 38 的候选在 S2 已达到 0.64 px；进入 S3 后，同一候选被口门反光弧校验拒绝，亮区 54 也出现相同拒绝。合成反光弧在 S1 已全部正确拒绝，这份数据没有显示额外口门校验的净收益。三点弯 215 和 248 保住了 Joint；335、413、435 的端点在 S2 仍落在原峰。'
    tail_findings='开发组A 398 的旧峰确实被扣分，但新峰仍比标注尖端所在列高约 6.28 分，端点没有回收。504 的候选在到达标注列前已结束，S2 使其再短 1 px。开发组A 113、299、366 的端点则从命中转为偏短；统一提高末端扣分会同时伤及真实细裂纹。'
    conclusion='建议保留 S1 的缺口裁剪和 S4 的等价算子作为独立工程改动。口门反光判据需要能区分同样亮、同样弯曲的真实新生裂纹；跨跳代价须先在 0.5× 与 2× 的同几何合成对上稳定，再确定是否进入识别主线。'
    resources=' · '.join([link(OUT/'difference_views/index.html','1,633 帧图册、差分图与三组视频'),link(OUT/'crack_lengths.csv','逐帧尖端与裂纹长度'),link(DOC/'FAILURES_AUDIT.md','失败审计'),link(OUT/'freeze.json','冻结指纹')])
    write('REPORT.md',['# V5.14 基准点与 ROI 解耦验证','## 结论','本轮未通过替换验收。'+precision+fp+fps,
        '## 方法与数据',method,algo,protocol,*core,'## 目标帧与变化',target_table,findings,tail_findings,
        '## 基准点左移',stress_note,'S4 左移 150 px 的结果为'+shift_text,stress_table,roi_links,legacy_table,'三点弯常规点对平移、间距扰动的复测结果如下。',jitter_table,
        '## 已发布动态库实测','通过已交付的 V5.12 CrackV4.dll 的 Create 和 Process 入口运行相同原始实验帧，四种左移各测四次，表中丢弃第一轮。此表可用于对照现场症状。V5.14 的时间来自研究实现。',dll_table,dll_note,
        '## 全序列速度与证据场拆分',time_note,perf,block_table,module_table,'## S3 与 S4 的有效区域等价性',parity_table,
        '## 全部合成矩阵',syn_table,'## 开发判断',conclusion,'## 交付文件',resources])
    write('FAILURES_AUDIT.md',['# V5.14 失败帧与耗时审计',precision+fp,protocol,*core,
        '## 重点帧',target_table,findings,tail_findings,'## 上游与局部算法交叉回放','对原始与亮区点位分别交叉运行 V5.13 / S1 局部算法和旧 / 新上游映射，表中统计最终端点变化帧数。',cross_table,
        '## 基准点左移与速度',stress_note,'S4 左移 150 px 的结果为'+shift_text,stress_table,roi_links,legacy_table,jitter_table,dll_table,dll_note,'## 证据场拆分',time_note,perf,block_table,module_table,
        '## 末端校准的因果对照','S1 和 S2 使用同一 DP 提议路线；表中扣分来自同一分支同一列的累计曲线差。曲线未到人工尖端的 x 坐标时，单纯改变末端扣分无法延长该提议。',halo_table,link(OUT/'halo_curve_audit.csv','所有标注帧各候选的曲线扣分'),'## 合成反例',scratch,fp,fp_table,table(['反例','倍率','噪声','光照','种子','端点'],[[r['case'],r['zoom'],r['noise'],r['photo'],r['seed'],r['tip']] for r in neg]),
        table(['S4 场景','0.5× 通过','1× 通过','2× 通过'],[[c,*[str(count(pick(synth,stage='S4',case=c,zoom=z),'passed'))+'/12' for z in ('0.5','1.0','2.0')]] for c in ('P6_isolated','P6_deformed_scratch','weak_material_bridge','active_fork','mouth_glare_arc_only')]),
        '## 所有可见 Joint 失败帧',*audit,'## 完整记录',link(OUT/'paired_probes.csv','全部 5,616 次合成输出')+' · '+link(OUT/'failure_index.csv','实帧失败索引')])
    print(precision,fp,fps,flush=True)

if __name__=='__main__':main()
