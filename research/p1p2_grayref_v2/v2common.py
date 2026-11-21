from pathlib import Path
import os,sys,json,csv,hashlib,datetime,gzip
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'config/project.json').exists())
sys.path.insert(0,str(ROOT/'src/python'))
from crackv4.dataset_policy import require,role
OUT=Path(os.environ.get('GRAYREF_V2_OUTPUT',str(ROOT/'output/experiments/p1p2_grayref_v2_20261112_r01'))).resolve()
assert OUT.is_relative_to(ROOT/'output') and str(OUT).isascii()
OLD=ROOT/'output/runs/p1p2_grayref_v1_20261112_r01'
AUDIT=ROOT/'output/diagnostics/group_c_same_bmp_root_cause_v1_20261112_r01'
FROZEN=ROOT/'paired_p1p2_roi_V1_FROZEN.py'
SHA='2e2e5ebef80ab33e486c561b6dec09ee15d23033020cc1886a7de24c7ce2baf6'
DEV=['group_a','ct2','group_h','ct3'];VAL=['group_c','three_point_bend'];COUNTS=dict(zip(DEV+VAL,[551,468,410,136,562,520]))
MODES=['V2_NUMERIC_CONTROL','V2_ORIGIN_ONLY','V2_REF_ONLY','V2_COMBINED','V2_TERMINAL']
LABELS=ROOT/'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,o):
 Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
def rows(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def save(p,data):
 assert data,str(p);Path(p).parent.mkdir(parents=True,exist_ok=True)
 with Path(p).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in data for k in r)));w.writeheader()
  for r in data:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict,tuple)) else v for k,v in r.items()})
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def packed(p,o):
 Path(p).parent.mkdir(parents=True,exist_ok=True)
 with gzip.open(p,'wt',encoding='utf8') as f:json.dump(o,f,ensure_ascii=False,allow_nan=False,separators=(',',':'))
def unpack(p):
 with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)
