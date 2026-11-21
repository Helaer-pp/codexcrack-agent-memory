"""Optional full-sequence viewing copies from completed GT-free evidence PNGs."""
import argparse,subprocess,concurrent.futures,io,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
from grayref_simplified_evidence_v0.common import *

def one(job):
    run,group=job;run=Path(run);out=run/'videos';out.mkdir(exist_ok=True);video=out/(group+'.mp4');qa=out/(group+'_qa.json')
    if qa.exists():assert sha(video)==get(qa)['sha256'];return get(qa)
    if video.exists():raise RuntimeError('Unsealed existing video; refusing overwrite')
    ffmpeg=ROOT/'third_party/ffmpeg/ffmpeg.exe';width,height=1600,1000
    cmd=[str(ffmpeg),'-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}','-r','6','-i','pipe:0','-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(video)]
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
    with open(out/(group+'_encode.log'),'wb') as log:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        for frame in range(1,GROUPS[group]+1):
            d=run/'galleries'/group/str(frame);manifest=get(d/'frame_manifest.json');r=readgz(d/'result.json.gz');result=next(x for x in r['results'] if x['mode']=='C_FUSION_RAW')
            im=Image.new('RGB',(width,height),'#0d1c28');draw=ImageDraw.Draw(im)
            role='开发组' if group in DEV else '已曝光验证组（不调参）'
            draw.text((18,9),f'{group}  {frame}/{GROUPS[group]}  {role}  C_FUSION_RAW  {result["output_state"]}',font=font,fill='white')
            draw.text((18,43),'绿色：观测路径；橙色：推断桥接；紫色：候选尖端（可能不确定）。无人工GT参与。播放6帧/秒不是算法速度。',font=small,fill='#b5d2df')
            panels=[('overlay_path_tip.png',(10,74,1580,400)),('gray_surface_raw.png',(10,490,780,480)),('roi_difference_signed.png',(800,490,790,480))]
            for name,(x,y,w,h) in panels:
                assert sha(d/name)==manifest['files'][name]['sha256']
                with Image.open(d/name) as source:pic=ImageOps.contain(source.convert('RGB'),(w,h),Image.Resampling.LANCZOS)
                im.paste(pic,(x+(w-pic.width)//2,y+(h-pic.height)//2))
            proc.stdin.write(im.tobytes())
        proc.stdin.close();code=proc.wait()
        if code:raise RuntimeError(f'Video encoder failed {group}')
    probe=subprocess.run([str(ffmpeg),'-v','error','-i',str(video),'-f','null','-','-progress','pipe:1'],capture_output=True,text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert probe.returncode==0;frames=[int(s.split('=')[1]) for s in probe.stdout.splitlines() if s.startswith('frame=')];assert frames and frames[-1]==GROUPS[group]
    result=dict(group=group,frames=frames[-1],fps=6,full_decode=True,sha256=sha(video),source='per-frame GT-free sealed PNGs; no detector rerun',role='DEVELOPMENT' if group in DEV else 'EXPOSED_REGRESSION',display_downsample_only=True)
    put(qa,result);return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--development-only',action='store_true');a=p.parse_args();run=Path(a.run)
    if a.development_only:
        assert (run/'inference_frozen_development.json').exists() and (run/'evaluation_complete_development.json').exists()
        groups=[g for g in GROUPS if g in DEV]
    else:
        assert (run/'completion_seal.json').exists();groups=list(GROUPS)
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(one,[(str(run),g) for g in groups]))
    if a.development_only:
        put(run/'videos/development_video_integrity.json',dict(script_sha=sha(__file__),frames=sum(r['frames'] for r in results),groups=results,scope='DEVELOPMENT_ONLY_PARTIAL_DELIVERY'))
        print(json.dumps(results,ensure_ascii=False,indent=2));return
    body='<meta charset="utf-8"><title>六组完整序列视频</title><style>body{font:18px sans-serif;background:#132431;color:white;margin:24px}a{color:#8edaff}video{width:100%;max-width:1280px}</style><h1>六组完整逐帧视频</h1><p>默认C_FUSION_RAW；完整图册保留全分辨率数值与九模式切换。每秒播放6帧，与推理性能无关。</p><a href="../galleries/index.html">完整逐帧图册</a>'
    for g in ['group_c','three_point_bend','group_a','ct2','group_h','ct3']:
        body+=f'<h2>{g} — {"DEVELOPMENT" if g in DEV else "EXPOSED_REGRESSION"}</h2><video controls preload="none" src="{g}.mp4"></video>'
    write_bytes(run/'videos/index.html',body.encode('utf-8'));put(run/'videos/video_integrity.json',dict(script_sha=sha(__file__),frames=sum(r['frames'] for r in results),groups=results));print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
