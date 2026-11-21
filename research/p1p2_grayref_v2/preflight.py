from v2common import *
from frozen_adapter import decode,compute
import collections,concurrent.futures,re,subprocess,shutil,numpy as np
def point_records(path):
 if path.suffix=='.csv':return {int(r['坐标num']):([[float(r[f'P{i}x']),float(r[f'P{i}y'])] for i in [1,2]],r['图片名']) for r in rows(path)}
 result={}
 for line in path.read_bytes().decode('gb18030',errors='replace').splitlines():
  v=re.findall(r'[-+]?\d+(?:\.\d+)?',line)
  if len(v)==5:result[int(v[0])]=([list(map(float,v[1:3])),list(map(float,v[3:5]))],None)
 return result
def main():
 assert not (OUT/'gate0_complete.json').exists() and not (OUT/'experiment_manifest.csv').exists(),'Do not overwrite a prepared run';OUT.mkdir(parents=True,exist_ok=True);assert sha(FROZEN)==SHA
 oldpolicy=read(ROOT/'config/dataset_usage_policy.json');assert oldpolicy['groups']['group_x']=='EXCLUDED'
 inventory=rows(ROOT/'output/runs/uctt_r05f_20261111_r01/input_inventory_allowed.csv');raw=rows(ROOT/'data/inputs/six_groups_manifest.csv');cache={};manifest=[]
 for group in DEV+VAL:
  require(group,'development' if group in DEV else 'validation');part=[r for r in inventory if r['dataset_id']==group];assert len(part)==COUNTS[group];part.sort(key=lambda r:int(r['frame_id']));ref=part[0];rp=json.loads(ref['points'])
  for i,r in enumerate(part):
   f=int(r['frame_id']);assert f==i+1;path=Path(r['p1p2_source']);key=str(path)
   if key not in cache:cache[key]=point_records(path)
   pp,filename=cache[key][i];assert pp==json.loads(r['points']) and (filename is None or filename==Path(r['source_image']).name)
   original=next((x for x in raw if x['dataset_alias']==group and int(x['frame_id'])==i),None)
   if original is None:assert group=='ct3' and path.suffix=='.csv','Missing primary mapping outside documented CT3 exception'
   else:assert json.loads(original['points'])==pp and original['input_image']==r['source_image']
   manifest.append(dict(group=group,frame_id=f,tracking_num=i,role=role(group),reference=ref['source_image'],current=r['source_image'],image_sha=r['sha256'],ref_sha=ref['sha256'],reference_points=rp,current_points=pp,point_source=key,point_source_sha=sha(path),point_kind='historical_coordinate_csv' if path.suffix=='.csv' else 'original_tracking_txt',width=int(r['width']),height=int(r['height'])))
 def check(r):
  assert sha(r['current'])==r['image_sha'],r['current'];return True
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for i,ok in enumerate(pool.map(check,manifest),1):
   if i%400==0:print('IMAGE HASH',i,'/2647',flush=True)
 save(OUT/'experiment_manifest.csv',manifest)
 a=read(AUDIT/'inputs.json');R=decode(a['reference_original']);C=decode(a['current_original']);assert np.array_equal(R,decode(a['reference'])) and np.array_equal(C,decode(a['current']))
 real=next(r for r in manifest if r['group']=='group_c' and r['frame_id']==237);p=a['points'];assert real['reference_points']==p['R_S'] and real['current_points']==p['C_S']
 checks=[]
 staging=OUT/'gate0/staging';staging.mkdir(parents=True);shutil.copyfile(a['reference_original'],staging/'reference.bmp');shutil.copyfile(a['current_original'],staging/'current.bmp')
 for name,rp,cp,old in [('A',p['R_G'],p['C_G'],OLD/'regression'),('D',real['reference_points'],real['current_points'],OLD/'py_runs/group_c/237')]:
  folder=OUT/'gate0'/name;v=compute(R,C,rp,cp,folder);plain=OUT/'gate0'/(name+'_cli');args=[sys.executable,str(FROZEN),'--reference',str(staging/'reference.bmp'),'--current',str(staging/'current.bmp'),'--output-dir',str(plain)]
  for prefix,pts in [('ref',rp),('cur',cp)]:
   for i,pt in enumerate(pts,1):args += [f'--p{i}-{prefix}',','.join(map(str,pt))]
  cli=subprocess.run(args,capture_output=True,text=True,errors='replace');write(OUT/'gate0'/(name+'_command.json'),dict(argv=args,returncode=cli.returncode));(OUT/'gate0'/(name+'_stdout.txt')).write_text(cli.stdout,encoding='utf8');(OUT/'gate0'/(name+'_stderr.txt')).write_text(cli.stderr,encoding='utf8');assert cli.returncode==0
  for trace in folder.glob('trace_*.csv'):
   assert sha(trace)==sha(old/trace.name)==sha(plain/trace.name);checks.append(dict(case=name,trace=trace.name,old_and_unmodified_cli_exact=True))
 save(OUT/'gate0/regression.csv',checks)
 stats=[]
 for suffix,groups in [('dev',DEV),('validation',VAL)]:
  historical=rows(OLD/'tables'/f'all_results_{suffix}.csv');summary=rows(OLD/'tables'/f'group_summary_{suffix}.csv')
  for s in summary:
   rr=[r for r in historical if (r['group']==s['group'] or s['group'] not in groups) and r['mode']==s['mode'] and r['threshold']==s['threshold']];v=[r for r in rr if r['visibility']=='VISIBLE'];errors=[float(r['error']) for r in v if r['error']]
   actual=dict(frames=len(rr),visible=len(v),hit10=sum(e<=10 for e in errors),over100=sum(e>100 for e in errors))
   assert all(int(s[k])==x for k,x in actual.items());stats.append(dict(group=s['group'],mode=s['mode'],threshold=s['threshold'],**actual,old_summary_exact=True))
 save(OUT/'gate0/old_statistics_recomputed.csv',stats)
 protected=read(AUDIT/'run_identity.json')['protected_production'];protected.update({str(FROZEN.relative_to(ROOT)):SHA,'output/build/p1p2_grayref_v1/Release/P1P2GrayRefV1.dll':sha(ROOT/'output/build/p1p2_grayref_v1/Release/P1P2GrayRefV1.dll')})
 identity=dict(utc=utc(),frozen_sha=SHA,manifest_sha=sha(OUT/'experiment_manifest.csv'),image_count=len(manifest),protected=protected,old_manifests={str(p):sha(p) for p in [OLD/'artifact_manifest.json',AUDIT/'artifact_manifest.json']},policy=oldpolicy,task_sha=sha(ROOT/'P1P2_GrayRef_V2_Strict_Development_Agent_Prompt.md'),point_sources={p:sha(p) for p in cache},labels_read=0,new_blind_holdout='NOT_AVAILABLE',ct3_provenance='Explicit historical coordinate CSV; independent original tracking TXT unavailable')
 write(OUT/'baseline_identity.json',identity);write(OUT/'gate0_complete.json',dict(passed=True,images=2647,regression_trace_checks=12,old_statistics_recomputed=True));print('GATE0 PASS',flush=True)
if __name__=='__main__':main()
