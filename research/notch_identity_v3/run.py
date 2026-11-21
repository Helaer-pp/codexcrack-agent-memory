"""Batch predictions, offline comparison, and one pre-frozen regression transaction."""
import argparse
import csv
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from . import detector
from research.raw_notch_trace_v2b import detector as baseline

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
R02=ROOT/'research/raw_notch_trace_v2b'
sys.path.append(str(R02))
from experiment import OLD, GROUPS, read, save, sha, draw_card
from evaluate import evaluate
from deliver import deliver

RUN=ROOT/'output/experiments/notch_identity_v3_20261118_r01'
PREVIOUS=ROOT/'output/experiments/raw_notch_trace_v2_20261118_r02'


def init():
    cv2.setNumThreads(1)
    # JIT warmup outside any dataset.
    baseline.trace_windowed(np.ones((15,20),np.float32),np.zeros((15,20),np.float32),1,7)


def globalize(result,offset):
    def xy(pt):
        return [pt[0]+offset[0],pt[1]+offset[1]] if pt is not None else None
    d=result['diagnostics']
    for candidate in d['candidates']:
        candidate['start']=xy(candidate['start'])
        candidate['tip']=xy(candidate['tip'])
        if 'near_end' in candidate:
            candidate['near_end']+=offset[0]
    if d.get('terminal'):
        d['terminal']['untrimmed_x']+=offset[0]
    for pair in d['pairs']:
        pair[2]+=offset[0]
    return {**result,'root':xy(result['root']),'tip':xy(result['tip']),'points':[xy(p) for p in result['points']]}


def process(job):
    row,stages=job
    group,fid=row['group'],row['frame_id']
    directory=OLD/'evidence'/group/fid
    meta=read(directory/'metadata.json')
    assert meta['input']['image_sha']==row['image_sha'] and sha(directory/'arrays.npz')==meta['arrays_sha']
    scene=meta['evidence']['scene']
    offset=scene['bounds'][:2]
    hint=np.rint(np.array(scene['root'] or scene['center'])-offset).astype(int).tolist()
    records={}
    with np.load(directory/'arrays.npz') as data:
        raw=data['raw']
        for stage in stages:
            if stage=='s1':
                prep=detector.prepare(raw,hint,scene['scale'])
                fn=detector.predict
            else:
                from . import terminal
                prep=terminal.prepare(raw,hint,scene['scale'],stage)
                fn=terminal.predict
            bonus=None
            if prep is not None:
                sl=prep[0]
                bonus=np.zeros(prep[3].shape,np.float32)
                for key in ('fixed','prev'):
                    bonus+=np.where(data[key+'__valid'][sl],.04*np.clip(data[key+'__signed'][sl]/20,0,1),0)
                bonus[prep[3]<1.]=0
            out=fn(prep,bonus)
            record=dict(group=group,frame=int(fid),source_sha=row['image_sha'])
            dest=RUN/stage/'frames'/group/(fid+'.jpg')
            assert cv2.imwrite(str(dest),draw_card(raw,out,hint,group,fid),[cv2.IMWRITE_JPEG_QUALITY,86])
            record['card_sha']=sha(dest)
            record['full']=globalize(out,offset)
            off=fn(prep,np.zeros_like(bonus) if bonus is not None else None)
            record['raw_only']=globalize(off,offset)
            records[stage]=record
    return records


def sources():
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted([HERE/name for name in ('detector.py','run.py','probes.py','terminal.py','topology.py','verify_dev.py')]+list(R02.glob('*.py')))}


def run(split,stages):
    if split=='locked':
        freeze=read(RUN/'freeze.json')
        assert stages==freeze['stages'] and sources()==freeze['sources']
        for stage in stages:
            assert freeze['dev'][stage]==sha(RUN/stage/'dev.jsonl')
    assert sha(R02/'detector.py')==read(PREVIOUS/'freeze.json')['source']['detector.py']
    with (OLD/'manifests/input_inventory.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=[r for r in csv.DictReader(f) if r['group'] in GROUPS[split]]
    handles={}
    for stage in stages:
        for group,n in GROUPS[split].items():
            assert [int(r['frame_id']) for r in rows if r['group']==group]==list(range(1,n+1))
            (RUN/stage/'frames'/group).mkdir(parents=True,exist_ok=True)
        path=RUN/stage/(split+'.jsonl')
        assert not path.exists()
        handles[stage]=path.with_suffix('.partial').open('x',encoding='utf-8')
    try:
        with ProcessPoolExecutor(max_workers=6,initializer=init) as pool:
            for i,records in enumerate(pool.map(process,((r,stages) for r in rows),chunksize=3),1):
                for stage,record in records.items():
                    handles[stage].write(json.dumps(record,default=lambda v:v.item(),separators=(',',':'))+'\n')
                if i%100==0:
                    print(split,stages,i,len(rows),flush=True)
    finally:
        for handle in handles.values():
            handle.close()
    for stage in stages:
        path=RUN/stage/(split+'.jsonl')
        path.with_suffix('.partial').rename(path)
        save(path.parent/(split+'_seal.json'),dict(frames=len(rows),predictions=sha(path),sources=sources()))
        evaluate(path.parent,split)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('split',choices=['dev','locked','freeze','deliver'])
    parser.add_argument('stages',nargs='+',choices=['s1','s2','s3','s3t'])
    args=parser.parse_args()
    if args.split=='freeze':
        assert not (RUN/'freeze.json').exists()
        assert read(RUN/'development_replay.json')['stage_mode_checks']==48
        save(RUN/'freeze.json',dict(primary='s3t',stages=args.stages,sources=sources(),dev={s:sha(RUN/s/'dev.jsonl') for s in args.stages},
                                    probes=sha(RUN/'probes.csv')))
    elif args.split=='deliver':
        deliver(RUN/args.stages[-1])
    else:
        run(args.split,args.stages)





