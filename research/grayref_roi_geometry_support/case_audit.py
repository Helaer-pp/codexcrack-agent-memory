"""Post-freeze descriptive GROUP_A cases. No detector execution or parameter changes."""
import argparse,collections,json
import numpy as np
from grayref_roi_geometry_ablation.common import *
from grayref_roi_geometry_ablation.geometry import MODES

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);run=Path(p.parse_args().run);assert (run/'evaluation_complete_group_a.json').exists();check_sources(run)
    seal=get(run/'frozen_group_a.json')
    for rel,h in seal['files'].items():assert sha(run/rel)==h
    metrics=rows(run/'offline_evaluation_group_a.csv');pool=rows(run/'candidate_pool_group_a.csv');lookup={(r['frame_id'],r['mode']):r for r in metrics}
    ids=sorted({r['frame_id'] for r in metrics if r['visibility']=='VISIBLE' and (r['hit10']=='True' or (r['mode']==MODES[0] and r['any_candidate_path_good']=='True'))},key=int);records=[];survival=[]
    for fid in ids:
        d=run/'frames/group_a'/fid;r=readgz(d/'result.json.gz');g=r['roi']
        with np.load(d/'evidence_arrays.npz') as q:
            nodes={mode:{(int(x)+g['xa'],int(y)+g['ya']) for x,y,*_ in q[mode+'__nodes']} for mode in MODES}
            segs={mode:{(int(x),int(y)):int(k) for k,x,y in q[mode+'__segments']} for mode in MODES}
            for mode,pred,s in zip(MODES,r['results'],r['stats']):
                pp=pred['paths'][0] if pred['paths'] else None;stops=[s for s in pp['stop_candidates'] if s['eligible']] if pp else [];m=lookup[fid,mode]
                records.append(dict(frame_id=fid,mode=mode,public_tip=pred['tip'],error=m['error'],public_state=pred['output_state'],pool_good=m['any_candidate_path_good'],selected_score=pp['score'] if pp else None,selected_trace_points=len(pp['selected_trace']) if pp else 0,observed=s['observed'],inferred=s['inferred'],last_observed=pred['last_observed_pixel'],nodes=s['nodes'],A_nodes_inside=s['A_nodes_inside'],A_nodes_retained=s['A_nodes_retained'],promoted_nodes=s['newly_retained_nodes'],containment=s['containment_deleted'],unvisited_budget=s['path_budget_not_visited'],eligible_stops=stops))
            ranks=[int(v['rank']) for v in pool if v['frame_id']==fid and v['mode']==MODES[0] and v['path_good']=='True']
            for rank in ranks:
                tr=r['results'][0]['paths'][rank]['observed_trace'];obs=[(int(x),int(y)) for x,y,hit in tr if hit]
                for mode in MODES[1:]:
                    mask=q[mode];inside=[bool(mask[y-g['ya'],x-g['xa']]) for x,y in obs];lost=[pt for pt in obs if pt not in nodes[mode]];splits=[]
                    for pa,pb in zip(obs,obs[1:]):
                        if pb[0]-pa[0]==1 and segs[MODES[0]].get(pa)==segs[MODES[0]].get(pb) and pa in nodes[mode] and pb in nodes[mode] and segs[mode][pa]!=segs[mode][pb]:splits.append([pa,pb])
                    survival.append(dict(frame_id=fid,A_good_path_rank=rank,mode=mode,observed_nodes=len(obs),outside_search=sum(not x for x in inside),missing_retained_nodes=len(lost),old_adjacent_fragment_links_split=len(splits),first_split=splits[0] if splits else None,first_missing=lost[0] if lost else None,offline_path_good_only=True))
    out=run/'case_audit';out.mkdir(exist_ok=True);csvwrite(out/'cases.csv',records);csvwrite(out/'A_good_path_survival.csv',survival)
    def table(rs,keys):return '| '+' | '.join(keys)+' |\n| '+' | '.join('---' for _ in keys)+' |\n'+''.join('| '+' | '.join(str(r.get(k,'')) for k in keys)+' |\n' for r in rs)
    md='# GROUP_A 锁后案例复核\n\n仅描述封存结果；案例按“新增公开命中或A原合格路径”事后选取，不用于调参，不是独立验证。\n\n'+table(records,['frame_id','mode','public_tip','error','public_state','pool_good','selected_trace_points','observed','inferred','nodes','promoted_nodes','containment','unvisited_budget'])
    md+='\n## 原A合格路径的节点与片段存活\n\n'+table(survival,list(survival[0]))+'\n节点都在新ROI且仍被保留，不保证原片段链接或动态规划路线保持不变。紧缩mask可以释放每列预算并引入其他已存在的局部峰，改变一对一邻接匹配；这是ROI操作通过冻结图构建器产生的效应，不是本轮修改了图规则。上表只证明实际节点/片段的首次变化，不能把所有路线损失归结为这一因素。\n\n'
    md+='GROUP_A451的B原生尖端(1356,1161)误差约0.983px，停止后负证据20/24，通过原0.8门；A/C停在较早路径且后方仍有支持。GROUP_A113在B/C失去原合格路径，说明新增一张成功同时伴有候选保真退化，不能只报告1/19的收益。完整状态和损失纳入预先冻结判定。\n\n'
    md+='计时说明：A/B/C固定执行顺序且共享缓存，存在并发和内存热身影响；shared_geometry_controller_ms还含边界诊断及封装开销，不能称纯走廊内核成本。速度表不替代目标硬件实时验收。\n'
    write_bytes(out/'GROUP_A_CASE_FINDINGS.md',md.encode('utf-8'));put(out/'seal.json',dict(utc=utc(),script_sha=sha(__file__),source_freeze_sha=sha(run/'source_hashes.json'),no_inference_change=True,posthoc_descriptive_only=True,files={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='seal.json'}));print(json.dumps(survival,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
