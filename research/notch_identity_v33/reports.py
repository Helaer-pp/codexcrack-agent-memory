"""Build Markdown reports and the independent tip-failure and path-only image sets."""
from collections import Counter
from html import escape
import re
from zipfile import ZipFile,ZIP_DEFLATED
from .audit import audit, failure_image, selected, fmt, regtext, MODES, NAMES
from .batch import ROOT,OUT,GROUPS,ALGS,SELECT,read,save
from research.v3_labelme_comparison.infer import read_csv
from research.v3_labelme_comparison.compare import write_csv,table
from research.notch_identity_v31.report import aggregate

FOCUS={'group_a':(67,366,504),'three_point_bend':(1,178,215,335,407,413,503),'group_c':(38,54,69,195,335,363,456,510)}
LABEL={'r02':'r02','s3t':'V3','v3_1':'V3.1','v3_2':'V3.2','curve':'弯曲重连','tail':'全尾复核','bidir':'加截断豁免','v3_3':'加分支排序'}
def pack_reports(name,body):
    text='\n\n'.join(body)+'\n'
    (OUT/name).write_text(text,encoding='utf-8')
    prefix='../../'+OUT.relative_to(ROOT).as_posix()+'/'
    archive=ROOT/'evidence/v3_3';archive.mkdir(exist_ok=True)
    (archive/name).write_text(re.sub(r'\]\(([^)]+)\)',lambda m:']('+prefix+m[1]+')',text),encoding='utf-8')
    for dest in (OUT/name,archive/name):
        for link in re.findall(r'\]\(([^)]+)\)',dest.read_text(encoding='utf-8')):
            assert (dest.parent/link).is_file(),(dest,link)

def explain(rec,r,mode):
    g,i=rec['group'],rec['frame'];models=rec['models'];m=models['v3_3'][mode]
    t=selected(m);ref=t.get('reference',{});geom=t.get('geometry');gx=t.get('geometry_cut')
    rebound=t.get('rebound_cut');dx=float(r['dx']);dy=float(r['dy'])
    if r['hit10']=='True':
        cause=f"尖端进入容差，人工路径覆盖 {float(r['coverage']):.1%}，预测路径精度 {float(r['precision']):.1%}。近缺口分支归属或缺测段影响路径。"
        test='固定末段，按同一分叉前区间分别比较各唇候选与人工路径的距离。'
    elif min(float(r['coverage']),float(r['precision']))<.05:
        cause='路径与人工线几乎完全分离，偏差从起点分支选择阶段已经存在。'
        test='在独立开口样本上比较上下唇前段净变暗及各分支排序，核查是否缺少可用的真分支。'
    elif ref.get('cut') is not None and dx<0:
        cause=f"局部参考将末段从 {ref['before_tip']} 回剪，最终停在人工尖端之前。"
        test='用已知加载前后对应关系的弱裂纹测试最后增暗列是否偏早。'
    elif dx<0 and abs(dx)>=abs(dy):
        part={'DISTAL_KINK':'弱隙转向','DISTAL_BRIGHT_GAP':'连续低响应亮隙','OTHER_LIP':'近口重连身份检查'}.get(geom,'')
        loc='；'.join(z for z in (f'{part}在 x={gx} 限制候选' if gx is not None else '',f'谷底回升判据在 x={rebound} 给出上限' if rebound is not None else '') if z)
        cause=(loc+'。' if loc else '')+f"最终在 x={m['tip'][0]} 停止，距人工点水平还差 {abs(dx):.2f} px。"
        test='在开发或合成弱带记录截断前后两窗的增暗分布，并单独关闭该截断，核验真实暗线能否重获。'
    elif abs(dy)>abs(dx) or (g=='group_c' and i==335):
        cause=f"尾部转向旁侧，纵向偏差 {dy:+.2f} px。"+(f'可见的亮隙界限 x={gx} 晚于已认证端点。' if gx is not None and gx>m['tip'][0] else '终止规则仍认证了偏离人工线的末段。')
        test='构造带斜向划痕的独立参考对，逐列核对第一次偏离、末端拐角和最后显著增暗位置。'
    else:
        cause=f"末段由 {t.get('gate')} 门认证，向右多走 {dx:.2f} px。"+(f'几何截断列为 x={gx}。' if gx is not None else '所选候选未触发远端几何截断。')
        test='用开发组增加“真尖端后仍有纹理”样本，同时记录最后认证、最后增暗及第一处低响应列。'
    before=models['bidir'][mode];prior=models['v3_2'][mode]
    if before['root']!=m['root']:
        cause+=f" 最后加入增量排序，起点从 {before['root']} 变为 {m['root']}。"
    elif g=='three_point_bend' and prior['root']!=m['root']:
        cause+=f" 相对 V3.2 起点由 {prior['root']} 改至 {m['root']}。"
    # Frame-specific checks are offline interpretations of already sealed outputs.
    special={
        ('three_point_bend',144):'弯曲重连恢复下唇后，覆盖从 27.4% 升至 90.4%，但该分支沿后段多走约 59 px。过冲在全尾复核和增量排序之前已存在。',
        ('three_point_bend',178):'下唇覆盖已经达到 100%，但认证尾端仍越过人工点约 23 px。有加载灰度变化的像素也可能落在人工尖端之外。',
        ('three_point_bend',1):'预测路径和人工路径的覆盖、精度均为零。固定参考与当前尾段完全相似，无法定位由新裂纹转入静态纹理的边界。',
        ('group_c',54):'所选短分支停在 x=2272。固定参考对近口分支的增量加分很小，加入排序前后选中同一起点；该暗影的物理身份仍待核实。',
        ('group_c',69):'最终短分支仅到 x=2274，提前近 30 px。粗、细定位在 full 中均通过，但所选尾窗未测到显著净增暗。截断未获豁免。',
        ('group_c',456):'所选强门尾点比人工点向右偏 10.09 px，二维误差仅比门槛高 0.10 px。路径覆盖和精度均为 100%。'}
    if (g,i) in special:
        if mode=='full' or (g,i) not in {('three_point_bend',1),('group_c',54),('group_c',69)}:
            cause=special[g,i]
    if g=='three_point_bend' and i==144:
        test='在独立双唇合流样本上固定同一根部候选，逐列检验人工尖端后长分支是否仍有持续材料证据。'
    if g=='group_c' and i==54:
        test='保留同帧所有有效根部分支，比较净增暗加分与原灰度排名差，区分候选缺失和排序未翻转。'
    return cause,test

def failures(rows,records):
    roster={(r['dataset_id'],int(r['frame_id'])):r for r in read_csv(SELECT) if r['dataset_id'] in GROUPS}
    intro='判定使用原图像素。可见标注的二维尖端误差超过 10 px 计入尖端失败；命中尖端且人工路径覆盖或预测点精度低于 80% 的帧另列。full 与 raw_only 分开记数，相同帧可在两个模式中出现。未标注及人工不确定帧不作失败判定。'
    doc=['# V3.3 失败帧专项整理与根因分析报告',intro]
    page=['<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V3.3 失败帧</title><style>body{font:17px/1.6 system-ui;max-width:1180px;margin:auto;padding:20px;color:#22333f}img{max-width:100%}a{color:#075673}article{margin-bottom:3em}</style><h1>V3.3 失败帧专项</h1><p>'+intro+'</p>']
    export=[]
    for mode in MODES:
        for bucket,title in [('tip','尖端超差'),('path','尖端命中、路径未达标')]:
            doc.append(f'## {mode} · {title}');page.append(f'<h2 id="{mode}-{bucket}">{mode} · {title}</h2>')
            for g in GROUPS:
                cases=[]
                for (group,i),rec in records.items():
                    if group!=g:continue
                    r=rows[g,i,'v3_3',mode]
                    if r['state']!='VISIBLE' or r['joint']=='True' or (r['hit10']=='False')!=(bucket=='tip'):continue
                    m=rec['models']['v3_3'][mode];d=m['diagnostics'];cr=d.get('coarse') or {};t=selected(m);ref=t.get('reference',{})
                    cause,test=explain(rec,r,mode)
                    link=failure_image(rec,mode,r,roster[g,i],bucket,cause)
                    cases.append(i); key=f'{NAMES[g]} {i}'
                    desc=f"人工 {r['gt']}，预测 {m['tip']}。dx / dy = {fmt(r['dx'])} / {fmt(r['dy'])}，二维误差 {fmt(r['error_px'])} px。覆盖 {float(r['coverage']):.1%}，精度 {float(r['precision']):.1%}。"
                    diag=f"追踪停止 {t.get('stop')}，尾门 {t.get('gate')}，几何检查 {t.get('geometry')}（列 {t.get('geometry_cut')}），谷底上限 {t.get('rebound_cut')}，获豁免列 {t.get('waived',[])}。"
                    note=(f"粗定位 {regtext(cr)}；局部 {regtext(ref)}。末窗净变暗均值 {fmt(ref.get('net'))} 灰度级，有效增暗比例 {fmt(ref.get('fraction'))}，复核判断 {ref.get('decision','—')}，回剪列 {ref.get('cut')}。"
                          if mode=='full' else 'raw_only 仅观测当前图；粗定位、局部偏移、NCC、净变暗与参考回剪均不适用。')
                    old=rows[g,i,'v3_2',mode]
                    doc.extend([f'### [{key} 叠图]({link})',desc+' V3.2 二维误差 '+fmt(old['error_px'])+' px。',diag+' '+note,cause+' '+test])
                    page.append(f'<article><h3>{key} · {fmt(r["error_px"])} px</h3><a href="{link}"><img loading="lazy" src="{link}" alt="{key}"></a><p>{escape(cause)} {escape(test)}</p></article>')
                    export.append(dict(group=g,frame=i,mode=mode,category=bucket,gt=r['gt'],tip=m['tip'],dx=r['dx'],dy=r['dy'],error=r['error_px'],
                      coverage=r['coverage'],precision=r['precision'],stop=t.get('stop'),gate=t.get('gate'),coarse=cr,reference=ref,waived=t.get('waived'),rank=t.get('increment_rank'),cause=cause,test=test,image=link))
                if not cases:doc.append(f'{NAMES[g]}该项为 0 帧。')
    write_csv(OUT/'failures.csv',export)
    (OUT/'failure_index.html').write_text('\n'.join(page)+'</html>',encoding='utf-8')
    pack_reports('FAILURES_AUDIT.md',doc)
    with ZipFile(OUT/'failure_frames.zip','w',ZIP_DEFLATED) as z:
        for name in ['FAILURES_AUDIT.md','failure_index.html','failures.csv',*[r['image'] for r in export]]:z.write(OUT/name,name)
    with ZipFile(OUT/'failure_frames.zip') as z:assert z.testzip() is None
    return export

def synthetic():
    base=read_csv(OUT/'probes.csv')
    full=read_csv(OUT/'paired_probes.csv')
    assert len(base)==936 and len(full)==468
    matrix=[];comparison=[];gap=[];scale_summary=[]
    for label,rs in [('V3.2 原灰度',[r for r in base if r['stage']=='v3_2']),('V3.3 原灰度',[r for r in base if r['stage']=='v3_3']),('V3.3 含参考',full)]:
        def key(r):return tuple(r[k] for k in ('case','width','contrast','noise','seed','zoom'))
        nom={key(r):r for r in rs if r['photo']=='nominal'}
        for p in ('nominal','dim','bright'):
            sub=[r for r in rs if r['photo']==p]
            comparison.append([label,p,f"{sum(r['passed']=='True' for r in sub)}/{len(sub)}",sum(r['passed']!=nom[key(r)]['passed'] for r in sub),sum(r['tip']!=nom[key(r)]['tip'] for r in sub)])
        if label.startswith('V3.3'):
            for case in dict.fromkeys(r['case'] for r in rs):
                for z in ('0.5','1.0','2.0'):
                    cells=[]
                    for ph in ('nominal','dim','bright'):
                        rr=[r for r in rs if (r['case'],r['zoom'],r['photo'])==(case,z,ph)]
                        n=len(rr);good=sum(r['passed']=='True' for r in rr)
                        cells.append(f'{good}/{n}'+(f'（FP {n-good}/{n}）' if rr[0]['negative']=='True' else ''))
                    matrix.append([label,case,z,*cells])
            for z in ('0.5','1.0','2.0'):
                ng=[r for r in rs if r['negative']=='True' and r['zoom']==z]
                scale_summary.append([label,z,*[str(sum(r['valid']=='True' for r in ng if r['photo']==p))+'/16' for p in ('nominal','dim','bright')]])
        if label.endswith('原灰度'):
            weak=[r for r in nom.values() if r['case']=='P1_weak_gap']
            gap.append([label,len(weak),sum(int(r['accepted']) for r in weak),sum(int(r['wrong']) for r in weak),sum(r['passed']=='True' for r in weak)])
    return matrix,comparison,gap,scale_summary

def main():
    rows,stats,records,times=audit()
    failures_list=failures(rows,records)
    prim={r['group']:r for r in stats if r['stage']=='v3_3' and r['mode']=='full'}
    overall=aggregate([r for (g,i,s,m),r in rows.items() if (s,m)==('v3_3','full')])
    passed=all(prim[g]['hit']>=goal and prim[g]['severe']==0 for g,goal in zip(GROUPS,(17,11,14)))
    decision='PRODUCTION_NO_GO' if not passed else 'PRIMARY_GATES_MET'
    matrix,exp,gap,scale_summary=synthetic()
    summary=['# V3.3 裂纹尖端追踪算法开发与消融验证报告',
        f"**{decision}**。完整模式在 54 帧可见标注上尖端命中 {overall['hit']}/54、严重误差 {overall['severe']} 帧、路径与尖端联合命中 {overall['joint']}/54。V3.2 对应为 38/54、0 帧和 30/54。",
        '[失败专项报告](FAILURES_AUDIT.md) · [分组失败图册](failure_index.html) · [失败帧离线包](failure_frames.zip) · [全序列逐帧图册](index.html) · [开发组A视频](group_a.mp4) · [三点弯视频](three_point_bend.mp4) · [验证组C视频](group_c.mp4)',
        '## 1　验收与实现',
        table(['组别','Hit@10 目标','V3.3 Hit@10','Severe','Joint','主指标'],[[NAMES[g],f'≥{target}/{prim[g]["visible"]}',f'{prim[g]["hit"]}/{prim[g]["visible"]}',prim[g]['severe'],prim[g]['joint'],'通过' if prim[g]['hit']>=target and prim[g]['severe']==0 else '未通过'] for g,target in zip(GROUPS,(17,11,14))]),
        '尖端误差按原图二维欧氏距离计算，≤10 px 为命中，>100 px 为严重。Joint 另需人工路径覆盖及预测点精度均 ≥80%，匹配容差 10 px。本轮三点弯和验证组C主要按尖端验收；开发组A同步要求 Joint ≥17/19。另有 6 张不确定标注及 1,573 张未标注帧，均提供结果图，不计入准确率。实测阴性误报率未知。',
        '仅以开发组A与独立合成图开发。三点弯在冻结后作阶段对照，验证组C在三点弯结果封存后执行一次冻结回归；两组有历史曝光。人工标注仅在相应组预测封存后比对。排除组X及其他材料未进入本轮。',
        table(['改动','实现和触发条件'],[
            ['弯曲下唇','取消直线外推残差硬门，保留谷宽比 ≤2。若重获暗线在失联前已作为独立相邻谷持续存在，拒绝跨唇；同时检查重获段切向反推的相邻谷和重获入口高度沿断带的连续证据。'],
            ['宽锚粗配准','宽约 0.92s、高 0.46s 的缺口和两侧材料窗口，用局部高通纹理抑制照明与轮廓主导，排除裂纹通道。搜索 ±0.04s；若粗定位不可靠，尝试上下两块独立材料窗，要求两者平移在 0.01s 内一致。'],
            ['尾段细配准','在粗平移附近 ±0.015s 微调，先查末段周边非裂纹纹理，再试更宽窗。两级都要求有效材料覆盖、曝光自适应纹理能量、NCC ≥0.75 与独立峰差 ≥0.012。任何一级失败都保留原灰度路径并记录原因。'],
            ['全候选末端复核','STRONG 和 TAPER 均检查最后 0.15s。逐点用两侧材料亮度补偿测得固定图到当前图的暗谷深度增量，以 max(2×局部噪声, 0.025×曝光跨度) 判断显著增暗。末端连续静态或弱谷、前方有已确认增暗时，约束到最后新增暗列，再走原终止认证。整个末段静态又缺少变化边界时记录歧义。'],
            ['双向保护','若远端低响应、拐折或谷底回升拟截断，在左右各约 0.022s 的窗口检查暗谷与净变暗。两侧分别至少 65% 观测满足增量门才豁免，后面仍须通过原灰度终止门。原始 DP 已停止的位置无法由此向外延长。'],
            ['分支软排序','full 的近缺口前 0.25s 估计平均正净变暗（按曝光跨度归一化并截顶）及显著比例。0.65 × 比例 × 平均量平方根加入整段名次和共同起源区间的分支得分。缺乏对齐证据时该加分为零。raw_only 保留原灰度竞争。']]),
        's 为锚距，以原图像素表示；窗口按 s 换算至可采样的整数像素。曝光跨度来自当前缺口邻域 3% 与 70% 分位。fixed 为上游已对齐的固定参考；本模块估计其相对当前 ROI 的残余平移，峰差是最优峰减去邻域外次峰。高 NCC 仍需满足峰唯一性。',
        '开发轮记录：r01 使用灰度 NCC 和仅宽度重连，原曝光弱带错接 8 次。r02 用高通纹理与既存相邻谷否决后降至 2 次，其余错接均在半倍率。r03 加入重获窗入口的连续证据与双侧材料锚，降至 0 次。三轮开发组A均为 17/19。冻结后仅生成评测与交付物。[源码冻结指纹](freeze.json)',
        '## 2　分阶段消融',
        '标注的 60 张图均运行八个预设和两种模式，V3.3 最终版另运行全部 1,633 帧。弯曲重连阶段沿用旧局部参考复核；全尾复核替换宽锚定位与尾段裁剪，接着独立加入截断豁免、分支排序。四个历史基线在相同图上重算，480 个帧／版本／模式组合的状态、起点、路径和端点逐项复现。',
        table(['组别','预设','模式','可见/有效','Hit@10','Severe','Joint','中位误差 px','最大误差 px'],[
            [NAMES[r['group']],LABEL[r['stage']],r['mode'],f"{r['visible']}/{r['valid']}",r['hit'],r['severe'],r['joint'],fmt(r['median']),fmt(r['max'])] for r in stats]),
        '[消融指标 CSV](ablation_metrics.csv) · [逐帧配准及增量审计](reference_audit.csv)',
        '## 3　历史问题帧逐帧复核',
        '下表为 full 模式，误差为原图像素。显示最终入选候选的粗、细配准和平移；旧几何截断、旧谷底及旧参考回剪都以原图 x 表示，缺省表示未触发。']
    focus=[]
    for g,ids in FOCUS.items():
        for i in ids:
            rec=records[g,i];end=rec['models']['v3_3']['full'];old=selected(rec['models']['v3_2']['full'])
            cr=end['diagnostics'].get('coarse') or {};t=selected(end);ref=t.get('reference',{})
            focus.append([f'[{NAMES[g]} {i}](labels/{g}/{i}.png)',*[fmt(rows[g,i,s,'full']['error_px']) for s in ('v3_2','curve','tail','bidir','v3_3')],regtext(cr),regtext(ref),
                          f"{old.get('geometry_cut')} / {old.get('rebound_cut')} / {old.get('reference',{}).get('cut')}",
                          f"{t.get('geometry_cut')} / {t.get('rebound_cut')} / {ref.get('cut')}",str(t.get('waived',[])),ref.get('decision','—')])
    summary.append(table(['帧','V3.2','弯曲重连','全尾复核','加豁免','最终','粗定位','尾端定位','旧几何/谷底/参考列','新几何/谷底/参考列','豁免列','末段增量判断'],focus))
    diff=[]
    for g in GROUPS:
        old={i for (grp,i,s,m),v in rows.items() if grp==g and s=='v3_2' and m=='full' and v['hit10']=='True'}
        new={i for (grp,i,s,m),v in rows.items() if grp==g and s=='v3_3' and m=='full' and v['hit10']=='True'}
        diff.append([NAMES[g],sorted(new-old),sorted(old-new)])
    summary.extend([table(['组','相对 V3.2 新命中','相对 V3.2 新超差'],diff),
        '## 4　合成、曝光、运行时间',
        '原曝光、dim（0.65I+9）、bright（1.16I+15）按 8 位截顶；倍率 0.5/1/2，噪声两档，种子两档。P1 要求尖端命中及 2.5 个基准像素内全路径覆盖；P2 要求折回基准后的尖端误差 ≤10；P3/P4 为阴性。full 使用独立噪声生成的未加载缺口图，含固定参考辅助，没有前帧；另以已知残余平移和已知静态／新增线段验证参考模块。',
        table(['模式','探针','倍率','nominal 通过','dim 通过','bright 通过'],matrix),
        table(['版本 / 模式','曝光','通过数','相对 nominal 判定改变','尖端坐标或有效性改变'],exp),
        table(['模式','倍率','nominal FP/N','dim FP/N','bright FP/N'],scale_summary),
        table(['弱带原曝光','样本','接受重接','错接','全路径通过'],gap),
        '原曝光 P2 为 10/12，三种曝光的合成阴性结果见上表。强曝光仍改变部分结果；实验覆盖这组三档扰动。模块专项验证已知平移 (−3,+2)、静态或弱尾 x=203 的精确回剪、整线静态、整线新增、参考缺损和低纹理，以及截断豁免正负例。[原灰度探针](probes.csv) · [含参考探针](paired_probes.csv) · [配准和增量专项](reference_tests.json)',
        '六个 CPU 工作进程，按单帧 full 的 prepare、两路辅助矩阵和预测计时；不含读盘、画图和编码。FPS 是单帧均值倒数。最坏值包含进程启动后的 JIT，不能据此推断流水线实时性。',
        table(['组别','帧','平均 ms','P95 ms','最坏 ms（帧）','FPS','两模式端点不同帧数'],[[NAMES[r['group']],r['frames'],fmt(r['mean_ms']),fmt(r['p95_ms']),f"{fmt(r['worst_ms'])}（{r['worst_frame']}）",fmt(r['fps']),r['full_raw_tip_changed']] for r in times]),
        table(['组别','粗配准成功 / 全帧','候选末段复核数','实际回剪候选','出现豁免的候选','复核后无法使用增量的候选'],[[NAMES[r['group']],f"{r['coarse'].get('OK',0)}/{r['frames']}",r['reviewed_candidates'],sum(r['review'].get(k,0) for k in ('TRIM_WEAK','TRIM_STATIC')),r['waiver_candidates'],r['review'].get('NO_ALIGNMENT',0)] for r in times]),
        '候选数含来自不同起点的重复路径。无唯一定位、低纹理或超出有效区域时不计算增量；整段静态且没有可辨认的变化边界时保留原结果。[计时和状态分布](timing.csv) · [全序列解码核验](delivery_check.json)'])
    fullfail=[r for r in failures_list if r['mode']=='full']
    summary.extend(['## 5　验收结论与优先排查项',
        '三点弯第 503 帧从 11.22 px 回到 8.58 px，第 144 帧从 9.92 px 恶化至 59.29 px，因此组内尖端命中数持平。弯曲重连让路径与尖端联合命中从 1/15 增至 9/15。对 60 张抽样标注帧，后续加入全尾复核、截断豁免和分支增量排序，各步均未改变上一步公开的 full 尖端坐标。三组全序列 full 与 raw_only 的尖端共有 54 帧不同，这些差异不能外推为准确率提升。',
        '验证组C 335 已进入强门末端复核，粗 NCC 0.80、峰差 0.28，尾窗 NCC 0.51 未达到 0.75 的可信门。195、363、456、510 的尾窗 NCC 也低于该门。对这些帧，报告中的 AMBIGUOUS 表示未通过综合配准门；最佳峰低与多峰难分是不同原因。此次证据支持端点偏离，静态划痕的身份仍缺直接参考证据。',
        '开发组A 366 用双侧纹理锚取得粗定位，尾窗纹理不足；504 的粗定位未通过。验证组C 38、54、69 则取得局部定位，但所选末窗的显著净增暗比例均为零。下一步应在独立开发样本上分别验证弱纹理对应、加载前已存在的暗线以及双唇合流后的终止位置。保持原验收容差可以区分方法改进与边界样本的指标波动。'])
    summary.append(f"本轮完整模式有 {sum(r['category']=='tip' for r in fullfail)} 张尖端超差，另有 {sum(r['category']=='path' for r in fullfail)} 张尖端已命中且路径未过门，分别成册。逐帧可核对人工点、预测点、实际停止条件、配准峰和净增暗。[失败专项](FAILURES_AUDIT.md)")
    pack_reports('REPORT.md',summary)
    meta=dict(run=OUT.relative_to(ROOT).as_posix(),primary='v3_3',decision=decision,date='2026-11-19',report='evidence/v3_3/REPORT.md',failures='evidence/v3_3/FAILURES_AUDIT.md',frames=1633,scored_visible=54,uncertain=6,overall_full=overall,groups=stats,real_fpr=None,timing=times)
    save(OUT/'metrics.json',meta);save(ROOT/'evidence/latest_metrics.json',meta)
    state=ROOT/'docs/CURRENT_STATE.md';text=state.read_text(encoding='utf-8-sig')
    header='## V3.3 尖端精度验证'
    if header not in text:
        title,rest=text.split('\n',1)
        block=f"2026-11-19。{decision}。54 帧可见标注中尖端命中 {overall['hit']} 帧、联合命中 {overall['joint']} 帧、严重误差 {overall['severe']} 帧。[开发报告](../evidence/v3_3/REPORT.md) · [失败帧专项](../evidence/v3_3/FAILURES_AUDIT.md)。"
        state.write_text(title+'\n\n'+header+'\n\n'+block+'\n'+rest,encoding='utf-8')
    print(decision,overall)
if __name__=='__main__':main()
