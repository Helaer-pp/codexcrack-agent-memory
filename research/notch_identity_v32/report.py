"""Build the six-section report from sealed outputs. Never invokes inference."""
from collections import Counter
import re
from .audit import audit, MODES
from .batch import ROOT, OUT, ALGS, GROUPS, read, save
from research.notch_identity_v31.report import NAMES, WHY, aggregate, num, yes
from research.v3_labelme_comparison.compare import table
from research.v3_labelme_comparison.infer import read_csv

FOCUS={'group_a':(366,451,504,542),'three_point_bend':(215,248,335,413,435,476),'group_c':(69,335,221,456,480,528)}
STAGES=ALGS[2:]


def rate(rows):
    return f"{sum(yes(r,'passed') for r in rows)}/{len(rows)}"


def probe_tables():
    probes=read_csv(OUT/'probes.csv')
    nominal=[r for r in probes if r['photo']=='nominal']
    matrix=[];weak=[];exposure=[]
    for case in dict.fromkeys(r['case'] for r in nominal):
        for stage in ('v3_1','v3_2'):
            cells=[]
            for zoom in ('0.5','1.0','2.0'):
                rs=[r for r in nominal if (r['case'],r['stage'],r['zoom'])==(case,stage,zoom)]
                cell=rate(rs)
                if yes(rs[0],'negative'):
                    cell+=f"（FP {sum(yes(r,'valid') for r in rs)}/{len(rs)}）"
                cells.append(cell)
            matrix.append([case,stage,*cells])
    totals={}
    for stage in ('v3_1','v3_2'):
        gap=[r for r in nominal if r['case']=='P1_weak_gap' and r['stage']==stage]
        totals[stage]={k:sum(int(r[k]) for r in gap) for k in ('accepted','wrong','rejected')}
        for width in (4,9,16):
            for contrast in ('0.0','0.2'):
                rs=[r for r in gap if (int(r['width']),r['contrast'])==(width,contrast)]
                weak.append([stage,width,contrast,len(rs),*[sum(int(r[k]) for r in rs) for k in ('accepted','wrong','rejected')],rate(rs)])
        def key(r):return tuple(r[k] for k in ('case','width','contrast','zoom','noise','seed'))
        base={key(r):r for r in nominal if r['stage']==stage}
        for photo in ('nominal','dim','bright'):
            rs=[r for r in probes if r['stage']==stage and r['photo']==photo]
            exposure.append([stage,photo,rate(rs),sum(r['passed']!=base[key(r)]['passed'] for r in rs),
                             sum(r['tip']!=base[key(r)]['tip'] for r in rs)])
    return matrix,weak,exposure,totals


def report():
    rows,metrics,diag,changes,failures,times,parity=audit()
    delivery=read(OUT/'delivery_check.json');assert delivery['cards']==1633 and delivery['manual']==60
    selected={(d['group'],d['frame'],d['stage'],d['mode']):d for d in diag}
    primary={m['group']:m for m in metrics if m['stage']=='v3_2' and m['mode']=='full'}
    overall=aggregate([r for r in rows.values() if r['stage']=='v3_2' and r['mode']=='full'])
    matrix,weak,exposure,gaps=probe_tables()
    parts=['# V3.2 裂纹尖端追踪算法高精度与普适性验证报告',
        '[交互逐帧图册](index.html) · [1,633 帧识别坐标、状态和图像](frames.csv) · [开发组A视频](group_a.mp4) · [三点弯视频](three_point_bend.mp4) · [验证组C视频](group_c.mp4)',
        '## 1　执行摘要与改动',
        f"2026-11-19，冻结版本 v32_precision_20261119_r03。54 张尖端可见的人工标注帧中，完整模式命中 {overall['hit']}/54，路径与尖端联合命中 {overall['joint']}/54，误差超过 100 px 共 {overall['severe']} 帧。另有 6 张标注为不确定，其余 1,573 帧提供识别图与坐标。真实数据缺少独立阴性标注，实际误报率未知。",
        table(['相对 V3.1 r04 的变动','判据及保留的诊断'],[
            ['背景包络','分别试验旧背景、逐列 85% 分位与局部均值和全局中值的上包络。原灰度双侧暗谷始终是主证据。'],
            ['渐弱终止门','三个连续尾窗检查衰减趋势、前方谷深相对噪声底以及主干与末段夹角；对于谷深跌至噪声后又持续回升的候选，在首个合格谷底前截断。强门独立保留。极低采样时允许单列谷底。'],
            ['远端防跳接','对单向 DP 的临时轨迹逐列检查。在起点 0.35 倍尺度之外，连续约 0.014 倍尺度的归一化响应低于 0.85，或短弱隙两端转向超过 22°，即在候选参与竞争前截断。'],
            ['固定参考局部复核','完整模式仅复核渐弱认证、发生重连或明显折转的候选。用路径外材料纹理做局部平移 NCC（±0.025 倍尺度）；仅在定位充分且观察到已变化主干与静态相似尾段的边界时回剪、重新认证。'],
            ['同唇重连与张口负例','沿断带前段切向外推，要求重获窗中位纵向残差 ≤0.012 倍尺度（至少 1 像素），断带两侧谷宽比 ≤2。对短张口外缘联合检查外移方向、起点横截面宽度与开口中心偏距。'],
            ['曝光及尺度','沿用局部 3% / 70% 分位差、归一化暗谷强度与无量纲长度排序；full 还保留 V3.1 的有界弱差分，raw_only 只使用当前灰度。']]),
        '开发限于开发组A与独立合成图。首轮开发组A 17/19、渐弱探针 9/12。第二轮把单列谷底判据用于全部分辨率，渐弱探针达 10/12，开发组A 217、299 提前截断，联合降至 15/19。最终轮只在谷底统计窗不超过两列时启用该判据，开发组A恢复 17/19，渐弱探针保持 10/12。所有参数在三点弯与验证组C推理前冻结；验证组C执行一次。两组有历史曝光，未取得全新独立盲测集。标签仅用于预测封存后的比较。排除组X未参与。',
        '## 2　分阶段消融',
        '九个预设均在每组同一批 20 张标注帧上比较，V3.2 同时覆盖三组全序列。Hit@10 为原图二维尖端距离 ≤10 px；Joint 另需路径覆盖率与预测点精度均 ≥80%（匹配距离 10 px）。Severe 为误差 >100 px。误差中位与最大值限于有效可见帧。r02 是旧灰度基线，与开发轮号分开。',
        '以 v3_1 为共同起点，background 只改背景，taper_only 只改尾端规则，paired 同时启用两项。随后依次叠加 distal 防跳接、reference 局部参考复核、v3_2 同唇与张口外缘校验。曝光和尺度规则在四格对照中保持一致。',
        table(['组别','阶段','模式','可见/有效','Hit@10','Joint','Severe','中位 px','最大 px'],[
            [NAMES[g],r['stage'],r['mode'],f"{r['visible']}/{r['valid']}",r['hit'],r['joint'],r['severe'],num(r['median']),num(r['max'])]
            for g in GROUPS for r in metrics if r['group']==g]),
        f"原图摘要逐帧核对；对 60 张标注帧的三个历史基线、两种模式，{parity} 条状态、起点、尖端和路径与封存结果逐点一致。[指标表](ablation_metrics.csv) · [冻结清单](freeze.json)",
        '## 3　反例、逐帧归因与新增受损帧',
        '下表为 full 模式二维误差（px），最终偏差是预测减人工。最后一列记录单独改变背景或尾端规则能否使旧漏检重新进入 10 px 容差；算法路径和排名也可能随规则改变。']
    focus=[]
    for g,ids in FOCUS.items():
        for i in ids:
            seq=[rows[g,i,s,'full'] for s in STAGES]
            base,bg,gate,both=seq[:4]
            cause='原已命中' if yes(base,'hit10') else ('两项单独均恢复' if yes(bg,'hit10') and yes(gate,'hit10') else
                 '仅背景单改恢复' if yes(bg,'hit10') else '仅尾门单改恢复' if yes(gate,'hit10') else '仅联合恢复' if yes(both,'hit10') else '两项均未恢复')
            end=seq[-1]
            focus.append([f"[{NAMES[g]} {i}](labels/{g}/{i}.png)",*[num(r['error_px']) for r in seq],
                          f"{num(end['dx'])} / {num(end['dy'])}",WHY.get(end['failure'],end['failure']),cause])
    parts.append(table(['帧',*STAGES,'最终 dx / dy','最终结果','四格对照'],focus))
    for i in (69,335):
        detail=[]
        for s in ('v3_1','paired','distal','reference','v3_2'):
            g='group_c';d=selected[g,i,s,'full'];r=rows[g,i,s,'full']
            link=f'labels/{g}/{i}.png' if s=='v3_2' else f'stage_images/{g}/{i}_{s}.png'
            detail.append([f'[{s}]({link})',d['root'],d['tip'],num(r['error_px']),d['geometry'] or '—',d['geometry_cut'],
                           d['rebound_cut'],d['ref_status'] or '—',num(d['ncc']),d['shift'],d['ref_cut'],d['before_tip']])
        parts.append(f"**验证组C第 {i} 帧**　人工尖端 {r['gt']}。截断列为原图 x；空值表示所选分支未发生该项截断。")
        parts.append(table(['阶段叠图','所选起点','预测尖端','误差 px','几何判断','几何截断','谷底截断','局部复核','NCC','平移','参考截断','复核前尖端'],detail))
    g='three_point_bend';i=215
    detail=[]
    for s in ('s3t','v3_1','paired','distal','reference','v3_2'):
        d=selected[g,i,s,'full'];r=rows[g,i,s,'full']
        detail.append([s,d['root'],d['tip'],d['first_loss'],d['events'],num(r['coverage']),num(r['precision']),r['joint']])
    parts.append(table(['三点弯 215','起点','尖端','首失列','重获事件¹','覆盖','精度','Joint'],detail))
    parts.append('¹ 事件依次为弱带起始列、重获窗首末列、纵向预测残差、谷宽比、是否通过。最终入选起点与截断可在[分阶段诊断](stage_diagnostics.csv)核对。')
    lost=[]
    for g in GROUPS:
        for mode in MODES:
            rs=[r for r in changes if r['baseline']=='v3_1' and r['group']==g and r['mode']==mode]
            lost.append([NAMES[g],mode,*[', '.join(str(r['frame']) for r in rs if k in r['changes']) or '—' for k in ('hit10_lost','joint_lost','error_up','coverage_down','precision_down')]])
    parts.append(table(['相对 V3.1','模式','丢失 Hit','丢失 Joint','误差增加','覆盖降低','精度降低'],lost))
    parts.append('以下为所有可见标注中 full 最终联合未命中的帧。偏差方向、覆盖和精度说明失败类型；记录的末端认证、首失列与复核状态描述触发机制，材料纹理的物理身份仍需独立证据。')
    parts.append(table(['异常帧','类型','dx / dy px','误差 px','覆盖 / 精度','尾门 / 停止条件','几何 / 局部复核'],[
        [f"[{NAMES[r['group']]} {r['frame']}]({r['overlay']})",WHY.get(r['failure'],r['failure']),f"{num(r['dx'])} / {num(r['dy'])}",
         num(r['error_px']),f"{num(r['coverage'])} / {num(r['precision'])}",f"{r['gate']} / {r['stop']}",f"{r['geometry']} / {r['ref_status']}"] for r in failures if r['mode']=='full']))
    parts.append('[两种模式的全部失败及上游阶段误差](failures.csv) · [连续指标退化清单](regressions.csv) · [不确定标注](uncertain.csv)')
    parts.extend(['## 4　合成探针与弱带错连',
        '相同的 156 个几何、噪声、弱带条件组合分别比较两个版本和三种曝光。下表为原曝光。P1 要求整条真线在 2.5 个基准像素容差内且尖端误差 ≤10，P2 仅按尖端阈值，P3/P4 为阴性。误差按倍率折回基准像素。',
        table(['探针','版本','0.5× 通过','1× 通过','2× 通过'],matrix),
        '72 个弱带样本的错误重连，只对最终入选轨迹中重获窗与注入区相交的事件计数。窗内贴合真下唇的点少于 80% 计一次错连。',
        table(['版本','弱带宽','残余对比','样本','接受','错连','同唇门拒绝','整路径通过'],weak),
        f"原曝光接受数从 {gaps['v3_1']['accepted']} 降至 {gaps['v3_2']['accepted']}，错连从 {gaps['v3_1']['wrong']} 次降至 {gaps['v3_2']['wrong']} 次。错连减少与保守截断同时发生。每个曝光及每个样本的路径评分见[探针原始数据](probes.csv)。",
        '## 5　曝光稳定性与运行时间',
        '固定几何分别施加 nominal 原灰度、dim = 0.65I+9、bright = 1.16I+15，并裁剪为 8 位。通过状态和尖端比较均相对同一版本、同一原曝光样本。',
        table(['版本','曝光','通过 / 总数','通过状态变化数','坐标或有效性变化数'],exposure),
        '六个 CPU 工作进程；每帧耗时包含 ROI 内准备、辅助矩阵与一次 full 预测，排除读盘、绘图、视频和 raw_only。FPS 为平均耗时的倒数。局部复核净耗时为所有帧（含未触发）的均值，按唯一末段缓存计时。阶段总耗时差为每组 20 帧 reference 减 distal，包含调度和候选重认证波动。',
        table(['组','帧','平均 ms','P95 ms','最慢 ms（帧）','FPS','局部复核 ms/帧','至少一次复核帧数','阶段差 ms/帧'],[
            [NAMES[t['group']],t['n'],num(t['mean_ms']),num(t['p95_ms']),f"{num(t['worst_ms'])}（{t['worst_frame']}）",num(t['fps']),num(t['review_ms']),t['active_review_frames'],num(t['paired_delta_ms'])] for t in times]),
        table(['组','复核后裁剪候选数（含重复候选）','最终入选有裁剪帧数','full/raw 尖端不同帧数','公开路径或状态不同帧数','full 无尖端帧数'],[
            [NAMES[t['group']],t['candidates'].get('TRIM_STATIC_SUFFIX',0),t['selected'].get('TRIM_STATIC_SUFFIX',0),t['full_raw_tip_changes'],t['full_raw_output_changes'],t['invalid']] for t in times]),
        '局部配准专项五例中，人为设置的静态后缀从 x=128 开始；平移估计为 (−3,+2)，首次裁剪在 x=127。整线静态、整线新增、参考缺像素及低纹理四例均保留原预测。旧公共矩阵 420 行逐项一致。新算法另由双版本的 936 条曝光与倍率观测覆盖。[配准测试](reference_tests.json) · [计时及复核状态分布](timing.csv) · [视频解码核验](delivery_check.json)'])
    parts.insert(parts.index('## 4　合成探针与弱带错连'),
        '九张历史过冲帧中，单改渐弱终止规则使三点弯 413、435 和验证组C 221、480 回到容差，单改背景只使验证组C 528 回到容差。加入远端检查后，三点弯 248、476 恢复，413 又离开容差。最终九帧恢复六帧，三点弯 335、413 和验证组C 456 仍过冲。开发组A 366 在两种单改下均退化，504 主要受尾端规则影响；451、542 仍联合命中。')
    parts.insert(parts.index('## 4　合成探针与弱带错连'),
        '验证组C 69 在 distal 阶段先遇 x=2310 折转，缩短后的有效轨迹又触发 x=2276 谷底截断，误差从过冲转为提前。最终所选起点改到 (2247,2344)，同唇校验在 x=2275 截断。局部 NCC 虽高，但峰值不唯一，两阶段均未据参考图裁剪。验证组C 335 的原灰度叠图可见算法线从人工终点转向右上暗线。新的终止规则把误差降到 30.64 px；远端首次满足连续亮隙条件在 x=2505，晚于已认证尖端 x=2494。所选尾段通过强门且未触发复核。图像支持旁侧暗线吸附，尚无法确认该线在固定参考中静止。')
    parts.insert(parts.index('## 4　合成探针与弱带错连'),
        '三点弯 215 的正确下唇从 (1474,2729) 出发。重获窗 x=1520–1533 的谷宽比为 1.22，切向外推中位残差 8.04 px，同唇门在 x=1507 拒绝该重连，下唇候选退至 x=1506。上唇候选因而胜出，尖端误差保持 2.08 px，覆盖率从 100% 降至 64.9%，路径精度从 100% 降至 60%。三点弯该阶段整体由 9/15 联合命中降至 1/15。三点弯第 1 帧路径覆盖和精度均为零，是另一类早期归属失败。[包括未入选分支的三帧记录](focus_candidates.csv)')
    parts.append('两种模式在三个组的可见帧 Hit、Joint、严重误差和误差分布均持平。全序列仍有 6 帧的尖端不同，逐帧差异和人工标注状态单列。[两种模式的全部输出差异](mode_disagreements.csv)。计时中的最慢帧位于各批启动阶段，包含新编译算子开销；阶段总耗时差可为负。局部参考与画面曝光的真实联合作用仍缺少受控实测。')
    return parts,primary,overall,metrics,times,gaps

def main():
    parts,primary,overall,metrics,times,gaps=report()
    issues=[
        ['同唇校验误拒真实弯曲下唇','三点弯 215 的预测残差 8.04 px，谷宽比 1.22；最终选到上唇。三点弯最后阶段丢失八个联合命中。','在开发组及独立合成图加入弯曲、合流、遮挡的双唇；分别消融切向与宽度，将正确拒绝和错误拒绝都列入事件统计。'],
        ['末端暗线离开主裂纹，或保护规则提前截断','验证组C 335 的远端亮隙触发晚于误选的暗线；69 的回剪跨过人工尖端，局部配准峰不唯一。','在独立开发图造出带已知真实尖端的斜向划痕，区分首次偏离列、首次弱隙列、实际截断列，并检验配准峰唯一性。'],
        ['弱尾及曝光边界','开发组A 366、504 由命中转为提前约 14 px；P2 的两个失败都在半倍率高噪声下。强曝光下合成通过数从 113 降到 104。','在独立采集的开发图改变倍率、曝光和噪声，验证弱尾信号分辨率及局部背景动态范围。'],
        ['实际误报率及实时性缺证','54 张可见人工尖端和 6 张不确定标注；已有序列缺少独立阴性和相机端到端时延测量。','取得独立无裂纹阴性序列并测量单路采集到输出的稳态及冷启动延迟。']]
    gates=[]
    for g,h,j in [('group_a',16,16),('three_point_bend',10,8),('group_c',13,13)]:
        r=primary[g]; passed=r['hit']>=h and r['joint']>=j and r['severe']==0
        gates.append([NAMES[g],f'Hit ≥{h}，Joint ≥{j}，严重 0',f"Hit {r['hit']}/{r['visible']}，Joint {r['joint']}/{r['visible']}，严重 {r['severe']}",'通过' if passed else '未通过'])
    decision='PRODUCTION_NO_GO' if any(g[-1]=='未通过' for g in gates) else 'REVIEW_OTHER_GATES'
    gates.extend([['弱带错连','相对 8/30 减至少于 3 次','错连 0/21 次接受；同一批 72 个样本','通过事件计数，接受数减少'],
                  ['P2_fade','至少 10/12','原曝光 10/12','通过'],
                  ['阴性误报','0.5× / 2× 逼近零','原曝光 P3/P4 两个倍率均 0/16','通过合成负例'],
                  ['双模式','full 不劣于 raw_only','三组可见标注的指标持平','通过本次对照']])
    parts.extend(['## 6　生产验收与遗留边界',f'**{decision}**。开发组A及原曝光合成目标通过。三点弯的尖端和路径指标、验证组C的尖端与联合指标均低于门槛。与 V3.1 相比，三个组汇总的尖端命中从 31/54 增到 38/54，联合命中均为 30/54。当前限制生产使用的首要问题是三点弯的近缺口路径归属。',table(['项目','门槛','实际','判定'],gates),table(['问题','已有证据','可检验的下一步'],issues)])
    report_text='\n\n'.join(parts)+'\n'
    (OUT/'REPORT.md').write_text(report_text,encoding='utf-8')
    rel=OUT.relative_to(ROOT).as_posix()
    target=ROOT/'evidence/v3_2'
    target.mkdir(parents=True,exist_ok=True)
    (target/'REPORT.md').write_text(re.sub(r'\]\(([^)]+)\)',lambda m:'](../../'+rel+'/'+m[1]+')',report_text),encoding='utf-8')
    meta=dict(date='2026-11-19',run=rel,primary='v3_2',decision=decision,frames=1633,scored_visible=54,uncertain=6,unlabeled=1573,
              overall_full=overall,groups=metrics,real_fpr=None,synthetic_gap=gaps,public_regression_rows=420,synthetic_rows=936,
              historical_prediction_parity=360,report='evidence/v3_2/REPORT.md',synthetic_p2_nominal='10/12',reference_tests=5,timing=times)
    save(OUT/'metrics.json',meta)
    save(ROOT/'evidence/latest_metrics.json',meta)
    for doc,header,body in [
        ('OPEN_PROBLEMS.md','## V3.2 精度与普适性',table(['问题','已有证据','可检验的下一步'],issues)),
        ('CURRENT_STATE.md','## V3.2 精度与普适性',f'2026-11-19。{decision}。开发组A、三点弯、验证组C的尖端命中分别为 17/19、9/15、12/20，联合命中分别为 17/19、1/15、12/20。三点弯同唇门误拒正确下唇；验证组C 69 提前，335 仍转向旁侧暗线。[完整报告](../evidence/v3_2/REPORT.md) · [逐帧查看与视频](../{rel}/index.html)。')]:
        path=ROOT/'docs'/doc
        content=path.read_text(encoding='utf-8-sig')
        if header not in content:
            title,remainder=content.split('\n',1)
            path.write_text(title+'\n\n'+header+'\n\n'+body+'\n'+remainder,encoding='utf-8')
    for path in (target/'REPORT.md',OUT/'REPORT.md'):
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            assert (path.parent/link).is_file(),link

if __name__=='__main__':
    main()

