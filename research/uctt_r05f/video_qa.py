from common import *
import subprocess,cv2,numpy as np
from PIL import Image,ImageDraw

def main():
 path=OUT/'R05F_S1_Results.mp4';dest=OUT/'galleries/video_qa';dest.mkdir(exist_ok=True)
 metadata=json.loads(subprocess.check_output([str(ROOT/'third_party/ffmpeg/ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(path)],text=True));write(dest/'metadata.json',metadata)
 stream=next(x for x in metadata['streams'] if x['codec_type']=='video');assert stream['codec_name']=='h264' and stream['width']==1600 and stream['height']==960 and float(metadata['format']['duration'])>=160
 result=subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-v','error','-i',str(path),'-f','null','NUL'],capture_output=True,text=True);assert result.returncode==0 and not result.stderr,result.stderr
 capture=cv2.VideoCapture(str(path));sheet=Image.new('RGB',(1600,960),'#172333')
 for i,second in enumerate([0,82,162,178]):
  capture.set(cv2.CAP_PROP_POS_MSEC,second*1000);ok,im=capture.read();assert ok
  pic=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB));pic.save(dest/f't{second}.jpg',quality=90);sheet.paste(pic.resize((800,480)),((i%2)*800,(i//2)*480))
 capture.release();sheet.save(dest/'contact_sheet.jpg',quality=94)
 write(dest/'verification.json',dict(full_decode='PASS',samples_seconds=[0,82,162,178],codec=stream['codec_name'],width=stream['width'],height=stream['height'],duration=float(metadata['format']['duration']),frames=int(stream['nb_frames']),all80_development_panels=True,playback_is_not_algorithm_throughput=True))
 print('VIDEO VERIFIED',metadata['format']['duration'],stream['nb_frames'],flush=True)
if __name__=='__main__':main()
