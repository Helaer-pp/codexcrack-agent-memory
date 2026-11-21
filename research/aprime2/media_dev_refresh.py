from common import *
from media import render,video_writer
import shutil
media=RUN/'08_media';writer,log=video_writer(media/'videos/DEV_v2_diagnostic.mp4');n=0
for z in jl(RUN/'05_DEV/full_v2/decision_predictions.jsonl'):
    frame=render(z,True);writer.stdin.write(frame.tobytes());n+=1
    fn=media/f'DEV_per_frame/{z["case_id"]}_{z["frame_id"]}.png';put(fn,cv2.cvtColor(frame,cv2.COLOR_RGB2BGR))
    if z['frame_id']==2 and (z['case_id'].startswith('DEV_0_1_') or z['Aprime2']['decision']=='RESEARCH_RELOCATED'):
        shutil.copyfile(fn,media/f'key_cases/{z["case_id"]}_{z["frame_id"]}.png')
writer.stdin.close();assert writer.wait()==0;log.close();print('DEV REFRESH',n,flush=True)
