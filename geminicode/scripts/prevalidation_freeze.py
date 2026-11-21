"""P3 Script: Prevalidation Freeze - Seal code, configs, DEV predictions, and protocol."""
import argparse
import json
from pathlib import Path

from geminicode.src.common import (
    PROJECT_ROOT,
    PACKAGE_ROOT,
    utc_now,
    sha256_file,
    save_json,
    get_source_file_hashes,
)

def perform_prevalidation_freeze(run_dir: Path):
    run_dir = Path(run_dir).resolve()
    manifest_dir = run_dir / 'manifests'
    assert manifest_dir.exists(), f"Manifest directory missing: {manifest_dir}"
    
    # Check that DEV inference outputs exist
    dev_csv = run_dir / 'raw_inference/results_dev_FULL.csv'
    dev_jsonl = run_dir / 'raw_inference/inference_dev_FULL.jsonl'
    assert dev_csv.exists() and dev_jsonl.exists(), "DEV FULL inference must be completed before prevalidation freeze!"
    
    # Hash all source files in geminicode
    src_hashes = get_source_file_hashes()
    cfg_path = PACKAGE_ROOT / 'configs/unified_global.yaml'
    cfg_hash = sha256_file(cfg_path)
    
    dev_csv_hash = sha256_file(dev_csv)
    dev_jsonl_hash = sha256_file(dev_jsonl)
    
    freeze_manifest = {
        'status': 'PREVALIDATION_FROZEN',
        'utc': utc_now(),
        'protocol': 'UCTIP-60Q-v1.0',
        'config_file': str(cfg_path.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'config_sha256': cfg_hash,
        'dev_predictions_csv_sha256': dev_csv_hash,
        'dev_predictions_jsonl_sha256': dev_jsonl_hash,
        'source_files_count': len(src_hashes),
        'source_hashes': src_hashes,
        'frozen_rules': [
            'Objective: Rightmost verified crack tip argmax(image_x) among verified branches; no crack length.',
            'No displacement hard threshold: Jumps trigger independent RAW/ref recheck; no MOTION_REJECTED.',
            'Dual references: Independent degradation; missing prev ref on frame 0 is normal degradation.',
            'No GT leakage: Zero labels used during inference.',
            'Locked validation: group_c single run authorized only after this freeze seal.',
        ],
    }
    
    save_json(manifest_dir / 'code_config_hashes.json', src_hashes, overwrite=True)
    save_json(manifest_dir / 'prevalidation_freeze.json', freeze_manifest, overwrite=True)
    
    print("Pre-validation freeze completed and sealed successfully!", flush=True)
    print(f"Sealed manifest: {manifest_dir / 'prevalidation_freeze.json'}", flush=True)

def main():
    parser = argparse.ArgumentParser(description="P3 Pre-validation Freeze")
    parser.add_argument('--run', required=True, help="Run output directory")
    args = parser.parse_args()
    
    run_dir = Path(args.run)
    if not run_dir.is_absolute():
        run_dir = PROJECT_ROOT / run_dir
    perform_prevalidation_freeze(run_dir)

if __name__ == '__main__':
    main()
