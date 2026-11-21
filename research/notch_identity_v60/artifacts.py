"""Compare signed residuals on identical native pixels for the prescribed spot checks."""
import json
import numpy as np
import cv2
from PIL import Image,ImageDraw
from . import batch as b, domain
from research.notch_identity_v515.domain import replay as legacy
from research.notch_identity_v34.difference_views import rgb_delta
from .reference_views import font
from research.v3_labelme_comparison.compare import write_csv

TARGETS={'three_point_bend':(144,178,215,381,407),'group_c':(7,38,54,335,510)}
BASE=b.OUT.parent/'v515_clean_fast_r02'


def frames(path, ids):
    with path.open(encoding='utf8') as stream:
        return {i:json.loads(line) for i,line in enumerate(stream,1) if i in ids}


def main():
    dst=b.OUT/'registration_audit'
    dst.mkdir(exist_ok=True)
    all_rows=[]
    for group, ids in TARGETS.items():
        current=frames(b.OUT/(group+'.jsonl'),ids)
        prior=frames(BASE/(group+'.jsonl'),ids)
        for i,rec in current.items():
            meta=b.read(b.OLD/'evidence'/group/str(i)/'metadata.json')
            inp=meta['input']
            fixed=b.old.read_fixed(inp['reference'],inp['ref_sha'])
            im=b.old.current(inp['current'],inp['image_sha'])
            for pl,models in rec['placements'].items():
                runs=[('V5.15 S2',prior[i],'S2',legacy),('V6.0 S1',rec,'S1',domain.replay),('V6.0 S2',rec,'S2',domain.replay)]
                patches=[]
                for name,record,stage,mapper in runs:
                    m=record['mappings'][pl][stage]
                    diag=record['placements'][pl][stage]['full']['diagnostics']['dual']
                    x,y,r,bot=m['bounds']
                    ref=mapper(fixed,np.array(m['cur']),np.array(m['ref']),m['bounds'],m)
                    dx,dy=(diag.get('registration') or {}).get('shift') or (0,0)
                    patches.append((ref,x-dx,y-dy))
                d=models['S1']['full']['diagnostics']['dual']
                front=d['front'];mid=rec['mappings'][pl]['S1']['windows'][0]['mid']
                for region,lo,hi in [('mouth',0,80),('distal',80,480)]:
                    x=max(front+lo,*[l for _,l,_ in patches])
                    r=min(front+hi,*[l+a.shape[1] for a,l,_ in patches])
                    y=max(mid-30,*[t for _,_,t in patches]);bot=min(mid+31,*[t+len(a) for a,_,t in patches])
                    if r<=x or bot-y<3:continue
                    gray=im[y:bot,x:r].astype(np.float32)
                    deltas=[a[y-t:bot-t,x-l:r-l]-gray for a,l,t in patches]
                    valid=(gray>12)&(gray<249)&(abs(np.arange(y,bot)-mid)[:,None]>3)
                    for delta in deltas:valid&=np.isfinite(delta)
                    pairs=valid[:-2]&valid[2:]
                    cell_width=460 if region=='mouth' else 810
                    tile_h=round((bot-y)*cell_width/(r-x))
                    row_h=tile_h+42
                    panel=Image.new('RGB',(cell_width*2+30,row_h*2+78),'#f8f8f5')
                    draw=ImageDraw.Draw(panel)
                    groupname='三点弯' if group=='three_point_bend' else '验证组C'
                    placement='亮区点位' if pl=='bright' else '原点位'
                    segment='缺口前 80 px' if region=='mouth' else '远段'
                    draw.text((10,8),f'{groupname}  第 {i} 帧  ·  {placement}  ·  {segment}  ·  x={x}…{r-1}',font=font(22),fill='#173847')
                    draw.text((10,41),'固定参考减当前，红为当前变暗，蓝为当前变亮。各图取相同原图像素，色阶 ±32。',font=font(17),fill='#435160')
                    for j,(name,img) in enumerate(zip(['当前灰度']+[s[0] for s in runs],[gray]+deltas)):
                        if j:
                            pairs_hit=(img[2:]*img[:-2]<0)&(np.minimum(abs(img[2:]),abs(img[:-2]))>=5)
                            hits=int((pairs_hit & pairs).sum())
                            all_rows.append(dict(group=group,placement=pl,frame=i,region=region,method=name,
                                   pairs=int(pairs.sum()),dipoles=hits,abs_mean=float(abs(img[valid]).mean()) if valid.any() else None))
                            tile=Image.fromarray(rgb_delta(img))
                        else:tile=Image.fromarray(img.astype('uint8')).convert('RGB')
                        left=10+(j%2)*(cell_width+10)
                        top=74+(j//2)*row_h
                        draw.text((left,top),name,font=font(20),fill='#173847')
                        panel.paste(tile.resize((cell_width,tile_h),Image.Resampling.NEAREST),(left,top+29))
                    panel.save(dst/f'{group}_{pl}_{i:04d}_{region}.png')
    write_csv(dst/'matched.csv',all_rows)

if __name__=='__main__':main()
