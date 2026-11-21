"""Render original and eight paired runs in one fixed original-pixel view."""
from pathlib import Path
import csv
import json
import subprocess
from zipfile import ZipFile, ZIP_STORED
from PIL import Image, ImageDraw, ImageFont
from ct3_roi_replay import CASES,OUT,ROOT,inventory,api

names=['实测 P1/P2','双点右移 5 px','双点右移 10 px','双点右移 20 px',
       '双点左移 10 px','双点上移 10 px','间距 × 0.75','间距 × 1.35']
def font(n):return ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
title,label,small=font(31),font(21),font(17)
ink='#e9f0f4';muted='#b2c6d0'
def main():
    paths=api.load(OUT/'paths.jsonl'); ds=inventory()['ct3'][1]
    data={(int(r['frame']),r['case']):r for r in csv.DictReader((OUT/'per_frame.csv').open(encoding='utf-8-sig'))}
    tips=[p for z in paths for c in z['cases'].values() for p in ([c['tip']] if c['tip'] else [])+c['anchors']]
    # Compute a single shared display crop for the series; never use it in detection.
    x0=int(min(p[0] for p in tips))-26;y0=int(min(p[1] for p in tips))-16
    x1=int(max(p[0] for p in tips))+28;y1=int(max(p[1] for p in tips))+16
    zoom=min(564/(x1-x0),194/(y1-y0))
    size=(round(zoom*(x1-x0)),round(zoom*(y1-y0)))
    frames=OUT/'frames';frames.mkdir(exist_ok=True)
    video=OUT/'CT3_ROI_尖端对比.mp4'
    cmd=[str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24',
         '-s','1920x1080','-r','15','-i','-','-an','-c:v','libx264','-pix_fmt','yuv420p','-crf','16',
         '-preset','veryfast','-movflags','+faststart',str(video)]
    with subprocess.Popen(cmd,stdin=subprocess.PIPE) as enc:
        for z,(path,_,_) in zip(paths,ds,strict=True):
            i=z['frame'];gray=api.read(path)
            base=Image.fromarray(gray[y0:y1,x0:x1]).resize(size,Image.Resampling.BILINEAR).convert('RGB')
            canvas=Image.new('RGB',(1920,1080),'#101b24');d=ImageDraw.Draw(canvas)
            d.text((28,16),'CT3 白色喷漆   /   八组选点的尖端复测',font=title,fill=ink)
            d.text((1410,25),f"第 {i:03d} / 136 帧     {path.name}",font=label,fill=ink)
            d.text((30,66),'相同视野，坐标为当前原图 px　　橙线 / 黄圈：新版路径与尖端　　紫色叉：该组选点的旧 A 尖端　　蓝点：P1、P2',font=small,fill=muted)
            for j,key in enumerate(['raw',*CASES]):
                x=18+(j%3)*630;y=110+(j//3)*300
                d.rounded_rectangle((x,y,x+618,y+288),radius=5,fill='#1d2c37')
                d.text((x+12,y+8),'原图局部' if j==0 else names[j-1],font=label,fill=ink)
                ox=x+(618-size[0])//2;oy=y+44
                canvas.paste(base,(ox,oy))
                def xy(p):return (ox+(p[0]-x0+.5)*size[0]/(x1-x0),oy+(p[1]-y0+.5)*size[1]/(y1-y0))
                if key=='raw':
                    note='同一张原图，未经检测线覆盖'
                else:
                    c=z['cases'][key];r=data[i,key];tip=c['tip']
                    for pt in c['anchors']:
                        a,b=xy(pt);d.ellipse((a-3,b-3,a+3,b+3),outline='#219ade',width=2)
                    if len(c['path'])>=2:d.line([xy(p) for p in c['path']],fill='#fc6b37',width=2)
                    if r['old_tip_valid']=='1':
                        a,b=xy((float(r['old_tip_x']),float(r['old_tip_y'])))
                        d.line((a-5,b-5,a+5,b+5),fill='#994bdb',width=2);d.line((a-5,b+5,a+5,b-5),fill='#994bdb',width=2)
                    if tip:
                        a,b=xy(tip);d.ellipse((a-6,b-6,a+6,b+6),outline='#ffca2d',width=2)
                    note=f"新尖端  ({tip[0]:.0f}, {tip[1]:.0f})" if tip else '新尖端  未确认'
                    note+='    |    旧 A '+('已确认' if r['old_tip_valid']=='1' else '未确认')
                d.text((x+12,y+253),note,font=small,fill=ink)
            n=sum(c['tip'] is not None for c in z['cases'].values())
            info='原选点旧 A 尖端落入全部 8 个实际 ROI' if data[i,'measured']['all_cover_proxy']=='True' else '旧 A 原选点无尖端，覆盖未知'
            d.text((28,1027),f'新版输出 {n}/8 组     |     {info}     |     真实尖端未经人工标注',font=small,fill=muted)
            canvas.save(frames/f"{i:03d}_{path.stem}.png",compress_level=2)
            enc.stdin.write(canvas.tobytes())
        enc.stdin.close()
        if enc.wait()!=0:raise RuntimeError('video encoding failed')
    images=sorted(frames.glob('*.png'))
    assert len(images)==len(ds)
    with ZipFile(OUT/'CT3_逐帧对比图.zip','w',ZIP_STORED) as archive:
        for p in images:
            with Image.open(p) as im:im.verify()
            archive.write(p,p.name)
    probe=subprocess.check_output([str(ROOT/'third_party/ffmpeg/ffprobe.exe'),'-v','error','-select_streams','v',
        '-show_entries','stream=nb_frames,width,height,r_frame_rate','-of','json',str(video)])
    meta=json.loads(probe)['streams'][0];assert int(meta['nb_frames'])==len(ds)
    print(meta)
if __name__=='__main__':main()
