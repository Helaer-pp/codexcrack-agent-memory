from replay import *
import subprocess
from crackv4.dataset_policy import allowed

def main():
 n=Native();pp=[[100,150],[100,350]];results=[]
 def check(name,passed,detail):results.append(dict(test=name,status='PASS' if passed else 'FAIL',detail=detail))
 def content(r):return [(c['xy'],c['source'],c['canonical_id']) for c in r['candidates']]
 im=np.full((512,768),180,np.uint8);cv2.line(im,(100,250),(600,250),60,3)
 for w in [1,3,7,13]:
  for slope in [0,.12,-.12]:
   for blur in [0,1.2]:
    test=np.full_like(im,180);end=(600,int(250+slope*500));cv2.line(test,(100,250),end,80,w)
    if blur:test=cv2.GaussianBlur(test,(7,7),blur)
    h=n.create(test,pp);r=n.process(h,test,pp,True);n.close(h)
    dist=min([np.linalg.norm(np.array(c['xy'])-end) for c in r['candidates']] or [9999])
    check(f'current_line_w{w}_slope{slope}_blur{blur}',dist<10,dict(nearest=dist,count=len(r['candidates']),ms=r['api_ms']))
 h=n.create(im,pp);r=n.process(h,im,pp,True)
 h2=n.create(np.zeros_like(im),pp);r2=n.process(h2,im,pp,True)
 check('reference_pixels_cannot_gate_current',content(r)==content(r2),'identical current image; reference textured line versus all zeros')
 r3=n.process(h,im,pp,True);check('repeat_frame_no_history_effect',content(r)==content(r3) and not r3['trusted_history_written'],'same raw candidates with frame counter advanced')
 for name,p in [('swapped',pp[::-1]),('degenerate',[[100,250],[100,251]]),('nan',[[float('nan'),100],[100,300]]),('outside',[[-1,10],[100,300]])]:
  rr=n.process(h,im,p);check('invalid_'+name,not rr['valid_anchors'] and rr['search_incomplete'] and not rr['observed'] and rr['trusted_path_size']==0,'invalid geometry gives null fallback')
 check('null_handle',n.lib.R05FProcess(None,C.byref(image(im)),points(pp))==-1,'explicit error')
 rc=n.lib.R05FProcess(h,None,points(pp));rr=json.loads(n.lib.R05FRead(h));check('invalid_image_clears_stale',rc==-2 and not rr['observed'] and not rr['candidates'],'does not retain earlier valid evidence')
 n.close(h);n.close(h2)
 check('policy_excluded',not allowed('group_x','development') and not allowed('group_x','validation'),'no excluded image opens')
 check('validation_not_development',all(not allowed(g,'development') for g in VAL),'group-level policy')
 seed=ROOT/'output/runs/phase1_r03_dynamic_roi_20261110_r01/fault_seed.txt'
 p=subprocess.run([str(BUILD/'Release/R03Original.exe'),str(seed)],capture_output=True,text=True)
 (OUT/'tests/r03_original.csv').write_text(p.stdout,encoding='utf8')
 check('original_r03_reproduction',p.returncode==2 and rows(OUT/'tests/r03_original.csv')==rows(seed.with_name('fault_injection_results.csv')),'original coherent_wrong_first_lock still FAIL; this check only verifies faithful reproduction')
 save(OUT/'tests/S1_contracts.csv',results)
 print('contracts',len(results),'PASS',sum(r['status']=='PASS' for r in results),'FAIL',sum(r['status']=='FAIL' for r in results),flush=True)
 for r in results:
  if r['status']=='FAIL':print(r)
if __name__=='__main__':main()
