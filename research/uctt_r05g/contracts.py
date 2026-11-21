"""Synthetic pressure tests. Truth lives here only, never in the native tracker."""
from native import *
import cv2,numpy as np,subprocess

def main():
 cv2.setNumThreads(1);n=Native();rr=[];pp=[[100,150],[100,350]]
 def call(name,im,seed=None,anchors=pp,variant=1,reference=None):
  h=n.create(im if reference is None else reference)
  try:t=n.process(h,im,anchors,variant,2) if seed is None else n.diagnostic(h,im,anchors,seed,variant,2)
  finally:n.close(h)
  write(OUT/'tests'/f'{name}.json',t);return t
 def record(name,t,expect,passed,kind='contract'):
  rr.append(dict(test=name,kind=kind,expected=expect,passed=bool(passed),proposed_observed=t['proposed_observed'],observed=t['observed'],tracking_tip=t['tracking_tip'],reason=t['reason'],incomplete=t['search_incomplete'],scans=t['scanline_count'],max_beam=t['max_active_beam'],weak=t['weak_observations'],reacquisitions=t['gap_reacquisitions'],history_written=t['trusted_history_written'],ms=t['time_total_native_ms']))
 for gap in [0,12,24,40]:
  im=np.full((512,768),180,np.uint8);cv2.line(im,(110,250),(330,250),65,2);cv2.line(im,(331+gap,250),(600,250),65,2)
  for variant,tag in [(0,'greedy'),(1,'beam'),(2,'no_gap')]:
   name=f'gap{gap}_{tag}';t=call(name,im,[140,250,1,0],variant=variant);err=float(np.linalg.norm(np.array(t['tracking_tip'])-[600,250])) if t['tracking_tip'] else None
   record(name,t,'reaches visible distal end <10px' if variant!=2 or gap==0 else 'ablation stops before gap',err is not None and (err<10 if variant!=2 or gap==0 else t['tracking_tip'][0]<350))
 for pixels in [2,3]:
  im=np.full((512,768),180,np.uint8);cv2.line(im,(110,250),(330,250),65,2);im[249:252,343:343+pixels]=171;cv2.line(im,(360,250),(600,250),65,2)
  t=call(f'weak_fragment_{pixels}',im,[140,250,1,0]);weak=[c for s in t['scans'] for c in s['candidates'] if c['weak'] and 341<=c['xy'][0]<=348 and abs(c['xy'][1]-250)<4]
  record(f'weak_fragment_{pixels}',t,'weak short fragment read and retained as candidate, no standalone confirmation',len(weak)>0 and not t['observed'])
 blank=np.full((512,768),180,np.uint8)
 for name,im in [('constant_gray',blank),('low_texture',np.tile(np.linspace(177,183,768).astype(np.uint8),(512,1))),('reflection_shadow',blank.copy())]:
  if name=='reflection_shadow':im[:,300:330]=230;im[:,420:460]=130
  t=call(name,im);record(name,t,'no autonomous visible endpoint',not t['proposed_observed'] and not t['observed'])
 t=call('seed_only_no_darkline',blank,[140,250,1,0]);record('seed_only_no_darkline',t,'manual seed is not current observation; null tracking_tip',t['tracking_tip'] is None)
 scratch=blank.copy();cv2.line(scratch,(110,250),(600,250),65,2)
 t=call('coherent_wrong_first_lock',scratch);record('coherent_wrong_first_lock',t,'reject geometric proposal for known pre-existing scratch',not t['proposed_observed'],'identity_safety')
 t=call('reference_preexisting_scratch',scratch,reference=scratch);record('reference_preexisting_scratch',t,'reference resolves existing scratch identity',False,'NOT_IMPLEMENTED_reference')
 for name,variant in [('parallel_scratch_beam',1),('parallel_scratch_greedy',0)]:
  im=blank.copy();cv2.line(im,(110,250),(420,250),110,2);cv2.line(im,(270,256),(650,256),55,2);t=call(name,im,[140,250,1,0],variant=variant)
  record(name,t,'remain on synthetic main line ending420,250',t['tracking_tip'] is not None and np.linalg.norm(np.array(t['tracking_tip'])-[420,250])<10,'tracking_safety')
 curved=blank.copy();pts=np.array([[x,int(250+.00022*(x-110)**2)] for x in range(110,601)],np.int32);cv2.polylines(curved,[pts],False,65,2);t=call('curved',curved,[140,250,1,0]);record('curved',t,'follow visible curve',t['tracking_tip'] is not None and np.linalg.norm(np.array(t['tracking_tip'])-pts[-1])<10)
 # Independent upper/lower material motions perturb the reference only; no reference use is claimed.
 ref=scratch.copy();ref[:250]=np.roll(ref[:250],8,axis=1);ref[250:]=np.roll(ref[250:],-7,axis=1);t=call('two_sided_reference_displacement',scratch,reference=ref);record('two_sided_reference_displacement',t,'reference disabled; no claimed motion/identity validation',t['reference_attempts']==0,'reference_off_control')
 for name,ap in [('reversed_anchors',pp[::-1]),('degenerate_anchors',[[100,150],[100,150]]),('out_of_bounds',[[100,-2],[100,350]]),('nonfinite_anchors',[[float('nan'),150],[100,350]])]:
  t=call(name,scratch,anchors=ap);record(name,t,'invalid geometry, no tip/history',not t['valid_geometry'] and t['tip'] is None and not t['trusted_history_written'])
 t=call('resolution_changed',scratch,reference=np.full((256,384),180,np.uint8));record('resolution_changed',t,'explicit reset required, no state reuse',not t['valid_geometry'])
 boundary=blank.copy();cv2.line(boundary,(110,250),(767,250),65,2);t=call('crop_boundary',boundary,[140,250,1,0]);record('crop_boundary',t,'boundary is not supported terminal',not t['proposed_observed'] and all(not e['terminal_supported'] for e in t['ends']))
 h=n.create(scratch)
 try:
  first=n.process(h,scratch,pp,1,2);again=n.process(h,scratch,pp,1,2);record('repeat_frame',again,'same non-timing current evidence',stable(first)==stable(again))
  closed=n.process(h,blank,pp,1,2);record('closure',closed,'no previous endpoint observed or written',closed['tracking_tip'] is None and not closed['observed'])
  jumped=blank.copy();cv2.line(jumped,(110,250),(700,300),65,2);t=n.process(h,jumped,pp,1,2);record('dropped_frame_large_jump',t,'no trusted-history propagation',not t['trusted_history_written'])
  rc=n.lib.R05GProcessAuto(h,None,points(pp),1,2);t=n.result(h,0);record('invalid_api_clears_stale',t,'error and null current result',rc==-2 and t['tracking_tip'] is None and not t['valid_geometry'])
 finally:n.close(h)
 save(OUT/'tests/synthetic_matrix.csv',rr)
 old=ROOT/'output/runs/phase1_r03_dynamic_roi_20261110_r01/fault_seed.txt';r=subprocess.run([str(BUILD/'Release/R03Original.exe'),str(old)],capture_output=True,text=True);(OUT/'tests/R03_original_fault_matrix.csv').write_text(r.stdout,encoding='utf8')
 write(OUT/'tests/safety_summary.json',dict(synthetic_cases=len(rr),passed=sum(r['passed'] for r in rr),failed=[r['test'] for r in rr if not r['passed']],R03_exit=r.returncode,G3='FAIL',history='disabled by missing independent identity, NOT evidence of safety success',real_no_visible_crack_FPR='N/A;4 UNCERTAIN are not negatives'))
 print(read(OUT/'tests/safety_summary.json'),flush=True)
if __name__=='__main__':main()
