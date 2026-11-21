from pathlib import Path
import sys,json,csv,hashlib,os
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/python'))
from crackv4.dataset_policy import require,filter_rows,role,POLICY_PATH
OUT=ROOT/'output/runs/uctt_r05h_20261112_r01'
BUILD=ROOT/'output/build/uctt_r05h'
F=ROOT/'output/runs/uctt_r05f_20261111_r01'
D=ROOT/'output/runs/uctt_r05d_20261111_r01'
LABELS=ROOT/'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip'
DEV=['group_a','ct2','group_h','ct3'];VAL=['group_c','three_point_bend']
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as stream:
  for b in iter(lambda:stream.read(4194304),b''):h.update(b)
 return h.hexdigest()
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def save(p,rr):
 if not rr:return
 with Path(p).open('w',encoding='utf-8-sig',newline='') as stream:
  w=csv.DictWriter(stream,fieldnames=list(dict.fromkeys(k for r in rr for k in r)));w.writeheader()
  for r in rr:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict,tuple)) else v for k,v in r.items()})
def stable(v):
 if isinstance(v,dict):return {k:stable(x) for k,x in v.items() if not k.endswith('_ms') and k not in ['frame','frame_id','io_decode_hash_ms','source_sha256','variant','dataset_id','call_wall_ms','debug_export_ms']}
 if isinstance(v,list):return [stable(x) for x in v]
 return v

G=ROOT/'output/runs/uctt_r05g_20261112_r01'
ALL=DEV+VAL
