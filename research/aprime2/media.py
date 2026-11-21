"""Scientific diagnostic rendering, original gray pixels and coordinate overlays."""
from common import *
from PIL import Image,ImageDraw,ImageFont
import subprocess,shutil
FONT='C:/Windows/Fonts/msyh.ttc'
FONTS={n:ImageFont.truetype(FONT,n) for n in (17,20,24,30)}
COLORS=dict(bg=(10,23,33),text=(230,235,240),muted=(171,187,198),red=(255,75,75),yellow=(255,215,30),orange=(255,155,40),cyan=(40,210,230),green=(50,220,120))
W,H=1600,900

def panel(im,rect,bounds=None):
    x,y,w,h=rect
    if bounds is None:bounds=[0,0,im.shape[1],im.shape[0]]
    x0,y0,x1,y1=bounds;crop=im[y0:y1,x0:x1]
    scale=min(w/crop.shape[1],h/crop.shape[0]);nw,nh=max(1,round(crop.shape[1]*scale)),max(1,round(crop.shape[0]*scale))
    small=cv2.resize(crop,(nw,nh),interpolation=cv2.INTER_AREA if scale<1 else cv2.INTER_CUBIC)
    left=x+(w-nw)//2;top=y+(h-nh)//2
    return Image.fromarray(small).convert('RGB'),(left,top),lambda p:(left+(p[0]-x0)*scale,top+(p[1]-y0)*scale)

def render(z,dev=False):
    im=read(z['input_image']);a=z['A']['formal'];p=np.asarray(a['raw_path'],float).reshape(-1,2);pp=np.asarray(z['points'])
    tip=a['tip'];canvas=Image.new('RGB',(W,H),COLORS['bg']);d=ImageDraw.Draw(canvas)
    group=z.get('group',z.get('case_id',''));fid=z['frame_id']
    d.text((20,10),f"A′2 研究诊断 | {group} | 帧 {fid}",font=FONTS[30],fill=COLORS['text'])
    d.text((20,52),'冻结 A 原样保留；橙色为停止假设，不代表已确认裂纹。真实资料无物理 GT。' if not dev else '受控 DEV / 已曝光；GT 仅用于离线评估，不能作为独立 TEST。',font=FONTS[20],fill=COLORS['muted'])
    content=np.vstack([pp,p]) if len(p) else pp;pad=max(30,np.linalg.norm(pp[1]-pp[0])*.15)
    bounds=[max(0,int(content[:,0].min()-pad)),max(0,int(content[:,1].min()-pad)),min(im.shape[1],int(content[:,0].max()+pad)+1),min(im.shape[0],int(content[:,1].max()+pad)+1)]
    rects=[(15,130,510,570),(545,130,510,570),(1075,130,510,570)]
    maps=[]
    for k,rect in enumerate(rects):
        tile,pos,fun=panel(im,rect,None if k==0 else bounds);canvas.paste(tile,pos);maps.append(fun)
        d.text((rect[0],98),['原图完整视野','A 路径 / 原始尖端','候选 + 可信参考有效域'][k],font=FONTS[24],fill=COLORS['text'])
    d=ImageDraw.Draw(canvas)
    for k in (1,2):
        fun=maps[k]
        if len(p)>1:d.line([fun(q) for q in p],fill=COLORS['red'],width=2)
        for j,q in enumerate(pp):
            x,y=fun(q);d.ellipse((x-4,y-4,x+4,y+4),outline=COLORS['cyan'],width=2);d.text((x+5,y),f'P{j+1}',font=FONTS[17],fill=COLORS['cyan'])
        if a['confirmed_tip']:
            x,y=fun(tip);d.ellipse((x-6,y-6,x+6,y+6),outline=COLORS['yellow'],width=2)
    fun=maps[2]
    for q in z.get('queries',[]):
        if q['reg']['local_supported']:
            hull=[fun(t) for t in q['reg']['polygon']]
            if len(hull)>2:d.line(hull+[hull[0]],fill=(55,145,150),width=1)
    for c in z.get('pool',[]):
        if c['A_original_bitwise']:continue
        x,y=fun(c['xy']);d.ellipse((x-4,y-4,x+4,y+4),outline=COLORS['orange'],width=2)
        d.text((x+4,y-15),str(c['candidate_id']),font=FONTS[17],fill=COLORS['orange'])
    decision=z.get('Aprime2',{})
    if decision.get('decision')=='RESEARCH_RELOCATED':
        x,y=fun(decision['tip']);d.ellipse((x-8,y-8,x+8,y+8),outline=COLORS['green'],width=3)
    if dev and z['GT']['observable']:
        for fun in maps[1:]:
            x,y=fun(z['GT']['tip']);d.line([(x-8,y),(x+8,y)],fill=(240,100,255),width=2);d.line([(x,y-8),(x,y+8)],fill=(240,100,255),width=2)
    tiptext=f"({tip[0]:.2f}, {tip[1]:.2f}) px" if a['confirmed_tip'] else 'null / 无有效尖端'
    d.text((20,715),f'A 尖端：{tiptext}    候选数：{len(z.get("pool",[]))}    停止：{z["A"]["native"]["stop_reason"]}',font=FONTS[20],fill=COLORS['yellow'])
    st=z.get('states',{});coverage=st.get('coverage',z.get('interval_coverage',0))
    msg=decision.get('decision','A_UNCHANGED / 真实参考泛化门槛未通过')
    d.text((20,748),f'路径参考可观察覆盖：{100*coverage:.1f}%    研究状态：{msg}',font=FONTS[20],fill=COLORS['text'])
    if dev:
        d.text((20,778),'黄圈=A 尖端；绿圈=研究改动端点；紫十字=程序 GT；青多边形=参考有效域（不是整条路径都有效）。',font=FONTS[17],fill=COLORS['muted'])
    ev=z.get('path_evidence',[])
    if len(ev)>1:
        x0,y0,ww,hh=25,800,1540,65;end=max(e['arc_s'] for e in ev);m=max(10,max(abs(e[k]) for e in ev for k in ['Vcur','Vref','DeltaV']))
        for key,color in [('Vcur',COLORS['text']),('Vref',COLORS['cyan']),('DeltaV',COLORS['orange'])]:
            coords=[(x0+e['arc_s']/max(1,end)*ww,y0+hh/2-e[key]/m*hh/2) for e in ev]
            d.line(coords,fill=color,width=1)
        d.text((20,872),'剖面：白=当前暗谷，青=参考暗谷，橙=差值；未验证区的数值仅诊断。视频 15 FPS 是播放速度。',font=FONTS[17],fill=COLORS['muted'])
    return np.asarray(canvas)

def video_writer(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    log=path.with_suffix('.ffmpeg.log').open('w')
    p=subprocess.Popen([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','15','-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],stdin=subprocess.PIPE,stderr=log)
    return p,log

def execute():
    media=RUN/'08_media';inventory=[];current=None;writer=None;log=None;count=0
    key={'group_x':{51,473},'ct2':{6,18,84},'three_point_bend':{0,100,300,519},'group_a':{0,100,550},'group_c':{0,170,561},'group_h':{0,200,409}}
    for z in jl(RUN/'04_reference_validity/real_predictions.jsonl'):
        g=z['group']
        if g!=current:
            if writer:writer.stdin.close();assert writer.wait()==0;log.close();inventory.append(dict(kind='real',group=current,frames=count,video=str(video.relative_to(RUN))))
            current=g;count=0;video=media/f'videos/{g}_A_AP2_diagnostic.mp4';writer,log=video_writer(video)
        frame=render(z);writer.stdin.write(frame.tobytes());count+=1
        fn=media/f'per_frame/{g}/{z["frame_id"]:04d}.png';put(fn,cv2.cvtColor(frame,cv2.COLOR_RGB2BGR))
        if z['frame_id'] in key.get(g,set()):
            dest=media/f'key_cases/{g}_{z["frame_id"]:04d}.png';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(fn,dest)
        if count%100==0:print('MEDIA',g,count,flush=True)
    if writer:writer.stdin.close();assert writer.wait()==0;log.close();inventory.append(dict(kind='real',group=current,frames=count,video=str(video.relative_to(RUN))))
    writer,log=video_writer(media/'videos/DEV_v2_diagnostic.mp4');count=0
    for z in jl(RUN/'05_DEV/full_v2/decision_predictions.jsonl'):
        frame=render(z,True);writer.stdin.write(frame.tobytes());count+=1
        fn=media/f'DEV_per_frame/{z["case_id"]}_{z["frame_id"]}.png';put(fn,cv2.cvtColor(frame,cv2.COLOR_RGB2BGR))
        if z['frame_id']==2 and (z['case_id'].startswith('DEV_0_1_') or z['Aprime2']['decision']=='RESEARCH_RELOCATED'):
            shutil.copyfile(fn,media/f'key_cases/{z["case_id"]}_{z["frame_id"]}.png')
    writer.stdin.close();assert writer.wait()==0;log.close();inventory.append(dict(kind='DEV',frames=count,video='08_media/videos/DEV_v2_diagnostic.mp4'))
    csvout(media/'inventory.csv',inventory)
    print('MEDIA_DONE',inventory,flush=True)

if __name__=='__main__':execute()
