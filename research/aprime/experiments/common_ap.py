from pathlib import Path
import os,sys,json,csv,hashlib,time,struct,datetime
sys.dont_write_bytecode=True
import cv2,numpy as np
S=Path(__file__).resolve().parent
ROOT=S.parents[2]
sys.path.insert(0,str(ROOT/'src/python'))
from crackv4 import frozen_a as api
from crackv4.paths import run_output
O=run_output()

sha=api.sha
def scalar(x):
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,np.generic):return x.item()
 if isinstance(x,Path):return str(x)
 raise TypeError(str(type(x)))
def write(p,t):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding='utf8')
def save(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2,default=scalar,allow_nan=False))
def rows(p):
 with Path(p).open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))
def csvout(p,rr,fields=None):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 keys=fields or list(dict.fromkeys(k for r in rr for k in r))
 if not keys:raise ValueError('Explicit columns required for empty output')
 with p.open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
  for r in rr:w.writerow({k:json.dumps(v,ensure_ascii=False,default=scalar)if isinstance(v,(list,dict,tuple,np.ndarray))else v for k,v in r.items()})
def jl(p):
 with Path(p).open(encoding='utf8')as f:
  for l in f:
   if l.strip():yield json.loads(l)
def read(p):
 x=cv2.imdecode(np.fromfile(str(p),np.uint8),cv2.IMREAD_GRAYSCALE)
 if x is None:raise RuntimeError(str(p))
 return x
def native(p):
 p=Path(p); rr=rows(p.with_suffix('.csv')); jj=list(jl(p.with_suffix('.jsonl')));pp=[]
 with p.with_suffix('.pathbin').open('rb')as f:
  for r in rr:
   n=struct.unpack('<i',f.read(4))[0];pp.append(np.frombuffer(f.read(n*16),'<f8').reshape(-1,2).copy())
 return rr,jj,pp
def guard():
 x=json.loads((ROOT/'baseline/frozen_a/identity.json').read_text(encoding='utf8'))
 for p,h in x['source_hashes'].items():assert sha(ROOT/p)==h,('FROZEN_A_CHANGED',p)
 return x

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def anchors(pp):
 pp=np.asarray(pp,float); v=pp[1]-pp[0];d=float(np.linalg.norm(v))
 if not np.isfinite(pp).all()or d<8 or v[1]<=0:raise ValueError('INVALID_ANCHOR_ORDER_OR_SPACING')
 return pp.mean(0),np.array([v[1],-v[0]])/d,d
def rigid(rp,cp):
 ro,ru,rd=anchors(rp);co,cu,cd=anchors(cp)
 # Native A uses a rigid rotation (not anchor-spacing scale).
 rv=np.array([-ru[1],ru[0]]);cv=np.array([-cu[1],cu[0]])
 R=np.column_stack([cu,cv])@np.column_stack([ru,rv]).T
 return np.column_stack([R,co-R@ro])
def apply(M,p):return np.asarray(p)@M[:,:2].T+M[:,2]
def sample(im,p):
 p=np.asarray(p,np.float32);shape=p.shape[:-1]
 return cv2.remap(im,p[...,0].reshape(1,-1),p[...,1].reshape(1,-1),cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0).reshape(shape).astype(float)
