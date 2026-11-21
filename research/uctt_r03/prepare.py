"""Freeze evidence before R03; never edit or execute sealed R01/R02 sources."""
from pathlib import Path
import hashlib,json,csv,shutil,platform,os
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/runs/phase1_r03_dynamic_roi_20261110_r01'
BUILD=ROOT/'output/build/uctt_r03'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(p):
    return {str(f.relative_to(ROOT)).replace('\\','/'):sha(f) for f in sorted(p.rglob('*')) if f.is_file() and '__pycache__' not in f.parts}
def write(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=False)
    protected={}
    for rel in ['src/cpp/a','output/runs/phase1_audit_decoupling_20261110_r01','output/runs/phase1_acceptance_r02']:
        protected.update(tree(ROOT/rel))
    for rel in ['config/project.json','config/datasets.json','data/inputs/six_groups_manifest.csv','output/build/src/cpp/a/Release/CrackV4.dll']:
        protected[rel]=sha(ROOT/rel)
    assert protected['output/build/src/cpp/a/Release/CrackV4.dll']=='55a0e7a79162da79e691ede9ff58229e59a56fdd1e0b1e3f609dc51128860402'
    snapshot=OUT/'frozen_production';shutil.copytree(ROOT/'src/cpp/a',snapshot,ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(ROOT/'output/build/src/cpp/a/Release/CrackV4.dll',OUT/'R02_original.dll')
    write('frozen_manifest_r03.json',dict(protected_files=protected,git_commit=None,git_reason='No repository metadata',cpu=os.environ.get('PROCESSOR_IDENTIFIER'),logical_cpus=os.cpu_count(),platform=platform.platform(),runtime=dict(flags=3572,policy=1,terminal=1,refine=True,threads=4),source_snapshot=str(snapshot),snapshot_is_restore_only=True))
    # Every R02 report is read; CSV dimensions/headers are inventoried separately.
    inventory=[]
    for base in ['output/runs/phase1_audit_decoupling_20261110_r01','output/runs/phase1_acceptance_r02']:
        for p in sorted((ROOT/base).glob('*')):
            if not p.is_file():continue
            rec=dict(path=str(p.relative_to(ROOT)),size=p.stat().st_size,sha256=sha(p),status='AVAILABLE')
            if p.suffix in ('.md','.json','.html','.diff'):rec['text_characters']=len(p.read_text(encoding='utf-8-sig'))
            if p.suffix=='.csv':
                with p.open(encoding='utf-8-sig',newline='') as f:
                    reader=csv.DictReader(f);rec['columns']=reader.fieldnames;rec['rows']=sum(1 for _ in reader)
            inventory.append(rec)
    write('evidence_inventory.json',inventory)
    (OUT/'stage0_audit.md').write_text('''# R03 preflight / Gate 0 pending replay

Production src/cpp/a/CrackV4.cpp and roi_tip.inc match R02 candidate DLL identity. R01/R02 evidence is hash-frozen; restore-only copy exists. No production edits are authorized by a PASS yet.

Constructor fixes origin/spacing/forward, reference templates and baseline_mask. estimateTipMotion is current-anchor independent. measureTip uses tipWindow, localReference, distalLine; a nonempty accepted path overwrites tip/path_valid/terminal. Therefore these three bits are correlated, not three independent proofs of physical ownership. Its status also depends on main-path length certification; separate tip-state and length-state metrics are required.

R02 profiling erroneously differences a counter reset each frame. R03 will use fresh per-frame values and independent outer timings, with nested scopes excluded from sums. R02 scripts' parents[3] relocation and sparse windows are not silently inherited.

Pilot: all seven measured R02 continuous windows plus four recorded failing variants; CT3 full 136, GROUP_A 252 (one confirmation, explicitly insufficient). Full 16-variant + additional 5% acceptance and A3/A4 are gated on A2 safety, never inferred from pilot.

Experimental lock gate reuses current terminal/path evidence, image-only motion, forward compatibility, 10 px boundary margin (9-sample terminal probe), 6 px connected-path locality. Strong first-frame structure may acquire immediately; this is a hypothesis requiring wrong-first-lock tests. No specimen-dependent thresholds. No GT enters runtime. State-only proposals never feed the detector. No production merge.
''',encoding='utf8')
    print(OUT, 'protected files',len(protected))
