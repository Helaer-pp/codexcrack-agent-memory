"""Locked seven-group evaluation. One chronological detector/adapter per specimen."""
import argparse
import csv
import hashlib
import io
import json
import struct
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from validate import api, DATA, ROOT, Stream, RoiComparison


def csv_rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def inventory():
    groups=json.loads((ROOT/'config/datasets.json').read_text(encoding='utf8'))['groups']
    manifest=csv_rows(ROOT/'data/inputs/six_groups_manifest.csv')
    seq={}
    for g in groups:
        rows=[r for r in manifest if r['dataset_alias']==g['id']]
        assert len(rows)==g['frames']
        for i,r in enumerate(rows):
            assert int(r['frame_id'])==i and (r['is_reference']=='True')==(i==0) and r['mode']==g['mode']
        seq[g['id']]=(g['mode'],[(Path(r['input_image']),json.loads(r['points']),r['input_sha256']) for r in rows])
    ct3=csv_rows(ROOT/'output/runs/ct3_white_frozenA_20261106_r01/逐帧裂纹结果.csv')
    assert len(ct3)==136 and [int(r['坐标num']) for r in ct3]==list(range(136))
    seq['ct3']=('auto',[(DATA/r['图片名'],[[float(r[f'P{k}x']),float(r[f'P{k}y'])] for k in (1,2)],None) for r in ct3])
    return seq


def run(group, dest):
    mode,rows=inventory()[group]
    folder=dest/group
    folder.mkdir(parents=True,exist_ok=True)
    if (folder/'summary.json').exists():raise FileExistsError('Group already verified')
    frames=folder/'frames';frames.mkdir(exist_ok=True)
    exporter=RoiComparison()
    prod=ROOT/'data/frozen_a_replay'
    if group=='ct3':
        reference=api.load(ROOT/'output/runs/ct3_white_frozenA_20261106_r01/paths.jsonl')
        prior=api.load(ROOT/'output/runs/ct3_adaptive_gate_final/paths.jsonl')
    else:
        reference=api.load(prod/(group+'_A.jsonl'))
    assert len(reference)==len(rows)
    ff=ROOT/'third_party/ffmpeg'
    video=folder/'result.mp4'
    records=[]
    with (folder/'paths.jsonl').open('w',encoding='utf8') as paths, subprocess.Popen(
        [str(ff/'ffmpeg.exe'),'-y','-v','error','-f','image2pipe','-framerate','15','-c:v','png','-i','-','-threads','2','-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],stdin=subprocess.PIPE) as enc:
        # Exact archived float64 centerlines, including non-confirmed candidates.
        bin_stream=None if group=='ct3' else (prod/(group+'_A.pathbin')).open('rb')
        det=None
        try:
            for i,(path,points,expected_hash) in enumerate(rows):
                data=path.read_bytes()
                digest=hashlib.sha256(data).hexdigest()
                if expected_hash and digest!=expected_hash:raise ValueError(('image hash',path))
                im=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_GRAYSCALE)
                if im is None:raise ValueError(path)
                if det is None:det=Stream(im,points,mode)
                z=det.frame(i,im,points)
                native=det.last_raw['native']; formal=det.last_raw['formal']; archived=reference[i]
                if group=='ct3':
                    assert (formal['raw_path'],z['A_tip'],formal['valid_full_length'])==(archived['path'],archived['tip'],archived['length_valid'])
                    assert (z['tip_px'],z['segments'],z['action'])==(prior[i]['tip_px'],prior[i]['segments'],prior[i]['action'])
                else:
                    assert api.normalized(native)==api.normalized(archived),(group,i,'A status')
                    n=struct.unpack('<i',bin_stream.read(4))[0]
                    assert np.asarray(formal['raw_path'],dtype='<f8').tobytes()==bin_stream.read(n*16),(group,i,'A path')
                if z['A_tip'] is not None:assert z['previous_tip']==z['A_tip']
                if z['previous_tip'] is not None:assert z['tip_px']==z['previous_tip'] and z['segments']==z['previous_segments']
                z.update(frame=i+1,image=path.name)
                frame,box=exporter.render(Image.fromarray(im),z)
                png=io.BytesIO();frame.save(png,format='PNG',compress_level=2)
                name=f'{i+1:04d}_{path.stem}.png'
                (frames/name).write_bytes(png.getvalue())
                enc.stdin.write(png.getbuffer())
                source='A' if z['A_tip'] is not None else 'gap' if z['previous_tip'] is not None else 'adapt' if z['tip_px'] is not None else 'none'
                a=z['A_tip'] or [None,None]; v=z['previous_tip'] or [None,None]; t=z['tip_px'] or [None,None]
                records.append(dict(frame=i+1,image=path.name,source=source,A_x=a[0],A_y=a[1],V1_x=v[0],V1_y=v[1],tip_x=t[0],tip_y=t[1],length_px=z['length_px'],A_stop=z['A_stop'],gap_reason=z['v1_reason'],action=z['action'],png=name))
                paths.write(json.dumps(dict(frame=i+1,image=path.name,image_sha256=digest,anchors=points,roi=box,tip=t if z['tip_px'] is not None else None,segments=z['segments'],length_px=z['length_px']),ensure_ascii=False)+'\n')
                if (i+1)%100==0:print(group,i+1,'/',len(rows),flush=True)
            if bin_stream:assert not bin_stream.read(1)
        finally:
            if det:det.det.close()
            if bin_stream:bin_stream.close()
            enc.stdin.close()
        if enc.wait():raise RuntimeError('FFmpeg encode failed')
    api.csvout(folder/'results.csv',records)
    nvideo=int(subprocess.check_output([str(ff/'ffprobe.exe'),'-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=nb_read_frames','-of','default=nw=1:nk=1',str(video)]))
    pngs=list(frames.glob('*.png'))
    assert len(set(r['png'] for r in records))==len(pngs)==len(rows)==nvideo
    for r in records:
        with Image.open(frames/r['png']) as pic:
            assert pic.size==(1442,360)
            pic.verify()
    totals={s:sum(r['source']==s for r in records) for s in ['A','gap','adapt','none']}
    summary=dict(group=group,mode=mode,frames=len(rows),verified_video_frames=nvideo,exact_A_frames=len(rows),A=totals['A'],V1=totals['A']+totals['gap'],latest=len(rows)-totals['none'],gap_add=totals['gap'],adapt_add=totals['adapt'],missing=totals['none'],complete_lengths=sum(r['length_px'] is not None for r in records))
    api.save(folder/'summary.json',summary)
    print(summary,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('group',choices=inventory().keys())
    parser.add_argument('run_id');args=parser.parse_args()
    if Path(args.run_id).name!=args.run_id:raise ValueError(args.run_id)
    api.BASE=ROOT/'output/build/Release/CrackGateProbe.dll'
    api.EXPECTED_BASE=api.sha(api.BASE)
    run(args.group,ROOT/'output/runs'/args.run_id)

