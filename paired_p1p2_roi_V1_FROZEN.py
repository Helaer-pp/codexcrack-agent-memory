#!/usr/bin/env python3
"""Reusable P1/P2-constrained paired-image *research prototype*.

Works without the previous screenshot, manual crack centerline or hardcoded ground-truth tip.
P1/P2 are required in the REFERENCE frame; in the current frame they can be supplied
from the user's point tracker (recommended), or estimated using local NCC templates.
The frozen image evidence / search rules match the November 12 single-pair experiment.
Not certified for other specimens or all frame states.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time
import cv2
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter, gaussian_filter1d
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# =============================================================================
# 用户设置区：日常更换图片只修改本区域，不用修改下面的算法实现。
# 各图像坐标均为原始图像像素坐标 (x, y)，原点在左上，y 向下。
# 图片既可放在此脚本同目录，也可填写完整绝对路径。
# 注：以下参数沿用上一轮单图成功实验，没有跨试件通用性保证。
# =============================================================================

# [A] 每换一组试验或帧，优先修改这几项 -------------------------------
REFERENCE_IMAGE = r"1 (1).bmp"           # 参考图路径
CURRENT_IMAGE   = r"3 (175).bmp"         # 当前变形图路径
OUTPUT_DIR      = r"results_easy_edit"   # 结果保存文件夹

# 参考图上的上下两个预制缺口标记点；更换参考图时需要同步更换。
P1_REFERENCE = (2243.75, 2247.50)   # 上侧点: (x,y)
P2_REFERENCE = (2260.00, 2431.25)   # 下侧点: (x,y)

# 建议直接填写已有的本帧 P1/P2 跟踪坐标，最可靠。
# 两个都写 None 时，程序从参考图自动做局部 NCC 模板匹配。
# 不允许一个写坐标、另一个为 None。
P1_CURRENT = None                   # 例：(2242.75, 2252.50)
P2_CURRENT = None                   # 例：(2259.00, 2435.25)

# 可选：仅用于离线人工对照，绝不进入算法搜索、起点选取或停止判断。
GROUND_TRUTH_TIP = None             # 例：(2423, 2344)，不需要则保持 None

# [B] 建议跨帧冻结的检测参数：不要逐张调参 --------------------------
THRESHOLDS = (8, 10, 12)            # 原图暗谷及参考新增变暗的阈值（灰度级）
MAIN_DISPLAY_THRESHOLD = 10         # 结果叠加图主显示哪一档（取最接近的一档）
GAP_MAX = 20                        # 连续多少列没有通过证据后允许停止
PATH_HALFWIDTH = 7                  # 每列围绕预测中心上下搜索半宽（像素）
MIN_MATERIAL_GRAY = 135.0           # 轨迹两侧材料最低亮度约束
RIGHT_EDGE_X = None                 # ROI 右边界，None 表示自动估计

# [C] P1/P2 自动模板匹配（填入 CURRENT 两点时这几项不会影响坐标） ----
POINT_TEMPLATE_RADIUS = 29          # 模板半径；裁块大小为 2r+1
POINT_SEARCH_RADIUS = 25            # 最大允许匹配位移（±像素）
MIN_POINT_NCC = 0.80                # 匹配相关性下限，低于该值则报错

# [D] 证据计算与曲线追踪：进阶参数，建议暂时冻结 ------------------
GRAY_SMOOTH_SIGMA = 0.7             # 当前/参考灰度图轻度 Gaussian 平滑
VALLEY_FLANK_OFFSETS = (6, 9, 12)   # 暗谷两侧采样距离
MATERIAL_FLANK_OFFSET = 10          # 有效两侧材料的灰度采样距离
PATH_CENTER_PENALTY = 0.55          # 偏离预测路径中心的距离惩罚
DIRECTION_HISTORY_POINTS = 12       # 用于当前方向估计的最近轨迹点数
DIRECTION_MIN_POINTS = 5           # 至少有多少个点才拟合斜率
MAX_ABS_SLOPE = 0.20               # 方向估计斜率绝对值限制 (dy/dx)

# [E] 初始化及 ROI 几何：进阶参数 -----------------------------------
MIN_ROI_HEIGHT = 25                 # P1/P2 的最小纵向间距
MIN_X_ROOM = 50                     # 左边到图像右边至少应留出的空间
MIN_IMAGE_Y_MARGIN = 15             # 上/下 ROI 距图像边缘的保护像素数
ROI_CROP_LEFT_PADDING = 30          # 工作裁剪相对 ROI 左边界额外取像素
ROI_CROP_VERTICAL_PADDING = 24      # 工作裁剪上下额外取像素
ROI_CROP_RIGHT_PADDING = 24         # 工作裁剪在 ROI 右边界后额外取像素
ROI_VALID_TOP_INSET = 2            # 有效 ROI 上边内缩像素
ROI_VALID_BOTTOM_INSET = 1         # 有效 ROI 下边内缩像素
START_X_AFTER_P = 6                 # 初始化位置 x=max(P1x,P2x)+此值
START_Y_INSET = 7                   # 初始化纵向范围上下内缩像素
CENTER_PRIOR_MIN_SIGMA = 12         # 初始中心先验最小标准差
CENTER_PRIOR_ROI_FACTOR = 0.23      # 初始中心先验标准差相对 P1/P2 间距
PATH_Y_BOUNDARY_INSET = 3          # 追踪时 ROI 上下边界内缩像素

# [F] ROI 右边界自动估计（可直接设 RIGHT_EDGE_X 关闭这一启发式） ----
RIGHT_GRAY_BAND_HALFHEIGHT = 8      # 以 P1/P2 中点 y 为中心的采样半高
RIGHT_GRAY_SMOOTH_SIGMA = 25        # 右端边界检查前的一维平滑尺度
RIGHT_SEARCH_BEGIN_AFTER_P = 300    # 从 xleft+该距离开始查找右边界
RIGHT_SEARCH_END_MARGIN = 120       # 距原图右边的排除区域
RIGHT_DARK_GRAY_THRESHOLD = 95      # 右侧区域的暗背景门槛
RIGHT_DARK_RUN_LENGTH = 95          # 后续多少列均值也必须低于门槛
RIGHT_DEFAULT_IMAGE_MARGIN = 25     # 自动估计不成功时，图右边回退距离

# [G] 绘图设置：只改变显示，不参与检测 ---------------------------------
PLOT_BEFORE_LEFT = 60               # 绘图从 ROI 左边向左延伸的宽度
PLOT_MIN_RIGHT_LENGTH = 420         # 绘图至少显示 ROI 向右的这段长度
PLOT_AFTER_TIP = 80                # 绘图在终点后延伸的宽度
PLOT_VERTICAL_MARGIN = 35          # 绘图在上下边界外的显示余量
PLOT_DPI = 170

# =============================================================================
# 配置结束。下面是算法实现：正常更换图片、点位或参数不需要继续修改。
# =============================================================================


def parse_point(s: str) -> tuple[float, float]:
    try:
        x,y = s.split(',')
        return (float(x), float(y))
    except Exception as e:
        raise argparse.ArgumentTypeError(f'Point must be x,y; got {s!r}') from e


def _default_point_string(value):
    return None if value is None else f"{value[0]},{value[1]}"


def parse_args():
    """直接运行使用顶部配置；命令行若提供参数，则覆盖对应配置。"""
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--reference', default=REFERENCE_IMAGE, help='参考图路径')
    p.add_argument('--current', default=CURRENT_IMAGE, help='当前变形图路径')
    p.add_argument('--p1-ref', type=parse_point, default=P1_REFERENCE, help='参考上侧点 x,y')
    p.add_argument('--p2-ref', type=parse_point, default=P2_REFERENCE, help='参考下侧点 x,y')
    p.add_argument('--p1-cur', type=parse_point, default=P1_CURRENT, help='当前上侧点 x,y')
    p.add_argument('--p2-cur', type=parse_point, default=P2_CURRENT, help='当前下侧点 x,y')
    p.add_argument('--output-dir', default=OUTPUT_DIR, help='输出目录')
    p.add_argument('--thresholds', default=','.join(map(str,THRESHOLDS)), help='灰度阈值，如 8,10,12')
    p.add_argument('--gap-max',type=int,default=GAP_MAX,help='连续无观测列数上限')
    p.add_argument('--halfwidth',type=int,default=PATH_HALFWIDTH,help='局部搜索半宽')
    p.add_argument('--min-material-gray',type=float,default=MIN_MATERIAL_GRAY,help='材料最低灰度')
    p.add_argument('--point-search',type=int,default=POINT_SEARCH_RADIUS,help='P点模板搜索半径')
    p.add_argument('--point-radius',type=int,default=POINT_TEMPLATE_RADIUS,help='P点模板半径')
    p.add_argument('--min-ncc',type=float,default=MIN_POINT_NCC,help='P点模板匹配最低相关性')
    p.add_argument('--right-edge',type=int,default=RIGHT_EDGE_X,help='ROI 右边界 x (不设自动估计)')
    p.add_argument('--gt-tip',type=parse_point,default=GROUND_TRUTH_TIP,help='仅作离线 GT 评价的尖端 x,y')
    a=p.parse_args()
    # 以脚本所在文件夹为相对路径的基准，避免从其他工作目录运行找不到图片。
    script_dir=Path(__file__).resolve().parent
    for attr in ('reference','current','output_dir'):
        path=Path(getattr(a,attr)).expanduser()
        if not path.is_absolute():
            path=script_dir/path
        setattr(a,attr,str(path))
    return a


def imread_gray(path):
    image=cv2.imread(str(path),cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f'Failed to read {path}')
    return image


def track_reference_point(ref, cur, pt, template_radius, search, min_ncc):
    x,y=pt
    ix,iy=round(x),round(y)
    r=template_radius
    if ix-r-search < 0 or iy-r-search < 0 or ix+r+search >= ref.shape[1] or iy+r+search >= ref.shape[0]:
        raise ValueError(f'P point {pt} too close to an image boundary for radius={r}, search={search}')
    tpl=ref[iy-r:iy+r+1,ix-r:ix+r+1]
    region=cur[iy-r-search:iy+r+search+1,ix-r-search:ix+r+search+1]
    result=cv2.matchTemplate(region,tpl,cv2.TM_CCOEFF_NORMED)
    _,q,_,loc=cv2.minMaxLoc(result)
    if not np.isfinite(q) or q < min_ncc:
        raise ValueError(f'P point tracking rejected at {pt}: NCC={q:.4f} < {min_ncc}. '
                         'Supply accurate --p1-cur/--p2-cur instead of forcing a false match.')
    dx,dy=loc[0]-search,loc[1]-search
    return (x+dx,y+dy), {'dx':float(dx),'dy':float(dy),'ncc':float(q),'mode':'ncc'}


def main():
    a=parse_args()
    if (a.p1_cur is None)!=(a.p2_cur is None):
        raise ValueError('Supply BOTH --p1-cur and --p2-cur, or neither (to track both).')
    if a.gap_max<0 or a.halfwidth<1 or a.point_search<0:
        raise ValueError('Gap, halfwidth or point search out of allowed ranges')
    if not isinstance(THRESHOLDS, (tuple,list)):
        raise ValueError('THRESHOLDS should be a tuple/list, e.g. (8,10,12)')
    if a.point_radius<1 or a.min_ncc < -1 or a.min_ncc > 1:
        raise ValueError('Invalid NCC template settings.')
    if START_X_AFTER_P < 0 or START_Y_INSET < 0 or not VALLEY_FLANK_OFFSETS:
        raise ValueError('Invalid initial-search or valley-flank parameters.')
    if GRAY_SMOOTH_SIGMA < 0 or RIGHT_GRAY_SMOOTH_SIGMA < 0 or MATERIAL_FLANK_OFFSET < 1:
        raise ValueError('Invalid smoothing or flank parameters.')
    OUT=Path(a.output_dir);OUT.mkdir(parents=True,exist_ok=True)
    t0=time.perf_counter()
    R=imread_gray(a.reference);C=imread_gray(a.current)
    if R.shape!=C.shape:
        raise ValueError(f'Reference and current sizes differ: {R.shape} vs {C.shape}. Registration/resampling required.')
    h,w=R.shape
    ref_points=[a.p1_ref,a.p2_ref]
    if a.p1_cur is not None:
        tracked=[a.p1_cur,a.p2_cur]
        reg=[{'dx':float(q[0]-p[0]),'dy':float(q[1]-p[1]),'ncc':None,'mode':'user_tracked'}
             for p,q in zip(ref_points,tracked)]
    else:
        pts=[track_reference_point(R,C,p,a.point_radius,a.point_search,a.min_ncc) for p in ref_points]
        tracked=[item[0] for item in pts];reg=[item[1] for item in pts]
    P1,P2=tracked
    if P1[1]>P2[1]:
        raise ValueError('Expected P1 to be upper point and P2 lower in image coordinates.')
    upper=int(np.ceil(min(P1[1],P2[1])))
    lower=int(np.floor(max(P1[1],P2[1])))
    xleft=int(np.ceil(max(P1[0],P2[0])))
    if lower-upper<MIN_ROI_HEIGHT:
        raise ValueError(f'P1/P2 vertical distance is too narrow (<{MIN_ROI_HEIGHT} px) for this profile geometry.')
    if not (0 <= xleft+MIN_X_ROOM < w and MIN_IMAGE_Y_MARGIN <= upper < lower < h-MIN_IMAGE_Y_MARGIN):
        raise ValueError(f'Point geometry outside image bounds: xleft={xleft} upper/lower={upper}/{lower}')
    # Automatic right boundary of the valid specimen; retain original research heuristic.
    mid_y=int(round((P1[1]+P2[1])/2))
    if a.right_edge is None:
        meanline=np.mean(C[mid_y-RIGHT_GRAY_BAND_HALFHEIGHT:mid_y+RIGHT_GRAY_BAND_HALFHEIGHT+1,:].astype(np.float32),axis=0)
        meanline=gaussian_filter1d(meanline,RIGHT_GRAY_SMOOTH_SIGMA)
        xr=w-RIGHT_DEFAULT_IMAGE_MARGIN
        for x in range(xleft+RIGHT_SEARCH_BEGIN_AFTER_P,w-RIGHT_SEARCH_END_MARGIN):
            if meanline[x]<RIGHT_DARK_GRAY_THRESHOLD and float(np.mean(meanline[x:x+RIGHT_DARK_RUN_LENGTH]))<RIGHT_DARK_GRAY_THRESHOLD:
                xr=x;break
    else:
        xr=int(a.right_edge)
    if not (xleft+8 < xr <= w-1):
        raise ValueError(f'Invalid right search boundary xr={xr}, xleft={xleft}')
    xa=max(0,xleft-ROI_CROP_LEFT_PADDING); xb=min(w,xr+ROI_CROP_RIGHT_PADDING)
    ya=max(0,upper-ROI_CROP_VERTICAL_PADDING);yb=min(h,lower+ROI_CROP_VERTICAL_PADDING)
    ca=C[ya:yb,xa:xb].astype(np.float32)
    Y,X=np.mgrid[ya:yb,xa:xb].astype(np.float32)
    # This is a rough displacement interpolation (not independently validated DIC).
    alpha=np.clip((Y-P1[1])/(P2[1]-P1[1]),0,1)
    dx=(1-alpha)*reg[0]['dx']+alpha*reg[1]['dx']
    dy=(1-alpha)*reg[0]['dy']+alpha*reg[1]['dy']
    reference_aligned=cv2.remap(R,X-dx,Y-dy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101).astype(np.float32)
    csm=gaussian_filter(ca,GRAY_SMOOTH_SIGMA)
    rsm=gaussian_filter(reference_aligned,GRAY_SMOOTH_SIGMA)
    valley=np.zeros_like(csm)
    for side in VALLEY_FLANK_OFFSETS:
        flank=(np.roll(csm,-side,axis=0)+np.roll(csm,+side,axis=0))*.5
        valley=np.maximum(valley,flank-csm)
    newdark=rsm-csm
    flank_low=np.minimum(np.roll(csm,MATERIAL_FLANK_OFFSET,axis=0),np.roll(csm,-MATERIAL_FLANK_OFFSET,axis=0))
    roi_mask=np.zeros_like(valley,dtype=bool)
    roi_mask[upper-ya+ROI_VALID_TOP_INSET:lower-ya-ROI_VALID_BOTTOM_INSET,xleft-xa:xr-xa]=True
    valid_material=(flank_low>a.min_material_gray)&roi_mask
    score=np.sqrt(np.maximum(valley,0)*np.maximum(newdark,0))
    score[~valid_material]=0
    thresholds=[float(x) for x in a.thresholds.split(',')]
    if not thresholds or any(x<=0 for x in thresholds):
        raise ValueError('Thresholds must be comma-separated positive values.')

    def track(method,thr):
        xstart=xleft+START_X_AFTER_P
        ctr=(P1[1]+P2[1])/2
        init_ys=np.arange(upper+START_Y_INSET,lower-START_Y_INSET)
        if len(init_ys)==0 or not (xa <= xstart < xr):
            raise ValueError('Empty initialization region. Check P1/P2 and START_* settings.')
        col=xstart-xa
        init_score=score[init_ys-ya,col] if method=='joint' else np.where(
            valid_material[init_ys-ya,col],np.maximum(valley[init_ys-ya,col],0),0)
        pri=np.exp(-.5*((init_ys-ctr)/max(CENTER_PRIOR_MIN_SIGMA,(lower-upper)*CENTER_PRIOR_ROI_FACTOR))**2)
        y0=int(init_ys[int(np.argmax(init_score*pri))])
        rows=[];obs=[];last=None;gap=0
        for x in range(xstart,xr):
            if obs:
                hist=np.asarray(obs[-DIRECTION_HISTORY_POINTS:],dtype=np.float32)
                if len(hist)>=DIRECTION_MIN_POINTS:
                    slope=float(np.clip(np.polyfit(hist[:,0],hist[:,1],1)[0],-MAX_ABS_SLOPE,MAX_ABS_SLOPE))
                    yp=float(obs[-1][1]+slope*(x-obs[-1][0]))
                else:
                    yp=float(obs[-1][1])
            else:
                yp=float(y0)
            ys=np.arange(max(upper+PATH_Y_BOUNDARY_INSET,int(np.floor(yp-a.halfwidth))),
                         min(lower-PATH_Y_BOUNDARY_INSET,int(np.ceil(yp+a.halfwidth))+1))
            j=x-xa;k=ys-ya
            c=valley[k,j];d=newdark[k,j];ok=valid_material[k,j]
            if method=='joint':
                strength=np.sqrt(np.maximum(c,0)*np.maximum(d,0))
                accept=ok&(c>=thr)&(d>=thr)
            else:
                strength=np.maximum(c,0)
                accept=ok&(c>=thr)
            merit=strength-PATH_CENTER_PENALTY*np.abs(ys-yp)
            vi=np.flatnonzero(accept)
            if len(vi):
                best=int(vi[np.argmax(merit[vi])]);y=int(ys[best]);hit=True
                obs.append((x,y));last=(x,y);gap=0
            else:
                best=int(np.argmax(merit)) if len(merit) else None
                y=int(ys[best]) if best is not None else int(round(yp));hit=False;gap+=1
            rows.append((x,y,float(c[best]) if best is not None else 0.,
                         float(d[best]) if best is not None else 0.,
                         float(strength[best]) if best is not None else 0.,hit,gap,yp))
            if gap>a.gap_max:
                break
        return rows,obs,last

    traces={};summary=[]
    for mode in ('joint','current'):
        for threshold in thresholds:
            rows,obs,tip=track(mode,threshold)
            key=f'{mode}_T{str(threshold).replace(".","p")}'
            cols=['x','selected_y','current_contrast','reference_new_darkening','joint_strength','is_observed','missing_run','predicted_y']
            pd.DataFrame(rows,columns=cols).to_csv(OUT/f'trace_{key}.csv',index=False)
            item={'mode':mode,'threshold':threshold,'tip_x':None if tip is None else tip[0],
                  'tip_y':None if tip is None else tip[1],
                  'observed_points':len(obs),'visited_columns':len(rows),
                  'last_visited_x':rows[-1][0] if rows else None,
                  'stop_reason':'gap_limit' if tip is not None else 'no_observed_point'}
            if a.gt_tip is not None and tip is not None:
                item['offline_gt_error_px']=float(np.hypot(tip[0]-a.gt_tip[0],tip[1]-a.gt_tip[1]))
            traces[(mode,threshold)]=(rows,obs,tip)
            summary.append(item)
    pd.DataFrame(summary).to_csv(OUT/'summary_results.csv',index=False)
    main_thr=min(thresholds,key=lambda z:abs(z-MAIN_DISPLAY_THRESHOLD))
    rows,obs,tip=traces[('joint',main_thr)]
    # Reproducible compact annotated preview. GT never passed to tracking.
    fig,ax=plt.subplots(figsize=(13,4.5),constrained_layout=True)
    x0=max(0,xleft-PLOT_BEFORE_LEFT);x1=min(w,max(xleft+PLOT_MIN_RIGHT_LENGTH,(tip[0]+PLOT_AFTER_TIP if tip is not None else xleft+PLOT_MIN_RIGHT_LENGTH)))
    y0=max(0,upper-PLOT_VERTICAL_MARGIN);y1=min(h,lower+PLOT_VERTICAL_MARGIN)
    ax.imshow(C[y0:y1,x0:x1],cmap='gray',vmin=0,vmax=255,
              extent=[x0,x1,y1,y0],interpolation='nearest')
    ax.axhline(upper,linestyle='--',color='cyan',alpha=.8)
    ax.axhline(lower,linestyle='--',color='cyan',alpha=.8)
    ax.scatter([P1[0],P2[0]],[P1[1],P2[1]],s=48,color='orange',marker='+',label='P1/P2 current')
    if obs:
        q=np.array(obs);ax.plot(q[:,0],q[:,1],color='lime',linewidth=1.2,label='Automatically selected pixels')
    if tip is not None:
        ax.scatter(*tip,marker='x',color='red',s=90,linewidth=2,label='Provisional tip')
    if a.gt_tip is not None:
        ax.scatter(*a.gt_tip,marker='+',color='deepskyblue',s=90,linewidth=2,label='Offline GT ONLY')
    ax.set(title=f'P1/P2 ROI result: joint T={main_thr}; provisional tip={tip}',xlabel='Original image x',ylabel='Original image y')
    ax.set_xlim(x0,x1);ax.set_ylim(y1,y0);ax.legend(fontsize=8,loc='lower right')
    fig.savefig(OUT/'result_overlay.png',dpi=PLOT_DPI);plt.close(fig)
    params={'reference':str(a.reference),'current':str(a.current),'reference_points':ref_points,
            'current_points':tracked,'current_point_source':'provided' if a.p1_cur is not None else 'NCC template',
            'point_translations':reg,'ROI':{'x_left':xleft,'x_right':xr,'y_top':upper,'y_bottom':lower},
            'algorithm':{'gaussian_sigma':GRAY_SMOOTH_SIGMA,'valley_flank_offsets':list(VALLEY_FLANK_OFFSETS),
                         'min_material_gray':a.min_material_gray,'path_halfwidth':a.halfwidth,
                         'gap_max':a.gap_max,'thresholds':thresholds,
                         'main_display_threshold':main_thr,
                         'material_flank_offset':MATERIAL_FLANK_OFFSET,
                         'path_center_penalty':PATH_CENTER_PENALTY,
                         'direction_history_points':DIRECTION_HISTORY_POINTS,
                         'max_abs_slope':MAX_ABS_SLOPE,
                         'start_x_offset':START_X_AFTER_P,
                         'right_boundary_mode':'automatic' if a.right_edge is None else 'user'},
            'runtime_seconds_total_including_io_and_render':round(time.perf_counter()-t0,4),
            'note':'Single image-pair research prototype; output is NOT independently confirmed crack tip. '
                   'Reference warp is rough interpolation, not validated material registration.'}
    (OUT/'metadata.json').write_text(json.dumps(params,ensure_ascii=False,indent=2),encoding='utf-8')
    print(pd.DataFrame(summary).to_string(index=False))
    print(f'Current P1/P2={tracked}; ROI={params["ROI"]}; output={OUT.resolve()}')


if __name__=='__main__':
    main()
