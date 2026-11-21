"""Produce the V6.1 acceptance and failure reports from sealed runs."""
from collections import Counter
from pathlib import Path
from statistics import median
import os
import json
import math
from . import batch as b
from .run import frozen
from research.notch_identity_v60 import batch as previous
from research.notch_identity_v512.report import table, f
from research.v3_labelme_comparison.compare import write_csv

DOC=b.ROOT/'evidence/v6_1'
OUT=b.OUT
SETS=(('group_a','original','开发组A'),('three_point_bend','original','三点弯'),('group_c','original','验证组C原点'),('group_c','bright','验证组C亮区'),('group_h','original','开发组H MT'))

def link(p,name):
    return f"[{name}]({Path(os.path.relpath(p,DOC)).as_posix()})"

def count(rr,k):
    return sum(r.get(k)=='True' for r in rr)

def doc(name,parts):
    (DOC/name).write_text('\n\n'.join(parts)+'\n',encoding='utf8')

def main():
    frozen();DOC.mkdir(parents=True,exist_ok=True)
    lengths=[r for g in b.GROUPS for r in b.read_csv(OUT/(g+'_lengths.csv'))]
    write_csv(OUT/'crack_lengths.csv',lengths)
    accuracy=[]; failures=[]; changes=[]; totals=[]; counters={}; mt=[]; real={}
    for g,pl,name in SETS:
        path=OUT/(g+'.jsonl')
        assert b.sha(path)==b.read(OUT/(g+'_seal.json'))['predictions']
        rs=[r for r in b.read_csv(OUT/(g+'_scores.csv')) if r['state']=='VISIBLE' and r['placement']==pl]
        roster={int(r['frame']):r for r in rs}
        real[g,pl]=rs
        prev={}
        if g!='group_h':
            base_rows=[r for r in previous.read_csv(previous.OUT/(g+'_scores.csv')) if r['placement']==pl and r['state']=='VISIBLE']
            for stage in ('S1','S2'):
                old=[r for r in base_rows if r['stage']==stage]
                accuracy.append([name,'V6.0 '+stage,len(old),*[count(old,k) for k in ('hit5','hit10','joint','severe')]])
            prev={int(r['frame']):r for r in base_rows if r['stage']=='S2'}
        else:
            accuracy.append([name,'V6.0 S2',18,0,0,0,0])
        accuracy.append([name,'V6.1 S2',len(rs),*[count(rs,k) for k in ('hit5','hit10','joint','severe')]])
        c=Counter()
        for rec in map(json.loads,path.open(encoding='utf8')):
            i=rec['frame'];m=rec['placements'][pl]['S2']['full'];d=m['diagnostics']['dual']
            mode=(d.get('registration') or {}).get('status','missing')
            c['n']+=1;c['mapped']+=mode=='MAPPED';c['zero']+=mode=='ZERO_FALLBACK'
            c['prepared']+=d.get('scale') is not None;c['center']+=d.get('ref_mode')=='center'
            c['valid']+=m['tip'] is not None;c[d['stop']]+=1
            if i not in roster:continue
            row=roster[i]
            if i in prev and prev[i]['joint']!=row['joint']:
                changes.append([name,i,prev[i]['joint'],row['joint'],prev[i]['source'],row['source'],f(row['error_px'])])
            if row['joint']=='True':continue
            gt=json.loads(row['gt'])
            branches=d.get('branches',[])
            win=next((br for br in branches if d['pick']=='BRANCH_'+str(br['id'])),None)
            winner_run=(win or {}).get('curve',{}).get('longest_dual_run')
            if not row['error_px']:why='未发布尖端，'+d['stop']
            elif row['hit10']=='True':why='端点命中，路径覆盖率或精确率不足'
            elif any(br.get('tip') and math.dist(gt,br['tip'])<=10 for br in branches):why='存在近真值分支，门控或排序选中另一候选'
            else:why='全部回溯分支未命中，输出'+('越过人工尖端' if float(row['dx'])>0 else '提前终止')
            failures.append(dict(group=g,placement=pl,frame=i,error=row['error_px'],dx=row['dx'],dy=row['dy'],reason=why,route=d['decision'],registration=mode,branches=len(branches),winner_run=winner_run))
            if g=='group_h':mt.append([i,f(row['error_px']),f(row['dx']),d['decision'],len(branches),why,link(OUT/'audit_views'/f'{g}_{pl}_{i:04d}.jpg','图与得分曲线')])
        counters[g,pl]=c
        totals.append([name,c['n'],c['prepared'],c['center'],c['mapped'],c['zero'],c['valid']])
    write_csv(OUT/'failure_index.csv',failures)
    acc=table(['组','版本','可见','Hit@5','Hit@10','Joint','>100 px'],accuracy)
    flow=table(['组','帧','进入配准／DP','参考中心回退','有 NCC 支持','全窗零回退','有尖端'],totals)
    bench=b.read_csv(OUT/'bench_S2_4.csv')
    assert len(bench)==520
    fps=520/sum(float(r['seconds']) for r in bench)
    pool=520/b.read(OUT/'bench_S2_4.json')['wall_seconds']
    coords=[];stdrows=[]
    spacing=b.read_csv(OUT/'spacing.csv')
    for g in b.GROUPS:
        a=b.read_csv(OUT/(g+'_stress.csv'))
        pulls=[r for r in a if r['delta']=='-150' and r['direction']=='left']
        eligible=[r for r in pulls if r['drift']]
        std=[r for r in spacing if r['group']==g]
        tested=[r for r in std if r['tested']=='True']
        stdrows.append([g,len(std),len(tested),count(tested,'changed_status'),count(tested,'changed_path'),count(tested,'changed_route')])
        dx=[float(r['actual_dx']) for r in pulls]
        coords.append([g,len(pulls),f(min(dx))+' 至 '+f(max(dx)),len(eligible),f(max((float(r['drift']) for r in eligible),default=None)),count(pulls,'status_change')])
    bright=[r for r in b.read_csv(OUT/'bright_spacing.csv') if r['factor']!='1.0']
    stable=(f"验证组C原亮区点对请求 0.8×、1.2× 时，40 次不满足材料区范围或局部亮度要求。另用原间距的 65% 建立短点对，"
            f"向右寻找同时容纳三种间距的首个亮区位置。在这个新点位的 {len(bright)} 次合法缩放中，"
            f"状态变化 {count(bright,'changed_status')} 次，路径变化 {count(bright,'changed_path')} 次。"
            +link(OUT/'bright_spacing.csv','实际坐标'))
    probes=b.read_csv(OUT/'paired_probes.csv');assert len(probes)==1404 and b.sha(OUT/'paired_probes.csv')==b.read(OUT/'probe_seal.json')['csv']
    neg=[r for r in probes if r['negative']=='True'];assert len(neg)==468
    fp=[r for r in neg if r['valid']=='True']
    groups=sorted({r['case'] for r in probes})
    synthetic=table(['合成场景','试次','通过','负例误报'],[[k,len(a),count(a,'passed'),sum(r['negative']=='True' and r['valid']=='True' for r in a)] for k in groups for a in [[r for r in probes if r['case']==k]]])
    fptable=table(['反例','倍率','噪声','种子','曝光','路由','配准','候选最大连续双证据列'],[[r[k] for k in ('case','zoom','noise','seed','photo','track','registration','longest_dual')] for r in fp])
    route=b.read_csv(OUT/'route_replay.csv')
    factor=b.read_csv(OUT/'scale_floor.csv')
    routetable=table(['组','点位','帧','正式路由','诊断路由','正式误差 px','诊断误差 px','诊断 Joint'],[[r['group'],r['placement'],r['frame'],r['official_route'],r['diagnostic_route'],f(r['official_error']),f(r['replay_error']),r['replay_joint']] for r in route])
    fact=table(['组','点位','帧','尺度 px','门限版本','残差','门限','静态'],[[r['group'],r['placement'],r['frame'],f(r['scale']),r['floor_version'],f(r['residual']),f(r['floor']),r['quiet']] for r in factor])
    findings='开发组A 18/19、三点弯 8/15、验证组C原点 12/20、验证组C亮区 11/20。按亮区点位合计 37/54，按原点位合计 38/54，目标为 45/54。上述三组严重错误 0。开发组H单列，18 张可见标注联合命中 9 张，严重错误 2 张。候选未达替换条件，日常默认继续使用 V5.15 S2。'
    methods='开发组A与开发组H为开发回放，三点弯、验证组C只做冻结后验证。按任务书直接应用给定常数。第 1 帧固定参考，每帧独立；图像来源与逐帧基准点经过校验。人工标签只用于预测封存后的计分。验证组C两套点位复用同一批图像。Joint 要求原像素尖端误差 ≤10 px，且路径精确率、覆盖率均 ≥80%；未输出尖端计漏检。'
    geometry='原边缺口定位优先，仅在其失败时从同一窗口内筛选暗连通域，按相对提示点的纵向距离加 0.15 倍横向距离择优。后端实测开口系数为 11.5，静态门限为 max(5, 0.042×局部灰度跨度, 3.5×局部噪声)。分侧或单窗 NCC 只要有一个通过，即记录有配准支持；全部零回退时，JOINT 发布还需至少连续 10 列双证据。'
    mechanism='验证组C第 7 帧两点位的尺度从 375 变为 287.5 px，口门统计窗同步缩小。残差从 4.492 升至 5.145，仍超过新门限 5.0。只改门限、固定旧窗口才会得到预期静态判定。诊断中仅切换为既有暗线分支，两套点位均恢复至 0.845 px。另有 13 个相对 V6.0 S2 退化的验证组C点位帧次走了相反的错误路由，切回联合分支后 13/13 恢复 Joint。上述诊断输出不计入正式成绩。三点弯第 1 帧的参考与当前相同，残差为 0，最终仍因累计分不足而无尖端。'
    fpwhy='弱材料桥 36/36。P3_parallel、P3_oblique 误报均已归零。P4_open 仍有 8 次误报，全部是零回退 JOINT，候选的连续双证据列可达到 11–17。另有 1 次口门反光弧误报具有 NCC 支持，因此不触发零回退门。总误报 9/468，上轮为 18/468。'
    hx='开发组H 410/410 帧由参考中心缺口回退完成准备并进入配准和路径搜索，410 帧的材料窗均缺少通过 NCC 的局部匹配，实际均使用粗对齐的零局部位移。342 帧发布尖端，68 帧无输出。上轮有效输出为 0/410。20 张人工标注中有 18 张可见、2 张不确定。Hit@5 为 7/18，Hit@10 为 9/18，Joint 为 9/18。'
    hxaudit='第 216、221 帧分别提前 116.75、117.37 px。两帧各只有一个可回溯候选，在重选端点前已停于原图 x=2754 附近。第 78、115 帧进入既有暗线路由后无法确认；强制联合分支，第 78 帧仍因路径太短被拒，第 115 帧误差反而达 140.29 px。'
    speed=f'三点弯 520 帧单独预热四进程再全序列回放，含上游映射平均 {fps:.2f} FPS/进程，池吞吐 {pool:.2f} FPS。每进程超过 4.5 FPS 门槛。'
    stress=table(['组','−150 配对试次','实际 dx（px）','双方均有尖端','最大漂移 px','状态变化'],coords)
    stnote='左移包含重裁与重新定位，每组 20 个抽检帧，含重复共 26 个配对。开发组H 26 次左移后均无可用缺口体，无法计算尖端漂移。20 个独立测试帧的参考窗口右界均缩至 x=2603（不含），原参考顶点 x=2643 已在窗外。三点弯第 120 帧最大漂移 48.21 px。验证组C亮区实际只能移动 −17 至 −14 px，第 95 帧漂移 22.80 px。'
    mt_table=table(['帧','误差 px','横向偏差 px','路由','回溯分支数','直接失效表现','证据'],mt)
    links=' · '.join([link(OUT/'difference_views/index.html','四组逐帧图与视频'),link(OUT/'crack_lengths.csv','全部裂纹长度'),link(OUT/'freeze.json','冻结清单'),link(OUT/'paired_probes.csv','全套合成结果'),link(DOC/'FAILURES_AUDIT.md','失败审计'),link(DOC/'GROUP_H_REPORT.md','开发组H专项报告')])
    doc('REPORT.md',['# V6.1 中心缺口与零回退门控验证',findings,links,methods,geometry,'## 冻结实帧回放',acc,flow,speed,'## 未通过的验收项',mechanism,fpwhy,hx,hxaudit,'## 基准点敏感性',table(['组','请求缩放','合法测试','状态变化','路径变化','路由变化'],stdrows),stable,stress,stnote,'## 合成矩阵',synthetic,'## 后续研发建议','在开发组和合成数据上拆开检验口门测量窗与静态门限，保留固定物理窗口的对照。零回退时单凭连续列数仍可能接受开口边缘，可单独检验两侧灰度形状和切向连续性。开发组H应先解决定位窗随基准点左移而截断中心缺口的问题，再比较远端路径丢失。'])
    failtable=table(['组','点位','帧','误差 px','横向偏差 px','配准','路由','失效表现','证据'],[[r['group'],r['placement'],r['frame'],f(r['error']),f(r['dx']),r['registration'],r['route'],r['reason'],link(OUT/'audit_views'/f"{r['group']}_{r['placement']}_{r['frame']:04d}.jpg",'图与曲线')] for r in failures])
    doc('FAILURES_AUDIT.md',['# V6.1 失败帧与因果复核',findings,'## 相对 V6.0 S2 的实帧变化',table(['组','帧','旧 Joint','新 Joint','旧路由','新路由','新误差 px'],changes),'## 全部失败标注帧',failtable,'## 同像素窗口与门限对照',mechanism,fact,'## 冻结路径的路由反事实',routetable,'## 合成反例',fpwhy,fptable,stnote])
    doc('GROUP_H_REPORT.md',['# 开发组H MT · V6.1 冻结回放',hx,link(OUT/'difference_views/group_h.mp4','410 帧参考、原图、裂纹路径与差分视频')+' · '+link(OUT/'group_h_scores.csv','人工标注计分')+' · '+link(OUT/'group_h_lengths.csv','全序列尖端与长度'),methods,flow.splitlines()[0]+'\n'+flow.splitlines()[1]+'\n'+flow.splitlines()[-1],hxaudit,'## 失败标注帧',mt_table,'## 基准点与适用条件',stnote,'名义点位下的中心缺口定位成功率不能外推到实际左移 150 px 的输入。'+link(OUT/'group_h_stress.csv','实际左移、定位状态与端点明细')+' · '+link(OUT/'group_h_left_apex.csv','参考窗右界与候选坐标')])
    print(findings,speed)

if __name__=='__main__':main()
