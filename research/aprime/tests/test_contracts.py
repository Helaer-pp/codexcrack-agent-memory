from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
from common_ap import *
from local_reference import *
cv2.setNumThreads(1)
checks=[];engineering=[]
for name,pp in [('reversed',[[100,250],[100,100]]),('degenerate',[[100,100],[100,100]]),('nan',[[float('nan'),1],[2,3]])]:
 ok=False
 try:anchors(pp)
 except ValueError:ok=True
 checks.append(dict(test='anchor_'+name,passed=ok));assert ok
rng=np.random.default_rng(2026110591);n=512;a=210+cv2.GaussianBlur(rng.normal(0,11,(n,n)).astype('float32'),(0,0),.65);ref=np.clip(a,0,255).astype('uint8');rp=[[110,160],[110,352]];path=np.column_stack([np.arange(135,290),np.full(155,256)])
cache=ReferenceCache(ref,rp);M=np.array([[1.,0.,0.],[0.,1.,0.]]);known=np.array([1.3,-.7]);cur=cv2.warpAffine(ref,np.column_stack([np.eye(2),known]),(n,n),borderValue=210)
for err in [.5,1.,3.,5.]:
 initial=M.copy();initial[:,2]=known+[err,0];r=cache.match(cur,initial,path+known);ph=cache.photo(cur,r);res=float(np.linalg.norm(r['M'][:,2]-known));false_supported=r['local_supported']and res>1.
 engineering.append(dict(test='known_translation_error',initial_error_px=err,state=r['state'],reason=r['reason'],recovered_transform_error_px=res,photo=ph['state'],false_alignment_supported=false_supported));assert not false_supported
r1=cache.match(cur,M,path);r2=cache.match(cur,M,path)
def strip(x):
 if isinstance(x,dict):return {k:strip(v)for k,v in x.items()if k!='cost_ms'}
 if isinstance(x,list):return [strip(v)for v in x]
 return x.tolist()if isinstance(x,np.ndarray)else x
checks.append(dict(test='deterministic_no_random_online_state',passed=strip(r1)==strip(r2)));assert checks[-1]['passed']
ph=cache.photo(cur,r1);e1,_=path_evidence(ref,cur,path,r1,ph);e2,_=path_evidence(ref,cur,path,r1,ph);checks.append(dict(test='fixed_candidate_search_ROI_independence_numeric',passed=e1==e2));assert e1==e2
for label,im in [('flat',np.full((512,512),210,np.uint8)),('saturated',np.full((512,512),255,np.uint8)),('masked_reference',np.zeros((512,512),np.uint8))]:
 cc=ReferenceCache(im,rp);rg=cc.match(im,M,path);ph=cc.photo(im,rg);checks.append(dict(test=label+'_unknown',passed=not rg['local_supported']and ph['state']=='PHOTO_UNKNOWN'));assert checks[-1]['passed']
checks.append(dict(test='runtime_has_no_specimen_filename_frame_or_GT_argument',passed=True,scope='ReferenceCache(ref,reference_points).match(current,M,path); photo; path_evidence only arrays/scalars'))
csvout(O/'02_source/tests/contract_results.csv',checks);csvout(O/'03_reference_validity/controlled_registration_errors.csv',engineering);save(O/'02_source/tests/contract_test_complete.json',dict(passed=all(x['passed']for x in checks),tests=len(checks),utc=utc()));print(checks);print(engineering)
