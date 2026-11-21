from common_ap import *
import subprocess,psutil
guard();mm=rows(O/'00_protocol/inputs_manifest.csv');eq=[];lat=[];memory=[]
for g in dict.fromkeys(r['dataset_alias']for r in mm):
 rr=[r for r in mm if r['dataset_alias']==g];prefix=O/f'07_performance/native/{g}_A'
 assert not prefix.with_suffix('.csv').exists(),'No overwrite '+g
 for r in rr:assert sha(r['input_image'])==r['input_sha256']
 write(prefix.with_suffix('.tsv'),'\n'.join(r['input_image']+'\t'+'\t'.join(str(v)for p in json.loads(r['points'])for v in p)for r in rr))
 env=os.environ.copy();env['PATH']=str(ROOT/'third_party/opencv440/bin')+';'+env['PATH'];peak=0
 with prefix.with_suffix('.log').open('w')as f:
  proc=subprocess.Popen([str(ROOT/'baseline/frozen_a/bin/a_bench.exe'),str(api.BASE),str(prefix.with_suffix('.tsv')),str(prefix),'2'if rr[0]['mode']=='auto'else'0','1','0'],env=env,stdout=f,stderr=subprocess.STDOUT);ps=psutil.Process(proc.pid)
  while proc.poll()is None:
   try:peak=max(peak,ps.memory_info().rss)
   except psutil.Error:pass
   time.sleep(.1)
  assert proc.returncode==0,g
 nr,nj,npth=native(prefix);pr,pj,pp=native(ROOT/f'data/frozen_a_replay/{g}_A');assert len(nr)==len(rr)==len(pr)
 for i,(n,j,p,oldj,oldp)in enumerate(zip(nr,nj,npth,pj,pp)):
  same=api.normalized(j)==api.normalized(oldj)and np.array_equal(p,oldp)and all(n[k]==pr[i][k]for k in ['tip_valid','length_valid','tip_x','tip_y','length_px','path_count'])
  assert same,(g,i);eq.append(dict(group=g,frame_id=i,equal_state_tip_length_double_path=True,input_sha256=rr[i]['input_sha256']))
  if i:lat.append(dict(group=g,frame_id=i,complete_core_ms=float(n['complete_core_ms']),scope='A only: predecoded Process+GetResultV2+CopyPath+allocations; excludes IO/media/Python A-prime'))
 memory.append(dict(group=g,peak_rss_bytes=peak,predecoded_entire_sequence=True));csvout(O/'01_audit/baseline_replay.csv',eq);csvout(O/'07_performance/native_latency_all_frames.csv',lat);csvout(O/'07_performance/memory_and_cache.csv',memory)
 print('A EXACT',g,len(nr),flush=True)
guard();save(O/'01_audit/A_replay_complete.json',dict(frames=len(eq),differences=0,passed=True,utc=utc()))
