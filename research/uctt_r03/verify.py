"""Gate 2 fault harness and legacy ABI checks, run only after Gate 0/1."""
import json,subprocess,ctypes as C,csv,math,re
from prepare import ROOT,OUT,BUILD,write
from pilot import api,inventory,lib,create,run,normalized
def main():
 gate=json.loads((OUT/'gate01.json').read_text());assert not any(v for k,v in gate.items() if k.endswith('mismatches') or k.endswith('failures'))
 with (OUT/'snapshots.jsonl').open(encoding='utf8') as f:
  seed=next(r for r in map(json.loads,f) if r['dataset_id']=='group_a' and r['stateonly']['visual_confirmed'])
 e=seed['stateonly'];size=seed['input'];path=e['input_path']
 (OUT/'fault_seed.txt').write_text(' '.join(map(str,[size['width'],size['height'],*e['search_roi'],len(path)]))+'\n'+'\n'.join(f'{x} {y}' for x,y in path),encoding='ascii')
 write('fault_seed_provenance.json',dict(dataset_id=seed['dataset_id'],frame_id=seed['frame_id'],image_sha256=size['sha256'],evidence_level='Candidate evidence injection; no altered image and no physical GT',injection='translate path and terminal together by (-30,-30); runtime sees no truth label'))
 result=subprocess.run([str(BUILD/'Release/R03Contracts.exe'),str(OUT/'fault_seed.txt')],capture_output=True,text=True)
 (OUT/'fault_injection_results.csv').write_text(result.stdout,encoding='utf-8-sig');(OUT/'fault_injection_stderr.log').write_text(result.stderr,encoding='utf8')
 assert result.returncode in (0,2),(result.returncode,result.stderr)
 cases=list(csv.DictReader(result.stdout.splitlines()))
 write('gate2.json',dict(exit_code=result.returncode,total=len(cases),passed=sum(r['pass']=='1' for r in cases),failed=[r['case_id'] for r in cases if r['pass']=='0'],A3_A4='BLOCKED' if result.returncode else 'NOT_STARTED',real_image_wrong_lock_safety='NOT_VERIFIED'))
 libs=[lib(BUILD/'Release/A0_R02.dll'),lib(BUILD/'Release/A1_SHADOW.dll')]
 mode,seq=inventory()['ct3'];ref=api.read(seq[0][0]);rows=[]
 invalid={'nan':[[float('nan'),10],[20,40]],'inf':[[10,float('inf')],[20,40]],'coincident':[[100,100],[100,100]],'out_of_bounds':[[-5,-5],[-10,-20]],'null':None}
 for tag,pair in invalid.items():
  ds=[create(l,ref,seq[0][1],mode) for l in libs];control=create(libs[0],ref,seq[0][1],mode)
  try:
   for i,(p,cp,h) in enumerate(seq[:5]):
    im=api.read(p);x=run(ds[0],im,pair,i==0);y=run(ds[1],im,pair,i==0);base=run(control,im,cp,i==0)
    before=libs[1].CrackV4LastJson(ds[1].handle)
    for _ in range(3):
     rr=api.Result();rr.struct_size=C.sizeof(rr);assert libs[1].CrackV4GetBaseline(ds[1].handle,C.byref(rr))==0
    after=libs[1].CrackV4LastJson(ds[1].handle)
    def tip(t):return (t[0].tip_confirmed,t[0].tip.x,t[0].tip.y)
    rows.append(dict(test=tag,frame_id=i+1,return_code_A0=x[1],return_code_A1=y[1],A0_A1_equal=normalized(x[3])==normalized(y[3]),tip_current_anchor_independent=tip(x)==tip(base),cached_baseline_does_not_mutate=before==after))
   # Invalid struct size must reject before temporal processing.
   rr=api.Result();rr.struct_size=0;ii=api.image(ref);before=libs[1].CrackV4LastJson(ds[1].handle)
   rc=libs[1].CrackV4Process(ds[1].handle,C.byref(ii),api.points(seq[0][1]),C.byref(rr));after=libs[1].CrackV4LastJson(ds[1].handle)
   rows.append(dict(test=tag+'_bad_result_size',frame_id=None,return_code_A1=rc,cached_baseline_does_not_mutate=before==after))
  finally:
   for d in ds+[control]:d.close()
 api.csvout(OUT/'api_abi_checks.csv',rows)
 executable='D:/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.29.30133/bin/Hostx64/x64/dumpbin.exe'
 exports={}
 for name,p in [('R02',OUT/'R02_original.dll'),('A0',BUILD/'Release/A0_R02.dll'),('A1',BUILD/'Release/A1_SHADOW.dll')]:
  result=subprocess.run([executable,'/exports',str(p)],capture_output=True)
  assert result.returncode==0
  txt=result.stdout.decode('utf8',errors='replace');(OUT/f'exports_{name}.txt').write_text(txt,encoding='utf8')
  exports[name]=re.findall(r'^\s+\d+\s+[0-9A-F]+\s+[0-9A-F]+\s+(\w+)\s*$',txt,re.M)
 write('abi_summary.json',dict(exports=exports,legacy_exports_equal=set(exports['R02'])==set(exports['A0'])=={x for x in exports['A1'] if not x.startswith('R03')},sizes={t.__name__:C.sizeof(t) for t in [api.Point,api.Image,api.Config,api.Result,api.V2]},rows=len(rows),checks_pass=all(all(v is True for k,v in r.items() if k.endswith('equal') or k.endswith('independent') or k.endswith('mutate')) for r in rows)))
 print(json.loads((OUT/'gate2.json').read_text()))
if __name__=='__main__':main()
