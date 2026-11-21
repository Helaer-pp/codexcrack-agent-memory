"""Replay CT3 with measured anchors. Output only confirmed segments, in current-image pixels."""
import argparse
import csv
import ctypes as C
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src/python'))
from crackv4 import frozen_a as api


def run_extra(det, im, i):
    fn = det.lib.CrackGapResume
    fn.argtypes = [C.c_void_p, C.POINTER(api.Image), C.c_uint64]
    fn.restype = C.c_char_p
    result = json.loads(fn(det.handle, C.byref(api.image(im)), i))
    if 'error' in result:
        raise RuntimeError(result)
    return result


def display(im, row, segments):
    # Both panels have exactly the same crop in original pixel coordinates.
    spacing = np.linalg.norm(np.diff(row['anchors'],axis=0))
    cx,cy = np.mean(row['anchors'],axis=0)
    extent = np.asarray([p for seg in segments for p in seg] or [[cx,cy]])
    x0,y0 = np.floor(np.minimum([cx-.45*spacing,cy-spacing],extent.min(0)-12)).astype(int)
    x1,y1 = np.ceil(np.maximum([cx+2.9*spacing,cy+spacing],extent.max(0)+12)).astype(int)
    crop=Image.fromarray(im).crop((x0,y0,x1,y1))
    scale=min(620/crop.width,365/crop.height)
    crop=crop.resize((round(scale*crop.width),round(scale*crop.height)),Image.Resampling.BICUBIC)
    canvas=Image.new('RGB',(1280,470),'#142330')
    draw=ImageDraw.Draw(canvas);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
    for panel, heading in enumerate(['原图','确认结果']):
        ox=panel*640+10
        canvas.paste(crop,(ox,48))
        draw.text((ox,12),f"{heading}   {row['image']}   第 {row['frame']} 帧",font=font)
    def xy(p):return (650+(p[0]-x0+.5)*scale,48+(p[1]-y0+.5)*scale)
    for seg in segments:
        if len(seg)>1: draw.line([xy(p) for p in seg],fill='#fa4238',width=2)
    if row['tip_px'] is not None:
        x,y=xy(row['tip_px']);draw.ellipse((x-6,y-6,x+6,y+6),outline='#ffac00',width=2)
    label={'A':'冻结 A 已确认','resumed':'断点后恢复','none':'尖端未确认'}[row['source']]
    tip=row['tip_px']; value='—' if tip is None else f'({tip[0]:.2f}, {tip[1]:.2f}) px'
    draw.text((12,425),f"{label}    尖端 {value}    完整长度 "+('未确认' if row['length_px'] is None else f"{row['length_px']:.2f} px"),font=font)
    return canvas


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-id',required=True)
    args=parser.parse_args()
    if Path(args.run_id).name!=args.run_id:raise ValueError(args.run_id)
    out=ROOT/'output/runs'/args.run_id
    out.mkdir(exist_ok=False)
    (out/'frames').mkdir()
    run=ROOT/'output/runs/ct3_white_frozenA_20261106_r01'
    with (run/'逐帧裂纹结果.csv').open(encoding='utf-8-sig') as stream:
        rows=list(csv.DictReader(stream))
    saved=api.load(run/'paths.jsonl')
    data=Path(r'D:/datasets\1-引伸计\1-裂纹\2.裂纹扩展\白色喷漆')
    api.BASE=ROOT/'output/build/Release/CrackV4GapResume.dll'
    api.EXPECTED_BASE=api.sha(api.BASE)
    results=[]
    for i,(r,z) in enumerate(zip(rows,saved)):
        im=api.read(data/r['图片名'])
        pp=np.array([[float(r[f'P{j}x']),float(r[f'P{j}y'])] for j in (1,2)])
        if not i:det=api.Baseline(im,pp,mode='auto')
        raw=det.run(im,pp,i==0)
        f=raw['formal']
        assert (f['tip'],f['raw_path'],f['valid_full_length'],raw['native']['stop_reason'])==(z['tip'],z['path'],z['length_valid'],r['停止原因'])
        extra=run_extra(det,im,i) if r['停止原因']=='gap_unresolved' else None
        tip=f['tip']; segments=[f['raw_path']] if tip is not None else []
        source='A' if tip is not None else 'none'
        if extra and extra['tip_px'] is not None:
            tip=extra['tip_px'];segments=extra['segments'];source='resumed'
            assert segments[-1][-1]==tip and extra['complete_length_px'] is None
        row=dict(frame=i+1,image=z['image'],anchors=pp.tolist(),source=source,tip_px=tip,length_px=f['length_px'],
                 A_stop=r['停止原因'],recovery=extra['reason'] if extra else None,segments=segments)
        results.append(row)
        display(im,row,segments).save(out/'frames'/f"{i+1:04d}_{z['image'][:-4]}.png")
    det.close()
    assert len(results)==len(saved)==len(rows)==136
    with (out/'paths.jsonl').open('w',encoding='utf8') as stream:
        for row in results:stream.write(json.dumps(row)+'\n')
    api.csvout(out/'results.csv',[dict(frame=r['frame'],image=r['image'],source=r['source'],tip_x=(r['tip_px'] or [None,None])[0],tip_y=(r['tip_px'] or [None,None])[1],full_length_px=r['length_px'],A_stop=r['A_stop'],recovery=r['recovery']) for r in results])
    report=dict(frozen_results_identical=len(results),candidate_sha256=api.sha(api.BASE),sources=dict(Counter(r['source'] for r in results)),gap_reasons=dict(Counter(r['recovery'] for r in results if r['recovery'])),frame109={k:v for k,v in results[108].items() if k!='segments'})
    api.save(out/'summary.json',report)
    with subprocess.Popen([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-v','error','-f','image2pipe',
                           '-framerate','15','-c:v','png','-i','-','-c:v','libx264','-crf','17',
                           '-pix_fmt','yuv420p','-movflags','+faststart',str(out/'CT3_recovery.mp4')],
                          stdin=subprocess.PIPE) as encoder:
        for frame in sorted((out/'frames').glob('*.png')):
            encoder.stdin.write(frame.read_bytes())
        encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError('video export failed')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
