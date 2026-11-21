import csv,json,math,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/python'))
from crackv4.dataset_policy import filter_rows
EXE=ROOT/'output/build/src/cpp/a/Release/CrackV4Example.exe'
if not EXE.exists(): raise SystemExit(f'missing {EXE}; run build.ps1 first')
rows=list(csv.DictReader((ROOT/'data/smoke/manifest.csv').open(encoding='utf-8-sig')))
rows=filter_rows(rows,'validation',dataset_key='dataset_alias')

def variants(p,frame):
    if frame==0:return p
    (x1,y1),(x2,y2)=p; mx=(x1+x2)/2; my=(y1+y2)/2
    # The points remain valid priors but deliberately carry translation,
    # unequal endpoint motion, spacing and small-angle tracking errors.
    dx,dy=((8,-6),(-7,9),(5,11))[frame-1]
    scale=(1.0,1.04,0.97)[frame-1]
    angle=math.radians((0,1.5,-1.2)[frame-1]); c,s=math.cos(angle),math.sin(angle)
    out=[]
    for x,y in p:
        u=(x-mx)*scale;v=(y-my)*scale
        out.append([mx+dx+c*u-s*v,my+dy+s*u+c*v])
    return out

def command(group,variant):
    rr=[r for r in rows if r['dataset_alias']==group][:3]
    args=[str(EXE),str({'clean':0,'cracked':1,'auto':2}[rr[0]['mode']]),'1']
    for i,r in enumerate(rr):
        p=json.loads(r['points'])
        q=variants(p,i) if variant=='perturbed' else p
        args += [str(ROOT/r['input_image']),*(str(v) for xy in q for v in xy)]
    return args

def endpoint_results(text):
    result=[]
    for line in text.splitlines():
        t=line.split()
        if not t:continue
        # Endpoint identity is the decoupling contract. Complete root-to-tip
        # length remains a separate root/path measurement.
        result.append((t[0],t[1],t[3],t[4]))
    return result

for group in dict.fromkeys(r['dataset_alias'] for r in rows):
    base=endpoint_results(subprocess.check_output(command(group,'measured'),text=True,stderr=subprocess.STDOUT))
    changed=endpoint_results(subprocess.check_output(command(group,'perturbed'),text=True,stderr=subprocess.STDOUT))
    if base!=changed: raise AssertionError((group,'perturbed',base,changed))
    print(f'{group}: bounded current-anchor perturbations invariant')
print('ANCHOR INVARIANCE PASSED')
