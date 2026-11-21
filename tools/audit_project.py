"""Read-only integrity audit. Writes its report only to project output/checks."""
from pathlib import Path
import json,csv,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def local(rel):
 p=(ROOT/rel).resolve()
 if not p.is_relative_to(ROOT):raise ValueError('Manifest path outside project')
 return p
identity=json.loads((ROOT/'baseline/frozen_a/identity.json').read_text(encoding='utf8'))
groups={'production':identity['source_hashes']}
retained=ROOT/'config/retained_data_hashes.json'
if retained.exists():groups['retained_data']=json.loads(retained.read_text(encoding='utf8'))['files']
results=[]
for group,files in groups.items():
 for rel,h in files.items():
  assert sha(local(rel))==h,(group,rel);results.append(dict(group=group,file=rel,passed=True))
mapping=ROOT/'docs/maintenance/latest_output_exact_copy.csv';n=0
with mapping.open(encoding='utf-8-sig',newline='')as f:
 for r in csv.DictReader(f):assert sha(local(r['destination']))==r['sha256'],r['destination'];n+=1
out=ROOT/'output/checks'/('integrity_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.json');out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(dict(passed=True,protected_files=len(results),latest_sealed_files=n,all_sealed_files_byte_identical=True),indent=2),encoding='utf8')
print('INTEGRITY PASSED',len(results),'protected files;',n,'sealed result files')
