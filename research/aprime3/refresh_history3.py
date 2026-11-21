"""Refresh diagnostic history only; assert every decision remains bitwise equal."""
from common3 import *
from decision3 import EndpointHistory
for rel in ['03_exposed_regression/predictions.jsonl','04_NEW_DEV/predictions.jsonl','03_exposed_regression/real_predictions.jsonl']:
 p=RUN/rel;temp=p.with_suffix('.history_tmp.jsonl');last=None;count=0;fields={}
 with temp.open('w',encoding='utf8') as out:
  for z in jl(p):
   key=z.get('case_id',z.get('group'))
   if key!=last:hist=EndpointHistory();last=key
   a=z['A']['formal'];z['history']=hist.update(np.asarray(z['A']['native']['transform_reference_to_current']),z['pool'],z['queries'],a['tip'],a['confirmed_tip'])
   for q in z['queries']:
    if 'funnel' in q['reg']:q['reg']['funnel']['NCC_attempted']=sum(p.get('ncc') is not None for p in q['reg']['patches'])
   dec=z.get('decision_result',z.get('modes',{}).get('FULL'));confirmed=dec['decision']=='RESEARCH_RELOCATED'
   z.update(research_valid=confirmed,research_tip=dec['tip'] if confirmed else None,selected_output_valid=dec['valid'],selected_output_tip=dec['tip'])
   fields[key,str(z['frame_id'])]={k:z[k] for k in ['research_valid','research_tip','selected_output_valid','selected_output_tip']}
   dump_line(out,z);count+=1
 # Same-schema streaming replacement; only this owned output file is replaced.
 temp.replace(p);print('HISTORY REFRESH',rel,count,flush=True)
 csvpath=p.parent/('real_per_frame.csv' if p.name.startswith('real_') else 'per_frame_predictions.csv')
 rr=rows(csvpath)
 for r in rr:r.update(fields[r.get('case_id',r.get('group')),r['frame_id']])
 csvout(csvpath,rr)
write(RUN/'00_protocol/implementation_corrections.md','''本轮推理后发现两个实验接线问题并修正，未改候选/参考/决策阈值：
1. 交叉消融统一使用同一 A′3 判决器，另列 AP2_LEGACY_RULE，避免候选与判决策略混淆；受控推理全量重跑。
2. 历史 proximity 日志必须要求前后两帧的局部几何和光度都有效，使用局部修正映射；不能仅当前帧有效便相信旧端点。该日志未参与尖端判决。对三份预测逐帧重算 history 字段。
3. NCC_attempted 按实际具有 NCC 值的模板数重算，不把匹配前的视野拒绝计作 NCC 运算。以上两个诊断字段刷新，尖端及判决字段不变。
4. research_valid/research_tip 专指研究确认；回退 A 的有效坐标单独写 selected_output_valid/selected_output_tip。valid 在内部决策结构中仅表示所选输出坐标有效，不等于研究确认。未改变所选坐标。
未用真实试验/GT修改算法参数。真实试验本轮均为曝光诊断，非独立验证。
''')
