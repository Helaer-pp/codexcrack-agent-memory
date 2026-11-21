from common import *
from media import render,video_writer,FONTS,COLORS,panel
from PIL import Image,ImageDraw
import shutil

def execute():
    media=RUN/'08_media';writer,log=video_writer(media/'videos/DEV_v3_prefilter_diagnostic.mp4');count=0;pairs={}
    for z in jl(RUN/'05_DEV/full_v3/decision_predictions.jsonl'):
        frame=render(z,True);writer.stdin.write(frame.tobytes());count+=1
        fn=media/f'DEV_v3_per_frame/{z["case_id"]}_{z["frame_id"]}.png';put(fn,cv2.cvtColor(frame,cv2.COLOR_RGB2BGR))
        if z['frame_id']==2 and (z['metrics']['changed'] or z['case_id'].startswith('DEV_0_1_')):
            shutil.copyfile(fn,media/f'key_cases/v3_{z["case_id"]}_{z["frame_id"]}.png')
        if z['pair_id'] and z['frame_id']==2:pairs.setdefault(z['pair_id'],{})[z['family']]=z
    writer.stdin.close();assert writer.wait()==0;log.close()
    for pid,qq in pairs.items():
        a,b=qq['STRONG_FALSE_TAIL'],qq['TRUE_LONG_MATCHED'];assert a['image_sha']==b['image_sha']
        canvas=Image.new('RGB',(1600,900),COLORS['bg']);d=ImageDraw.Draw(canvas)
        d.text((20,15),f'同一当前图 / 不同参考：{pid}（已曝光 DEV）',font=FONTS[30],fill=COLORS['text'])
        d.text((20,62),'当前图 SHA 完全相同；程序 GT 不同，仅供离线评价。不能用当前灰度独自确定裂纹归属。',font=FONTS[20],fill=COLORS['muted'])
        for j,(path,label) in enumerate([(a['reference_image'],'短裂纹假设的参考（已有表面尾线）'),(b['reference_image'],'真长裂纹假设的参考'),(a['input_image'],'两者共享的当前图（原始灰度）')]):
            im=read(path);tile,pos,fun=panel(im,(20+530*j,160,510,570));canvas.paste(tile,pos)
            d.text((20+530*j,120),label,font=FONTS[20],fill=COLORS['text'])
        d.text((20,760),f"短端 GT：{np.round(a['GT']['tip'],2).tolist()}  A误差={a['A_error']:.2f}px  研究误差={a['metrics']['Aprime2_error']:.2f}px",font=FONTS[24],fill=COLORS['yellow'])
        d.text((20,805),f"长端 GT：{np.round(b['GT']['tip'],2).tolist()}  A误差={b['A_error']:.2f}px  研究误差={b['metrics']['Aprime2_error']:.2f}px",font=FONTS[24],fill=COLORS['cyan'])
        put(media/f'key_cases/{pid}_shared_current.png',cv2.cvtColor(np.asarray(canvas),cv2.COLOR_RGB2BGR))
    save(media/'extra_inventory.json',dict(video='08_media/videos/DEV_v3_prefilter_diagnostic.mp4',frames=count,pair_images=len(pairs)))
    print('EXTRA_MEDIA',count,len(pairs),flush=True)

if __name__=='__main__':execute()
