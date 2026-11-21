from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[3]
def run_output():
 name=os.environ.get('CRACK_RUN_ID','workspace_check')
 if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'for c in name):raise ValueError('Invalid CRACK_RUN_ID')
 return ROOT/'output/runs'/name
def require_output(p):
 p=Path(p).resolve()
 if not p.is_relative_to((ROOT/'output').resolve()):raise ValueError('Output must remain in CodexCrack/output')
 return p
