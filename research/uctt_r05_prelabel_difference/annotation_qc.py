"""Portable package QC: run with Python + Pillow, no detector required."""
from pathlib import Path
import csv,json,hashlib,argparse,math,collections
from PIL import Image
ALLOWED={'crack_path':{'linestrip'},'crack_tip':{'point'},'interference':{'linestrip','polygon'},'uncertain_region':{'polygon'},'branch_path':{'linestrip'}}
def validate(package,initial=False):
 package=Path(package);rs=list(csv.DictReader((package/'selection_manifest.csv').open(encoding='utf-8-sig')));output=[];seen=set();groups=collections.Counter();splits=collections.Counter()
 for r in rs:
  p=package/r['selected_image'];j=package/r['selected_json'];data=json.loads(j.read_text(encoding='utf8'));assert (j.parent/data['imagePath']).resolve()==p.resolve()
  assert hashlib.sha256(p.read_bytes()).hexdigest()==r['source_sha256'];assert r['source_sha256'] not in seen;seen.add(r['source_sha256'])
  with Image.open(p) as im:im.load();w,h=im.size
  assert (w,h)==(data['imageWidth'],data['imageHeight'])==(int(r['image_width']),int(r['image_height']))
  assert isinstance(data['shapes'],list) and isinstance(data['flags'],dict)
  if initial:assert data['shapes']==[] and data['flags']=={}
  counts=collections.Counter()
  for s in data['shapes']:
   label=s['label'];typ=s['shape_type'];assert label in ALLOWED and typ in ALLOWED[label],(j,label,typ);pts=s['points'];assert len(pts)>={'point':1,'linestrip':2,'polygon':3}[typ]
   if typ=='point':assert len(pts)==1
   assert all(len(p)==2 and all(isinstance(x,(int,float)) and math.isfinite(x) for x in p) and 0<=p[0]<w and 0<=p[1]<h for p in pts)
   counts[label]+=1
  negative=data['flags'].get('no_visible_crack',False);assert isinstance(negative,bool)
  assert not(negative and any(counts[x] for x in ['crack_tip','crack_path','branch_path']))
  status='NO_VISIBLE_CRACK' if negative else 'REVIEW_REQUIRED_MULTIPLE_TIPS' if counts['crack_tip']>1 else 'ANNOTATED_VISIBLE' if counts['crack_tip']==1 and counts['crack_path'] else 'UNCERTAIN' if counts['uncertain_region'] else 'PARTIAL' if data['shapes'] else 'UNANNOTATED'
  groups[r['dataset_id']]+=1;splits[r['dataset_id'],r['split']]+=1
  output.append(dict(dataset_id=r['dataset_id'],frame_id=r['frame_id'],split=r['split'],annotation_status=status,crack_path_count=counts['crack_path'],crack_tip_count=counts['crack_tip'],interference_count=counts['interference'],uncertain_count=counts['uncertain_region'],no_visible_crack_flag=negative,reviewer='',review_note=''))
 assert all(n==20 for n in groups.values()) and all(splits[g,'development']==15 and splits[g,'holdout']==5 for g in groups)
 return output
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('package',nargs='?',default=str(Path(__file__).resolve().parent));parser.add_argument('--initial',action='store_true');a=parser.parse_args();result=validate(a.package,a.initial)
 dest=Path(a.package)/'annotation_progress.csv'
 with dest.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
 print(json.dumps(dict(files=len(result),status_counts=dict(collections.Counter(r['annotation_status'] for r in result)),QC='PASS'),ensure_ascii=False))
