"""Additional frozen-build contracts; no parameter changes or annotation reads."""
from native import *
import cv2,numpy as np
def main():
 n=Native();pp=[[70.,130.],[70.,230.]];rng=np.random.default_rng(83);ref=np.clip(rng.normal(185,12,(360,640)),120,230).astype(np.uint8);cv2.fillPoly(ref,[np.array([[55,166],[90,166],[115,180],[90,194],[55,194]],np.int32)],20);im=ref.copy();cv2.line(im,(114,180),(350,180),65,1,cv2.LINE_AA);checks=[]
 def run(reference,current,points=pp):
  h=n.create(reference,pp);r=n.process(h,current,points);n.close(h);return r
 same=run(im,im);new=sum(q['reference']['classification']=='NEW' for q in same['alternative_stops']);checks.append(dict(test='identical_reference_not_new',passed=new==0,new_votes=new))
 shift=np.array([[1.,0,4],[0,1,3]]);shifted=cv2.warpAffine(im,shift,(640,360),borderValue=185);moved=run(ref,shifted,[[74,133],[74,233]]);err=float(np.linalg.norm(np.array(moved['working_tip'])-[354,183])) if moved['working_tip'] else 999;checks.append(dict(test='material_translation',passed=err<=5,error=err,status=moved['status']))
 bad=run(ref,im[:-1]);checks.append(dict(test='image_size_mismatch',passed=not bad['observed'] and not bad['search_complete']))
 a=run(ref,im);b=run(ref,im);checks.append(dict(test='fresh_handle_repeat',passed=a['status']==b['status'] and a['working_tip']==b['working_tip']))
 # Indistinguishable morphology deliberately challenges the physical-notch heuristic:
 # the harness declares this coherent notch-attached line to be a scratch. Runtime has no semantic hint.
 ambiguous=run(im,im);checks.append(dict(test='coherent_notch_attached_distractor',passed=not ambiguous['observed'] and not ambiguous['history_written'],status=ambiguous['status'],history_written=ambiguous['history_written'],evidence='synthetic semantic-negative stress; same pixels can represent crack or scratch'))
 # Near-border continuation must not acquire a boundary endpoint.
 boundary=ref.copy();cv2.line(boundary,(114,180),(639,180),65,1);r=run(ref,boundary);checks.append(dict(test='image_boundary_not_tip',passed=not r['observed'],status=r['status'],reason=r['reason']))
 save(OUT/'tests/frozen_safety_checks.csv',checks);write(OUT/'tests/frozen_safety_detail.json',dict(checks=checks,translation=moved,ambiguous=ambiguous,boundary=r));print(checks,flush=True)
if __name__=='__main__':main()
