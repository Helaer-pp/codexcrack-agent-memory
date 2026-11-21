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

ARCHIVE=ROOT/'evidence/v4_0'
FOCUS={'group_a':[366,398,504],'three_point_bend':[1,144,178,335,407],'group_c':[38,54,69,195,335,347,363,456,510,528]}
STAGE_NAMES=dict(r02='r02',s3t='V3',v3_6='V3.6',track_a='A 灰度',evidence='A + 计算 E_diff',track_b='双轨裁决',v4_0='双轨 + 精修')

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

def collect():
    lock=read(OUT/'freeze.json')
    assert lock['sources']==sources()
    for k,f in [('group_a','group_a.jsonl'),('dev_scores','group_a_scores.csv'),('events','weak_events.csv'),('paired_probes','paired_probes.csv')]:
        assert sha(OUT/f)==lock[k]
    scores={(g,int(r['frame']),r['stage'],r['mode']):r for g in GROUPS for r in read_csv(OUT/(g+'_scores.csv'))}
    metrics=[];records={};timing=[];diagnostics=[]
    for g,n in GROUPS.items():
        for s in ALGS:
            for mode in ('full','raw_only'):
                rr=[r for (gg,i,ss,mm),r in scores.items() if (gg,ss,mm)==(g,s,mode)]
                metrics.append(dict(group=g,stage=s,mode=mode,**aggregate(rr),hit5=sum(r['hit5']=='True' for r in rr),subpixel=sum(bool(r['error_px']) and float(r['error_px'])<1 for r in rr)))
        t=[];previous=[];matched=[]
        for folder in (OUT,BASE):
            seal=read(folder/(g+'_seal.json'))
            assert sha(folder/(g+'.jsonl'))==seal['predictions'] and seal['frames']==n
        with (OUT/(g+'.jsonl')).open() as a,(BASE/(g+'.jsonl')).open() as b:
            for i,(s1,s2) in enumerate(zip_longest(a,b),1):
                cur=json.loads(s1);old=json.loads(s2)
                assert i==cur['frame']==old['frame'] and cur['source_sha']==old['source_sha']
                m=cur['models']['v4_0'];v=old['models']['v3_6']
                assert signature(m['raw_only'])==signature(v['raw_only'])
                t.append(m['seconds']);previous.append(v['seconds'])
                d=m['full']['diagnostics']['dual']
                diagnostics.append(dict(group=g,frame=i,**d))
                if (g,i,'v4_0','full') in scores:
                    for mode in ('full','raw_only'):assert signature(cur['models']['v3_6'][mode])==signature(v[mode])
                    matched.append((cur['models']['v3_6']['seconds'],m['seconds']))
                if (g,i,'v4_0','full') in scores or i in FOCUS[g]:records[g,i]=(m,v)
        assert len(t)==n
        timing.append(dict(group=g,n=n,old_fps=1/np.mean(previous),fps=1/np.mean(t),ms=1000*np.mean(t),old_ms=1000*np.mean(previous),matched_v36_ms=1000*np.mean(matched,axis=0)[0],matched_v40_ms=1000*np.mean(matched,axis=0)[1]))
    for name,rows in [('ablation.csv',metrics),('timing.csv',timing),('tracks.csv',diagnostics)]:write_csv(OUT/name,rows)
    return scores,records,metrics,timing

def failure_report(scores,records):
    entries=[];doc=['# V4.0 失败帧与受损帧专项分析','逐帧对比同图、同标注的冻结 V3.6。受损涵盖尖端误差增加、路径覆盖下降、路径精度下降和有效结果丢失。坐标使用当前原图像素。B 坐标为精修前的增量轨尖端。']
    for g in GROUPS:
        for mode in ('full','raw_only'):
            doc.append('## '+NAMES[g]+' · '+mode);raw_images=[]
            for (gg,i),(pair,prior) in records.items():
                if gg!=g or (g,i,'v4_0',mode) not in scores:continue
                r=scores[g,i,'v4_0',mode];old=scores[g,i,'v3_6',mode]
                if r['state']!='VISIBLE':continue
                losses=[]
                for k,sign,name in [('error_px',1,'尖端误差增加'),('coverage',-1,'人工路径覆盖下降'),('precision',-1,'预测路径精度下降')]:
                    if old[k] and r[k] and sign*(float(r[k])-float(old[k]))>1e-9:losses.append(name)
                if old['error_px'] and not r['error_px']:losses.append('丢失有效尖端')
                if r['joint']=='True' and not losses:continue
                m=pair[mode];d=pair['full']['diagnostics']['dual'];gt=np.array(json.loads(r['gt']));a=d['track_a_tip'];b=d['track_b_tip'] if mode=='full' else None
                photo=f'difference_views/frames/{g}/{i:04d}.jpg' if mode=='full' else f'failure_raw/{g}/{i:04d}.jpg'
                if mode=='raw_only':raw_images.append(i)
                decision=d['decision'] if mode=='full' else 'TRACK_A_ONLY'
                if b is not None:
                    ae=np.linalg.norm(np.subtract(a,gt)) if a is not None else None;be=np.linalg.norm(b-gt)
                    why=f'增量轨通过认证后优先。A 误差 {num(ae)} px，B 精修前误差 {num(be)} px。'
                    if ae is not None and ae<=10<be:why+='本帧裁决舍弃了已命中尖端的 A。'
                    elif be>10:why+='偏差在 B 的路径或终止认证阶段已出现。'
                    if r['hit10']=='True' and r['joint']!='True':why+='尖端达标，沿程覆盖或精度低于 80%。'
                else:
                    why='输出来自原灰度轨。'
                    if mode=='full':why+=f"口门种子 {d['seeds']}，末端候选 {d['certified']}，几何排除 {d['rejections']}，配准 {(d.get('registration') or {}).get('source','无')}。"
                if mode=='full' and b is None:
                    if d['certified'] and d['rejections'].get('CLOSED_RIM',0)==d['certified']:
                        why+='所有通过增量末端认证的候选均被原图闭环检查淘汰，这是本帧 B 无法参与裁决的直接原因；冻结记录未保存被拒候选的端点，无法据此判定其中是否有真裂纹。'
                    elif d['seeds']==0 and i==1:
                        why+='首帧的固定参考与当前原图相同，差分为零，结果只能取决于 A 的裂纹归属。'
                    elif d['seeds'] and not d['certified']:
                        why+='增量口门存在响应，未形成通过 B 末端认证的候选。'
                if mode=='full':
                    ra=scores[g,i,'track_a','full'];rb=scores[g,i,'track_b','full']
                    why+=f" 路径覆盖 A / 双轨 / 精修为 {num(ra['coverage'])} / {num(rb['coverage'])} / {num(r['coverage'])}；三阶段路径精度为 {num(ra['precision'])} / {num(rb['precision'])} / {num(r['precision'])}。原图根点 V3.6 {coord(prior[mode]['root'])}，本次 {coord(m['root'])}。"
                    if b is not None and r['hit10']!='True' and rb['hit10']!='True':
                        why+='±2 px 法向精修无法补回该帧的追踪或纵向终止误差。'
                if r['dx']:why+=f" 相对人工端点，水平方向{'提前' if float(r['dx'])<0 else '向右'} {abs(float(r['dx'])):.2f} px，纵向有符号偏差 {float(r['dy']):+.2f} px。"
                category='联合失败' if r['joint']!='True' else '命中但受损'
                entries.append(dict(group=g,frame=i,mode=mode,category=category,losses='、'.join(losses),gt=r['gt'],old_tip=prior[mode]['tip'],track_a=a,track_b=b,selected=m['tip'],decision=decision,old_error=old['error_px'],error=r['error_px'],coverage=r['coverage'],precision=r['precision'],reason=why,image=photo))
                doc.extend([f'### 第 {i} 帧 · {category}',f"人工 {coord(gt)}，V3.6 {coord(prior[mode]['tip'])}，A {coord(a)}，B {coord(b)}，最终 {coord(m['tip'])}。裁决 `{decision}`。误差 {num(old['error_px'])} → {num(r['error_px'])} px。覆盖 {num(old['coverage'])} → {num(r['coverage'])}，精度 {num(old['precision'])} → {num(r['precision'])}。{'、'.join(losses)}",why+f' [四栏叠图]({photo})'])
            for card,_,row in views.source_frames(g,set(raw_images),'raw_only') if raw_images else ():
                dest=OUT/f"failure_raw/{g}/{row['frame']:04d}.jpg";dest.parent.mkdir(parents=True,exist_ok=True);card.save(dest,quality=94,subsampling=0)
    write_csv(OUT/'failures.csv',entries);pack('FAILURES_AUDIT.md',doc)
    with ZipFile(OUT/'failure_audit.zip','w',ZIP_DEFLATED) as z:
        for f in ['FAILURES_AUDIT.md','failures.csv',*[r['image'] for r in entries]]:z.write(OUT/f,f)
    with ZipFile(OUT/'failure_audit.zip') as z:assert z.testzip() is None
    return entries

def development_report(scores,records,metrics,timing,entries):
    main=[r for r in metrics if r['stage']=='v4_0' and r['mode']=='full']
    base=[r for r in metrics if r['stage']=='v3_6' and r['mode']=='full']
    goal={'group_a':(19,19),'three_point_bend':(12,12),'group_c':(16,15)}
    acceptance={r['group']:r['hit']>=goal[r['group']][0] and r['joint']>=goal[r['group']][1] and r['severe']==0 for r in main}
    counts=lambda rr,k:sum(r[k] for r in rr)
    total=counts(main,'visible')
    md=['# V4.0 裂纹尖端追踪架构解耦与验证报告',
        f"54 张可见标注的 Hit@5 为 {counts(main,'hit5')}/{total}，Hit@10 为 {counts(main,'hit')}/{total}，联合命中 {counts(main,'joint')}/{total}，严重误差 {counts(main,'severe')}。V3.6 对应为 {counts(base,'hit5')}、{counts(base,'hit')}、{counts(base,'joint')}、{counts(base,'severe')}。误差严格小于 1 px 的 V4.0 预测共 {counts(main,'subpixel')} 帧。小数坐标和 Hit@5 均不足以证明亚像素测量精度。",
        '本轮开发只使用开发组A与独立合成图。冻结记录绑定源代码、开发组A结果、开发评分、合成预测和弱带事件。三点弯作冻结阶段对照，验证组C在其后单轮运行。两组均有历史暴露，不能视作从未接触的新材料测试。人工标注仅用于离线对比；排除组X排除。60 张标注中 6 张只有不确定区域，未进入误差分母。三组完整序列均提供结果，其余未标注帧只作定性复查。',
        '[四栏逐帧图册、视频与独立差分](difference_views/index.html) · [失败与受损专项](FAILURES_AUDIT.md) · [冻结记录](freeze.json) · [完整双轨裁决与配准日志](tracks.csv)',
        '## 数据组验收',table(['组','Hit@10 / 目标','Joint / 目标','Severe','中位 px','命中与严重误差门'],[(NAMES[r['group']],f"{r['hit']} / {goal[r['group']][0]}",f"{r['joint']} / {goal[r['group']][1]}",r['severe'],num(r['median']),'通过' if acceptance[r['group']] else '未通过') for r in main]),
        '## 从 V3.6 到 V4.0',
        'V3.6 以原灰度候选为主，在追踪期间补种、豁免遮挡和延伸，再按参考形状、静态竞争和末端回溯修正输出。V4.0 保留纯灰度 A、切向 DP、拓扑检测、几何映射与配准原语。完整模式中，A 与 B 独立追踪；V3.5/V3.6 的混合候选排名、静态分支淘汰、末端划痕回剪及尖端外推均退出增量轨。软件仍包含继承的灰度规则和多个认证阈值。',
        '参考图先映射到当前帧坐标，细配准优先，纹理不足依次使用可用的缺口/双材料区粗配准或轮廓保底。对参考减当前提取窄带双侧暗谷、法向双极响应及方向相容的参考暗谷抑制。B 在这张图内独立扫描、追踪、认证，最后检查原图根连通和闭环。通过的 B 优先，否则使用 A。精修在静态风险较低的单峰原灰度响应上做法向抛物线插值。',
        '展示的第四栏为有符号原灰度差分，全部采用 ±32 灰度级，红为当前变暗、蓝为当前变亮。算法另外使用过滤后的 E_diff。参考对应位置按本帧登记的变换反投影，近似配准会在图中注明。',
        '### 增量实现规模',
    ]
    def complexity(files):
        lines=branches=0
        for f in files:
            src=f.read_text(encoding='utf-8-sig');lines+=sum(bool(x.strip()) and not x.strip().startswith('#') for x in src.splitlines())
            branches+=sum(isinstance(n,(ast.If,ast.IfExp,ast.For,ast.While,ast.comprehension)) for n in ast.walk(ast.parse(src)))
        return len(files),lines,branches
    research_root=ROOT/'research'
    files=lambda v,n:[research_root/('notch_identity_'+v)/(s+'.py') for s in n.split()]
    stages=[('V3.6 版本专有',files('v36','terminal competition reference horizontal')),('V4.0 版本专有',files('v40','terminal evidence tracking'))]
    md.extend([table(['统计范围','模块','有效行','条件/循环节点'],[(n,*complexity(fs)) for n,fs in stages]),'按本版本专有推理模块的非空非注释行和 AST 节点计数。共享 V3.1–V3.5 代码、测试、报告和渲染未计入，本表不能代表运行时间。',
        '### 参数与物理量','s 为锚距，span 为灰度曝光分位跨度。长度由 s 换算并取整，噪声以灰度估计。下表给出机制与主参数。逐行参数及继承配准、原灰度与 DP 公式见[参数索引](parameters.md)。',
        table(['环节','参数与作用'],[
            ['配准','缺口或双材料区粗搜索 ±0.04s；缺口轮廓 ±0.025s；前向 0.24s 处细窗搜索 ±0.015s，纹理相关阈 0.75，峰差 0.012。'],
            ['E_diff','中心 ±0.28s 处理带，双侧半径 0.007/0.014/0.024s，方向 −0.52/0/+0.52 弧度。切向 0.009s；法向 ±0.014s 抑制双极。'],
            ['静态相容','半径 0.025s，参考方向响应至少为最强方向的 0.90，参考深度超过 3 倍噪声与 0.028 span，按相对深度软衰减，最高衰减 96%。'],
            ['归一化','取 0.012 span、2.8 倍差分高频 MAD、1.5 倍图像噪声三者最大值。'],
            ['起点与追踪','全口门纵向 ±0.16s，前后 −0.14s 至 +0.10s，累积窗 0.026s，最多 10 种子。DP 参数及断带外推约束见索引。'],
            ['末端认证','侧方 0.035–0.10s 的背景 97 分位估计杂波，0.033s 窗中检查强列占比及均强；依据差分梯度的切向方向性及末段相对减弱，检查延续的散斑。'],
            ['法向精修','最大半径 min(2 px, max(0.75 px, 0.007s))，9 点取样，只在单峰突出超过噪声且静态风险低时接受。']]),
        '## 分阶段消融','A + 计算 E_diff 阶段只生成证据，公开输出仍来自 A。双轨阶段首次允许 B 发布结果，最终阶段再启用精修。Joint 同时要求误差 ≤10 px、人工路径覆盖和预测路径精度均 ≥80%（路径容差 10 px）。Severe 表示有效预测误差 >100 px；无有效结果计入命中分母。中位值和最大值只统计有坐标的帧。'])
    for g in GROUPS:
        md.extend(['### '+NAMES[g],table(['阶段','有效 / 可见','Hit@5','Hit@10','Joint','Severe','中位 px','最大 px'],[(STAGE_NAMES[r['stage']],f"{r['valid']}/{r['visible']}",r['hit5'],r['hit'],r['joint'],r['severe'],num(r['median']),num(r['max'])) for r in metrics if r['group']==g and r['mode']=='full'])])
    md.extend(['逐帧比对全部 1,633 帧的纯灰度状态、根点、路径点和尖端，与冻结 V3.6 完全一致。全体 60 张有标注帧的 V3.6 重放，在完整及纯灰度模式也均一致。[全部消融及纯灰度指标](ablation.csv)','## 指定疑难帧'])
    for g,ids in FOCUS.items():
        focus=[]
        for i in ids:
            pair,prior=records[g,i];m=pair['full'];old=prior['full'];d=m['diagnostics']['dual']
            r=scores.get((g,i,'v4_0','full'),{});v=scores.get((g,i,'v3_6','full'),{})
            url=f'difference_views/frames/{g}/{i:04d}.jpg'
            old_url='../'+BASE.name+'/'+url
            focus.append([f"{i} [旧]({old_url}) [新]({url})",coord(old['tip']),coord(d['track_a_tip']),coord(d['track_b_tip']),coord(m['tip']),num(v.get('error_px'))+' → '+num(r.get('error_px')),num(v.get('coverage'))+' → '+num(r.get('coverage')),d['decision']])
        md.extend(['### '+NAMES[g],table(['帧与四栏图','V3.6','A','B','精修后/回退','误差 px','覆盖','裁决'],focus)])
    pair,prior=records['group_c',347]
    old=prior['full'];new=pair['full']
    md.append(f"验证组C 347 无人工尖端，表内误差和覆盖留空。V3.6 根点 {coord(old['root'])}、路径 {len(old['points'])} 个观测点；V4.0 根点 {coord(new['root'])}、路径 {len(new['points'])} 个观测点。图像可以检查参考原图中相同位置的纹理，无法由此给出真值误差。")
    md.append('三点弯 144 的细配准通过；B 提出的 4 个种子中有 2 条路径通过增量末端认证，但均被闭环检查淘汰。回退的 A 沿人工端点右侧的浅灰纹理继续前进，过冲约 59 px。三点弯 407 的 6 条末端候选也全部被闭环检查淘汰，回退 A 提前约 19 px。两个例子表明同一个裁决门可令输出朝不同方向偏移。')
    md.append('验证组C 363 从 13.03 px 改善到 0.84 px；335 仍命中但由 2.18 px 增至 7.84 px。验证组C 54 的两个增量末端候选均未通过根连通检查；69 的 B 已通过裁决，仍向右过冲 23.39 px。121 与 469 的完整模式分别退化到 51.41 和 54.72 px，均在增量轨主选后出现。第 469 帧四栏图上，人工端点附近的连续红色差分带明显减弱，预测绿线仍沿点状响应向右延伸；该帧细配准标记为 AMBIGUOUS，显示使用缺口粗定位。后两帧说明即便狭窄差分路径可以连通，末端认证也可能将背景延伸一并纳入。')
    probes=read_csv(OUT/'paired_probes.csv');events=read_csv(OUT/'weak_events.csv')
    matrix=[];cases=list(dict.fromkeys(r['case'] for r in probes))
    for case in cases:
        line=[case]
        for z in ('.5','1','2'):
            for ph in ('nominal','dim','bright'):
                rr=[r for r in probes if r['case']==case and float(r['zoom'])==float(z) and r['photo']==ph]
                fp=sum(r['valid']=='True' and r['negative']=='True' for r in rr)
                line.append(f"{sum(r['passed']=='True' for r in rr)}/{len(rr)}"+(f' FP {fp}' if rr[0]['negative']=='True' else ''))
        matrix.append(line)
    md.extend(['## 独立合成压力矩阵','每格为通过数/样本数；阴性另列误报数。每种缩放均依次显示标准、暗、亮三档。正例误差按原始尺度 ≤10 px；P1 还要求人工路径全覆盖（2.5 px 容差），P6 还要求路径精度 ≥95%。每格含两档噪声和两组随机种子，弱带格另交叉三种断带宽度及两种残余对比。',table(['探针']+[f'{z}× {ph}' for z in (.5,1,2) for ph in ('标准','暗','亮')],matrix)])
    for ph in ('nominal','dim','bright'):
        rs=[r for r in events if r['photo']==ph];neg=[r for r in probes if r['photo']==ph and r['negative']=='True']
        md.append(f"{ph} 曝光：阴性误报 {sum(r['valid']=='True' for r in neg)}/{len(neg)}；弱带接受重连 {sum(int(r['accepted']) for r in rs)} 次，其中错接 {sum(int(r['wrong']) for r in rs)} 次。")
    md.append('开发组依次检验了侧方背景噪声底、纵向持续性、闭环检查、根部前缀恢复和断带两侧方向一致性。初版开发组A联合 11/19；引入侧方背景后 16/19；过强的纵向连续性约束一度退至 11/19。冻结版保留两侧支持及低方向性散点的末端检查。半倍尺度下新增窄谷可接近或小于一个采样像素，渐隐与离散点串难以区分。P5、P6 阳性还继承了 P2 的渐隐尾段与散点，阳性失败不能单独归因于塑性区或形变。')
    for case in ('P2_fade','P5_plastic_zone','P6_deformed_scratch'):
        rs=[r for r in probes if r['case']==case];dx=[json.loads(r['tip'])[0]/float(r['zoom'])-199 for r in rs if r['valid']=='True']
        md.append(f"{case}：{len(dx)}/{len(rs)} 个有效输出。按原始像素折算，超出真实端点右侧 10 px 有 {sum(x>10 for x in dx)} 个，提前超过 10 px 有 {sum(x< -10 for x in dx)} 个。")
    md.extend(['[全部 612 个探针](paired_probes.csv) · [弱带逐例事件](weak_events.csv)','## 单帧耗时与吞吐','全序列按各自运行时记录的 prepare + full 耗时取算术平均再换算 FPS，排除读图、评分、视频和纯灰度复算。六进程并行时单帧耗时受竞争影响。末两列是本次同一批 20 张标注图上的同进程配对均值。',table(['组','全序列帧','V3.6 ms / FPS','V4.0 ms / FPS','配对 V3.6 ms','配对 V4.0 ms'],[(NAMES[t['group']],t['n'],num(t['old_ms'])+' / '+num(t['old_fps']),num(t['ms'])+' / '+num(t['fps']),num(t['matched_v36_ms']),num(t['matched_v40_ms'])) for t in timing]),'## 使用结论',
        '暂不替换项目基线。优先从独立合成样例核对短断带、连续渐隐末端与离散点列的区分，并记录口门种子到人工端点的可达性。验证组的具体帧仅用于解释本次冻结结果。'])
    md.append('推理入口为 research/notch_identity_v40/terminal.py 的 prepare 和 predict。运行器 batch.py 提取当前图、参考图和口门几何，score.py 在预测封存后关联标注，difference_views.py 由封存记录渲染，delivery_check.py 校验交付文件，report.py 生成报告。')
    parameters=['# V4.0 参数索引','以下按实现函数列出实参、窗宽、能量阈值、像素下限和归一化常数。继承项中也包括底层数值保护。']
    for f in stages[1][1]+files('v33','reference')+files('v35','reference')+files('v34','terminal')+files('v32','terminal guards')+files('v31','terminal topology'):
        src=f.read_text(encoding='utf-8-sig').splitlines();parameters.append('## '+str(f.relative_to(ROOT)))
        for fn in ast.walk(ast.parse('\n'.join(src))):
            if not isinstance(fn,ast.FunctionDef):continue
            if f.parent.name=='notch_identity_v35' and fn.name!='contour':continue
            rows=[f'{j+1:4d} {src[j].strip()}' for j in range(fn.lineno-1,fn.end_lineno) if re.search(r'\d',src[j]) and not src[j].strip().startswith('#')]
            if rows:parameters.extend([fn.name,'```python\n'+'\n'.join(rows)+'\n```'])
    (OUT/'parameters.md').write_text('\n\n'.join(parameters),encoding='utf8')
    pack('REPORT.md',md)
    data=dict(version='V4.0',run=OUT.name,decision='PRODUCTION_NO_GO',groups=main,baseline=base,acceptance=acceptance,timing=timing,raw_only_parity=sum(GROUPS.values()),stress_cases=len(probes),negative_fp=sum(r['valid']=='True' and r['negative']=='True' for r in probes),wrong_reconnections=sum(int(r['wrong']) for r in events),archive_entries=len(entries))
    full_scores=[r for (_,_,s,m),r in scores.items() if s=='v4_0' and m=='full']
    overall=aggregate(full_scores)
    overall['hit5']=counts(main,'hit5')
    pointer=dict(data,run=OUT.relative_to(ROOT).as_posix(),primary='v4_0',date='2026-11-19',report='evidence/v4_0/REPORT.md',failures='evidence/v4_0/FAILURES_AUDIT.md',frames=sum(GROUPS.values()),scored_visible=total,uncertain=len(full_scores)-total,overall_full=overall)
    save(OUT/'latest_metrics.json',pointer);save(ARCHIVE/'latest_metrics.json',pointer);save(ROOT/'evidence/latest_metrics.json',pointer)
    return data

if __name__=='__main__':
    scores,records,metrics,timing=collect()
    entries=failure_report(scores,records)
    print(json.dumps(development_report(scores,records,metrics,timing,entries),ensure_ascii=False,indent=1))
