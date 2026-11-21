"""Serial clean DLL timing and packaged-release identity check after diagnostic runs."""
from replay import *
from baseline import load,make,digest

def main():
 assert (OUT/'B0_complete.json').exists()
 n=Native();release=load(ROOT/'output/releases/A_Win64_OpenCV440/bin/CrackV4.dll')
 old={(r['dataset_id'],r['frame_id']):r for r in map(json.loads,(OUT/'A0_frames.jsonl').read_text().splitlines())}
 modes={r['id']:r['mode'] for r in read(ROOT/'config/datasets.json')['groups']};modes['ct3']='auto'
 groups=collections.defaultdict(list)
 for r in filter_rows(rows(OUT/'input_inventory_allowed.csv'),'development'):groups[r['dataset_id']].append(r)
 results=[];eq=[];cv2.setNumThreads(1)
 for g,seq in groups.items():
  h=None;a=None
  try:
   for i,r in enumerate(seq):
    require(g,'development');assert int(r['frame_order'])==i
    start=time.perf_counter();raw=Path(r['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=json.loads(r['points']);f=int(r['frame_id']);io=(time.perf_counter()-start)*1000
    if h is None:h=n.create(im,pp);a=make(release,im,pp,modes[g])
    ii=image(im);ps=points(pp);start=time.perf_counter();rc=n.lib.R05FProcess(h,C.byref(ii),ps);elapsed=(time.perf_counter()-start)*1000;assert rc==0
    ra=a.run(im,pp,is_reference=i==0);match=digest(ra)==old[g,f]['result_hash'];eq.append(dict(dataset_id=g,frame_id=f,release_hash=digest(ra),frozen_build_hash=old[g,f]['result_hash'],exact=match))
    results.append(dict(dataset_id=g,frame_id=f,variant='B0',role='DEVELOPMENT',dll_process_wall_ms=elapsed,reference_frame=i==0,io_decode_hash_ms=io,debug_export='disabled',native_threads=4,A_release_api_ms=ra['formal']['api_ms'],A_release_call_ms=ra['formal']['process_ms'],cpu='Ryzen9 7950X',target_i7='NOT_VERIFIED',concurrency='serial A and B0; no other experiment running'))
    if (i+1)%100==0:print('clean benchmark',g,f,round(elapsed,2),'release_exact',match,flush=True)
  finally:
   if h:n.close(h)
   if a:a.close()
 save(OUT/'experiments/clean_performance_frames.csv',results);save(OUT/'release_equivalence.csv',eq)
 write(OUT/'release_equivalence.json',dict(status='PASS' if all(r['exact'] for r in eq) else 'FAIL',frames=len(eq),exact=sum(r['exact'] for r in eq),release_sha=sha(ROOT/'output/releases/A_Win64_OpenCV440/bin/CrackV4.dll'),frozen_build_sha=sha(ROOT/'output/build/src/cpp/a/Release/CrackV4.dll')))
 print('CLEAN BENCHMARK COMPLETE',len(results),'release exact',sum(r['exact'] for r in eq),flush=True)
if __name__=='__main__':main()
