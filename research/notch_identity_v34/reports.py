"""Post-freeze scoring, per-candidate evidence and failure attribution."""
from collections import Counter
from html import escape
from zipfile import ZipFile, ZIP_DEFLATED
import re
from .audit import audit, failure_image, selected, fmt, MODES, NAMES
from .batch import ROOT,OUT,BASE,GROUPS,ALGS,SELECT,read,save
from research.v3_labelme_comparison.infer import read_csv
from research.v3_labelme_comparison.compare import write_csv,table
from research.notch_identity_v31.report import aggregate
HIST={'group_a':[366,504],'three_point_bend':[1,144,178,335,407,413],'group_c':[38,54,69,195,335,363,456,510]}
def pack_reports(name,body):
    text='\n\n'.join(body)+'\n'
    (OUT/name).write_text(text,encoding='utf-8')
    prefix='../../'+OUT.relative_to(ROOT).as_posix()+'/'
    archive=ROOT/'evidence/v3_4';archive.mkdir(exist_ok=True)
    (archive/name).write_text(re.sub(r'\]\(([^)]+)\)',lambda m:']('+prefix+m[1]+')',text),encoding='utf-8')
    for dest in (OUT/name,archive/name):
        for link in re.findall(r'\]\(([^)]+)\)',dest.read_text(encoding='utf-8')):
            assert (dest.parent/link).is_file(),(dest,link)

def synthetic():
    base=read_csv(OUT/'probes.csv')
    full=read_csv(OUT/'paired_probes.csv')
    assert len(base)==936 and len(full)==468
    matrix=[];comparison=[];gap=[];scale_summary=[]
    for label,rs in [('V3.3 原灰度',[r for r in base if r['stage']=='v3_3']),('V3.4 原灰度',[r for r in base if r['stage']=='v3_4']),('V3.4 含参考',full)]:
        def key(r):return tuple(r[k] for k in ('case','width','contrast','noise','seed','zoom'))
        nom={key(r):r for r in rs if r['photo']=='nominal'}
        for p in ('nominal','dim','bright'):
            sub=[r for r in rs if r['photo']==p]
            comparison.append([label,p,f"{sum(r['passed']=='True' for r in sub)}/{len(sub)}",sum(r['passed']!=nom[key(r)]['passed'] for r in sub),sum(r['tip']!=nom[key(r)]['tip'] for r in sub)])
        if label.startswith('V3.4'):
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


def reason(rec,mode,r,t):
    ref=t.get('reference',{});decision=ref.get('decision')
    dx=float(r['dx']);dy=float(r['dy'])
    if r['hit10']=='True' and r['joint']!='True':
        return '尖端命中，人工线覆盖或预测点精度低于 80%。','在同一合流点之前比较两唇候选，逐段确定哪一段丢失。'
    if r['joint']=='True':
        return '最终仍联合命中，但误差、覆盖或精度相对上一版出现退化。','固定原候选集，分别检查裁剪上限与分支排名的变化。'
    if mode=='full':
        specific={
            ('three_point_bend',1):('当前图就是固定参考图，增暗为零，背景边缘与预存裂纹无法按新增量区分，灰度兜底选错分支。','构造带预存开裂的零载荷对照，分别检查根部归属和两唇路径。'),
            ('three_point_bend',144):('原虚尾已被标记为缺少连续增暗边界，但静态兜底仍允许同尖端候选胜出。','在开发材料上对比全静态兜底、末端弃权和最后可信增暗位置，分别记录有效率和误差。'),
            ('three_point_bend',407):('三个亮隙已获豁免，最终尖端仍停在第一处豁免之前。解除几何截断不足以通过后续末端认证。','输出弱段之后逐列强度、前方对比与锥形门结果，在开发组合成相同强弱转换。'),
            ('group_c',54):('可竞争候选的全路径增暗比例均为零，多个上侧种子触发 OTHER_LIP，亦有根部和闭合轮廓拒绝。','在独立上唇样本比较所拒绝段与人工线，分别检验候选生成、根附着和跨唇豁免。'),
            ('group_c',69):('上侧种子出现 OTHER_LIP、无可信尾端及轮廓排除。最终可竞争候选均无有效增暗，近口没有跨唇豁免。','用已知双唇身份的独立序列验证上侧候选何时消失，并统计放宽后的错接。'),
            ('group_c',38):('所选短线无连续增暗边界，分支排序仍保留了近口灰度兜底。','对独立短裂纹逐根核对是否存在到达人工尖端的候选。'),
            ('group_c',335):('粗定位已解锁，但末窗一半观测点仍被判定新增，末端复核放行了向上偏离的暗线。','在开发组合成带有局部形变的斜划痕，沿路径检测第一次偏航。'),
            ('group_c',363):('邻域暗谷查重触发回剪，方向偏离减小，但重新认证的尖端落在人工尖端左侧。','分别量化去除错位划痕所需的最短裁剪距离以及重新认证造成的额外回退。'),
            ('group_c',528):('在 x=2516 豁免亮隙后，预测尖端由 x=2515 延至 2524，新增过冲。','独立复现亮隙后短暗线，检验其是否恢复到同一根路径。')}
        if (rec['group'],rec['frame']) in specific:return specific[rec['group'],rec['frame']]
    if min(float(r['coverage']),float(r['precision']))<.05:
        return '路径与标注几乎完全分离，误差从缺口路径归属阶段已经存在。','比较同一缺口各候选的根部位置和全路径增暗分层，检查候选缺失与全静态兜底。'
    if dx<0 and ref.get('cut') is not None:
        return f"参考复核在 x={ref['cut']} 给出上限，重新认证后尖端提前。",'合成弱尾叠加既有纹理，区分真实暗谷、噪声最大值和双极伪影。'
    if dx<0 and abs(dx)>=abs(dy):
        return f"所选轨迹提前，几何判据 {t.get('geometry')}，几何上限 {t.get('geometry_cut')}，谷底上限 {t.get('rebound_cut')}。",'逐列比较截断前后净积分，核对候选前向缓存、豁免以及重新认证三者的首个失败点。'
    if ref.get('source')=='NONE':
        return '增量证据不可用，原灰度路径越过人工尖端或转向旁侧。','在独立同材质图上测量宽锚对应精度及参考缺测范围。'
    if abs(dy)>abs(dx) or (rec['group']=='group_c' and rec['frame']==335 and dy< -10):
        return f"末段横向偏离人工路径，dy={dy:+.2f} px，最终复核为 {decision or '纯灰度'}。",'用残余错位的斜向暗线对照，检查首次偏航列和查重、双极判据的触发顺序。'
    return f"末端向右超出 {dx:.2f} px，终止门 {t.get('gate')} 仍认证该候选。",'在开发图分别测试渐弱后的真实延伸与相邻纹理，核对最后增暗边界和首次几何断点。'

def records_for_review(rows,records):
    roster={(r['dataset_id'],int(r['frame_id'])):r for r in read_csv(SELECT) if r['dataset_id'] in GROUPS}
    doc=['# V3.4 失败帧与受损帧专项分析','本报告按模式与组别列出所有可见标注中尖端超差、仅路径失分以及仍联合命中但连续量退化的帧。覆盖或精度的任意可复现下降均记入比较；一帧有多项变化时只归入一个类别。坐标、裁剪列和误差使用原图 px。']
    entries=[];page=['<!doctype html><html lang="zh"><meta charset="utf-8"><title>V3.4 失败与受损帧</title><style>body{font:17px/1.65 system-ui;max-width:1200px;margin:auto;padding:1em}img{max-width:100%}</style><h1>V3.4 失败与受损帧</h1>']
    for mode in MODES:
        for g in GROUPS:
            group_rows=[]
            for (grp,i),rec in records.items():
                if grp!=g:continue
                r=rows[g,i,'v3_4',mode];old=rows[g,i,'v3_3',mode]
                if r['state']!='VISIBLE':continue
                flags=[label for k,label,sign in [('error_px','误差增加',1),('coverage','覆盖下降',-1),('precision','精度下降',-1)] if (float(r[k])-float(old[k]))*sign>1e-9]
                kind='尖端超差' if r['hit10']!='True' else '尖端命中但路径失分' if r['joint']!='True' else '仍联合命中但连续量退化' if flags else None
                if kind is None:continue
                m=rec['models']['v3_4'][mode];t=selected(m);ref=t.get('reference',{})
                cause,test=reason(rec,mode,r,t)
                changes=[]
                for a,b in zip(('v3_3','unlock','shield','branch'),('unlock','shield','branch','v3_4')):
                    p=rec['models'][a][mode];q=rec['models'][b][mode]
                    if p['tip']!=q['tip'] or p['root']!=q['root']:
                        changes.append(f"{b} 根 {q['root']}、尖端 {q['tip']}")
                # Keep the previous version and each changed stage visible.
                link=failure_image(rec,mode,r,roster[g,i],{'尖端超差':'tip','尖端命中但路径失分':'path','仍联合命中但连续量退化':'regression'}[kind],cause)
                entry=dict(group=g,frame=i,mode=mode,category=kind,changes=','.join(flags),gt=r['gt'],tip=m['tip'],dx=r['dx'],dy=r['dy'],error=r['error_px'],old_error=old['error_px'],coverage=r['coverage'],precision=r['precision'],coarse=m['diagnostics'].get('coarse'),ref=ref,
                    waived=t.get('waived'),lip=t.get('waived_lip'),geometry=t.get('geometry'),geom_cut=t.get('geometry_cut'),stop=t.get('stop'),gate=t.get('gate'),branch=t.get('increment_rank'),transitions=changes,cause=cause,test=test,image=link)
                entries.append(entry);group_rows.append(entry)
            for kind in ('尖端超差','尖端命中但路径失分','仍联合命中但连续量退化'):
                subset=[a for a in group_rows if a['category']==kind]
                heading=f'{NAMES[g]} · {mode} · {kind}（{len(subset)}）'
                doc.append('## '+heading);page.append('<h2>'+heading+'</h2>')
                if not subset:doc.append('本项 0 帧。')
                for a in subset:
                    q=a['ref'];cr=a['coarse'] or {}
                    detail=f"人工 {a['gt']}，预测 {a['tip']}；dx/dy 为 {fmt(a['dx'])}/{fmt(a['dy'])}，误差 {fmt(a['old_error'])} → {fmt(a['error'])} px。覆盖 {float(a['coverage']):.1%}，精度 {float(a['precision']):.1%}。"
                    align=(f"粗定位 {cr.get('status','—')}、NCC {fmt(cr.get('ncc'))}、峰差 {fmt(cr.get('margin'))}；细定位 {q.get('local_status',q.get('status','—'))}、NCC {fmt(q.get('ncc'))}。采用 {q.get('source','—')}，平移 {q.get('shift')}。净积分均值 {fmt(q.get('net'))}，负正能量比 {fmt(q.get('ratio'))}，查重比例 {fmt(q.get('duplicate'))}，有效增暗比例 {fmt(q.get('fraction'))}，判断 {q.get('decision')}，裁剪列 {q.get('cut')}。" if mode=='full' else '纯原灰度模式，无参考配准、查重、能量比或参考回剪。')
                    stages='；'.join(a['transitions']) or '各阶段所选起点与尖端坐标相同'
                    doc.extend([f"### [第 {a['frame']} 帧叠图]({a['image']})",detail+' '+align,
                                f"停止 {a['stop']}，尾门 {a['gate']}，几何 {a['geometry']}（列 {a['geom_cut']}），豁免列 {a['waived']}，其中跨唇 {a['lip']}。{stages}。",a['cause']+' '+a['test']])
                    page.append(f"<h3>第 {a['frame']} 帧</h3><a href='{a['image']}'><img loading='lazy' src='{a['image']}'></a><p>{escape(detail+' '+a['cause'])}</p>")
    write_csv(OUT/'failures.csv',entries)
    (OUT/'failure_index.html').write_text('\n'.join(page)+'</html>',encoding='utf-8')
    pack_reports('FAILURES_AUDIT.md',doc)
    with ZipFile(OUT/'failure_frames.zip','w',ZIP_DEFLATED) as z:
        for name in ['FAILURES_AUDIT.md','failure_index.html','failures.csv',*[a['image'] for a in entries]]:z.write(OUT/name,name)
    with ZipFile(OUT/'failure_frames.zip') as z:assert z.testzip() is None
    return entries
