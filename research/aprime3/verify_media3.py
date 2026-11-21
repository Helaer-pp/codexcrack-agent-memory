from common3 import *
from PIL import Image
records=[];count=0
for kind in ['real','exposed','new']:
 for r in rows(RUN/f'07_media/{kind}_png_inventory.csv'):
  p=RUN/r['path'];assert sha(p)==r['sha256']
  with Image.open(p) as im:assert im.size==(1600,900);im.verify()
  count+=1
 for r in rows(RUN/f'07_media/{kind}_video_inventory.csv'):
  p=RUN/r['video'];result=subprocess.run([str(ROOT/'third_party/ffmpeg/ffprobe.exe'),'-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,r_frame_rate,duration','-of','json',str(p)],capture_output=True,check=True)
  s=json.loads(result.stdout)['streams'][0];assert int(s['nb_frames'])==int(r['frames']);assert s['r_frame_rate']=='15/1';assert [s['width'],s['height']]==[1600,900]
  decoded=subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-v','error','-threads','2','-i',str(p),'-f','null','-'],capture_output=True)
  log=RUN/f'07_media/{r["group"]}_decode.log';log.write_bytes(decoded.stderr);assert decoded.returncode==0 and not decoded.stderr
  records.append(dict(group=r['group'],frames=int(r['frames']),**s,decode_pass=True,sha256=sha(p)));print('VERIFIED VIDEO',r['group'],s['nb_frames'],flush=True)
assert count==4493 and len(records)==8
csvout(RUN/'07_media/verified_videos.csv',records);save(RUN/'07_media/verification.json',dict(png_verified=count,videos_full_decode_verified=len(records),passed=True));print('MEDIA VERIFIED',count,flush=True)
