"""V4.2 report built exclusively from frozen predictions and post-seal scores."""
from collections import Counter
from . import batch as b
from .reporting import *

def main():
    scores,records,metrics=collect(b);stage='v4_2'
    def explain(g,i,m,r,mode):
        d=m['diagnostics']['dual'];before=records[g,i]['models']['no_break']['full']
        return (f"移除近口截断后尖端 {coord(before['tip'])}；放行主段强增量后为 {coord(m['tip'])}。"
                f"灰度基座 {coord(d.get('base_tip'))}；主选 {d['decision']}，停止 {d.get('stop')}。尝试 {len(d.get('trials',[]))} 条增量轨，拒绝 {d.get('rejections',{})}。"
                +('下一步应检查候选是否在人工端点后转入背景。' if r['dx'] and float(r['dx'])>10 else '可检查缺口归属以及人工尖端与最后可见支持列之间的差距。'))
    failures,entries=failure_list(b,scores,records,['v3_6','v4_1'],explain)
    failures+=focus_tables(b,scores,records,['v3_6','v4_1','no_break',stage])
    pack(b,'FAILURES_AUDIT.md',failures)
    def files(p):return read_csv(p)
    final=[r for r in metrics if r['stage']==stage and r['mode']=='full']
    tests=[('V3.6',files(b.OUT/'v3_6_probes.csv')),('V4.1',files(b.BASE/'paired_probes.csv')),('① 仅移除近口截断',files(b.OUT/'no_break_probes.csv')),('② V4.2',files(b.OUT/'paired_probes.csv'))]
    current=tests[-1][1];previous=tests[1][1]
    weak=lambda rr:sum(r['case']=='P1_weak_gap' and r['passed']=='True' for r in rr)
    fp=sum(r['valid']=='True' and r['negative']=='True' for r in current)
    decisions={r['group']:r['hit']>={'group_a':19,'three_point_bend':10,'group_c':13}[r['group']] and r['joint']>={'group_a':19,'three_point_bend':10,'group_c':13}[r['group']] and not r['severe'] and (r['group']!='group_a' or r['median']<3) for r in final}
    body=['# V4.2 止血验证与消融报告',
          '；'.join(f"{NAMES[r['group']]} 联合 {r['joint']}/{r['visible']}、严重误差 {r['severe']}" for r in final)+'。',
          '完整模式彻底移除 V4.1 颈部跨唇截断。放行阶段保留近口强增量种子，并允许主段持续单极变暗、参考图缺乏相容暗谷的候选进入竞争；已证实隔着空白材料的孤立暗线、增量闭环与静态纹理仍受约束。长距离渐隐外推要求主干已经出现衰减。红色补种的联合信号与深度图按帧惰性构建并共用。①与②均包含相同的渐隐及计算清理，二者之差衡量颈部门放行效果。',
          '先运行独立合成与开发组A开发组，封存代码、参数和开发指标后依次运行三点弯、验证组C一次。验证组具有历史暴露。排除组X排除，人工标注仅作离线比较。',
          f"合成弱带通过数 V4.1 {weak(previous)}/216 → V4.2 {weak(current)}/216；阴性误报 {fp}/216，实测组达标情况 {decisions}。",
          '[完整图册、视频和每帧独立差分](difference_views/index.html) · [失败与疑难帧](FAILURES_AUDIT.md) · [冻结记录](freeze.json)']
    body+=metric_tables(b,metrics)+focus_tables(b,scores,records,['v3_6','v4_1','no_break',stage])+probe_tables(tests)
    from research.notch_identity_v36.batch import OUT as old36
    from research.notch_identity_v32.audit import signature
    speeds=[];admitted=[]
    for g in b.GROUPS:
        series=[[],[],[]];same=0;votes=Counter()
        with (old36/(g+'.jsonl')).open() as f36,(b.BASE/(g+'.jsonl')).open() as f41,(b.OUT/(g+'.jsonl')).open() as f42:
            for lines in zip(f36,f41,f42):
                recs=[json.loads(l) for l in lines]
                assert len({a['source_sha'] for a in recs})==1
                ms=[a['models'][v] for a,v in zip(recs,('v3_6','v4_1','v4_2'))]
                same+=int(signature(ms[0]['raw_only'])==signature(ms[2]['raw_only']))
                for arr,m in zip(series,ms):arr.append(m['seconds'])
                dual=ms[-1]['full']['diagnostics']['dual'];votes['body']+=sum(t['status']=='BODY_INCREMENT' for t in dual.get('trials',[]))
                votes['increment']+=int(dual['decision']=='FRONT_INCREMENT')
        assert same==b.GROUPS[g]
        speeds.append([NAMES[g],same,*[num(1/mean(t)) for t in series]])
        admitted.append([NAMES[g],votes['body'],votes['increment']])
    body+=['## 全序列对照','同源逐帧核验当前 raw_only 的状态、根点、路径和尖端与 V3.6 完全一致。按各版原运行全序列的单帧推理耗时换算如下。',table(['组','总帧','V3.6 FPS','V4.1 FPS','V4.2 FPS'],speeds),table(['组','凭主段增量通过的候选数','最终使用增量轨的帧数'],admitted),'纠正并行唇缘错接时，要求断前两个不同的局部暗谷同时有测量支持，且断后能在进入断带的切向延长线上重新找到暗谷。正常单条弯曲路径不再因缺列截断。']
    pack(b,'REPORT.md',body)
    result=dict(primary=stage,run=b.OUT.relative_to(b.ROOT).as_posix(),groups=final,accuracy_gate=decisions,negative_fp=fp,weak_pass=weak(current),severe=sum(r['severe'] for r in final))
    b.save(b.OUT/'latest_metrics.json',result);b.save(b.ROOT/'evidence'/stage/'latest_metrics.json',result)
    print(result)
if __name__=='__main__':main()
