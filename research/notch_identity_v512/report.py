"""Publish frozen score tables and per-frame failure explanations."""
import json
import os
from statistics import mean
from pathlib import Path
from .batch import GROUPS, ROOT, OUT, read, read_csv, sha, sources
from research.v3_labelme_comparison.compare import write_csv

DOC=ROOT/'evidence/v5_12'
PREV=OUT.parent/'v511_diff_unblock_r02'
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
    records={}; scores=[]; lengths=[]; allrows=[]; gatecounts={}
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
                    if s=='S4':
                        from collections import Counter
                        counts=gatecounts.setdefault((g,p),Counter())
                        diag=b['full']['diagnostics']['dual']
                        win=next((a for a in diag['branches'] if diag['pick']=='BRANCH_'+str(a['id'])),{})
                        counts['peak_lock']+=sum(isinstance(e,dict) and e.get('reason')=='PEAK_BLANK_SPAN' for e in diag.get('events',[]))
                        counts['bridge_lock']+=sum(a['bridge'].get('reason')=='BRIDGE_BLANK_SPAN' for a in diag['branches'])
                        counts['cost']+=sum(a['bridge'].get('reason')=='STATIC_EXTENSION_COST' for a in diag['branches'])
                        counts['blocked']+=sum(a['reason'] in ('DETACHED_RESCUE','NO_BLUE_COMPETITOR') for a in diag['branches'])
                        counts['forks']+=sum(a.get('fork_rescue',False) for a in diag['branches'])
                        counts['won']+=bool(win.get('fork_rescue'))
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
        for case in ['全部阳性','P1_weak_gap','weak_material_bridge','active_fork','P6_isolated','P6_deformed_scratch','全部阴性']:
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
    import math
    consistency=[]
    for g in GROUPS:
        pl='bright' if g=='group_c' else 'original'
        base={r['frame']:r for r in scores if (r['group'],r['stage'],r['mode'],r['placement'])==(g,'S4','full',pl)}
        nr=read_csv(OUT/(g+'_native_jitter.csv'))
        zeros=[r for r in nr if float(r['delta'])==0]
        def tip(r):return json.loads(r['tip']) if r['tip'] else None
        def published(r):
            v=base[r['frame']]
            return [int(v['pred_x']),int(v['pred_y'])] if v['pred_x'] else None
        distances=[math.dist(tip(r),published(r)) for r in zeros if tip(r) is not None and published(r) is not None]
        hit=sum(tip(r) is not None and math.dist(tip(r),json.loads(base[r['frame']]['gt']))<=10 for r in zeros if base[r['frame']]['gt'])
        consistency.append((NAMES[g],sum(tip(r)==published(r) for r in zeros),len(zeros),f(max(distances,default=0)),hit))
    reference_check=table(['数据','零扰动与封存端点相同','比较帧','最大差异 px','零扰动 Hit@10'],consistency)
    geom=[[],[]]
    for rec in map(json.loads,(OUT/'group_c.jsonl').open()):
        orig,bright=(rec['placements'][pl]['S4']['full'] for pl in ('original','bright'))
        same=orig['tip']==bright['tip']
        geom[0].append(same)
        if ('group_c',rec['frame']) in records:geom[1].append(same)
    agreement=f"封存预测中，验证组C原点/亮区两套点位有 {sum(geom[1])}/{len(geom[1])} 个标注帧及 {sum(geom[0])}/{len(geom[0])} 个全序列帧给出相同端点（含同时无输出）。主评测继承 V5.11 S3 的上游参考缓存，验证组C两套点位共用该缓存。在重配准试验中，每次使用实际点对重新生成上游映射。下表检查零扰动原图重算与主评测的一致性。"
    target=[]
    for g,frames in [('group_a',[299]),('three_point_bend',[215,248,306,413,435]),('group_c',[1,7,38,54,232,324,335,345,510])]:
        for i in frames:
            for pl in records[g,i]['placements'] if (g,i) in records else ():
                a=[r for r in scores if (r['group'],r['frame'],r['placement'],r['mode'])==(g,str(i),pl,'full')]
                old=[r for r in read_csv(PREV/(g+'_scores.csv')) if (r['frame'],r['placement'],r['mode'],r['stage'])==(str(i),pl,'full','S4')][0]
                a=[next(r for r in a if r['stage']==s) for s in STAGES]
                target.append((NAMES[g],i,pl,f(old['error_px']),*[f(r['error_px']) for r in a],f(a[-1]['dx']),a[-1]['pick']))
    targets=table(['组别','帧','点位','V5.11 误差','S1','S2','S3','S4','S4 Δx','S4 分支'],target)
    intro=f"以冻结 V5.11 r02 为基座。S4 可见帧 Joint 为 {sum([result['开发组A'],result['三点弯'],result['验证组C 亮区']])}/54，V5.11 为 41/54，V5.10 为 46/54。验证组C两种点位使用同一批图像，在总数中仅计一次。共运行 {sum(GROUPS.values()):,} 张原图。开发组A用于开发，三点弯和验证组C均在配置冻结后顺序运行，均为已接触的验证数据。排除组X排除。人工标注仅作封存后的评分与误差诊断。"
    methods="""S1 恢复 V5.11 S3 的上游参考映射、完整局部匹配窗口和 DP 搜索域。所有阶段使用编译后的邻域形态算子。下游峰与桥接跨越长空白时保留初始峰；对同一前缀的近端弱峰另检验末端连续正增益与灰度暗谷支撑，以稳定开发组基准点扰动。S2 在普通分支评估后再决定低分候选能否参与排序；保送需要根部连接，已有有效竞争分支时还要求其独有区段出现蓝带。成熟路径的长延伸若主体与末段净收益都为负，则撤销。S3 允许从一个实测缺口种子作最多 4 px 的叉根跃迁，要求跃迁处暗谷连通、其后三列为双一致，仍需八列连续双证据及蓝带竞争。S4 复用同帧双侧脊深度、形态开运算和原灰度得分，配准窗口、几何映射、搜索范围及阈值与 S3 相同。"""
    metrics="""每组抽取 20 个标注帧，合计 54 帧有可见尖端。真实帧误差为原图欧氏距离。Hit@5/10 按像素判定，Joint 同时要求 10 px 邻域路径覆盖率、精确率均 ≥80%，Severe 为有定位且误差 >100 px。无预测计入可见分母。消融速度为相同 20 帧的调用数除以算法累计时间；下表另列完整序列速度，含 ROI 准备、局部配准及检测，不含读盘、原始上游参考图构建、评分或视频编码。"""
    views=OUT/'difference_views'
    links=' · '.join([link(views/'index.html','逐帧四联图与差分 PNG'),*[link(views/(g+'.mp4'),NAMES[g]+'视频') for g in GROUPS],link(OUT/'crack_lengths.csv','逐帧裂纹长度（px）'),link(views/'failure_views.zip','主点位失败帧图包'),link(DOC/'FAILURES_AUDIT.md','失败审计')])
    body=['# V5.12 裂纹尖端开发与冻结验证',intro,links,'## 四阶段消融',methods,metrics,real,speed,'## 目标帧复核',targets,'## 合成矩阵', '每阶段共 1,404 个样本。合成误差还原为一倍尺度像素，Joint 用 2.5 px 路径邻域。场景验收使用各场景原有判据，阴性通过表示无输出。',syn,'## 基准点敏感性', '每帧十种扰动，覆盖沿轴、法向 ±10/20 px 与点间距 ±20%。固定实验锁定名义参考映射；全流程从原始 BMP 重裁剪并重新生成映射，各自与本流程零扰动预测比较。验证组C采用亮区策略。无端点对时漂移留空。',jitter,agreement,reference_check]
    profile=read_csv(OUT/'paired_tpb_profile_ms.csv')
    same_load=read_csv(OUT/'paired_four_worker_tpb.csv')
    paired_fps=table(['固定四工作进程、交错先后顺序','520 帧 full FPS','复现封存尖端及状态'],[(ver,rate([r for r in same_load if r['version']==ver],'seconds'),n([r for r in same_load if r['version']==ver],'identical_endpoint')) for ver in ('V5.11','V5.12')])
    stream_timing='原始 BMP 的整段重算计时正在进行。'
    if (OUT/'uncached_tpb_seconds.csv').exists():
        native_time=read_csv(OUT/'uncached_tpb_seconds.csv')
        stream_timing=f"另外从三点弯的 520 张原始 BMP 逐帧重建裁框与上游映射，使用各帧已提供的测量点。含上游映射和检测的速度为 {rate(native_time,'total')} FPS，其中 {n(native_time,'identical')}/520 帧与封存结果的状态、路径和尖端相同。计时包含首次调用，排除读盘、点跟踪与渲染。"+link(OUT/'uncached_tpb_seconds.csv','520 帧耗时')
    prows=[]
    for key,title in [('prepare','缺口与 ROI 准备'),('registration','局部配准'),('fields','证据场（扣除局部配准）'),('normal','差分形态与偶极子邻域'),('lattice','动态规划'),('peaks','下游峰（旧峰搜索）'),('bridge','桥接（候选生成）'),('other','其余检测与门控'),('total','单帧合计')]:
        vals=[mean(float(r[key]) for r in profile if r['model']==m) for m in ('S3','S4')]
        prows.append((title,*map(f,vals),f(vals[1]-vals[0])))
    profile_note="采用同一进程对三点弯 20 个相同帧作预热后配对计时，单位为 ms/帧。各模块扣除已单列子调用。全序列主表为单工作进程逐帧统计；V5.11 历史主表为四进程，跨轮速度同时受并发度影响。"
    timings=table(['模块','V5.12 S3','V5.12 S4','变化 ms'],prows)
    body+=['## 三点弯工程提速',profile_note,timings,paired_fps,stream_timing]
    cols=read_csv(OUT/'failure_evidence.csv')
    matched=[(NAMES[r['group']],r['frame'],r['placement'],r['stage'],r['n'],r['red'],r['morph'],r['raw'],r['retained'],r['longest']) for r in cols if r['reason']=='matched']
    mt=table(['组别','帧','点位','阶段','区段列数','红差分','细脊','暗谷','保留列','最长连续'],matched)
    measured=[]
    for rec in records.values():
        for place,models in rec['placements'].items():
            x,y=(models[st]['full'] for st in ('S3','S4'))
            measured.append((x['status'],x['points'],x['tip'],x['diagnostics']['dual'].get('registration'))==(y['status'],y['points'],y['tip'],y['diagnostics']['dual'].get('registration')))
    bystage={st:[r for r in probes if r['stage']==st] for st in STAGES}
    parity=sum(all(x[k]==y[k] for k in ('case','seed','zoom','photo','tip','coverage','precision','passed')) for x,y in zip(bystage['S3'],bystage['S4']))
    note=f"12 组合成输入的 S3/S4 逐像素证据场、种子、配准记录及门控统计完全一致。纯算子等价检查覆盖全部标注帧与点位。S3 和 S4 的状态、整条折线、端点和局部配准记录在 {sum(measured)}/{len(measured)} 个组合一致。合成矩阵中，尖端、路径评分和验收状态在 {parity}/1404 个配对样本一致。"
    def focus(g,i,pl='original',stage='S4'):
        return next(r for r in scores if (r['group'],r['frame'],r['placement'],r['mode'],r['stage'])==(g,str(i),pl,'full',stage))
    gates=table(['组','点位','锁下游峰','锁桥接空白','静态延伸撤销','保送被拒','新叉根候选','新叉根最终获选'],[(NAMES[g],pl,*[counts[k] for k in ('peak_lock','bridge_lock','cost','blocked','forks','won')]) for (g,pl),counts in gatecounts.items()])
    focusrows=[]
    for g,ids,pl in [('three_point_bend',[215,248],'original'),('group_c',[38,54,232,324,335,345,510],'bright')]:
        for i in ids:
            row=focus(g,i,pl)
            m=records[g,i]['placements'][pl]['S4']['full']
            d=m['diagnostics']['dual']
            win=next((b for b in d['branches'] if 'BRANCH_'+str(b['id'])==d['pick']),{})
            bridge=win.get('bridge',{})
            focusrows.append((NAMES[g],i,' / '.join(focus(g,i,pl,st)['pick'].replace('BRANCH_','') for st in STAGES),f(row['error_px']),f(row['coverage']),f(row['precision']),row['joint'],str(win.get('base_tip')),str(m['tip']),bridge.get('reason','—')))
    focus_table=table(['组','帧','分支 S1/S2/S3/S4','误差 px','覆盖率','精确率','Joint','初始峰','最终尖端','桥接判据'],focusrows)
    targeted=[]
    for g,i,pl in [('three_point_bend',215,'original'),('three_point_bend',248,'original'),('group_c',38,'bright'),('group_c',510,'bright')]:
        for stage,model in records[g,i]['placements'][pl].items():
            diag=model['full']['diagnostics']['dual']
            branches=diag['branches']
            targeted.append((NAMES[g],i,stage,diag['pick'],' / '.join(f"{a['id']} {a['reason']}，初分 {f(a['initial_total'])}，排名分 {f(a['merit'])}" for a in branches)))
    targeted_table=table(['组','帧','阶段','最终分支','分支编号、门控和得分'],targeted)
    summary=read(OUT/'interpretation.json')
    findings=summary['findings'];conclusion=summary['decision']
    body+=['## 核心帧与原因',focus_table,findings,'全序列各候选的实际拦截与晋级次数。同一帧可出现多个候选。',gates,note,'## 验收决定',conclusion,'## 复核入口',' · '.join([link(OUT/'freeze.json','冻结清单'),link(OUT/'gate_replay.csv','重点帧门控回放'),link(OUT/'operator_parity.json','逐像素算子一致性'),link(OUT/'paired_probes.csv','合成逐例结果'),link(OUT/'paired_tpb_profile_ms.csv','配对模块计时'),link(ROOT/'research/notch_identity_v512/batch.py','全序列运行器'),link(ROOT/'research/notch_identity_v512/terminal.py','检测实现')])]
    (DOC/'REPORT.md').write_text('\n\n'.join(body)+'\n',encoding='utf8')
    failure_index=read_csv(OUT/'failure_index.csv')
    audit=['# V5.12 失败帧与性能审计',intro,'## S1–S4 消融复核',metrics,real,speed,'## 合成与基准点扰动',syn,jitter,agreement,reference_check,'## S3 与 S4 一致性',note,'## 目标帧证据',findings,targets,focus_table,targeted_table,gates,mt,'按同一 V5.10 端点后人工标注路径取样，纵向容差 ±2 px。通过列表示该列五个像素内至少一个满足对应条件，各条件可能来自不同像素。保留列要求同一像素同时具备红色差分并通过静态与偶极子筛选。','## 三点弯模块计时','同组 20 个原始输入，预热后逐帧配对，同一进程、单 OpenCV 线程，单位为平均毫秒。嵌套调用按独占时间归属；S3 和 S4 使用同一封存的上游映射。此项用于定位耗时，全序列 FPS 见前表。',timings,profile_note,paired_fps,stream_timing,'## 全部可见失败帧','每个 full 与 raw_only 失败分别列出，涵盖验证组C两套点位。通过率为通过列数除以可评列数，偶极放行表示该列搜索带存在通过偶极筛选的像素。raw_only 的差分指标来自同点位配套参考，是诊断对照。无可信差分配准时按零局部位移重放，证据不能解释为运行时采用。'+link(OUT/'individual_columns.csv','逐列原始标志')]
    idx={(r['group'],r['frame'],r['placement'],r['mode']):r for r in cols if r['reason']=='failure'}
    subgroups={}
    for item in failure_index:
        g,i,pl,mode=key=tuple(item[x] for x in ('group','frame','placement','mode'))
        c=idx[key]; d=records[g,int(i)]['placements'][pl]['S4'][mode]['diagnostics']['dual']
        score=next(r for r in scores if (r['group'],r['frame'],r['placement'],r['mode'],r['stage'])==(*key,'S4'))
        branches=[]
        for b in d['branches']:
            branches.append(f"{b['id']} {b['reason']} 总分 {f(b.get('initial_total'))}→{f(b['value'])}，排名分 {f(b['merit'])}"+('，保送' if b.get('promoted') else '')+(f"，独有红/蓝 {b['dual_columns']}/{b['blue_columns']}" if 'dual_columns' in b else ''))
        counts=str(c['n']); metricsrow=' / '.join(f"{int(c[x])/int(c['n']):.0%}" if c['n'] and int(c['n']) else '—' for x in ('red','morph','raw','dip_clear','retained'))
        cause=item['cause']
        if score['hit10']=='True':cause+=' 尖端已命中，失败来自路径重合度。'
        entry=(i,f(item['error']),f(item['coverage'])+'/'+f(item['precision']),c['segment']+' '+str(c['start'])+'–'+str(c['stop']),counts,metricsrow,c['longest'],d['pick']+'；'+'；'.join(branches),cause+' '+link(item['card'],'图')+' '+link(item['curve'],'曲线'))
        subgroups.setdefault((g,pl,mode),[]).append(entry)
    for (g,pl,mode),rows in subgroups.items():
        audit+=['### '+NAMES[g]+' · '+pl+' · '+mode,table(['帧','误差 px','覆盖/精确','审计区段','列数','红/细脊/暗谷/偶极放行/保留','最长','选择与候选','终止原因和图'],rows)]
    audit+=['## 验收决定',conclusion,links]
    (DOC/'FAILURES_AUDIT.md').write_text('\n\n'.join(audit)+'\n',encoding='utf8')

if __name__=='__main__':main()
