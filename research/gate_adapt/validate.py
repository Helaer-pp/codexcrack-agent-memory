"""CT3 ordered replay, comparisons and controlled false-line checks."""
import argparse
import csv
import ctypes as C
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import cv2
from adapt import GateAdapter
from controls import controls
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/gap_resume'))
from replay import api
from interference import make_cases
from PIL import Image
from render_roi import RoiComparison

DATA=Path(r'D:/datasets\1-引伸计\1-裂纹\2.裂纹扩展\白色喷漆')
V1=ROOT/'output/runs/ct3_gap_resume_final'
FROZEN=ROOT/'output/runs/ct3_white_frozenA_20261106_r01'


class Stream:
    def __init__(self,ref,anchors,mode='auto'):
        self.det=api.Baseline(ref,anchors,mode=mode)
        self.adapter=GateAdapter(ref,anchors)
        self.fn=self.det.lib.CrackGateProbe
        self.fn.argtypes=[C.c_void_p,C.POINTER(api.Image),C.c_uint64]
        self.fn.restype=C.c_char_p

    def frame(self,i,im,anchors):
        raw=self.det.run(im,anchors,i==0)
        self.last_raw=raw
        f=raw['formal'];stop=raw['native']['stop_reason']
        reason=None
        base=[f['raw_path']] if f['tip'] is not None else []
        blocked=[]
        if stop=='gap_unresolved':
            probe=json.loads(self.fn(self.det.handle,C.byref(api.image(im)),i))
            if 'error' in probe:raise ValueError(probe)
            reason=probe['reason'];blocked=probe['segments']
            if reason=='recovered':base=blocked
        matrix=np.asarray(raw['native']['transform_reference_to_current'],dtype=np.float64)
        ok=raw['geometry']['registration_state']=='REGISTRATION_VALID' and raw['geometry']['current_anchor_valid']
        segs,action=self.adapter.apply(i,im,matrix,base,stop,blocked,reason,ok)
        tip=(f['tip'] if f['tip'] is not None else segs[-1][-1] if segs else None)
        old_tip=f['tip'] if f['tip'] is not None else base[-1][-1] if base else None
        return dict(segments=segs,tip_px=tip,action=action,previous_segments=base,previous_tip=old_tip,
                    A_stop=stop,v1_reason=reason,length_px=f['length_px'],
                    matrix=matrix.tolist(),anchors=anchors,A_tip=f['tip'])


def run(out):
    rows=api.load(V1/'paths.jsonl')
    ref=api.read(DATA/rows[0]['image'])
    stream=Stream(ref,rows[0]['anchors'])
    result=[]
    folder=out/'frames';folder.mkdir()
    exporter=RoiComparison()
    for i,r in enumerate(rows):
        im=api.read(DATA/r['image']); z=stream.frame(i,im,r['anchors'])
        assert (z['previous_tip'],z['previous_segments'],z['A_stop'],z['v1_reason'],z['length_px'])==(r['tip_px'],r['segments'],r['A_stop'],r['recovery'],r['length_px'])
        z.update(frame=i+1,image=r['image'])
        result.append(z)
        img,_=exporter.render(Image.fromarray(im),z)
        img.save(folder/f"{i+1:04d}_{Path(z['image']).stem}.png")
    stream.det.close()
    with (out/'paths.jsonl').open('w',encoding='utf8') as f:
        for z in result:f.write(json.dumps(z)+'\n')
    api.csvout(out/'results.csv',[dict(frame=z['frame'],image=z['image'],old_tip_x=(z['previous_tip'] or [None,None])[0],old_tip_y=(z['previous_tip'] or [None,None])[1],new_tip_x=(z['tip_px'] or [None,None])[0],new_tip_y=(z['tip_px'] or [None,None])[1],length_px=z['length_px'],action=z['action']) for z in result])
    added=[(z['frame'],z['tip_px'],z['action']) for z in result if z['previous_tip'] is None and z['tip_px'] is not None]
    cases=[]
    for name,reference,current in make_cases(ref,api.read(DATA/rows[108]['image']),np.array(result[108]['matrix'])):
        stream=Stream(reference,rows[0]['anchors'])
        for i,r in enumerate(rows[:109]):
            im=reference if i==0 else current if i==108 else api.read(DATA/r['image'])
            z=stream.frame(i,im,r['anchors'])
        stream.det.close()
        cases.append(dict(case=name,previous=z['previous_tip'],adapted=z['tip_px'],action=z['action']))
    report=dict(frames=len(rows),v1_confirmed=sum(z['previous_tip'] is not None for z in result),
                adapted_confirmed=sum(z['tip_px'] is not None for z in result),added=added,controls=cases)
    report['gate_fixtures']=controls()
    assert all(z['previous_tip'] is None or z['previous_tip']==z['tip_px'] for z in result)
    assert len(result)==136
    api.save(out/'summary.json',report)
    print(json.dumps(report,indent=2))
    with subprocess.Popen([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-v','error','-f','image2pipe','-framerate','15','-c:v','png','-i','-','-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'CT3_adapted.mp4')],stdin=subprocess.PIPE) as enc:
        for p in sorted(folder.glob('*.png')):enc.stdin.write(p.read_bytes())
        enc.stdin.close()
        if enc.wait():raise RuntimeError('encoder failed')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('run_id');opts=parser.parse_args()
    if Path(opts.run_id).name!=opts.run_id:raise ValueError(opts.run_id)
    out=ROOT/'output/runs'/opts.run_id;out.mkdir(exist_ok=False)
    api.BASE=ROOT/'output/build/Release/CrackGateProbe.dll';api.EXPECTED_BASE=api.sha(api.BASE)
    run(out)

