"""Publish frozen score tables and per-frame failure explanations."""
import json
import os
from statistics import mean
from pathlib import Path
from .batch import GROUPS, ROOT, OUT, read, read_csv, sha, sources
from research.v3_labelme_comparison.compare import write_csv

DOC=ROOT/'evidence/v5_11'
PREV=OUT.parent/'v510_vertex_r02'
STAGES=('S1','S2','S3','S4')
NAMES={'group_a':'开发组A','three_point_bend':'三点弯','group_c':'验证组C'}
def link(p,title=None):
    p=Path(p)
    return f"[{title or p.name}]({Path(os.path.relpath(p,DOC)).as_posix()})"
def table(header,rows):
    def line(items):return '| '+' | '.join(str(i) for i in items)+' |'
    return '\n'.join([line(header),line(['---']*len(header)),*map(line,rows)])
def f(x):
    return f'{float(x):.2f}' if x not in (None,'') else '—'
def n(rows,key):
    return sum(r[key]=='True' for r in rows)
def rate(rows,key):
    return f(len(rows)/sum(float(r[key]) for r in rows)) if rows else '—'
def main():
    DOC.mkdir(exist_ok=True,parents=True)
    assert read(OUT/'freeze.json')['sources']==sources()
    records={}; scores=[]; lengths=[]; allrows=[]
    for g in GROUPS:
        assert read(OUT/(g+'_seal.json'))['predictions']==sha(OUT/(g+'.jsonl'))
        picked=read_csv(OUT/(g+'_scores.csv'));scores+=picked
        lengths+=read_csv(OUT/(g+'_lengths.csv'))
        sel={int(r['frame']) for r in picked}
        for rec in map(json.loads,(OUT/(g+'.jsonl')).open()):
            i=rec['frame']
            if i in sel:records[g,i]=rec
            for p,models in rec['placements'].items():
                for s,b in models.items():
                    allrows.append(dict(group=g,placement=p,stage=s,seconds=b['seconds'],raw_seconds=b['raw_seconds']))
    write_csv(OUT/'crack_lengths.csv',lengths)
    mainrows=[];speedrows=[];result={}
    for s in STAGES:
        for g,pl in [('group_a','original'),('three_point_bend','original'),('group_c','original'),('group_c','bright')]:
            a=[r for r in scores if (r['group'],r['placement'],r['stage'],r['mode'])==(g,pl,s,'full')]
            v=[r for r in a if r['state']=='VISIBLE']
            seq=[r for r in allrows if (r['group'],r['placement'],r['stage'])==(g,pl,s)]
            name=NAMES[g]+(' 亮区' if pl=='bright' else ' 原点' if g=='group_c' else '')
            mainrows.append((s,name,len(v),n(v,'hit5'),n(v,'hit10'),n(v,'joint'),n(v,'severe'),rate(a,'seconds')))
            if s=='S4':
                result[name]=n(v,'joint')
                speedrows.append((name,len(seq),rate(seq,'seconds'),rate(seq,'raw_seconds')))
    real=table(['阶段','数据及点位','可见','Hit@5','Hit@10','Joint','Severe','20 帧 full FPS'],mainrows)
    speed=table(['组别','序列帧','full FPS','raw_only FPS'],speedrows)
    probes=read_csv(OUT/'paired_probes.csv'); synth=[]
    for s in STAGES:
        a=[r for r in probes if r['stage']==s]
        for case in ['全部阳性','P1_weak_gap','weak_material_bridge','active_fork','全部阴性']:
            b=[r for r in a if r['negative']==('True' if case=='全部阴性' else 'False')] if case.startswith('全部') else [r for r in a if r['case']==case]
            errs=[float(r['error']) for r in b if r['error']]
            neg=case=='全部阴性'
            synth.append((s,case,len(b),*(['—']*4 if neg else [sum(x<=5 for x in errs),sum(x<=10 for x in errs),n(b,'joint'),sum(x>100 for x in errs)]),n(b,'passed'),n(b,'valid') if neg else '—',rate(b,'seconds')))
    syn=table(['阶段','合成类别','样本','Hit@5','Hit@10','Joint','Severe','场景验收通过','误报','FPS'],synth)
    sens=[]
    for g in GROUPS:
        for file,label in [('jitter','固定配准'),('native_jitter','重裁剪重配准')]:
            rows=[r for r in read_csv(OUT/(g+'_'+file+'.csv')) if float(r['delta'])!=0]
            valid=[r for r in rows if r['drift']];maxrow=max(valid,key=lambda r:float(r['drift']),default={})
            vis={r['frame'] for r in scores if r['group']==g and r['state']=='VISIBLE'}
            vm=max([float(r['drift']) for r in valid if r['frame'] in vis],default=0)
            changed=sum(r['status_change']=='True' for r in rows) if file=='native_jitter' else sum(bool(r['baseline_tip'])!=bool(r['tip']) for r in rows)
            sens.append((NAMES[g],label,len(rows),len(valid),changed,f(maxrow.get('drift')),maxrow.get('frame','—'),f(vm)))
    jitter=table(['组别','输入','扰动数','双端点可比','状态/有无变化','最大漂移 px','对应帧','可见帧最大 px'],sens)
    target=[]
    for g,frames in [('group_a',[299]),('three_point_bend',[215,248,306,413,435]),('group_c',[1,7,38,54])]:
        for i in frames:
            for pl in records[g,i]['placements'] if (g,i) in records else ():
                a=[r for r in scores if (r['group'],r['frame'],r['placement'],r['mode'])==(g,str(i),pl,'full')]
                old=[r for r in read_csv(PREV/(g+'_scores.csv')) if (r['frame'],r['placement'],r['mode'],r['stage'])==(str(i),pl,'full','v5_10')][0]
                a=[next(r for r in a if r['stage']==s) for s in STAGES]
                target.append((NAMES[g],i,pl,f(old['error_px']),*[f(r['error_px']) for r in a],f(a[-1]['dx']),a[-1]['pick']))
    targets=table(['组别','帧','点位','V5.10 误差','S1','S2','S3','S4','S4 Δx','S4 分支'],target)
    intro=f"以冻结 V5.10 r02 为基座。S4 可见帧 Joint 为 {sum([result['开发组A'],result['三点弯'],result['验证组C 亮区']])}/54，基线为 46/54。验证组C两种点位使用同一批图像，在总数中仅计一次。共运行 {sum(GROUPS.values()):,} 张原图。开发组A用于开发，三点弯和验证组C均在配置冻结后顺序运行，均为已接触的验证数据。排除组X排除。人工标注仅作封存后的评分与误差诊断。"
    methods="""S1 在同一像素检查红色形态细脊、当前图暗谷和差分阈值，对满足条件的位置豁免静态及偶极子删除。S2 为总分不足且存在连续八列双证据的路径重建候选，在竞争分支各自独有的区段比较红蓝符号，允许有限纵向跃迁。S3 在原配准失败时尝试材料缺口局部相关匹配，要求相关系数至少 0.90；使用暗谷与差分证据从谷底续接到下一个峰，保留材料带安全边距。短分支允许从 8 列起接续，单凭谷到峰上升的较弱路径仍要求 15 列。S4 用基准点位移及点间距估算材料带逐行位移，缩小局部配准与动态规划的计算域，将邻域形态计算合并到编译循环。"""
    metrics="""每组抽取 20 个标注帧，合计 54 帧有可见尖端。真实帧误差为原图欧氏距离。Hit@5/10 按像素判定，Joint 同时要求 10 px 邻域路径覆盖率、精确率均 ≥80%，Severe 为有定位且误差 >100 px。无预测计入可见分母。消融速度为相同 20 帧的调用数除以算法累计时间；下表另列完整序列速度，均不含读盘、评分或视频编码。"""
    views=OUT/'difference_views'
    links=' · '.join([link(views/'index.html','逐帧四联图与差分 PNG'),*[link(views/(g+'.mp4'),NAMES[g]+'视频') for g in GROUPS],link(OUT/'crack_lengths.csv','逐帧裂纹长度（px）'),link(views/'failure_views.zip','主点位失败帧图包'),link(DOC/'FAILURES_AUDIT.md','失败审计')])
    body=['# V5.11 裂纹尖端开发与冻结验证',intro,links,'## 四阶段消融',methods,metrics,real,speed,'## 目标帧复核',targets,'## 合成矩阵', '每阶段共 1,404 个样本。合成误差还原为一倍尺度像素，Joint 用 2.5 px 路径邻域。场景验收使用各场景原有判据，阴性通过表示无输出。',syn,'## 基准点敏感性', '每帧十种扰动，覆盖沿轴、法向 ±10/20 px 与点间距 ±20%。固定实验锁定名义参考映射；全流程从原始 BMP 重裁剪并重新生成映射，各自与本流程零扰动预测比较。验证组C采用亮区策略。无端点对时漂移留空。',jitter]
    profile=read_csv(OUT/'paired_tpb_profile_ms.csv')
    prows=[]
    for key,title in [('prepare','缺口与 ROI 准备'),('upstream','材料坐标参考重映射'),('fields','证据场及局部配准'),('normal','差分形态及偶极子邻域'),('lattice','动态规划内核'),('peaks','下游峰'),('bridge','桥接'),('other','其余'),('total','单帧合计')]:
        vals=[mean(float(r[key]) for r in profile if r['model']==m) for m in ('V5.10','S4')]
        prows.append((title,*map(f,vals),f(vals[1]-vals[0])))
    profile_note=f"单独配对计时中，V5.10 为 {prows[-1][1]} ms/帧、S4 为 {prows[-1][2]} ms/帧，S4 折合 {1000/float(prows[-1][2]):.2f} FPS。全序列批量评测使用四个工作进程，以单次调用耗时汇总，实测 3.62 FPS。两次测量的处理器竞争与样本范围不同，验收采用全序列结果。"
    body+=['## 三点弯速度复核',profile_note]
    timings=table(['模块','V5.10 ms/帧','S4 ms/帧','变化 ms'],prows)
    cols=read_csv(OUT/'failure_evidence.csv')
    matched=[(NAMES[r['group']],r['frame'],r['placement'],r['stage'],r['n'],r['red'],r['morph'],r['raw'],r['retained'],r['longest']) for r in cols if r['reason']=='matched']
    mt=table(['组别','帧','点位','阶段','区段列数','红差分','细脊','暗谷','保留列','最长连续'],matched)
    intervention=read_csv(OUT/'reference_intervention.csv')
    cf=table(['验证组C亮区帧','S3 尖端','S4 尖端','仅换回原参考映射的 S4'],[(r['frame'],r['S3'],r['S4'],r['S4_legacy_map']) for r in intervention if r['group']=='group_c' and r['placement']=='bright' and int(r['frame']) in {232,324,335,345}])
    correct=sum(r['restores_S3']=='True' for r in intervention)
    explanation=f"封存后固定 S4 检测代码、当前帧、裁框、点位和参数，仅替换上游配准参考，{correct}/{len(intervention)} 组帧与点位复现了 S3 的端点（含无输出）。下表列出验证组C亮区新增错误。"+link(OUT/'reference_intervention.csv','全部对照')
    findings="""验证组C 54 在 S2 首次命中。验证组C 38 的原点历史末段在 S1 已恢复 15/16 列，但 S4 亮区仍只有第 2 分支有效，第 0 分支没有通过总分门槛。支持列存在不保证入口至尖端的整条分支能晋级。三点弯 215 在 S1 已恢复 37/37 列，S2 首次命中尖端；S4 覆盖率 77.7%、精确率 79.3%。三点弯 248 从 S2 起失去 Joint，S4 尖端误差 2.20 px，路径覆盖率 60.8%、精确率 63.2%。306、413、435 的 S4 均保持 Joint，末端横向偏差分别为 +2.48、+6.21、+5.40 px。验证组C 510 在 S3 首次失去 Joint。215 和 248 从 S2 起均选中保送的第 1 分支，原第 2 分支仍合格。两帧在 S4 的第 1/2 分支排名分分别为 338.3/313.5 与 426.5/372.6。合成 P6_isolated 的场景通过数从 S1 的 36/36 降至 S2 的 0/36，P6_deformed_scratch 从 23/36 降至 2/36；S3、S4 仍保留这两项退化。"""
    conclusion="""本轮未通过整体验收，继续以 V5.10 作为比较基线。验证组C亮区与原点的结果分离，亮区 324、335、345 产生严重错误。开发组A 299 的十种重配准扰动全部归零，验证组C亮区重配准最大漂移达 215.13 px。三点弯全序列速度仍低于 4 FPS。下一轮宜先在开发材料上构造能复现点对位移梯度变化的对照，验证参考映射引起的远端证据偏移；再用带路径标注的合成分叉区分“尖端命中”和“连接到正确裂纹”。性能优化优先复测证据场和局部配准。"""
    body+=['## 失败归因与验收决定',findings,explanation,cf,conclusion,'## 复核入口',' · '.join([link(OUT/'freeze.json','冻结清单'),link(OUT/'paired_probes.csv','合成逐例结果'),link(OUT/'paired_tpb_profile_ms.csv','配对模块计时'),link(ROOT/'research/notch_identity_v511/batch.py','全序列运行器'),link(ROOT/'research/notch_identity_v511/terminal.py','检测实现')])]
    (DOC/'REPORT.md').write_text('\n\n'.join(body)+'\n',encoding='utf8')
    failure_index=read_csv(OUT/'failure_index.csv')
    audit=['# V5.11 失败帧与性能审计',intro,'## S1–S4 消融复核',metrics,real,speed,'## 合成与基准点扰动',syn,jitter,'## 冻结后参考映射对照',explanation,cf,'## 目标帧证据',findings,targets,mt,'按同一 V5.10 端点后人工标注路径取样，纵向容差 ±2 px。通过列表示该列五个像素内至少一个满足对应条件，各条件可能来自不同像素。保留列要求同一像素同时具备红色差分并通过静态与偶极子筛选。','## 三点弯模块计时','同组 20 个原始输入，预热后逐帧配对，同一进程、单 OpenCV 线程，单位为平均毫秒。嵌套调用按独占时间归属；V5.10 直接读缓存的上游映射。此项用于定位耗时，全序列 FPS 见前表。',timings,profile_note,'## 全部可见失败帧','每个 full 与 raw_only 失败分别列出，涵盖验证组C两套点位。表内为通过列数/可评列数，偶极放行表示该列搜索带存在通过偶极筛选的像素。raw_only 的差分指标来自同点位配套参考，是诊断对照。无可信差分配准时按零局部位移重放，证据不能解释为运行时采用。'+link(OUT/'individual_columns.csv','逐列原始标志')]
    idx={(r['group'],r['frame'],r['placement'],r['mode']):r for r in cols if r['reason']=='failure'}
    subgroups={}
    for item in failure_index:
        g,i,pl,mode=key=tuple(item[x] for x in ('group','frame','placement','mode'))
        c=idx[key]; d=records[g,int(i)]['placements'][pl]['S4'][mode]['diagnostics']['dual']
        score=next(r for r in scores if (r['group'],r['frame'],r['placement'],r['mode'],r['stage'])==(*key,'S4'))
        branches=[]
        for b in d['branches']:
            branches.append(f"{b['id']} {b['reason']} 总分 {f(b.get('initial_total'))}→{f(b['value'])}，排名分 {f(b['merit'])}"+('，保送' if b.get('promoted') else '')+(f"，独有红/蓝 {b['dual_columns']}/{b['blue_columns']}" if 'dual_columns' in b else ''))
        counts=str(c['n']); metricsrow='/'.join(str(c[x]) for x in ('red','morph','raw','dip_clear','retained'))
        cause=item['cause']
        if score['hit10']=='True':cause+=' 尖端已命中，失败来自路径重合度。'
        entry=(i,f(item['error']),f(item['coverage'])+'/'+f(item['precision']),c['segment']+' '+str(c['start'])+'–'+str(c['stop']),counts,metricsrow,c['longest'],d['pick']+'；'+'；'.join(branches),cause+' '+link(item['card'],'图')+' '+link(item['curve'],'曲线'))
        subgroups.setdefault((g,pl,mode),[]).append(entry)
    for (g,pl,mode),rows in subgroups.items():
        audit+=['### '+NAMES[g]+' · '+pl+' · '+mode,table(['帧','误差 px','覆盖/精确','审计区段','列数','红/细脊/暗谷/偶极放行/保留','最长','选择与候选','终止原因和图'],rows)]
    audit+=['## 验收决定',conclusion,links]
    (DOC/'FAILURES_AUDIT.md').write_text('\n\n'.join(audit)+'\n',encoding='utf8')

if __name__=='__main__':main()
