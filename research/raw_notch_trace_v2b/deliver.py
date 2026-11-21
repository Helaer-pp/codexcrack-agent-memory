"""Verify every comparison frame, encode each sequence, and build local navigation."""
import argparse
import json
import subprocess
from pathlib import Path
import cv2
from experiment import ROOT,GROUPS,read,save,sha


def deliver(run):
    groups={**GROUPS['dev'],**GROUPS['locked']}
    videos=[]
    for split in GROUPS:
        file=run/(split+'.jsonl')
        assert sha(file)==read(run/(split+'_seal.json'))['predictions']
        for r in map(json.loads,file.read_text().splitlines()):
            image=run/'frames'/r['group']/(str(r['frame'])+'.jpg')
            assert sha(image)==r['card_sha'] and cv2.imread(str(image)).shape[:2]==(490,1280)
    for g,count in groups.items():
        movie=run/(g+'.mp4')
        subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-loglevel','error','-n','-framerate','10',
                        '-start_number','1','-i',str(run/'frames'/g/'%d.jpg'),'-frames:v',str(count),'-c:v','libx264',
                        '-pix_fmt','yuv420p','-threads','3','-crf','19','-movflags','+faststart',str(movie)],check=True)
        cap=cv2.VideoCapture(str(movie))
        n=0
        while True:
            ok,img=cap.read()
            if not ok:break
            assert img.shape[:2]==(490,1280)
            n+=1
        cap.release()
        assert n==count
        videos.append(dict(group=g,frames=n,sha=sha(movie)))
    save(run/'verified_videos.json',videos)
    html="""<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>从缺口追踪裂纹 · 逐帧对比</title><style>body{background:#191919;color:#eee;font:17px system-ui;margin:2vw}select,input,button{font:inherit}img{width:min(100%,1440px);display:block;margin:1em 0}a{color:#91dbff}label,button{margin-right:.6em}</style>
<h1>从缺口追踪裂纹</h1><label>实验组 <select id="group"><option value="group_a">GROUP_A</option><option value="three_point_bend">三点弯</option><option value="group_c">验证组C</option></select></label>
<button id="prev">上一帧</button><label>帧号 <input id="num" type="number" min="1" value="1"></label><button id="next">下一帧</button>
<span id="total"></span> <a id="movie">整组视频</a><p>左侧为原图，右侧为同坐标结果。蓝十字为缺口起点，绿色为实际观测路径，黄点为短间断后的首个观测点，红圈为正式尖端。</p>
<img id="picture" alt="原图与检测结果局部对比"><a id="jpg">打开本帧原尺寸对比图</a>
<script>const counts={group_a:551,three_point_bend:520,group_c:562};const el=id=>document.getElementById(id);
const g=el('group'),n=el('num');const params=new URLSearchParams(location.search);
if(Object.hasOwn(counts,params.get('group')))g.value=params.get('group');n.value=Number(params.get('frame'))||1;
function show(){n.max=counts[g.value];n.value=Math.max(1,Math.min(Number(n.max),Math.trunc(Number(n.value))||1));el('picture').src=el('jpg').href='frames/'+g.value+'/'+n.value+'.jpg';el('movie').href=g.value+'.mp4';el('total').textContent='/ '+n.max;el('prev').disabled=n.value==1;el('next').disabled=n.value==n.max}
g.onchange=()=>{n.value=1;show()};n.onchange=show;el('prev').onclick=()=>{n.value--;show()};el('next').onclick=()=>{n.value++;show()};show()</script></html>"""
    (run/'index.html').write_text(html,encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);deliver(p.parse_args().run)

