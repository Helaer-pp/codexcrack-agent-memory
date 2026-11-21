from media import *
import re,zipfile
def main():
 summary=rows(OUT/'experiments/comparison_by_group.csv');lookup={(r['variant'],r['dataset_id']):r for r in summary};b=lookup['E0_BEAM','ALL'];a=lookup['E1_BEAM','ALL'];images=OUT/'galleries/images';slides=[]
 texts=[('R05G：实际研发结果',[
  '已实现：C++ 当前图像方向横截面逐步追踪、有限束、缺失与重捕获。',
  'G1 基本机制 PASS；G2 归属/终止 FAIL；G3 首次锁定安全 FAIL。',
  f'诊断短起点：路径覆盖10px约 {float(b["mean_full_path_coverage10"])*100:.1f}%，但路径精度仅 {float(b["mean_visible_path_precision10"])*100:.1f}%。',
  f'同样76帧，诊断束暂定端点≤10px：{b["tentative_hit10"]}/76；全自动束：{a["tentative_hit10"]}/76。',
  '所有新分支正式 observed=0：身份功能未通过，不是全拒绝证明了安全。',
  '没有替换生产；验证组C、三点弯不准入；排除组X排除；标注不训练、不调参。']),
 ('如何看这80帧证据',[
  '6面板：当前原图/人工对照、旧A与B0、AUTO贪心/束、短起点贪心/束。',
  '紫色：离线人工路径/尖端。青绿：当前真实观测。橙色虚线：推断缺口。',
  '黄色：实际访问横截面。蓝色方块：起点。红叉：首次离轨诊断位置。',
  'AUTO贪心首轮允许最多3个起源候选，此后宽1；E0为严格单起点宽1。',
  '每张停留3秒，播放器可暂停。完整1565帧另有视频及逐帧JPG。',
  'Ryzen7950X处理P95约17.33ms，但353帧搜索不完整；i7未验证。',
  'JSON调试导出、文件读取另计；本视频速度不表示算法处理速度。'])]
 for i,(title,body) in enumerate(texts):
  card=Image.new('RGB',(1800,1330),'#111d2b');d=ImageDraw.Draw(card);titlefont=ImageFont.truetype(FONTPATH,52);bodyfont=ImageFont.truetype(FONTPATH,30);lines(d,(70,70),title,titlefont)
  for j,text in enumerate(body):lines(d,(70,230+j*120),text,bodyfont)
  path=images/f'video_intro_{i}.jpg';card.save(path,quality=94);slides.append((path,8))
 for r in rows(OUT/'selection.csv'):slides.append((images/f'{r["dataset_id"]}_{int(r["frame_id"]):06d}.jpg',3))
 weak_jpeg=images/'group_h78_raw_pixels_video.jpg'
 with Image.open(images/'group_h78_raw_pixels.png') as weak:
  weak=weak.convert('RGB');weak.thumbnail((1800,1330),Image.Resampling.LANCZOS);padded=Image.new('RGB',(1800,1330),'#111d2b');padded.paste(weak,((1800-weak.width)//2,(1330-weak.height)//2));padded.save(weak_jpeg,quality=97)
 slides.append((weak_jpeg,8))
 concat=OUT/'galleries/selected_video_frames.txt';concat.write_text(''.join("file '"+str(path).replace('\\','/')+"'\nduration "+str(duration)+'\n' for path,duration in slides)+"file '"+str(slides[-1][0]).replace('\\','/')+"'\n",encoding='utf8')
 cmd=[str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-y','-hide_banner','-loglevel','warning','-f','concat','-safe','0','-i',str(concat),'-vf','scale=1800:1330:force_original_aspect_ratio=decrease,pad=1800:1330:(ow-iw)/2:(oh-ih)/2,fps=10','-t',str(sum(duration for _,duration in slides)),'-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'R05G_Selected_Evidence.mp4')]
 with (OUT/'logs/selected_video_encode.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
 archive=OUT/'R05G_Local_Comparisons.zip';manifest=rows(OUT/'galleries/render_manifest.csv');assert len(manifest)==1565
 if not archive.exists():
  with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:
   for r in manifest:z.write(OUT/r['path'],r['path'].removeprefix('galleries/'))
   z.write(OUT/'galleries/render_manifest.csv','render_manifest.csv');z.writestr('README.txt','1565帧裂纹局部对比图。每帧均来自实际原图及原生回放。\n青绿轨迹为未确认研究输出，不能当生产尖端。\n80帧有离线人工标注，其余帧无GT评分；完整报告及80选帧多变体图册见同一run目录。\nrender_manifest.csv给出来源SHA256和原图/显示坐标矩阵。')
 with zipfile.ZipFile(archive) as z:assert len([x for x in z.namelist() if x.endswith('.jpg')])==1565;assert z.testzip() is None
 qa=[]
 for name in ['R05G_All_Development_Frames.mp4','R05G_Selected_Evidence.mp4']:
  path=OUT/name;probe=subprocess.run([str(ROOT/'third_party/ffmpeg/ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,check=True);info=json.loads(probe.stdout);video=next(x for x in info['streams'] if x['codec_type']=='video');decode=subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-hide_banner','-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True);assert decode.returncode==0 and not decode.stderr.strip(),decode.stderr
  qa.append(dict(file=name,width=video['width'],height=video['height'],frames=int(video['nb_frames']),duration=float(info['format']['duration']),codec=video['codec_name'],pixel_format=video['pix_fmt'],full_decode_error_count=0,bytes=path.stat().st_size))
  if name=='R05G_Selected_Evidence.mp4':assert float(info['format']['duration'])==264 and int(video['nb_frames'])==2640,(info['format']['duration'],video['nb_frames'])
  at=75 if name.startswith('R05G_All') else 120;out=OUT/'galleries/images'/f'qa_{path.stem}.jpg';subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-y','-v','error','-ss',str(at),'-i',str(path),'-frames:v','1',str(out)],check=True)
 write(OUT/'video_qa.json',qa)
 # Native file references are checked mechanically; no remote assets or fetch dependency.
 for name in ['index.html','all_frames.html']:
  p=OUT/'galleries'/name;text=p.read_text(encoding='utf8');extra='<p><a href="../R05G_Selected_Evidence.mp4">80选帧慢速证据视频</a> · <a href="../R05G_Local_Comparisons.zip">1565张逐帧对比图ZIP</a> · <a href="images/group_h78_raw_pixels.png">开发组H78原像素放大</a></p><p>AUTO贪心首轮最多3个起源候选，此后宽1；E0为严格单起点宽1。原生处理时间不含完整调试JSON导出与文件读取。</p>'
  if '80选帧慢速证据视频' not in text:text=text.replace('<h1>',extra+'<h1>',1)
  if name=='index.html' and '截面响应</a>' not in text:text=text.replace('<label>试验组','<p>'+''.join(f'<a href="images/profile_{g}_{f}.png">{g}/{f}截面响应</a> ' for g,f in SENTINELS)+'</p><label>试验组')
  p.write_text(text,encoding='utf8')
  for ref in re.findall(r'(?:href|src)="([^"#]+)"',text):
   if ':' not in ref:assert (p.parent/ref).is_file(),ref
 pngjpg=list((OUT/'galleries/local_frames').rglob('*.jpg'));assert len(pngjpg)==1565
 for path in pngjpg:
  with Image.open(path) as im:im.verify()
 write(OUT/'delivery_qa.json',dict(local_images=1565,selected_cards=80,sentinel_cards=9,profile_figures=9,raw_pixel_zoom=1,zip_jpg_count=1565,zip_crc_pass=True,all_local_images_decode=True,html_static_refs_exist=True,video_full_decode_pass=True,all_frame_video_last_frame_duplicate='concat final image repeated for final duration;1565 distinct replay images',visual_review='actual JPG cards and video extracted frames reviewed separately',source='actual replay artifacts only'))
 print('DELIVERY COMPLETE',qa,flush=True)
if __name__=='__main__':main()
