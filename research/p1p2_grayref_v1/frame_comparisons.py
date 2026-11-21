"""Full-sequence reference/raw-current/frozen-track panels; no GT-derived crop."""
from media import *

def main(g):
 require(g,'comparison');assert (OUT/f'evaluation_{"dev" if g in DEV else "validation"}_complete.json').exists()
 seq=[r for r in rows(OUT/'inputs'/('manifest.csv' if g in DEV else 'validation_manifest.csv')) if r['group']==g];reference=cv2.imdecode(np.frombuffer(Path(seq[0]['reference']).read_bytes(),np.uint8),0);dest=OUT/'galleries/comparison_frames'/g;dest.mkdir(parents=True,exist_ok=True)
 for row in seq:
  f=int(row['frame_id']);folder=OUT/'py_runs'/g/str(f);meta=read(folder/'metadata.json');roi=meta['ROI'];current=cv2.imdecode(np.frombuffer(Path(row['current']).read_bytes(),np.uint8),0);bounds=[max(0,roi['x_left']-45),max(0,roi['y_top']-30),min(current.shape[1],roi['x_right']+24),min(current.shape[0],roi['y_bottom']+30)];joint=rows(folder/'trace_joint_T10p0.csv');single=rows(folder/'trace_current_T10p0.csv');canvas=Image.new('RGB',(1800,1060),'#111d2b');d=ImageDraw.Draw(canvas);text(d,(20,12),f'{NAMES[g]} / {f} · 全帧原图局部对比 · 固定ROI，无GT裁切',BIG)
  for i,(title,im,kind) in enumerate([('参考原图（参考坐标；未宣称严格材料配准）',reference,'ref'),('当前原图（独立保留，不覆盖裂纹灰度）',current,'raw'),('当前原图 + joint/current T10 冻结实际轨迹',current,'trace')]):
   y=65+i*310;text(d,(20,y),title,FONT);base,M=view(im,bounds,size=(1760,268));base=overlay(base,M,meta if kind!='raw' else None,trace=joint if kind=='trace' else None,current=single if kind=='trace' else None,ref=kind=='ref');canvas.paste(base,(20,y+32))
  text(d,(20,1010),'青绿=联合暂定路径；橙=仅当前暂定路径；虚线=缺失；P点为十字。无独立确认。人工对照仅在120张详细卡片中。',SMALL);canvas.save(dest/f'{f:06d}.jpg',quality=90)
 write(OUT/f'frame_comparisons_complete_{g}.json',dict(group=g,frames=len(seq),panels=3,crop='frozen_metadata_ROI_plus_fixed_padding',uses_gt=False));print('FRAME COMPARISONS COMPLETE',g,len(seq),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--group',choices=DEV+VAL,required=True);a=p.parse_args();main(a.group)
