"""Run the same detector for all experiments, sealing predictions before scoring."""
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from research.notch_identity_v58_strict import batch as old
from research.notch_identity_v58_material.region import geometry
from research.notch_identity_v58_strict.jitter import synchronized
from research.notch_identity_v58_bright.evaluate import patch_min
from research.v3_labelme_comparison.infer import read_csv
from . import terminal


ROOT,OLD,SELECT,GROUPS=old.ROOT,old.OLD,old.SELECT,old.GROUPS
OUT=ROOT/'output/experiments/v515_clean_fast_r01'
sha,save,read=old.sha,old.save,old.read
POLICY=ROOT/'output/experiments/v58_material_group_c_r07/freeze.json'
BASELINE=ROOT/'output/experiments/v58_valley_bridge_20261120_r04'
SCALE=288.
ALGS=terminal.STAGES


def sources():
    here=Path(__file__).parent
    from research.notch_identity_v514.batch import sources as baseline_sources
    deps=[here/n for n in ('terminal.py','transition.py','domain.py','corridor.py','gates.py','__init__.py','batch.py','probes.py')]
    return {**baseline_sources(),**{str(p.relative_to(ROOT)):sha(p) for p in deps}}


def run_mode(image,fixed,pair,rpair,origin,stage,mode,surf=None,aligned=None,locked_warp=False,prepared=False):
    start=time.perf_counter()
    prep=terminal.prepare(image,pair.mean(0)-origin,SCALE,stage,fixed,rpair.mean(0)-origin) if prepared is False else ((*prepared[:2],stage) if prepared else None)
    if mode=='full' and aligned is None:raise ValueError('Pre-aligned reference required')
    result=terminal.predict(prep,None,aligned if mode=='full' else None,surf)
    elapsed=time.perf_counter()-start
    d=result['diagnostics']['dual']
    if 'front' in d:
        d['front']+=origin[0]
        d['roi_y']=(np.asarray(d['roi_y'])+origin[1]).tolist()
        d['material_band']=(np.asarray(d['material_band'])+origin[1]).tolist()
    for branch in d['branches']:
        for key in ('root','tip','base_tip'):
            if branch[key] is not None:branch[key]=(np.asarray(branch[key])+origin).tolist()
    if d.get('coarse_tip'):d['coarse_tip']=(np.asarray(d['coarse_tip'])+origin).tolist()
    if d.get('peak'):d['peak']=(np.asarray(d['peak'])+origin).tolist()
    result=old.globalize(result,origin)
    result.update(old.lengths(result,dict(points_geometry=pair,points_observed=True)))
    if surf:surf['origin']+=origin
    return result,elapsed


