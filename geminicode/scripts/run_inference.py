"""Batch inference runner executing sequential frame processing with zero GT access."""
import argparse
import json
import time
from pathlib import Path
import yaml

from geminicode.src.common import (
    PROJECT_ROOT,
    PACKAGE_ROOT,
    save_json,
    save_json_gz,
    save_csv,
    load_csv,
    sha256_file,
    get_source_file_hashes,
)
from geminicode.src.data_contract import SequenceLoader
from geminicode.src.engine import CrackTipEngine

def run_split_inference(
    run_dir: Path,
    split: str,
    cfg_override: dict = None,
    arm_name: str = "FULL",
    target_group: str = None,
):
    run_dir = Path(run_dir).resolve()
    manifest_path = run_dir / 'manifests/input_inventory.csv'
    assert manifest_path.exists(), f"Input inventory missing: {manifest_path}. Run inventory.py first."
    
    cfg_path = PACKAGE_ROOT / 'configs/unified_global.yaml'
    cfg = cfg_override or yaml.safe_load(cfg_path.read_text(encoding='utf-8'))
    
    # Pre-validation freeze check for locked split
    if split.lower() == 'locked':
        freeze_file = run_dir / 'manifests/prevalidation_freeze.json'
        assert freeze_file.exists(), "LOCKED validation cannot be run before prevalidation freeze! Run prevalidation_freeze.py first."
    
    loader = SequenceLoader(manifest_path)
    
    # Determine groups to process
    if target_group:
        groups = [target_group]
    elif split.lower() == 'dev':
        groups = ['group_a', 'three_point_bend']
    elif split.lower() == 'locked':
        groups = ['group_c']
    else:
        raise ValueError(f"Unknown split: {split}")
        
    code_hashes = get_source_file_hashes()
    code_hash_summary = next(iter(code_hashes.values())) if code_hashes else "N/A"
    config_hash = sha256_file(cfg_path)
    
    engine = CrackTipEngine(cfg, code_hash=code_hash_summary, config_hash=config_hash)
    
    raw_inf_dir = run_dir / 'raw_inference'
    raw_inf_dir.mkdir(parents=True, exist_ok=True)
    evidence_base = run_dir / 'evidence'
    evidence_base.mkdir(parents=True, exist_ok=True)
    diag_dir = run_dir / 'diagnostics'
    diag_dir.mkdir(parents=True, exist_ok=True)
    
    jsonl_path = raw_inf_dir / f'inference_{split}_{arm_name}.jsonl'
    csv_rows = []
    failure_records = []
    jump_records = []
    ref_records = []
    budget_records = []
    
    total_frames = 0
    valid_count = 0
    t0 = time.time()
    
    with open(jsonl_path, 'w', encoding='utf-8') as jsonl_f:
        for group in groups:
            print(f"[{arm_name}] Starting sequence processing for group '{group}' ({split.upper()})...", flush=True)
            grp_frames = 0
            
            # Initialize fixed reference for this group from frame 0
            first_frame_input = None
            for frame_in in loader.iter_group(group):
                if grp_frames == 0:
                    first_frame_input = frame_in
                    engine.initialize(
                        fixed_ref_img=frame_in.fixed_ref_img,
                        fixed_ref_p1=frame_in.fixed_ref_p1,
                        fixed_ref_p2=frame_in.fixed_ref_p2,
                    )
                
                meta = {'frame_key': f"{group}_{frame_in.frame_id}"}
                out = engine.process_frame(
                    current_img=frame_in.current_img,
                    current_p1=frame_in.current_p1,
                    current_p2=frame_in.current_p2,
                    prev_img=frame_in.prev_img,
                    prev_p1=frame_in.prev_p1,
                    prev_p2=frame_in.prev_p2,
                    frame_meta=meta,
                )
                
                d = out.to_dict()
                d['group'] = group
                d['frame_id'] = frame_in.frame_id
                d['tracking_num'] = frame_in.tracking_num
                d['arm'] = arm_name
                
                # Write JSONL
                jsonl_f.write(json.dumps(d, ensure_ascii=False) + '\n')
                
                # Accumulate CSV summary row
                csv_rows.append({
                    'group': group,
                    'frame_id': frame_in.frame_id,
                    'tracking_num': frame_in.tracking_num,
                    'status': out.status,
                    'tip_x': out.tip_x,
                    'tip_y': out.tip_y,
                    'selected_track_id': out.selected_track_id,
                    'preferred_uncertain_tip_x': out.preferred_uncertain_tip[0] if out.preferred_uncertain_tip else None,
                    'preferred_uncertain_tip_y': out.preferred_uncertain_tip[1] if out.preferred_uncertain_tip else None,
                    'fixed_ref_channel': out.channels.get('fixed'),
                    'prev_ref_channel': out.channels.get('prev'),
                    'failure_stage': out.failure_stage,
                    'failure_reason': out.failure_reason,
                    'budget_exhausted': out.budget.get('exhausted'),
                    'time_ms': out.budget.get('time_ms'),
                    'num_candidates': out.diagnostics.get('num_candidates', 0),
                    'flags': ";".join(out.flags),
                })
                
                # Diagnostic records
                if out.status != 'VALID':
                    failure_records.append({
                        'group': group,
                        'frame_id': frame_in.frame_id,
                        'status': out.status,
                        'failure_stage': out.failure_stage,
                        'failure_reason': out.failure_reason,
                        'flags': ";".join(out.flags),
                    })
                    
                for cand in out.candidate_tips:
                    if cand.get('jump_dist', 0) > 40.0:
                        jump_records.append({
                            'group': group,
                            'frame_id': frame_in.frame_id,
                            'track_id': cand.get('track_id'),
                            'jump_dist': cand.get('jump_dist'),
                            'evidence_state': cand.get('evidence_state'),
                            'flags': ";".join(cand.get('flags', [])),
                        })
                        
                ref_records.append({
                    'group': group,
                    'frame_id': frame_in.frame_id,
                    'fixed_status': out.channels.get('fixed'),
                    'prev_status': out.channels.get('prev'),
                    'fixed_conf': out.diagnostics.get('fixed_conf'),
                    'prev_conf': out.diagnostics.get('prev_conf'),
                })
                
                budget_records.append({
                    'group': group,
                    'frame_id': frame_in.frame_id,
                    'exhausted': out.budget.get('exhausted'),
                    'expansions': out.budget.get('expansions'),
                    'pixels_scanned': out.budget.get('pixels_scanned'),
                    'time_ms': out.budget.get('time_ms'),
                })
                
                # Save evidence JSON
                frame_ev_dir = evidence_base / group / str(frame_in.frame_id)
                frame_ev_dir.mkdir(parents=True, exist_ok=True)
                save_json_gz(frame_ev_dir / 'result.json.gz', d, overwrite=True)
                
                grp_frames += 1
                total_frames += 1
                if out.status == 'VALID':
                    valid_count += 1
                    
                if grp_frames % 50 == 0:
                    print(f"  Processed {grp_frames} frames in group '{group}'... (valid: {valid_count})", flush=True)
                    
            print(f"Group '{group}' completed: {grp_frames} frames.", flush=True)
            
    # Save CSV tables
    save_csv(raw_inf_dir / f'results_{split}_{arm_name}.csv', csv_rows, overwrite=True)
    if arm_name == "FULL":
        save_csv(diag_dir / f'failure_stages_{split}.csv', failure_records, overwrite=True)
        save_csv(diag_dir / f'abnormal_jump_audit_{split}.csv', jump_records, overwrite=True)
        save_csv(diag_dir / f'reference_quality_{split}.csv', ref_records, overwrite=True)
        save_csv(diag_dir / f'budget_audit_{split}.csv', budget_records, overwrite=True)
        
    elapsed = time.time() - t0
    print(f"Inference [{split.upper()} - {arm_name}] complete: {total_frames} frames in {elapsed:.1f}s ({valid_count}/{total_frames} VALID).", flush=True)
    return csv_rows

def main():
    parser = argparse.ArgumentParser(description="Run crack tip batch inference")
    parser.add_argument('--run', required=True, help="Run directory")
    parser.add_argument('--split', required=True, choices=['dev', 'locked'], help="Dataset split")
    parser.add_argument('--arm', default='FULL', help="Ablation arm name")
    parser.add_argument('--group', default=None, help="Optional group filter")
    args = parser.parse_args()
    
    run_dir = Path(args.run)
    if not run_dir.is_absolute():
        run_dir = PROJECT_ROOT / run_dir
        
    run_split_inference(run_dir=run_dir, split=args.split, arm_name=args.arm, target_group=args.group)

if __name__ == '__main__':
    main()
