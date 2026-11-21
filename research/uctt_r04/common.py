from pathlib import Path
import hashlib,json,csv,sys,ctypes as C
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/runs/uctt_r04_path_tip_20261111_r01'
BUILD=ROOT/'output/build/uctt_r04'
GEN=ROOT/'output/build/uctt_r04_source'
R03=ROOT/'output/runs/phase1_r03_dynamic_roi_20261110_r01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(p):return {str(f.relative_to(ROOT)).replace('\\','/'):sha(f) for f in sorted(p.rglob('*')) if f.is_file() and '__pycache__' not in f.parts}
def write(name,x):(OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def save(name,rs):
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
  if not rs:return
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rs for k in r)));w.writeheader()
  for r in rs:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict,tuple)) else v for k,v in r.items()})
sys.path.insert(0,str(ROOT/'src/python'));sys.path.insert(0,str(ROOT/'research/gate_adapt'))
from crackv4 import frozen_a as api
from all_groups import inventory
def lib(path):
 api.BASE=path;api.EXPECTED_BASE=sha(path);api._base=None;l=api.base_library()
 l.CrackV4LastDebugJson.argtypes=[C.c_void_p];l.CrackV4LastDebugJson.restype=C.c_char_p
 return l
def create(l,im,p,mode):api._base=l;return api.Baseline(im,p,mode=mode)
def normalized(v):
 if isinstance(v,dict):return {k:normalized(x) for k,x in v.items() if k not in ['api_ms','detector_ms']}
 if isinstance(v,list):return list(map(normalized,v))
 return v
# Preselected from R04 supplied windows, before checking new results. Prefixes
# are processed chronologically; videos contain these windows, not cherry picks.
WINDOWS={'group_a':[(232,246)],'group_c':[(30,72)],'ct2':[(1,12)],'group_h':[(1,10),(70,82)],'group_x':[(1,4)],'three_point_bend':[(1,24)],'ct3':[(1,32)]}
VARIANTS={'group_c':'p1_plus_5pct_x','ct2':'shift_x_plus_2pct','group_h':'shift_y_plus_10pct','group_x':'shift_y_plus_10pct'}
def selected(g,i):return any(a<=i<=b for a,b in WINDOWS[g])
