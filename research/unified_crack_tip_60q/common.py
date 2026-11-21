import csv,gzip,hashlib,json,os,sys
from pathlib import Path
from datetime import datetime,timezone
import cv2,numpy as np

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(__file__).resolve().parent
GROUPS={'group_a':551,'three_point_bend':520,'group_c':562}
ROLES={'group_a':'DEV','three_point_bend':'DEV','group_c':'LOCKED'}
VISIBLE={'group_a':19,'three_point_bend':15,'group_c':20}
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def get(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def clean(v):
    if isinstance(v,np.ndarray):return clean(v.tolist())
    if isinstance(v,np.generic):return clean(v.item())
    if isinstance(v,float) and not np.isfinite(v):return None
    if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [clean(x) for x in v]
    return v
def put(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    b=json.dumps(clean(v),ensure_ascii=False,indent=2,allow_nan=False).encode('utf-8')
    if p.exists():assert p.read_bytes()==b,'Refuse overwrite: '+str(p)
    else:p.write_bytes(b)
def write(p,text):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    b=text.encode('utf-8')
    if p.exists():assert p.read_bytes()==b,'Refuse overwrite: '+str(p)
    else:p.write_bytes(b)
def putgz(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    b=gzip.compress(json.dumps(clean(v),ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8'),compresslevel=1,mtime=0)
    if p.exists():assert p.read_bytes()==b
    else:p.write_bytes(b)
def readgz(p):return json.loads(gzip.decompress(Path(p).read_bytes()))
def rows(p):
    with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def csvwrite(p,rs):
    import io
    rs=list(rs);keys=list(dict.fromkeys(k for r in rs for k in r));s=io.StringIO(newline='')
    w=csv.DictWriter(s,fieldnames=keys);w.writeheader();w.writerows(clean(rs));write(p,s.getvalue())
def imread(p):
    image=cv2.imdecode(np.frombuffer(Path(p).read_bytes(),np.uint8),cv2.IMREAD_UNCHANGED)
    if image is None or image.ndim!=2 or image.dtype!=np.uint8:raise ValueError('Expected original uint8 grayscale BMP: '+str(p))
    return image
def parse_points(p):
    import re
    result={}
    for line in Path(p).read_bytes().decode('gb18030',errors='replace').splitlines():
        nums=re.findall(r'[-+]?\d+(?:\.\d+)?',line)
        if len(nums)==5 and line.lower().lstrip().startswith('num'):
            k=int(nums[0]);v=list(map(float,nums[1:]));assert k not in result;result[k]=[v[:2],v[2:]]
    return result
def source_hashes():
    return {str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sorted(SOURCE.rglob('*')) if p.is_file() and p.suffix in ['.py','.json','.yaml','.md','.ps1','.js','.cjs','.html']}
def check_freeze(run):
    f=get(Path(run)/'manifests/prevalidation_freeze.json')
    assert f['source']==source_hashes(),'Frozen implementation changed'
    for key,rel in [('execution_backend','manifests/DEV_execution_backend_registration.json'),('DEV_seal','manifests/DEV_inference_seal.json'),('DEV_evidence','manifests/DEV_evidence_seal.json'),('DEV_viewer','galleries/DEV_identity_audit_seal.json'),('environment','manifests/environment.json'),('dependencies','manifests/dependency_versions.json'),('video_toolchain','manifests/video_toolchain.json'),('protocol','manifests/task_protocol.json'),('development_metrics','offline_evaluation/DEV_metrics.csv'),('protocol_deviation','manifests/protocol_deviation_legacy_project_check.json')]:
        assert sha(Path(run)/rel)==f[key],'Frozen protocol/dependency artifact changed: '+rel
    return f
def inventory(run,split=None):
    r=rows(Path(run)/'manifests/input_inventory.csv')
    assert {g:sum(x['group']==g for x in r) for g in GROUPS}==GROUPS
    return r if split is None else [x for x in r if x['role']==split.upper()]
def framedir(run,row):return Path(run)/'evidence'/row['group']/row['frame_id']
