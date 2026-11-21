"""Current-image notch and rolling dark-valley path. All coordinates here are ROI-local."""
import cv2
import numpy as np
from numba import njit


def locate_root(raw, hint, scale):
    """Find the end of the thick connected notch body in the current exposure."""
    x, y = np.rint(hint).astype(int)
    h, w = raw.shape
    radius = max(16, round(.23 * scale))
    left, top = max(0, x - 2*radius), max(0, y-radius)
    patch = raw[top:min(h,y+radius+1), left:min(w,x+radius+1)]
    if min(patch.shape) < 7:
        return None
    # Opening removes thin outgrowths before locating the notch mouth.
    body = cv2.morphologyEx((patch < 57).astype('uint8'), cv2.MORPH_OPEN,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(body, 8)
    candidates = []
    for i in range(1,n):
        bx, by, width, height, area = stats[i]
        if bx > 2 or width < 10 or height < 5 or area < 50:
            continue
        end = bx + width - 1
        ys = np.flatnonzero(labels[:, end] == i)
        pt = (int(left+end), int(top+np.median(ys)))
        candidates.append((np.hypot(pt[0]-x, pt[1]-y), pt, i, end))
    if not candidates:
        return None
    _,center,component,end=min(candidates)
    starts=[center]
    # Follow the forward-facing boundary of the same body on either side of the opening.
    for yy in range(max(0,center[1]-top-round(.15*scale)),
                    min(labels.shape[0],center[1]-top+round(.15*scale)+1),3):
        xs=np.flatnonzero(labels[yy]==component)
        if len(xs) and end-xs[-1]<=max(12,.13*scale):
            starts.append((int(left+xs[-1]),int(top+yy)))
    return list(dict.fromkeys(starts))


def valley_image(raw):
    gray = raw.astype(np.float32)
    response = np.zeros_like(gray)
    for radius in (2,4,7):
        flanks = np.minimum(gray[:-2*radius],gray[2*radius:])
        depth = np.maximum(0, flanks-gray[radius:-radius])
        response[radius:-radius] = np.maximum(response[radius:-radius],
                                              np.where(flanks>40,depth,0))
    # Local pooling along x suppresses isolated single-pixel impulses.
    longitudinal = cv2.GaussianBlur(response,(5,3),1.0,.65)
    evidence = .55*response+.45*longitudinal
    resid = gray-cv2.medianBlur(raw,3)
    sample = resid[::4,::4]
    noise = max(1., float(np.median(np.abs(sample-np.median(sample))))*1.4826)
    # Score relative to off-line responses in the same longitudinal slice.
    background = np.percentile(evidence[::3],85,axis=0).astype(np.float32)
    threshold = np.maximum(4., 1.0*background + 1.8*noise)
    return np.ascontiguousarray(evidence/threshold), response


@njit(cache=False)
def trace_windowed(signal, bonus, x, y):
    """Rescore each short horizon from the last committed pixel, retaining competing rows."""
    h,w = signal.shape
    path = []
    weak = 0
    slope = 0.
    while x+1 < w:
        horizon = min(20,w-1-x)
        low, high = max(0,y-22),min(h,y+23)
        height = high-low
        prev = np.full(height,-1e10)
        prev[y-low] = 0
        parent = np.zeros((horizon,height),np.int16)
        for t in range(horizon):
            nxt = np.full(height,-1e10)
            for i in range(height):
                best = -1e10
                for j in range(max(0,i-2),min(height,i+3)):
                    value = prev[j]-.48*abs(i-j)-.16*abs(i-j-slope)
                    if value>best:
                        best=value
                        parent[t,i]=j
                v=signal[low+i,x+t+1]
                nxt[i]=best+min(4.,v)-1.1+bonus[low+i,x+t+1]
            prev=nxt
        idx=np.argmax(prev)
        line=np.empty(horizon,np.int32)
        for t in range(horizon-1,-1,-1):
            line[t]=low+idx
            idx=parent[t,idx]
        for t in range(min(5,horizon)):
            yy=line[t]
            x+=1
            slope=.7*slope+.3*(yy-y)
            y=yy
            v=signal[y,x]
            path.append((x,y,v))
            weak = 0 if v>=1. else weak+1
            if weak>=4:
                return path
        if len(path)>=12:
            count=0
            for j in range(len(path)-10,len(path)):
                count+=path[j][2]>=1.
            if count<5:
                break
    return path


def follow(signal, response, bonus, root):
    x,y=root
    # Attach only to a supported pixel in the immediate cross-section at the body tip.
    seeds = range(max(0,y-4),min(signal.shape[0],y+5))
    seed = max(seeds,key=lambda j: min(4.,signal[j,x])-.35*abs(j-y))
    track=trace_windowed(signal,bonus,x,seed)
    hits=[i for i,(px,py,v) in enumerate(track) if v>=1. and response[py,px]>=3.]
    if not hits or hits[0]>2:
        return dict(status='NO_ROOT_ATTACHMENT',points=[],tip=None)
    # Final observation needs neighboring measured support. Save gaps separately.
    end=next((i for i in reversed(hits) if sum(j>=i-5 and j<=i for j in hits)>=4),None)
    if end is None or end+1<9:
        return dict(status='SHORT_ROOT_TRACE',points=[[int(track[j][0]),int(track[j][1])] for j in hits],tip=None)
    points=[[int(track[j][0]),int(track[j][1])] for j in hits if j<=end]
    status='VALID' if points[-1][0]<signal.shape[1]-2 else 'ROI_BOUNDARY'
    return dict(status=status,points=points,tip=points[-1] if status=='VALID' else None)


def prepare(raw, hint, scale):
    starts=locate_root(raw,hint,scale)
    if starts is None:
        return None
    root=starts[0]
    radius=max(35,round(.55*scale))
    top=max(0,root[1]-radius)
    bottom=min(raw.shape[0],root[1]+radius+1)
    left=max(0,min(x for x,y in starts)-10)
    sl=np.s_[top:bottom,left:]
    signal,response=valley_image(raw[sl])
    return sl,(left,top),[(x-left,y-top) for x,y in starts],signal,response


def predict(prepared, bonus):
    if prepared is None:
        return dict(status='NO_NOTCH_BODY',root=None,points=[],tip=None)
    _,(left,top),starts,signal,response=prepared
    root=starts[0]
    result=follow(signal,response,bonus,root)
    # Test both lips when the forward root alone produces only a short attachment.
    # An alternative must continue beyond the front of the thick notch body.
    if result['tip'] is None or result['tip'][0]-root[0]<55:
        for start in starts[1:]:
            trial=follow(signal,response,bonus,start)
            if trial['tip'] and trial['tip'][0]>=starts[0][0]+9:
                if result['tip'] is None or trial['tip'][0]>result['tip'][0]+2:
                    result,root=trial,start
    result['points']=[[x+left,y+top] for x,y in result['points']]
    if result['tip'] is not None:
        result['tip']=result['points'][-1]
    result['root']=[root[0]+left,root[1]+top]
    return result

