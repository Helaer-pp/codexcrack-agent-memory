"""Pair failure-frame evidence with each reachable branch's signed V(x)."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
from . import batch as b, difference_views as views
from .reference_views import font

TARGETS={'group_a':{113,299,366,398,504},'three_point_bend':{84,144,215,248,335,381,413,435,503},'group_c':{7,38,54,324,335,345,510}}


def draw(card,model,gt):
    width=card.width
    out=Image.new('RGB',(width,card.height+300),'white')
    out.paste(card)
    d=ImageDraw.Draw(out)
    branches=[a for a in model['diagnostics']['dual']['branches'] if a.get('V')]
    y0=card.height
    d.text((20,y0+7),'分支累计净得分 V(x)    ·    横轴为原图 x 像素    ·    金线为人工尖端所在列',font=font(20),fill='#12293b')
    if not branches:
        d.text((20,y0+90),'没有可回溯的候选曲线',font=font(22),fill='#45515c')
        return out
    xlo=min([a['root'][0] for a in branches]+[gt[0]])
    xhi=max([a['root'][0]+len(a['V'])-1 for a in branches]+[gt[0]])
    lo=min([min(a['V']) for a in branches]+[0]);hi=max([max(a['V']) for a in branches]+[1])
    def x(v):return 100+(v-xlo)/max(1,xhi-xlo)*(width-490)
    def y(v):return y0+247-(v-lo)/max(1,hi-lo)*169
    d.line((100,y(0),width-390,y(0)),fill='#b7bec6',width=2)
    d.line((x(gt[0]),y0+65,x(gt[0]),y0+248),fill='#b98613',width=3)
    for value in (xlo,xhi):
        d.text((x(value)-10,y0+252),str(round(value)),font=font(16),fill='#415468')
    for value in (lo,hi):
        d.text((12,y(value)-7),f'{value:.1f}',font=font(15),fill='#415468')
    colors=('#146b86','#a73b45','#4c8e55','#775792','#b7642b')
    for j,a in enumerate(branches):
        c=colors[j%len(colors)]
        pts=[(x(a['root'][0]+k),y(v)) for k,v in enumerate(a['V'])]
        if len(pts)>1:d.line(pts,fill=c,width=3)
        k=int(a['tip'][0]-a['root'][0])
        if 0<=k<len(pts):
            X,Y=pts[k];d.ellipse([X-4,Y-4,X+4,Y+4],fill=c)
        d.text((width-365,y0+43+24*j),f"B{a['id']}  {a['reason']}  {a['merit']:.1f}",font=font(16),fill=c)
    return out


def group(g):
    dst=b.OUT/'audit_views'; dst.mkdir(parents=True,exist_ok=True)
    stage=b.read(b.OUT/'selection.json')['stage']
    for pl in (('original','bright') if g=='group_c' else ('original',)):
        scored={int(r['frame']):r for r in b.read_csv(b.OUT/(g+'_scores.csv')) if r['stage']==stage and r['placement']==pl and r['state']=='VISIBLE'}
        ids={i for i,r in scored.items() if r['joint']!='True' or i in TARGETS[g]}
        records={r['frame']:r for r in map(json.loads,(b.OUT/(g+'.jsonl')).open()) if r['frame'] in ids}
        for card,delta,row in views.source_frames(g,ids,placement=pl):
            i=row['frame']
            m=records[i]['placements'][pl][stage]['full']
            draw(card,m,json.loads(scored[i]['gt'])).save(dst/f'{g}_{pl}_{i:04d}.jpg',quality=92)
    print(g,'audit views complete',flush=True)


if __name__=='__main__':
    for group_id in b.GROUPS:group(group_id)
