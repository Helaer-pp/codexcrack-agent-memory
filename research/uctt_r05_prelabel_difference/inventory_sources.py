import re,os,sys,platform,collections
from common import *
def main():
 OUT.mkdir(parents=True,exist_ok=False)
 protected={}
 for folder in ['src/cpp/a','output/runs/phase1_acceptance_r02','output/runs/phase1_r03_dynamic_roi_20261110_r01','output/runs/uctt_r04_path_tip_20261111_r01','data/anchors']:
  protected.update(tree(ROOT/folder))
 for p in ['config/project.json','config/datasets.json','data/inputs/six_groups_manifest.csv','output/build/src/cpp/a/Release/CrackV4.dll','output/releases/A_Win64_OpenCV440/bin/CrackV4.dll']:
  protected[p]=sha(ROOT/p)
 write(OUT/'frozen_manifest.json',dict(protected=protected,python=sys.version,opencv=cv2.__version__,platform=platform.platform(),labelme_version='5.2.1',labelme_isolated_path=str(LABELME),selection_seed=20261111,production_changed=False))
 inventory=[];summary=[];issues=[]
 for g,seq in all_sources().items():
  point_records={}
  if g!='ct3':
   for line in Path(seq[0]['p1p2_source']).read_text(encoding='utf8',errors='replace').splitlines():
    v=re.findall(r'[-+]?\d+(?:\.\d+)?',line)
    if len(v)==5:point_records[int(v[0])]=np.array(list(map(float,v[1:]))).reshape(2,2)
  first=seq[0]['source_image'];sizes=collections.Counter();seen=set();valid=0
  for i,r in enumerate(seq):
   assert r['frame_order']==i and r['frame_id']==i+1
   p=Path(r['source_image']);rec=dict(r,reference_image=first,source_kind='unmodified_original',exists=p.is_file(),width=None,height=None,sha256=None,decode_ok=False,notes='')
   if not p.is_file():rec['notes']='SOURCE_MISSING';inventory.append(rec);continue
   data=p.read_bytes();digest=hashlib.sha256(data).hexdigest();assert not r['expected_sha256'] or r['expected_sha256']==digest,(g,i,'hash mismatch')
   im=cv2.imdecode(np.frombuffer(data,np.uint8),0)
   if im is None:rec['notes']='DECODE_FAILED';inventory.append(rec);continue
   h,w=im.shape;pp=np.array(r['points']);ptvalid=bool(np.isfinite(pp).all() and (pp[:,0]>=0).all() and (pp[:,0]<w).all() and (pp[:,1]>=0).all() and (pp[:,1]<h).all() and np.linalg.norm(pp[1]-pp[0])>1)
   if g!='ct3':assert i in point_records and np.max(np.abs(pp-point_records[i]))<1e-6,(g,i,'point mapping')
   v=pp[1]-pp[0];small=cv2.resize(im,(128,128),interpolation=cv2.INTER_AREA);dh=cv2.resize(small,(9,8),interpolation=cv2.INTER_AREA);bits=np.packbits((dh[:,1:]>dh[:,:-1]).ravel()).tobytes().hex()
   rec.update(width=w,height=h,sha256=digest,decode_ok=True,p1p2_valid=ptvalid,p1_x=pp[0,0],p1_y=pp[0,1],p2_x=pp[1,0],p2_y=pp[1,1],opening_distance=float(np.linalg.norm(v)) if ptvalid else None,rotation_proxy=float(np.arctan2(v[1],v[0])) if ptvalid else None,texture_proxy=float(np.std(small)),saturation_proxy=float(np.mean((small<5)|(small>250))),perceptual_hash=bits,duplicate_exact=digest in seen,byte_size=len(data),notes='original point file exactly matched' if g!='ct3' else 'CT3 points from explicit frozen CSV; independent raw point source unavailable')
   seen.add(digest);sizes[w,h]+=1;valid+=1;inventory.append(rec)
   if(i+1)%100==0:print(g,i+1,'/',len(seq),flush=True)
  summary.append(dict(dataset_id=g,listed=len(seq),decoded=valid,unique_sha=len(seen),image_sizes=dict((f'{w}x{h}',n) for (w,h),n in sizes.items()),point_mapping='exact source num match' if g!='ct3' else 'frozen explicit mapping only',reference_order=0,reference_sha256=sha(first)))
  save(OUT/'input_inventory.csv',inventory);write(OUT/'inventory_summary.json',summary);print('completed',g,flush=True)
 write(OUT/'source_evidence.json',dict(known_failure_reports=[dict(path=p,sha256=sha(ROOT/p)) for p in ['output/runs/phase1_acceptance_r02/first_divergence.csv','output/runs/phase1_r03_dynamic_roi_20261110_r01/first_divergence_r03.csv','output/runs/uctt_r04_path_tip_20261111_r01/first_divergence_r04.csv','output/runs/uctt_r04_path_tip_20261111_r01/R04_results.mp4']],new_real_holdout=False))
 print(summary)
if __name__=='__main__':main()
