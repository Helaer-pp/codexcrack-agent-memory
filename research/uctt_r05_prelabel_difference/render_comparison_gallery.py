"""Add source-ROI residual overlays; these are explicitly diagnostic candidates."""
from PIL import Image,ImageDraw,ImageFont
from common import *
def main():
 font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20);count=0
 for p in sorted((OUT/'diagnostics').glob('*.npz')):
  with np.load(p) as d:
   canvas=Image.new('RGB',(1600,620),'#17212b');draw=ImageDraw.Draw(canvas);current=d['current'];common=d['common_mask'];draw.text((20,15),p.stem+' | ALGORITHM DIAGNOSTICS, NOT HUMAN GT',fill='white',font=font)
   draw.text((20,48),'Orange: geometric static-strip residual >25 | Red: predefined candidate-strip residual >25',fill='#ffc071',font=font)
   for i,arm in enumerate(['E0_CURRENT_ONLY','E1_FIXED_REF','E2_MATCHED_HISTORY']):
    rgb=cv2.cvtColor(current,cv2.COLOR_GRAY2RGB);field=arm+'_signed_difference';text=arm
    if arm!='E0_CURRENT_ONLY':
     if field in d and common.any():
      act=(abs(d[field])>25)&common;rgb[act&d['holdout_mask']]=[255,150,30];rgb[act&d['candidate_mask']]=[255,50,50]
     else:text+=' N/A: no valid paired area'
    im=Image.fromarray(rgb);im.thumbnail((510,400));canvas.paste(im,(20+i*525,140));draw.text((20+i*525,100),text,fill='white',font=font)
   draw.text((20,575),'Current original-image ROI: '+str(d['roi'].tolist())+' | no visible-tip decision is made',fill='#b7cad8',font=font)
   canvas.save(p.with_name(p.stem+'_hotspots.jpg'),quality=88);count+=1
 page=OUT/'R05_Reference_Difference_Comparison.html';s=page.read_text(encoding='utf8')
 for p in sorted((OUT/'diagnostics').glob('*.npz')):
  old=f'<a href="diagnostics/{p.stem}.npz">';new=f'<a href="diagnostics/{p.stem}_hotspots.jpg">原图ROI残差热点（非GT）</a> | '+old;s=s.replace(old,new)
 page.write_text(s,encoding='utf8');print('HOTSPOT OVERLAYS',count)
if __name__=='__main__':main()
