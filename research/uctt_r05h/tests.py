from native import *
import cv2,numpy as np
def main():
 (OUT/'tests').mkdir(exist_ok=True);n=Native();pp=[[70.,130.],[70.,230.]];rng=np.random.default_rng(20261112)
 base=np.clip(rng.normal(185,12,(360,640)),120,230).astype(np.uint8);flat=np.full_like(base,185)
 def scene(background,notch=True,end=350,gap=0,old=False,weak=0):
  im=background.copy()
  if notch:cv2.fillPoly(im,[np.array([[55,166],[90,166],[115,180],[90,194],[55,194]],np.int32)],20)
  cv2.line(im,(114 if notch else 145,180),(end,180),155 if weak else 65,1,cv2.LINE_AA)
  if gap:im[176:185,220:220+gap]=background[176:185,220:220+gap]
  return im
 cases=[]
 for name,ref,cur,expected in [
  ('continuous',scene(base,end=114),scene(base),'positive'),
  ('preexisting_true_crack',scene(base),scene(base),'positive'),
  ('reference_low_texture',flat,scene(flat),'positive'),
  ('coherent_wrong_first_lock',scene(base,False),scene(base,False),'negative'),
  ('reference_preexisting_scratch',scene(base,False,end=500),scene(base,False,end=500),'negative'),
  ('blank',flat,flat,'negative'),
 ]+[(f'gap_{gap}',scene(base,end=114),scene(base,gap=gap),'positive') for gap in [12,24,40]]:
  h=n.create(ref,pp);r=n.process(h,cur,pp);n.close(h);err=float(np.linalg.norm(np.array(r['working_tip'])-[350,180])) if r['working_tip'] else None
  passed=(not r['observed'] and not r['history_written']) if expected=='negative' else bool(r['observed'] and err is not None and err<=5)
  cases.append(dict(test=name,expected=expected,status=r['status'],error=err,passed=passed,history_written=r['history_written'],reason=r['reason']));write(OUT/'tests'/f'{name}.json',r)
 # Explicit two/three-column terminal fragments; coverage and selected endpoint reported separately.
 for width in [2,3]:
  im=scene(flat,end=320);im[180,340:340+width]=155;h=n.create(flat,pp);r=n.process(h,im,pp);n.close(h)
  distances=[np.linalg.norm(np.array(p['xy'])-[340,180]) for p in r['main_path'] if p['visible']];hit=min(distances,default=999)<=3
  cases.append(dict(test=f'weak_{width}_column',expected='weak_visible_fragment_preserved',status=r['status'],error=None,passed=bool(hit),history_written=r['history_written'],reason=r['reason']));write(OUT/'tests'/f'weak_{width}.json',r)
 # A parallel old scratch must not replace the notch-connected current line.
 ref=scene(base,end=114);cv2.line(ref,(145,196),(570,196),35,2);im=scene(base);cv2.line(im,(145,196),(570,196),35,2)
 h=n.create(ref,pp);r=n.process(h,im,pp);n.close(h);err=float(np.linalg.norm(np.array(r['working_tip'])-[350,180])) if r['working_tip'] else 999
 cases.append(dict(test='parallel_scratch_beam',expected='correct_or_unconfirmed',status=r['status'],error=err,passed=bool(err<=5 or not r['observed']),history_written=r['history_written'],reason=r['reason']));write(OUT/'tests/parallel_scratch_beam.json',r)
 h=n.create(scene(base,end=114),pp);states=[]
 for end in [350,270,360]:states.append(n.process(h,scene(base,end=end),pp))
 n.close(h);tips=[x['working_tip'] for x in states];passed=all(tips) and tips[1][0]<tips[0][0]-40
 cases.append(dict(test='closure_reopening',expected='current_tip_can_retreat',status=states[-1]['status'],passed=bool(passed),history_written=states[-1]['history_written']));write(OUT/'tests/closure.json',states)
 h=n.create(flat,pp);bad=n.process(h,flat,[pp[0],pp[0]]);n.close(h);cases.append(dict(test='invalid_geometry',passed=not bad['observed'] and not bad['search_complete']))
 save(OUT/'tests/synthetic_matrix.csv',cases);print(json.dumps(cases,indent=2),flush=True)
if __name__=='__main__':main()
