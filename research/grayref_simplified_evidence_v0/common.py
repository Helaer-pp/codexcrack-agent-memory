import csv,gzip,hashlib,json,os
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import cv2
ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/'output/experiments/p1p2_grayref_v2_20261112_r01'
GROUPS={'group_a':551,'ct2':468,'group_h':410,'ct3':136,'group_c':562,'three_point_bend':520}
DEV={'group_a','ct2','group_h','ct3'}
def utc():return datetime.now(timezone.utc).isoformat()
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
def json_bytes(obj):return (json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
def write_bytes(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data:raise RuntimeError(f'Refusing overwrite: {path}')
        return
    tmp=path.with_name(path.name+'.partial');tmp.write_bytes(data);os.replace(tmp,path)
def put(path,obj):write_bytes(path,json_bytes(obj))
def get(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def readgz(path):return json.loads(gzip.decompress(Path(path).read_bytes()))
def putgz(path,obj):write_bytes(path,gzip.compress(json_bytes(obj),compresslevel=6,mtime=0))
def rows(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def csvwrite(path,data):
    import io
    data=list(data)
    if not data:raise ValueError('Empty table')
    fields=list(dict.fromkeys(k for row in data for k in row));s=io.StringIO(newline='');w=csv.DictWriter(s,fields);w.writeheader();w.writerows(data);write_bytes(path,s.getvalue().encode('utf-8-sig'))
def imread(path):
    image=cv2.imdecode(np.fromfile(path,np.uint8),cv2.IMREAD_GRAYSCALE)
    if image is None:raise ValueError(f'Cannot decode {path}')
    return image
def save_npz(path,**values):
    if Path(path).exists():return
    import io
    b=io.BytesIO();np.savez_compressed(b,**values);write_bytes(path,b.getvalue())
def frame_dir(run,row):return Path(run)/'galleries'/row['group']/str(row['frame_id'])
def safe_manifest(path):
    data=rows(path);policy=get(ROOT/'config/dataset_usage_policy.json')['groups']
    if set(r['group'] for r in data)!=set(GROUPS):raise ValueError('Unexpected/excluded dataset')
    for g,n in GROUPS.items():
        subset=[r for r in data if r['group']==g]
        if len(subset)!=n or len({r['frame_id'] for r in subset})!=n:raise ValueError('Frame count/identity mismatch')
        if policy[g]!=('DEVELOPMENT' if g in DEV else 'VALIDATION_ONLY'):raise ValueError('Dataset policy changed')
    return data
