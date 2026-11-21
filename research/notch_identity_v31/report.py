"""Report exclusively from sealed outputs, including failed annotated frames."""
import json
from collections import Counter
from pathlib import Path
import numpy as np
from .batch import ROOT,OUT,V3,GROUPS,ALGS,read,save,sha,sources
from research.v3_labelme_comparison.infer import read_csv
from research.v3_labelme_comparison.compare import write_csv,table

NAMES={'group_a':'开发组A','three_point_bend':'三点弯','group_c':'验证组C'}
WHY={'JOINT_HIT':'联合命中','TIP_SHORT':'尖端提前','TIP_OVERSHOOT':'向右过冲','LATERAL_TIP_ERROR':'纵向偏差主导',
     'PATH_MISMATCH':'尖端命中、路径未达标','UNCERTAIN_LABEL':'人工不确定'}

def val(x):
    return float(x) if x not in (None,'') else None

def num(x):
    return '—' if val(x) is None else f'{float(x):.2f}'

def yes(r,k):
    return r[k]=='True'

def aggregate(rs):
    vis=[r for r in rs if r['state']=='VISIBLE']
    errors=[float(r['error_px']) for r in vis if r['error_px']]
    return dict(visible=len(vis),valid=len(errors),hit=sum(yes(r,'hit10') for r in vis),joint=sum(yes(r,'joint') for r in vis),
                severe=sum(yes(r,'severe') for r in vis),median=float(np.median(errors)) if errors else None,max=max(errors,default=None))

def records(g):
    path=OUT/(g+'.jsonl');assert sha(path)==read(OUT/(g+'_seal.json'))['predictions']
    with path.open() as f:yield from map(json.loads,f)

def main():
    assert sources()==read(OUT/'freeze.json')['sources']
    assert read(OUT/'delivery_check.json')['cards']==1633
    allrows=[r for g in GROUPS for r in read_csv(OUT/(g+'_scores.csv'))]
    key={(r['group'],int(r['frame']),r['mode'],r['stage']):r for r in allrows}
    m=[dict(stage=s,group=g,mode=mode,**aggregate([r for r in allrows if (r['group'],r['stage'],r['mode'])==(g,s,mode)]))
       for s in ALGS for g in GROUPS for mode in ('full','raw_only')]
    write_csv(OUT/'ablation_metrics.csv',m)
    final=[r for r in allrows if r['stage']=='v3_1' and r['mode']=='full' and r['state']=='VISIBLE']
    stats=aggregate(final)
    damaged=[];manual=[];timings=[];data215=None
    for g in GROUPS:
        ts=[]
        for rec in records(g):
            ts.append(rec['models']['v3_1']['seconds'])
            if len(rec['models'])==1:continue
            f=rec['frame']
            for mode in ('full','raw_only'):
                new=key[g,f,mode,'v3_1']
                if new['state']!='VISIBLE':continue
                final_model=rec['models']['v3_1'][mode]
                diagnostic=final_model['diagnostics']
                for ref in ('r02','s3t'):
                    old=key[g,f,mode,ref]
                    flags=[]
                    for field in ('hit10','joint'):
                        if yes(old,field) and not yes(new,field):flags.append(field+'_lost')
                    if val(old['error_px']) is not None and (val(new['error_px']) is None or float(new['error_px'])>float(old['error_px'])+1e-9):flags.append('error_up')
                    for field in ('coverage','precision'):
                        if float(old[field])>float(new[field])+1e-9:flags.append(field+'_down')
                    if not yes(old,'severe') and yes(new,'severe'):flags.append('new_severe')
                    if not flags:continue
                    old_out=rec['models'][ref][mode]
                    first=next((z for z in ALGS[ALGS.index(ref)+1:] if (rec['models'][z][mode]['tip'],rec['models'][z][mode]['points'])!=(old_out['tip'],old_out['points'])),None)
                    damaged.append(dict(group=g,frame=f,mode=mode,baseline=ref,regression=','.join(flags),first_output_change=first,
                         old_error=old['error_px'],error=new['error_px'],dx=new['dx'],dy=new['dy'],old_coverage=old['coverage'],coverage=new['coverage'],
                         old_precision=old['precision'],precision=new['precision'],terminal_gate=new['gate'],stop=new['stop'],failure=new['failure']))
                if mode=='full':
                    old=key[g,f,mode,'s3t']
                    manual.append(dict(group=g,frame=f,old_tip=rec['models']['s3t'][mode]['tip'],tip=final_model['tip'],gt=new['gt'],
                        old_error=old['error_px'],error=new['error_px'],dx=new['dx'],dy=new['dy'],old_coverage=old['coverage'],coverage=new['coverage'],
                        precision=new['precision'],result=new['failure'],gate=new['gate'],body=new['body'],tail=new['tail'],front=new['front'],stop=new['stop'],
                        first_loss=new['first_loss'],reconnections=new['reconnections'],overlay=f'labels/{g}/{f}.png'))
            if g=='three_point_bend' and f==215:data215=rec
        times=np.array(ts)
        timings.append(dict(group=g,n=len(ts),mean_ms=times.mean()*1000,p95_ms=np.percentile(times,95)*1000,worst_ms=max(ts)*1000,
                            worst_frame=int(times.argmax())+1,inverse_mean_fps=1/times.mean()))
    write_csv(OUT/'regressions.csv',damaged);write_csv(OUT/'visible_failure_audit.csv',manual);write_csv(OUT/'timing.csv',timings)
    assert data215 is not None
    branches=[]
    for alg in ('s3t','gap','taper','weak_ref','v3_1'):
        d=data215['models'][alg]['full']['diagnostics']
        for i,c in enumerate(d['candidates']):
            a=c.get('trace',{})
            branches.append(dict(stage=alg,id=i,selected=i==d['selected'],start=c['start'],tip=c['tip'],status=c['status'],first_loss=a.get('first_loss'),
                                 reconnections=a.get('reconnections'),gate=a.get('gate'),stop=a.get('stop'),merge_pairs=[p for p in d['pairs'] if i in p[:2]]))
    write_csv(OUT/'frame215_candidates.csv',branches)
    probe=read_csv(OUT/'probes.csv')
    nominal=[r for r in probe if r['photo']=='nominal']
    gap=read_csv(OUT/'synthetic_reconnections.csv')
    ptable=[];photos=[];gap_rows=[]
    for case in dict.fromkeys(r['case'] for r in nominal):
        for zoom in ('0.5','1.0','2.0'):
            line=[case,zoom]
            for s in ('r02','s3t','v3_1'):
                rs=[r for r in nominal if (r['case'],r['zoom'],r['stage'])==(case,zoom,s)]
                n=len(rs);good=sum(yes(r,'passed') for r in rs)
                rate=f'{good}/{n}'
                if yes(rs[0],'negative'):rate+=f'（FP {n-good}/{n}）'
                line.append(rate)
            ptable.append(line)
    for photo in ('nominal','dim','bright'):
        for s in ('s3t','v3_1'):
            rs=[r for r in probe if r['photo']==photo and r['stage']==s]
            orig={(r['case'],r['width'],r['factor'],r['zoom'],r['noise'],r['seed']):r for r in nominal if r['stage']==s}
            changes=sum(r['passed']!=orig[r['case'],r['width'],r['factor'],r['zoom'],r['noise'],r['seed']]['passed'] for r in rs)
            coords=sum(r['tip']!=orig[r['case'],r['width'],r['factor'],r['zoom'],r['noise'],r['seed']]['tip'] for r in rs)
            photos.append([photo,s,f"{sum(yes(r,'passed') for r in rs)}/{len(rs)}",changes,coords])
    for w in (4,9,16):
        for factor in (0.,.2):
            rs=[r for r in gap if int(r['width'])==w and float(r['factor'])==factor]
            n=sum(int(r['injected_band_accepted']) for r in rs);bad=sum(int(r['wrong_injected']) for r in rs)
            lost=[float(r['first_loss_x']) for r in rs if r['first_loss_x']]
            gap_rows.append([w,factor,len(rs),n,f'{bad}/{n}' if n else '—',num(np.median(lost)) if lost else '—'])
    small=[]
    for name in ('r01','r02','r03','r04'):
        directory=OUT.with_name('v31_weak_crack_20261119_'+name)
        a=aggregate([r for r in read_csv(directory/'group_a_scores.csv') if r['stage']=='v3_1' and r['mode']=='full'])
        probes=read_csv(directory/'probes.csv')
        pf=[r for r in probes if r['photo']=='nominal' and r['case']=='P2_fade' and r['stage']=='v3_1']
        small.append([name,a['hit'],a['joint'],a['severe'],f"{sum(yes(r,'passed') for r in pf)}/12"])
    explain={'r02':'冻结原灰度对照','s3t':'冻结 V3','gap':'① 切向与条件重连','taper':'② 加渐弱终止与背景中值','weak_ref':'③ 加弱区辅助','v3_1':'④ 加曝光、尺度与轮廓自适应'}
    sections=['# V3.1 裂纹尖端追踪算法弱裂纹修复与普适性验证报告',
    '2026-11-19 · 完整版本 v3_1，最终开发轮 r04。**生产验收未通过**。',
    '[1,633 张逐帧原图与识别图、60 张人工叠图](index.html) · [逐帧坐标与状态](frames.csv) · [标注可见帧逐帧归因](visible_failure_audit.csv) · [开发组A视频](group_a.mp4) · [三点弯视频](three_point_bend.mp4) · [验证组C视频](group_c.mp4)',
    '## 1　执行摘要与实际代码差异',
    f"所有 1,633 帧均输出正式尖端。54 张人工尖端可见帧中，完整模式 Hit@10 为 {stats['hit']}/54，Joint 为 {stats['joint']}/54；另有 6 张人工不确定。没有独立阴性标注，因此无法由这些帧估算真实误报率。开发组A恢复了原先提前截断的四帧；三点弯 215 重新选中下唇。验证组C固定回归退化。",
    '任务书的伪代码与本地冻结实现有版本差异。V3 已使用增量斜率记忆，实际连续弱区预算约 0.014s、主干比例门为 0.18，整段排名已有 length/s。本文以本地 SHA256 冻结源码为参照，s 是当前锚点距离。P4_ring/open 在 V3 的 4/12、5/12 是误报数。',
    table(['模块 / 函数','实现与物理含义'],[
       ['detector.locate_root / exposure','最终版用提示点附近 3% 与 70% 灰度分位差定义曝光范围；在该范围的 28% 水平提取连通缺口。形态学内核随锚距缩放。'],
       ['terminal.prepare / valley','双侧暗谷半径 0.007/0.014/0.024s；背景采用逐列分位与局部中位的较大值；暗谷侧翼下限、噪声底和弱深度随曝光范围变化。'],
       ['trace_windowed','DP 每步惩罚偏离局部切向，强支持时更新斜率。近起点 0.35s 内保留最长 0.045s 的缺测段，须在 0.05s 窗内重获均值 ≥1.05、强支持占比 ≥80%，失败回滚。只输出获认证的观测点。'],
       ['follow','保留原有强通道，另以局部主干、前方材料、MAD、曲率约束认证渐弱尾端；仅在弱带后长距离出现低幅、跨两个滞后重复的纹理时尝试回剪。终止时保存门型和实测谷深。'],
       ['predict / 候选竞争','DP 差分仅在 0.55≤sig<1 生效，两路总增益 ≤0.08，近缺口前 0.2s 屏蔽。主干、尖端及重获强支持用纯灰度验证。保留 V3 的无量纲长度排名，前段深度按局部对比度归一化。'],
       ['topology.check','沿用原有孔洞/厚边检查，再按尺度闭合细缝，按面积/s²、宽高/s 与相对灰度过滤闭环及短斜开口边。'],
       ['probes.sample','下唇中段独立改变断带宽度及残余对比度，同时保留另一唇，记录错误重接与首个丢失位置。']]),
    '最终版保留离散图像的一像素采样、邻域梯度及 8 位输入接口；继承的上游 ROI/配准仍沿用原冻结设置。新增自适应作用于追踪核心，真实曝光扰动尚未重新采集验证。',
    '## 2　分阶段消融与隔离',
    '仅使用开发组A和合成图开发。下表前四轮为开发记录；r04 封存后只对三点弯作阶段对照并一次性处理已曝光的验证组C。所有阈值均在验证组C推理前冻结。排除组X及任务书以外的组均未参与。人工标签在相应组预测封存后单独比较。',
    table(['开发轮次','开发组A Hit/19','Joint/19','>100 px','P2_fade'],small),
    '下表全部取相同的 54 张可见标注。各阶段及 r02 都用当前输入重算，完整 V3.1 另跑全序列；full 含有界辅助差分。Hit 的容差为 10 原图像素；Joint 另需人工路径覆盖、预测点精度均 ≥80%。严重误差为 >100 px；误差分布只统计有效尖端。',
    table(['阶段','组别','模式','可见/有效','Hit@10','Joint','严重','中位 px','最大 px'],[[explain[r['stage']],NAMES[r['group']],r['mode'],f"{r['visible']}/{r['valid']}",r['hit'],r['joint'],r['severe'],num(r['median']),num(r['max'])] for r in m]),
    '完整模式在三组的 Hit、Joint、严重误差计数均与 raw_only 持平。此结论限于本次标注分母，不构成针对任意未来图像的保证。[消融指标 CSV](ablation_metrics.csv) · [冻结指纹](freeze.json)',
    '## 3　关键反例与失败帧',
    '三点弯 215 原下唇候选到 x=1505。V3.1 所选下唇从 (1474,2729) 出发，首次连续失去支持在 x=1507，确认重连 1 次，最终到 (1612,2718)。上下唇候选的端点相同，竞争器登记 x_merge=1612；该值可由端点接近触发，不足以确定更早的持续重合位置。V3 → V3.1 的覆盖率 57.4% → 100%，预测路径精度达到 100%，端点误差 2.08 → 7.02 px，本帧联合命中。[第 215 帧叠图](labels/three_point_bend/215.png) · [逐候选诊断](frame215_candidates.csv)',
    table(['开发组A帧','V3 尖端 → V3.1 尖端','误差 px（旧 → 新）','认证通道','主干 / 尾部 / 前方谷深'],[
      [r['frame'],f"{r['old_tip']} → {r['tip']}",f"{num(r['old_error'])} → {num(r['error'])}",r['gate'],f"{num(r['body'])} / {num(r['tail'])} / {num(r['front'])}"] for r in manual if r['group']=='group_a' and r['frame'] in (366,451,504,542)]),
    '完整模式逐组列出全部可见失败。尖端与标注的偏差方向可由坐标直接复核；过冲帧的尾点符合当前认证条件，但超出标注尖端，具体微观纹理身份仍需独立材料证据。覆盖或精度不合格且端点正确时单列路径失败。']
    for g in GROUPS:
        failed=[r for r in manual if r['group']==g and r['result']!='JOINT_HIT']
        sections.append(table([NAMES[g]+'帧','原因','dx / dy px','二维误差 px','覆盖 / 精度','尾端认证'],[
          [r['frame'],WHY.get(r['result'],r['result']),f"{num(r['dx'])} / {num(r['dy'])}",num(r['error']),
           f"{num(r['coverage'])} / {num(r['precision'])}",r['gate']] for r in failed]))
    sections.append('受损记录包含命中丢失、误差增加、覆盖或精度下降。下表列出相对两个基线丢失 Hit / Joint 的帧号；所有连续量退化及首次输出发生变化的阶段列入[逐帧受损清单](regressions.csv)。首个输出变化只能定位阶段，不能独自证明因果。')
    sections.append('阶段对比把主要退化定位在第②步。只改切向与近缺口重连时，三点弯保持 10/15 个尖端命中，联合从 1 增至 7；验证组C仍有 13/20 联合命中。叠加渐弱终止和背景中值后，三点弯端点命中降至 5，验证组C联合降至 8。两项改动在同一阶段引入，不能由这个对照单独归因于某个阈值。三点弯第 1 帧覆盖与精度均为零，即使使用强门也沿错路径；验证组C第 38 帧尖端仍命中，但预测路径精度 77% 低于门槛。')
    loss=[]
    for g in GROUPS:
        for mode in ('full','raw_only'):
            for ref in ('r02','s3t'):
                rs=[r for r in damaged if (r['group'],r['mode'],r['baseline'])==(g,mode,ref)]
                loss.append([NAMES[g],mode,ref,*[', '.join(str(r['frame']) for r in rs if s in r['regression']) or '—' for s in ('hit10_lost','joint_lost')]])
    sections.extend([table(['组','模式','对照','丢失 Hit','丢失 Joint'],loss),
        '## 4　弱断带与倍率合成探针',
        '宽度、位置与误差都按基准倍率定义。原有 P1 要求整条人工线在 2.5 个基准像素内且尖端误差 ≤10，P2 要求尖端误差 ≤10；P3/P4 是负例。弱带样本沿用 P1 严格全覆盖口径，另报实际重连接受与错误，避免把跨过一段缺测直接算路径成功。噪声档为 1、5，随机种子为 17、31，正负例阈值沿用原评价器。',
        table(['探针','倍率','r02 通过','V3 通过','V3.1 通过'],ptable),
        '弱带起始 x=94；宽度以基准像素计，残余对比度比例为 0 或 0.2。下表只统计最终入选轨迹中，与注入弱带相交且通过再获门的事件。若再获窗口中落在真下唇 2.5 个基准像素内的观测少于 80%，记为错误重接。首次连续失去支持的位置为选中轨迹的归一化 x，分母含有损失记录的轨迹。',
        table(['宽度','残余对比度','样本','正式重接','错误 / 重接','首次失去支持 x 中位'],gap_rows),
        '共 72 个弱带样本，其中 30 次正式重接与注入带相交，8/30 连接到了错误路径。强证据重获不能单独证明仍在原唇。渐弱线达到 9/12，未达 10/12。分辨率缩小时的噪声/采样损失及尽端的点状纹理仍是限制。[全部探针数据](probes.csv) · [重连事件审计](synthetic_reconnections.csv)',
        '## 5　普适性与效率',
        '在相同几何与种子上对输入灰度施加仿射扰动并裁剪到 uint8。dim 为 0.65I+9，bright 为 1.16I+15。下表同时检查验收翻转和尖端坐标变化。分母含 72 个弱带样本，不能解读为真实材料的准确率。',
        table(['曝光','版本','通过 / 总数','相对原曝光通过状态改变','端点坐标或有效性改变'],photos),
        '批量推理使用六个 CPU 工作进程。以下按每帧计时，含 ROI 内 prepare、辅助矩阵构造与一次 full 预测，排除缓存读盘、评分、画图及视频编码。FPS 为平均耗时倒数，未测工业相机端到端吞吐。',
        table(['组别','帧数','平均 ms','P95 ms','最坏 ms（帧）','平均耗时倒数 FPS'],[
            [NAMES[t['group']],t['n'],num(t['mean_ms']),num(t['p95_ms']),f"{num(t['worst_ms'])}（{t['worst_frame']}）",num(t['inverse_mean_fps'])] for t in timings]),
        '每个起点的 DP 沿 x 单向推进，最多 16 个起点，重连缓冲受缺口宽度和重获窗口约束；本批 1,633 帧均完成。尾段周期检查会扫描部分后缀，随 ROI 尺度和长度增长，尚无任意尺寸实时上界。420 行原公共合成自检全部一致。[完整性和视频解码核验](delivery_check.json)',
        '## 6　生产验收与遗留边界',
        '开发组A full/raw_only 均达 16/19 且无严重误差。三点弯 Joint 为 5/15，未达 8/15；验证组C Joint 为 9/20，未守住 13/20。弱渐变探针亦未过门，结论为 **PRODUCTION_NO_GO**。'])
    issues=[['弱带后误接到相邻唇','合成弱带正式重接中 8/30 关联错误，三点弯 215 的修复不能代表全部帧。','在合成双唇上固定终点门，另测重获窗切向及跨断带两侧宽度一致性。'],
            ['弱尾认证与材料纹理过冲竞争','三点弯和验证组C的逐帧失败以向右过冲为主，旧命中帧有损失。','在开发/合成数据上对固定候选单独消融强门和渐弱门，记录首次多走的实测列；保留组仅在冻结后评测。'],
            ['倍率与曝光稳定性仍有限','P2 为 9/12，P4_open 仍有 2/12 次假阳性。','增加独立采集倍率和曝光序列，分别检验采样丢失与图像重采样的影响。']]
    sections.append(table(['问题','已有证据','可检验的下一步'],issues))
    (OUT/'REPORT.md').write_text('\n\n'.join(sections)+'\n',encoding='utf-8')
    metadata=dict(run=str(OUT.relative_to(ROOT).as_posix()),primary='v3_1',date='2026-11-19',decision='PRODUCTION_NO_GO',
        scored_visible=54,frames=1633,overall_full=stats,groups=m,real_fpr=None,public_regression_rows=420,synthetic_gap=dict(accepted=30,wrong=8))
    save(OUT/'metrics.json',metadata);save(ROOT/'evidence/latest_metrics.json',metadata)
    pointer=ROOT/'evidence/v3_1';pointer.mkdir(exist_ok=True)
    import re
    prefix='../../'+OUT.relative_to(ROOT).as_posix()+'/'
    linked=re.sub(r'\]\(([^)]+)\)',lambda match:']('+prefix+match[1]+')',(OUT/'REPORT.md').read_text(encoding='utf-8'))
    (pointer/'REPORT.md').write_text(linked,encoding='utf-8')
    doc=ROOT/'docs/OPEN_PROBLEMS.md';text=doc.read_text(encoding='utf-8-sig')
    if '## V3.1 弱裂纹验证' not in text:doc.write_text(text+'\n## V3.1 弱裂纹验证\n\n'+table(['问题','已有证据','可检验的下一步'],issues)+'\n',encoding='utf-8')
    print([(r['group'],r['mode'],r['hit'],r['joint'],r['severe']) for r in m if r['stage']=='v3_1'])
if __name__=='__main__':main()


