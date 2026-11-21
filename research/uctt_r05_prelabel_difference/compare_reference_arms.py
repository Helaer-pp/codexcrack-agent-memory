"""Research only: paired original-image difference experiment; never predicts a tip."""
import time,functools,html,collections
from PIL import Image,ImageDraw,ImageFont
from common import *
from select_causal_history import CausalHistory,RULES,score,state
from register_two_sides import context,register,metrics
cv2.setNumThreads(1);cv2.setRNGSeed(20261111)

@functools.lru_cache(maxsize=8)
def cached_image(path):return read_image(path)

def load(row):
 start=time.perf_counter();im=cached_image(row['source_image']);return im,(time.perf_counter()-start)*1000

def panel(ctx,results,title,normalized=False):
 canvas=Image.new('RGB',(1600,980),'#17212b');draw=ImageDraw.Draw(canvas);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
 draw.text((20,12),title,fill='white',font=font);draw.text((20,45),'DIAGNOSTICS ONLY / NO HUMAN GT / fixed absolute-difference display scale: 0..80 gray levels',fill='#ffe197',font=small)
 items=[('E0 CURRENT / same current ROI',ctx['current'],None)]
 e1,e2=results.get('E1_FIXED_REF'),results.get('E2_MATCHED_HISTORY')
 paired_mask=e1['mask']&e2['mask'] if e1 and e2 and e1['valid'] and e2['valid'] else None
 for arm in ['E1_FIXED_REF','E2_MATCHED_HISTORY']:
  r=results.get(arm);items.append((arm+' aligned' if r else arm+' NOT AVAILABLE',r['warp'] if r else None,r))
 overlay=cv2.cvtColor(ctx['current'],cv2.COLOR_GRAY2RGB);overlay[ctx['transition']]=[160,50,160];items.append(('Transition band excluded (magenta)',overlay,None))
 for arm in ['E1_FIXED_REF','E2_MATCHED_HISTORY']:
  r=results.get(arm)
  if r is None:items.append((arm+' difference unavailable',None,None));continue
  signed=ctx['current'].astype(float)-r['warp']
  if normalized:
   for i,s in enumerate(r['sides']):
    if s.get('normalization_offset') is not None:signed[ctx['sides'][i]]-=s['normalization_offset']
  diff=np.clip(abs(signed)*255/80,0,255).astype(np.uint8);diff=cv2.cvtColor(diff,cv2.COLOR_GRAY2RGB);diff[~(paired_mask if paired_mask is not None else r['mask'])]=[80,55,80]
  items.append((arm+' diff | '+('COMMON MASK' if paired_mask is not None else 'UNPAIRED' if r['valid'] else 'REJECTED'),diff,r))
 for i,(label,a,r) in enumerate(items):
  x=20+(i%3)*525;y=90+(i//3)*430;draw.text((x,y),label,fill='white',font=small)
  if a is not None:
   im=Image.fromarray(a);im.thumbnail((510,320));canvas.paste(im,(x,y+32))
  else:draw.text((x+20,y+120),'N/A - no eligible causal reference',fill='#ff9999',font=small)
  if r:
   txt=' | '.join(f"{s['side']}: {s['reason'] or 'valid'}" for s in r['sides']);draw.text((x,y+360),txt[:65],fill='#b7cad8',font=small)
 draw.text((20,945),'No growth phase or physical tip inferred. Masked / failed pixels are excluded, never scored as zero residual.',fill='#ffe197',font=small)
 return canvas

def main():
 diag=OUT/'diagnostics';diag.mkdir(exist_ok=False);inv=rows(OUT/'input_inventory.csv');selected=rows(PACKAGE/'selection_manifest.csv');targets={(r['dataset_id'],int(r['frame_order'])) for r in selected}
 # Fixed first eight-frame window in each stream, predeclared before image fits.
 groups=collections.defaultdict(list)
 for r in inv:groups[r['dataset_id']].append(r)
 for g in groups:targets.update((g,t) for t in range(8))
 write(OUT/'global_rules.json',dict(**RULES,targets='140 annotation frames plus fixed orders 0..7 in each stream',static_regions='geometric outer-fit and withheld near-side strips; unverified material stability',photometric_normalization='clipped +/-20 median offset on fit strip; diagnostic only, primary raw residual',future_tip_metrics='AWAITING_MANUAL_ANNOTATION'))
 comparisons=[];selections=[];candidate_logs=[];case_logs=[];sens=[];gallery=[]
 for g,stream in groups.items():
  history=CausalHistory(RULES['history_capacity']);alternate={cap:CausalHistory(cap) for cap in [32,128]};fixed=stream[0];previous=None;cached_image.cache_clear()
  for current in stream:
   t=int(current['frame_order']);is_target=(g,t) in targets
   if not is_target:
    history.add(current)
    for h in alternate.values():h.add(current)
    previous=current;continue
   tic=time.perf_counter();candidates,why=history.candidates(current,RULES['candidate_budget']);retrieval_ms=(time.perf_counter()-tic)*1000
   for cap,hist in alternate.items():
    alt,_=hist.candidates(current,RULES['candidate_budget']);sens.append(dict(dataset_id=g,target_frame=current['frame_id'],capacity=cap,candidate_frames=[r['frame_id'] for r in alt],opening_best_frame=alt[0]['frame_id'] if alt else None,only_metadata=True))
   image,io_ms=load(current);ctx=context(image,current)
   if ctx is None:raise ValueError('Current ROI unavailable: '+g+' '+str(t))
   evaluated={};rs={};refrows={};reg_ms=0.
   def evaluate(past):
    nonlocal io_ms,reg_ms
    h=int(past['frame_order']);assert h<t
    if h not in evaluated:
     im,elapsed=load(past);io_ms+=elapsed;result=register(im,past,ctx);reg_ms+=result['ms'];evaluated[h]=result
    return evaluated[h]
   if t>0:rs['E1_FIXED_REF']=evaluate(fixed);refrows['E1_FIXED_REF']=fixed
   valid=[]
   for past in candidates:
    result=evaluate(past);q=float(np.mean([s['p95'] for s in result['sides']])) if result['valid'] else None
    fit_quality=float(np.mean([s['fit_ecc'] for s in result['sides']])) if result['valid'] else None
    selection_score=score(current,past)+.2*(1-fit_quality) if fit_quality is not None else None
    candidate_logs.append(dict(dataset_id=g,target_frame=current['frame_id'],candidate_frame=past['frame_id'],candidate_order=past['frame_order'],opening_score=score(current,past),quality_p95=q,selection_score=selection_score,registration_valid=result['valid'],reason=result['reason'],sides=result['sides']))
    if result['valid']:valid.append((selection_score,-int(past['frame_order']),past,result))
   if valid:
    _,_,best,result=min(valid,key=lambda a:(a[0],a[1]));rs['E2_MATCHED_HISTORY']=result;refrows['E2_MATCHED_HISTORY']=best
   elif candidates:why='poor_registration_all_candidates'
   if previous is not None:rs['C0_NEAREST_PAST']=evaluate(previous);refrows['C0_NEAREST_PAST']=previous
   if candidates:rs['C1_OPENING_ONLY']=evaluate(candidates[0]);refrows['C1_OPENING_ONLY']=candidates[0]
   for arm in ['E1_FIXED_REF','E2_MATCHED_HISTORY','C0_NEAREST_PAST','C1_OPENING_ONLY']:
    r=rs.get(arm);p=refrows.get(arm);a=state(current);b=state(p) if p else None
    selections.append(dict(dataset_id=g,target_frame=current['frame_id'],target_order=t,reference_type=arm,selected_frame=p['frame_id'] if p else None,selected_order=int(p['frame_order']) if p else None,causal_ok=p is None or int(p['frame_order'])<t,D_target=a['D'],D_selected=b['D'] if b else None,delta_D=abs(a['D']-b['D']) if b else None,delta_theta=abs(np.arctan2(np.sin(a['theta']-b['theta']),np.cos(a['theta']-b['theta']))) if b else None,p1p2_valid=True,candidate_count=len(candidates) if arm in ['E2_MATCHED_HISTORY','C1_OPENING_ONLY'] else int(p is not None),selection_score=score(current,p) if p else None,registration_valid_top=r['sides'][0]['valid'] if r and r['sides'] else None,registration_valid_bottom=r['sides'][1]['valid'] if r and r['sides'] else None,registration_quality=[s.get('p95') for s in r['sides']] if r else None,selection_reason='opening+rotation shortlist; heldout image registration gate' if arm=='E2_MATCHED_HISTORY' else arm,fallback_reason=why if p is None else r['reason']))
   e1,e2=rs.get('E1_FIXED_REF'),rs.get('E2_MATCHED_HISTORY');common=np.zeros_like(ctx['current'],bool)
   if e1 and e2 and e1['valid'] and e2['valid']:common=e1['mask']&e2['mask']
   # Ancillary arms use the exact E1/E2 common mask intersected with their valid areas;
   # separately store a four-arm common mask for fair C0/C1 ablations.
   ablation=common.copy()
   for arm in ['C0_NEAREST_PAST','C1_OPENING_ONLY']:
    r=rs.get(arm);ablation&=r['mask'] if r and r['valid'] else False
   case=f'{g}__frame_{t+1:06d}';arrays=dict(current=ctx['current'],common_mask=common,ablation_common_mask=ablation,holdout_mask=ctx['holdout'],candidate_mask=ctx['candidate'],transition_mask=ctx['transition'],roi=np.array(ctx['roi']),scale=np.array(ctx['scale']))
   for arm in ['E0_CURRENT_ONLY','E1_FIXED_REF','E2_MATCHED_HISTORY','C0_NEAREST_PAST','C1_OPENING_ONLY']:
    r=rs.get(arm);p=refrows.get(arm);begin=time.perf_counter();m=metrics(ctx,r,common if arm in ['E1_FIXED_REF','E2_MATCHED_HISTORY'] else ablation);ab=metrics(ctx,r,ablation)
    comparisons.append(dict(dataset_id=g,target_frame=t+1,arm=arm,reference_frame=int(p['frame_id']) if p else None,roi_original=ctx['roi'],resolution=list(ctx['current'].shape[::-1]),common_valid_pixel_count=int(common.sum()),valid_pixel_ratio=float(common.mean()),own_valid_pixel_ratio=float(r['mask'].mean()) if r else None,intersection_loss_ratio=float(r['mask'].mean()-common.mean()) if r else None,registration_valid_top=r['sides'][0]['valid'] if r and r['sides'] else None,registration_valid_bottom=r['sides'][1]['valid'] if r and r['sides'] else None,**m,ablation_common_pixel_count=int(ablation.sum()),ablation_static_p95=ab['static_residual_p95'],opening_delta=abs(state(current)['D']-state(p)['D']) if p else None,history_age=t-int(p['frame_order']) if p else None,registration_ms=r['ms'] if r else None,difference_ms=(time.perf_counter()-begin)*1000,quality_status='CURRENT_ONLY_NO_DIFFERENCE' if arm=='E0_CURRENT_ONLY' else 'VALID_PAIRED' if r and r['valid'] and common.any() else 'EXCLUDED',exclusion_reason='' if r and r['valid'] and common.any() else (r['reason'] or 'no_common_valid_pair') if r else why or 'no_prior_candidate',source_hash=current['sha256']))
    if r:
     arrays[arm+'_warp']=r['warp'];arrays[arm+'_valid_mask']=r['mask'];arrays[arm+'_signed_difference']=ctx['current'].astype(np.int16)-r['warp'].astype(np.int16)
     norm=arrays[arm+'_signed_difference'].astype(float)
     for i,s in enumerate(r['sides']):
      if s.get('normalization_offset') is not None:norm[ctx['sides'][i]]-=s['normalization_offset']
     arrays[arm+'_normalized_difference']=norm.astype(np.float32)
   np.savez_compressed(diag/(case+'.npz'),**arrays)
   panel(ctx,rs,f'{g} | frame {t+1} | fixed=1 | history={refrows.get("E2_MATCHED_HISTORY",{}).get("frame_id","N/A")} | ROI {ctx["roi"]}').save(diag/(case+'.jpg'),quality=88)
   panel(ctx,rs,f'{g} | frame {t+1} | FIT-STRIP OFFSET NORMALIZED / diagnostic only',normalized=True).save(diag/(case+'_normalized.jpg'),quality=85)
   case_logs.append(dict(dataset_id=g,target_frame=t+1,annotation_selected=(g,t) in {(x['dataset_id'],int(x['frame_order'])) for x in selected},roi=ctx['roi'],scale=ctx['scale'],history_cache_entries=len(history.cache),candidate_count=len(candidates),image_io_ms=io_ms,history_retrieval_ms=retrieval_ms,registration_total_ms=reg_ms,arms={arm:dict(valid=r['valid'],reason=r['reason'],sides=r['sides']) for arm,r in rs.items()}))
   gallery.append(f'<section><h2>{g} / frame {t+1}</h2><a href="diagnostics/{case}.npz">原始数值、掩膜与 warp</a> | <a href="diagnostics/{case}_normalized.jpg">有限亮度归一化后（仅诊断）</a><img loading="lazy" src="diagnostics/{case}.jpg"></section>')
   history.add(current)
   for h in alternate.values():h.add(current)
   previous=current
   print(g,t+1,'E1',e1['valid'] if e1 else None,'E2',e2 is not None,'common',int(common.sum()),flush=True)
  save(OUT/'history_reference_selection.csv',selections);save(OUT/'history_candidate_log.csv',candidate_logs);save(OUT/'difference_comparison.csv',comparisons);save(OUT/'history_capacity_sensitivity.csv',sens);write(OUT/'case_registration_details.json',case_logs)
 (OUT/'R05_Reference_Difference_Comparison.html').write_text('<!doctype html><meta charset="utf-8"><title>R05 difference diagnostics</title><style>body{font:16px system-ui;background:#e7edf0;margin:24px}section{background:white;padding:16px;margin-bottom:24px}img{width:100%;max-width:1600px}</style><h1>固定参考 / 严格因果历史参考差分</h1><p>诊断图，不是人工真值。灰度显示统一 0–80；紫色表示排除区域。配准失败和没有历史为 N/A，不能计零残差。所有尺寸与 ROI 见逐帧记录，差分在统一缩放 ROI 计算。</p>'+''.join(gallery),encoding='utf8')
 print('COMPARE COMPLETE',len(case_logs),flush=True)

if __name__=='__main__':main()
