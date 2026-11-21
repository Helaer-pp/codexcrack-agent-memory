"""Dataset-use boundaries, separate from the production detector and ABI."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
POLICY_PATH=ROOT/'config/dataset_usage_policy.json'
def policy():return json.loads(POLICY_PATH.read_text(encoding='utf8'))
def role(dataset):
    roles=policy()['groups']
    if dataset not in roles:raise ValueError('Unknown dataset: '+str(dataset))
    return roles[dataset]
def allowed(dataset,purpose,*,uses_annotations=False):
    r=role(dataset)
    if r=='EXCLUDED':return False
    if uses_annotations and purpose not in policy()['annotations']['allowed_uses']:return False
    if purpose in ['comparison','annotation_qc','validation']:return True
    if purpose in ['development','model_training','parameter_fitting','automatic_threshold_search']:
        return r=='DEVELOPMENT' and not uses_annotations
    raise ValueError('Unknown data-use purpose: '+str(purpose))
def require(dataset,purpose,*,uses_annotations=False):
    if not allowed(dataset,purpose,uses_annotations=uses_annotations):
        raise PermissionError(f'Data policy rejects {dataset} / {purpose} / annotations={uses_annotations}')
def filter_rows(rows,purpose,*,dataset_key='dataset_id',uses_annotations=False):
    return [r for r in rows if allowed(r[dataset_key],purpose,uses_annotations=uses_annotations)]
