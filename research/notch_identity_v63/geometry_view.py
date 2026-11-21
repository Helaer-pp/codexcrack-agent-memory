"""Draw the measured nominal and displaced reference vertices against the fixed MT image."""
import json
from PIL import Image,ImageDraw
from research.notch_identity_v62 import batch as prior
from . import inputs,batch as b
from .reference_views import font


def main():
    i=78
    info=inputs.metadata('group_h',i)['input']
    fixed=Image.fromarray(b.old.read_fixed(info['reference'],info['ref_sha']).astype('uint8')).convert('RGB')
    earlier={int(r['delta']):r for r in b.read_csv(prior.OUT/'group_h_reference_scan.csv') if int(r['frame'])==i}
    shifted={int(r['dx']):r for r in b.read_csv(b.OUT/'group_h_shift.csv') if int(r['frame'])==i}
    left,top,right,bottom=2190,550,2830,970
    canvas=Image.new('RGB',(1350,580),'#f6f8f6')
    d=ImageDraw.Draw(canvas)
    d.text((18,12),'开发组H第 78 帧 · 固定参考图中的缺口定位',font=font(29),fill='#173945')
    for j,dx in enumerate((0,-150)):
        x0=18+670*j;y0=90
        canvas.paste(fixed.crop((left,top,right,bottom)),(x0,y0))
        old=earlier[dx]
        row=shifted[-150]
        a=json.loads(old['reference_apex']);v=json.loads(row[('nominal_' if dx==0 else '')+'reference_apex'])
        band=json.loads(row[('nominal_' if dx==0 else '')+'material_band'])
        d.text((x0,55),'名义基准点' if dx==0 else '两基准点左移 150 px',font=font(20),fill='#173945')
        for pt,color,rad in ((a,'#c85d21',8),(v,'#00818a',5)):
            x,y=x0+pt[0]-left,y0+pt[1]-top
            d.ellipse((x-rad,y-rad,x+rad,y+rad),outline=color,width=3)
        bottom62=int(old['band_bottom'])
        if top<=bottom62<bottom:
            y=y0+bottom62-top
            d.line((x0,y,x0+639,y),fill='#c85d21',width=3)
            d.text((x0+5,y+5),'V6.2 搜索下界',font=font(15),fill='#a04613')
        d.text((x0,519),f'V6.2 橙圈 {a}     V6.3 青圈 {v}',font=font(18),fill='#173945')
        d.text((x0,547),f"材料带纵坐标：V6.2 [{old['band_top']}, {bottom62})    V6.3 [{band[0]}, {band[1]})",font=font(16),fill='#173945')
    canvas.save(b.OUT/'group_h_0078_geometry.png')

if __name__=='__main__':main()
