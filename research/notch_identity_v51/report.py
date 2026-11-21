"""Assemble post-freeze comparisons, primary/control audits and handoff metrics."""
from collections import Counter
import json
from . import batch as b
from .curves import generate
from .difference_views import source_frames
from research.notch_identity_v42.reporting import collect,pack,metric_tables,focus_tables,probe_tables,failure_list,read_csv,table,NAMES,num,aggregate

FORMULA = """令 s 为锚距、L 为曝光跨度、σ 为局部噪声、R 为沿用的多尺度双侧暗谷响应。原图基线 B=max(2.25σ+0.007L,1.9×局部均值 R,0.033L,3.8σ)。Sraw=max(−0.56,2.45 tanh(R/(2B))−1.46)，零点约为 1.37B。固定参考经配准后取 fixed−current，以同一窄带算子和法向双极抑制得到 I。增量基线 Bd=max(2.45σ+0.007L,2×局部平均 I)，Sd=2.1 tanh(I/(2Bd))−0.97。

t=clip((x−front−0.04s)/(0.14s),0,1)，Q 为邻域静态暗谷风险。以既有加权和减 1.38tQ 为基础，近口允许原图与正增量竞争，对通过持续性及静态风险检查的强差分设置净分下限。低原图支撑只对较弱差分施加 −0.8 上限。缺口前 0.24s 的联合证据允许累计分降至 −0.105s，此后恢复 −0.025s。每列仍只从上列的五个允许斜率递推，取整张图的最高峰回溯。

在口门列 t=0，基础融合的下界取 max(0.90 Sraw+0.10 Sd, max(Sraw,0.93 Sd)−0.16)。强增量的独立下界为 0.90 Sd−1.20 Q。在前 0.24s 内以未饱和暗谷深度比较竞争唇缘。两个强观测沿同一局部切向夹住短断带时，在前 0.26s 内为该通道提供 0.66 的得分下限。可见原图近口分数另有保护。所有分数进入同一次 DP。

远端差分同时使用纵向平均、横纵梯度能量比及参考暗谷列间重叠比例。光滑基底上，渐隐裂纹仍有较强法向梯度，而离散斑点的轴向梯度明显。位移容忍窗里的暗谷只有与当前列重叠时才承担完整静态扣分。候选与移动划痕叠加时，用法向邻域的净增暗辅助区分新增暗谷和亮暗配对条纹。[实现与全部系数](../../../research/notch_identity_v51/terminal.py)

同图或仅有传感器波动且没有持续增量，只有在可靠配准下进入预存裂纹判别。强谷须超过 max(5.5σ,0.105L)，在前缘后 0.015s～0.20s 的获胜路径上连续至少 0.035s，并通过总分及长度门。失败返回 no_tip、空路径。配准失效保留单通道状态。"""
def main():
    scores,records,metrics=collect(b)
    from research.notch_identity_v36.batch import OUT as hist36
    from itertools import islice
    assert b.sha(hist36/'group_c.jsonl')==b.read(hist36/'group_c_seal.json')['predictions']
    with (hist36/'group_c.jsonl').open() as stream:old=json.loads(next(islice(stream,346,None)))
    target=records['group_c',347]
    assert old['source_sha']==target['source_sha']
    target['models']['v3_6']=old['models']['v3_6']
    raw_cards={g:set() for g in b.GROUPS}
    def explain(g,i,m,r,mode):
        msg=generate(g,i,m,r,mode)
        if mode=='raw_only':
            raw_cards[g].add(i)
            msg+=f' [纯灰度四栏图](raw_failures/{g}/{i:04d}.jpg)'
        return msg
    audit,entries=failure_list(b,scores,records,['v3_6','v4_2','v5_0'],explain,('full','raw_only'))
    for g,ids in raw_cards.items():
        folder=b.OUT/'raw_failures'/g;folder.mkdir(exist_ok=True,parents=True)
        for card,_,r in source_frames(g,ids,'raw_only'):card.save(folder/f"{r['frame']:04d}.jpg",quality=91)
    audit.insert(1,'蓝线为每列全部可达方向状态的最大累计分，金线取人工路径所在像素。虚线标示人工端点与裁决前全局峰。下图给出两条路径的局部净证据。反事实检验每次只放宽一项约束，仅用于封存后的归因。未标注及尖端不确定帧不纳入数值失败判定。')
    pack(b,'FAILURES_AUDIT.md',audit)
    stage='v5_1';final=[r for r in metrics if r['stage']==stage and r['mode']=='full']
    probes=read_csv(b.OUT/'paired_probes.csv');weak=[r for r in probes if r['width']!='0'];neg=[r for r in probes if r['negative']=='True']
    gates={r['group']:r['joint']>={'group_a':18,'three_point_bend':12,'group_c':14}[r['group']] and r['severe']==0 and (r['group']!='group_c' or r['median']<3.5) for r in final}
    def positives(q):return sum(r['passed']=='True' for r in q)
    res=dict(primary=stage,run=b.OUT.relative_to(b.ROOT).as_posix(),report='evidence/v5_1/REPORT.md',failures='evidence/v5_1/FAILURES_AUDIT.md',groups=final,
        overall_full=aggregate([r for (g,i,s,m),r in scores.items() if s==stage and m=='full']),
        hit5=sum(r['hit5'] for r in final),accuracy_gate=gates,speed_gate={r['group']:r['fps']>=10 for r in final},
        weak_pass=positives(weak),weak_crossed=sum(int(r['accepted']) for r in weak),weak_wrong=sum(int(r['wrong']) for r in weak),
        negative_fp=sum(r['valid']=='True' for r in neg),negative_count=len(neg),delivery=b.read(b.OUT/'delivery_check.json')['video_frames'])
    res['decision']='PRODUCTION_NO_GO' if not all(gates.values()) or not all(res['speed_gate'].values()) or res['negative_fp'] or res['weak_wrong'] else 'REVIEW'
    import numpy as np
    legacy=[r for r in neg if not r['case'].startswith('control_')]
    res['legacy_negative_fp']=sum(r['valid']=='True' for r in legacy)
    res['legacy_negative_count']=len(legacy)
    header=['# V5.1 全局自由终点 DP 修正与验证报告',
        '完整模式联合命中为'+'、'.join(f"{NAMES[r['group']]} {r['joint']}/{r['visible']}，严重 {r['severe']} 帧" for r in final)+f"。验收结论 {res['decision']}。",
        '[逐帧视频与图册](difference_views/index.html) · [失败与退化帧专项分析](FAILURES_AUDIT.md) · [冻结记录](freeze.json) · [逐项消融](ablation.csv)',
        '## 分组与评分',
        '合成与开发组A用于开发。标注仅用于预测封存后的对照。算法参数、开发组预测、开发指标与探针结果锁定后，依次一次运行三点弯和验证组C。同一帧的消融预设在同一次验证里执行。验证组曾用于历史问题诊断。排除组X已排除。',
        '## 公式与判定',
        FORMULA,
        'neck_fusion 在 V5.0 上修正近口融合和累计负分容限。zero_gate 增加可靠配准下的强预存暗谷判别。v5_1 进一步提高纯灰度净分零点。三阶段共用相同口门、拓扑约束和全局自由终点求解器。无参考输入是独立计时的 raw_only。原灰度单通道全局 DP 与 raw_only 使用同一幅证据图。',
        '## 首帧判定',
        '开发组A首帧以任务书指定的空白对照复核。其 LabelMe 尖端为不确定，不进入 19 个可见帧的分母。三点弯和验证组C首帧具有可见人工端点，应分别计入阳性。']
    first=[];calibration=[];extensions=[];speed=[]
    res['background']={};res['first_frames']={}
    for g in b.GROUPS:
        m=records[g,1]['models'];d=m[stage]['full']['diagnostics']['dual']
        annotation=scores[g,1,stage,'full']
        first.append([NAMES[g],annotation['state'],annotation['gt'] or '—',m['v5_0']['full']['tip'],m[stage]['full']['tip'],m[stage]['full']['status'],d['decision'],d.get('strong_run','—'),num(annotation['error_px'])])
        res['first_frames'][g]={'label':annotation['state'],'status':m[stage]['full']['status'],'tip':m[stage]['full']['tip'],'error_px':annotation['error_px'] or None}
        wall=b.read(b.OUT/(g+'_seal.json'))['wall_seconds']
        speed.append([NAMES[g],b.GROUPS[g],num(wall),num(b.GROUPS[g]/wall)])
        bg=[];inc=[];spans=[[],[]]
        with (b.OUT/(g+'.jsonl')).open() as cur,(b.BASE/(g+'.jsonl')).open() as oldrun:
            for a,z in zip(map(json.loads,cur),map(json.loads,oldrun)):
                assert a['source_sha']==z['source_sha']
                d=a['models'][stage]['full']['diagnostics']['dual']
                if d.get('background_raw') is not None:bg.append(d['background_raw'])
                if d.get('background_diff') is not None:inc.append(d['background_diff'])
                for dest,rec,v in zip(spans,(z,a),('v5_0',stage)):
                    out=rec['models'][v]['raw_only']
                    if out['tip']:dest.append(out['tip'][0]-out['root'][0])
        calibration.append([NAMES[g],len(bg),num(np.mean(bg) if bg else None),sum(-.60<=v<=-.35 for v in bg),len(inc),num(np.mean(inc) if inc else None)])
        res['background'][g]=dict(raw_mean=float(np.mean(bg)),difference_mean=float(np.mean(inc)) if inc else None,raw_frames=len(bg),inside_target=sum(-.60<=v<=-.35 for v in bg))
        extensions.append([NAMES[g],*[f"{max(v,default=0)} / {sum(x>1000 for x in v)}" for v in spans]])
    header+=[table(['组','标注状态','人工坐标','V5.0','V5.1','输出状态','证据来源','连续强谷列','误差 px'],first),
        '## 背景标定与单通道延伸',
        '侧翼抽样取缺口前方、距口门中线超过 0.12s 的有效区域。表内是各帧均值的等权平均，侧翼包含真实材料纹理，属于背景代理量。对于差分同时给出有效帧数。',table(['组','原图帧','平均 Sraw','均值在目标区间帧数','差分帧','平均 Sdiff'],calibration),
        '另逐帧检查全序列纯灰度预测的水平跨度。下表每格为最大跨度（px）与跨度超过 1000 px 的帧数。人工端点精度见后面的标注帧表。',table(['组','V5.0','V5.1'],extensions)]
    for g,i in [('group_a',67),('group_c',1)]:
        header.append(f"{NAMES[g]} {i} 纯灰度尖端误差由 {num(scores[g,i,'v5_0','raw_only']['error_px'])} 变为 {num(scores[g,i,stage,'raw_only']['error_px'])} px。")
    header+=['## 吞吐口径','以下为六进程整组经过时间，含两种预测模式、标注帧逐项消融、读取、校验及写盘。后续消融表中的 FPS 是单帧推理耗时的倒数。',table(['组','帧数','整组秒数','批处理帧/秒'],speed)]
    header+=metric_tables(b,metrics)+focus_tables(b,scores,records,['v3_6','v4_2','v5_0',stage])
    header+=['## 合成验收',f"原有阴性误报 {res['legacy_negative_fp']}/{len(legacy)}，另有同图空白与独立噪声空白对照。弱带通过 {res['weak_pass']}/{len(weak)}，{res['weak_crossed']} 条轨迹跨过弱带，其中 {res['weak_wrong']} 条在恢复段错接。新增反光对照在缺口前制造 10 或 15 个原尺度像素的平灰断带，固定图保留亮脊，控制同一位置的差分可见性。"]
    header+=probe_tables([('V5.0',read_csv(b.BASE/'paired_probes.csv')),('V5.1',probes)])
    q0=read_csv(b.BASE/'paired_probes.csv')
    subset=[]
    for case in ('P2_fade','P5_plastic_zone','P6_deformed_scratch'):
        for desc,match in [('半倍率',lambda r:float(r['zoom'])==.5),('暗曝光',lambda r:r['photo']=='dim'),('半倍率且暗曝光',lambda r:float(r['zoom'])==.5 and r['photo']=='dim')]:
            a=[r for r in q0 if r['case']==case and match(r)]
            z=[r for r in probes if r['case']==case and match(r)]
            subset.append([case,desc,f"{positives(a)}/{len(a)}",f"{positives(z)}/{len(z)}"])
    header+=['## 暗曝光与半倍率',table(['探针','子集','V5.0','V5.1'],subset)]
    dev=[]
    for path in sorted(b.OUT.parent.glob('v51_dp_fix_20261119_r*')):
        if not (path/'group_a_scores.csv').exists():continue
        q=read_csv(path/'paired_probes.csv')
        a=aggregate([x for x in read_csv(path/'group_a_scores.csv') if x['stage']==stage and x['mode']=='full'])
        dev.append([path.name[-3:],a['joint'],num(a['median']),positives([x for x in q if x['case']=='P1_weak_gap']),sum(int(x['wrong']) for x in q)])
    header+=['## 开发迭代',table(['轮次','开发组A Joint /19','中位 px','弱带通过 /216','错接'],dev)]
    header+=['## 冻结验证结论',
        '开发组A 67 在两种模式下误差均为 0.27 px，第 398 帧依然向右偏约 12 px。验证组C首帧正确输出预存端点，误差 1.26 px。纯灰度在验证组C全序列的最大水平跨度从 2099 降至 301 px，超过 1000 px 的帧从 562 降至零。纯灰度第 195 帧仍有 106.02 px 误差。',
        '三点弯 335 的误差从 197.04 降至 8.67 px。第 215 帧在 x=1520 时，预测沿下方水平暗线停于 y=2730，而人工裂纹已向上弯至 y=2714.32，两条路径在同一列相距 15.68 px。人工端点已经可达，V=23.93，算法在其前方约 85 列取得 V=55.58。取消转弯代价或累计负分下限都未恢复端点。第 503 帧已经追过人工端点，后续 15 列平均 S=+0.30，80% 的列是正分。两个失败方向相反。下一轮应在开发组构建“连续弱段后再生长”和“尖端后短段背景仍为正分”的配对样本，分开检验沿真实路径的累计分与背景竞争峰。 [三点弯 215 曲线](curves/three_point_bend/0215_full.png) · [三点弯 503 曲线](curves/three_point_bend/0503_full.png)',
        '验证组C 510 在人工尖端后又追了 17 列，平均 S=+0.69，94% 的列给出正分。优先排查这些列上参考差分、原灰度谷深与背景长纹理的相对得分。 [验证组C 510 曲线](curves/group_c/0510_full.png)']
    pack(b,'REPORT.md',header)
    for dest in (b.OUT,b.ROOT/'evidence'/stage,b.ROOT/'evidence'):b.save(dest/'latest_metrics.json',res)
    print(res)
if __name__=='__main__':main()
