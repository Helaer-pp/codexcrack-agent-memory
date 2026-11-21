"""Publish paired ablations, curve evidence, speed and sensitivity after sealing."""
import ast
import json
import math
import os
from collections import Counter
from pathlib import Path
from statistics import mean, median
from research.v3_labelme_comparison.compare import write_csv
from research.notch_identity_v512.report import table
from .batch import ROOT, OUT, GROUPS, read, read_csv, sha
from .run import frozen

DOC=ROOT/'evidence/v5_13'
DATA=(('group_a','original','开发组A'),('three_point_bend','original','三点弯'),('group_c','original','验证组C原点'),('group_c','bright','验证组C亮区'))
STAGES=('S1','S2','S3')
PREV=OUT.parent/'v512_stabilize_r01'
def link(path,label):
    return f'[{label}]({Path(os.path.relpath(path,DOC)).as_posix()})'
def f(x):return '—' if x in ('',None) else f'{float(x):.2f}'
def count(rows,key):return sum(r[key]=='True' for r in rows)
def rate(rows):return f(len(rows)/sum(float(r['seconds']) for r in rows))
def select(rows,**keys):return [r for r in rows if all(r[k]==v for k,v in keys.items())]
def statistics(rows):return [count(rows,k) for k in ('hit5','hit10','joint','severe')]
def write(name,lines):
    (DOC/name).write_text('\n\n'.join(lines)+'\n',encoding='utf8')


def main():
    frozen(); DOC.mkdir(exist_ok=True,parents=True)
    scores=[]; lengths=[]; candidates=[]; parity=[]; jit=[]; benchmarks=[]; profiles=[]
    for g in GROUPS:
        scores+=read_csv(OUT/(g+'_scores.csv'))
        lengths+=read_csv(OUT/(g+'_lengths.csv'))
        candidates+=read_csv(OUT/(g+'_curves.csv'))
        comp=read_csv(OUT/(g+'_parity.csv'))
        maps=read_csv(OUT/(g+'_reference_parity.csv'))
        for pl in sorted({r['placement'] for r in comp}):
            a=select(comp,placement=pl)
            parity.append([g,pl,len(a),count(a,'status'),count(a,'tip'),count(a,'path'),count(a,'registration'),count(a,'field'),count(a,'field_present'),sum(int(r['pixels']) for r in select(maps,placement=pl)),count(select(maps,placement=pl),'equal')])
        for mode,file in [('固定映射','jitter'),('重裁剪重配准','native_jitter')]:
            records=read_csv(OUT/(g+'_'+file+'.csv'))
            for stage in STAGES:
                rows=[r for r in select(records,stage=stage) if float(r['delta'])!=0]
                ds=[r for r in rows if r['drift']]
                worst=max(ds,key=lambda r:float(r['drift']),default={})
                jit.append([g,mode,stage,len(rows),len(ds),count(rows,'status_change'),f(max((float(r['drift']) for r in ds),default=None)),worst.get('frame','—')])
    write_csv(OUT/'crack_lengths.csv',lengths)
    visible=select(scores,state='VISIBLE')
    old=[]
    for g in GROUPS:old+=select(read_csv(PREV/(g+'_scores.csv')),stage='S4',mode='full',state='VISIBLE')
    speed={n:read_csv(OUT/f'labeled_speed_{n}.csv') for n in (1,4)}
    real=[]
    for stage in STAGES:
        for g,pl,name in DATA:
            rows=select(visible,stage=stage,group=g,placement=pl)
            key=dict(stage=stage,group=g,placement=pl)
            real.append([stage,name,len(rows),*statistics(rows),*[rate(select(speed[n],**key)) for n in (1,4)]])
    realtable=table(['阶段','组及点位','可见','Hit@5','Hit@10','Joint','Severe','单进程 FPS','四进程每进程 FPS'],real)
    for stage in STAGES:
        for n in (1,4):
            speedrow=read(OUT/f'bench_{stage}_{n}.json')
            a=read_csv(OUT/f'bench_{stage}_{n}.csv')
            assert len(a)==speedrow['n']==520
            refs={}
            for rec in map(json.loads,(OUT/'three_point_bend.jsonl').open()):
                m=rec['placements']['original'][stage]['full']
                refs[str(rec['frame'])]=(m['tip'],m['status'])
            matched=sum((ast.literal_eval(r['tip']) if r['tip'] else None,r['status'])==refs[r['frame']] for r in a)
            benchmarks.append([stage,n,520,rate(a),f(520/speedrow['wall_seconds']),matched])
            profiles.append([stage,n,*[f(mean(float(r[k]) for r in a)) for k in ('fields_ms','registration_ms','normal_ms')],
                            f(1000*mean(float(r['seconds']) for r in a))])
    timings=table(['阶段','进程','帧','每进程算法 FPS','含缓存文件读入的总吞吐 FPS','端点与状态复现'],benchmarks)
    modules=table(['阶段','进程','证据场（扣除配准）ms','局部配准 ms','差分形态 ms','检测合计 ms'],profiles)
    synth=read_csv(OUT/'paired_probes.csv'); synth_rows=[]
    ss={n:read_csv(OUT/f'synthetic_speed_{n}.csv') for n in (1,4)}
    cases=sorted({r['case'] for r in synth})
    for stage in STAGES:
        for case in ['全部阴性','全部阳性',*cases]:
            keys=dict(stage=stage)
            if case.startswith('全部'):keys['negative']='True' if case=='全部阴性' else 'False'
            else:keys['case']=case
            a=select(synth,**keys)
            errors=[float(r['error']) for r in a if r['error']]
            neg=all(r['negative']=='True' for r in a)
            metrics=['—']*4 if neg else [sum(x<=5 for x in errors),sum(x<=10 for x in errors),count(a,'joint'),sum(x>100 for x in errors)]
            synth_rows.append([stage,case,len(a),*metrics,count(a,'passed'),count(a,'valid') if neg else '—',
                              *[rate(select(ss[n],**keys)) for n in (1,4)]])
    syntable=table(['阶段','场景','样本','Hit@5','Hit@10','Joint','Severe','场景通过','误报','单进程 FPS','四进程每进程 FPS'],synth_rows)
    gates=[]
    def stagecase(stage,gt,pl,frame):
        row=select(visible,stage=stage,group=gt,placement=pl,frame=str(frame))[0]
        return ('命中' if row['joint']=='True' else '失败')+' / '+f(row['error_px'])
    for st in STAGES:
        cases13=[select(synth,stage=st,case=k) for k in ('P6_isolated','weak_material_bridge','P1_weak_gap')]
        gates.append([st,stagecase(st,'three_point_bend','original',215),stagecase(st,'three_point_bend','original',248),
                      stagecase(st,'group_c','bright',38),*[f"{count(a,'passed')}/{len(a)}" for a in cases13],
                      str(count(select(synth,stage=st,negative='True'),'valid'))+'/468'])
    gate_table=table(['阶段','三点弯 215 Joint / 误差','三点弯 248 Joint / 误差','验证组C 38 Joint / 误差','孤立划痕通过','材料桥接通过','弱间断通过','负样本误报'],gates)
    changes=[]
    for g,pl,name in DATA:
        for a in select(visible,group=g,placement=pl,stage='S3'):
            before=select(old,group=g,placement=pl,frame=a['frame'])[0]
            if a['frame'] in {'38','215','248','324','335','345','510','398'} or a['joint']!=before['joint']:
                changes.append([name,a['frame'],f(before['error_px']),f(a['error_px']),f(a['dx']),f(100*float(a['coverage'])),f(100*float(a['precision'])),before['joint'],a['joint'],a['pick']])
    cases_table=table(['组别','帧','V5.12 误差 px','V5.13 误差 px','横向误差 px','覆盖率 %','精确率 %','原 Joint','现 Joint','胜出分支'],changes)
    sections=[]; failure_index=[]
    for g,pl,name in DATA:
        for row in select(visible,group=g,placement=pl,stage='S3'):
            if row['joint']=='True':continue
            i=row['frame'];gt=ast.literal_eval(row['gt'])
            branches=select(candidates,group=g,placement=pl,stage='S3',frame=i)
            gated=[]; cr=[]
            for item in branches:
                info=ast.literal_eval(item['details']) if item['details'] else {}
                dist=math.dist(ast.literal_eval(item['tip']),gt) if item['tip'] else None
                if dist is not None:gated.append((dist,item['branch'],item['reason']))
                cr.append([item['branch'],item['winner'],item['reason'],f(item['initial']),f(item['merit']),f(dist),info.get('dual_columns','—'),f(info.get('red')),f(info.get('blue')),f(info.get('geometry_cost')),info.get('max_blank','—'),f(info.get('drawdown'))])
            if row['hit10']=='True':
                reason='尖端在 10 px 内，路径'+('覆盖率' if float(row['coverage'])<.8 else '精确率')+'低于 80%。'
            elif not row['error_px']:
                reason='没有分支取得有效尖端。终止原因为 '+row['stop']+'。'
            elif gated and min(gated)[0]<=10:
                near=min(gated)
                reason=f'分支 {near[1]} 的端点距标注 {near[0]:.2f} px，候选状态 {near[2]}，最终选择 {row["pick"]}。'
            elif gated:
                reason=f'记录的各分支峰都未进入 10 px 邻域；最近峰距标注 {min(gated)[0]:.2f} px。'
            else:reason='没有记录到可达的候选峰。'
            if row['dx']:
                dx=float(row['dx']);dy=float(row['dy'])
                reason+=f' 当前坐标相对标注偏移 ({dx:+.2f}, {dy:+.2f}) px。'
            sections+=['### '+name+' · 第 '+i+' 帧',link(OUT/'audit_views'/f'{g}_{pl}_{int(i):04d}.jpg','参考、当前、路径、差分和各分支 V(x) 曲线'),
                f'尖端误差 {f(row["error_px"])} px，覆盖率 {f(row["coverage"])}，精确率 {f(row["precision"])}。{reason}',
                table(['分支','胜出','裁决','静态分','最终分','端点误差','双一致列','红脊和','蓝带和','几何代价','最长空档','V 最大回撤'],cr) if cr else '未形成可回溯分支。']
            failure_index.append(dict(group=g,placement=pl,frame=i,error_px=row['error_px'],pick=row['pick'],reason=reason))
    write_csv(OUT/'failure_index.csv',failure_index)
    drift248=select(read_csv(OUT/'three_point_bend_native_jitter.csv'),stage='S3',frame='248')
    worst248=max((float(r['drift']) for r in drift248 if r['drift']),default=None)
    drift84=select(read_csv(OUT/'three_point_bend_native_jitter.csv'),stage='S3',frame='84')
    p84=max((r for r in drift84 if r['drift']),key=lambda r:float(r['drift']))
    summary=[]
    for g,pl,name in DATA:
        a=select(visible,group=g,placement=pl,stage='S3')
        pre=select(old,group=g,placement=pl)
        summary.append(f"{name} {count(pre,'joint')} → {count(a,'joint')}/{len(a)}")
    outcome='V5.12 至 V5.13 的 Joint 命中数为'+'，'.join(summary)+'。'
    falsepos=select(synth,stage='S3',negative='True',valid='True')
    highlight=f'三点弯 248 重裁剪重配准最大漂移 {f(worst248)} px。合成负样本误报 {len(falsepos)}/468。'
    highlight+=f" 三点弯 84 在点对轴向平移 {p84['delta']} px 后仍有 {float(p84['drift']):.2f} px 漂移。"
    common=[realtable,'真实图像沿用原图欧氏尖端误差。Joint 要求 Hit@10 且路径覆盖率和精确率均 ≥80%。Severe 为有尖端且误差 >100 px。无尖端的可见帧计入命中分母。每组各取 20 帧，未确定尖端的帧只保留记录。验证组C两种点位来自同一序列。']
    perf_note='工作进程均使用 OpenCV 单线程，启动数值库前将 OMP、MKL、OpenBLAS 等线程数设为 1。各阶段按同一线程设置配对测量，此对照用于隔离 S3 算子实现的影响。每进程算法 FPS 用帧数除以各次检测累计秒数。三点弯 520 帧以独立的单进程池、四进程池顺序测量，采用相同上游缓存；计时覆盖 ROI 准备、局部配准及检测。总吞吐另含证据缓存校验、解码与进程间传输。已提供上游映射，原图读入、上游映射重建及视频渲染不计入算法 FPS。'
    s3bench=[r for r in benchmarks if r[0]=='S3']
    perf_result='S3 在三点弯完整序列的单进程 / 四进程每进程速度为 '+' / '.join(r[3] for r in s3bench)+' FPS。单进程达到 4.0 FPS，四进程下的每进程速度低于门槛。四进程证据场仍耗时约 135 ms，局部配准约 30 ms。'
    effects=[]
    for n in (1,4):
        a,e=[next(r for r in profiles if r[:2]==[v,n]) for v in ('S2','S3')]
        effects.append([n,*[f(float(y)-float(x)) for x,y in zip(a[2:],e[2:])]])
    speed_delta=table(['进程数','证据场变化 ms','配准变化 ms','形态变化 ms','检测总耗时变化 ms'],effects)
    change_text='S1 从缺口种子启动方向状态 DP，以差分细红脊、当前暗谷和有限的 V5.12 先验累计得分。高亮且低对比处降低空档扣分，蓝带和远离缺口切向的连接增加代价。沿候选累计曲线取最大值为端点。S2 向双一致 ≥8 列且净分为正的路径开放静态分门槛，直接用净分排序。S3 复用薄脊计算缓冲，跳过全有效 NCC 窗口的缺失像素膨胀与复制，保持上游 S3 几何映射。工作进程显式限制 OpenCV 与 BLAS/OMP 线程。'
    fields=read_csv(OUT/'target_field_audit.csv')
    fieldtable=table(['组','帧','点位','采样线','有效列','V 增量和（几何扣分前）','红强度均值','蓝强度均值','最长非正区','该区反光权重','末 12 列净均值'],
        [[r['group'],r['frame'],r['placement'],r['trace'],r['finite_columns'],f(r['net_sum']),f(r['mean_red']),f(r['mean_blue']),
          r['max_nonpositive_columns'],f(r['gap_reflection']),f(r['tail12_mean'])] for r in fields])
    synthetic_fail=read_csv(OUT/'synthetic_failures.csv')
    physical=[]
    for case in ('P6_isolated','P6_deformed_scratch','P1_weak_gap'):
        bad=select(synthetic_fail,case=case)
        def med(key):
            values=[float(r[key]) for r in bad if r[key]]
            return f(median(values)) if values else '—'
        physical.append([case,len(bad),med('dx_normalized'),med('precision'),med('coverage'),med('V_change_from_gt_column')])
    diagnostic_table=table(['失败合成场景','失败数','水平偏移中位数','路径精确率中位数','覆盖率中位数','预测峰 V 减标注尖端列 V 的中位数'],physical)
    lessons='验证组C 38 和三点弯 215 都在开放红脊分支后取得 Joint；三点弯 248 已在 S1 恢复。三点弯 335、413、435 从原先的 Joint 转为末端过追，开发组A 398 与验证组C 510 的过冲仍在。下一轮可在相同缺口种子上比较真裂纹与相邻划痕跨连接区域的累计净增益，同时单独约束末端微红晕的增益。建议先用冻结的合成正负对验证这两个机制，再提交下一轮固定参数回归。'
    engineering='DP 在每列保留方向状态。跨档横向偏移与切向罚分在各入口回溯出的路径上重新累计；因此这部分罚分能改变该路径的终点和分支排序，无法找回回溯前已被剪去的路线。即使同一列覆盖了真尖端，错误分支也可能得到更高累计值。'
    write('REPORT.md',['# V5.13 差分净得分实验','## 验收结论','本轮未达到替换门槛。'+outcome+highlight,gate_table,
        '## 算法与数据',change_text,engineering,'开发组A为开发组。任务书中的 DEV-B（三点弯）与 REG-C（验证组C）均作为冻结后验证。验证组C默认使用冻结亮区，另列原点。人工标注仅用于离线比较。排除组X未进入实验。',*common,
        '## 目标帧和 Joint 变化',lessons,cases_table,'## 三点弯全序列速度',perf_note,perf_result,timings,modules,'下表为 S3 减 S2 的平均耗时，负值表示加快。',speed_delta,
        '## S2 与 S3 等价性',table(['数据','点位','帧','状态相同','端点相同','路径逐点相同','配准相同','净场 SHA 相同（含无场）','有证据场','映射对比像素（含边界）','映射逐像素相同帧'],parity),
        '## 基准点敏感性','每个标注帧测试沿点对轴和法向各平移 ±10/20 px，并将点距改变 ±20%。固定映射与全流程重裁剪重配准分别统计，只在两次均有端点时计漂移。',table(['组','操作','阶段','扰动','可算漂移','状态变更','最大漂移 px','帧'],jit),
        '## 合成矩阵','每阶段包含 936 个阳性、468 个阴性。合成误差除以图像缩放倍率。场景通过沿用原测试定义，P1 要求完整路径覆盖，P6 要求路径精确率至少 95%。',syntable,
        '## 可复核结果',link(OUT/'difference_views/index.html','逐帧参考、当前、路径及差分图与视频')+' · '+link(OUT/'crack_lengths.csv','逐帧根点至尖端弧长与投影长度')+' · '+link(DOC/'FAILURES_AUDIT.md','失败审计')+' · '+link(OUT/'freeze.json','冻结文件指纹')])
    write('FAILURES_AUDIT.md',['# V5.13 失败审计',outcome+highlight,'## S1–S3 消融',gate_table,*common,'## 前端耗时',perf_note,perf_result,modules,speed_delta,timings,
        '## 目标帧的差分证据','三点弯 248 的预测路径跨过 32 列非正净证据，该段反光权重均值接近 0。215 的对应值为 14 列与接近 0。数据支持去除硬锁后远端红脊能补偿前段扣分，尚未验证高光分类本身是恢复的原因。开发组A 398、验证组C 510 的预测路径末 12 列净增量仍平均为正，分别约 0.98、1.76，当前末端基底仍允许过追。灰度和差分无法单独判定该信号的物理来源。','在预测完成后，将原图标注路径与算法路径分别按列重采样到同一 S3 净场。非正区长度描述该采样线经过的背景；沿人工中心线采样受标注误差影响。',fieldtable,'## 合成失败',diagnostic_table,'两类 P6 的路径通常先覆盖真裂纹，再沿划痕继续累计正分。弱间断的失败主要发生在中间路线，即使端点命中仍达不到完整覆盖要求。',link(OUT/'synthetic_failures.csv','逐条失败合成输入、候选与 V 曲线'),'S3 的孤立划痕、变形划痕和弱间断场景可在下表核对。P6 逐条记录包含路径覆盖率与精确率，P1 即使端点命中也可能走错中间路径。',
        table(['场景','错误或漏检数','无端点','预测端点 >10 px','有端点且精确率 <95%'],[[case,len(bad),sum(not r['error'] for r in bad),sum(float(r['error'])>10 for r in bad if r['error']),sum(r['valid']=='True' and float(r['precision'])<.95 for r in bad)] for case in ['P6_isolated','P6_deformed_scratch','P1_weak_gap'] for bad in [[r for r in select(synth,stage='S3',case=case) if r['passed']!='True']]]),
        '负样本误报条件：'+'；'.join(f"{r['case']}，倍率 {r['zoom']}，噪声 {r['noise']}，种子 {r['seed']}，光照 {r['photo']}" for r in falsepos),
        '## 实帧审计','以下逐帧覆盖 S3 的每个可见 Joint 失败。详细 CSV 中保留 S1–S3 候选完整 V(x) 数列。静态或无增量模式不产生双一致曲线，表中显示为空。候选端点距标注仅供离线定位。',
        *[link(OUT/(g+'_curves.csv'),g+' 各分支曲线') for g in GROUPS],*sections])
    print(outcome,highlight,benchmarks,flush=True)


if __name__=='__main__':main()
