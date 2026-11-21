"""Meaningful isolation tests: causal future perturbation and failed registration semantics."""
import copy,tempfile
from common import *
from select_causal_history import CausalHistory,state
from register_two_sides import context,register,metrics

def replay(stream,images,stop):
 h=CausalHistory(8);answer=[]
 for r in stream:
  t=int(r['frame_order'])
  if t>stop:break
  cc,why=h.candidates(r,2);ctx=context(images[t],r)
  for p in cc:
   result=register(images[int(p['frame_order'])],p,ctx)
   answer.append((t,int(p['frame_order']),result['valid'],result['sides'],hashlib.sha256(result['warp'].tobytes()).hexdigest(),hashlib.sha256(result['mask'].tobytes()).hexdigest()))
  assert all(int(p['frame_order'])<t for p in cc) and len(h.cache)<=8
  h.add(r)
 return answer

def main():
 cv2.setNumThreads(1);cv2.setRNGSeed(20261111);rng=np.random.default_rng(20261111)
 base=rng.integers(15,235,(240,480),dtype=np.uint8);base=cv2.GaussianBlur(base,(3,3),0);stream=[];images=[]
 for t in range(12):
  stream.append(dict(frame_order=t,p1p2_valid=True,p1_x=40+t,p1_y=60,p2_x=40+t,p2_y=180))
  images.append(cv2.warpAffine(base,np.float32([[1,0,t],[0,1,0]]),(480,240)))
 first=replay(stream,images,7);mutated=copy.deepcopy(stream);changed=[a.copy() for a in images]
 for t in range(8,12):mutated[t]['p1_x']=-999;changed[t][:]=255
 assert first==replay(mutated,changed,7)==replay(stream,images,7)
 assert any(x[2] for x in first),'positive translation control must register'
 # Missing geometry returns explicit no-valid-points. Blank material is rejected.
 h=CausalHistory();bad=dict(stream[0],p1p2_valid=False);assert h.candidates(bad)[1]=='no_valid_p1p2'
 ctx=context(np.ones_like(base)*100,stream[1]);failure=register(np.ones_like(base)*100,stream[0],ctx)
 assert not failure['valid'] and not failure['mask'].any()
 assert all(v is None for v in metrics(ctx,failure,np.ones_like(base,dtype=bool)).values())
 # Real-source prefix: altered future metadata and pixels cannot change earlier fits.
 rr=[r for r in rows(OUT/'input_inventory.csv') if r['dataset_id']=='ct3'][:4];real=[read_image(r['source_image']) for r in rr]
 a=replay(rr,real,2);rr2=copy.deepcopy(rr);rr2[3]['p1_x']='-1000';real2=real[:3]+[np.zeros_like(real[3])];assert a==replay(rr2,real2,2)
 write(OUT/'contract_tests.json',dict(T01_future_metadata_and_pixels='PASS synthetic 8 targets and CT3 first3',T05_missing_points_and_texture='PASS',T10_repeatability='PASS exact arrays and side metrics',synthetic_positive_registrations=sum(x[2] for x in first),real_comparisons=len(a)))
 print('CONTRACT TESTS PASS',len(first),len(a),flush=True)
if __name__=='__main__':main()
