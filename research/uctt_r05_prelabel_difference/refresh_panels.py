"""Re-render saved arrays, without reselecting references or modifying numeric results."""
from common import *
from compare_reference_arms import panel
def main():
 cases=json.loads((OUT/'case_registration_details.json').read_text(encoding='utf8'));refs=rows(OUT/'history_reference_selection.csv')
 for c in cases:
  case=f"{c['dataset_id']}__frame_{c['target_frame']:06d}"
  with np.load(OUT/'diagnostics'/(case+'.npz')) as z:
   transition=z['transition_mask'];yy=np.indices(transition.shape)[0];mid=float(np.mean(yy[transition]));ctx=dict(current=z['current'],transition=transition,sides=[(yy<mid)&~transition,(yy>mid)&~transition]);rs={a:dict(**r,warp=z[a+'_warp'],mask=z[a+'_valid_mask']) for a,r in c['arms'].items()}
   ref=next(r for r in refs if r['dataset_id']==c['dataset_id'] and int(r['target_frame'])==c['target_frame'] and r['reference_type']=='E2_MATCHED_HISTORY')
   panel(ctx,rs,f"{c['dataset_id']} | frame {c['target_frame']} | fixed=1 | history={ref['selected_frame'] or 'N/A'} | ROI {c['roi']}").save(OUT/'diagnostics'/(case+'.jpg'),quality=88)
   panel(ctx,rs,f"{c['dataset_id']} | frame {c['target_frame']} | FIT-STRIP OFFSET NORMALIZED / diagnostic only",normalized=True).save(OUT/'diagnostics'/(case+'_normalized.jpg'),quality=85)
 print('PANELS COMMON MASK VERIFIED',len(cases))
if __name__=='__main__':main()
