from common import *
import numpy as np
from PIL import Image,ImageDraw,ImageFont

def main():
 arr=np.load(OUT/'pixel_audit/group_h_78_w55.npz');score=arr['score'];ridge=arr['ridge'];labels=arr['components'];gt=arr['gt_local'];yy,xx=np.indices(score.shape)
 cx,cy=np.round(gt).astype(int);x0=max(0,cx-26);y0=max(0,cy-18);x1=min(score.shape[1],cx+27);y1=min(score.shape[0],cy+19)
 font='C:/Windows/Fonts/msyh.ttc';out=Image.new('RGB',(1500,720),'#0b1423');d=ImageDraw.Draw(out)
 def text(xy,s,size=23,color='#e4edf8'):d.text(xy,s,font=ImageFont.truetype(font,size),fill=color)
 text((25,18),'开发组H78：当前响应已经恢复，短脊线在片段门被丢弃',31)
 maps=[];base=np.zeros((*score.shape,3),np.uint8);base[:]=[30,38,53];base[score>=3]=[30,213,224];maps.append(base)
 base=np.zeros((*score.shape,3),np.uint8);base[:]=[30,38,53]
 for cid in np.unique(labels):
  if not cid:continue
  ys,xs=np.where(labels==cid);qualified=len(xs)>=4 and len(np.unique(xs))>=4 and xs.max()-xs.min()+1>=4
  base[labels==cid]=[70,233,132] if qualified else [255,158,51]
 maps.append(base)
 for i,rgb in enumerate(maps):
  crop=Image.fromarray(rgb[y0:y1,x0:x1]).resize((680,470),Image.Resampling.NEAREST);p=ImageDraw.Draw(crop);sx=680/(x1-x0);sy=470/(y1-y0);x=(gt[0]-x0)*sx;y=(gt[1]-y0)*sy;p.line((x-10,y,x+10,y),fill='#ff41ed',width=3);p.line((x,y-10,x,y+10),fill='#ff41ed',width=3)
  out.paste(crop,(25+i*755,120));text((25+i*755,80),'青：native score ≥ 3' if i==0 else '橙：不足4列的NMS分量；绿：通过片段长度门',22)
 text((25,612),'紫十字仅为离线人工尖端。最近两像素分量端点距标注0.288px，却未进入候选池。',24)
 text((25,653),'这是证据转换失败，不代表两像素响应已具备主裂纹身份或终止证明。原生数组：pixel_audit/',22)
 out.save(OUT/'galleries/images/group_h78_response_segment_failure.jpg',quality=95)
 print('AUDIT IMAGE COMPLETE')
if __name__=='__main__':main()
