"""Per-column signed evidence in mouth coordinates (x forward, y normal)."""
import cv2
import numpy as np
from research.notch_identity_v54.terminal import increments


def evidence(scene, prior, ridge, dual, core, signed, dipole, band):
    gray = scene.local[:, scene.front:].astype(np.float32)
    scale = max(1., scene.span)
    radius = max(1, round(.012 * scene.scale))
    kernel = np.ones((2 * radius + 1, 1), np.uint8)
    contrast = cv2.dilate(gray, kernel) - cv2.erode(gray, kernel)
    bright = np.clip((gray - scene.black - .68 * scale) / (.27 * scale), 0, 1)
    smooth = np.clip(1 - contrast / max(4 * scene.noise, .12 * scale), 0, 1)
    reflection = (bright * smooth).T
    floor = max(1., 2.7 * scene.noise, .030 * scale)
    red = np.tanh(np.maximum(0, signed) / (2 * floor)) * np.tanh(ridge / 2.)
    blue = np.tanh(np.maximum(0, -signed) / (2 * floor))
    gain = red * (.45 + .55 * core) + .35 * dual
    blank = (.72 - .53 * reflection) * (1 - np.clip(gain, 0, 1))
    # Centering the distal response suppresses diffuse red ahead of the visible ridge.
    prior_weight = .36 + .38 * np.exp(-np.arange(len(prior),dtype=np.float32)[:,None] / (.14 * scene.scale))
    net = (1.65 * gain + prior_weight * np.clip(prior,-1.2,1.4)
           - blank - .85 * blue - .40 * dipole - .14)
    net[~np.isfinite(prior)] = -np.inf
    rows = np.arange(net.shape[1]) + scene.origin[1]
    net[:, (rows < band[0]) | (rows >= band[1])] = -np.inf
    return np.ascontiguousarray(net, dtype=np.float32), red, blue, reflection


def trace(path, field, dual, red, blue, reflection, scale):
    x, y = path.T
    steps = increments(field, path)
    measured = dual[x,y]
    breaks = np.flatnonzero(np.diff(np.r_[False, ~measured, False]))
    penalty = np.zeros(len(x))
    for a,b in zip(breaks[::2],breaks[1::2]):
        left = max(0,a-1)
        right = min(len(y)-1,b)
        width = max(1,right-left)
        reach = max(2,round(.025*scale))
        k = max(0,left-reach)
        j = min(len(y)-1,right+reach)
        incoming = (y[left]-y[k])/max(1,left-k)
        outgoing = (y[j]-y[right])/max(1,j-right)
        displacement = abs(y[right]-y[left]-np.clip(incoming,-1,1)*width)
        angle = abs(np.arctan(incoming)-np.arctan(outgoing))
        penalty[right] += .32*displacement + 1.15*angle
    curve = np.cumsum(steps-penalty)
    end = int(np.argmax(curve))+1
    info = dict(red=float(red[x[:end],y[:end]].sum()),blue=float(blue[x[:end],y[:end]].sum()),
                geometry_cost=float(penalty[:end].sum()),dual_columns=int(measured[:end].sum()),
                max_blank=max((min(b,end)-a for a,b in zip(breaks[::2],breaks[1::2]) if a<end),default=0),
                reflection_mean=float(reflection[x[:end],y[:end]].mean()),peak=float(curve[end-1]),
                drawdown=float(np.max(np.maximum.accumulate(curve)-curve)),start_x=int(x[0]))
    return path[:end], info, curve
