"""Offline GT evaluation comparing sealed predictions against human annotations."""
import argparse
import json
import math
import zipfile
from pathlib import Path
import numpy as np

from geminicode.src.common import (
    PROJECT_ROOT,
    GROUPS,
    ROLES,
    VISIBLE,
    save_json,
    save_csv,
    load_csv,
)

LABELS_ZIP = PROJECT_ROOT / 'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip'
SELECTED_FRAMES_CSV = PROJECT_ROOT / 'output/runs/uctt_r05f_20261111_r01/selected_frames.csv'

ACCEPTANCE_THRESHOLDS = {
    'group_a': {'N': 19, 'min_hit10': 14, 'min_valid': 16, 'max_severe100': 0},
    'three_point_bend': {'N': 15, 'min_hit10': 11, 'min_valid': 12, 'max_severe100': 0},
    'group_c': {'N': 20, 'min_hit10': 14, 'min_valid': 16, 'max_severe100': 1},
}

def load_visible_gt_annotations(groups: list[str]) -> dict[tuple[str, int], dict]:
    """Load visible GT crack tips from sealed annotations snapshot."""
    assert LABELS_ZIP.exists(), f"Labels snapshot missing: {LABELS_ZIP}"
    assert SELECTED_FRAMES_CSV.exists(), f"Selected frames CSV missing: {SELECTED_FRAMES_CSV}"
    
    selected_rows = load_csv(SELECTED_FRAMES_CSV)
    gt_map = {}
    
    with zipfile.ZipFile(LABELS_ZIP) as z:
        for r in selected_rows:
            g = r['dataset_id']
            if g not in groups:
                continue
            fid = int(r['frame_id'])
            data = json.loads(z.read(r['selected_json']))
            
            # Extract tip and path
            tips = [s['points'][0] for s in data['shapes'] if s['label'] == 'crack_tip']
            paths = [s['points'] for s in data['shapes'] if s['label'] == 'crack_path']
            
            if tips:
                gt_map[(g, fid)] = {
                    'tip': (float(tips[0][0]), float(tips[0][1])),
                    'path': paths[0] if paths else [],
                    'visibility': 'VISIBLE',
                    'json_member': r['selected_json'],
                }
            else:
                gt_map[(g, fid)] = {
                    'tip': None,
                    'path': paths[0] if paths else [],
                    'visibility': 'UNCERTAIN',
                    'json_member': r['selected_json'],
                }
    return gt_map

def evaluate_predictions(
    run_dir: Path,
    split: str,
    arm_name: str = "FULL",
):
    run_dir = Path(run_dir).resolve()
    eval_dir = run_dir / 'offline_evaluation'
    eval_dir.mkdir(parents=True, exist_ok=True)
    
    results_csv = run_dir / f'raw_inference/results_{split}_{arm_name}.csv'
    assert results_csv.exists(), f"Inference results missing: {results_csv}"
    
    pred_rows = load_csv(results_csv)
    pred_map = {(r['group'], int(r['frame_id'])): r for r in pred_rows}
    
    # Read full JSONL to get candidate tips for Oracle evaluation
    jsonl_path = run_dir / f'raw_inference/inference_{split}_{arm_name}.jsonl'
    jsonl_candidates = {}
    if jsonl_path.exists():
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)
                jsonl_candidates[(item['group'], int(item['frame_id']))] = item.get('candidate_tips', [])
                
    groups = ['group_a', 'three_point_bend'] if split == 'dev' else ['group_c']
    gt_map = load_visible_gt_annotations(groups)
    
    detailed_rows = []
    group_stats = {}
    
    for g in groups:
        visible_items = {k: v for k, v in gt_map.items() if k[0] == g and v['visibility'] == 'VISIBLE'}
        N = len(visible_items)
        expected_N = VISIBLE.get(g)
        assert N == expected_N, f"Visible GT count mismatch for {g}: {N} vs expected {expected_N}"
        
        valid_count = 0
        hit3 = 0
        hit5 = 0
        hit10 = 0
        hit20 = 0
        severe100 = 0
        errors = []
        oracle_errors = []
        oracle_hit10 = 0
        
        for (grp, fid), gt_info in sorted(visible_items.items(), key=lambda x: x[0][1]):
            gt_tip = gt_info['tip']
            pred = pred_map.get((grp, fid))
            assert pred is not None, f"Missing prediction for frame {grp}_{fid}"
            
            status = pred['status']
            tip_x = float(pred['tip_x']) if pred.get('tip_x') not in [None, 'None', ''] else None
            tip_y = float(pred['tip_y']) if pred.get('tip_y') not in [None, 'None', ''] else None
            
            err = None
            if status == 'VALID' and tip_x is not None and tip_y is not None:
                valid_count += 1
                err = float(math.hypot(tip_x - gt_tip[0], tip_y - gt_tip[1]))
                errors.append(err)
                if err <= 3.0: hit3 += 1
                if err <= 5.0: hit5 += 1
                if err <= 10.0: hit10 += 1
                if err <= 20.0: hit20 += 1
                if err > 100.0: severe100 += 1
            
            # Oracle Best-of-Candidates evaluation
            cands = jsonl_candidates.get((grp, fid), [])
            best_cand_err = None
            if cands:
                cand_errs = [float(math.hypot(c['x'] - gt_tip[0], c['y'] - gt_tip[1])) for c in cands if 'x' in c and 'y' in c]
                if cand_errs:
                    best_cand_err = min(cand_errs)
                    oracle_errors.append(best_cand_err)
                    if best_cand_err <= 10.0:
                        oracle_hit10 += 1
                        
            detailed_rows.append({
                'group': grp,
                'frame_id': fid,
                'status': status,
                'tip_x': tip_x,
                'tip_y': tip_y,
                'gt_x': gt_tip[0],
                'gt_y': gt_tip[1],
                'error_px': round(err, 3) if err is not None else None,
                'hit10': (err is not None and err <= 10.0),
                'severe100': (err is not None and err > 100.0),
                'oracle_min_error_px': round(best_cand_err, 3) if best_cand_err is not None else None,
                'oracle_hit10': (best_cand_err is not None and best_cand_err <= 10.0),
                'failure_stage': pred.get('failure_stage'),
                'failure_reason': pred.get('failure_reason'),
                'flags': pred.get('flags'),
            })
            
        thresh = ACCEPTANCE_THRESHOLDS[g]
        passed_hit10 = (hit10 >= thresh['min_hit10'])
        passed_valid = (valid_count >= thresh['min_valid'])
        passed_severe = (severe100 <= thresh['max_severe100'])
        group_pass = passed_hit10 and passed_valid and passed_severe
        
        group_stats[g] = {
            'group': g,
            'split': ROLES[g],
            'arm': arm_name,
            'N_visible_gt': N,
            'valid_count': valid_count,
            'coverage_pct': round(valid_count / N * 100.0, 1),
            'hit3_count': hit3,
            'hit5_count': hit5,
            'hit10_count': hit10,
            'hit10_rate_pct': round(hit10 / N * 100.0, 1),
            'hit20_count': hit20,
            'severe100_count': severe100,
            'severe100_rate_pct': round(severe100 / N * 100.0, 1),
            'mean_error_px': round(float(np.mean(errors)), 2) if errors else None,
            'median_error_px': round(float(np.median(errors)), 2) if errors else None,
            'p95_error_px': round(float(np.percentile(errors, 95)), 2) if len(errors) >= 5 else None,
            'max_error_px': round(float(np.max(errors)), 2) if errors else None,
            'oracle_hit10_count': oracle_hit10,
            'oracle_hit10_pct': round(oracle_hit10 / N * 100.0, 1),
            'threshold_min_hit10': thresh['min_hit10'],
            'threshold_min_valid': thresh['min_valid'],
            'threshold_max_severe100': thresh['max_severe100'],
            'passed_hit10': passed_hit10,
            'passed_coverage': passed_valid,
            'passed_severe': passed_severe,
            'group_accepted': group_pass,
        }
        
    save_csv(eval_dir / f'detailed_errors_{split}_{arm_name}.csv', detailed_rows, overwrite=True)
    stats_list = list(group_stats.values())
    save_csv(eval_dir / f'metrics_summary_{split}_{arm_name}.csv', stats_list, overwrite=True)
    
    print("\n================== OFFLINE EVALUATION RESULTS ==================", flush=True)
    for g, s in group_stats.items():
        print(f"Group '{g}' ({s['split']}) - Arm: {arm_name}", flush=True)
        print(f"  N: {s['N_visible_gt']} | VALID: {s['valid_count']} ({s['coverage_pct']}%) | Hit@10: {s['hit10_count']} ({s['hit10_rate_pct']}%) | Severe>100: {s['severe100_count']}", flush=True)
        print(f"  Errors (px): Mean={s['mean_error_px']} | Median={s['median_error_px']} | Max={s['max_error_px']}", flush=True)
        print(f"  Oracle Best-of-Candidates Hit@10: {s['oracle_hit10_count']}/{s['N_visible_gt']} ({s['oracle_hit10_pct']}%)", flush=True)
        print(f"  Threshold Check: Hit@10>={s['threshold_min_hit10']} ({s['passed_hit10']}) | VALID>={s['threshold_min_valid']} ({s['passed_coverage']}) | Severe<={s['threshold_max_severe100']} ({s['passed_severe']})", flush=True)
        print(f"  ---> Group Status: {'PASSED' if s['group_accepted'] else 'FAILED'}", flush=True)
    print("=================================================================\n", flush=True)
    
    return group_stats

def main():
    parser = argparse.ArgumentParser(description="Offline GT Evaluator")
    parser.add_argument('--run', required=True, help="Run output directory")
    parser.add_argument('--split', required=True, choices=['dev', 'locked'], help="Dataset split")
    parser.add_argument('--arm', default='FULL', help="Ablation arm name")
    args = parser.parse_args()
    
    run_dir = Path(args.run)
    if not run_dir.is_absolute():
        run_dir = PROJECT_ROOT / run_dir
    evaluate_predictions(run_dir=run_dir, split=args.split, arm_name=args.arm)

if __name__ == '__main__':
    main()
