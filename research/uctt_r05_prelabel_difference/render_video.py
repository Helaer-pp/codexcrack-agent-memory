"""Real diagnostics slideshow; playback speed is not algorithm throughput."""
import subprocess
from PIL import Image,ImageDraw,ImageFont
from common import *
def title(lines):
 im=Image.new('RGB',(1600,980),'#152536');d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',36)
 for i,line in enumerate(lines):d.text((70,90+i*95),line,fill='#e8edf3',font=font)
 return im
def main():
 dest=OUT/'R05_Reference_Difference_Results.mp4';ff=ROOT/'third_party/ffmpeg/ffmpeg.exe';fps=5;manifest=rows(PACKAGE/'selection_manifest.csv')
 intro=title(['R05-PRE：140张原图已整理为 LabelMe 待标注包','7组 × 20张；原图字节不变，未预填任何尖端/路径标签','以下为同帧固定参考 / 严格因果历史参考差分诊断','包含可用配对，也保留配准失败和有效区域不足','紫色区域：不可用或过渡带；失败不计作零残差','这些是算法诊断，不是人工真值；真实尖端准确率 N/A','视频每例2秒，播放速度不等于算法处理速度'])
 end=title(['本轮结论：标注包可用，生产算法未改动','历史参考差分价值：INCONCLUSIVE','因果性 / 同ROI公共掩膜 / 缺失处理检查通过','没有人工标签，不能称真实尖端更准或噪点已解决','请在 images/组名 内标注并保存同名 JSON','完整原图、中文说明、清单和校验脚本都在标注包中'])
 intro.save(OUT/'video_intro.png');end.save(OUT/'video_conclusion.png');source=[(intro,5)]+[(OUT/'diagnostics'/f"{r['dataset_id']}__frame_{int(r['frame_id']):06d}.jpg",2) for r in manifest]+[(end,5)]
 cmd=[str(ff),'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1600x980','-r',str(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)]
 count=0
 with (OUT/'video_encode.log').open('wb') as log:
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
  try:
   for item,seconds in source:
    im=Image.open(item).convert('RGB') if isinstance(item,Path) else item;data=im.tobytes()
    for _ in range(seconds*fps):proc.stdin.write(data);count+=1
   proc.stdin.close();assert proc.wait()==0
  except BaseException:proc.kill();raise
 cap=cv2.VideoCapture(str(dest));assert cap.isOpened();assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT))==count;assert (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))==(1600,980);cap.release()
 decoded=subprocess.run([str(ff),'-v','error','-i',str(dest),'-f','null','NUL'],capture_output=True);assert decoded.returncode==0 and not decoded.stderr,decoded.stderr
 write(OUT/'video_qa.json',dict(status='PASS',codec='H264',width=1600,height=980,fps=fps,frames=count,seconds=count/fps,real_cases=len(manifest),full_decode='PASS',sha256=sha(dest),scope='research diagnostic ROI panels, not annotation originals or native speed'))
 print('VIDEO READY',dest,count/fps,flush=True)
if __name__=='__main__':main()
