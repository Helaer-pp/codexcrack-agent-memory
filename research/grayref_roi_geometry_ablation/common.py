import json, numpy as np
from pathlib import Path
from grayref_simplified_evidence_v0.common import ROOT,sha,get,put,putgz,readgz,rows,csvwrite,write_bytes,save_npz,imread,utc
OLD=ROOT/'output/experiments/grayref_simplified_evidence_v0_20261113_r01'
GROUPS={'group_a':551,'group_c':562,'three_point_bend':520}
SOURCE=Path(__file__).parent

def manifest(path=None,full=True):
    raw=rows(path or OLD/'input_manifest.csv');data=[r for r in raw if r['group'] in GROUPS]
    if path and len(raw)!=len(data):raise ValueError('Excluded group in explicit manifest')
    if full:
        assert {g:sum(r['group']==g for r in data) for g in GROUPS}==GROUPS
        assert len({(r['group'],r['frame_id']) for r in data})==1633
    return data

def directory(run,row):return Path(run)/'frames'/row['group']/row['frame_id']

def cached(row,verify=True):
    if row['group'] not in GROUPS:raise ValueError('Excluded group')
    d=OLD/'galleries'/row['group']/row['frame_id'];m=get(d/'frame_manifest.json')
    if verify:
        for key in ['roi_gray.npz','roi_difference.npz','result.json.gz','candidate_graphs.npz']:
            assert sha(d/key)==m['files'][key]['sha256'],key
    r=readgz(d/'result.json.gz');assert r['identity']['image_sha']==row['image_sha'] and r['identity']['reference_points']==row['reference_points'] and r['identity']['current_points']==row['current_points']
    with np.load(d/'roi_gray.npz') as q:gray={k:q[k] for k in ['raw','valley_raw','background']}
    with np.load(d/'roi_difference.npz') as q:diff={k:q[k] for k in q.files if k!='roi'}
    a=dict(gray=[gray['raw']],valley=[gray['valley_raw']],background=gray['background'],material=diff['valid_material_mask'],roi=r['roi'],noise=r['noise'],threshold=r['threshold'],diff=diff,reference_windows=r['reference_windows'],reference_status=r['reference_status'],notch=r['notch'])
    return a,r,dict(path=str(d.relative_to(ROOT)).replace('\\','/'),files={k:m['files'][k]['sha256'] for k in ['roi_gray.npz','roi_difference.npz','result.json.gz','candidate_graphs.npz']},input_sha=row['image_sha'],reference_sha=row['ref_sha'],cache_hit=True,cache_not_new_inference=True)

def source_hashes():
    files=list(SOURCE.rglob('*.py'))+list(SOURCE.glob('*.md'))+list(SOURCE.glob('*.ps1'))+list(SOURCE.glob('*.json'))+list(SOURCE.glob('*.yaml'))
    files+=[ROOT/'research/grayref_simplified_evidence_v0/algorithm.py',ROOT/'research/grayref_simplified_evidence_v0/common.py',ROOT/'research/grayref_simplified_evidence_v0/offline_evaluate.py']
    return {str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sorted(files)}

def check_sources(run):assert get(Path(run)/'source_hashes.json')['files']==source_hashes(),'Frozen source changed'

def native_result(r):
    q={k:v for k,v in r.items() if k not in ['native_output_state','native_tip','geometry_boundary']};q['mode']='C_FUSION_RAW';return q
