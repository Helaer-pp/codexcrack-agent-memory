"""Offline evaluator only; this module is never imported by an inference runner."""
from common3 import *
def error(tip,valid,g):
 return float(np.linalg.norm(np.asarray(tip)-g['tip'])) if valid and g['observable'] else None
def execute(kind):
 folder=RUN/('03_exposed_regression' if kind=='exposed' else '04_NEW_DEV');labels={(z['case_id'],z['frame_id']):z for z in jl(folder/'evaluator_GT.jsonl')}
 rr=[];cc=[];paired=collections.defaultdict(dict);groups=collections.defaultdict(list);gfalse=[]
 for z in jl(folder/'predictions.jsonl'):
  key=z['case_id'],z['frame_id'];lab=labels[key];g=lab.get('GT',lab);a=z['A']['formal'];ae=error(a['tip'],a['confirmed_tip'],g)
  oc={}
  for name,pp in [('old',z['old_pool']),('full',z['pool']),('endpoint_only',z['endpoint_only_pool']),('multiscale_only',z['multiscale_only_pool'])]:
   e=min([float(np.linalg.norm(np.asarray(c['xy'])-g['tip'])) for c in pp],default=None) if g['observable'] else None
   oc[name+'_oracle_error']=e;oc[name+'_oracle_correct']=e is not None and e<=8
  for c in z['pool']:cc.append(dict(case_id=key[0],frame_id=key[1],candidate_id=c['candidate_id'],origin=c['origin'],xy=c['xy'],GT_error_EVALUATOR_ONLY=float(np.linalg.norm(np.asarray(c['xy'])-g['tip'])) if g['observable'] else None))
  preserved=not a['confirmed_tip'] or any(c['A_original_bitwise'] and np.array_equal(c['xy'],a['tip']) for c in z['pool']);assert preserved
  base=dict(case_id=key[0],frame_id=key[1],family=lab['family'],background=lab.get('background',lab.get('metrics',{}).get('background')),pair_id=lab.get('pair_id'),identity_pair_id=lab.get('identity_pair_id'),
     positive=g['positive'],observable=g['observable'],A_error=ae,A_correct=ae is not None and ae<=8,A_stop=z['A_stop'],
     old_K=z['old_K'],K=z['K'],old_coverage=z['old_coverage'],new_coverage=z['new_coverage'],A_original_preserved=preserved,**oc)
  for mode,d in z['modes'].items():
   e=error(d['tip'],d['valid'],g);correct=e is not None and e<=8;neg=not g['positive']
   loss=min(e,64.) if e is not None else 32. if g['observable'] else (32. if neg and d['valid'] else 0. if neg else None)
   row=dict(**base,mode=mode,valid=d['valid'],tip=d['tip'],error=e,correct=correct,FP=bool(neg and d['valid']),loss=loss,
      changed=d['tip']!=a['tip'],A_correct_changed_wrong=bool(base['A_correct'] and not correct),catastrophic=bool(base['A_correct'] and e is not None and e>160),
      decision=d['decision'],reason=d.get('reason'))
   rr.append(row);groups[mode].append(row)
   if mode=='FULL':paired[lab.get('pair_id'),key[1]][lab['family']]=row
  Mgt=np.asarray(lab['M_GT'],float)
  for j,q in enumerate(z['queries']):
   if not q['reg']['local_supported']:continue
   target=np.asarray(q['target'])+np.array([[-16,-16],[-16,16],[16,-16],[16,16]])
   refcoords=apply(cv2.invertAffineTransform(Mgt),target);errors=np.linalg.norm(apply(np.asarray(q['reg']['M']),refcoords)-target,axis=1)
   gfalse.append(dict(case_id=key[0],frame_id=key[1],query=j,max_transform_error=float(max(errors)),false_accept=bool(max(errors)>1.)))
 metrics=[]
 for mode,q in groups.items():
  metrics.append(dict(mode=mode,n=len(q),observable=sum(r['observable'] for r in q),correct=sum(r['correct'] for r in q),FP=sum(r['FP'] for r in q),
      changed=sum(r['changed'] for r in q),A_correct_changed_wrong=sum(r['A_correct_changed_wrong'] for r in q),catastrophic=sum(r['catastrophic'] for r in q),
      penalized_loss=float(np.mean([r['loss'] for r in q if r['loss'] is not None]))))
 full=groups['FULL'];activation=[]
 inputs={(z['case_id'],z['frame_id']):z for z in jl(folder/('inference_inputs.jsonl' if kind=='exposed' else 'inference_manifest.jsonl'))}
 for (pid,f),pair in paired.items():
  if not pid:continue
  x,y=pair['STRONG_FALSE_TAIL'],pair['TRUE_LONG_MATCHED'];xi=inputs[x['case_id'],f];yi=inputs[y['case_id'],f]
  same=sha(xi['input_image'])==sha(yi['input_image']) and xi['points']==yi['points'];assert same
  act=x['A_error'] is not None and x['A_error']>32 and y['A_correct']
  activation.append(dict(pair_id=pid,frame_id=f,background=x['background'],same_current_and_anchors=same,different_reference=sha(xi['reference_image'])!=sha(yi['reference_image']),activated=act,A_false_error=x['A_error'],A_long_error=y['A_error'],full_short_correct=x['correct'],full_long_correct=y['correct'],both_correct=x['correct'] and y['correct']))
 fam=[]
 for name in dict.fromkeys(r['family'] for r in full):
  q=[r for r in full if r['family']==name];fam.append(dict(family=name,n=len(q),A_correct=sum(r['A_correct'] for r in q),full_correct=sum(r['correct'] for r in q),
     old_oracle=sum(r['old_oracle_correct'] for r in q),new_oracle=sum(r['full_oracle_correct'] for r in q),endpoint_only_oracle=sum(r['endpoint_only_oracle_correct'] for r in q),multiscale_only_oracle=sum(r['multiscale_only_oracle_correct'] for r in q),FP=sum(r['FP'] for r in q),
     old_coverage=float(np.mean([r['old_coverage'] for r in q])),new_coverage=float(np.mean([r['new_coverage'] for r in q]))))
 metricsdict={m['mode']:m for m in metrics};fc=metricsdict['FULL'];ac=metricsdict['A_ONLY'];am={r['pair_id'] for r in activation if r['activated']};ab={r['background'] for r in activation if r['activated']}
 gains={r['family']:r['new_oracle']-r['old_oracle'] for r in fam}
 summary=dict(frames=len(full),observable=sum(r['observable'] for r in full),A_correct=ac['correct'],full_correct=fc['correct'],old_oracle=sum(r['old_oracle_correct'] for r in full),new_oracle=sum(r['full_oracle_correct'] for r in full),
    old_oracle_losses=sum(r['old_oracle_correct'] and not r['full_oracle_correct'] for r in full),max_K=max(r['K'] for r in full),A_original_preserved=all(r['A_original_preserved'] for r in full),
    activated_pairs=len(am),activated_pair_frames=sum(r['activated'] for r in activation),activated_backgrounds=len(ab),
    old_coverage=float(np.mean([r['old_coverage'] for r in full])),new_coverage=float(np.mean([r['new_coverage'] for r in full])),geometry_supported_queries=len(gfalse),geometry_false_accepts=sum(r['false_accept'] for r in gfalse),
    gate_A=sum(gains.values())>=5 and gains.get('STRONG_FALSE_TAIL',0)>=1 and gains.get('WEAK_FADE',0)>=1 and not any(r['old_oracle_correct'] and not r['full_oracle_correct'] for r in full),
    gate_activation=len(am)>=12 and len(ab)>=3,
    gate_C=fc['correct']>ac['correct'] and fc['penalized_loss']<ac['penalized_loss'] and fc['FP']<=ac['FP'] and fc['A_correct_changed_wrong']==0 and fc['catastrophic']==0)
 csvout(folder/'evaluated_per_frame_all_modes.csv',rr);csvout(folder/'candidate_GT_distances_EVAL_ONLY.csv',cc);csvout(folder/'ablation_metrics.csv',metrics);csvout(folder/'activation_audit.csv',activation);csvout(folder/'paired_stop_continue.csv',activation);csvout(folder/'family_metrics.csv',fam);csvout(folder/'geometry_accuracy_EVAL_ONLY.csv',gfalse)
 csvout(folder/'remaining_failures.csv',[r for r in full if r['observable'] and not r['correct']]);save(folder/'evaluation_summary.json',summary)
 print('EVALUATED',kind,summary,flush=True)
if __name__=='__main__':execute(sys.argv[1] if len(sys.argv)>1 else 'new')
