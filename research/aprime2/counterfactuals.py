from common import *
from reference import MaterialCache,query_intervals
from decision import validated_decision

v3='--prefilter' in sys.argv
folder=RUN/('05_DEV/full_v3' if v3 else '05_DEV/full_v2');pairs={};out=[]
for z in jl(folder/'decision_predictions.jsonl'):
    if z['pair_id']:pairs[z['case_id'],z['frame_id']]=z
for (case,fid),z in pairs.items():
    other=case.replace('STRONG_FALSE_TAIL','TRUE_LONG_MATCHED') if 'STRONG_FALSE_TAIL' in case else case.replace('TRUE_LONG_MATCHED','STRONG_FALSE_TAIL')
    zz=pairs[other,fid];assert z['image_sha']==zz['image_sha']
    cur=read(z['input_image']);a=z['A']['formal'];M=np.array(z['A']['native']['transform_reference_to_current']);ref=read(z['reference_image'])
    variants=[('REFERENCE_SWAP',read(zz['reference_image'])),('REMOVE_EVERY_FIFTH_MATERIAL_BLOCK',ref)]
    for name,r in variants:
        cache=MaterialCache(r,z['reference_points'],prefilter=v3)
        if name.startswith('REMOVE'):cache.features=[f for i,f in enumerate(cache.features) if i%5!=0]
        q,ev,st=query_intervals(cache,cur,M,a['raw_path'],z['pool'],a['width_px'])
        dec,_,_=validated_decision(r,cur,a['raw_path'],z['pool'],q,ev,a['tip'],a['confirmed_tip'],a['width_px'])
        out.append(dict(case_id=case,frame_id=fid,control=name,fixed_A_path_candidates=True,
            nominal_decision=z['Aprime2']['decision'],control_decision=dec['decision'],
            nominal_tip=z['Aprime2']['tip'],control_tip=dec['tip'],same_tip=z['Aprime2']['tip']==dec['tip'],coverage=st['coverage']))
    masked=[dict(e,O=False,ownership_state='INSUFFICIENT_EVIDENCE') for e in z['path_evidence']]
    dec,_,_=validated_decision(ref,cur,a['raw_path'],z['pool'],[],masked,a['tip'],a['confirmed_tip'],a['width_px'])
    out.append(dict(case_id=case,frame_id=fid,control='REFERENCE_EVIDENCE_MASKED',fixed_A_path_candidates=True,
        nominal_decision=z['Aprime2']['decision'],control_decision=dec['decision'],nominal_tip=z['Aprime2']['tip'],control_tip=dec['tip'],same_tip=z['Aprime2']['tip']==dec['tip'],coverage=0.))
csvout(folder/'reference_counterfactuals.csv',out)
save(folder/'counterfactual_summary.json',dict(rows=len(out),effects={k:sum(x['control']==k and not x['same_tip'] for x in out) for k in set(x['control'] for x in out)},
    ROI_fixed_window='No ROI parameter in evidence/decision; candidate audit windows remain explicit and fixed. Not counted as rerun experiment.',
    ROI_search_rerun='NOT_EXECUTED: frozen public ABI has no independent ROI override; Gate B failed before advancing full Gate C validation.'))
print('COUNTERFACTUALS',len(out),flush=True)
