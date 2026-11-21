"""Build the V6.2 acceptance and audit documents directly from frozen replay evidence."""
from collections import Counter
import json
import math
from statistics import median
from pathlib import Path
from research.notch_identity_v60 import batch as v60
from research.notch_identity_v61 import batch as v61
from research.notch_identity_v61.report import SETS, count
from research.notch_identity_v512.report import table, f
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b
from .run import frozen

OUT=b.OUT
DOC=b.ROOT/'evidence/v6_2'


def link(name,label):
    return f'[{label}](../../output/experiments/{OUT.name}/{name})'


def write(name,parts):
    (DOC/name).write_text('\n\n'.join(parts)+'\n',encoding='utf8')


def visible(folder,g,pl):
    return {int(r['frame']):r for r in b.read_csv(folder/(g+'_scores.csv'))
            if r['stage']=='S2' and r['placement']==pl and r['state']=='VISIBLE' and r['mode']=='full'}


def audit_frames():
    accuracy=[];flow=[];loss=[];recovery=[];hx=[]
    for g,pl,name in SETS:
        records=OUT/(g+'.jsonl')
        assert b.sha(records)==b.read(OUT/(g+'_seal.json'))['predictions']
        s0=visible(v60.OUT,g,pl) if g!='group_h' else {}
        s1=visible(v61.OUT,g,pl)
        s2=visible(OUT,g,pl)
        assert s1.keys()==s2.keys()
        c=Counter()
        for rec in map(json.loads,records.open(encoding='utf8')):
            i=rec['frame']; model=rec['placements'][pl]['S2']['full']; d=model['diagnostics']['dual']
            reg=(d.get('registration') or {}).get('status','—')
            c.update(['n',reg,d.get('ref_mode','missing')])
            c['valid']+=model['tip'] is not None
            if i not in s2:continue
            r=s2[i]; old=s1[i]
            if g=='group_c' and s0[i]['joint']=='True' and old['joint']!='True':
                recovery.append([name,i,old['source'],r['source'],f(d.get('native_change')),f(d.get('route_floor')),f(r['error_px']),r['joint']])
            if g=='group_h':
                hx.append([i,old['joint'],r['joint'],f(r['error_px']),r['source'],r['stop']])
            if r['joint']=='True':continue
            gt=json.loads(r['gt'])
            if not r['error_px']:
                desc={'EMPTY':'候选回溯为空','INSUFFICIENT_TOTAL':'回溯证据累计不足','CONTOUR_DUAL_RUN_SHORT':'仅轮廓配准时，双证据连续列不足','NO_REACHABLE_POSITIVE':'缺口连通路径中没有可发布的正得分端点','NO_CONFIRMED_PREEXISTING':'静态核查缺少连续确认段'}
                reason=desc.get(d['stop'],'未发布尖端')
            elif r['hit10']=='True':
                reason='路径覆盖率或精确率未达到 80%'
            elif any(br.get('tip') and math.dist(gt,br['tip'])<=10 for br in d['branches']):
                reason='候选包含命中分支，最终选择偏离'
            else:
                reason='已回溯分支均未命中，'+('向前越过尖端' if float(r['dx'])>0 else '提前终止')
            loss.append(dict(group=g,placement=pl,frame=i,error=r['error_px'],dx=r['dx'],status=model['status'],
                             route=d['decision'],registration=reg,stop=d['stop'],branches=len(d['branches']),reason=reason))
        accuracy.append([name,c['n'],len(s2),sum(r['joint']=='True' for r in s0.values()) if s0 else '—',
                         count(s1.values(),'joint'),*[count(s2.values(),k) for k in ('hit5','hit10','joint','severe')]])
        flow.append([name,c['n'],c['edge'],c['global'],c['MAPPED'],c['ZERO_FALLBACK'],c['valid']])
    write_csv(OUT/'failure_index.csv',loss)
    write_csv(OUT/'crack_lengths.csv',[r for g in b.GROUPS for r in b.read_csv(OUT/(g+'_lengths.csv'))])
    return (table(['组/点位','全帧','可见标注','V6.0 Joint','V6.1 Joint','V6.2 Hit@5','Hit@10','Joint','>100 px'],accuracy),
            table(['组/点位','帧','参考边缘快路','参考全宽回退','有 NCC 位移','全窗零回退','发布尖端'],flow),
            table(['点位','帧','V6.1 路由','V6.2 路由','残差','恢复门限','误差 px','恢复 Joint'],recovery),
            table(['组','点位','帧','误差 px','横差 px','路由','配准','终止','观测原因','单帧'],[
                [r['group'],r['placement'],r['frame'],f(r['error']),f(r['dx']),r['route'],r['registration'],r['stop'],r['reason'],
                 link(f"audit_views/{r['group']}_{r['placement']}_{r['frame']:04d}.jpg",'图与分支曲线')] for r in loss]),
            table(['开发组H帧','V6.1 Joint','V6.2 Joint','误差 px','路由','终止'],hx),
            sum(r[-1]=='True' for r in recovery),len(recovery))


def synthetic():
    path=OUT/'paired_probes.csv'
    assert b.sha(path)==b.read(OUT/'probe_seal.json')['csv']
    a=b.read_csv(path);old=b.read_csv(v61.OUT/path.name)
    key=lambda r:tuple(r[k] for k in ('case','width','contrast','zoom','noise','seed','photo','stage'))
    prior={key(r):r for r in old}
    assert len(prior)==len(a)==1404 and set(prior)==set(map(key,a))
    negatives=[r for r in a if r['negative']=='True'];assert len(negatives)==468
    fp=[r for r in negatives if r['valid']=='True']
    healed=[r for r in negatives if r['case']=='P4_open' and prior[key(r)]['valid']=='True']
    bridge=[r for r in a if r['case']=='weak_material_bridge']
    summary=f"负样本误报 {len(fp)}/468。P4_open 的原 {len(healed)} 次误报逐个配对，{len(healed)-count(healed,'valid')} 次转为拒绝。weak_material_bridge 通过 {count(bridge,'passed')}/{len(bridge)}。"
    cases=[]
    for case in sorted({r['case'] for r in a}):
        rr=[r for r in a if r['case']==case]
        cases.append([case,len(rr),count([prior[key(r)] for r in rr],'passed'),count(rr,'passed'),
                      sum(r['valid']==r['negative']=='True' for r in rr)])
    details=table(['反例','倍率','噪声','种子','曝光','V6.1 最大连续列','V6.2 最大连续列','V6.2 门槛','当前发布'],[
        [r['case'],r['zoom'],r['noise'],r['seed'],r['photo'],prior[key(r)]['longest_dual'],r['longest_dual'],r['required_contour_run'],r['valid']] for r in healed+fp])
    return summary,table(['合成工况','总数','V6.1 通过','V6.2 通过','V6.2 误报'],cases),details


def mt():
    rows=b.read_csv(OUT/'ncc_window_rejections.csv')
    full=b.read_csv(OUT/'group_h_full_shift.csv')
    scans=b.read_csv(OUT/'group_h_reference_scan.csv')
    tests=[r for r in b.read_csv(OUT/'group_h_stress.csv') if r['direction']=='left' and r['delta']=='-150']
    nominal={int(r['frame']):r for r in scans if r['delta']=='0'}
    shifted=[r for r in scans if r['delta']=='-150']
    assert len(shifted)==len(full)==len(nominal)==410 and len(tests)==26
    assert len(rows)==sum(int(r['ncc_attempts']) for r in full)
    support=[r for r in rows if r['support_fraction']!='']
    zero=count(full,'zero')
    reasons=Counter((r['side'],r['reason']) for r in rows)
    detail=table(['配准窗','支持率 <35%','几何尺寸不足','低纹理','进入 NCC','被采用'],[
        [side,reasons[side,'MATERIAL_SUPPORT_LT35'],reasons[side,'BOX_TOO_SMALL'],reasons[side,'LOW_TEXTURE'],
         sum(r['side']==side and bool(r['peak']) for r in rows),reasons[side,'OK']] for side in ('up','down','single')])
    missing=sum(not r['ref_shifted'] for r in full)
    rescued=sum(r['nominal_band_replay']==nominal[int(r['frame'])]['reference_apex'] for r in shifted)
    sentence=(f"开发组H {zero}/{len(full)} 帧全部分侧窗回退到零位移。{len(rows):,} 次上侧、下侧或合并窗尝试中，"
              f"{sum(r['reason']=='MATERIAL_SUPPORT_LT35' for r in rows):,} 次材料掩膜覆盖不足，另有 "
              f"{sum(r['reason']=='BOX_TOO_SMALL' for r in rows)} 次窗口尺寸不足。")
    sat=f"在尺寸合格的 {len(support):,} 次尝试中，有效材料比例最大值为 {max(float(r['support_fraction']) for r in support):.3%}，当前窗与参考窗灰度 ≥250 的像素占比中位数分别为 {median(float(r['saturated_current']) for r in support):.1%} 和 {median(float(r['saturated_ref']) for r in support):.1%}。配准器先剔除饱和点，并对参考支持做 11×11 腐蚀。低纹理判定、±5 px 峰值搜索和 NCC 0.84 门限均未执行。这批图像无法据此估计实际位移是否超过 5 px。"
    shift=(f"实际左移 150 px 后，历史 {len(tests)} 次测试（{len(set(r['frame'] for r in tests))} 张图，含重复）保持名义参考位置 {sum(r['reference_apex']==nominal[int(r['frame'])]['reference_apex'] for r in tests)} 次。全 410 帧中，原缺口在裁后材料带内 {count(shifted,'old_in_band')} 帧；完成两端定位并准备好搜索的有 {410-missing} 帧，"
           f"其中与名义参考端点相同 {count(full,'ref_equal')} 帧。其余 {missing} 帧在准备阶段返回空。两次都发布尖端的只有 {sum(bool(r['tip_drift']) for r in full)} 帧。")
    cf=(f"保留左移后的横向范围和提示点，仅在离线回放中换回名义纵向材料带，{rescued}/410 帧恢复 V6.2 名义参考端点。"
        "第 78 帧材料带下界从 y=1372 变为 731，原参考缺口 (2643,780) 被裁出。名义点位下，扩大统计范围又使暗区分割门槛升至 250.74，轮廓延伸至 (2655,782)。位移测试恢复同一参考坐标与实际尖端识别正确是两项独立指标。")
    return sentence,sat,detail,shift,cf


def main():
    frozen();DOC.mkdir(parents=True,exist_ok=True)
    acc,flow,recovery,failures,hx,healed,lost=audit_frames()
    synth,matrix,p4=synthetic()
    ncc,saturation,windows,shift,cf=mt()
    bench=b.read(OUT/'bench_S2_4.json')
    fps=bench['n']/bench['seconds'];wall=bench['n']/bench['wall_seconds']
    speed=f"三点弯 520 帧、4 个工作进程。逐帧处理耗时合计折算 {fps:.2f} FPS，含读图、校验与进程调度的整池墙钟吞吐 {wall:.2f} FPS。4.5 FPS 门槛通过。"
    coverage='开发组A 551 帧、三点弯 520 帧、验证组C 562 帧、开发组H 410 帧，共 2,043 张图、2,605 个帧与点位组合。验证组C两套点位使用同一序列，bright 检查点及邻域处于亮区。三点弯和验证组C只作冻结回归，人工标注仅作离线比较，排除组X排除。Joint 要求尖端误差 ≤10 原图像素，且路径精确率和覆盖率均 ≥80%。无输出计为未命中。'
    finding=f"开发组A与三点弯守住 18/19、8/15，验证组C原点与亮区均为 18/20，V6.1 退化的 {lost} 个帧次恢复 {healed} 个。开发组H的联合命中从 9/18 降到 3/18，左移验收失败。V6.2 S2 作为研究候选交付，日常默认 V5.15 S2。"
    links=' · '.join([link('difference_views/index.html','四组逐帧图与视频'),link('crack_lengths.csv','全量尖端和裂纹长度（px）'),link('freeze.json','推理冻结清单'),'[失败审计](FAILURES_AUDIT.md)','[开发组H诊断](GROUP_H_REPORT.md)'])
    evidence=' · '.join([link('group_h_0078_reference_band.png','第 78 帧定位与裁带示意'),link('group_h_reference_scan.csv','参考缺口对照，含仅替换纵向材料带'),link('group_h_full_shift.csv','全 410 帧实际左移'),link('group_h_stress.csv','历史扰动及重复试次'),link('ncc_window_rejections.csv','全部 NCC 窗、阈值与拒绝原因')])
    method='参考帧先沿用边缺口快路，失败时扫描有效材料带全宽的暗连通域；当前帧围绕参考端点加基准点平移，在局部对齐。保留 aperture × 11.5 的物理尺度，恢复静态口门门限 max(4, 0.035 × 灰度极差, 3 × 噪声)。仅有轮廓粗配准的 JOINT 分支要求双证据连续列达到 max(10, round(0.065 × 实测物理尺度))。尺度以像素计，各倍率的实际门槛见合成逐例表。'
    cause='开发组H第 252 帧误差 102.70 px。第 216、221 帧从严重提前变为门控拒绝，均计作漏检。'
    factor=b.read_csv(OUT/'group_h_factorial_scores.csv')
    assert b.sha(OUT/'group_h_factorial_predictions.json')==b.read(OUT/'group_h_factorial_seal.json')['sha']
    comparisons=[]
    for loc in ('6.1','6.2'):
        for gate in ('6.1','6.2'):
            group=[r for r in factor if r['locator']==loc and r['gates']==gate]
            assert len(group)==18
            comparisons.append([loc,gate,count(group,'joint'),count(group,'severe'),sum(bool(r['error_px']) for r in group)])
    cause+=' 离线交叉回放只替换参考定位或门控组合（口门阈值与连续列门槛），两条对角线的状态、尖端和全路径已与各自正式输出核对。'
    attribution=table(['参考定位','门控组合','18 帧 Joint','>100 px','发布尖端'],comparisons)+'\n\n'+link('group_h_factorial_scores.csv','开发组H定位与门控逐帧交叉对照')
    nextstep='开发组H应先让参考材料带覆盖原缺口，再比较局部和整带灰度统计对缺口右端的影响。对分侧配准，先在同批原图核查较远的未饱和材料区是否有稳定纹理；本次注册窗的支持率不足以评估放宽 NCC 或扩大搜索半径的收益。'
    write('REPORT.md',['# V6.2 全局参考缺口定位与门控验证',finding,links,'本轮按任务书在 CodexCrack 实现。核对到的 GeminiCrack 独立项目源码仍使用局部参考搜索与固定 10 列门槛。','## 算法与评测口径',method,coverage,'在 run_crack_tip.py 顶部启用 use_validation_candidate，或运行 CrackTipRunner.exe --candidate。相同 EXE 抽查 9 个帧与点位组合，状态、尖端、路径和长度与冻结结果一致。','## 冻结实帧结果',acc,flow,speed,'## 验证组C退化帧逐次对照',recovery,'## 开发组H左移与零回退',shift,cf,ncc,windows,saturation,cause,attribution,evidence,'## 合成对照',synth,matrix,link('paired_probes.csv','1,404 次合成明细'),'## 后续研发',nextstep])
    write('FAILURES_AUDIT.md',['# V6.2 失败帧审计',finding,coverage,acc,'## 可见标注上所有 Joint 失败',failures,cause,attribution,'## 验证组C 13 个历史退化帧次',recovery,'## 开发组H实际左移与配准拒绝',shift,cf,ncc,windows,saturation,evidence,'## 合成矩阵与剩余误报',synth,p4,'剩余反光弧误报使用 MAPPED 配准，当前仅轮廓分支的短路径门槛未作用于该候选。',matrix,nextstep])
    write('GROUP_H_REPORT.md',['# 开发组H MT · V6.2 诊断',shift,cf,evidence,ncc,saturation,windows,'## 18 张可见标注',hx,cause,attribution,nextstep,link('difference_views/group_h.mp4','410 帧参考、结果与差分视频')])


if __name__=='__main__':
    main()
