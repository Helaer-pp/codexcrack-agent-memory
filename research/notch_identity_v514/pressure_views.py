"""Fixed-frame left-shift panels using actual sensor coordinates from the timing run."""
import ast
import numpy as np
from PIL import Image,ImageDraw
from .reference_views import font
from . import batch as b


def main():
    dest=b.OUT/'pressure_views';dest.mkdir(exist_ok=True)
    for group,i,title in [('group_a',398,'开发组A'),('three_point_bend',248,'三点弯'),('group_c',335,'验证组C亮区')]:
        rows={int(r['delta']):r for r in b.read_csv(b.OUT/(group+'_stress.csv')) if r['frame']==str(i) and r['repeat']=='0' and r['stage']=='S4' and r['direction']=='left'}
        meta=b.read(b.OLD/'evidence'/group/str(i)/'metadata.json')
        info=meta['input']
        fixed=b.old.read_fixed(info['reference'],info['ref_sha'])
        current=b.old.current(info['current'],info['image_sha'])
        requested=np.vstack([ast.literal_eval(r['requested']) for r in rows.values()])
        actual=np.vstack([ast.literal_eval(r['actual_current']) for r in rows.values()])
        corners=np.vstack([requested,actual])
        xs=[int(r['front']) for r in rows.values() if r['front']]
        left=max(0,int(min(corners[:,0].min(),min(xs,default=float('inf')))-40))
        right=min(current.shape[1],int(max(corners[:,0].max(),max(xs,default=0))+135))
        top=max(0,int(corners[:,1].min()-65));bottom=min(current.shape[0],int(corners[:,1].max()+65))
        W,H=620,215;scale=min(W/(right-left),H/(bottom-top))
        size=(round((right-left)*scale),round((bottom-top)*scale))
        card=Image.new('RGB',(1310,1100),'#f6f6f3'); d=ImageDraw.Draw(card)
        d.text((16,9),f'{title} · 第 {i} 帧 · 基准点左移',font=font(26),fill='#18323e')
        d.text((16,53),'固定参考：橙叉为请求，蓝圈为实际点位',font=font(19),fill='#18323e')
        d.text((670,53),'当前帧：蓝圈为输入点，绿线为特征窗，黄线为映射窗',font=font(18),fill='#18323e')
        for row,dx in enumerate((0,-50,-100,-150)):
            record=rows[dx];ybase=88+row*250
            for col,im in enumerate((fixed,current)):
                panel=Image.fromarray(im[top:bottom,left:right]).resize(size,Image.Resampling.BILINEAR).convert('RGB')
                draw=ImageDraw.Draw(panel)
                def xy(point):return ((point[0]-left)*scale,(point[1]-top)*scale)
                if col:
                    for key,color in [('map_box','#e5b520'),('field_box','#39dc82')]:
                        box=ast.literal_eval(record[key])
                        if box:draw.rectangle([xy(box[:2]),xy(box[2:])],outline=color,width=2)
                else:
                    for point in ast.literal_eval(record['requested']):
                        x,y=xy(point);draw.line((x-7,y-7,x+7,y+7),fill='#ff8833',width=3);draw.line((x-7,y+7,x+7,y-7),fill='#ff8833',width=3)
                for point in ast.literal_eval(record['actual_current' if col else 'actual']):
                    x,y=xy(point);draw.ellipse((x-6,y-6,x+6,y+6),outline='#28b5ff',width=3)
                card.paste(panel,(16+col*654,ybase))
            d.text((16,ybase+218),f"请求 {dx} px    实际平均 {float(record['actual_dx']):.1f} px    映射 {record['map_pixels']} px    特征场 {record['field_pixels']} px",font=font(17),fill='#18323e')
        card.save(dest/f'{group}_{i}.jpg',quality=93)

if __name__=='__main__':main()
