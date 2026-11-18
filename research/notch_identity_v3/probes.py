"""Deterministic counterexamples independent of experimental images and labels."""
import csv
import sys
from pathlib import Path
import cv2
import numpy as np
from scipy.spatial import cKDTree
from . import detector
from research.raw_notch_trace_v2b import detector as baseline

RUN=Path(__file__).resolve().parents[2]/'output/experiments/notch_identity_v3_20261118_r01'
CASES=('P1_upper','P1_lower','P2_fade','P3_parallel','P3_oblique','P4_ring','P4_open')


def scene(case,zoom,noise,seed):
    base=np.full((160,310),172,np.uint8)
    body=np.array([[0,52],[70,72],[70,88],[0,108]])
    cv2.fillPoly(base,[body],22)
    target=[]
    depth=95 if noise==1 else 65
    if case.startswith('P1'):
        sign=-1 if case.endswith('upper') else 1
        for side,contrast in ((-sign,.35*depth),(sign,depth)):
            line=[]
            for x in range(70,202):
                y=round(80+side*8*max(0,1-(x-70)/72)+.035*max(0,x-142))
                line.append((x,y))
            cv2.polylines(base,[np.array(line)],False,round(172-contrast),1)
            if side==sign:
                target=line
    elif case=='P2_fade':
        target=[(x,80+round(.04*(x-70))) for x in range(70,200)]
        for x,y in target:
            base[y,x]=round(172-depth*min(1,(200-x)/32))
        for x in range(202,290,4):
            cv2.circle(base,(x,85+round(2*np.sin(x))),1,157,-1)
    elif case=='P3_parallel':
        cv2.line(base,(75,80),(155,80),72,1)
        cv2.line(base,(77,75),(152,75),94,1)
    elif case=='P3_oblique':
        cv2.line(base,(75,83),(143,60),69,1)
    elif case=='P4_ring':
        cv2.ellipse(base,(98,80),(28,9),0,0,360,70,1)
    elif case=='P4_open':
        cv2.fillPoly(base,[np.array([[66,72],[105,49],[73,80],[105,111],[66,88]])],26)
    img=cv2.resize(base,None,fx=zoom,fy=zoom,interpolation=cv2.INTER_AREA if zoom<1 else cv2.INTER_LINEAR)
    img=np.clip(img.astype(float)+np.random.default_rng(seed).normal(0,noise,img.shape),0,255).astype('uint8')
    return img,np.rint(np.array([70,80])*zoom).astype(int),288*zoom,np.asarray(target)*zoom


def run(stages):
    rows=[]
    for case in CASES:
        for zoom in (.5,1.,2.):
            for noise in (1,5):
                for seed in (17,31):
                    img,hint,scale,gt=scene(case,zoom,noise,seed)
                    for stage in ['r02']+stages:
                        model=baseline if stage=='r02' else detector
                        if stage in ('s2','s3','s3t'):
                            from . import terminal as model
                            prep=model.prepare(img,hint,scale,stage)
                        else:
                            prep=model.prepare(img,hint,scale)
                        result=model.predict(prep,np.zeros_like(prep[3]) if prep is not None else None)
                        tip=result['tip']
                        valid=tip is not None
                        error=float(np.linalg.norm(gt[-1]-tip)/zoom) if len(gt) and valid else None
                        coverage=float((cKDTree(result['points']).query(gt)[0]<=2.5*zoom).mean()) if len(gt) and result['points'] else 0.
                        passed=(valid and error<=10 and (not case.startswith('P1') or coverage==1.)) if len(gt) else not valid
                        rows.append(dict(case=case,stage=stage,zoom=zoom,noise=noise,seed=seed,status=result['status'],
                                         valid=valid,normalized_error=error,coverage=coverage if len(gt) else None,
                                         false_positive=valid and not len(gt),passed=passed))
    with (RUN/'probes.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


if __name__=='__main__':
    run(sys.argv[1:])


