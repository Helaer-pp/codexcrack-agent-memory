"""P2 Script: Run pre-registered single-arm and combinational ablations on DEV."""
import argparse
import copy
from pathlib import Path
import yaml

from geminicode.src.common import PROJECT_ROOT, PACKAGE_ROOT, save_csv
from geminicode.scripts.run_inference import run_split_inference
from geminicode.scripts.evaluate import evaluate_predictions

ABLATION_ARMS = [
    'FULL',
    '-FIXED_REF',
    '-PREV_REF',
    '-TRACKING',
    '-GAP',
    '-DYNAMIC_ROI',
    '-MULTITRACK',
    '-OPENING',
    '-FIXED_REF -PREV_REF',
    '-TRACKING -MULTITRACK',
    '-GAP -DYNAMIC_ROI',
]

def get_ablation_config(base_cfg: dict, arm: str) -> dict:
    cfg = copy.deepcopy(base_cfg)
    
    if '-FIXED_REF' in arm:
        cfg['scoring']['fixed_diff_weight'] = 0.0
        
    if '-PREV_REF' in arm:
        cfg['scoring']['prev_diff_weight'] = 0.0
        
    if '-TRACKING' in arm:
        cfg['multitrack']['history_hysteresis_bonus'] = 0.0
        cfg['multitrack']['max_lost_frames'] = 0
        
    if '-GAP' in arm:
        cfg['connectivity']['max_inferred_gap_px'] = 0.0
        
    if '-DYNAMIC_ROI' in arm:
        cfg['dynamic_roi']['max_expansions_per_frame'] = 0
        cfg['dynamic_roi']['max_lateral_expansions'] = 0
        
    if '-MULTITRACK' in arm:
        cfg['budget']['max_candidate_paths'] = 1
        cfg['multitrack']['branch_split_dist_min_px'] = 9999.0
        
    if '-OPENING' in arm:
        # Opening proxy weight zeroed
        cfg['scoring']['origin_proximity_weight'] = 0.0
        
    return cfg

def run_all_ablations(run_dir: Path, arms: list[str] = None):
    run_dir = Path(run_dir).resolve()
    base_cfg_path = PACKAGE_ROOT / 'configs/unified_global.yaml'
    base_cfg = yaml.safe_load(base_cfg_path.read_text(encoding='utf-8'))
    
    selected_arms = arms or ABLATION_ARMS
    summary_rows = []
    
    for arm in selected_arms:
        arm_slug = arm.replace(' ', '_')
        print(f"\n=======================================================", flush=True)
        print(f"RUNNING ABLATION ARM: {arm} (slug: {arm_slug})", flush=True)
        print(f"=======================================================", flush=True)
        
        arm_cfg = get_ablation_config(base_cfg, arm)
        # 1. Run inference on DEV if not already executed
        csv_file = run_dir / f'raw_inference/results_dev_{arm_slug}.csv'
        if not csv_file.exists():
            run_split_inference(
                run_dir=run_dir,
                split='dev',
                cfg_override=arm_cfg,
                arm_name=arm_slug,
            )
        else:
            print(f"Results for arm '{arm_slug}' already exist at {csv_file}, evaluating directly.", flush=True)
        
        # 2. Evaluate against visible GT on DEV
        stats = evaluate_predictions(
            run_dir=run_dir,
            split='dev',
            arm_name=arm_slug,
        )
        
        for g, s in stats.items():
            row = {
                'arm': arm,
                'arm_slug': arm_slug,
                'group': g,
                'split': s['split'],
                'N_visible': s['N_visible_gt'],
                'valid_count': s['valid_count'],
                'coverage_pct': s['coverage_pct'],
                'hit10_count': s['hit10_count'],
                'hit10_pct': s['hit10_rate_pct'],
                'severe100_count': s['severe100_count'],
                'mean_error_px': s['mean_error_px'],
                'median_error_px': s['median_error_px'],
                'oracle_hit10_count': s['oracle_hit10_count'],
                'group_accepted': s['group_accepted'],
            }
            summary_rows.append(row)
            
    # Save ablation summary table
    abl_dir = run_dir / 'ablations'
    abl_dir.mkdir(parents=True, exist_ok=True)
    save_csv(abl_dir / 'ablation_summary.csv', summary_rows, overwrite=True)
    print(f"\nAblations completed! Summary saved to {abl_dir / 'ablation_summary.csv'}", flush=True)

def main():
    parser = argparse.ArgumentParser(description="P2 Pre-registered Ablations Runner")
    parser.add_argument('--run', required=True, help="Run output directory")
    parser.add_argument('--arms', default=None, help="Comma-separated string of arms to run")
    args = parser.parse_args()
    
    run_dir = Path(args.run)
    if not run_dir.is_absolute():
        run_dir = PROJECT_ROOT / run_dir
    selected_arms = [a.strip() for a in args.arms.split(',')] if args.arms else None
    run_all_ablations(run_dir, selected_arms)

if __name__ == '__main__':
    main()
