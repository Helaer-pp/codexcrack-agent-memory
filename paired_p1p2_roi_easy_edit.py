#!/usr/bin/env python3
"""P1/P2 folder processing with original-image ROI and crack-result comparisons.

Works without the previous screenshot, manual crack centerline or hardcoded ground-truth tip.
P1/P2 are required in the REFERENCE frame; in the current frame they can be supplied
from the user's point tracker (recommended), or estimated using local NCC templates.
Set REFERENCE_IMAGE, IMAGE_FOLDER and P1_REFERENCE/P2_REFERENCE, then run this file.
The fixed image evidence / search rules are retained from the single-pair prototype.
Not certified for other specimens or all frame states.
"""
from __future__ import annotations
import argparse
import os
import json
import html
import re
import hashlib
import webbrowser
from datetime import datetime
from pathlib import Path
import time
import cv2
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter, gaussian_filter1d
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parent/'output/cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


# =============================================================================
# 用户设置区：日常更换图片只修改本区域，不用修改下面的算法实现。
# 各图像坐标均为原始图像像素坐标 (x, y)，原点在左上，y 向下。
# 图片既可放在此脚本同目录，也可填写完整绝对路径。
# 注：以下参数沿用上一轮单图成功实验，没有跨试件通用性保证。
# =============================================================================

# [A] 批量使用只需设置：参考帧、图像文件夹、参考帧上的 P1/P2 ----------
REFERENCE_IMAGE = r"D:/datasets\裂纹数据\CT裂纹\开发组A\测试-1\20240328171125068-2.bmp"           # 参考图路径
IMAGE_FOLDER = r"D:/datasets\裂纹数据\CT裂纹\开发组A\测试-1"
CURRENT_IMAGE = None               # 默认批量；填单张路径或传 --current 则运行单对图像
OUTPUT_DIR      = "output/paired_p1p2_roi_easy_edit"   # 结果保存在项目内，不写入原始数据目录
OPEN_RESULTS = True               # 完成后在浏览器打开可翻页的结果；命令行 --no-open 可关闭
POINT_TRACKING_MODE = 'previous'   # previous=上一成功定位帧；reference=始终对初始参考帧匹配
DISPLAY_MODE = 'joint'             # joint=当前暗谷+参考增量；current=仅当前暗谷；只控制显示
IMAGE_EXTENSIONS = ('.bmp', '.png', '.jpg', '.jpeg', '.tif', '.tiff')

# 参考图上的上下两个预制缺口标记点；更换参考图时需要同步更换。
# P1_REFERENCE = (2243.75, 2247.50)   # 上侧点: (x,y)
# P2_REFERENCE = (2260.00, 2431.25)   # 下侧点: (x,y)

P1_REFERENCE = (864, 995)   # 上侧点: (x,y)
P2_REFERENCE = (876, 1281)   # 下侧点: (x,y)

# 批量模式必须保持下面两项为 None，程序自动逐帧定位。
# 单张 --current 模式可填写已有的本帧 P1/P2 跟踪坐标。
# 两项须同时填写或同时为 None。
P1_CURRENT = None                   # 例：(2242.75, 2252.50)
P2_CURRENT = None                   # 例：(2259.00, 2435.25)

# 单张模式可选：仅用于离线人工对照；批量模式须为 None，避免把一个标签套用到所有帧。
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


def parse_args(argv=None):
    """直接运行使用顶部配置；命令行若提供参数，则覆盖对应配置。"""
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--reference', default=REFERENCE_IMAGE, help='参考图路径')
    p.add_argument('--current', default=CURRENT_IMAGE, help='当前变形图路径')
    p.add_argument('--image-folder', default=IMAGE_FOLDER, help='批量图像文件夹；只读取本层，按文件名自然排序')
    p.add_argument('--point-tracking', choices=['previous','reference'], default=POINT_TRACKING_MODE)
    p.add_argument('--display-mode', choices=['joint','current'], default=DISPLAY_MODE)
    p.add_argument('--open', dest='open_results', action=argparse.BooleanOptionalAction, default=OPEN_RESULTS)
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
    a=p.parse_args(argv)
    # 以脚本所在文件夹为相对路径的基准，避免从其他工作目录运行找不到图片。
    script_dir=Path(__file__).resolve().parent
    for attr in ('reference','current','image_folder','output_dir'):
        if getattr(a,attr) is None:
            continue
        path=Path(getattr(a,attr)).expanduser()
        if not path.is_absolute():
            path=script_dir/path
        setattr(a,attr,str(path.resolve()))
    if a.current is not None:
        a.image_folder=None
    return a


def imread_gray(path):
    # Python handles Unicode paths; OpenCV only receives the encoded image bytes.
    # Let read_bytes preserve genuine missing-file/permission errors.
    data=Path(path).read_bytes()
    if not data:
        raise ValueError(f'Image file is empty: {path}')
    image=cv2.imdecode(np.frombuffer(data,dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f'Image file exists but could not be decoded: {path}')
    return image


def track_reference_point(ref, cur, pt, template_radius, search, min_ncc):
    x,y=pt
    ix,iy=round(x),round(y)
    r=template_radius
    if ix-r-search < 0 or iy-r-search < 0 or ix+r+search >= ref.shape[1] or iy+r+search >= ref.shape[0]:
        raise ValueError(f'P point {pt} too close to an image boundary for radius={r}, search={search}')
    tpl=ref[iy-r:iy+r+1,ix-r:ix+r+1]
    if float(np.std(tpl)) < 1e-6:
        raise ValueError(f'P point {pt}: constant template has no tracking texture.')
    region=cur[iy-r-search:iy+r+search+1,ix-r-search:ix+r+search+1]
    result=cv2.matchTemplate(region,tpl,cv2.TM_CCOEFF_NORMED)
    _,q,_,loc=cv2.minMaxLoc(result)
    if not np.isfinite(q) or q < min_ncc:
        raise ValueError(f'P point tracking rejected at {pt}: NCC={q:.4f} < {min_ncc}. '
                         'Supply accurate --p1-cur/--p2-cur instead of forcing a false match.')
    dx,dy=loc[0]-search,loc[1]-search
    return (x+dx,y+dy), {'dx':float(dx),'dy':float(dy),'ncc':float(q),'mode':'ncc'}


def validate_settings(a):
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
    thresholds=[float(x) for x in a.thresholds.split(',')]
    if not thresholds or any(not np.isfinite(x) or x<=0 for x in thresholds):
        raise ValueError('Thresholds must be finite positive numbers.')
    for pt in [a.p1_ref,a.p2_ref,a.p1_cur,a.p2_cur]:
        if pt is not None and (len(pt)!=2 or not np.isfinite(pt).all()):
            raise ValueError('P points must contain two finite coordinates.')
    if a.p1_ref[1]>=a.p2_ref[1]:
        raise ValueError('P1 must be above P2 in the reference image.')


def process_pair(a, R=None, C=None, point_tracking=None):
    """Original numerical detector, shared by single-pair and folder runners."""
    validate_settings(a)
    OUT=Path(a.output_dir);OUT.mkdir(parents=True,exist_ok=True)
    t0=time.perf_counter()
    R=imread_gray(a.reference) if R is None else R
    C=imread_gray(a.current) if C is None else C
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
    if point_tracking:
        for translation,local_match in zip(reg,point_tracking['local_matches']):
            translation.update(mode=point_tracking['mode'],ncc=local_match['ncc'])
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
                  'stop_reason':('no_observed_point' if tip is None else 'gap_limit' if rows[-1][6]>a.gap_max else 'roi_right_boundary')}
            if a.gt_tip is not None and tip is not None:
                item['offline_gt_error_px']=float(np.hypot(tip[0]-a.gt_tip[0],tip[1]-a.gt_tip[1]))
            traces[(mode,threshold)]=(rows,obs,tip)
            summary.append(item)
    pd.DataFrame(summary).to_csv(OUT/'summary_results.csv',index=False)
    main_thr=min(thresholds,key=lambda z:abs(z-MAIN_DISPLAY_THRESHOLD))
    rows,obs,tip=traces[('joint',main_thr)]
    render_result(C, tracked, (xleft,xr,upper,lower), traces[(a.display_mode,main_thr)],
                  a.display_mode, main_thr, OUT/'result_overlay.png', a.gt_tip)
    params={'reference':str(a.reference),'current':str(a.current),'reference_points':ref_points,
            'current_points':tracked,'current_point_source':point_tracking['mode'] if point_tracking else ('provided' if a.p1_cur is not None else 'NCC template'),
            'point_tracking':point_tracking, 'display_mode':a.display_mode,
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
    return summary, params


def render_result(image, points, roi, trace, mode, threshold, path, gt=None):
    """Same crop in the raw/result panels; no line across a missing observation."""
    left,right,top,bottom=roi
    rows,observed,tip=trace
    h,w=image.shape
    x0=max(0,left-PLOT_BEFORE_LEFT)
    x1=min(w,max(left+PLOT_MIN_RIGHT_LENGTH,(tip[0]+PLOT_AFTER_TIP if tip else left+PLOT_MIN_RIGHT_LENGTH)))
    y0=max(0,top-PLOT_VERTICAL_MARGIN);y1=min(h,bottom+PLOT_VERTICAL_MARGIN)
    fig,axes=plt.subplots(1,3,figsize=(17,6),gridspec_kw={'width_ratios':[1,1.4,1.4]},constrained_layout=True)
    full,raw,result=axes
    full.imshow(image,cmap='gray',vmin=0,vmax=255)
    full.add_patch(Rectangle((left,top),right-left,bottom-top,fill=False,edgecolor='cyan',linewidth=1.2,label='Search ROI'))
    full.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,edgecolor='gold',linestyle=':',label='Local view'))
    full.set_title('Full original image + search ROI')
    for ax in axes:
        if ax is not full:
            ax.imshow(image[y0:y1,x0:x1],cmap='gray',vmin=0,vmax=255,extent=[x0,x1,y1,y0],interpolation='nearest')
            ax.add_patch(Rectangle((left,top),right-left,bottom-top,fill=False,edgecolor='cyan',linewidth=1))
            ax.set_xlim(x0,x1);ax.set_ylim(y1,y0)
        ax.scatter(*np.asarray(points).T,c=['red','blue'],s=35,marker='+')
        ax.set(xlabel='Original x [px]',ylabel='Original y [px]')
    raw.set_title('Original ROI detail (no crack overlay)')
    if rows:
        q=np.asarray(rows,dtype=float);seen=q[:,5].astype(bool)
        result.plot(q[:,0],np.where(seen,q[:,1],np.nan),c='lime',lw=1,label='Observed path')
        result.scatter(q[seen,0],q[seen,1],c='lime',s=3)
        if (~seen).any():
            result.scatter(q[~seen,0],q[~seen,7],c='orange',s=7,marker='.',label='Gap prediction (not observed)')
    if tip is not None:
        result.scatter(*tip,marker='x',color='red',s=75,linewidths=2,label='Provisional endpoint')
    if gt is not None:
        result.scatter(*gt,marker='+',color='deepskyblue',s=75,label='Offline GT only')
    status='NO_TIP' if tip is None else f'provisional=({tip[0]}, {tip[1]})'
    result.set_title(f'Crack result: {mode} T={threshold:g}\n{status}')
    full.legend(fontsize=8);result.legend(fontsize=8,loc='best')
    fig.suptitle('P1 red / P2 blue | Cyan: complete search ROI | Yellow: displayed local crop')
    try:
        fig.savefig(path,dpi=PLOT_DPI)
    finally:
        plt.close(fig)


def data_role(path):
    """Enforce known exclusions before opening pixels; roles never change detection."""
    root=Path(__file__).resolve().parent
    path=Path(path).resolve()
    name=str(path).casefold()
    if '排除组X' in name or 'group_x' in name:
        raise PermissionError(f'Excluded dataset (group_x): {path}')
    policy=json.loads((root/'config/dataset_usage_policy.json').read_text(encoding='utf-8'))
    config=json.loads((root/'config/datasets.json').read_text(encoding='utf-8'))
    for group in config['groups']:
        if path.is_relative_to(Path(group['images']).resolve()):
            role=policy['groups'][group['id']]
            if role=='EXCLUDED':
                raise PermissionError(f'Excluded dataset: {group["id"]}')
            return role
    return 'USER_FOLDER_FIXED_RULE_INFERENCE'


def natural_key(path):
    # The tie-breaker also makes 1.png vs 01.png and equal numeric stems deterministic.
    return ([int(x) if x.isdigit() else x.casefold() for x in re.split(r'(\d+)',path.name)],path.name)


def list_images(folder):
    folder=Path(folder)
    data_role(folder)
    if not folder.is_dir():
        raise NotADirectoryError(f'Image folder not found: {folder}')
    images=sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.casefold() in IMAGE_EXTENSIONS),key=natural_key)
    if not images:
        raise ValueError(f'No supported images in folder: {folder}')
    for path in images:
        data_role(path)
    return images


def write_gallery(out, records, total, state):
    pd.DataFrame(records,columns=['index','filename','status','tip_x','tip_y','p1_x','p1_y','p2_x','p2_y',
                                 'tracking_source','image','detail','error']).to_csv(out/'batch_summary.csv',index=False,encoding='utf-8-sig')
    payload=json.dumps(records,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>P1/P2 批量结果</title>
<style>body{margin:22px;background:#15212d;color:#eef;font:17px sans-serif}button,select{font:inherit;padding:7px;margin:4px}a{color:#7ee5ff}img{max-width:100%;background:white}pre{white-space:pre-wrap}#meta{margin:12px 0}</style>
<h1>原图 ROI 与裂纹结果</h1><p>__STATE__；已处理 __DONE__ / __TOTAL__ 张。端点为原算法暂定结果；NO_TIP / ERROR 都保留。</p>
<p><a href="batch_summary.csv">汇总CSV</a> · <a href="all_mode_results.csv">所有模式/阈值结果</a> · <a href="run_config.json">本次配置</a></p>
<button id="prev">← 上一张</button><select id="pick"></select><button id="next">下一张 →</button>
<div id="meta"></div><a id="detail">逐列轨迹/参数</a><pre id="error"></pre><a id="large" target="_blank"><img id="picture"></a>
<script>const data=__DATA__;let index=0;const pick=document.getElementById('pick');
data.forEach((r,i)=>{let o=document.createElement('option');o.value=i;o.textContent=`${r.index}. ${r.filename} | ${r.status}`;pick.append(o)});
function show(){if(!data.length)return;let r=data[index];pick.value=index;
document.getElementById('meta').textContent=`${r.filename} | ${r.status} | 尖端: ${r.tip_x==null?'无':r.tip_x+', '+r.tip_y} | P1: ${r.p1_x??'未知'},${r.p1_y??'未知'} | P2: ${r.p2_x??'未知'},${r.p2_y??'未知'}`;
document.getElementById('error').textContent=r.error||'';document.getElementById('detail').href=r.detail;
let im=document.getElementById('picture');im.hidden=!r.image;if(r.image)im.src=r.image;else im.removeAttribute('src');document.getElementById('large').href=r.image||'#';
document.getElementById('prev').disabled=index===0;document.getElementById('next').disabled=index===data.length-1;}
function step(d){index=Math.max(0,Math.min(data.length-1,index+d));show()}
pick.onchange=()=>{index=Number(pick.value);show()};document.getElementById('prev').onclick=()=>step(-1);document.getElementById('next').onclick=()=>step(1);
document.addEventListener('keydown',e=>{if(e.target.tagName==='SELECT')return;if(e.key==='ArrowLeft')step(-1);if(e.key==='ArrowRight')step(1)});show();</script></html>'''
    page=template.replace('__DATA__',payload).replace('__STATE__',html.escape(state)).replace('__DONE__',str(len(records))).replace('__TOTAL__',str(total))
    (out/'index.html').write_text(page,encoding='utf-8')


def main(argv=None):
    a=parse_args(argv);validate_settings(a)
    batch=a.current is None
    if batch and (a.p1_cur is not None or a.gt_tip is not None):
        raise ValueError('Folder mode: set P1_CURRENT/P2_CURRENT/GROUND_TRUTH_TIP=None; per-frame coordinates cannot be reused for an entire sequence.')
    role=data_role(a.reference)
    images=list_images(a.image_folder) if batch else [Path(a.current)]
    roles=[data_role(p) for p in images]
    root=Path(__file__).resolve().parent
    output_base=Path(a.output_dir).resolve()
    if not output_base.is_relative_to(root/'output'):
        raise ValueError('OUTPUT_DIR must be inside this project output/ directory.')
    for source in ([Path(a.image_folder).resolve()] if batch else []):
        if output_base.is_relative_to(source) or source.is_relative_to(output_base):
            raise ValueError('Keep input image directories and output directories separate.')
    if any(p.resolve().is_relative_to(output_base) for p in [*images,Path(a.reference)]):
        raise ValueError('Input images cannot be stored inside the chosen output directory.')
    R=imread_gray(a.reference)
    # Validate reference templates before starting a long sequence, even if an early image is corrupt.
    if a.p1_cur is None:
        for p in (a.p1_ref,a.p2_ref):
            track_reference_point(R,R,p,a.point_radius,a.point_search,a.min_ncc)
    out=output_base/('run_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    out.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).read_bytes();(out/'script_snapshot.py').write_bytes(source)
    config={'arguments':vars(a),'constants':{k:v for k,v in globals().items() if k.isupper() and isinstance(v,(str,int,float,bool,list,tuple,type(None)))},
            'source_sha256':hashlib.sha256(source).hexdigest(),'reference_role':role,'input_roles':sorted(set(roles)),
            'inputs':[str(p) for p in images],'expected_frames':len(images),'annotations_used_for_training':False,
            'reference_for_difference':'fixed original reference', 'sort':'natural filename order, current folder only'}
    (out/'run_config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    previous_image=R;previous_points=[a.p1_ref,a.p2_ref];previous_name=a.reference
    records=[];all_modes=[];state='COMPLETE';started=time.perf_counter()
    print(f'Images: {len(images)}; reference: {a.reference}; output: {out}',flush=True)
    try:
        for number,path in enumerate(images,1):
            frame=out/'frames'/f'{number:06d}';frame.mkdir(parents=True)
            record=dict(index=number,filename=path.name,status='ERROR',tip_x=None,tip_y=None,p1_x=None,p1_y=None,p2_x=None,p2_y=None,
                        tracking_source='',image='',detail=f'frames/{number:06d}/metadata.json',error='')
            C=None
            try:
                C=imread_gray(path)
                if C.shape!=R.shape:
                    raise ValueError(f'Reference/current size mismatch: {R.shape} vs {C.shape}')
                pair=argparse.Namespace(**vars(a));pair.current=str(path);pair.output_dir=str(frame)
                tracking=None
                if a.p1_cur is None:
                    if not batch or a.point_tracking=='reference':
                        template,anchors,source_name=R,[a.p1_ref,a.p2_ref],a.reference
                    else:
                        template,anchors,source_name=previous_image,previous_points,previous_name
                    matches=[track_reference_point(template,C,p,a.point_radius,a.point_search,a.min_ncc) for p in anchors]
                    pair.p1_cur,pair.p2_cur=[m[0] for m in matches]
                    tracking={'mode':'NCC_'+(a.point_tracking if batch else 'reference'),'source_image':str(source_name),'local_matches':[m[1] for m in matches]}
                    record['tracking_source']=str(source_name)
                result,metadata=process_pair(pair,R,C,tracking)
                previous_image=C;previous_points=metadata['current_points'];previous_name=str(path)
                selected=min((r for r in result if r['mode']==a.display_mode),key=lambda r:abs(r['threshold']-MAIN_DISPLAY_THRESHOLD))
                p1,p2=previous_points
                record.update(status='NO_TIP' if selected['tip_x'] is None else 'PROVISIONAL_TIP',tip_x=selected['tip_x'],tip_y=selected['tip_y'],
                              p1_x=p1[0],p1_y=p1[1],p2_x=p2[0],p2_y=p2[1],image=f'frames/{number:06d}/result_overlay.png')
                all_modes.extend(dict(frame_index=number,filename=path.name,**r) for r in result)
            except Exception as exc:
                record['error']=f'{type(exc).__name__}: {exc}'
                (frame/'metadata.json').write_text(json.dumps({'current':str(path),'status':'ERROR','error':record['error']},ensure_ascii=False,indent=2),encoding='utf-8')
                if C is not None:
                    fig,ax=plt.subplots(figsize=(8,6),constrained_layout=True)
                    ax.imshow(C,cmap='gray',vmin=0,vmax=255);ax.set_title('ERROR: ROI/result unavailable; see error message')
                    try:fig.savefig(frame/'error_original.png',dpi=100)
                    finally:plt.close(fig)
                    record['image']=f'frames/{number:06d}/error_original.png'
            records.append(record)
            print(f'[{number}/{len(images)}] {path.name}: {record["status"]} {record["error"]}',flush=True)
    except KeyboardInterrupt:
        state='INTERRUPTED'
    finally:
        if all_modes:
            pd.DataFrame(all_modes).to_csv(out/'all_mode_results.csv',index=False,encoding='utf-8-sig')
        else:
            pd.DataFrame(columns=['frame_index','filename','mode','threshold','tip_x','tip_y']).to_csv(out/'all_mode_results.csv',index=False,encoding='utf-8-sig')
        errors=sum(r['status']=='ERROR' for r in records)
        if state=='COMPLETE' and errors:state='COMPLETE_WITH_ERRORS'
        write_gallery(out,records,len(images),state)
        (out/'run_status.json').write_text(json.dumps({'status':state,'expected':len(images),'processed':len(records),'errors':errors,
                                                    'seconds':time.perf_counter()-started},indent=2),encoding='utf-8')
    print(f'{state}: {len(records)}/{len(images)}, errors={errors}\nViewer: {out/"index.html"}',flush=True)
    if a.open_results:
        try:webbrowser.open((out/'index.html').as_uri())
        except Exception as exc:print(f'Open index.html manually: {exc}')
    return out


if __name__=='__main__':
    main()



