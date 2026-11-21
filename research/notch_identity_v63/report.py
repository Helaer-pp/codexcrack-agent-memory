"""Generate the acceptance reports from frozen real predictions and paired synthetic results."""
from collections import Counter
import json
import math
from research.notch_identity_v61 import batch as prior61
from research.notch_identity_v62 import batch as prior62
from research.notch_identity_v61.report import SETS,count
from research.notch_identity_v62.report import visible
from research.notch_identity_v512.report import table,f
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b
from .run import frozen

OUT=b.OUT
DOC=b.ROOT/'evidence/v6_3'


def link(path,label):
    return f'[{label}](../../output/experiments/{OUT.name}/{path})'


def pic(g,pl,i):
    return link(f'audit_views/{g}_{pl}_{i:04d}.jpg','单帧与分支曲线')


def write(name,sections):
    (DOC/name).write_text('\n\n'.join(sections)+'\n',encoding='utf8')


def frame_data():
    main=[];coverage=[];failures=[];mt=[];changed=[];metrics={}
    for g,pl,name in SETS:
        a=visible(prior61.OUT,g,pl);old=visible(prior62.OUT,g,pl);new=visible(OUT,g,pl)
        assert a.keys()==old.keys()==new.keys()
        metrics[g,pl]=count(new.values(),'joint')
        regained=sum(r['joint']=='True' and old[i]['joint']=='False' for i,r in new.items())
        lost=sum(r['joint']=='False' and old[i]['joint']=='True' for i,r in new.items())
        main.append([name,b.GROUPS[g],len(new),count(a.values(),'joint'),count(old.values(),'joint'),
                     *[count(new.values(),k) for k in ('joint','hit5','hit10','severe')],regained,lost])
        c=Counter()
        path=OUT/(g+'.jsonl')
        assert b.sha(path)==b.read(OUT/(g+'_seal.json'))['predictions']
        for rec in map(json.loads,path.open(encoding='utf8')):
            i=rec['frame'];model=rec['placements'][pl]['S2']['full'];d=model['diagnostics']['dual']
            reg=(d.get('registration') or {}).get('status','—')
            c[reg]+=1;c[d.get('ref_mode','missing')]+=1;c['valid']+=bool(model['tip'])
            branches=d['branches']
            chosen=next((br for br in branches if d['pick']==f"BRANCH_{br['id']}"),{})
            c['clean']+=bool(chosen.get('curve',{}).get('clean_primer_admitted'))
            c['short']+=any(br['reason']=='MAPPED_SHORT_ISOLATED' for br in branches)
            if i not in new:continue
            r=new[i];pr=old[i];gt=json.loads(r['gt'])
            near=min((math.dist(br['tip'],gt) for br in branches if br['tip']),default=None)
            if r['joint']!=pr['joint']:
                changed.append([name,i,pr['joint'],r['joint'],f(pr['error_px']),f(r['error_px']),r['stop']])
            if g=='group_h':
                wins=rec['mappings'][pl]['S2']['windows']
                def flank_modes(point):
                    w=next((w for w in wins if point and w['x0']<=point[0]<w['x1']),None)
                    return w['up_mode']+'/'+w['down_mode'] if w else '—'
                mt.append([i,a[i]['joint'],pr['joint'],r['joint'],f(r['error_px']),r['stop'],reg,
                           flank_modes(model['tip']),flank_modes(gt),f(near)])
            if r['joint']=='True':continue
            if not r['error_px']:
                causes={'INSUFFICIENT_TOTAL':'候选路径的累计证据未达发布门槛','MOUTH_DEAD_END':'从缺口唇缘出发的路径未通过连续性检查','MAPPED_SHORT_ISOLATED':'唯一可达的映射分支过短，缺少向前连续支撑','EMPTY':'回溯为空','NO_CONFIRMED_PREEXISTING':'静态核查缺少连续确认段','CONTOUR_DUAL_RUN_SHORT':'轮廓回退分支的双证据连续列不足'}
                reason=causes.get(r['stop'],'算法未发布端点，见终止原因')
            elif r['hit10']=='True':
                reason='尖端命中，路径覆盖率或精确率不足'
            elif near is not None and near<=10:
                reason='有近端点候选，最终发布的分支偏离'
            else:
                reason='全部分支均未命中，'+('提前终止' if float(r['dx'])<0 else '越过尖端')
            failures.append(dict(group=g,placement=pl,frame=i,error=r['error_px'],dx=r['dx'],reason=reason,
                                 route=r['source'],registration=reg,stop=r['stop'],branches=len(branches),
                                 best_branch_error=near,winner_run=chosen.get('curve',{}).get('longest_dual_run')))
        coverage.append([name,c['edge'],c['global_refined'],c['MAPPED'],c['ZERO_FALLBACK'],c['valid'],c['clean'],c['short']])
    write_csv(OUT/'failure_index.csv',failures)
    write_csv(OUT/'crack_lengths.csv',[r for g in b.GROUPS for r in b.read_csv(OUT/(g+'_lengths.csv'))])
    return dict(metrics=metrics,main=table(['组/点位','帧','可见','6.1 Joint','6.2 Joint','6.3 Joint','Hit@5','Hit@10','>100 px','恢复','新增失败'],main),
                coverage=table(['组/点位','参考边缘','中心精修','有采用窗','全窗回退','有尖端','单极放行且最终选中','有映射短分支被拦'],coverage),
                changes=table(['组','帧','6.2 Joint','6.3 Joint','原误差 px','现误差 px','终止'],changed),
                failures=table(['组','点位','帧','误差 px','横差 px','帧级配准','终止','最近分支误差 px','原因','图'],[
                    [r['group'],r['placement'],r['frame'],f(r['error']),f(r['dx']),r['registration'],r['stop'],f(r['best_branch_error']),r['reason'],pic(r['group'],r['placement'],r['frame'])] for r in failures]),
                mt=table(['开发组H帧','6.1 Joint','6.2 Joint','6.3 Joint','误差 px','终止','帧级配准','预测处上/下窗','标注处上/下窗','最近分支误差 px'],mt))


def probes():
    path=OUT/'paired_probes.csv'
    assert b.sha(path)==b.read(OUT/'probe_seal.json')['csv']
    rows=b.read_csv(path)
    def key(r):return tuple(r[k] for k in ('case','width','contrast','zoom','noise','seed','photo','stage'))
    old={key(r):r for r in b.read_csv(prior62.OUT/path.name)}
    assert len(rows)==len(old)==1404 and set(map(key,rows))==old.keys()
    neg=[r for r in rows if r['negative']=='True']
    pos=[r for r in rows if r['negative']=='False']
    detail=[]
    for case in sorted({r['case'] for r in rows}):
        rr=[r for r in rows if r['case']==case]
        detail.append([case,len(rr),count([old[key(r)] for r in rr],'passed'),count(rr,'passed'),sum(r['negative']==r['valid']=='True' for r in rr)])
    prior_fp=[r for r in neg if old[key(r)]['valid']=='True']
    row,=prior_fp
    loss=sum(r['passed']=='False' and old[key(r)]['passed']=='True' for r in pos)
    gains=sum(r['passed']=='True' and old[key(r)]['passed']=='False' for r in pos)
    short=(f"负样本误报 {count(neg,'valid')}/{len(neg)}。P4_open 和 weak_material_bridge 分别通过 "
           f"{count([r for r in rows if r['case']=='P4_open'],'passed')}/36、"
           f"{count([r for r in rows if r['case']=='weak_material_bridge'],'passed')}/36。"
           f"{len(pos)} 个正样本逐例比对原通过判据，新增失败 {loss}，新增通过 {gains}。")
    glare=(f"旧误报 {row['case']}（倍率 {row['zoom']}，噪声 {row['noise']}，种子 {row['seed']}，曝光 {row['photo']}）"
           f"配准为 {row['registration']}，最大连续双证据 {row['longest_dual']} 列，"
           f"触发短分支拒绝 {row['mapped_short_rejected']}，实际发布尖端 {row['valid']}。")
    return short,glare,table(['工况','试次','6.2 通过','6.3 通过','6.3 误报'],detail)


def group_h():
    rows=b.read_csv(OUT/'group_h_shift.csv');shift=[]
    for delta in ('-150','-350'):
        subset=[r for r in rows if r['dx']==delta];assert len(subset)==410
        drift=[float(r['tip_drift']) for r in subset if r['tip_drift']]
        shift.append([delta,len(subset),*[count(subset,k+'_equal') for k in ('material_band','reference_apex','current_apex','status','path')],
                      len(drift),f(max(drift,default=None)),','.join(sorted({str(json.loads(r['reference_apex'])[0]) if r['reference_apex'] else '—' for r in subset}))])
    ncc=b.read_csv(OUT/'group_h_ncc_summary.csv')
    frame=b.read_csv(OUT/'group_h_ncc_frames.csv')
    adopted=sum(int(r['adopted']) for r in ncc)
    attempts=sum(int(r['attempt']) for r in ncc)
    entered=sum(int(r['ncc']) for r in ncc)
    reached=f"放开白底漆上限后，{attempts:,} 次尝试中 {entered:,} 次进入 NCC，实际采用 {adopted} 次。410 帧中 {count(frame,'mapped')} 帧至少有一个采纳窗，{410-count(frame,'mapped')} 帧仍全部零回退。采纳一个合并窗计一次，即使两侧共用。非零位移另列。V6.2 的 63,960 次尝试全部在 NCC 之前被拒，两版物理尺度与窗口数量不同。"
    stages=b.read_csv(OUT/'group_h_stages.csv')
    assert b.sha(OUT/'group_h_stage_predictions.json')==b.read(OUT/'group_h_stage_seal.json')['sha']
    step=[];targets=[]
    for key,label in [('V62','V6.2'),('geometry','仅换材料带与缺口精修'),('geometry_mask','再换配准掩膜与 NCC 数值处理'),('V63','完整 V6.3，加入两项终端复核')]:
        rr=[r for r in stages if r['variant']==key];assert len(rr)==18
        step.append([label,count(rr,'joint'),count(rr,'severe'),sum(bool(r['error_px']) for r in rr)])
        targets.append([label,*[f(next(r['error_px'] for r in rr if int(r['frame'])==i)) for i in (216,221,252,317)]])
    return dict(shift=table(['实移 px','帧','材料带相同','参考顶点相同','当前顶点相同','状态相同','全路径相同','两次均有尖端','最大尖端漂移 px','左移后参考 x'],shift),
                reached=reached,ncc=table(['窗','尝试','上下文不足','低纹理','进入 NCC','峰不明确','低相关','采用','采用非零位移'],
                    [[r[k] for k in ('side','attempt','insufficient','low_texture','ncc','ambiguous','low_ncc','adopted','nonzero')] for r in ncc]),
                ablation=table(['按顺序替换组件','Joint/18','>100 px','发布尖端'],step),
                specific=table(['离线回放','216 误差 px','221 误差 px','252 误差 px','317 误差 px'],targets))


def main():
    frozen();DOC.mkdir(parents=True,exist_ok=True)
    real=frame_data();syn,glare,matrix=probes();mt=group_h()
    bench=b.read(OUT/'bench_S2_4.json');fps=bench['n']/bench['wall_seconds'];rate=bench['n']/bench['seconds']
    speed=f"三点弯 520 帧，以 4 个工作进程独立计时，整池墙钟吞吐 {fps:.2f} FPS，4.5 FPS 要求{'通过' if fps>=4.5 else '未通过'}。按逐帧处理耗时合计折算 {rate:.2f} FPS。"
    summary='，'.join(f"{name} {real['metrics'][g,pl]}/{len(visible(OUT,g,pl))}" for g,pl,name in SETS)+'。开发组H目标为至少 9/18 且无超过 100 px 误差。'
    method='纵向亮带使用整幅输入 ROI 的多列灰度中位数，保留基准点纵向平移。内部缺口先全宽搜索，再围绕候选主体与右端用局部百分位阈值精修；边缘缺口沿用快路。配准掩膜接受白色底漆的 250–255 灰度，检查有限值、暗背景以及位移足迹。对相关计算先减去常数 255，避免平坦白区方差计算的大数相消。位移搜索半径 5 px，采用门槛 NCC ≥0.84。'
    gates='全窗零回退时，缩短连续列要求只适用于低纹理白色窗口内与原灰度窄脊重合、无明显负差分侧翼的正差分；其余分支保留尺度门槛。MAPPED 分支若双证据连续列小于 max(10, round(0.035 × 尺度))，且整条候选短于两倍该门槛，则拒绝发布。'
    policy='代码先冻结，再回放原图。开发组A与开发组H为开发组，三点弯和验证组C仅冻结验证，排除组X排除。人工标注仅作离线比较。Joint 同时要求端点误差 ≤10 原图像素、路径精确率和覆盖率分别 ≥80%。验证组C原点与亮区共用同一批图像。'
    artifact=' · '.join([link('difference_views/index.html','2,043 帧参考、当前、结果、差分及四组视频'),link('crack_lengths.csv','2,605 个帧与点位的尖端坐标和长度（px）'),link('freeze.json','源码冻结清单'),'[失败帧审计](FAILURES_AUDIT.md)','[开发组H专项](GROUP_H_REPORT.md)'])
    inputs=' · '.join([link('group_h_0078_geometry.png','第 78 帧原图定位对照'),link('group_h_shift.csv','全序列两档位移与坐标'),link('group_h_ncc_windows.csv','逐窗拒绝或采用'),link('group_h_ncc_frames.csv','逐帧计数'),link('group_h_stages.csv','开发组H分步回放'),link('difference_views/group_h.mp4','开发组H视频')])
    cause='第 252 帧的误差由 102.70 降至 37.68 px，仅替换几何组件就出现同样改善。第 216 帧在采用新配准后从拒绝变为提前 116.75 px；第 221 帧在仅替换几何时已提前 117.37 px。两帧各有一个已发布分支，连续双证据分别为 13、24 列。预测端点处上下窗均采用分侧配准，但两个标注尖端所在的上下窗均回退为零位移。第 317 帧因证据累计不足而漏检。下一轮宜检查这几帧从已发布端点到标注端点之间的原灰度窄脊、差分和逐窗配准状态，重点区分路径是否可达以及何处停止。'
    controls=b.read_csv(OUT/'primer_controls.csv')
    rows=[]
    for shade in ('0','22'):
        for mode,name in [('unipolar','新增暗线'),('displaced_line','旧线侧移 3 px'),('unchanged','无变化')]:
            group=[r for r in controls if r['fixture_gray']==shade and r['mode']==mode]
            assert len(group)==15
            rows.append([shade,name,len(group),sum(bool(r['old_tip']) for r in group),sum(bool(r['tip']) for r in group),
                         count(group,'selected_by_exception')])
    extra=table(['缺口灰度','额外白底漆工况','长度试次','6.2 发布','6.3 发布','单极放行'],rows)
    limitation='冻结后另设白底漆对照，裂纹长度取 8–22 px。均匀白底上，零回退单极复核新增放行 4 条已知新增的合成短线（10–13 px）；该规则在正式实帧中没有新增选中分支。模拟旧线侧移 3 px 时，两种缺口灰度合计出现 22/30 误报，V6.2 为 18/30，新增 4 次均经过 MAPPED 路由。这组额外压力试验说明，正式矩阵的 0/468 不能外推到所有红蓝偶极。'
    controls_link=link('primer_controls.csv','90 个冻结后白底漆对照')
    stable='V6.3 S2 作为研究候选提供。在 run_crack_tip.py 顶部启用 use_validation_candidate 或运行 CrackTipRunner.exe --candidate 即可使用，日常默认为 V5.15 S2。'
    checks=b.ROOT/'output/verification/v63_public_runner/checks.csv'
    if checks.is_file():
        verified=b.read_csv(checks)
        assert len(verified)==9 and all(r['matched']=='True' for r in verified)
        stable+=' 同一 EXE 回放 9 个帧与点位组合，已核对状态、尖端、完整路径、长度与输出媒体。[入口复核记录](../../output/verification/v63_public_runner/checks.csv)'
    write('REPORT.md',['# V6.3 白底漆配准与参考缺口定位',summary,artifact,'## 本轮方法',method,gates,policy,'## 实帧与速度',real['main'],real['coverage'],speed,'## 开发组H基准点与 NCC',mt['shift'],mt['reached'],mt['ncc'],mt['ablation'],cause,inputs,'## 合成与交付',syn,glare,limitation,extra,controls_link,link('paired_probes.csv','合成矩阵全部结果'),stable])
    write('FAILURES_AUDIT.md',['# V6.3 失败审计',summary,real['main'],'## 对 V6.2 的逐帧变化',real['changes'],'## 全部可见标注失败帧',real['failures'],'## 开发组H的定位、配准与终止',mt['shift'],mt['ncc'],mt['specific'],cause,inputs,'## 成对合成回归',syn,glare,matrix,limitation,extra,controls_link])
    write('GROUP_H_REPORT.md',['# 开发组H MT · V6.3 全序列',summary,'## 实际基准点平移',mt['shift'],'两档扰动均从原始图像重建输入 ROI，参考与当前 P1/P2 同步移动。表内坐标均已还原至原图。全路径相同包含两次均为空，另列同时有尖端的帧数。','## 白底漆与局部配准',mt['reached'],mt['ncc'],'## 可见标注与逐步替换',mt['ablation'],mt['specific'],real['mt'],cause,limitation,extra,controls_link,inputs])
    print(summary,speed,flush=True)

if __name__=='__main__':main()
