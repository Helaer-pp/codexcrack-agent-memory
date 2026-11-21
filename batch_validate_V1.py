#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch replay for the immutable P1/P2 gray/reference V1 detector.

The detector is executed as an unmodified subprocess per frame.
Ground-truth labels are read AFTER the complete inference loop and never
passed to the detector. Requires Python 3.9+, numpy/pandas/scipy/opencv/matplotlib
for the frozen detector; batch runner itself uses only the standard library.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time
from collections import defaultdict

FIELDS = ["group", "frame_id", "split", "reference", "current",
          "p1_ref_x", "p1_ref_y", "p2_ref_x", "p2_ref_y",
          "p1_cur_x", "p1_cur_y", "p2_cur_x", "p2_cur_y"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def sanitize(s: str) -> str:
    return re.sub(r'[^\w.-]', '_', s, flags=re.UNICODE)[:80] or 'unknown'


def pt(row: dict, prefix: str, *, required: bool) -> str | None:
    x, y = row.get(prefix + '_x','').strip(), row.get(prefix + '_y','').strip()
    if not x and not y and not required:
        return None
    if not x or not y:
        raise ValueError(f'{prefix} x/y must both be present')
    coords = [float(x), float(y)]
    if not all(map(math.isfinite, coords)):
        raise ValueError(f'Invalid non-finite coordinates for {prefix}')
    return f'{coords[0]},{coords[1]}'


def read_csv(path: Path) -> list[dict]:
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None):
    if fields is None:
        fields = list(dict.fromkeys(k for r in rows for k in r.keys()))
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def percentile(vals, p):
    if not vals:
        return None
    vals = sorted(vals)
    r = (len(vals) - 1) * p / 100
    i = int(r)
    return vals[i] + (vals[min(i+1,len(vals)-1)] - vals[i]) * (r - i)


def resolve_path(manifest: Path, path: str) -> Path:
    x = Path(path).expanduser()
    return (manifest.parent / x).resolve() if not x.is_absolute() else x.resolve()


def main():
    root = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', required=True, type=Path, help='CSV input, format examples/manifest_example.csv')
    p.add_argument('--output', required=True, type=Path, help='New output folder; refuses existing nonempty folder unless --overwrite')
    p.add_argument('--detector', default=str(root/'paired_p1p2_roi_V1_FROZEN.py'), type=Path)
    p.add_argument('--labels', default=None, type=Path, help='Optional offline labels CSV, read only after inference')
    p.add_argument('--python', default=sys.executable, help='Python executable for detector')
    p.add_argument('--dry-run', action='store_true', help='Check input manifest without executing detector')
    a = p.parse_args()

    manifest = a.manifest.resolve()
    if not manifest.is_file():
        p.error(f'Manifest not found: {manifest}')
    detector = a.detector.resolve()
    if not detector.is_file():
        p.error(f'Detector not found: {detector}')
    if a.output.resolve() == root or a.output.resolve() == manifest.parent:
        p.error('Output directory cannot be the frozen source folder or manifest folder')
    rows = read_csv(manifest)
    if not rows:
        p.error('Empty manifest')
    missing_fields = [k for k in FIELDS if k not in rows[0]]
    if missing_fields:
        p.error('Manifest missing fields: '+', '.join(missing_fields))
    records, seen = [], set()
    for n, row in enumerate(rows, 2):
        group = row['group'].strip()
        frame_id = row['frame_id'].strip()
        split = row['split'].strip().upper()
        if not group or not frame_id or split not in ('DEVELOPMENT','VALIDATION_ONLY'):
            p.error(f'Manifest row {n}: group/frame_id missing or invalid split: {split}')
        key = (group,frame_id)
        if key in seen:
            p.error(f'Duplicate group/frame_id {key}')
        seen.add(key)
        try:
            rpath, cpath = (resolve_path(manifest,row[k].strip()) for k in ('reference','current'))
            p1r,p2r = pt(row,'p1_ref',required=True),pt(row,'p2_ref',required=True)
            p1c,p2c = pt(row,'p1_cur',required=False),pt(row,'p2_cur',required=False)
            if (p1c is None) != (p2c is None):
                raise ValueError('Both current P1 and P2 required, or neither')
        except (ValueError,TypeError) as e:
            p.error(f'Manifest row {n}: {e}')
        for fpath in (rpath,cpath):
            if not fpath.is_file():
                p.error(f'Manifest row {n}: missing image: {fpath}')
        records.append(dict(group=group, frame_id=frame_id, split=split,
                            ref=rpath, cur=cpath, p1r=p1r,p2r=p2r,p1c=p1c,p2c=p2c))
    out = a.output.resolve()
    digest = sha256(detector)
    source_digest = sha256(root/'paired_p1p2_roi_V1_FROZEN.py') if (root/'paired_p1p2_roi_V1_FROZEN.py').is_file() else None
    if digest != source_digest:
        p.error('Detector SHA256 differs from frozen V1! Abort to prevent silent parameter edits.')
    print(f'Validated manifest: {len(records)} frames, {len(set(q["group"] for q in records))} groups; frozen_SHA256={digest}')
    if a.dry_run:
        print('DRY RUN: no inference, output or labels read')
        return 0
    if out.exists() and any(out.iterdir()):
        p.error('Output folder already nonempty; use a new --output to preserve prior runs')
    out.mkdir(parents=True, exist_ok=True)
    manifest_hash = sha256(manifest)
    run_details = []
    for index, row in enumerate(records, 1):
        subdir = out/'cases'/sanitize(row['group'])/sanitize(row['frame_id'])
        if subdir.exists() and any(subdir.iterdir()):
            p.error(f'Case output already exists; refusing to mix runs: {subdir}')
        subdir.mkdir(parents=True,exist_ok=True)
        cmd = [a.python, str(detector), '--reference',str(row['ref']), '--current',str(row['cur']),
               '--p1-ref',row['p1r'],'--p2-ref',row['p2r'],'--output-dir',str(subdir)]
        if row['p1c'] is not None:
            cmd += ['--p1-cur',row['p1c'],'--p2-cur',row['p2c']]
        tic = time.perf_counter()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, errors='replace', check=False)
            return_code = result.returncode
            stdout,stderr = result.stdout,result.stderr
        except Exception as exc:
            return_code = -1
            stdout,stderr = '',f'{type(exc).__name__}: {exc}'
        elapsed = time.perf_counter()-tic
        (subdir/'runner_stdout.txt').write_text(stdout,encoding='utf-8')
        (subdir/'runner_stderr.txt').write_text(stderr,encoding='utf-8')
        info = {'group':row['group'],'frame_id':row['frame_id'],'split':row['split'],
                'reference':str(row['ref']),'current':str(row['cur']),
                'p1_source':'provided' if row['p1c'] is not None else 'NCC',
                'return_code':return_code, 'runtime_wall_seconds':round(elapsed,4),
                'status':'OK' if return_code==0 else 'ERROR',
                'output_dir':str(subdir)}
        run_details.append(info)
        print(f'[{index}/{len(records)}] {row["group"]}/{row["frame_id"]}: {info["status"]} {elapsed:.2f}s', flush=True)

    # GT is intentionally loaded after all inference calls, never passed on command line.
    labelmap = {}
    if a.labels is not None:
        labels_path = a.labels.resolve()
        for r in read_csv(labels_path):
            labelmap[(r['group'].strip(),r['frame_id'].strip())] = r

    all_results = []
    for rec in run_details:
        key = (rec['group'],rec['frame_id'])
        label = labelmap.get(key)
        vis = str(label.get('visibility','')).strip().upper() if label else ''
        case_dir = Path(rec['output_dir'])
        roi_gt_inside = 'UNKNOWN'
        if vis == 'VISIBLE' and label is not None and (case_dir/'metadata.json').is_file():
            try:
                roi = json.loads((case_dir/'metadata.json').read_text(encoding='utf-8'))['ROI']
                gx, gy = float(label['tip_x']), float(label['tip_y'])
                roi_gt_inside = 'YES' if (roi['x_left'] <= gx < roi['x_right'] and roi['y_top'] <= gy <= roi['y_bottom']) else 'NO'
            except (ValueError,KeyError,TypeError,FileNotFoundError):
                pass
        summary_path = case_dir/'summary_results.csv'
        metrics = read_csv(summary_path) if rec['status']=='OK' and summary_path.is_file() else []
        if not metrics:
            metrics = [dict(mode=m,threshold=str(t),tip_x='',tip_y='') for m in ('joint','current') for t in (8,10,12)]
        for m in metrics:
            tipx,tipy = m.get('tip_x','').strip(),m.get('tip_y','').strip()
            gt_error = None
            if vis == 'VISIBLE' and tipx and tipy and label:
                try:
                    gt_error = math.hypot(float(tipx)-float(label['tip_x']),float(tipy)-float(label['tip_y']))
                except (ValueError,KeyError,TypeError):
                    gt_error = None
            all_results.append({'group':rec['group'],'frame_id':rec['frame_id'],'split':rec['split'],
                                'status':rec['status'],'visibility':vis or 'UNLABELED',
                                'roi_contains_gt':roi_gt_inside,
                                'mode':m.get('mode'), 'threshold':m.get('threshold'),
                                'tip_x':tipx,'tip_y':tipy,'gt_error_px':None if gt_error is None else round(gt_error,4),
                                'observed_points':m.get('observed_points',''),
                                'visited_columns':m.get('visited_columns',''),
                                'stop_reason':m.get('stop_reason',''),
                                'runtime_wall_seconds':rec['runtime_wall_seconds'],
                                'output_dir':rec['output_dir']})
    write_csv(out/'all_frames.csv',run_details)
    write_csv(out/'all_results.csv',all_results)

    by_group = defaultdict(list)
    for r in all_results:
        by_group[(r['group'],r['split'],r['mode'],str(r['threshold']))].append(r)
    aggregates=[]
    for (group,split,mode,threshold),rs in sorted(by_group.items()):
        vis = [r for r in rs if r['visibility']=='VISIBLE']
        scored=[float(r['gt_error_px']) for r in vis if r['gt_error_px'] is not None]
        aggregates.append({'group':group,'split':split,'mode':mode,'threshold':threshold,
                           'frames':len(rs),'inference_ok':sum(r['status']=='OK' for r in rs),
                           'visible_gt':len(vis),'gt_scored':len(scored),
                           'gt_missing_or_error':len(vis)-len(scored),
                           'visible_gt_inside_roi':sum(r['roi_contains_gt']=='YES' for r in vis),
                           'visible_gt_outside_roi':sum(r['roi_contains_gt']=='NO' for r in vis),
                           'tip_le3_all_visible':sum(x<=3 for x in scored),
                           'tip_le5_all_visible':sum(x<=5 for x in scored),
                           'tip_le10_all_visible':sum(x<=10 for x in scored),
                           'tip_gt100_all_visible':sum(x>100 for x in scored),
                           'tip_gt500_all_visible':sum(x>500 for x in scored),
                           'tip_p50_scored_only_px':percentile(scored,50),
                           'tip_p95_scored_only_px':percentile(scored,95),
                           'runtime_p50_wall_seconds':percentile([float(r['runtime_wall_seconds']) for r in rs],50),
                           'runtime_p95_wall_seconds':percentile([float(r['runtime_wall_seconds']) for r in rs],95)})
    write_csv(out/'group_summary.csv',aggregates)
    provenance = {'algorithm_id':'P1P2_GrayRef_V1_FROZEN',
                  'frozen_source':str(detector),'source_sha256':digest,
                  'manifest_sha256':manifest_hash,
                  'manifest':str(manifest),'labels':str(a.labels.resolve()) if a.labels else None,
                  'labels_loaded_after_all_inference':True,
                  'frame_count':len(records),'successful_frames':sum(x['status']=='OK' for x in run_details),
                  'warning':'Provisional tip only; no independent physical crack identity/visibility confirmation. '
                            'No threshold changed from frozen source. Wall timing includes Python startup, image I/O and rendering.'}
    (out/'run_identity.json').write_text(json.dumps(provenance,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Wrote:', out/'group_summary.csv',out/'all_results.csv',out/'run_identity.json')
    return 0 if all(x['status']=='OK' for x in run_details) else 2


if __name__ == '__main__':
    raise SystemExit(main())
