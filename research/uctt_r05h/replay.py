"""Causal image-only replay. Human annotations are never opened by this runner."""
from native import *
import cv2,numpy as np,gzip,collections,shutil,datetime
VARIANTS={'FULL':0,'NO_REFERENCE':1,'LAST_ENDPOINT':2,'NO_HISTORY':3}
def locked_files():
 files=list((ROOT/'research/uctt_r05h').glob('*.hpp'))+list((ROOT/'research/uctt_r05h').glob('*.cpp'))+[ROOT/'research/uctt_r05h/CMakeLists.txt',ROOT/'research/uctt_r05h/native.py',Path(__file__),BUILD/'Release/R05H.dll',POLICY_PATH]
 return {str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files}
def main():
 for d in ['traces','experiments','source_snapshot','galleries/images','videos','tests']:(OUT/d).mkdir(parents=True,exist_ok=True)
 inventory=filter_rows(rows(F/'input_inventory_allowed.csv'),'validation');assert len(inventory)==2647
 save(OUT/'input_inventory.csv',inventory);save(OUT/'selection.csv',filter_rows(rows(F/'selected_frames.csv'),'validation'))
 assert not (OUT/'freeze.json').exists(),'A frozen run must not be overwritten'
 gsource=(ROOT/'research/uctt_r05g/tracker.hpp').read_text(encoding='utf8');hsource=(ROOT/'research/uctt_r05h/sampling.hpp').read_text(encoding='utf-8-sig')
 def section(t):return t[t.index(' Scan crossSection('):t.index(' std::vector<Seed> originSeeds')]
 assert section(gsource)==section(hsource)
 protected=list((ROOT/'src/cpp/a').rglob('*'))+list((ROOT/'config').glob('*'))+[ROOT/'output/build/src/cpp/a/Release/CrackV4.dll',ROOT/'output/releases/A_Win64_OpenCV440/bin/CrackV4.dll',LABELS]
 protected={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in protected if p.is_file()}
 lock=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=locked_files(),protected=protected,variants=VARIANTS,labels_opened=0,validation_images_opened=0,excluded_images_opened=0,cross_section_sha256=hashlib.sha256(section(hsource).encode()).hexdigest(),rules='Frozen after synthetic mechanism checks; no real-label parameter fitting. Dev 4 variants; validation FULL once only. Accuracy failures do not suppress validation requested by user.',budgets={'tracking_ms':350,'terminal_start_cutoff_ms':450,'reference_top_stops':12},references={g:next(x['sha256'] for x in inventory if x['dataset_id']==g) for g in ALL})
 write(OUT/'freeze.json',lock)
 for p in (ROOT/'research/uctt_r05h').glob('*'):
  if p.is_file():shutil.copy2(p,OUT/'source_snapshot'/p.name)
 shutil.copy2(BUILD/'Release/R05H.dll',OUT/'source_snapshot/R05H.dll')
 groups=collections.defaultdict(list)
 for row in inventory:groups[row['dataset_id']].append(row)
 cv2.setNumThreads(1);n=Native();metrics=[];access=[];selections={(r['dataset_id'],int(r['frame_id'])) for r in rows(OUT/'selection.csv')}
 for g in ALL:
  isval=g in VAL
  require(g,'validation' if isval else 'development');assert locked_files()==lock['files']
  if isval:write(OUT/f'validation_entry_{g}.json',dict(frozen=True,code_hashes_verified=True,development_frames_finished=len([a for a in access if a['dataset_id'] in DEV]),utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
  variants={'FULL':0} if isval else VARIANTS;handles={};streams={tag:gzip.open(OUT/'traces'/f'{g}_{tag}.jsonl.gz','wt',encoding='utf8',compresslevel=1) for tag in variants}
  try:
   for i,row in enumerate(groups[g]):
    assert int(row['frame_order'])==i;f=int(row['frame_id']);start=time.perf_counter();raw=Path(row['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=json.loads(row['points']);io=(time.perf_counter()-start)*1000
    if not handles:handles={tag:n.create(im,pp) for tag in variants}
    for tag,v in variants.items():
     t=n.process(handles[tag],im,pp,v);assert t['past_history_frame']<t['frame'];assert not t['history_written'] or t['observed'];t.update(dataset_id=g,frame_id=f,frame_order=i,variant=tag,role=role(g),source_sha256=row['sha256'],io_decode_hash_ms=io)
     streams[tag].write(json.dumps(t,separators=(',',':'))+'\n')
     if (g,f) in selections:write(OUT/'traces'/f'{g}_{f}_{tag}.json',t)
     metrics.append({k:v for k,v in t.items() if k not in ['main_path','visible_segments','inferred_gaps','alternative_stops','navigation']}|dict(stop_count=len(t['alternative_stops']),reference_attempts=sum(bool(q['reference']['matches']) for q in t['alternative_stops']),reference_valid=sum(q['reference']['state']=='VALID' for q in t['alternative_stops']),**t['runtime_breakdown']))
    access.append(dict(dataset_id=g,frame_id=f,frame_order=i,role=role(g),sha256=row['sha256'],annotations_read=False))
    if (i+1)%25==0:print(g,i+1,'/',len(groups[g]),'status',t['status'],flush=True)
  finally:
   for h in handles.values():n.close(h)
   for stream in streams.values():stream.close()
  save(OUT/'experiments/per_frame.csv',metrics);save(OUT/'image_access_log.csv',access);print('GROUP COMPLETE',g,flush=True)
 assert locked_files()==lock['files'];assert all(sha(ROOT/p)==s for p,s in protected.items())
 write(OUT/'replay_complete.json',dict(frames=len(access),calls=len(metrics),development_frames=1565,validation_frames=1082,annotations_opened=0,excluded_images_opened=0,protected_unchanged=True,frozen_unchanged=True))
 print('COMPLETE',len(access),len(metrics),flush=True)
if __name__=='__main__':main()
