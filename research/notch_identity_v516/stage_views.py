"""Render the same labeled frame under all four sealed candidates."""
from PIL import Image, ImageDraw
from . import batch as b
from . import difference_views as views
from .reference_views import font

FRAMES={'group_a':{113,299,366,398},'three_point_bend':{144,215,248,271,335,381,413,435,503},'group_c':{7,38,54,510}}

def main():
    dst=b.OUT/'stage_views';dst.mkdir(exist_ok=True)
    for group,ids in FRAMES.items():
        for pl in (('bright','original') if group=='group_c' else ('original',)):
            sheets={i:Image.new('RGB',(2000,4*300),'white') for i in ids}
            for j,s in enumerate(b.ALGS):
                for card,_,row in views.source_frames(group,ids,placement=pl,stage=s):
                    f=row['frame'];sheet=sheets[f]
                    draw=ImageDraw.Draw(sheet)
                    error=('端点误差 '+format(float(row['error']),'.2f')+' px') if row['error'] else '无可评分端点'
                    draw.text((20,300*j+4),f"V5.16 {s}    {group} / {pl}    第 {f} 帧    {error}     参考原图 / 当前原图 / 路径与尖端 / 配准差分",font=font(23),fill='#173847')
                    sheet.paste(card.crop((0,374,2000,620)),(0,300*j+43))
            for i,img in sheets.items():img.save(dst/f'{group}_{pl}_{i:04d}.jpg',quality=90)
if __name__=='__main__':main()
