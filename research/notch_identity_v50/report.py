"""Assemble post-freeze comparisons, primary/control audits and handoff metrics."""
from collections import Counter
import json
from . import batch as b
from .curves import generate
from .difference_views import source_frames
from research.notch_identity_v42.reporting import collect,pack,metric_tables,focus_tables,probe_tables,failure_list,read_csv,table,NAMES,num,aggregate

def main():
    scores,records,metrics=collect(b)
    # Frame 347 is unlabelled; attach only its sealed historical outputs for the qualitative table.
    from itertools import islice
    from research.notch_identity_v36.batch import OUT as hist36
    hist02=b.ROOT/'output/experiments/raw_notch_trace_v2_20261118_r02'
    target=records['group_c',347]
    for base,file,seal,stage in [(hist02,'locked.jsonl','locked_seal.json','r02'),(hist36,'group_c.jsonl','group_c_seal.json','v3_6')]:
        assert b.sha(base/file)==b.read(base/seal)['predictions']
        with (base/file).open() as stream:old=json.loads(next(islice(stream,346,None)))
        assert (old['frame'],old['source_sha'])==(347,target['source_sha'])
        target['models'][stage]=old['models'][stage] if 'models' in old else {'full':old['full']}
    raw_cards={g:set() for g in b.GROUPS}
    def explain(g,i,m,r,mode):
        msg=generate(g,i,m,r,mode)
        if mode=='raw_only':
            raw_cards[g].add(i)
            msg+=f' [纯灰度四栏图](raw_failures/{g}/{i:04d}.jpg)'
        return msg
    audit,entries=failure_list(b,scores,records,['v3_6','v4_2'],explain,('full','raw_only'))
    for g,ids in raw_cards.items():
        folder=b.OUT/'raw_failures'/g;folder.mkdir(exist_ok=True,parents=True)
        for card,_,r in source_frames(g,ids,'raw_only'):card.save(folder/f"{r['frame']:04d}.jpg",quality=91)
    audit.insert(1,'蓝线为每列全部可达方向状态的最大累计分，金线取人工路径所在像素。虚线标示人工端点与裁决前全局峰。下图给出两条路径的局部净证据。反事实检验每次只放宽一项约束，仅用于封存后的归因。未标注及尖端不确定帧不纳入数值失败判定。')
    pack(b,'FAILURES_AUDIT.md',audit)
    stage='v5_0';final=[r for r in metrics if r['stage']==stage and r['mode']=='full']
    probes=read_csv(b.OUT/'paired_probes.csv');weak=[r for r in probes if r['width']!='0'];neg=[r for r in probes if r['negative']=='True']
    gates={r['group']:r['joint']>={'group_a':18,'three_point_bend':12,'group_c':15}[r['group']] and r['severe']==0 for r in final}
    def positives(q):return sum(r['passed']=='True' for r in q)
    res=dict(primary=stage,run=b.OUT.relative_to(b.ROOT).as_posix(),report='evidence/v5_0/REPORT.md',failures='evidence/v5_0/FAILURES_AUDIT.md',groups=final,
        overall_full=aggregate([r for (g,i,s,m),r in scores.items() if s==stage and m=='full']),
        hit5=sum(r['hit5'] for r in final),accuracy_gate=gates,speed_gate={r['group']:r['fps']>=20 for r in final},
        weak_pass=positives(weak),weak_crossed=sum(int(r['accepted']) for r in weak),weak_wrong=sum(int(r['wrong']) for r in weak),
        negative_fp=sum(r['valid']=='True' for r in neg),negative_count=len(neg),delivery=b.read(b.OUT/'delivery_check.json')['video_frames'])
    res['decision']='PRODUCTION_NO_GO' if not all(gates.values()) or not all(res['speed_gate'].values()) or res['negative_fp'] or res['weak_wrong'] else 'REVIEW'
    header=['# V5.0 全局自由终点 DP 开发与验证报告',
        '完整模式联合命中为'+'、'.join(f"{NAMES[r['group']]} {r['joint']}/{r['visible']}" for r in final)+f"。严重误差 {res['overall_full']['severe']} 帧。验收结论 {res['decision']}。",
        '[逐帧图册、差分与三组视频](difference_views/index.html) · [失败与受损帧曲线](FAILURES_AUDIT.md) · [冻结记录](freeze.json) · [同帧消融表](ablation.csv)',
        '## 数据隔离与标定',
        '开发输入只有合成探针和开发组A。开发期间在每一版生成预测后才读取人工标注计算误差。三点弯与验证组C按顺序各运行一次冻结算法。张数按图像身份和序号核对。验证组曾用于历史版本问题回顾，本次结果衡量相同冻结逻辑在这两组的表现。排除组X已排除。',
        '## 净证据与全局寻优',
        '在缺口前缘定位上下唇，在局部搜索区域内计算暗谷。以锚距 s 决定半径，局部曝光跨度 L 和残差 MAD 决定噪声 σ，噪声下限为 0.006 L。分别在 0.007s、0.014s、0.024s 半径取中心相对两侧较暗的一侧仍能满足的暗谷深度。将该响应与三个方向的灰度开运算组合，抑制干净基底上的孤立斑点，再沿切向平滑。记结果为 R。基准 τ=max(2.25σ+0.007L,1.9×局部平均 R)。原图净证据为 Sraw=2.1 tanh(R/(2τ))−0.97。',
        '固定参考经锚点映射及局部平移校正后取 D=fixed−current，对 D 应用相同的窄脊算子，并按法向邻域负极性与正极性强度比抑制双极条纹。τd=max(2.45σ+0.007L,2×局部平均增量响应)。增量分以相同 tanh 函数计算。参考暗谷在 ±0.025s 邻域内的持续响应与当前深度、噪声共同得到风险系数 Q∈[0,1]。缺口近处参考唇缘容易与裂纹重合，静态扣分按前向距离渐增。设 t=clip((x−front−0.04s)/(0.14s),0,1)，Sfull=(0.90−0.47t)Sraw+(0.10+0.47t)Sdiff−1.38tQ。当前图缺少暗谷支撑时，上限设为 −0.8。无参考、配准失败、没有可测增量或像素无对应时回退至原图证据。',
        '从前缘至 0.020s 处，只允许与缺口暗体连通且前方仍有暗谷支撑的像素起追。状态 V(x,y,d) 保存最后一步斜率 d∈{−2,−1,0,1,2}。合法种子初始化为 max(0,S)，向右递推 S(x,y)+max_k[V(x−1,y−d,k)−0.13|d|−0.19|d−k|]。低于 −0.025s 的延伸失效。全局总分最高的状态决定尖端，沿前驱一次回溯。总分下限 0.040s，水平长度下限 0.030s，最终路径做闭环检测。24 组小栅格以穷举对照全部可达值、最优分和回溯代价。',
        'global_raw 使用原图与相同自由终点求解器。joint_dp 合并原图与参考图证据，跳过最终闭环判定。v5_0 启用最终闭环判定。raw_only 独立完成图像准备和推理。r02、V3.6、V4.2 对照来自已封存同帧预测与原运行计时。']
    dev=[]
    for path in sorted(b.OUT.parent.glob('v50_global_dp_20261119_r*')):
        if not (path/'group_a_scores.csv').is_file():continue
        q=read_csv(path/'paired_probes.csv')
        a=aggregate([r for r in read_csv(path/'group_a_scores.csv') if r['stage']==stage and r['mode']=='full'])
        dev.append([path.name[-3:],a['joint'],num(a['median']),positives([r for r in q if r['case']=='P1_weak_gap']),sum(r['negative']=='True' and r['valid']=='True' for r in q)])
    header+=[table(['开发轮','开发组A Joint /19','中位 px','弱带通过 /216','阴性 FP /216'],dev)]
    header+=metric_tables(b,metrics)+focus_tables(b,scores,records,['r02','v3_6','v4_2','v5_0'])
    header+=['相邻版本对弱带采用不同事件定义。V5 路径逐列连续，统计确实越过已知弱带并延伸至少 4 个原尺度像素的路径，在后方 8 个原尺度像素上核对走向，匹配比例低于 80% 时记错接。V4.2 的计数来自跳列和显式重连事件。跨版可直接比较同一口径的弱带通过数。']
    header+=probe_tables([('V4.2',read_csv(b.BASE/'paired_probes.csv')),('V5.0',probes)])
    header+=['## 失败与后续验证',f"合成阴性误报 {res['negative_fp']}/{len(neg)}。弱带通过 {res['weak_pass']}/{len(weak)}，跨带 {res['weak_crossed']} 次，其中 {res['weak_wrong']} 次在断后选错分支。实测各失败帧和相对 V3.6、V4.2 的退化帧均附原图、对应参考及得分曲线。优先改善长程弱谷与竞争纹理的净得分排序，在新开发样本和合成探针上验证，再冻结到独立数据。"]
    header+=['三点弯 335 的人工端点原本不可达。仅去掉累计负分下限，峰值误差从 197.04 降至 9.60 px。503 从 284.10 降至 16.80 px，恢复长主干后仍有末端误差。应针对真实连续弯曲但局部证据为负的下唇构造独立开发探针，同时保留分离划痕阴性控制。 [335 得分曲线](curves/three_point_bend/0335_full.png) · [503 得分曲线](curves/three_point_bend/0503_full.png)',
        '验证组C 1 当前图与固定参考相同，回退到原图后，在人工端点右侧多追了 2070 列。这段路径平均 S 为 +0.28、74% 像素为正，形成远端假峰。分别放宽转弯与负分限制均未恢复尖端。应在开发数据加入同图参考下延伸很远的连通背景纹理，校准原图分数的背景零点。验证组C 7 的峰值距人工点约 4 px，但总分 5.49 低于输出下限 7.48，独立计作漏检。 [验证组C 1 得分曲线](curves/group_c/0001_full.png) · [验证组C 7 得分曲线](curves/group_c/0007_full.png)']
    pack(b,'REPORT.md',header)
    for dest in (b.OUT,b.ROOT/'evidence'/stage,b.ROOT/'evidence'):b.save(dest/'latest_metrics.json',res)
    print(res)
if __name__=='__main__':main()
