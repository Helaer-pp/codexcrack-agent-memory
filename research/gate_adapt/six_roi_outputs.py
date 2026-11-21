"""Compare only the intersection coverage cohort; render all frames in order."""
import argparse
import csv
import itertools
import json
import math
import subprocess
from zipfile import ZipFile,ZIP_STORED

import numpy as np
from PIL import Image,ImageDraw,ImageFont
from six_roi_replay import OUT,ROOT,NAMES,DISPLAY,CASES,contains,api,inventory

def distance(a,b):
    return math.dist(a,b) if a is not None and b is not None else None

def assess(group,records):
    folder=OUT/group
    frame_rows=[];case_rows=[];pair_rows=[]
    for z in records:
        cases=z['cases']; eligible=z['coverage']=='shared'
        valid=[v['tip'] for v in cases.values() if v['tip'] is not None]
        span=max((math.dist(a,b) for a,b in itertools.combinations(valid,2)),default=None)
        common_tips=all(contains(c['roi'],t) for t in valid for c in cases.values())
        for name,c in cases.items():
            t=c['tip']
            case_rows.append(dict(frame=z['frame'],image=z['image'],case=name,coverage=z['coverage'],proxy=z['proxy'],
                confirmed=int(t is not None),tip_x=t[0] if t else None,tip_y=t[1] if t else None,
                distance_to_proxy_px=distance(t,z['proxy']) if eligible else None,
                tip_measure_reason=c.get('tip_measure_reason'),
                status=c.get('status'),
                roi=c['roi'],points=c['anchors']))
        if eligible:
            for a,b in itertools.combinations(CASES,2):
                ta,tb=cases[a]['tip'],cases[b]['tip']
                pair_rows.append(dict(frame=z['frame'],image=z['image'],a=a,b=b,confirmed_a=int(ta is not None),
                    confirmed_b=int(tb is not None),delta_px=distance(ta,tb)))
        frame_rows.append(dict(frame=z['frame'],image=z['image'],coverage=z['coverage'],proxy=z['proxy'],
            confirmed=len(valid),missing=8-len(valid),pair_max_px=span if eligible else None,
            all_returned_tips_in_all_roi=common_tips if eligible and valid else None))
    rr=[r for r in frame_rows if r['coverage']=='shared']
    d=[r['pair_max_px'] for r in rr if r['pair_max_px'] is not None]
    diff=[r for r in rr if r['pair_max_px'] and r['pair_max_px']>0]
    worst=max(diff,key=lambda r:r['pair_max_px'],default=None)
    cases=[]
    for name in CASES:
        sample=[r for r in case_rows if r['coverage']=='shared' and r['case']==name]
        errors=[r['distance_to_proxy_px'] for r in sample if r['confirmed']]
        cases.append(dict(group=group,case=name,common=len(sample),confirmed=len(errors),missing=len(sample)-len(errors),
            median_to_proxy_px=float(np.median(errors)) if errors else None))
    summary=dict(group=group,total=len(records),shared=len(rr),unknown=sum(r['coverage']=='unknown' for r in frame_rows),
        outside=sum(r['coverage']=='outside' for r in frame_rows),none=sum(r['confirmed']==0 for r in rr),
        mixed=sum(0<r['confirmed']<8 for r in rr),all8=sum(r['confirmed']==8 for r in rr),
        same8=sum(r['confirmed']==8 and r['pair_max_px']==0 for r in rr),co_confirmed=len(d),
        varying_coordinates=len(diff),variation_with_all_tips_shared=sum(r['all_returned_tips_in_all_roi'] for r in diff),
        max_px=max(d,default=None),p95_frame_span_px=float(np.percentile(d,95)) if d else None,
        worst_frame=worst['frame'] if worst else None,miss_range=[min(c['missing'] for c in cases),max(c['missing'] for c in cases)])
    assert len(rr)==summary['all8']+summary['mixed']+summary['none'] and len(pair_rows)==len(rr)*28
    api.csvout(folder/'frames.csv',frame_rows);api.csvout(folder/'per_case.csv',case_rows)
    api.csvout(folder/'common_pairs.csv',pair_rows);api.csvout(folder/'case_summary.csv',cases)
    api.save(folder/'summary.json',summary)
    return summary

def render(group,records):
    folder=OUT/group;frames=folder/'frames';frames.mkdir(exist_ok=True)
    labels=['原 A 对照',*DISPLAY]
    if group=='group_h':labels[-1]='间距 × 1.20'
    fonts=[ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n) for n in [32,22,18,16]]
    path=folder/'comparison.mp4'
    cmd=[str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24',
        '-s','1920x1080','-framerate','15','-i','-','-an','-c:v','libx264','-threads','2','-pix_fmt','yuv420p',
        '-crf','17','-preset','veryfast','-movflags','+faststart',str(path)]
    seq=inventory()[group][1]
    old_path=api.load(ROOT/'output/runs/seven_groups_gate_locked_r01'/group/'paths.jsonl')
    # Stable camera for the sequence; expand to include every recorded tip
    # and visible path. Anchor marks outside the display crop are skipped.
    marks=[p for z in records for c in z['cases'].values() for s in c['segments'] for p in s]
    marks += [z['proxy'] for z in records if z['proxy'] is not None]
    marks += [np.mean(z['cases']['measured']['anchors'],axis=0) for z in records]
    pos=np.asarray(marks);lo=pos.min(0)-18;hi=pos.max(0)+18
    center=(lo+hi)*.5; width=max(150,hi[0]-lo[0],(hi[1]-lo[1])*2.85);height=width/2.85
    crop=tuple(map(int,[math.floor(center[0]-width/2),math.floor(center[1]-height/2),
                        math.ceil(center[0]+width/2),math.ceil(center[1]+height/2)]))
    with subprocess.Popen(cmd,stdin=subprocess.PIPE) as enc:
        for z,(file,_,_) in zip(records,seq,strict=True):
            assert z['image']==file.name
            frame=z['frame'];gray=api.read(file)
            h,w=gray.shape;x0=max(0,crop[0]);y0=max(0,crop[1]);x1=min(w,crop[2]);y1=min(h,crop[3])
            scale=min(450/(x1-x0),202/(y1-y0))
            size=(round((x1-x0)*scale),round((y1-y0)*scale))
            base=Image.fromarray(gray[y0:y1,x0:x1]).resize(size,Image.Resampling.LANCZOS).convert('RGB')
            canvas=Image.new('RGB',(1920,1080),'#101b24');draw=ImageDraw.Draw(canvas)
            draw.text((26,14),NAMES[group]+'  |  八组选点下的裂纹尖端',font=fonts[0],fill='#eef5f8')
            draw.text((1360,25),f"{frame:03d} / {len(seq)}      {file.name}",font=fonts[1],fill='#eef5f8')
            draw.text((28,66),'各格使用同一原图视野　　橙线 / 黄圈：当前路径与尖端　　紫色叉：旧 A 实测选点对照　　蓝点：视野内 P1、P2',font=fonts[2],fill='#c2d5df')
            names=['raw','old',*CASES]
            for j,name in enumerate(names):
                x=18+(j%4)*477;y=108+(j//4)*300
                draw.rounded_rectangle((x,y,x+468,y+288),radius=5,fill='#1d2c37')
                draw.text((x+12,y+7),'原图局部' if j==0 else labels[j-1],font=fonts[1],fill='white')
                ox=x+(468-size[0])//2;oy=y+42
                canvas.paste(base,(ox,oy))
                def xy(p):return (ox+(p[0]-x0+.5)*size[0]/(x1-x0),oy+(p[1]-y0+.5)*size[1]/(y1-y0))
                note='同帧原图，无检测标记'
                if j:
                    if name=='old':
                        c=old_path[frame-1]
                        tip=c.get('tip')
                        segments=c.get('segments',[])
                        anchors=z['cases']['measured']['anchors']
                    else:
                        c=z['cases'][name];tip=c['tip']
                        segments=c['segments'];anchors=c['anchors']
                    for pt in anchors:
                        if not (x0<=pt[0]<x1 and y0<=pt[1]<y1):continue
                        a,b=xy(pt);draw.ellipse((a-3,b-3,a+3,b+3),outline='#168ed7',width=2)
                    for seg in segments:
                        if len(seg)>=2:draw.line([xy(p) for p in seg],fill='#ff7434',width=2)
                    if z['proxy']:
                        a,b=xy(z['proxy']);draw.line((a-4,b-4,a+4,b+4),fill='#bc68ff',width=2)
                        draw.line((a-4,b+4,a+4,b-4),fill='#bc68ff',width=2)
                    if tip:
                        a,b=xy(tip);draw.ellipse((a-5,b-5,a+5,b+5),outline='#ffde27',width=2)
                    note=f'尖端  ({tip[0]:.0f}, {tip[1]:.0f}) px' if tip else '尖端  未确认'
                draw.text((x+12,y+254),note,font=fonts[2],fill='#e9f0f4')
            n=sum(c['tip'] is not None for c in z['cases'].values())
            info={'shared':'计入比较 · 八个 ROI 均覆盖旧 A 对照点','unknown':'跳过比较 · 旧 A 无对照点','outside':'跳过比较 · 对照点位于部分 ROI 外'}[z['coverage']]
            draw.text((28,1025),f'{info}     |     当前确认 {n}/8 组     |     坐标为原图像素',font=fonts[2],fill='#c2d5df')
            canvas.save(frames/f'{frame:04d}_{file.stem}.png',compress_level=2)
            enc.stdin.write(canvas.tobytes())
        enc.stdin.close()
        if enc.wait():raise RuntimeError('video encoding')
    pngs=sorted(frames.glob('*.png'))
    assert len(pngs)==len(records)
    with ZipFile(folder/'frames.zip','w',ZIP_STORED) as archive:
        for p in pngs:
            with Image.open(p) as im:
                assert im.size==(1920,1080);im.verify()
            archive.write(p,p.name)
    with ZipFile(folder/'frames.zip') as z:assert z.testzip() is None
    probe=subprocess.check_output([str(ROOT/'third_party/ffmpeg/ffprobe.exe'),'-v','error','-select_streams','v:0','-count_frames',
        '-show_entries','stream=width,height,r_frame_rate,nb_read_frames','-of','json',str(path)])
    meta=json.loads(probe)['streams'][0]
    assert int(meta['nb_read_frames'])==len(records) and meta['r_frame_rate']=='15/1'
    api.save(folder/'media.json',dict(**meta,png=len(pngs),crop=crop))
    print('verified media',group,len(records),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('groups',nargs='+',choices=NAMES);parser.add_argument('--summary-only',action='store_true')
    args=parser.parse_args()
    for group in args.groups:
        records=api.load(OUT/group/'records.jsonl')
        print(assess(group,records),flush=True)
        if not args.summary_only:render(group,records)
