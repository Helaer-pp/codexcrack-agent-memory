"""Build the two Chinese reports from locked detector results and offline audits."""
from ast import literal_eval
from .reports import (read_csv,write_csv,table,OUT,BASE,ROOT,GROUPS,NAMES,HIST,MODES,
                      read,save,aggregate,audit,selected,fmt,records_for_review,synthetic,pack_reports)

def main():
    rows,stats,recs,times=audit()
    reviewed=records_for_review(rows,recs)
    full=[r for r in rows.values() if r['mode']=='full' and r['stage']=='v3_4']
    overall=aggregate(full)
    decision='PRODUCTION_NO_GO'
    overview=['# V3.4 裂纹尖端追踪算法开发与消融验证报告',
      f"**{decision}。** 54 张可见标注中尖端与联合命中均由 38 帧增至 {overall['hit']} 帧。开发组达到门槛，两个保留组与含参考图的弱带错接指标未达标。开发组A 366、三点弯 413 恢复，验证组C 528 新增失败。不能将参考图的可用率直接解释为尖端准确率。",
      '[带固定参考的逐帧图册](fixed_views/index.html) · [失败帧分析](FAILURES_AUDIT.md) · [失败及受损帧图册](failure_index.html) · [逐帧坐标](frames.csv) · [冻结清单](freeze.json)',
      '## 数据与验收',
      '仅用开发组A与独立合成图开发。三点弯在冻结后作阶段对照，验证组C随后一次冻结回归。两组存在前版评测历史，本轮没有用其图像调整规则。排除组X全部排除，人工标注只在各批预测封存后评分。每组各有 20 张标注，6 张不确定位于分母之外。其余 1,573 帧仅供逐帧复查。实测序列缺少已确认阴性样本，真实误报率未知。',
      '尖端误差为原图二维欧氏距离。Hit@10 为误差 ≤10 px，Severe 为误差 >100 px，Joint 还要求人工路径覆盖率和预测点精度均 ≥80%，路径匹配容差 10 px。',
      table(['组别','V3.3 命中 / 联合','V3.4 命中 / 联合','严重','门槛（命中 / 联合）','结果'],[
        [NAMES[r['group']],{'group_a':'17 / 17','three_point_bend':'9 / 9','group_c':'12 / 12'}[r['group']],f"{r['hit']} / {r['joint']}（共 {r['visible']}）",r['severe'],{'group_a':'18 / 18','three_point_bend':'12 / 11','group_c':'15 / 未单设'}[r['group']],'通过' if r['group']=='group_a' else '未通过'] for r in stats if r['mode']=='full' and r['stage']=='v3_4']),
      '## 原灰度追踪与参考增量',
      '原灰度暗线仍生成起点、动态规划轨迹和尖端候选。以 s 表示锚距。细配准可靠时使用局部平移；低纹理、模糊峰或局部上下文不足且粗配准可靠时使用粗平移。两级均无可信对应或取样缺失时保留灰度回退。沿切线平滑三点，沿法线 ±0.014s 对补偿两侧材料亮度后的 fixed − current 积分；在 0.010s 半径内搜索参考图暗谷。',
      '单列有效需净积分超过 max(2.5 倍噪声底, 0.022 倍曝光跨度)，负正能量比小于 0.60，且通过邻域查重。固定暗谷达到当前深度的 55% 且超过噪声门才记重复，避免把孤立噪声认作划痕。持续出现重复或双极列且末窗支持不足时，从首次具有前后证据的转折处回剪，再跑原终止认证。',
      '双向豁免分别测量截断前后的净增暗。远端弱停时最多额外观察 0.060s，不直接发布观察段。通过豁免后，若重获段有至少 75% 有效列、下一处几何断点之后不超过 25% 且深度减半，可重新认证原图强灰度端点。跨唇豁免额外要求谷宽比 ≤2、断带及重获段分别至少 50% 和 80% 有效。',
      '全路径有效比例 ≥0.40 的已认证候选优先；小于 0.15 且净均值不高于两倍噪声者最后竞争。同档保留原灰度评分，并加入全路径和前 0.25s 共同支持。最终末窗要求有效比例 ≥0.45、净积分为正、负正比 <0.65。未达门且找到持续增暗边界时回剪；全段没有可信边界时标记 NO_SUPPORTED_BOUNDARY，仍可由原灰度兜底。这一例外在三点弯 144 导致过冲。',
      '开发过程中，单取邻域最大值误伤了弱尾；加入切向连续性、受限前看和重新认证后，开发组A 366 得以越过 x=1302。所有常量在保留组运行前封存。六百条历史模式/帧结果回放通过比对，整段 1,633 帧的 raw_only 输出与 V3.3 核对一致。',
      '## 分阶段消融',
      '后四级依次累加，衡量各项在前一级基础上的变化。unlock 为参考解锁与法向/暗谷检测，shield 加双向豁免，branch 加分支惩罚与跨唇豁免，v3_4 加末窗门。r02 为早期原图基线，s3t 为 V3。']
    for g in GROUPS:
        overview.extend(['### '+NAMES[g],table(['阶段','模式','可见 / 有效','Hit@10','Severe','Joint','中位 px','最大 px'],
            [[r['stage'],r['mode'],f"{r['visible']} / {r['valid']}",r['hit'],r['severe'],r['joint'],fmt(r['median']),fmt(r['max'])] for r in stats if r['group']==g])])
    old={r['group']:r for r in read_csv(BASE/'timing.csv')};avail=[]
    for r in times:
        g=r['group'];v=r['review'];o=old[g];a=literal_eval(o['review'])['NO_ALIGNMENT'];b=int(o['reviewed_candidates'])
        c=v.get('NO_ALIGNMENT',0);d=r['reviewed_candidates']
        avail.append([NAMES[g],f'{a}/{b} ({a/b:.1%})',f'{c}/{d} ({c/d:.1%})',v.get('SOURCE_FINE',0),v.get('SOURCE_COARSE',0),v.get('NO_SUPPORTED_BOUNDARY',0),fmt(o['mean_ms']),fmt(r['mean_ms']),fmt(r['fps']),fmt(r['p95_ms'])])
    overview+=['## 候选参考可用率与效率','统计分母为实际进入复核的所有候选，包括复核后失去资格者。无可信边界表示已获得信号，无法从信号确定末端。耗时为本机六工作进程并行时每帧 full 准备与推理的均值，含进程首次编译，排除图像读写、评分和编码。FPS 为平均单帧耗时的倒数。',
      table(['组','V3.3 无增量','V3.4 无增量','细定位','粗定位','无可信边界','旧均值 ms','新均值 ms','FPS','P95 ms'],avail),
      '## V3.3 的 16 张尖端超差帧',
      '表中各列来自最终胜出候选。负正比、重复占比、有效占比与净积分取裁剪决策前末窗，裁剪列为被排除的第一列，最终尖端由灰度门重新认证。未获得参考时记为 —。']
    hist=[]
    for g,ids in HIST.items():
        for i in ids:
            p=rows[g,i,'v3_3','full'];r=rows[g,i,'v3_4','full'];m=recs[g,i]['models']['v3_4']['full'];t=selected(m);q=t['reference']
            hist.append([NAMES[g],i,fmt(p['error_px']),fmt(r['error_px']),q['source'],fmt(q['net']),fmt(q.get('ratio')),fmt(q.get('duplicate')),fmt(q['fraction']),q['decision'],q['cut'] or '—',str(t['waived']),'命中' if r['hit10']=='True' else '超差'])
    overview.append(table(['组','帧','V3.3 px','V3.4 px','定位','净积分','负正比','重复占比','有效占比','复核','裁剪列','豁免列','结果'],hist))
    candidates=[]
    for (g,i),rec in recs.items():
        if i not in HIST[g] and (g,i)!=('group_c',528):continue
        for s in ('v3_3','unlock','shield','branch','v3_4'):
            d=rec['models'][s]['full']['diagnostics']
            for j,c in enumerate(d['candidates']):
                t=c['trace'];q=t.get('reference',{});rk=t.get('increment_rank',{})
                candidates.append(dict(group=g,frame=i,stage=s,candidate=j,selected=j==d['selected'],start=c['start'],tip=c['tip'],status=c['status'],geometry=t.get('geometry'),geometry_cut=t.get('geometry_cut'),gate=t.get('gate'),waived=t.get('waived'),lip=t.get('waived_lip'),events=t.get('events'),tier=rk.get('tier'),fraction=rk.get('fraction'),near=rk.get('near_fraction'),mean=rk.get('mean'),reference=q))
    write_csv(OUT/'historical_candidates.csv',candidates)
    overview+=['[重点帧逐候选记录](historical_candidates.csv)',
      '验证组C 54、69 每帧有 14 个种子。最终可竞争分支均为静态档，末端分别汇到 x=2272、2274。上侧种子既有 OTHER_LIP，也有根部附着和轮廓门拒绝；两帧均未触发跨唇豁免。排序时已没有有效增暗比例 ≥0.40 的有效候选可以改选。仅凭这些结果不能证实被拒分支都是真裂纹。',
      '三点弯 144 的静态虚尾复核已由 RETAIN 变为无可信边界，仍被兜底选中；另有尖端靠近人工的候选，但未胜出。407 的三处亮隙已获豁免，终止认证仍退回原位置。验证组C 335 末窗有效占比 0.50，超过 0.45 门槛，参考图可用后仍放行。363 的查重回剪至 x=2474，重新认证在 x=2471 停下，方向得到纠正但尖端提前。528 豁免 x=2516 后向右越过人工尖端。',
      '## 合成探针与曝光']
    matrix,comp,gap,scale=synthetic()
    overview+=[table(['模式','探针','倍率','nominal','dim','bright'],matrix),
        table(['模式','曝光','通过数','较同版 nominal 翻转','尖端坐标变化'],comp),
        table(['模式','倍率','nominal 阴性 FP','dim','bright'],scale)]
    events=[]
    for name,label in [('previous_paired_events.csv','V3.3 full'),('paired_events.csv','V3.4 full')]:
        a=read_csv(OUT/name)
        for ph in ('nominal','dim','bright'):
            b=[r for r in a if r['photo']==ph]
            events.append([label,ph,len(b),*[sum(int(r[k]) for r in b) for k in ('accepted','wrong','wrong_lip_waivers')],sum(r['passed']=='True' for r in b)])
    overview+=[table(['原灰度模式','nominal 弱带数','接受事件','错接','整例通过'],gap),table(['模式','曝光','弱带数','接受事件','错接','其中由跨唇豁免放行','整例通过'],events),
      '按实际送入几何门的动态规划坐标复核选中路径的重获区间，少于 80% 点落在 2.5 倍倍率像素容差内计错接。标准曝光下纯灰度仍为 0/22；含参考模式由 0/22 变成 2/24，均来自新增跨唇豁免。整体通过数会漏掉这种事件级退化。较暗及较亮曝光也存在错接。开发材料上的下一次测试应先解耦远端亮隙与近口跨唇豁免，保留开发组A 366 作正对照，逐一复测错误重获事件，再考虑新保留组。',
      '[含参考弱带事件明细](paired_events.csv) · [V3.3 含参考对照](previous_paired_events.csv) · [曝光及倍率明细](paired_probes.csv)']
    def key(r):return tuple(r[k] for k in ('case','width','contrast','noise','seed','zoom','photo'))
    prior={key(r):r for r in read_csv(BASE/'paired_probes.csv')};new=read_csv(OUT/'paired_probes.csv')
    assert len(prior)==len(new)==468
    flip=sum(r['passed']!=prior[key(r)]['passed'] for r in new)
    overview.append(f'相同曝光、倍率、噪声和种子下，V3.4 full 相对 V3.3 full 的整例通过状态翻转 {flip}/468。标准曝光 P2 渐弱探针为 10/12。420 项公共检查通过。以下独立样例分离了光滑背景无细配准与残余错位两种情况。')
    overview.append(table(['专测','定位','判断','净积分','负正比','重复占比','裁剪列'],[[x['case'],x['measure']['source'],x['measure']['decision'],fmt(x['measure']['net']),fmt(x['measure'].get('ratio')),fmt(x['measure'].get('duplicate')),x['measure']['cut'] or '—'] for x in read(OUT/'residual_tests.json')]))
    overview+=['## 交付与复查','[开发组A视频](fixed_views/group_a.mp4) · [三点弯视频](fixed_views/three_point_bend.mp4) · [验证组C视频](fixed_views/group_c.mp4) · [失败帧固定参考对照](fixed_views/failure_comparisons.zip) · [两种模式失败与受损图包](failure_frames.zip)',
      '每组视频包含全部帧。参考图、当前原图和预测叠图采用同倍率窗口，配准等级与参考原图坐标逐帧显示。人工对照可在图册中筛选。']
    pack_reports('REPORT.md',overview)
    metrics=dict(run=OUT.relative_to(ROOT).as_posix(),primary='v3_4',decision=decision,date='2026-11-19',report='evidence/v3_4/REPORT.md',failures='evidence/v3_4/FAILURES_AUDIT.md',frames=1633,scored_visible=54,uncertain=6,overall_full=overall,groups=stats,real_fpr=None,timing=times,paired_events=events,synthetic_case_flips=flip)
    save(OUT/'metrics.json',metrics)
    save(ROOT/'evidence/latest_metrics.json',metrics)
    print(overall,len(reviewed),events,flush=True)

if __name__=='__main__':main()
