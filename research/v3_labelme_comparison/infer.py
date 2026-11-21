"""Fresh inference on the selected originals. No LabelMe import or annotation access."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from research.unified_crack_tip_60q.common import clean
from research.unified_crack_tip_60q.config import CONFIG
from research.unified_crack_tip_60q.features import scene_geometry, register_reference, ordered_points
from research.notch_identity_v3 import terminal
from research.notch_identity_v3.run import globalize, sources

ROOT=Path(__file__).resolve().parents[2]
V3=ROOT/'output/experiments/notch_identity_v3_20261118_r01'
OUT=ROOT/'output/experiments/v3_labelme_compare_20261118_r02'
MAN=ROOT/'output/experiments/grayref_simplified_evidence_v0_20261113_r01/input_manifest.csv'
SELECT=ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv'
POLICY=ROOT/'config/dataset_usage_policy.json'
NAMES={'group_a':'开发组A','ct2':'CT2','ct3':'CT3','group_h':'开发组H','three_point_bend':'三点弯','group_c':'验证组C'}

def read_csv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read_json(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def save(p,data):
    p.write_text(json.dumps(clean(data),ensure_ascii=False,indent=1,allow_nan=False),encoding='utf-8')

def current(path,expected):
    buf=Path(path).read_bytes()
    assert hashlib.sha256(buf).hexdigest()==expected, path
    img=cv2.imdecode(np.frombuffer(buf,np.uint8),cv2.IMREAD_UNCHANGED)
    assert img is not None and img.dtype==np.uint8 and img.ndim==2,path
    return img

fixed_image=lru_cache(maxsize=6)(current)

def predict(job):
    row,prev=job
    raw=current(row['current'],row['image_sha'])
    assert raw.shape==(int(row['height']),int(row['width']))
    fixed=fixed_image(row['reference'],row['ref_sha'])
    points=json.loads(row['current_points'])
    fp=json.loads(row['reference_points'])
    pp=json.loads(prev['current_points']) if prev else None
    previous=current(prev['current'],prev['image_sha']) if prev else None
    assert ordered_points(points,raw.shape) is not None
    scene=scene_geometry(raw,points,fixed,fp,None,CONFIG)
    xa,ya,xb,yb=scene['bounds']
    roi=raw[ya:yb,xa:xb]
    legacy_graph_budget_exceeded=bool(roi.size>CONFIG['max_roi_pixels'])
    offset=[xa,ya]
    hint=np.rint(np.array(scene['root'] or scene['center'])-offset).astype(int)
    prep=terminal.prepare(roi,hint,scene['scale'],'s3t')
    bonus=None
    ref_status={}
    if prep is not None:
        sl=prep[0]
        bonus=np.zeros(prep[3].shape,np.float32)
        for channel,ref,rp in [('fixed',fixed,fp),('previous',previous,pp)]:
            data,info=register_reference(ref,raw,rp,points,scene,CONFIG)
            bonus+=np.where(data['valid'][sl],.04*np.clip(data['signed'][sl]/20,0,1),0)
            ref_status[channel]=info['status']
        bonus[prep[3]<1.]=0.
    full=globalize(terminal.predict(prep,bonus),offset)
    off=globalize(terminal.predict(prep,np.zeros_like(bonus) if prep is not None else None),offset)
    return dict(group=row['group'],frame=int(row['frame_id']),source_sha=row['image_sha'],
                reference_sha=row['ref_sha'],previous_sha=prev['image_sha'] if prev else None,
                legacy_graph_budget_exceeded=legacy_graph_budget_exceeded,point_kind=row['point_kind'],bounds=scene['bounds'],hint=hint+offset,
                reference_status=ref_status,full=full,raw_only=off)

def run(out):
    out.mkdir(parents=True,exist_ok=False)
    cv2.setNumThreads(1)
    policy=read_json(POLICY)
    allowed={g for g,role in policy['groups'].items() if role in ('DEVELOPMENT','VALIDATION_ONLY')}
    assert allowed==set(NAMES)
    freeze=read_json(V3/'freeze.json')
    assert freeze['primary']=='s3t' and freeze['sources']==sources()
    manifest=[r for r in read_csv(MAN) if r['group'] in allowed]
    selected=[r for r in read_csv(SELECT) if r['dataset_id'] in allowed]
    assert Counter(r['dataset_id'] for r in selected)==dict.fromkeys(allowed,20)
    index={(r['group'],int(r['tracking_num'])):r for r in manifest}
    assert len(index)==len(manifest)
    jobs=[]
    for item in selected:
        g=item['dataset_id']; k=int(item['frame_order']); row=index[g,k]
        assert row['frame_id']==item['frame_id'] and row['image_sha']==item['sha256']
        assert np.array_equal(json.loads(row['current_points']),json.loads(item['points']))
        assert row['ref_sha']==index[g,0]['image_sha'] and row['reference']==index[g,0]['current']
        jobs.append((row,index[g,k-1] if k else None))
    for p in {r['point_source'] for r,_ in jobs}:
        assert digest(Path(p))==next(r['point_source_sha'] for r,_ in jobs if r['point_source']==p)
    save(out/'lock.json',dict(mode='s3t',sources=freeze['sources'],selection_sha=digest(SELECT),
         manifest_sha=digest(MAN),policy_sha=digest(POLICY),features_sha=digest(ROOT/'research/unified_crack_tip_60q/features.py'),
         feature_config_sha=digest(ROOT/'research/unified_crack_tip_60q/config.py'),roles=policy['groups']))
    path=out/'predictions.jsonl'
    with path.with_suffix('.partial').open('x',encoding='utf-8') as f,ThreadPoolExecutor(2) as pool:
        for i,r in enumerate(pool.map(predict,jobs),1):
            f.write(json.dumps(clean(r),ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')
            if i%20==0:print(i,r['group'],flush=True)
    path.with_suffix('.partial').rename(path)
    judged={(r['group'],r['frame']):r for r in map(json.loads,path.read_text().splitlines())}
    assert len(judged)==120
    overlaps=[]; differences=[]
    for split in ('dev','locked'):
        old=V3/'s3t'/(split+'.jsonl')
        assert digest(old)==read_json(V3/'s3t'/(split+'_seal.json'))['predictions']
        for b in map(json.loads,old.read_text().splitlines()):
            key=b['group'],b['frame']
            if key not in judged:continue
            r=judged[key]; assert b['source_sha']==r['source_sha']
            overlaps.append(key)
            for mode in ('full','raw_only'):
                for field in ('status','root','points','tip'):
                    if r[mode][field]!=b[mode][field]:differences.append([*key,mode,field])
    assert len(overlaps)==60
    save(out/'seal.json',dict(predictions_sha=digest(path),frames=120,overlap_frames=len(overlaps),overlap_differences=differences))
    print('previous run parity',len(overlaps),len(differences),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,default=OUT)
    run(parser.parse_args().out)


