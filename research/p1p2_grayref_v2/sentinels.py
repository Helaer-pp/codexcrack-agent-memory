from replay import *
import copy,math
def make_plan():
 a=read(AUDIT/'inputs.json');points=a['points'];seq=parse_manifest();d=next(r for r in seq if r['group']=='group_c' and r['frame_id']==237);assert d['reference_points']==points['R_S'] and d['current_points']==points['C_S'];cases=[]
 for name,rp,cp in [('A',points['R_G'],points['C_G']),('B',points['R_G'],d['current_points']),('C',d['reference_points'],points['C_G']),('D',d['reference_points'],d['current_points'])]:cases.append(dict(name=name,base=name,kind='same_BMP_ABCD',row=dict(d,reference_points=rp,current_points=cp)))
 for base in ['A','D']:
  origin=next(c['row'] for c in cases if c['name']==base)
  for side in ['reference_points','current_points']:
   for point in [0,1]:
    for axis in [0,1]:
     for delta in [-5,-2,2,5]:
      row=copy.deepcopy(origin);row[side][point][axis]+=delta;cases.append(dict(name=f'{base}_{side}_{point}_{axis}_{delta:+}',base=base,kind='single_point_xy',side=side,point=point,axis=axis,delta=delta,row=row))
  for scope in ['reference','current','both']:
   for axis in [0,1]:
    for delta in [-3,-1,1,3]:
     row=copy.deepcopy(origin)
     for side in ['reference','current']:
      if scope in [side,'both']:
       for p in row[side+'_points']:p[axis]+=delta
     cases.append(dict(name=f'{base}_{scope}_translation_{axis}_{delta:+}',base=base,kind='translation_xy',scope=scope,axis=axis,delta=delta,row=row))
 A=cases[0]['row'];D=cases[3]['row']
 for k in range(11):
  t=k/10;row=copy.deepcopy(d)
  for side in ['reference_points','current_points']:row[side]=[[A[side][i][j]*(1-t)+D[side][i][j]*t for j in [0,1]] for i in [0,1]]
  cases.append(dict(name=f'interpolation_{k:02}',base='A_to_D',kind='fixed_interpolation',t=t,row=row))
 for g,f in [('group_c',1),('group_c',7),('group_c',38),('group_c',232),('group_c',237),('group_a',504),('ct2',395),('group_h',78),('ct3',65)]:cases.append(dict(name=f'{g}_{f}',base=g,kind='predefined_sentinel',row=next(r for r in seq if r['group']==g and r['frame_id']==f)))
 return cases
def run_case(case):
 locked();cv2.setNumThreads(1);folder=OUT/'sentinels'/case['name'];v,a=execute_case(case['row'],folder)
 if case['kind'] in ['same_BMP_ABCD','predefined_sentinel'] and a is not None:np.savez_compressed(folder/'evidence.npz',**a)
 write(folder/'case.json',case);print('SENTINEL',case['name'],flush=True);return case['name']
def main():
 assert (OUT/'development_evaluation_complete.json').exists();locked();plan=make_plan();write(OUT/'perturbation_plan.json',dict(utc=utc(),parameters_from_preinference_plan=True,cases=plan,not_measured_noise_distribution=True))
 with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
  for _ in pool.map(run_case,plan):pass
 output=[];audit=[]
 for case in plan:
  data=unpack(OUT/'sentinels'/case['name']/'result.json.gz');base=unpack(OUT/'sentinels'/(case['base'] if case['base'] in ['A','D'] else 'A')/'result.json.gz')
  for v in [data['baseline']]+data['results']:
   b=next(x for x in [base['baseline']]+base['results'] if x['mode']==v['mode']);jump=math.dist(v['tip'],b['tip']) if v['tip'] and b['tip'] else None;rawjump=math.dist(v['candidate_tip'],b['candidate_tip']) if v['candidate_tip'] and b['candidate_tip'] else None
   output.append(dict(case=case['name'],base=case['base'],kind=case['kind'],mode=v['mode'],reference_points=case['row']['reference_points'],current_points=case['row']['current_points'],state=v['output_state'],tip=v['tip'],candidate_tip=v['candidate_tip'],chosen_seed=v['chosen_seed'],seed_count=v['seed_candidates_count'],public_tip_jump=jump,raw_tip_jump=rawjump,state_changed=v['output_state']!=b['output_state'],stop_reason=v['stop_reason'],observed=v['observed_path_count'],gt_accessed_at_inference=False))
   if case['name']=='D':
    for y in [2282,2351]:
     found=[s for s in v['seeds'] if s['x']==2255 and s['y']==y];audit.append(dict(case='D',mode=v['mode'],audit_coordinate_only=[2255,y],generated_raw=bool(found),candidate_records=found,chosen_seed=v['chosen_seed'],output_state=v['output_state'],tip=v['tip'],note='Coordinates queried only after inference; not detector input'))
 save(OUT/'perturbation_robustness.csv',output);save(OUT/'D_two_origins_audit.csv',audit);write(OUT/'sentinels_complete.json',dict(utc=utc(),cases=len(plan),perturbation_cases=sum(c['kind'] in ['single_point_xy','translation_xy','fixed_interpolation'] for c in plan),case_modes=len(output),passed_execution=True,labels_read=0));print('GATE4 EXECUTION COMPLETE',len(plan),flush=True)
if __name__=='__main__':main()
