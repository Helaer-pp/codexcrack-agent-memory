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
    full=[r for r in metrics if r['mode']=='full' and r['stage']=='v3_6']
    goals={'group_a':(19,19),'three_point_bend':(12,11),'group_c':(15,0)}
    def passed(r):
        h,j=goals[r['group']]
        return r['hit']>=h and r['joint']>=j and not r['severe']
    passed_groups=all(passed(r) for r in full)
    synt_ok=all(r['wrong']==0 and r['negative_fp']==0 and r['p2']>=10 for r in totals)
    status='RESEARCH_GATES_PASSED' if passed_groups and synt_ok else 'PRODUCTION_NO_GO'
    all_full=aggregate([r for (g,i,s,m),r in rows.items() if s=='v3_6' and m=='full'])
    prev=aggregate([r for (g,i,s,m),r in rows.items() if s=='v3_5' and m=='full'])
    changes=[(g,i,rows[g,i,'v3_5','full'],rows[g,i,'v3_6','full']) for g,i in records if rows[g,i,'v3_6','full']['state']=='VISIBLE']
    recovered=[f'{NAMES[g]} {i}' for g,i,a,b in changes if a['hit10']!='True' and b['hit10']=='True']
    lost=[f'{NAMES[g]} {i}' for g,i,a,b in changes if a['hit10']=='True' and b['hit10']!='True']
    from .horizontal import measure
    horizontal=measure(records,rows)
    doc=['# V3.6 裂纹尖端精准修补开发与消融验证',
      f"**{status}**。共 54 张可见标注，尖端命中 {prev['hit']} → {all_full['hit']}，联合命中 {prev['joint']} → {all_full['joint']}。中位误差 {num(prev['median'])} → {num(all_full['median'])} px，严重误差 {all_full['severe']}。恢复命中：{'、'.join(recovered) or '无'}。新增漏命中：{'、'.join(lost) or '无'}。",
      '[四栏逐帧图册及差分 PNG](difference_views/index.html) · [失败与受损帧分析](FAILURES_AUDIT.md) · [全部候选记录](candidate_audit.csv) · [冻结清单](freeze.json)',
      '## 规则与数据范围',
      '仅以开发组A和独立合成图开发。封存代码、开发组A预测、评分与合成探针后，依次运行三点弯和验证组C，验证组C仅回归一次。两个验证组都有历史评测记录。人工标注只用于封存后的对比，排除组X排除。共 1,633 帧，其中 54 帧可见、6 帧人工不确定、1,573 帧未标注。真实严重误差按可见标注评分，真实阴性误报率无可核验分母。',
      '① 全口门补种。原胜出候选缺少连续增暗边界或全路径增暗占比低于 0.15 时，沿缺口上下唇全高度扫描至前缘右方 0.10 倍锚距。逐列积分正负差分，负正比 <0.50，五个方向检验约 0.043 倍锚距上的连续支持。候选必须与当前原图的缺口暗区连通。根部 OTHER_LIP 增加断带与重获段的单极差分审查；续接到已知闭环末端的种子仍被排除。',
      '② 同帧竞争。先检查已通过几何、拓扑和长度要求的候选。存在主干或局部显著增暗的非静态候选时，清除主干为零或标记 NO_SUPPORTED_BOUNDARY 的参考可用候选，再按原规则排名。若全帧只有静态候选，保留灰度兜底。',
      '③ 回溯和水平断带。原复核命中形状或暗谷重复时，从已有裁剪列向左最多观察 0.15 倍锚距，按当前坐标补齐断开的列。结合净增暗低谷、前方已有支持、超过 18° 的方向变化与转折后增暗衰减确定裁剪列，重新认证尖端。对没有形状命中的尾部，要求连续约 0.02 倍锚距降至噪声门以下，且重新出现的部分支持比例不超过 0.32，才提前截断。随曝光与噪声缩放，避免用统一尾/干比误砍渐弱真尾。',
      '首轮全口门扫描将与缺口分离的合成暗线也作为起点，标准曝光有 25/48 次阴性误报。增加暗区连通和闭环末端核验后再冻结。独立专项中，预存近口段右侧的新增脊线能被检出，断开或同图对照被拒；形状匹配后回剪列从 356 回溯到 343。[专项结果](fixtures.json)',
      '## 累加消融与验收',
      'mouth、veto、v3_6 依次增加上述三项。尖端命中要求二维误差 ≤10 px，联合命中另要求覆盖及精度均 ≥80%，严重误差为 >100 px。']
    doc.append(table(['组别','阶段（full）','可见 / 有效','Hit@10','Joint','Severe','中位 px','最大 px'],[
        [NAMES[r['group']],r['stage'],f"{r['visible']} / {r['valid']}",r['hit'],r['joint'],r['severe'],num(r['median']),num(r['max'])] for r in metrics if r['mode']=='full']))
    doc.append(table(['组别','命中 / 联合目标','结果','纯灰度命中 / 联合'],[
        [NAMES[r['group']],f"{goals[r['group']][0]} / "+(str(goals[r['group']][1]) if goals[r['group']][1] else '未单设'),'通过' if passed(r) else '未通过',next(f"{x['hit']} / {x['joint']}" for x in metrics if x['stage']=='v3_6' and x['mode']=='raw_only' and x['group']==r['group'])] for r in full]))
    doc.extend(['纯灰度全序列的状态、起点、路径点和终点与 V3.5 逐帧一致。60 张有标注帧的 V3.5 双模式重放也与原封存结果一致。[两种模式全部消融与连续指标](ablation.csv)',
      '## V3.5 的全部尖端超差帧',
      '误差按原图像素；全口门种子计入非极大抑制后提出的种子，静态淘汰数取最终一次候选竞争；前后裁剪列均为当前图坐标。'])
    oldmiss=[];detailed=[]
    for g,i,a,b in changes:
        if a['hit10']=='True':continue
        rec=records[g,i];m=rec['models']['v3_6']['full'];d=m['diagnostics'];t=selected(m);q=t.get('reference',{})
        oldmiss.append([NAMES[g],f'[{i}](difference_views/frames/{g}/{i:04d}.jpg)',num(a['error_px']),num(b['error_px']),d.get('whole_mouth_seeds',0),sum(bool(c.get('static_veto')) for c in d['candidates']),q.get('source','—'),q.get('decision','—'),q.get('prior_cut') or '—',q.get('cut') or '—'])
    assert len(oldmiss)==14
    doc.append(table(['组别','帧','V3.5 px','V3.6 px','全口门种子','淘汰静态','配准','终点复核','回溯前 x','最终裁剪 x'],oldmiss))
    doc.append('全口门补种使验证组C 38 的尖端误差由 18.68 降到 9.64 px；验证组C 54、69 分别补出 5、7 个种子，但同帧仅有一条差分种子候选通过认证，仍回到静态近口阴影。三点弯 144 最终淘汰 4 条静态候选，胜出尖端由 x=1591 改为 x=1502；相对人工端点从过冲变为提前，仍差 33.55 px。静态淘汰同时作用于首轮与补种后的竞争，因此在首轮胜出分支已改变时，补种触发次数也会改变。')
    doc.append('验证组C 335 的裁剪列由 x=2488 回溯至 x=2469，重新认证的端点为 (2468,2345)，误差 2.18 px。验证组C 363 同样触发回溯，但在原本就提前的路径上又少追了一列，误差 12.17 → 13.03 px。验证组C 7 的尖端坐标相同，起点由 (2252,2337) 移至 (2255,2333)，人工路径覆盖由 100% 降到 94.4%。54、69 的覆盖也有下降。')
    doc.extend(['## 验证组C水平过冲专项','离线把胜出路径映射到连续原图列，统计位于人工尖端 x 右侧的部分。使用胜出候选复核的参考平移，双侧材料校正，净积分 ≤max(2 倍噪声, 0.012 倍曝光跨度) 计低增暗。表中给出连续低值最大列数与该帧所需长度。照明、亚像素错位或人工端点差异都可能贡献残差信号。[两版本逐帧测量](horizontal_tail.csv)',
      table(['帧','越过人工端点列数','平均净积分','负正比','暗谷重复比例','低值连续列 / 所需列','豁免列'],[[r['frame'],r['columns'],num(r['net']),num(r['neg_pos']),num(r['duplicate']),f"{r['low_run']} / {r['needed']}",r['waived']] for r in horizontal if r['stage']=='v3_6']),
      '456、510、528 在越过人工端点后均没有连续低于噪声门的列；195 最长低值段达到 4 列，附加前后支持条件未使其截断。对这四帧，单纯继续收紧相对主干强度缺乏依据。',
      '## 合成探针与效率',
      table(['曝光','弱带错接 / 接受（旧）','弱带错接 / 接受（新）','P2 命中','阴性 FP'],[[r['photo'],f"{r['old_wrong']}/{r['old_accepted']}",f"{r['wrong']}/{r['accepted']}",f"{r['p2']}/{r['p2_cases']}",f"{r['negative_fp']}/{r['negatives']}"] for r in totals]),
      table(['曝光','样本','通过','较前版通过状态变化','较标准曝光状态变化','较标准曝光尖端变化'],sensitivity),
      '暗曝光、0.5 倍率、噪声 5、种子 17 下，P1 下唇和一例 P1 弱带由通过转为未通过；路径覆盖分别由 100% 降至 86.4%、92.4%。合成的 P1 要求路径完全覆盖。已接受的重获事件仍全部符合局部身份检验。',
      '每档曝光的 48 个阴性样本由 0.5、1、2 倍三个倍率各 16 个组成。弱带每档 72 个样本，分母为实际接受的重连事件数。另有 468 个纯灰度用例与前版逐项核对。[按缩放和噪声的合成记录](paired_probes.csv) · [弱带记录](paired_events.csv) · [纯灰度记录](raw_probes.csv)',
      table(['实验组','帧数','平均 ms','P95 ms','等效 FPS'],[[NAMES[r['group']],r['frames'],num(r['mean_ms']),num(r['p95_ms']),num(r['fps'])] for r in times]),
      '耗时为本机六工作进程并行时的单帧 full 准备与识别时间，含进程首次编译，不含输入读取、评测、绘图、视频编码。等效 FPS 为平均单帧耗时的倒数。',
      '[验证组C视频](difference_views/group_c.mp4) · [三点弯视频](difference_views/three_point_bend.mp4) · [开发组A视频](difference_views/group_a.mp4) · [失败与受损图包](failure_audit.zip) · [对应坐标](difference_views/coordinates.csv)'])
    pack('REPORT.md',doc)
    data=dict(run=OUT.relative_to(ROOT).as_posix(),primary='v3_6',decision=status,date='2026-11-19',report='evidence/v3_6/REPORT.md',failures='evidence/v3_6/FAILURES_AUDIT.md',frames=sum(GROUPS.values()),scored_visible=54,uncertain=6,overall_full=all_full,groups=metrics,real_fpr=None,timing=times,synthetic=totals,recovered=recovered,lost=lost,audit_items=len(failures))
    save(OUT/'metrics.json',data);save(ROOT/'evidence/latest_metrics.json',data)
    print(status,all_full,recovered,lost)
if __name__=='__main__':main()
