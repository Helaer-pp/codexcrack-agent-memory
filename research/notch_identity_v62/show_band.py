"""Display the audited native reference points and actual vertical cut for MT frame 78."""
import json
from PIL import Image, ImageDraw
from . import batch as b,inputs
from .reference_views import font


def main():
    rows=[r for r in b.read_csv(b.OUT/'group_h_reference_scan.csv') if int(r['frame'])==78]
    before,after=sorted(rows,key=lambda r:int(r['delta']),reverse=True)
    info=inputs.metadata('group_h',78)['input']
    gray=Image.fromarray(b.old.read_fixed(info['reference'],info['ref_sha']).astype('uint8')).convert('RGB')
    left,right,top,bottom=2190,2830,550,970
    card=Image.new('RGB',(1344,556),'#f8faf9')
    draw=ImageDraw.Draw(card)
    draw.text((18,12),'开发组H第 78 帧 · 同一固定参考图的缺口与材料带下界',font=font(28),fill='#172d39')
    for k,row in enumerate((before,after)):
        dx=20+670*k
        card.paste(gray.crop((left,top,right,bottom)),(dx,86))
        draw.text((dx,56),'原基准点' if k==0 else '两点同步左移 150 px',font=font(20),fill='#172d39')
        line_y=int(row['band_bottom'])-top+86
        if 86<=line_y<506:
            draw.line((dx,line_y,dx+639,line_y),fill='#bf2547',width=3)
            draw.text((dx+8,line_y+6),'线下已裁出搜索区',font=font(16),fill='#ab1742')
        for key,color,size in [('old_nominal','#007ab3',11),('reference_apex','#c45c00',6)]:
            x,y=json.loads(row[key]);x+=dx-left;y+=86-top
            draw.ellipse((x-size,y-size,x+size,y+size),outline=color,width=3)
        draw.text((dx,516),f"蓝圈 V6.1 原点 {row['old_nominal']}    橙圈 V6.2 {row['reference_apex']}",font=font(16),fill='#172d39')
    card.save(b.OUT/'group_h_0078_reference_band.png')

if __name__=='__main__':
    main()
