"""Compute stage acceptance from sealed predictions, probes and isolated block timings."""
import ast
import json
import math
import os
from pathlib import Path
from statistics import median
import numpy as np
from research.notch_identity_v512.report import table, f
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b, gate
from .run import frozen

DOC=b.ROOT/'evidence/v6_0'
OUT=b.OUT
BASE=OUT.parent/'v515_clean_fast_r02'
SETS=(('group_a','original','开发组A'),('three_point_bend','original','三点弯'),('group_c','original','验证组C原点'),('group_c','bright','验证组C亮区'))
ST=b.ALGS
def link(path,title):
    return f"[{title}]({Path(os.path.relpath(path,DOC)).as_posix()})"
def both(loc,suffix):
    return [r for g in b.GROUPS for r in b.read_csv(loc/(g+'_'+suffix+'.csv'))]
def key(r):return r['group'],r['placement'],int(r['frame'])
def visible(rows,st):return {key(r):r for r in rows if r['stage']==st and r['state']=='VISIBLE'}
def count(rows,k):return sum(r[k]=='True' for r in rows)
def by(rows,**filters):return [r for r in rows if all(r[k]==str(v) for k,v in filters.items())]
def rate(rows,field):return len(rows)/sum(float(r[field]) for r in rows)
def md(name,parts):(DOC/name).write_text('\n\n'.join(parts)+'\n',encoding='utf8')

def synthetic():
    a=b.read_csv(OUT/'paired_probes.csv')
    seal=b.read(OUT/'probe_seal.json')
    assert seal['sources']==b.sources() and seal['csv']==b.sha(OUT/'paired_probes.csv')
    stats={};summary=[];full=[]
    baseline=b.read_csv(BASE/'paired_probes.csv')
    baseline=[dict(r,stage='V5.15 S2') for r in baseline if r['stage']=='S2']
    a=baseline+a
    labels=('V5.15 S2',*ST)
    for st in labels:
        rows=by(a,stage=st); neg=by(rows,negative='True')
        assert len(rows)==1404 and len(neg)==468
        d=dict(fp=count(neg,'valid')); stats[st]=d
        for k in ('active_fork','weak_material_bridge','P4_open','mouth_glare_arc_only'):
            d[k]=count(by(rows,case=k),'passed')
        for k in ('P6_isolated','P6_deformed_scratch'):d[k]=[count(by(rows,case=k,zoom=z),'passed') for z in (.5,1.,2.)]
        summary.append([st,d['fp'],d['P4_open'],d['mouth_glare_arc_only'],d['weak_material_bridge'],d['active_fork'],*[' / '.join(map(str,d[k])) for k in ('P6_isolated','P6_deformed_scratch')]])
    for case,width,c in sorted({(r['case'],r['width'],r['contrast']) for r in a}):
        rows=by(a,case=case,width=width,contrast=c)
        full.append([case,width,c,*[' / '.join(str(count(by(rows,stage=s,zoom=z),'passed')) for z in (.5,1.,2.)) for s in labels]])
    return stats,table(['阶段','误报 /468','P4 /36','反光弧 /36','弱桥 /36','分叉 /36','P6 孤立各 /12','P6 变形各 /12'],summary),table(['场景','间断宽度','对比度',*labels],full)

def bench():
    mins={};out=[];blocks=[];modules=[]
    for st,folder,label in [('S2',BASE,'V5.15 S2')]+[(s,OUT,s) for s in ST]:
        prefix=f'bench_{st}_4'
        rows=b.read_csv(folder/(prefix+'.csv'))
        assert [int(r['frame']) for r in rows]==list(range(1,521))
        modules.append([label,*[f(np.mean([float(r[k]) for r in rows])) for k in ('upstream_ms','registration_ms','fields_ms','normal_ms','lattice_ms')]])
        parts=[rows[j:j+52] for j in range(0,520,52)]
        slow=min(rate(p,'seconds') for p in parts)
        wall=b.read(folder/(prefix+'.json'))['wall_seconds']
        if folder==OUT:mins[st]=slow
        out.append([label,f(rate(rows,'seconds')),f(rate(rows,'detector_seconds')),f(520/wall),f(slow),round(median(float(r['field_pixels']) for r in rows))])
        blocks.extend(dict(stage=label,first=p[0]['frame'],last=p[-1]['frame'],fps=rate(p,'seconds')) for p in parts)
    write_csv(OUT/'benchmark_blocks.csv',blocks)
    return mins,table(['阶段','含映射 FPS/进程','检测 FPS/进程','整池 FPS','最慢 52 帧 FPS/进程','累计证据像素中位'],out),table(['阶段','上游映射 ms','局部配准 ms','其余证据场 ms','法向证据 ms','DP ms'],modules)

def sensitivity():
    out=[];summary={}
    for g,pl,name in SETS:
        if g=='group_c' and pl=='original':continue
        data=b.read_csv(OUT/(g+'_stress.csv'))
        for st in ST:
            normal={(r['frame'],r['repeat']):r for r in by(data,stage=st,direction='left',delta=0)}
            rows=by(data,stage=st,direction='left',delta=-150)
            ratios=[];pix=[];shifts=[];drift=[]
            for r in rows:
                n=normal[r['frame'],r['repeat']]
                ratios.append(float(r['seconds'])/float(n['seconds']))
                if float(n['field_pixels']):pix.append(float(r['field_pixels'])/float(n['field_pixels']))
                shifts.append(float(r['actual_dx']))
                if r['drift']:drift.append(float(r['drift']))
            point=dict(ratio=median(ratios),max_drift=max(drift,default=0),changed=count(rows,'status_change'),min_dx=min(shifts),max_dx=max(shifts))
            summary.setdefault(st,{})[g]=point
            out.append([name,st,len(rows),f(min(shifts))+' 至 '+f(max(shifts)),f(median(pix)),f(point['ratio']),f(np.percentile(ratios,95)),f(point['max_drift']),point['changed']])
    return summary,table(['组','阶段','配对试次','实际 dx（px）','像素比中位','时间比中位','时间比 P95','最大漂移 px','状态改变'],out)


def decide():
    frozen()
    scores=both(OUT,'scores')
    stats,_,_=synthetic()
    def passed(stage):return {k for k,v in visible(scores,stage).items() if v['joint']=='True'}
    p6=lambda s:stats[s]['P6_isolated']+stats[s]['P6_deformed_scratch']
    verdict=gate.select(stats['S3']['fp'],stats['S3']['weak_material_bridge'],passed('S2'),passed('S3'),p6('S2'),p6('S3'))
    verdict.update(release=None,baseline='V5.15 S2')
    b.save(OUT/'selection.json',verdict)
    write_csv(OUT/'crack_lengths.csv',by(both(OUT,'lengths'),stage=verdict['stage']))
    return verdict

def main():
    from collections import Counter
    verdict=decide()
    chosen=verdict['stage']
    DOC.mkdir(exist_ok=True,parents=True)
    before=visible(both(BASE,'scores'),'S2')
    scores=both(OUT,'scores')
    real={s:visible(scores,s) for s in ST}
    real={'V5.15 S2':before,**real}
    assert all(set(prev)==set(before) for prev in real.values())
    summary=[]
    for g,pl,name in SETS:
        for stage,rs in real.items():
            rows=[v for k,v in rs.items() if k[:2]==(g,pl)]
            summary.append([name,stage,len(rows),*[count(rows,k) for k in ('hit10','hit5','joint','severe')],sum(not v['error_px'] for v in rows)])
    accuracy=table(['组','阶段','可见帧','Hit@10','Hit@5','Joint','Severe','无尖端'],summary)
    stats,syn,full=synthetic()
    _,timing,modules=bench()
    _,shifts=sensitivity()
    diag={}
    outcomes=[]
    bands=[]
    distributions=[]
    for g,pl,name in SETS:
        data=OUT/(g+'.jsonl')
        assert b.read(OUT/(g+'_seal.json'))['predictions']==b.sha(data)
        counts={s:[] for s in ST}
        aperture={s:[] for s in ST}
        paired={s:Counter() for s in ST}
        rates={s:[0,0,0,0] for s in ST}
        for rec in map(json.loads,data.open(encoding='utf8')):
            for s,model in rec['placements'][pl].items():
                m=model['full'];d=m['diagnostics']['dual']
                info=rec['mappings'][pl][s]
                aperture[s].append(d.get('scale'))
                if (g,pl,rec['frame']) in before:diag[g,pl,rec['frame'],s]=d
                counts[s].extend(info['windows'])
                if info['windows']:
                    for j,k in enumerate(info['before']+info['after']):rates[s][j]+=k
                if g=='group_c':
                    alt=rec['placements']['bright' if pl=='original' else 'original'][s]['full']
                    paired[s]['same_route']+=d['decision']==alt['diagnostics']['dual']['decision']
                    paired[s]['same_state']+=m['status']==alt['status']
                    if m['tip'] and alt['tip']:
                        paired[s]['both']+=1
                        paired[s]['le1']+=math.dist(m['tip'],alt['tip'])<=1
        for s in ST:
            ws=counts[s];sc=[z for z in aperture[s] if z is not None]
            if g=='group_c' and pl=='original':
                c=paired[s];outcomes.append([s,c['same_route'],c['same_state'],c['both'],c['le1']])
            got=rates[s]
            bands.append([name,s,f(min(sc)),f(median(sc)),f(max(sc)),f(1000*got[0]/max(1,got[1])),f(1000*got[2]/max(1,got[3]))])
            for k,side in [('up','上'),('down','下')]:
                modes=Counter(w[k+'_mode'] for w in ws)
                shifts_array=np.array([w[k] for w in ws])
                assert np.max(abs(shifts_array))<=5
                trusted=[w[k+'_ncc'] for w in ws if w[k+'_mode']=='side']
                assert all(v>=.84 for v in trusted)
                bounds=lambda a:'/'.join(f(v) for v in np.percentile(a,[5,50,95]))
                distributions.append([name,s,side,len(ws),modes['side'],modes['single'],modes['zero'],int(np.any(shifts_array!=0,axis=1).sum()),int(sum(w['up']!=w['down'] for w in ws)),bounds(shifts_array[:,0]),bounds(shifts_array[:,1]),f(np.mean(trusted)) if trusted else '—'])
    shift_stats=table(['组','阶段','侧','窗口','独立','单窗回退','零回退','本侧非零','上下位移不同','dx P5/50/95','dy P5/50/95','独立 NCC 均值'],distributions)
    pairtable=table(['阶段','同路由 /562','同状态 /562','双侧均有尖端','距离 ≤1 px'],outcomes)
    sctable=table(['组','阶段','尺度最小 px','中位','最大','粗对齐偶极/千对','分侧后偶极/千对'],bands)
    matches=b.read_csv(OUT/'registration_audit/matched.csv')
    targets=[]
    for g,pl,i,region in sorted({(r['group'],r['placement'],int(r['frame']),r['region']) for r in matches}):
        row=by(matches,group=g,placement=pl,frame=i,region=region)
        targets.append([g,pl,i,region,row[0]['pairs'],*[f(1000*int(a['dipoles'])/max(1,int(a['pairs']))) for a in row],link(OUT/'registration_audit'/f'{g}_{pl}_{i:04d}_{region}.png','同窗差分')])
    artifact_table=table(['组','点位','帧','区段','公共像素对','基线','S1','S2','对照图'],targets)
    common=[]
    for g,pl,name in SETS:
        if not by(matches,group=g,placement=pl):continue
        for region in ['mouth','distal']:
            rates=[]
            for method in ('V5.15 S2','V6.0 S1','V6.0 S2'):
                rr=by(matches,group=g,placement=pl,region=region,method=method)
                num=sum(int(a['dipoles']) for a in rr)
                denom=sum(int(a['pairs']) for a in rr)
                rates.append(f(1000*num/denom))
            common.append([name,region,*rates])
    common_table=table(['重点帧共用材料像素','区段','V5.15 S2','S1','S2'],common)
    focus=[];fail=[];ft=[];changes=[]
    for k,row in sorted(real[chosen].items()):
        g,pl,i=k
        d=diag[(*k,chosen)]
        if i in {'group_c':{7,38,54,335,510},'three_point_bend':{144,178,215,381,407},'group_a':{113,299,366}}[g]:
            focus.append([g,pl,i,*[f(real[s][k]['error_px']) for s in real],d['decision'],d['stop'],f(d.get('native_change')),f(d.get('route_floor')),str(d.get('proximal_replay',False))])
        for s,prev in zip(ST,['V5.15 S2','S1','S2']):
            a,z=real[prev][k],real[s][k]
            if a['joint']!=z['joint']:
                changes.append([g,pl,i,s,a['joint']+' → '+z['joint'],f(a['error_px'])+' → '+f(z['error_px']),a['source']+' → '+z['source'],z['stop']])
        if row['joint']=='True':continue
        possible=[math.dist(br['tip'],ast.literal_eval(row['gt'])) for br in d['branches'] if br.get('tip')]
        if not row['error_px']:why='未输出尖端，终止原因为 '+d['stop']
        elif row['hit10']=='True':why='尖端在 10 px 内，路径覆盖或精确率未达到 80%'
        elif min(possible,default=float('inf'))<=10:why='存在 10 px 内分支，最终门控或排序选中另一支'
        elif float(row['dx'])>0:why='回溯分支均未命中，选中尖端在标注右侧'
        else:why='回溯分支均未命中，选中尖端提前结束'
        fail.append(dict(group=g,placement=pl,frame=i,reason=why,error_px=row['error_px'],dx=row['dx'],dy=row['dy']))
        ft.append([g,pl,i,f(row['error_px']),f(row['dx']),f(row['coverage']),f(row['precision']),why,link(OUT/'audit_views'/f'{g}_{pl}_{i:04d}.jpg','原图与候选曲线')])
    write_csv(OUT/'failure_index.csv',fail)
    neg=b.read_csv(OUT/'negative_audit.csv')
    nc=Counter((v['stage'],v['case'],v['previous_stop'],v['source'],v['zero_only']) for v in neg)
    negtable=table(['阶段','反例','基线终止','新路由','全窗零回退','误报次数'],[list(k)+[v] for k,v in sorted(nc.items())])
    focus_table=table(['组','点位','帧','基线 px','S1 px','S2 px','S3 px','展示阶段路由','终止','原生残差','路由阈值','口门重算'],focus)
    change_table=table(['组','点位','帧','阶段','Joint','误差 px','路由','终止原因'],changes)
    fps={s:rate(b.read_csv(OUT/f'bench_{s}_4.csv'),'seconds') for s in ST}
    tdiff=float(np.mean([float(r['upstream_ms']) for r in b.read_csv(OUT/'bench_S1_4.csv')]))-float(np.mean([float(r['upstream_ms'])+float(r['registration_ms']) for r in b.read_csv(BASE/'bench_S2_4.csv')]))
    floors=f"S1 四进程含映射 {fps['S1']:.2f} FPS/进程，硬门 4.5、目标 6。与 V5.15 S2 历史基线的上游映射加局部配准合计相比，S1 每帧净变化 {tdiff:+.2f} ms。新映射计时包含偶极统计、重采样及回退。对照来自不同批次，不能分离机器负载造成的差异。"
    headline='，'.join(n+' '+str(count([v for k,v in real[chosen].items() if k[:2]==(g,p)],'joint'))+'/'+str(sum(k[:2]==(g,p) for k in before)) for g,p,n in SETS)
    decision=f"研究展示采用 V6.0 {chosen}。{headline}。S3 负样本误报 {stats['S3']['fp']}/468，弱材料桥 {stats['S3']['weak_material_bridge']}/36，相对 S2 丢失 {len(verdict['lost_joints'])} 个实帧 Joint。日常默认保留 V5.15 S2。"
    intro='开发组A用于开发。三点弯和验证组C按冻结代码验证，验证组C两套点位对应同一批图像。排除组X排除。人工尖端和路径只在逐组预测封存后计分。Joint 要求误差 ≤10 px 且路径覆盖率、精确率均 ≥80%。Severe 指有预测时误差 >100 px。'
    method='S1 保留 V5.15 S2 的缺口裁剪、窄走廊与证据预算。以点对中点的平移粗对齐，在实际缺口右侧分块，用缺口中线划分材料窗，中心 ±3 px 留空。每窗 NCC 仅搜索 ±5 px，材料、纹理、峰值间隔及 NCC ≥0.84 全部通过才采用。失败侧尝试跨两侧的同一材料窗，再失败则局部位移为零。中线用平滑权重合成，上下游共用同一次采样结果。'
    method2='S2 在固定参考的实体顶点后 2、4、6 px 三列测量与顶点相接的暗轮廓高度，取中位并限幅。后端用该开口换算尺度，范围 64–384 px；中线前方的原生灰度变化、短路径门槛和口门死端重算均使用这个尺度。原始点位与输入尺度仅参与粗定位，裁框和定位失败仍可能影响输出。S3 仅增加按尺度归一化的跨跳代价及反号划痕截断。'
    units='偶极计数取同列相隔 2 px、符号相反且两端绝对差均 ≥5 灰度级的材料像素对，排除裂纹中线 ±3 px。按每千有效像素对报告。该量衡量配准残差，真实开口也可能产生相反符号。'
    links=' · '.join(link(OUT/p,n) for p,n in [('difference_views/index.html','全部逐帧图与视频'),('crack_lengths.csv','尖端与裂纹长度'),('registration_audit/matched.csv','同窗差分统计'),('paired_probes.csv','全部合成观测'),('freeze.json','冻结清单'),('selection.json','S3 准入')])
    findings=(
        'S1 的三点弯 Joint 从 8/15 升至 9/15，验证组C两套点位均达到 19/20。开发组A全部材料窗回退至零局部位移，'
        '三点弯共有 527 个分块的上下位移不同。S1 同时替换了旧映射和下游配准，准确率变化不能全部归因于分侧位移。'
        'S2 让验证组C 7 两套点位走相同的 JOINT 分支，但两处都失去尖端。S1 在两处走既有暗线分支，误差均为 0.84 px。'
        '三点弯 144 在 S2 恢复路径，端点误差 29.17 px。S3 在三点弯 306 保留了 3.49 px 的端点误差，但路径未过 Joint。')
    fpwhy=('S2/S3 的 18 个负样本误报来自 P4_open 11 次、P3_parallel 4 次和 P3_oblique 3 次。'
           '这些反例全部在上、下材料窗均回退零位移时进入 JOINT 并输出尖端。'
           '优先排查失去可靠配准后联合证据的准入，以及从原生缺口变化切换路由时的短路径判定。')
    rr=b.read_csv(OUT/'spacing.csv')
    rt=b.read_csv(OUT/'native_vertices.csv')
    pairs=[(a,z) for a,z in zip(rt[::2],rt[1::2]) if a['route_mismatch']=='True']
    origins=sum(a['fixed_vertex']!=z['fixed_vertex'] for a,z in pairs)
    cur=sum(a['current_vertex']!=z['current_vertex'] for a,z in pairs)
    same_scale=sum(a['scale']==z['scale'] for a,z in pairs)
    coupling=(f"固定裁框和点对中点，将开发组A、三点弯的 P1/P2 间距缩至 0.8 倍或增至 1.2 倍，"
              f"{len(rr)} 次比对中有 {count(rr,'changed_path')} 次路径变化、{count(rr,'changed_route')} 次路由变化。"
              f"验证组C真实更换点位后，{len(pairs)} 帧 S2 路由不同，其中 {same_scale} 帧的后端尺度相同，"
              f"{origins} 帧出现固定参考轮廓顶点坐标变化，{cur} 帧当前轮廓顶点也发生变化。"
              "第 7 帧两侧的后端尺度均为 375 px，灰度残差均为 4.49，高于门限 4.00，因而都进入 JOINT。"
              "左移检查中，验证组C亮区第 469 帧实际移动 −14.5 px，尖端漂移 10.0 px。"
              +link(OUT/'spacing.csv','固定裁框间距对照')+' · '+link(OUT/'native_vertices.csv','参考与当前顶点坐标'))
    reproduce=("在项目根目录通过 Python 的 `-m research.notch_identity_v60.<模块>` 运行。"
               "先执行 `run seal`，再用 `run predict <组名>` 推理三组，每组封存后 `score` 离线评分。"
               "`run probes` 运行合成矩阵，`run bench <阶段> 4` 分别回放 520 帧。"
               "依次完成 `stress`、`spacing`、`registration_check`、`negative_audit`、`route_audit`、`artifacts`、`report select`，"
               "最后运行 `difference_views`、`audit_views`、`report`、`public_check` 与 `verify`。"
               +link(b.ROOT/'research/notch_identity_v60/terminal.py','检测源码'))
    md('REPORT.md',['# V6.0 分侧配准与物理尺度验证',decision,findings,fpwhy,intro,links,'## 逐阶段实帧结果',accuracy,'## 配准与缺口尺度',method,method2,shift_stats,units,sctable,common_table,'三点弯五个重点帧的口门偶极密度下降最明显。验证组C亮区重点帧的口门同样下降，远段略升。完整性和尖端精度仍须单独核验。','已知位移图上，上侧 (+3, −2)、下侧 (−4, +1) 均被独立找回。纯平坦图回退到零，单侧平坦时使用单窗或零回退。'+link(OUT/'registration_check.json','逐窗记录'),'## 四进程三点弯 520 帧',floors,timing,modules,'各阶段单独启动四个进程并预热，同一 520 帧全量重放。每进程速度按帧数除以计算耗时之和；整池速度包含读盘、调度和校验。','## 点位与左移敏感性',pairtable,shifts,coupling,'左移压力测试逐次重裁和配准。验证组C使用亮区投影后的实际 dx。状态改变与双侧有预测时的尖端漂移分别统计。','## 重点帧',focus_table,'## 合成矩阵',syn,'三个倍率依次为 0.5、1、2，每格各 12 次。',full,'## 失败与差分复核',link(DOC/'FAILURES_AUDIT.md','逐帧失败原因、同像素差分图及阶段得失'),'## 复现',reproduce])
    md('FAILURES_AUDIT.md',['# V6.0 失败帧与分侧配准复核',decision,findings,fpwhy,'## 与 V5.15 S2 的实帧对照',accuracy,'## 逐阶段 Joint 得失',change_table,'## 逐帧失败原因',table(['组','点位','帧','误差 px','横向偏差 px','覆盖率','精确率','直接观察','证据'],ft),'## 指定帧残差',units+' 下表三阶段均取相同原图矩形、相同有效材料像素。mouth 为缺口前 80 px，distal 为随后最多 400 px。图册中的参考位置使用同一映射反算。',artifact_table,'## 验证组C点位及口门路由',focus_table,pairtable,coupling,'## 合成负样本归因',negtable,'各误报与相同输入的 V5.15 S2 成对复算。全窗零回退表示仅剩粗对齐，联合分支仍可能接受口门或既有暗线。该对照定位到失效的门控路径；它不能单独证明某一位移引发了误报。'+link(OUT/'negative_audit.csv','每次误报的候选证据')])
    print(decision)

if __name__=='__main__':
    import sys
    if sys.argv[1:]==['select']:print(decide())
    else:main()
