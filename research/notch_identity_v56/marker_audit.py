"""Post-seal image-based attribution of the fork veto to distinct connected components."""
import numpy as np
import cv2
from PIL import Image,ImageDraw
from . import batch as b, native
from research.notch_identity_v34.reference_views import font
from research.notch_identity_v42.reporting import table
from research.v3_labelme_comparison.infer import current
from research.v3_labelme_comparison.compare import write_csv

def audit():
    summary=[];rows=[]
    for group,index in [('three_point_bend',i) for i in (144,178,215)]+[('group_c',i) for i in (221,324,456,510)]:
        assert b.sha(b.OUT/(group+'.jsonl'))==b.read(b.OUT/(group+'_seal.json'))['predictions']
        meta=b.read(b.OLD/'evidence'/group/str(index)/'metadata.json');info=meta['input']
        image=current(info['current'],info['image_sha']);points=np.asarray(meta['current_points'])
        p=native.prepare(image,points,'v5_6');x,y=p.body_root;w=p.mouth_thickness
        r=int(max(28,4*w));left=max(0,x-160);top=max(0,min(y-r,int(points[:,1].min())-32));bottom=min(len(image),max(y+r+1,int(points[:,1].max())+32))
        crop=image[top:bottom,left:min(image.shape[1],x+210)]
        threshold=p.black+.28*p.span
        _,cc,stats,_=cv2.connectedComponentsWithStats((crop<threshold).astype('uint8'))
        ids=[int(cc[int(round(py))-top,int(round(px))-left]) for px,py in points]
        votes=without=0;marker_runs=0
        canvas=Image.fromarray(crop).convert('RGB').resize((crop.shape[1]*2,crop.shape[0]*2))
        draw=ImageDraw.Draw(canvas)
        for j,(px,py) in enumerate(points):
            a=(px-left)*2;c=(py-top)*2
            draw.ellipse((a-10,c-10,a+10,c+10),outline='#f0ca44',width=3)
            draw.text((a+14,c-10),f'P{j+1} / CC {ids[j]}',font=font(18),fill='#fccb31',stroke_width=1,stroke_fill='#312c25')
        for lag in (1,2,3,4):
            xcol=x-lag;lo=max(0,y-r);hi=min(len(image),y+r+1)
            col=image[lo:hi,xcol]<threshold
            edges=np.flatnonzero(np.diff(np.r_[False,col,False]))
            runs=[]
            for a,c in zip(edges[::2],edges[1::2]):
                if c-a<max(2,.15*w):continue
                cid=int(cc[lo+(a+c-1)//2-top,xcol-left]);assert cid!=0
                marker=cid in ids
                runs.append((int(a),int(c),cid,marker))
                marker_runs+=int(marker)
                rows.append(dict(group=group,frame=index,x=xcol,y_first=int(lo+a),y_last=int(lo+c-1),component=cid,
                            marker='P'+str(ids.index(cid)+1) if marker else '',thickness=w))
                draw.line(((xcol-left)*2,(lo+a-top)*2,(xcol-left)*2,(lo+c-top)*2),fill='#ef4e8d' if marker else '#2adb9c',width=2)
            def has_vote(rr):
                return any(a[0]-c[1]>max(2,.35*w) for c,a in zip(rr,rr[1:]))
            votes+=has_vote(runs)
            without+=has_vote([q for q in runs if not q[3]])
        draw.text((12,10),f'F{index}    fork votes {votes}/4',font=font(20),fill='white',stroke_width=2,stroke_fill='#26323c')
        target=b.OUT/'marker_audit'/f'{index:04d}.png';target.parent.mkdir(exist_ok=True)
        canvas.save(target)
        summary.append(['三点弯' if group=='three_point_bend' else '验证组C',f'[{index}]({target.relative_to(b.OUT).as_posix()})',[int(x),int(y)],round(w,1),ids,marker_runs,votes,without])
    write_csv(b.OUT/'marker_audit'/'cross_sections.csv',rows)
    return ['## 基准标记是否进入裂纹判别','在冻结预测后，按正式算法的灰度阈值和四个截面重建暗区。用同一裁剪图的八连通标签核对暗带是否包含 P1/P2 中心。图中黄圈是实测点，粉红线是与标记中心同连通体的计数暗带，绿线是其余暗带。连通体号 0 表示该中心像素在此阈值下属于背景。',
        table(['实验','原图与截面','图像根部','估计厚度 px','P1/P2 连通体号','标记暗段数','正式赞成票/4','事后去标记票数/4'],summary),
        '达到两票即触发 OPEN_FORK。最后一列仅重算拓扑判据，没有重新运行检测或计入验证命中。该实验表明，输入坐标平移稳定，仍可能把图像中的实体基准标记当作缺口几何。下一轮应在合成及开发图像里加入独立深色标记，只让属于缺口本体的壁面参与拓扑计票，并保留无坐标提示的标记对照。 [逐列连通体记录](marker_audit/cross_sections.csv)']
