from media import *
def main():
 r=next(r for r in rows(OUT/'selection.csv') if r['dataset_id']=='group_h' and int(r['frame_id'])==78);require('group_h','development');im=cv2.imdecode(np.frombuffer(Path(r['source_image']).read_bytes(),np.uint8),0)
 audit=next(r for r in read(OUT/'tests/group_h78_short_fragment_audit.json') if r['variant']=='E1_BEAM' and r['columns']==2);p=np.array(audit['fragment_endpoint']);x,y=np.floor(p).astype(int);crop=im[y-25:y+26,x-40:x+41];lo,hi=np.percentile(crop,[1,99]);hi=max(hi,lo+1);enhanced=np.uint8(np.clip((crop.astype(float)-lo)*255/(hi-lo),0,255));size=(810,510);raw=Image.fromarray(crop).resize(size,Image.Resampling.NEAREST).convert('RGB');display=Image.fromarray(enhanced).resize(size,Image.Resampling.NEAREST).convert('RGB')
 t=read(OUT/'traces/E1_BEAM_group_h_78.json');M=np.array([[10.,0.,-10*(x-40)],[0.,10.,-10*(y-25)]]);canvas=Image.new('RGB',(1680,1280),'#111d2b');d=ImageDraw.Draw(canvas)
 lines(d,(20,10),'开发组H/78：原先两列弱片段的实际原像素证据',BIG);lines(d,(20,53),'固定81×51原像素；最近邻放大10倍。右侧仅显示拉伸，不进入算法，也不改变标注。',SMALL)
 panel(canvas,(20,90),raw,M,'原始灰度（未增强）','R05F 两列片段原坐标 x≈2797.91, y≈755.66')
 panel(canvas,(850,90),display,M,'同一原像素，线性显示拉伸',f'显示范围 [{lo:.2f}, {hi:.2f}] → [0,255]，算法仍读取原始灰度')
 panel(canvas,(20,700),raw,M,'原灰度 + 自动束搜索实际轨迹','黄色=实际截面；青绿=观测；橙色=推断',t=t)
 panel(canvas,(850,700),display,M,'显示拉伸 + 同一条实际轨迹','保留原片段附近观测不等于确认了主裂纹身份',t=t)
 canvas.save(OUT/'galleries/images/group_h78_raw_pixels.png')
 write(OUT/'tests/group_h78_display_transform.json',dict(source_sha256=r['sha256'],original_crop=[int(x-40),int(y-25),81,51],display_only_percentile=[1,99],lo=float(lo),hi=float(hi),scale=10,interpolation='nearest',no_runtime_feedback=True))
if __name__=='__main__':main()
