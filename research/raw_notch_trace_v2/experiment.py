"""Run split, seal predictions, and render equal-coordinate RAW / trace images."""
import argparse
import concurrent.futures
import csv
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from detector import prepare, predict

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
OLD = ROOT/'output/experiments/unified_crack_tip_60q_20261113_r01'
GROUPS = {'dev':{'group_a':551,'three_point_bend':520},'locked':{'group_c':562}}


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=1),encoding='utf-8')


def source_hash():
    return {p.name:sha(p) for p in sorted(SOURCE.glob('*.py'))}


def draw_card(raw, result, hint, group, frame):
    h,w=raw.shape
    root=result['root'] or hint
    points=result['points']
    extent=np.asarray([root]+points)
    xlo,ylo=extent.min(0)
    xhi,yhi=extent.max(0)
    width=min(w,max(390,int(xhi-xlo)+85,int((yhi-ylo+60)*2.2)))
    height=min(h,max(112,int(width/2.2)))
    left=int(np.clip(xlo-40,0,w-width))
    top=int(np.clip((ylo+yhi-height)/2,0,h-height))
    color=cv2.cvtColor(raw,cv2.COLOR_GRAY2BGR)
    trace=color.copy()
    for a,b in zip(points,points[1:]):
        if b[0]-a[0]==1:
            cv2.line(trace,tuple(a),tuple(b),(90,210,0),1)
        else:
            cv2.circle(trace,tuple(b),1,(0,180,240),-1)
    if result['root']:
        cv2.drawMarker(trace,tuple(root),(255,140,0),cv2.MARKER_CROSS,11,1)
    if result['tip']:
        cv2.circle(trace,tuple(result['tip']),6,(20,40,255),1,cv2.LINE_AA)
    card=np.full((490,1280,3),25,np.uint8)
    def panel(img,x,y,width,height):
        factor=min(width/img.shape[1],height/img.shape[0])
        scaled=cv2.resize(img,None,fx=factor,fy=factor,interpolation=cv2.INTER_AREA if factor<1 else cv2.INTER_LINEAR)
        card[y:y+scaled.shape[0],x:x+scaled.shape[1]]=scaled
    def title(msg,pt):
        cv2.putText(card,msg,pt,cv2.FONT_HERSHEY_SIMPLEX,.58,(235,235,235),1,cv2.LINE_AA)
    title(f'{group}   frame {frame}    {result["status"]}',(12,24))
    title('Raw ROI and local detail',(12,52))
    title('Root (+)   observed crack (green)   tip (red circle)',(650,52))
    for x,img in ((8,color),(648,trace)):
        panel(img,x,66,622,122)
        panel(img[top:top+height,left:left+width],x,197,622,282)
    return card


def process(args):
    run,row,control=args
    g,fid=row['group'],row['frame_id']
    folder=OLD/'evidence'/g/fid
    meta=read(folder/'metadata.json')
    scene=meta['evidence']['scene']
    assert meta['input']['image_sha']==row['image_sha']
    offset=np.array(scene['bounds'][:2])
    hint=np.rint(np.array(scene['root'] or scene['center'])-offset).astype(int).tolist()
    assert sha(folder/'arrays.npz') == meta['arrays_sha']
    with np.load(folder/'arrays.npz') as data:
        raw=data['raw']
        prep=prepare(raw,hint,scene['scale'])
        bonus=None
        if prep is not None:
            sl=prep[0]
            bonus=np.zeros(prep[3].shape,np.float32)
            for key in ('fixed','prev'):
                valid=data[key+'__valid'][sl]
                signed=data[key+'__signed'][sl]
                bonus+=np.where(valid,.04*np.clip(signed/20,0,1),0)
            # No bonus for a pixel without raw-valley support.
            bonus[prep[3]<1.]=0
    out=predict(prep,bonus)
    card=draw_card(raw,out,hint,g,fid)
    dest=run/'frames'/g/(fid+'.jpg')
    assert cv2.imwrite(str(dest),card,[cv2.IMWRITE_JPEG_QUALITY,90])
    def globalize(result):
        def xy(p):return [p[0]+int(offset[0]),p[1]+int(offset[1])] if p else None
        return {**result,'root':xy(result['root']),'tip':xy(result['tip']),
                'points':[xy(p) for p in result['points']]}
    record=dict(group=g,frame=int(fid),source_sha=row['image_sha'],full=globalize(out),card_sha=sha(dest))
    if control:
        off=predict(prep,np.zeros_like(bonus) if prep is not None else None)
        record['raw_only']=globalize(off)
    return record


def run_split(run,split):
    if split=='locked':
        freeze=read(run/'freeze.json')
        assert freeze['source']==source_hash() and freeze['dev_predictions']==sha(run/'dev.jsonl')
    with (OLD/'manifests/input_inventory.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=[r for r in csv.DictReader(f) if r['group'] in GROUPS[split]]
    for g,n in GROUPS[split].items():
        group=[int(r['frame_id']) for r in rows if r['group']==g]
        assert group==list(range(1,n+1))
        (run/'frames'/g).mkdir(parents=True,exist_ok=True)
    path=run/(split+'.jsonl')
    assert not path.exists() and not path.with_suffix('.partial').exists()
    cv2.setNumThreads(1)
    with path.with_suffix('.partial').open('x',encoding='utf-8') as out:
        with concurrent.futures.ThreadPoolExecutor(5) as pool:
            for i,record in enumerate(pool.map(process,((run,r,split=='dev') for r in rows)),1):
                out.write(json.dumps(record,separators=(',',':'))+'\n')
                if i%150==0:print(split,i,len(rows),flush=True)
    path.with_suffix('.partial').rename(path)
    save(run/(split+'_seal.json'),dict(frames=len(rows),source=source_hash(),predictions=sha(path)))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('split',choices=['dev','locked','freeze'])
    parser.add_argument('run',type=Path)
    args=parser.parse_args()
    if args.split=='freeze':
        assert not (args.run/'freeze.json').exists()
        dev=read(args.run/'dev_seal.json')
        assert dev['source']==source_hash() and dev['predictions']==sha(args.run/'dev.jsonl')
        assert (args.run/'dev_metrics.json').is_file()
        save(args.run/'freeze.json',dict(source=source_hash(),dev_predictions=dev['predictions'],dev_metrics=sha(args.run/'dev_metrics.json')))
    else:run_split(args.run,args.split)


