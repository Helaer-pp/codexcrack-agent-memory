"""Generate the report and audits from sealed predictions, never change inference."""
import csv
import json
from collections import Counter,defaultdict
from pathlib import Path
import cv2
import numpy as np
from .run import RUN,PREVIOUS,ROOT,GROUPS,sha,save,read

STAGES=['r02','s1','s2','s3','s3t']
GROUP={'group_a':'GROUP_A','three_point_bend':'三点弯','group_c':'验证组C'}
STAGE={'r02':'r02','s1':'S1','s2':'S2','s3':'S3 差分与附着','s3t':'S3 完整版'}
FINAL='s3t'


def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def write_csv(name,records):
    with (RUN/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=records[0].keys());w.writeheader();w.writerows(records)


def fmt(x):
    return '—' if x is None or x=='' else f'{float(x):.2f}'


def table(headers,lines):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers)]+
                     ['| '+' | '.join(str(v) for v in line)+' |' for line in lines])


def stream(path):
    with path.open(encoding='utf-8') as f:
        yield from map(json.loads,f)


def differences(first,second):
    a=dict(first['points']); b=dict(second['points'])
    changed=sorted(x for x in a.keys()|b.keys() if a.get(x)!=b.get(x))
    intervals=[]
    for x in changed:
        if intervals and intervals[-1][1]==x-1:
            intervals[-1][1]=x
        else:
            intervals.append([x,x])
    return intervals


def report():
    visible={}; selected={}; aggregates=[]; metrics={}; seq=[]; diffs=[]
    for s in STAGES:
        directory=PREVIOUS if s=='r02' else RUN/s
        for split in GROUPS:
            path=directory/(split+'.jsonl')
            assert read(directory/(split+'_seal.json'))['predictions']==sha(path)
            labelled=rows(directory/(split+'_visible.csv'))
            for r in labelled:
                visible[s,r['group'],int(r['frame']),r['mode']]=r
            keys={(r['group'],int(r['frame'])) for r in labelled}
            valid=Counter(); count=Counter()
            for r in stream(path):
                g,i=r['group'],r['frame']
                count[g]+=1
                if (g,i) in keys:
                    selected[s,g,i]=r
                for mode in ('full','raw_only'):
                    if mode in r:
                        valid[g,mode]+=r[mode]['tip'] is not None
                if s==FINAL:
                    out=r['full']; off=r['raw_only']
                    changed=differences(out,off)
                    seq.append(dict(group=g,frame=i,source_sha256=r['source_sha'],status=out['status'],
                                    root=out['root'],tip=out['tip'],observed_points=len(out['points']),
                                    raw_only_tip=off['tip'],visible_annotation=(g,i) in keys,
                                    comparison=f's3t/frames/{g}/{i}.jpg'))
                    diffs.append(dict(group=g,frame=i,full_root=out['root'],raw_only_root=off['root'],
                                      full_tip=out['tip'],raw_only_tip=off['tip'],changed_x_intervals=changed,
                                      changed_columns=sum(b-a+1 for a,b in changed)))
            assert dict(count)==GROUPS[split]
            for g,n in count.items():
                for mode in ('full','raw_only'):
                    items=[r for r in labelled if r['group']==g and r['mode']==mode]
                    if not items:
                        continue
                    err=[float(r['error']) for r in items if r['error']]
                    hit=sum(r['hit10']=='True' for r in items)
                    joint=sum(r['joint']=='True' for r in items)
                    record=dict(stage=s,group=g,mode=mode,visible=len(items),valid=len(err),hit10=hit,joint=joint,
                                severe=sum(e>100 for e in err),median_error=float(np.median(err)) if err else None,
                                max_error=max(err,default=None),sequence_valid=valid[g,mode],sequence_total=n)
                    metrics[s,g,mode]=record
                    aggregates.append(record)
    write_csv('frames.csv',seq);write_csv('reference_changes.csv',diffs)
    save(RUN/'metrics.json',aggregates)
    changes=[]; audits=[]; overshoots=[]
    for key,old in visible.items():
        s,g,i,mode=key
        if s!='r02':
            continue
        for stage in STAGES[1:]:
            new=visible[stage,g,i,mode]
            er0=float(old['error']) if old['error'] else None
            er1=float(new['error']) if new['error'] else None
            changes.append(dict(stage=stage,group=g,frame=i,mode=mode,
                                hit_before=old['hit10'],hit_after=new['hit10'],joint_before=old['joint'],joint_after=new['joint'],
                                error_before=er0,error_after=er1,delta_error=None if None in (er0,er1) else er1-er0,
                                coverage_before=old['coverage'],coverage_after=new['coverage'],
                                precision_before=old['precision'],precision_after=new['precision']))
        if mode!='full':
            continue
        before=selected['r02',g,i][mode]; final=selected[FINAL,g,i][mode]
        new=visible[FINAL,g,i,mode]
        if g=='three_point_bend':
            s1=selected['s1',g,i][mode]; d=s1['diagnostics']
            audits.append(dict(frame=i,old_root=before['root'],stage1_root=s1['root'],final_root=final['root'],
                               s1_selected=d['selected'],s1_candidates=json.dumps(d['candidates'],separators=(',',':')),
                               s1_merge_pairs=d['pairs'],final_candidates=json.dumps(final['diagnostics']['candidates'],separators=(',',':')),
                               final_merge_pairs=final['diagnostics']['pairs'],coverage_before=old['coverage'],
                               coverage_s1=visible['s1',g,i,mode]['coverage'],coverage_final=new['coverage'],
                               error_before=old['error'],error_s1=visible['s1',g,i,mode]['error'],error_final=new['error']))
        if g=='group_c' and old['hit10']=='False' and float(old['tip_dx'])>0:
            term=final['diagnostics'].get('terminal') or {}
            overshoots.append(dict(frame=i,x_before=before['tip'][0],x_final=final['tip'][0] if final['tip'] else None,
                                   x_gt=before['tip'][0]-float(old['tip_dx']),dx_before=float(old['tip_dx']),
                                   dx_final=new['tip_dx'],error_final=new['error'],body_response_ref=term.get('body_response_ref'),
                                   local_response=term.get('local_response'),after_response=term.get('after_response'),
                                   required=term.get('required'),raw_tail_x=term.get('untrimmed_x')))
    write_csv('visible_changes.csv',changes);write_csv('three_point_lips.csv',audits);write_csv('group_c_overshoot.csv',overshoots)
    probes=rows(RUN/'probes.csv')
    report_lines=['# 裂纹尖端追踪算法升级开发与验证报告','2026-11-18 · 原图灰度追踪 V3 · 研究结论 **未通过生产验收**。',
    '## 1　执行摘要与代码改动',
    '三组共 1,633 帧。完整模型保留为 S3 完整版，所有阶段在同一原图坐标系输出。裂纹路径沿缺口追踪，缺少可靠尖端时记录空值。人工线和点只在预测封存后比较。排除组X及任务书以外的组未参与。三点弯按本次任务书列为 DEV-B 对照，标注未用于训练、拟合或搜索阈值。验证组C曾在历史实验曝光，本次只在冻结后统一运行各预设消融。',
    table(['函数','r02 → 本轮实现','尺度或控制变量'],[
        ['locate_root','最右单列 → 对组件前缘带按行取最右点，以中位行和双侧分位采样产生最多 16 个起点','前缘带 0.04s，采样半径 0.15s，开运算直径 2·round(0.007s)+1'],
        ['valley_image','S1 调用冻结函数；S2 加入列背景宽窗均值与全局中位下界，保留噪声项','双侧谷深半径 0.007/0.014/0.024s；背景平滑半径 0.05s'],
        ['trace_windowed','S1 调用冻结 DP；S2 将前瞻、带宽、提交与断点长度按尺度换算；S3 抑制缺口前端后 0.2s 内的差分','前瞻 0.07s，半带 0.076s，每次提交 0.017s，每步最大斜率 2'],
        ['follow','S1 终止门固定；S2 需要尾段比前方材料响应更强，达到主干、噪声和材料离散度下界；S3 加入附着、亮隙、直线性、闭环和厚边检查','主干前 60%，尾窗 0.021s，前方 0.035s；差分只轻微辅助已有支持'],
        ['predict','每个起点实际运行；分离终点比较密度与有效延伸，汇合簇比较前段支持、谷深、附着和跳变','汇合容差 0.007s，端点距离 0.03s；前段最长 0.25s']]),
    's 为当前锚点间距，单位是原图像素。离散取整下界为一个采样点。S1 有意继承 r02 固定像素的追踪与终止门；所有后续阶段仍共享按列推进以及 8 位灰度阈值等采样假设。S2 的阶段差值同时包含支持门与其几何尺度换算，无法再拆成两个独立因果量。',
    '完整模式中，验证组C的 Hit 与 Joint 均从 6/20 提升到 13/20，尖端中位误差从 14.52 降至 5.86 px。GROUP_A 联合命中 16/19 → 14/19，三点弯仍为 1/15。全部 54 张可见标注中，两代的 >100 px 错误均为零。',
    '## 2　逐阶段消融',
    'Hit@10 为二维尖端误差 ≤10 px。Joint 还要求人工路径覆盖率及预测路径精度均 ≥80%，匹配距离 ≤10 px。Severe 为有效尖端误差 >100 px。中位数及最大值只统计有效尖端，Visible 包含所有可见标注帧。表内 Δ 为相对同组同模式 r02 的命中及联合数变化。验证组C r02 当时仅封存 full。',
    table(['阶段','组 / 模式','Visible / Valid','Hit@10','Joint','Severe','中位 px','最大 px','Δ Hit / Joint'],[
        [STAGE[a['stage']],GROUP[a['group']]+' / '+a['mode'],f"{a['visible']} / {a['valid']}",a['hit10'],a['joint'],a['severe'],fmt(a['median_error']),fmt(a['max_error']),
         ('%+d / %+d'%(a['hit10']-metrics['r02',a['group'],a['mode']]['hit10'],a['joint']-metrics['r02',a['group'],a['mode']]['joint'])) if ('r02',a['group'],a['mode']) in metrics else '—'] for a in aggregates]),
    'S1 的两组 Hit、Joint、Severe 与基线相同，因此进入 S2；GROUP_A 最大误差由 92.06 增到 94.02 px。最终 GROUP_A 未达到 16/19，三点弯 Joint 未达到 8/15；GROUP_A 开启辅助差分比 raw_only 少一次联合命中。保留旧版生产实现。',
    '## 3　逐帧诊断',
    '[每帧识别图册](s3t/index.html) · [1,633 行逐帧结果](frames.csv) · [开发组完整原图坐标与候选](s3t/dev.jsonl) · [验证组C完整原图坐标与候选](s3t/locked.jsonl)。预览中左为原灰度，右为同坐标路径与尖端。实际计分只有 54 张可见标注，其余帧仅报告识别输出。',
    '[54 张人工叠图](visible_review/index.html) · [可见帧逐阶段原图坐标](visible_stage_coordinates.csv) · [三点弯每个备选起点及近段得分](three_point_candidate_scores.csv)。候选表含 r02 全部可用起点；对未进入近段排名的候选，离线补算的得分单独标识。',
    '### 三点弯全部 15 张可见帧',
    '下表列出 r02、S1 和最终版的缺口起点，及 S1 获选种子参与的汇合 x 和近段得分。每个备选唇缘的原图坐标、终点、候选编号、各项分数以及所有配对的汇合 x 收录在[逐帧唇缘审计](three_point_lips.csv)。未进入父簇的候选仅参与整段竞争。',
    table(['帧','旧起点 → S1 → 最终','S1 所选候选的汇合 x','近段分','覆盖 r02 → S1 → 最终','误差 r02 → S1 → 最终 px'],[
        [a['frame'],f"{a['old_root']} → {a['stage1_root']} → {a['final_root']}",','.join(str(x) for x in sorted({p[2] for p in a['s1_merge_pairs'] if a['s1_selected'] in p[:2]})) or '—',
         fmt(json.loads(a['s1_candidates'])[a['s1_selected']].get('near',{}).get('score')) if a['s1_selected'] is not None else '—',
         ' → '.join(fmt(a[k]) for k in ('coverage_before','coverage_s1','coverage_final')),' → '.join(fmt(a[k]) for k in ('error_before','error_s1','error_final'))] for a in audits]),
    '三点弯 215 的 S1 上唇候选到 x=1603，下唇候选在 x=1505 停止。两条上唇种子在 x=1473 汇合；没有观测到从下唇延续到相同尖端的候选。端点接近人工点时，真正影响联合命中的仍可能是近缺口路径。',
    '### 验证组C基线 14 张右偏漏命中',
    table(['帧','旧 x','新 x','人工 x','旧 dx','新 dx','主干谷深','截断处谷深','前方谷深'],[[r['frame'],r['x_before'],r['x_final'],*[fmt(r[k]) for k in ('x_gt','dx_before','dx_final','body_response_ref','local_response','after_response')]] for r in overshoots]),
    '[验证组C完整截断数据](group_c_overshoot.csv)。dx 在原图横轴上向右为正，和二维误差分别统计。',
    '验证组C 38 的二维误差从 22.75 降到 1.58 px；新版当前候选的末次原始支持与认证端点同在 x=2291，不能将整段改善单归因于末端回剪。验证组C 54 则由向右 2.51 px 变为提前 29.49 px。验证组C最终 full 与 raw_only 的所有路径相同，不能把该组改善归功于差分。',
    '### 受益、受损及差分影响',
    '[全部可见帧逐阶段对照](visible_changes.csv)收录同模式 r02 与新阶段的覆盖率、精度、误差和命中得失。[逐帧差分影响](reference_changes.csv)列出所有 full 与 raw_only 路径不同的原图 x 区间，两端包含在内。下表列出最终版相对基线的实际变化。误差微增按原始浮点数判定。']
    summary_damage=[]
    for g in GROUP:
        for mode in ('full','raw_only'):
            rs=[r for r in changes if r['stage']==FINAL and r['group']==g and r['mode']==mode]
            if not rs:
                continue
            def ids(test):
                return ', '.join(str(r['frame']) for r in rs if test(r)) or '—'
            summary_damage.append([GROUP[g]+' / '+mode,ids(lambda r:r['hit_before']=='True' and r['hit_after']=='False'),
                ids(lambda r:r['joint_before']=='True' and r['joint_after']=='False'),
                ids(lambda r:r['hit_before']=='True' and (r['delta_error'] or 0)>0),
                ids(lambda r:r['hit_before']=='False' and r['hit_after']=='True'),
                ids(lambda r:r['joint_before']=='False' and r['joint_after']=='True')])
    report_lines.extend([table(['组 / 模式','丢失 Hit','丢失 Joint','原命中且误差增大','新增 Hit','新增 Joint'],summary_damage)])
    for g in GROUP:
        changed=[d for d in diffs if d['group']==g and d['changed_columns']]
        report_lines.append(f"{GROUP[g]} 有 {len(changed)} 帧的观测路径受差分影响，其中 {sum(d['full_tip']!=d['raw_only_tip'] for d in changed)} 帧的尖端坐标或有效性也改变。")
    report_lines.extend(['GROUP_A 净损首先出现在 S2。最终丢失命中的 366、451、504、542 均提前结束，横向分别偏左 13.07、16.10、19.97、21.93 px。第 250 帧从向右 91.93 px 缩至 4.93 px。较严格的材料上下文筛选、列背景下界以及尺度换算共同改变了候选终点，当前消融只支持定位到该阶段。GROUP_A 的命中损失不满足保真要求。每个误差增大的帧可由原图坐标和阶段 CSV 复核。',
        '## 4　独立合成探针与倍率检验',
        '尺度 0.5×、1×、2×，基准 s=288。每种几何各用两级噪声/对比度组合及两个确定性随机种子。P1 真支路分别在上、下，要求全部目标路径在 2.5 个基准像素内且端点误差 ≤10 个基准像素；P2 要求渐弱线端点误差 ≤10；P3/P4 无裂纹，输出有效尖端即假阳性。P5 为同一批数据按倍率分层，不重复计入样本数。',
        table(['探针','r02 通过','S1 通过','S2 通过','S3 差分与附着','S3 完整版','最终负例 FP/N'],[
        [case,*[str(sum(r['passed']=='True' for r in probes if r['case']==case and r['stage']==s))+'/12' for s in STAGES],
         (str(sum(r['false_positive']=='True' for r in probes if r['case']==case and r['stage']==FINAL))+'/12') if case.startswith(('P3','P4')) else '—'] for case in dict.fromkeys(r['case'] for r in probes)])])
    p5=[]
    for z in ('0.5','1.0','2.0'):
        for s in ('r02',FINAL):
            rs=[r for r in probes if r['zoom']==z and r['stage']==s]
            errs=[float(r['normalized_error']) for r in rs if r['normalized_error']]
            neg=[r for r in rs if r['case'].startswith(('P3','P4'))]
            p5.append([z,STAGE[s],f"{sum(r['passed']=='True' for r in rs)}/{len(rs)}",f"{sum(r['false_positive']=='True' for r in neg)}/{len(neg)}",len(errs),fmt(np.median(errs)) if errs else '—',fmt(max(errs,default=None))])
    report_lines.extend([table(['倍率','版本','通过 / 总数','负例 FP / N','正例有效数','归一误差中位','归一误差最大'],p5),
        '[全部探针逐例结果](probes.csv)。误差已除以缩放倍率。真实图像没有完备的无裂纹负例标注，真实 FPR 无法估计。',
        '## 5　普适性与鲁棒性',
        '代码只接收灰度、当前缺口提示、锚点尺度和可信参考响应。列背景分位及主干相对谷深可以适应部分照明和对比度变化。尺度约束覆盖多起点采样、局部搜索带、断裂长度和尖端上下文。候选数有界，单轨沿 x 单向推进；总耗时随实际延伸长度与工作带大小增长。未测量在线帧率，也没有独立新材料盲测。单向推进限制大角度折返，静态单帧无法唯一辨认所有开口和划痕。',
        '合成双唇对称测试能选择深暗谷，但真实三点弯的下唇可能更早中断。三种倍率仍有不一致；结构检查降低合成假阳性，未达到清零目标。当前证据不能证明跨材料部署可靠。',
        '## 6　残余问题与可检验的下一步'])
    issues=[
        ['下唇候选提前终止','三点弯 215 在 S1 中下唇只到 x=1505，上唇到 1603，最终路径联合命中仍为 1/15。','用合成双唇加入渐弱断带，分别测首次掉点、错误接续与近段覆盖；规则冻结后再按实验分组复查。'],
        ['真实尖端与材料纹理的取舍','GROUP_A 完整版 Hit 为 14/19，原灰度对照 15/19；逐帧审计保留原本命中的受损帧。','固定候选路径，分别消融背景平滑与前方材料门，按首次截断点对照尾端残余谷深。'],
        ['弱差分仍可改错路径','同帧开关差分会改变部分观测列和端点；开发组未达到 full 全面不劣于 raw_only。','在固定候选上只辅助尾端置信，然后与改变 DP 像素选择的模式独立对照。'],
        ['闭环和张开边缘仍误报','最终 P4 两类负例仍有假阳性；明暗对比、重采样和轮廓闭合性会影响结构门。','增加缺边闭环、真实弯裂和多角度张开对照，固定规则检验是否既拒绝假边又保留真实分支。'],
        ['跨域外推尚缺独立样本','验证组C是历史曝光回归，真实负例分母缺失。','补充独立序列、无裂纹负例和多标注者路径一致度；将新样本封存后一次评测。']]
    report_lines.extend([table(['问题','已有证据','可检验的下一步'],issues),
        '复现入口位于 research/notch_identity_v3。开发重放核验 6 帧 × 4 阶段 × 2 模式的状态、原图坐标与正式路径。冻结记录、逐阶段预测哈希、完整视频解码及独立图像核验见同目录交付文件。'])
    (RUN/'REPORT.md').write_text('\n\n'.join(report_lines)+'\n',encoding='utf-8')
    problem=ROOT/'docs/OPEN_PROBLEMS.md'
    history=ROOT/'output/github_handoff_20261118/codexcrack-agent-memory/docs/OPEN_PROBLEMS.md'
    if not problem.exists():
        problem.write_text(history.read_text(encoding='utf-8-sig'),encoding='utf-8')
    content=problem.read_text(encoding='utf-8-sig')
    heading='## 原图灰度 V3 分阶段验证'
    if heading not in content:
        problem.write_text(content+'\n'+heading+'\n\n'+table(['问题','已有证据','可检验的下一步'],issues)+'\n',encoding='utf-8')
    evidence=ROOT/'evidence/latest_metrics.json'
    evidence.parent.mkdir(exist_ok=True)
    save(evidence,dict(run=str(RUN.relative_to(ROOT).as_posix()),decision='PRODUCTION_NO_GO',primary=FINAL,
                       frames=len(seq),annotation_visible=54,stages=aggregates,synthetic_matrix='probes.csv'))
    assert len(seq)==1633 and len(audits)==15 and len(overshoots)==14


if __name__=='__main__':
    report()


