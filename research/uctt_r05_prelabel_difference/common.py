from pathlib import Path
import csv,json,hashlib
import cv2,numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/runs/uctt_r05_prelabel_difference_20261111_r01'
PACKAGE=OUT/'R05_LabelMe_Annotation_Package'
LABELME=ROOT/'output/toolchains/labelme_5_2_1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(p):return {str(f.relative_to(ROOT)).replace('\\','/'):sha(f) for f in sorted(p.rglob('*')) if f.is_file() and '__pycache__' not in f.parts}
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def save(p,rr):
 with Path(p).open('w',encoding='utf-8-sig',newline='') as f:
  if not rr:return
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rr for k in r)));w.writeheader()
  for r in rr:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict,tuple)) else v for k,v in r.items()})
def read_image(p):
 a=cv2.imdecode(np.fromfile(str(p),np.uint8),cv2.IMREAD_GRAYSCALE)
 if a is None:raise ValueError(p)
 return a
def all_sources():
 cfg=json.loads((ROOT/'config/datasets.json').read_text(encoding='utf8'));ss=rows(ROOT/'data/inputs/six_groups_manifest.csv');out={}
 for g in cfg['groups']:
  rr=[r for r in ss if r['dataset_alias']==g['id']];assert len(rr)==g['frames']
  out[g['id']]=[dict(dataset_id=g['id'],frame_id=int(r['frame_id'])+1,frame_order=int(r['frame_id']),source_image=r['input_image'],expected_sha256=r['input_sha256'],points=json.loads(r['points']),p1p2_source=str(ROOT/r['anchor_file']),sequence_role=g['role'],mapping_source='six_groups_manifest zero-based frame_id + original num record') for r in rr]
 ct3=rows(ROOT/'output/runs/ct3_white_frozenA_20261106_r01/逐帧裂纹结果.csv')
 directory=Path('D:/datasets/1-引伸计/1-裂纹/2.裂纹扩展/白色喷漆')
 out['ct3']=[dict(dataset_id='ct3',frame_id=int(r['帧号']),frame_order=int(r['坐标num']),source_image=str(directory/r['图片名']),expected_sha256=None,points=[[float(r[f'P{k}x']),float(r[f'P{k}y'])] for k in [1,2]],p1p2_source=str(ROOT/'output/runs/ct3_white_frozenA_20261106_r01/逐帧裂纹结果.csv'),sequence_role='EXPOSED_REGRESSION',mapping_source='frozen replay CSV explicit image name + coordinate num; separate original tracking file unavailable') for r in ct3]
 return out
