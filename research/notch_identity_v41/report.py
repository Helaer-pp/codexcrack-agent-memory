"""Compile the frozen evaluation and check delivered links and parity."""
import ast
import json
import os
import re
from collections import Counter
from itertools import zip_longest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np
from .batch import ROOT, OUT, BASE, GROUPS, ALGS, sources, sha, read, save
from . import difference_views as views
from research.notch_identity_v31.report import aggregate, NAMES, num
from research.notch_identity_v32.audit import signature
from research.v3_labelme_comparison.infer import read_csv
from research.v3_labelme_comparison.compare import table, write_csv

ARCHIVE=ROOT/'evidence/v4_1'
FOCUS={'group_a':[67,366,398,504],'three_point_bend':[1,144,178,335,407],'group_c':[38,54,69,195,335,347,363,456,469,510,528]}
STAGE_NAMES=dict(r02='r02',s3t='V3',v3_6='V3.6',v4_0='V4.0',front='① 前缘 + 窄带',floor='② 加原图底线',v4_1='③ 加增量根与闭环判据')

def pack(name,parts):
    body='\n\n'.join(parts)+'\n'
    ARCHIVE.mkdir(exist_ok=True)
    for folder in (OUT,ARCHIVE):
        def rewrite(m):
            target=OUT/m[1]
            assert target.is_file(),target
            return ']('+Path(os.path.relpath(target,folder)).as_posix()+')'
        (folder/name).write_text(re.sub(r'\]\(([^)]+)\)',rewrite,body),encoding='utf8')

def coord(x):
    return '—' if x is None else '('+', '.join(f'{v:.2f}' for v in x)+')'


def decode(path):
    with path.open(encoding='utf8') as f:yield from map(json.loads,f)

def summarize():
    from research.notch_identity_v36.batch import OUT as v36
    from .probes import synthetic_gate
    groups=[g for g in GROUPS if (OUT/(g+'_scores.csv')).is_file()]
    assert synthetic_gate(OUT)
    metrics=[];times=[];tracks=[];scored={};models={};prefix_checks=[]
    for g in groups:
        n=GROUPS[g]
        paths=[folder/(g+'.jsonl') for folder in (OUT,BASE,v36)]
        for path in paths:assert sha(path)==read(path.parent/(g+'_seal.json'))['predictions']
        if g!='group_a':assert read(OUT/'freeze.json')['sources']==sources()
        for r in read_csv(OUT/(g+'_scores.csv')):scored[g,int(r['frame']),r['stage'],r['mode']]=r
        t=[]
        for i,rec in enumerate(zip_longest(*(decode(path) for path in paths)),1):
            assert all(a['frame']==i and a['source_sha']==rec[0]['source_sha'] for a in rec)
            model,old4,old3=[a['models'][v] for a,v in zip(rec,('v4_1','v4_0','v3_6'))]
            assert signature(model['raw_only'])==signature(old3['raw_only'])
            m=model['full'];d=m['diagnostics']['dual']
            if 'front' in d and m['tip']:
                assert m['root'][0]>=d['front'],(g,i,m['root'],d)
            tracks.append(dict(group=g,frame=i,status=m['status'],tip=m['tip'],root=m['root'],decision=d['decision'],stop=d.get('stop'),base_tip=d.get('base_tip'),front=d.get('front'),trials=d.get('trials',[]),rejections=d.get('rejections',{})))
            t.append([q['seconds'] for q in (old3,old4,model)])
            if (g,i,'v4_1','full') in scored:
                # Diagnose the first gap in a sealed public stage-1 path when the
                # same anchored base endpoint was retained before terminal processing.
                from .batch import OLD
                from research.notch_identity_v31.detector import px
                p0=rec[0]['models']['front']['full']
                if p0['tip'] and p0['tip']==d.get('base_tip') and p0['diagnostics']['dual']['decision']=='ANCHORED_V36' and d['decision']=='ANCHORED_V36':
                    scale=read(OLD/'evidence'/g/str(i)/'metadata.json')['evidence']['scene']['scale']
                    x,y=np.array(p0['points']).T
                    for j in np.flatnonzero((np.diff(x)>=px(scale,.012))&(x[:-1]<=d['front']+px(scale,.32))):
                        l=np.searchsorted(x,x[j]-px(scale,.035))
                        expected=y[j]+np.clip((y[j]-y[l])/max(1,x[j]-x[l]),-.65,.65)*(x[j+1]-x[j])
                        residual=abs(y[j+1]-expected)
                        if residual>max(2,.016*scale):
                            prefix_checks.append(dict(group=g,frame=i,left=int(x[j]),right=int(x[j+1]),dy=int(y[j+1]-y[j]),residual=float(residual),limit=max(2,.016*scale),base_x=p0['tip'][0],final_x=m['tip'][0] if m['tip'] else None))
                            break
                for stage,old in [('v4_0',old4),('v3_6',old3)]:
                    for mode in ('full','raw_only'):assert signature(rec[0]['models'][stage][mode])==signature(old[mode])
            if (g,i,'v4_1','full') in scored or i in FOCUS[g]:models[g,i]=[q['full'] for q in (old3,old4,model)]
        assert len(t)==n
        for s in ALGS:
            for mode in ('full','raw_only'):
                rr=[r for (gg,i,ss,mm),r in scored.items() if (gg,ss,mm)==(g,s,mode)]
                metrics.append(dict(group=g,stage=s,mode=mode,**aggregate(rr),hit5=sum(r['hit5']=='True' for r in rr)))
        for stage,ms in zip(('v3_6','v4_0','v4_1'),np.mean(t,axis=0)):
            times.append(dict(group=g,stage=stage,frames=n,ms=float(ms*1000),fps=float(1/ms)))
    for f,rr in [('ablation.csv',metrics),('timing.csv',times),('tracks.csv',tracks),('near_mouth_gaps.csv',prefix_checks)]:
        if rr:write_csv(OUT/f,rr)
    return groups,scored,models,metrics,times

def local_profiles(group,frame,gt,tip,shift):
    from .batch import OLD
    from research.notch_identity_v31.detector import px
    cache=OLD/'evidence'/group/str(frame);meta=read(cache/'metadata.json')
    scene=meta['evidence']['scene'];origin=np.array(scene['bounds'][:2])
    with np.load(cache/'arrays.npz') as z:
        gray=z['raw'].astype(float);fixed=z['fixed__aligned']
    dx,dy=shift;radius=px(scene['scale'],.014)
    def at(point):
        if point is None:return None
        x,y=np.rint(np.asarray(point)-origin).astype(int)
        ys=np.array([y-radius,y,y+radius])
        if not (0<=x<gray.shape[1] and 0<=x+dx<fixed.shape[1] and ys.min()>=0 and ys.max()<len(gray) and ys.min()+dy>=0 and ys.max()+dy<len(fixed)):return None
        cur=gray[ys,x];ref=fixed[ys+dy,x+dx];delta=ref-cur
        if not np.isfinite(delta).all():return None
        return (min(cur[0],cur[2])-cur[1],delta[1]-max(delta[0],delta[2]))
    return at(gt),at(tip)

def failures(groups,scores,models):
    notes=['# V4.1 失败帧与受损帧专项分析','仅纳入可见标注。相对任一对照版误差增加、路径覆盖或精度下降、丢失有效尖端，均列为受损；同一帧只列一次。表内坐标为当前原图像素。']
    entries=[]
    near_file=OUT/'near_mouth_gaps.csv'
    gaps={(r['group'],int(r['frame'])):r for r in read_csv(near_file)} if near_file.is_file() else {}
    shifts={(r['group'],int(r['frame'])):json.loads(r['shift']) for r in read_csv(OUT/'difference_views/coordinates.csv')}
    notes.append('局部复核在当前原图两个法向采样点（竖直方向 ±0.014s）和中心计算。第一项为中心相对两侧的原图凹陷深度，第二项为参考减当前的中心增量相对两侧的突出量，单位均为灰度级。该三点剖面用于人工复查，倾斜暗线和配准偏差会影响数值。')
    for g in groups:
        notes.append('## '+NAMES[g]);count=0
        for (gg,i),(old3,old4,m) in models.items():
            if gg!=g or (g,i,'v4_1','full') not in scores:continue
            rr=[scores[g,i,v,'full'] for v in ('v3_6','v4_0','v4_1')];r=rr[-1]
            if r['state']!='VISIBLE':continue
            losses=[]
            for prev,name in zip(rr[:2],('V3.6','V4.0')):
                for k,sign,label in [('error_px',1,'尖端误差增加'),('coverage',-1,'覆盖下降'),('precision',-1,'路径精度下降')]:
                    if r[k] and prev[k] and (float(r[k])-float(prev[k]))*sign>1e-9:losses.append(name+' '+label)
                if prev['error_px'] and not r['error_px']:losses.append(name+' 有效尖端丢失')
            if not losses and r['joint']=='True':continue
            count+=1;d=m['diagnostics']['dual'];st=d.get('stop')
            image=f'difference_views/frames/{g}/{i:04d}.jpg'
            category='联合失败' if r['joint']!='True' else '命中但相对对照退化'
            reasons=[f"主选 {d['decision']}，终止 {st}，增量尝试 {len(d.get('trials',[]))} 条，拒绝计数 {d.get('rejections',{})}。"]
            if m['tip'] and r['dx']:
                if abs(float(r['dy']))>abs(float(r['dx'])):reasons.append('纵向误差占主导，需复查前缘分支归属。')
                elif float(r['dx'])>10:reasons.append('末端位于人工端点右侧，需复核延伸区是否仍有连续原图凹陷及相同参考纹理。')
                elif float(r['dx'])< -10:reasons.append('末端提前，需核对最后保留列后的弱暗谷、参考掩膜和认证噪声底。')
                if r['hit10']=='True' and r['joint']!='True':reasons.append('端点在容差内，路径覆盖或预测精度未达 80%。')
            gap=gaps.get((g,i))
            if gap:
                reasons.append(f" 对封存的①阶段公开路径复核，近口相邻观测列从 x={gap['left']} 跳到 {gap['right']}，纵向跳变 {gap['dy']} px；恢复点距外推中心 {float(gap['residual']):.1f} px，超过 {float(gap['limit']):.1f} px 跨唇门。原基座尖端 x={gap['base_x']}，最终 x={gap['final_x']}。日志的终止字段只保留最后一次修改，可能覆盖首次截断。")
            gt_profile,pred_profile=local_profiles(g,i,json.loads(r['gt']),m['tip'],shifts[g,i])
            def fmt(v):return '无有效对应' if v is None else f'{v[0]:.1f} / {v[1]:.1f}'
            reasons.append(f' 人工端点的原图凹陷 / 窄带增量为 {fmt(gt_profile)}，预测端点为 {fmt(pred_profile)}。')
            if pred_profile and r['dx'] and float(r['dx'])>10 and pred_profile[1]<=0:
                reasons.append('预测点在该截面无正的净增量突出，需沿末段区分残余背景线与裂纹。')
            notes.extend([f'### {i} · {category}',f"人工 {r['gt']}。V3.6、V4.0、V4.1 依次为 {coord(old3['tip'])}、{coord(old4['tip'])}、{coord(m['tip'])}，误差依次为 "+' / '.join(num(s['error_px']) for s in rr)+' px。覆盖依次为 '+' / '.join(num(s['coverage']) for s in rr)+'，精度为 '+' / '.join(num(s['precision']) for s in rr)+'。',''.join(reasons)+' '.join(losses)+f'。[四栏图]({image})'])
            entries.append(dict(group=g,frame=i,category=category,losses=losses,gt=r['gt'],tip=m['tip'],error=r['error_px'],decision=d['decision'],stop=st,rejections=d.get('rejections'),image=image))
        if not count:notes.append('本组无失败或受损帧。')
    if entries:write_csv(OUT/'failures.csv',entries)
    pack('FAILURES_AUDIT.md',notes)
    with ZipFile(OUT/'failure_audit.zip','w',ZIP_DEFLATED) as z:
        z.write(OUT/'FAILURES_AUDIT.md','FAILURES_AUDIT.md')
        for r in entries:z.write(OUT/r['image'],r['image'])
    return entries

def report():
    groups,scores,models,metrics,times=summarize();entries=failures(groups,scores,models)
    rows=read_csv(OUT/'paired_probes.csv');prior=read_csv(BASE/'paired_probes.csv')
    final=[r for r in metrics if r['stage']=='v4_1' and r['mode']=='full']
    main=['# V4.1 裂纹尖端追踪提纯融合验证报告',
          '以 V3.6 灰度主干、近缺口重连与参考复核为基座。将完整模式的种子限制到物理前缘起向右 0.10s 以内，再用 V4.0 窄带有符号增量及 ±0.025s 参考预抑制判别候选。纯灰度模式保留独立基线行为。',
          '人工标注仅用于结果对比，排除组X已排除。先运行合成探针，然后运行开发组A。两验证组历史上均已暴露。P5/P6 保留旧版复合探针，同时增加等长、恒定深度、无末端散点的裂纹对照，分别单独施加宽域变暗和错位静态划痕。',
          '## 实现和数据流','① 限制起点与补种范围。② 增量轨需同时有当前图凹陷，渐隐末端用局部衰减和实际观测列认证；检查参考图相容偏移的连续暗谷以制止划痕延伸。③ 强增量根可用直至嘴沿的单极连续暗化代替原图连通；闭环仅由增量掩膜中的封闭区域判定。弱证据保留原灰度主干。阶段表逐项累加。']
    main.append('渐隐拟合仅用于分辨率下的细暗线。有可分辨宽度的主干沿用 V3.6 的几何端点，只在局部增量衰减至侧方背景噪声时，回到最后连续观测窗的中心。颈部拒绝跨唇跳变。重复灰度候选和相同路径的参考回剪评审按帧缓存。')
    if len(groups)==3:
        main[1:1]=['**冻结版未通过验收。** 开发组A、三点弯、验证组C联合命中分别为 19/19、1/15、8/20，共 28/54。V3.6 为 42/54，V4.0 为 37/54。三点弯出现 11 帧尖端误差超过 100 px，继续使用原有基线。']
    for name in ('terminal.py','evidence.py','backbone.py'):
        src=(Path(__file__).parent/name).read_text(encoding='utf-8-sig')
        main.append(f"{name} 共 {sum(bool(l.strip()) and not l.strip().startswith('#') for l in src.splitlines())} 行非空、非纯注释代码。共用 V3.6 原语、评测与渲染未计入。")
    main+=['## 合成压力矩阵','各格为 V4.0 → V4.1 通过数/分母。顺序为三档缩放，每档内标准、暗、亮。独立扰动控制在 V4.0 没有同场记录。阳性按原始尺度尖端误差 ≤10 px，P1 还要求路径全覆盖，P6 还要求路径精度 ≥95%。']
    matrix=[]
    for case in dict.fromkeys(r['case'] for r in rows):
        out=[case]
        for z in (.5,1.,2.):
            for ph in ('nominal','dim','bright'):
                def cell(src):
                    q=[r for r in src if (r['case'],float(r['zoom']),r['photo'])==(case,z,ph)]
                    return f"{sum(r['passed']=='True' for r in q)}/{len(q)}" if q else '—'
                out.append(cell(prior)+' → '+cell(rows))
        matrix.append(out)
    main.append(table(['探针']+[f'{z}× {ph}' for z in (.5,1,2) for ph in ('标准','暗','亮')],matrix))
    for ph in ('nominal','dim','bright'):
        q=[r for r in rows if r['photo']==ph];neg=[r for r in q if r['negative']=='True']
        main.append(f"{ph} 阴性误报 {sum(r['valid']=='True' for r in neg)}/{len(neg)}；已发布弱带重连 {sum(int(r['accepted']) for r in q)} 次，错接 {sum(int(r['wrong']) for r in q)} 次。")
    for case in ('P2_fade','P5_plastic_zone','P6_deformed_scratch'):
        counts=[]
        for src in (prior,rows):
            rr=[r for r in src if r['case']==case]
            dx=[json.loads(r['tip'])[0]/float(r['zoom'])-199 for r in rr if r['tip'] and r['valid']=='True']
            counts.append(f"{sum(x< -10 for x in dx)} 提前、{sum(x>10 for x in dx)} 过冲、{len(rr)-len(dx)} 无预测")
        main.append(case+' 按原始尺度统计水平偏差超过 10 px 的正例。V4.0 → V4.1 为 '+' → '.join(counts)+'。')
    main.append('每档曝光的 72 个阴性样例含独立纹理、闭环、开口边缘及仅有塑性暗化或形变划痕的背景。事件统计审查发布路径中的实际缺列及获准重连，邻近重复事件合并；与 V4.0 的内部事件口径有所不同。低采样弱裂纹的局部原图暗谷可能只有单像素，因此半倍尺度的失败仍需单列。')
    main+=['[逐例合成结果](paired_probes.csv) · [弱带事件](weak_events.csv)','## 实测消融','Joint 要求尖端 ≤10 px 且 10 px 容差内的路径覆盖和精度均 ≥80%。Severe 为误差 >100 px。无预测计入命中分母，误差分布仅包含有效坐标。']
    for g in groups:
        main += ['### '+NAMES[g],table(['阶段','有效 / 可见','Hit@5','Hit@10','Joint','Severe','中位 px','最大 px'],[(STAGE_NAMES[r['stage']],f"{r['valid']}/{r['visible']}",r['hit5'],r['hit'],r['joint'],r['severe'],num(r['median']),num(r['max'])) for r in metrics if r['group']==g and r['mode']=='full'])]
    main+=['## 指定帧对照','三列坐标与误差均按 V3.6、V4.0、V4.1 排列。验证组C 347 无标注，仅供定性检查。']
    for g in groups:
        lines=[]
        for i in FOCUS[g]:
            ms=models[g,i];err=[scores.get((g,i,v,'full'),{}).get('error_px') for v in ('v3_6','v4_0','v4_1')]
            root=ms[-1]['diagnostics']['dual']
            from research.notch_identity_v36.batch import OUT as v36_folder
            picture=f'difference_views/frames/{g}/{i:04d}.jpg'
            links=f"{i} [3.6](../{v36_folder.name}/{picture}) [4.0](../{BASE.name}/{picture}) [4.1]({picture})"
            lines.append([links,*[coord(m['tip']) for m in ms],' / '.join(num(x) for x in err),root['decision'],root.get('stop')])
        main+=['### '+NAMES[g],table(['帧','V3.6','V4.0','V4.1','误差 px','路径来源','末端判定'],lines)]
    if 'three_point_bend' in groups:
        main+=['## 冻结失效的定位','三点弯①阶段仍有 10/15 联合命中，②阶段降至 1/15，③没有恢复。13 张有可比封存基座路径的可见标注帧触发近口跨唇判据。第 503 帧基座走到 x=1795，跨唇检查在 x=1516 首次截断，后续末端认证留下 x=1502，最终误差 285.10 px。重复截在同一处，说明这段带缺列的弯曲路径被当成了跨唇重连。记录中的最后停止原因不足以解释首次损失。[近口截断逐帧数据](near_mouth_gaps.csv)']
    if 'group_c' in groups:
        main.append('验证组C 469 恢复到 9.71 px，335 为 2.18 px；363 未保住 V4.0 的 0.84 px，最终为 13.03 px。54 和 69 均有 3 个候选未通过颈部连续性检查、1 个未形成足够长的增量，新的原图门豁免没有得到可发布候选。69 的基座结果在前缘阶段已偏至 42.29 px。')
    main.append('下一轮可在独立合成图中并列生成“弯曲但同唇、观测缺列”和“平行两唇之间的真实跳接”。记录断前、断后切向以及参考图对应纹理，先验证能否区分这两个情形，再决定是否对已由灰度主干验证的路径执行截断。')
    main+=['## 效率与验收','各版本冻结全序列单帧推理算术均值，排除读图、标注评分和渲染；不同运行时 CPU 并发与系统负载会影响对比。视频播放帧率与推理速度独立。',table(['组','版本','帧','毫秒/帧','FPS'],[(NAMES[t['group']],t['stage'],t['frames'],num(t['ms']),num(t['fps'])) for t in times])]
    goals={'group_a':(19,19),'three_point_bend':(12,12),'group_c':(15,14)}
    passed={r['group']:r['hit']>=goals[r['group']][0] and r['joint']>=goals[r['group']][1] and r['severe']==0 and (r['group']!='group_a' or r['median']<3) for r in final}
    for g,ok in passed.items():main.append(NAMES[g]+'的尖端与路径验收'+('通过。' if ok else '未通过。'))
    for g in groups:
        rr=[r for r in metrics if r['group']==g and r['mode']=='full']
        by={r['stage']:r for r in rr}
        main.append(f"{NAMES[g]} 联合命中 V3.6、V4.0、V4.1 依次为 {by['v3_6']['joint']}、{by['v4_0']['joint']}、{by['v4_1']['joint']}。")
    audit=read(OUT/'delivery_check.json').get('front_band',{})
    if audit:
        main.append(f"复核全部已保存的主选根、候选起点和增量种子，共 {sum(g['checks'] for g in audit.values())} 个坐标记录，越出前缘带 {sum(len(g['outside']) for g in audit.values())} 个。相同坐标在不同记录中可能重复。")
    main.append('同源核验逐帧检查了纯灰度状态、根点、尖端和路径；标注帧的两个冻结版本均与历史推理结果一致。真实序列只有人工可见标注帧可计算尖端误差。')
    main+=['[逐帧图册与视频](difference_views/index.html) · [失败与退化帧](FAILURES_AUDIT.md) · [逐帧裁决](tracks.csv)']

    results=[r for (g,i,s,m),r in scores.items() if s=='v4_1' and m=='full']
    data=dict(primary='v4_1',run=OUT.relative_to(ROOT).as_posix(),report='evidence/v4_1/REPORT.md',failures='evidence/v4_1/FAILURES_AUDIT.md',groups=final,overall_full=aggregate(results),hit5=sum(r['hit5']=='True' for r in results),accuracy_gate=passed,timing=times,frames=sum(GROUPS[g] for g in groups),synthetic= len(rows),archive_entries=len(entries))
    all_speeds=all(next(t['fps'] for t in times if t['group']==g and t['stage']=='v4_1')>=next(t['fps'] for t in times if t['group']==g and t['stage']=='v3_6') for g in groups)
    main.append('三个组的全序列速度均达到 V3.6。' if all_speeds and len(groups)==3 else '本轮未在全部三个组取得达到 V3.6 的全序列速度。')
    main.append('P1 弱带的错接和覆盖是两项独立指标；回退或截断也会使错接数下降。应同时检查矩阵中的覆盖验收通过率。')
    pack('REPORT.md',main)
    data['throughput_gate']=all_speeds
    data['decision']='RESEARCH_GATES_PASSED' if len(groups)==3 and all(passed.values()) and all_speeds else 'PRODUCTION_NO_GO'
    save(OUT/'latest_metrics.json',data);save(ARCHIVE/'latest_metrics.json',data);save(ROOT/'evidence/latest_metrics.json',data)
    print(data)

if __name__=='__main__':report()
