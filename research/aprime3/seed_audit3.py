from common3 import *
from native3 import engine3,seed
last=None;e=None;rr=[]
for z in jl(RUN/'03_exposed_regression/inference_inputs.jsonl'):
 if z['case_id']!=last:
  if e:e.close()
  ref=read(z['reference_image']);rp=z['reference_points'];e=engine3(ref,rp);e.run(ref,rp,True);last=z['case_id']
 a=e.run(read(z['input_image']),z['points']);prior=z['A'];q=seed(e)
 assert api.normalized(a['native'])==api.normalized(prior['native']),(last,z['frame_id'])
 assert np.asarray(a['formal']['raw_path'],dtype='<f8').tobytes()==np.asarray(prior['formal']['raw_path'],dtype='<f8').tobytes()
 reason={0:'PRE_DP_OR_NO_TRACE',1:'SEED_SUPPORT_OR_GAIN_REJECT',2:'CONTIGUOUS_SPAN_REJECT',3:'STARTUP_FRACTION_OR_PEAK_REJECT',4:'SEED_PASSED'}.get(int(q['stage']))
 rr.append(dict(case_id=last,frame_id=z['frame_id'],A_stop=a['native']['stop_reason'],formal_equal=True,**q,seed_gate=reason))
if e:e.close()
csvout(RUN/'01_diagnosis/native_seed_gates.csv',rr)
print('SEED AUDIT',len(rr),collections.Counter(r['seed_gate'] for r in rr if r['A_stop']=='no_seed'),flush=True)

