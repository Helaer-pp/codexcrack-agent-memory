"""Write the V3.5 ablation, synthetic, performance and failed-frame reports."""
from .report import (BASE,OUT,ROOT,GROUPS,ALGS,MODES,FOCUS,pack,read,save,read_csv,
                     write_csv,table,NAMES,num,aggregate,selected,collect,failure_report)

def synth():
    cases=read_csv(OUT/'paired_probes.csv');past=read_csv(BASE/'paired_probes.csv')
    key=lambda r:tuple(r[k] for k in ('case','width','contrast','noise','seed','zoom','photo'))
    old={key(r):r for r in past}
    assert len(cases)==len(old)==468 and set(old)=={key(r) for r in cases}
    matrix=[];sensitivity=[]
    for case in sorted({r['case'] for r in cases}):
        for zoom in ('0.5','1.0','2.0'):
            cells=[]
            for ph in ('nominal','dim','bright'):
                rr=[r for r in cases if r['case']==case and r['zoom']==zoom and r['photo']==ph]
                cells.append(f"{sum(old[key(r)]['passed']=='True' for r in rr)} → {sum(r['passed']=='True' for r in rr)} / {len(rr)}")
            matrix.append([case,zoom,*cells])
    totals=[]
    for ph in ('nominal','dim','bright'):
        rr=[r for r in cases if r['photo']==ph]
        sums=lambda a,k:sum(r[k]=='True' for r in a)
        p2=[r for r in rr if r['case']=='P2_fade'];neg=[r for r in rr if r['negative']=='True']
        evt=[]
        for folder in (BASE,OUT):
            events=[r for r in read_csv(folder/'paired_events.csv') if r['photo']==ph]
            evt.append([sum(int(r[k]) for r in events) for k in ('wrong','accepted','rejected')])
        same={key(r)[:-1]:r for r in cases if r['photo']=='nominal'}
        sensitivity.append([ph,len(rr),sums(rr,'passed'),sum(old[key(r)]['passed']!=r['passed'] for r in rr),sum(same[key(r)[:-1]]['passed']!=r['passed'] for r in rr),sum(same[key(r)[:-1]]['tip']!=r['tip'] for r in rr)])
        totals.append(dict(photo=ph,weak_cases=len(events),wrong=evt[1][0],accepted=evt[1][1],rejected=evt[1][2],old_wrong=evt[0][0],old_accepted=evt[0][1],negative_fp=sums(neg,'valid'),negatives=len(neg),p2=sums(p2,'passed'),p2_cases=len(p2)))
    return matrix,sensitivity,totals

def main():
    rows,metrics,times,records=collect()
    failures=failure_report(rows,records)
    matrix,sensitivity,totals=synth()
    raw=read_csv(OUT/'raw_probes.csv');assert len(raw)==468
    full=[r for r in metrics if r['mode']=='full' and r['stage']=='v3_5']
    goals={'group_a':(18,18),'three_point_bend':(12,11),'group_c':(15,0)}
    def passed(r):
        h,j=goals[r['group']]
        return r['hit']>=h and r['joint']>=j and not r['severe']
    passed_groups=all(passed(r) for r in full)
    synt_ok=all(r['wrong']==0 and r['negative_fp']==0 and r['p2']>=10 for r in totals)
    status='RESEARCH_GATES_PASSED' if passed_groups and synt_ok else 'PRODUCTION_NO_GO'
    all_full=aggregate([r for (g,i,s,m),r in rows.items() if s=='v3_5' and m=='full'])
    prev=aggregate([r for (g,i,s,m),r in rows.items() if s=='v3_4' and m=='full'])
    changes=[(g,i,rows[g,i,'v3_4','full'],rows[g,i,'v3_5','full']) for g,i in records if rows[g,i,'v3_5','full']['state']=='VISIBLE']
    recovered=[f'{NAMES[g]} {i}' for g,i,a,b in changes if a['hit10']!='True' and b['hit10']=='True']
    lost=[f'{NAMES[g]} {i}' for g,i,a,b in changes if a['hit10']=='True' and b['hit10']!='True']
    doc=['# V3.5 双通道裂纹尖端开发与消融验证报告',
      f"**{status}。** 54 张可见标注的尖端命中由 {prev['hit']} 变为 {all_full['hit']}，联合命中由 {prev['joint']} 变为 {all_full['joint']}，严重误差 {all_full['severe']}，中位误差 {num(prev['median'])} → {num(all_full['median'])} px。恢复命中：{'、'.join(recovered) or '无'}。新增漏命中：{'、'.join(lost) or '无'}。",
      '[四栏逐帧图册](difference_views/index.html) · [失败与受损帧专项](FAILURES_AUDIT.md) · [逐候选取证表](candidate_audit.csv) · [冻结校验清单](freeze.json)',
      '## 数据范围与验收',
      '仅在开发组A和独立合成图上开发。开发组A、合成矩阵、弱带事件和五个专项样例完成后封存代码及预测哈希。三点弯先运行，验证组C在三点弯预测封存、评分完成后单次回归，两组均在历史回合有所曝光。人工标注只在各组推理封存后用于对照，不参与训练。排除组X排除。全序列 1,633 帧，60 张有标注，其中 54 张可见、6 张不确定。真实阴性误报率缺乏可核验分母。',
      '误差为原图二维距离。Hit@10 的门槛为 ≤10 px，Severe 为 >100 px。Joint 另需人工线覆盖与预测点精度均 ≥80%（距离容差 10 px）。',
      table(['实验组','可见 / 有效','前版命中 / 联合','本版命中 / 联合','严重','目标命中 / 联合','验收'],[[NAMES[r['group']],f"{r['visible']} / {r['valid']}",next(f"{x['hit']} / {x['joint']}" for x in metrics if x['group']==r['group'] and x['stage']=='v3_4' and x['mode']=='full'),f"{r['hit']} / {r['joint']}",r['severe'],f"{goals[r['group']][0]} / "+(str(goals[r['group']][1]) if goals[r['group']][1] else '未单设'),'通过' if passed(r) else '未通过'] for r in full]),
      '## 四项改动',
      '① 缺口保底与平坦区续接。纹理粗定位多峰时，在缺口左侧 0.30s 范围内提取上、下暗边，s 为锚距。搜索 ±0.025s 的平移，同时约束可见截面比例、缺口收窄幅度、上下边误差与上游零偏移先验。保底成功后，将参考减当前的正向窄脊以有限权重加入远端弱原灰度响应。固定参考足够平坦时，沿已有轨迹切向最多观察 0.065s，逐列匹配窄暗脊，满足连续性、强度和可见终止才发布续接点。',
      '② 差分前端。原候选均失效或胜出候选的全路径有效增暗比例低于 0.15 时，在已有缺口根带内沿三个方向筛选连续增暗脊种子。二次竞争融合有界原图和差分，在原有近口/全路径证据上比较。重获区必须在差分图上得到支持；强增暗候选可以复核近口轮廓拒绝，已确认闭合环仍由闭合门拒绝。',
      '③ 远端形变。沿当前尾段法向搜索 ±0.030s 的共同位移，对小段横截面作两侧补偿，要求形状相关 ≥0.80、参考深度为当前的 0.53 至 1.8 倍；沿迹向前查找连续匹配块的起点。计算前 65% 路径中强支持点的平均净增暗与尾窗/主干比。若尾段低于主干 20%、存在连续低增暗且伴转折或双极，则回剪至最后连续支持边界。已有可信回剪优先。主干有明显增暗且末端静态、找不到边界时可拒绝候选。表中原图与参考原图的坐标差含上游映射，不能单独作为残余错位测量。',
      '④ 豁免解耦。保留远端亮隙双侧验证，近口跨唇另需谷宽相容、前后切线角差 ≤0.25 rad、入口对断前外推的偏差受锚距约束，且断前及重获段均有单极新增暗线。原灰度路径统一调用已冻结的 V3.4 纯灰度实现。',
      '首轮开发中，整条轨迹融合损失了开发组A 366 等原命中帧，允许新增暗线覆盖闭环门也引入合成环状误报。第二轮限制融合位置、加入平坦区续接并恢复闭环门。第三轮保留已经有效的双极回剪，同时沿轨迹寻找形状匹配块的起点，解决开发组A 113 过度回剪。',
      '## 累加消融',
      'r02 与 s3t 分别代表早期基线及 V3。contour、front、shape、v3_5 分别依序加入上述四项。每个有标注帧均运行各阶段及两种模式。']
    for g in GROUPS:
        doc.extend(['### '+NAMES[g],table(['阶段','模式','可见 / 有效','Hit@10','Severe','Joint','中位 px','最大 px'],
         [[r['stage'],r['mode'],f"{r['visible']} / {r['valid']}",r['hit'],r['severe'],r['joint'],num(r['median']),num(r['max'])] for r in metrics if r['group']==g])])
    history=[]
    for g,ids in FOCUS.items():
        for i in ids:
            rec=records[g,i];m=rec['models']['v3_5']['full'];d=m['diagnostics'];co=d.get('coarse') or {};t=selected(m);q=t.get('reference',{});sm=q.get('shape_match') or {}
            old=rows[g,i,'v3_4','full'];r=rows[g,i,'v3_5','full']
            history.append([NAMES[g],f'[{i}](difference_views/frames/{g}/{i:04d}.jpg)',num(old['error_px']),num(r['error_px']),str(co.get('anchor'))+'/'+str(co.get('status')),q.get('source','—'),num(q.get('body_net')),num(q.get('tail_body_ratio')),sm.get('normal_shift','—'),q.get('decision','—'),q.get('cut') if q.get('cut') is not None else '—',t.get('geometry_cut') or '—',d.get('added_ridge_seeds',0),t.get('clean_extension',0)])
    doc+=['## 关键帧',
      '末窗/主干和法向匹配位移对应最终胜出候选的回剪前观测。参考裁剪列与几何门截断列均为当前原图坐标。主干无可测增暗时该比值留空。前端种子数包括在原种子位置重新取得差分支持的候选。',
      table(['组','帧','V3.4 px','V3.5 px','粗定位','末端定位','主干净增暗','尾/干','形状位移 px','复核','参考裁剪 x','几何截断 x','差分种子','平坦区续接点'],history),
      '开发组A 504 经缺口轮廓保底取零平移，沿干净参考背景续接后误差由 14.18 降至 1.17 px；398 由 4.17 降至 1.90 px。验证组C 335 触发形状查重，匹配块相关约 0.85、相对深度 0.65、沿法线残余偏移 1 px。回剪后误差由 30.64 降至 23.40 px，仍沿着部分错误斜纹。',
      '验证组C 38、54、69 补充差分种子均为零。当前方法在原种子附近的窄带寻找连续红脊，对红脊起始于原种子下游的情形仍无有效候选。三点弯 144 的胜出候选主干净增暗为零，另外三条可见正增暗的候选提前停止，新种子在根部被截断，静态兜底仍产生 59.29 px 过冲。407 虽有三次亮隙豁免，最终认证仍在第一次豁免之前。',
      '下一轮可在独立合成双唇图中把红脊起点逐步移离灰度根部，分别测量种子召回和附着误接；并将“同帧所有候选都静态”与“本候选静态而其他候选主干有增暗”分开检验。保留组继续仅作封存后验证。',
      '## 合成、曝光与性能',
      '样本覆盖三个倍率、两个噪声幅度、两个随机种子、三种曝光。弱带另交叉三种宽度和两档残余对比。P1 要求尖端命中且人工路径完全覆盖，P2 检查渐弱端点，其余阴性探针检查拒绝输出。表内是同条件 V3.4 → V3.5 的通过数/样本数。',
      table(['探针','倍率','标准','暗','亮'],matrix),
      table(['曝光','样本','通过','与前版通过状态不同','与本版标准曝光通过状态不同','与本版标准曝光尖端不同'],sensitivity),
      table(['曝光','V3.4 弱带错接 / 接受','V3.5 弱带错接 / 接受','V3.5 拒绝事件','P2 通过','阴性误报'],[[r['photo'],f"{r['old_wrong']}/{r['old_accepted']}",f"{r['wrong']}/{r['accepted']}",r['rejected'],f"{r['p2']}/{r['p2_cases']}",f"{r['negative_fp']}/{r['negatives']}"] for r in totals]),
      '独立重放 468 项纯灰度组合，逐例核对尖端及有真值时的路径覆盖、误差和标准曝光弱带事件，均与 V3.4 相同。[纯灰度对照明细](raw_probes.csv)',
      '弱带以胜出候选实际送入几何门的重获段坐标核对 GT，接受的事件数可随规则改变。按命中案例统计和按重连事件统计使用不同分母。专项样例含新线、法向错位 7 px 的已有划痕、无关单点、无锚、已知轮廓平移。[专项实测](fixtures.json) · [弱带逐事件计数](paired_events.csv) · [全部合成结果](paired_probes.csv)',
      table(['组','帧数','平均 ms','P95 ms','等效 FPS','轮廓保底帧','启动差分种子帧'],[[NAMES[r['group']],r['frames'],num(r['mean_ms']),num(r['p95_ms']),num(r['fps']),r['anchors'].get('CONTOUR',0),r['ridge_seed_frames']] for r in times]),
      '耗时为六个工作进程并行时，单帧 full 准备与识别的墙钟时间，含工作进程初次编译。等效 FPS 为平均耗时倒数，排除读图、标注评分、绘图及视频编码。核对 1,633 帧 V3.5 纯灰度输出和 V3.4 完全相同；60 张标注帧的三个历史版本、两模式共 360 条输出与旧版封存值一致。',
      '## 交付',
      '[验证组C视频](difference_views/group_c.mp4) · [三点弯视频](difference_views/three_point_bend.mp4) · [开发组A视频](difference_views/group_a.mp4) · [全部逐帧差分图](difference_views/index.html) · [失败及受损图包](failure_audit.zip) · [参考原图坐标](difference_views/coordinates.csv)',
      '每帧同时展示参考原图对应位置、当前灰度、预测结果与差分，分别查看整段裂纹和尖端局部。差分固定为参考减当前、色阶 ±32 灰度级。图册可单独打开每帧原像素尺寸的差分 PNG。']
    pack('REPORT.md',doc)
    data=dict(run=OUT.relative_to(ROOT).as_posix(),primary='v3_5',decision=status,date='2026-11-19',report='evidence/v3_5/REPORT.md',failures='evidence/v3_5/FAILURES_AUDIT.md',frames=sum(GROUPS.values()),scored_visible=54,uncertain=6,overall_full=all_full,groups=metrics,real_fpr=None,timing=times,synthetic=totals,recovered=recovered,lost=lost,audit_items=len(failures))
    save(OUT/'metrics.json',data);save(ROOT/'evidence/latest_metrics.json',data)
    print(status,all_full,recovered,lost)
if __name__=='__main__':main()
