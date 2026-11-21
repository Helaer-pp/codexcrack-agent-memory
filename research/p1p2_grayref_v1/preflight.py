"""Metadata-only adapter and exact frozen-source identity check; no inference/GT reads."""
from pathlib import Path
import argparse
import collections
import csv
import hashlib
import json
import math
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/python'))
from crackv4.dataset_policy import require,role

EXPECTED_SHA='2e2e5ebef80ab33e486c561b6dec09ee15d23033020cc1886a7de24c7ce2baf6'
INVENTORY=ROOT/'output/runs/uctt_r05f_20261111_r01/input_inventory_allowed.csv'
EXPECTED_COUNTS={'group_a':551,'ct2':468,'group_h':410,'ct3':136}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def read_csv(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write_csv(path,records):
    with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in records for k in r)))
        writer.writeheader();writer.writerows(records)

def write_json(path,data):
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')

def source_points(path):
    """Read coordinate fields only; never import historical detector tips/paths."""
    path=Path(path)
    if path.suffix.lower()=='.csv':
        return {int(r['坐标num']):([[float(r[f'P{k}x']),float(r[f'P{k}y'])] for k in [1,2]],r['图片名']) for r in read_csv(path)}
    result={}
    for line in path.read_text(encoding='utf8',errors='replace').splitlines():
        values=re.findall(r'[-+]?\d+(?:\.\d+)?',line)
        if len(values)==5:
            index=int(values[0]);numbers=list(map(float,values[1:]));result[index]=([numbers[:2],numbers[2:]],None)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen-root',type=Path,default=ROOT/'P1P2_GrayRef_V1_Frozen')
    parser.add_argument('--output',type=Path,default=ROOT/'output/runs/p1p2_grayref_v1_20261112_r01')
    args=parser.parse_args();out=args.output.resolve()
    if not out.is_relative_to((ROOT/'output').resolve()):raise ValueError('Output must remain within project output/')
    if (out/'freeze_manifest.json').exists():raise RuntimeError('Do not overwrite a frozen run')
    (out/'inputs').mkdir(parents=True,exist_ok=True)
    required=['paired_p1p2_roi_V1_FROZEN.py','README_中文.md','batch_validate_V1.py','baseline/expected_summary_results.csv']
    availability={name:(args.frozen_root/name).is_file() for name in required}
    detector=args.frozen_root/required[0]
    actual=sha(detector) if detector.is_file() else None
    identity_ok=actual==EXPECTED_SHA
    grouped=collections.defaultdict(list)
    for row in read_csv(INVENTORY):
        if role(row['dataset_id'])!='DEVELOPMENT':continue
        require(row['dataset_id'],'development');grouped[row['dataset_id']].append(row)
    manifest=[];audit=[];summary=[];issues=[];point_hashes={}
    for group in EXPECTED_COUNTS:
        sequence=sorted(grouped[group],key=lambda r:int(r['frame_order']))
        if len(sequence)!=EXPECTED_COUNTS[group]:issues.append(f'{group}: count {len(sequence)} != {EXPECTED_COUNTS[group]}')
        if not sequence:continue
        reference=sequence[0];rp=json.loads(reference['points']);point_cache={};missing=0;badpoints=0;mismatch=0
        for row in sequence:
            source=Path(row['p1p2_source']);order=int(row['frame_order']);pp=json.loads(row['points']);frame=int(row['frame_id'])
            if str(source) not in point_cache:
                point_cache[str(source)]=source_points(source);point_hashes[str(source)]=sha(source)
            independent=point_cache[str(source)].get(order)
            mapping_ok=independent is not None and independent[0]==pp and (independent[1] is None or independent[1]==Path(row['source_image']).name)
            exists=Path(row['source_image']).is_file();valid=all(math.isfinite(v) for point in pp for v in point) and pp[0][1]<pp[1][1] and all(0<=p[0]<int(row['width']) and 0<=p[1]<int(row['height']) for p in pp)
            missing+=not exists;badpoints+=not valid;mismatch+=not mapping_ok
            if row['reference_image']!=reference['source_image']:issues.append(f'{group}/{frame}: reference mapping inconsistent')
            if frame!=order+1:issues.append(f'{group}/{frame}: frame ID/order inconsistent')
            record=dict(group=group,frame_id=frame,split='DEVELOPMENT',reference=reference['source_image'],current=row['source_image'],p1_ref_x=rp[0][0],p1_ref_y=rp[0][1],p2_ref_x=rp[1][0],p2_ref_y=rp[1][1],p1_cur_x=pp[0][0],p1_cur_y=pp[0][1],p2_cur_x=pp[1][0],p2_cur_y=pp[1][1]);manifest.append(record)
            audit.append(dict(group=group,frame_id=frame,frame_order=order,reference_frame_id=int(reference['frame_id']),reference_frame_order=0,filename=Path(row['source_image']).name,current_exists=exists,reference_exists=Path(reference['source_image']).is_file(),points_valid=valid,point_source=str(source),point_source_mapping_equal=mapping_ok,point_source_kind='historical_coordinate_csv' if source.suffix.lower()=='.csv' else 'original_tracking_txt',coordinates='original_image_pixels_xy',point_identity='P1_above_P2',historical_image_sha256=row['sha256'],historical_width=row['width'],historical_height=row['height'],image_bytes_read_this_preflight=False))
        summary.append(dict(group=group,frames=len(sequence),expected=EXPECTED_COUNTS[group],missing_files=missing,invalid_points=badpoints,point_mapping_mismatches=mismatch))
    write_csv(out/'inputs/manifest.csv',manifest);write_csv(out/'inputs/input_audit.csv',audit);write_csv(out/'inputs/group_inventory.csv',summary)
    protected=[ROOT/'output/build/src/cpp/a/Release/CrackV4.dll',ROOT/'output/releases/A_Win64_OpenCV440/bin/CrackV4.dll']+list((ROOT/'src/cpp/a').rglob('*'))
    protected={str(p.relative_to(ROOT)):sha(p) for p in protected if p.is_file()}
    result=dict(status='INPUTS_PREPARED_SOURCE_READY' if identity_ok and all(availability.values()) else 'AWAITING_EXACT_FROZEN_PACKAGE',expected_sha256=EXPECTED_SHA,actual_frozen_sha256=actual,frozen_source_identity_ok=identity_ok,required_files=availability,frozen_root=str(args.frozen_root),existing_easy_edit_sha256=sha(ROOT/'paired_p1p2_roi_easy_edit.py'),inventory_source=str(INVENTORY),inventory_source_sha256=sha(INVENTORY),point_source_hashes=point_hashes,protected_production=protected,development_frames=len(manifest),groups=summary,issues=issues,inference_frames=0,image_bytes_read=0,validation_image_bytes_read=0,excluded_image_bytes_read=0,annotations_read=0,limitations=['CT3 coordinates from explicit historical CSV; separate original tracking file unavailable.','Image existence checked; image hashes/dimensions above are historical metadata, not newly verified.','No V1 source or parameter identity inferred from easy_edit; require the exact frozen package.'])
    write_json(out/'preflight_status.json',result)
    print(json.dumps({k:result[k] for k in ['status','development_frames','groups','required_files','actual_frozen_sha256','issues']},ensure_ascii=True,indent=2))

if __name__=='__main__':main()
