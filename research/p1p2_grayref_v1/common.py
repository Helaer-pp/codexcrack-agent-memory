from pathlib import Path
import sys,json,csv,hashlib,os
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/python'))
from crackv4.dataset_policy import require,role
OUT=ROOT/'output/runs/p1p2_grayref_v1_20261112_r01'
BUILD=ROOT/'output/build/p1p2_grayref_v1'
FROZEN=ROOT/'paired_p1p2_roi_V1_FROZEN.py'
EXPECTED_SHA='2e2e5ebef80ab33e486c561b6dec09ee15d23033020cc1886a7de24c7ce2baf6'
DEV=['group_a','ct2','group_h','ct3'];VAL=['group_c','three_point_bend']
F=ROOT/'output/runs/uctt_r05f_20261111_r01';D=ROOT/'output/runs/uctt_r05d_20261111_r01'
LABELS=ROOT/'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip'
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as stream:
  for b in iter(lambda:stream.read(4194304),b''):h.update(b)
 return h.hexdigest()
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def save(p,rr):
 Path(p).parent.mkdir(parents=True,exist_ok=True)
 if not rr:return
 with Path(p).open('w',encoding='utf-8-sig',newline='') as stream:
  w=csv.DictWriter(stream,fieldnames=list(dict.fromkeys(k for r in rr for k in r)));w.writeheader()
  for r in rr:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict,tuple)) else v for k,v in r.items()})
