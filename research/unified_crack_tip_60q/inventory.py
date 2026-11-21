"""Metadata-only locked inventory. Locked pixels/anchors are opened only after freeze."""
import argparse,concurrent.futures,platform,shutil,subprocess,sys
from .common import *

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();run=ROOT/a.run
    assert run.resolve().is_relative_to(ROOT/'output')
    run.mkdir(parents=True,exist_ok=False)
    prior=ROOT/'output/experiments/grayref_roi_geometry_group_a_only_20261113_r01'
    raw=rows(prior/'input_manifest.csv');data=[]
    # Discard historical coordinate fields: source TXT is read only for the permitted split.
    keep=['group','frame_id','tracking_num','reference','current','image_sha','ref_sha','point_source','point_source_sha','point_kind','width','height']
    for r in raw:
        if r['group'] not in GROUPS:continue
        q={k:r[k] for k in keep};q['role']=ROLES[r['group']];data.append(q)
    assert {g:sum(r['group']==g for r in data) for g in GROUPS}==GROUPS
    assert len({(r['group'],r['frame_id']) for r in data})==1633
    for g in GROUPS:
        part=sorted([r for r in data if r['group']==g],key=lambda r:int(r['tracking_num']))
        assert [int(r['tracking_num']) for r in part]==list(range(GROUPS[g]))
        for i,r in enumerate(part):
            r['previous_actual']=part[i-1]['current'] if i else '';r['previous_tracking_num']=i-1 if i else ''
            assert Path(r['current']).is_file() and Path(r['point_source']).is_file()
            r['original_sequence']='original_tracking_num';r['pixel_verification']='DEFERRED_UNTIL_SPLIT_EXECUTION'
    data.sort(key=lambda r:(list(GROUPS).index(r['group']),int(r['tracking_num'])))
    csvwrite(run/'manifests/input_inventory.csv',data)
    put(run/'manifests/task_protocol.json',dict(spec='UCTIP-60Q-v1.0',roles=ROLES,groups=GROUPS,visible_expected=VISIBLE,
        role_override='Latest explicitly invoked documents move three_point_bend from historical VALIDATION_ONLY to this task DEV only; global policy file retained.',
        annotations='Independent post-seal comparison only; no model training and no GT parameter search in r01',locked='Previously exposed, not new blind test',
        locked_pixels_points_not_opened=True,metadata_source_sha=sha(prior/'input_manifest.csv'),documents={x:sha(ROOT/x) for x in ['Gemini_Agent_Unified_Crack_Tip_Development_Prompt.md','Unified_Crack_Tip_Algorithm_Development_Spec.md']}))
    selected=rows(ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv')
    selected=[r for r in selected if r['dataset_id'] in GROUPS]
    put(run/'manifests/annotation_metadata.json',dict(counts={g:sum(r['dataset_id']==g for r in selected) for g in GROUPS},archive_exists=(ROOT/'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip').is_file(),visible_counts='Verify independently after each inference seal; expected19/15/20, no labels opened here'))
    dirs=['src/cpp/a','baseline/frozen_a','research/p1p2_grayref_v1','research/p1p2_grayref_v2','research/grayref_simplified_evidence_v0','research/grayref_roi_geometry_ablation',
          'output/runs/p1p2_grayref_v1_20261112_r01','output/experiments/p1p2_grayref_v2_20261112_r01','output/experiments/grayref_simplified_evidence_v0_20261113_r01','output/experiments/grayref_roi_geometry_group_a_only_20261113_r01']
    files=[]
    for d in dirs:
        q=ROOT/d;assert q.is_dir(),d;files.extend(p for p in q.rglob('*') if p.is_file())
    files.append(ROOT/'output/releases/A_Win64_OpenCV440/bin/CrackV4.dll')
    print('Protecting '+str(len(files))+' historical source/output files',flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        hashes={str(p.relative_to(ROOT)).replace('\\','/'):h for p,h in zip(files,pool.map(sha,files))}
    put(run/'manifests/baseline_protection_manifest.json',dict(utc=utc(),files=hashes,count=len(hashes),byte_hash_only_no_locked_result_interpretation=True))
    status=subprocess.run(['git','status','--short'],cwd=ROOT,capture_output=True,text=True)
    put(run/'manifests/environment.json',dict(utc=utc(),python=sys.version,platform=platform.platform(),numpy=np.__version__,opencv=cv2.__version__,free_disk=shutil.disk_usage(ROOT).free,git_status=status.stdout if status.returncode==0 else status.stderr.strip()))
    write(run/'reports/data_contract_audit.md','# Input contract\n\nMetadata resolves GROUP_A551 + three_point_bend520 DEV, group_c562 LOCKED, tracking_num0-based contiguous and frame_id1-based. Fixed reference from original manifest; previous_actual is immediately preceding original frame, never last successful detection. All paths exist. Locked pixel/header/hash and original point parsing deferred until prevalidation freeze; original uint8 decoding and TXT-to-frame checks required then. No locked image/point values or labels used for development.\n\nHistorical six-group split superseded only for this explicitly requested round. CT2/group_h/CT3/group_x are not in queues. Labels only evaluated after sealed results. Original GT is assumed to denote the rightmost crack tip, not independently revalidated.\n\nOld outputs are byte-hashed for protection, not used for parameter selection; actual original sources must still be checked at execution. No git repository is reported verbatim in environment.json.\n')
    write(run/'reports/BLOCKERS.md','# Blockers\n\nNo input-path blocker found in metadata inventory. Locked pixel/point verification and label denominators are deliberately pending their authorized stages, not claimed PASS. Algorithm, full replay, ablations and final acceptance remain pending.\n')
    print('INVENTORY READY '+str(run),flush=True)

if __name__=='__main__':main()
