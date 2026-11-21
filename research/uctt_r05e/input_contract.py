"""Original image + deliberately invalid CURRENT anchors, no annotation reads."""
from common import *
from baseline import load,make,clean,digest
from replay import configure
import cv2,numpy as np
def main():
 cv2.setNumThreads(1);a=load(ROOT/'output/build/src/cpp/a/Release/CrackV4.dll');b=load(BUILD/'Release/B2.dll');configure(b);b.R05DCapture(0)
 seq=[r for r in filter_rows(rows(OUT/'input_inventory_allowed.csv'),'development') if r['dataset_id']=='group_a'][:2];ims=[]
 for r in seq:
  raw=Path(r['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];ims.append(cv2.imdecode(np.frombuffer(raw,np.uint8),0))
 pp=json.loads(seq[0]['points']);mode=next(g['mode'] for g in read(ROOT/'config/datasets.json')['groups'] if g['id']=='group_a');results=[]
 for invalid in [[[10,10],[10,10]],[[-1,20],[20,40]],[[float('nan'),10],[20,40]]]:
  ea=make(a,ims[0],pp,mode);eb=make(b,ims[0],pp,mode)
  try:
   ra=ea.run(ims[1],invalid,is_reference=False);rb=eb.run(ims[1],invalid,is_reference=False)
   assert digest(ra)==digest(rb);native=json.loads(b.CrackV4LastGeometryJson(eb.handle))
   # Existing ABI explicitly reports invalid-current-anchor status. It may still
   # measure a tip through its independent image registration branch.
   assert native['current_anchor_invalid'];side=json.loads(b.R05ERead(eb.handle));assert side['sidecar_output'] is None and not side['trusted_history_write']
   results.append(dict(case='degenerate' if invalid[0]==invalid[1] else 'outside' if invalid[0][0]==-1 else 'nonfinite',status='PASS',production_equal=True,current_anchor_invalid=True,sidecar_observed=False,sidecar_history_write=False,legacy_observed=rb['formal']['confirmed_tip']))
  finally:ea.close();eb.close()
 save(OUT/'tests/invalid_current_anchors.csv',results);print('INVALID CURRENT ANCHORS',len(results),'PASS')
if __name__=='__main__':main()
