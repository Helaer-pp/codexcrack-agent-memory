"""Raw current-image origin strips, no annotation reader or GT input."""
from common import *
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
def main():
 font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17);mapping=[]
 for g in DEV:
  selected=[r for r in rows(OUT/'selection.csv') if r['dataset_id']==g];sheet=Image.new('RGB',(2400,1500),'#142033');draw=ImageDraw.Draw(sheet)
  for i,row in enumerate(selected):
   require(g,'development');f=int(row['frame_id']);raw=Path(row['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=np.array(json.loads(row['points']));origin=pp.mean(axis=0);delta=pp[1]-pp[0];spacing=np.linalg.norm(delta);t=np.array([delta[1],-delta[0]])/spacing;normal=np.array([-t[1],t[0]])
   # Raw affine display from u=-0.1L..1.1L, v=-0.22L..0.22L.
   w,h=580,220;u=np.linspace(-.1*spacing,1.1*spacing,w);v=np.linspace(-.22*spacing,.22*spacing,h);xx=origin[0]+u[None,:]*t[0]+v[:,None]*normal[0];yy=origin[1]+u[None,:]*t[1]+v[:,None]*normal[1];crop=cv2.remap(im,xx.astype('float32'),yy.astype('float32'),cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=255);pic=Image.fromarray(crop).convert('RGB');pd=ImageDraw.Draw(pic)
   for fraction in [0,.2,.4,.6,.8,1.]:
    x=(fraction+.1)/1.2*(w-1);pd.line((x,0,x,14),fill='#19dcee',width=2);pd.text((x+2,2),str(fraction),font=font,fill='#006180')
   pd.line((0,(h-1)/2,w-1,(h-1)/2),fill='#a7dce0',width=1)
   col=i%4;rr=i//4;pos=(col*600+10,rr*300+45);sheet.paste(pic,pos);draw.text((pos[0],pos[1]-30),f'{g}/{f}  u/L, v/L=0 at cyan line',font=font,fill='white')
   mapping.append(dict(dataset_id=g,frame_id=f,origin=origin.tolist(),forward=t.tolist(),normal=normal.tolist(),spacing=float(spacing),source_sha256=row['sha256'],display='raw image only; no GT; diagnostic seed u/v fractions must name current frame'))
  sheet.save(OUT/'seeds'/f'{g}_raw_origin_sheet.jpg',quality=97)
 save(OUT/'seeds/origin_mapping.csv',mapping);print('raw seed sheets complete')
if __name__=='__main__':main()
