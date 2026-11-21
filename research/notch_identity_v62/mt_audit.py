"""Replay the sealed MT mapping with a passive NCC diagnostic, then actually shift both anchor pairs."""
from concurrent.futures import ProcessPoolExecutor
from unittest.mock import patch
import json
import math
import cv2
import numpy as np
from research.notch_identity_v60 import domain as mapping
from research.notch_identity_v514.registration import align
from research.unified_crack_tip_60q.features import CONFIG, scene_geometry
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b, inputs
from .run import frozen, workers


def trace(rows, current, fixed, box, radius, center, noise, contrast, mask_fn, material):
    result = align(current, fixed, box, radius, center, noise, contrast, mask_fn, material)
    assert center == (0, 0) and radius == 5
    h, w = current.shape
    l, t, r, bot = box
    l, t = max(l,radius), max(t,radius)
    r, bot = min(r,w-radius), min(bot,h-radius)
    sigma = support = extended = saturated_current = saturated_ref = None
    threshold = max(1.8*noise,.02*contrast)
    reason = 'BOX_TOO_SMALL'
    if min(r-l,bot-t) >= 2*radius+1:
        mask = mask_fn(np.arange(l,r)[None,:], np.arange(t,bot)[:,None]) & material[t:bot,l:r]
        area = fixed[t-radius:bot+radius,l-radius:r+radius]
        if not np.isfinite(area).all():
            missing = cv2.dilate((~np.isfinite(area)).astype('uint8'),np.ones((11,11),np.uint8))
            mask &= ~missing[radius:-radius,radius:-radius].astype(bool)
        saturated_current=float((current[t:bot,l:r]>=250).mean())
        saturated_ref=float((fixed[t:bot,l:r]>=250).mean())
        support = float(mask.mean())
        reason = 'MATERIAL_SUPPORT_LT35'
        if support >= .35:
            sigma = float(np.std(current[t:bot,l:r][mask]))
            if result['status'] == 'LOW_TEXTURE':
                reason = 'LOW_TEXTURE'
            else:
                peak, gap = result['ncc'], result['margin']
                reason = ('NCC_LT075_AND_MARGIN' if peak < .75 and gap < .012 else
                          'NCC_LT075' if peak < .75 else 'AMBIGUOUS_MARGIN' if gap < .012 else
                          'NCC_LT084' if peak < .84 else 'OK')
                # A wider *diagnostic* window, with material eroded for its larger footprint.
                # This test can shrink the support and never supplies an applied displacement.
                expanded_material = cv2.erode(material.astype('uint8'),np.ones((11,11),np.uint8),
                                             borderType=cv2.BORDER_CONSTANT,borderValue=0).astype(bool)
                extended = align(current,fixed,box,10,center,noise,contrast,mask_fn,expanded_material)
    assert (reason in ('BOX_TOO_SMALL','MATERIAL_SUPPORT_LT35')) == (result['status']=='INSUFFICIENT_CONTEXT')
    assert (reason == 'OK') == (result['status']=='OK' and result['ncc']>=.84)
    shift = result['shift']
    outside = bool(extended and extended['status']=='OK' and extended['ncc']>=.84
                   and max(map(abs,extended['shift']))>radius)
    rows.append(dict(reason=reason,support_fraction=support,texture_rms=sigma,texture_floor=threshold,
                     saturated_current=saturated_current,saturated_ref=saturated_ref,
                     width=r-l,height=bot-t,peak=result['ncc'],margin=result['margin'],shift=shift,
                     at_radius=bool(shift and max(map(abs,shift))==radius),
                     wide_status=extended['status'] if extended else None,wide_peak=extended['ncc'] if extended else None,
                     wide_shift=extended['shift'] if extended else None,wide_trusted_outside=outside))
    return result


def replay(job):
    i, box, saved, nominal = job
    meta=inputs.metadata('group_h',i)['input']
    cur=b.old.current(meta['current'],meta['image_sha'])
    fixed=b.old.read_fixed(meta['reference'],meta['ref_sha'])
    cp,rp=map(np.array,(saved['cur'],saved['ref']))
    x,y,r,bot=box
    prep=b.terminal.prepare(cur[y:bot,x:r],cp.mean(0)-[x,y],b.SCALE,'S2',fixed[y:bot,x:r],rp.mean(0)-[x,y])
    mapped=mapping.ReferenceMap(cur,fixed,cp,rp,box,prep,'S2')
    audit=[]
    if saved['windows']:
        with patch.object(mapping,'align',lambda *args:trace(audit,*args)):
            mapped(saved['bounds'][2]-x)
        assert np.array_equal(mapped.bounds,saved['bounds'])
        k=0
        for win, expected in zip(mapped.info['windows'],saved['windows'],strict=True):
            assert win==expected
            for side in ('up','down','single'):
                if side=='single' and audit[k-2]['reason']=='OK' and audit[k-1]['reason']=='OK':
                    continue
                row=audit[k]
                assert row['peak']==win[side+'_ncc']
                row.update(frame=i,x0=win['x0'],x1=win['x1'],side=side)
                k+=1
        assert k==len(audit)
    alt_cp,alt_rp=cp-[150,0],rp-[150,0]
    bounds=scene_geometry(cur,alt_cp,fixed,alt_rp,None,CONFIG)['bounds']
    l,t,r,bot=bounds
    raw,ref=cur[t:bot,l:r],fixed[t:bot,l:r]
    origin=np.array([l,t])
    prep=b.terminal.prepare(raw,alt_cp.mean(0)-origin,b.SCALE,'S2',ref,alt_rp.mean(0)-origin)
    shifted=mapping.ReferenceMap(cur,fixed,alt_cp,alt_rp,bounds,prep,'S2')
    pred,_=b.run_mode(raw,ref,alt_cp,alt_rp,origin,'S2','full',aligned=shifted,prepared=prep)
    d=pred['diagnostics']['dual']
    return audit,dict(frame=i,dx=-150,ref_nominal=nominal['reference_apex'],ref_shifted=d.get('reference_apex'),
                      cur_nominal=nominal['current_apex'],cur_shifted=d.get('current_apex'),
                      ref_equal=nominal['reference_apex'] is not None and nominal['reference_apex']==d.get('reference_apex'),
                      cur_equal=nominal['current_apex'] is not None and nominal['current_apex']==d.get('current_apex'),
                      status_equal=pred['status']==nominal['status'],path_equal=pred['points']==nominal['points'],
                      tip_drift=math.dist(pred['tip'],nominal['tip']) if pred['tip'] and nominal['tip'] else None,
                      windows=len(saved['windows']),ncc_attempts=len(audit),
                      zero=bool(saved['windows']) and all(w['up_mode']==w['down_mode']=='zero' for w in saved['windows']))


def main():
    frozen()
    path=b.OUT/'group_h.jsonl'
    assert b.sha(path)==b.read(b.OUT/'group_h_seal.json')['predictions']
    tasks=[]
    for rec in map(json.loads,path.open(encoding='utf8')):
        m=rec['placements']['original']['S2']['full']
        d=m['diagnostics']['dual']
        nominal={**{k:d.get(k) for k in ('reference_apex','current_apex')},**{k:m[k] for k in ('status','tip','points')}}
        tasks.append((rec['frame'],rec['box'],rec['mappings']['original']['S2'],nominal))
    rows=[]; frames=[]
    with ProcessPoolExecutor(4,initializer=workers) as pool:
        for diag,frame in pool.map(replay,tasks,chunksize=3):
            rows.extend(diag)
            frames.append(frame)
    assert len(frames)==410
    write_csv(b.OUT/'ncc_window_rejections.csv',rows)
    write_csv(b.OUT/'group_h_full_shift.csv',frames)


if __name__=='__main__':
    main()
