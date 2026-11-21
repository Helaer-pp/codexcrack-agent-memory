"""Full chronological image-only replay. No labels or diagnostic seeds imported."""
from native import *
import cv2,numpy as np,gzip,collections,shutil
VARIANTS={'E1_GREEDY':0,'E1_BEAM':1,'E1_NO_GAP':2,'E1_STRONG':3}
def compact(t):
 return {k:v for k,v in t.items() if k not in ['nodes','scans']}|{'scans':[{k:s[k] for k in ['id','parent','step_index','predicted_point','tangent','normal','halfwidth','max_radius','phase','window_polygon']} for s in t['scans']]}
def main():
 assert read(OUT/'G1_gate.json')['status']=='PASS';cv2.setNumThreads(1);n=Native()
 src={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in (ROOT/'research/uctt_r05g').glob('*') if p.is_file()}
 src[str((BUILD/'Release/R05G.dll').relative_to(ROOT))]=sha(BUILD/'Release/R05G.dll');write(OUT/'E1_pre_run_lock.json',dict(files=src,variants=VARIANTS,labels_opened=0,history='NOT_IMPLEMENTED: G3 identity certificate absent, no trusted history writes',evaluation='all76 visible +4 uncertain; no scoring-driven parameter changes'))
 for p in (ROOT/'research/uctt_r05g').glob('*'):
  if p.is_file():shutil.copy2(p,OUT/'source_snapshot'/p.name)
 shutil.copy2(BUILD/'Release/R05G.dll',OUT/'source_snapshot/R05G.dll')
 selections={(r['dataset_id'],int(r['frame_id'])) for r in rows(OUT/'selection.csv')};groups=collections.defaultdict(list)
 for r in rows(OUT/'input_inventory.csv'):require(r['dataset_id'],'development');groups[r['dataset_id']].append(r)
 metrics=[];access=[]
 streams={tag:gzip.open(OUT/'traces'/f'{tag}_frames.jsonl.gz','wt',encoding='utf8',compresslevel=1) for tag in VARIANTS}
 try:
  for g,seq in groups.items():
   handles={}
   try:
    for i,r in enumerate(seq):
     assert int(r['frame_order'])==i;f=int(r['frame_id']);start=time.perf_counter();raw=Path(r['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=json.loads(r['points']);io=(time.perf_counter()-start)*1000
     if not handles:handles={tag:n.create(im) for tag in VARIANTS}
     for tag,variant in VARIANTS.items():
      t=n.process(handles[tag],im,pp,variant,2 if (g,f) in selections else 0);t.update(dataset_id=g,frame_id=f,variant=tag,source_sha256=r['sha256'],io_decode_hash_ms=io,width=im.shape[1],height=im.shape[0]);assert not t['observed'] and not t['trusted_history_written']
      if (g,f) in selections:write(OUT/'traces'/f'{tag}_{g}_{f}.json',t)
      streams[tag].write(json.dumps(compact(t),ensure_ascii=False,separators=(',',':'))+'\n')
      metric={k:v for k,v in t.items() if k not in ['nodes','scans','selected_path','ends','seeds']};metric.update(seed_count=len(t['seeds']),path_nodes=len(t['selected_path']),visible_nodes=sum(p['visible'] for p in t['selected_path']),visible_path_length=sum(float(np.linalg.norm(np.array(b['xy'])-a['xy'])) for a,b in zip(t['selected_path'][:-1],t['selected_path'][1:]) if a['visible'] and b['visible']),read_repeat_ratio=1-t['unique_pixels_sampled']/max(1,t['original_pixel_reads']),candidate_count=sum(len(s.get('candidates',[])) for s in t['scans']) if (g,f) in selections else None)
      metrics.append(metric)
     access.append(dict(dataset_id=g,frame_id=f,sha256=r['sha256'],role='DEVELOPMENT'))
     if (i+1)%50==0:print('E1',g,f,'/',len(seq),flush=True)
   finally:
    for h in handles.values():n.close(h)
 finally:
  for stream in streams.values():stream.close()
 save(OUT/'experiments/all_variants_frame_summary.csv',metrics);save(OUT/'experiments/frame_summary.csv',[r for r in metrics if r['variant']=='E1_BEAM']);save(OUT/'image_access_log.csv',access)
 write(OUT/'E1_complete.json',dict(frames=len(access),variant_calls=len(metrics),variants=list(VARIANTS),annotations_opened=0,validation_images_opened=0,excluded_images_opened=0,full_causal_prefix=True,first_frame='current processed normally; no cached-reference substitution'))
 print('E1 COMPLETE',len(access),len(metrics),flush=True)
if __name__=='__main__':main()
