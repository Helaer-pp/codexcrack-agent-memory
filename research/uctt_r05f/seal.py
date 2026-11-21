from common import *
import gzip,numpy as np,collections,re,zipfile,shutil,ast

def main():
 report=OUT/'development_report.md';assert report.exists()
 manifest=read(OUT/'baseline_manifest.json');check=[]
 for section in ['protected','prior_inputs']:
  for name,expected in manifest[section].items():check.append(dict(path=name,section=section,exact=sha(ROOT/name)==expected))
 prior=read(E/'artifact_manifest.json')['files']
 for name,entry in prior.items():check.append(dict(path=str((E/name).relative_to(ROOT)),section='prior_R05E_artifact',exact=sha(E/name)==entry['sha256']))
 assert all(r['exact'] for r in check),'protected evidence changed'
 counts=collections.Counter();summary=[];n=0;maxcand=0;maxseg=0
 with gzip.open(OUT/'traces/B0_frames.jsonl.gz','rt',encoding='utf8') as f:
  for line in f:
   t=json.loads(line);g=t['dataset_id'];require(g,'development');counts[g]+=1;n+=1;assert t['frame']==counts[g] and t['frame_id']==counts[g]
   assert not t['observed'] and t['output_tip'] is None and not t['trusted_history_written'] and t['trusted_path_size']==0
   assert len(t['windows'])<=192 and len(t['segments'])<=8192 and len(t['candidates'])<=32768
   assert t['unique_source_pixels']<=t['window_pixels_sum'];assert t['reference_calls']==0
   for i,c in enumerate(t['candidates']):assert c['id']==i and 0<=c['canonical_id']<=i and t['candidates'][c['canonical_id']]['canonical_id']==c['canonical_id']
   maxcand=max(maxcand,len(t['candidates']));maxseg=max(maxseg,len(t['segments']))
   summary.append(dict(dataset_id=g,frame_id=t['frame_id'],windows=len(t['windows']),window_pixels_sum=t['window_pixels_sum'],unique_source_pixels=t['unique_source_pixels'],revisit_ratio=1-t['unique_source_pixels']/t['window_pixels_sum'] if t['window_pixels_sum'] else None,segments=len(t['segments']),candidates=len(t['candidates']),dedup_candidates=t['retained_candidates'],budget_reason=t['reason'],search_incomplete=t['search_incomplete'],frontier_steps=0,maximum_jump_px=None,cache_hits=0,stepwise='NOT_IMPLEMENTED'))
 assert n==1565 and dict(counts)==dict(group_a=551,ct2=468,group_h=410,ct3=136)
 save(OUT/'experiments/search_control_frames.csv',summary)
 html=(OUT/'galleries/index.html').read_text(encoding='utf8');sources=re.findall(r'<img[^>]+src="([^"]+)"',html);assert len(sources)==80 and all((OUT/'galleries'/s).is_file() for s in sources)
 for p in (ROOT/'research/uctt_r05f').glob('*.py'):ast.parse(p.read_text(encoding='utf8'))
 locked={k.replace('\\','/'):v for k,v in read(OUT/'B0_lock.json')['files'].items()};important=['research/uctt_r05f/current.hpp','research/uctt_r05f/runtime.cpp','research/uctt_r05f/compare.py','output/build/uctt_r05f/Release/R05F.dll']
 for name in important:assert sha(ROOT/name)==locked[name],name
 save(OUT/'protected_integrity.csv',check)
 write(OUT/'final_integrity.json',dict(protected_files=len(check),protected_unchanged=True,full_trace_frames=n,group_counts=dict(counts),max_stored_candidates=maxcand,max_stored_segments=maxseg,canonical_lineage_valid=True,all_shadow_no_history=True,core_and_comparator_match_prerun_lock=True,html_images=len(sources),html_images_exist=True,source_policy='DEVELOPMENT only; all labels offline; no excluded or validation image opens',gate='S1 FAIL; no production replacement',video_exists=(OUT/'R05F_S1_Results.mp4').is_file()))
 for p in sorted((ROOT/'research/uctt_r05f').glob('*.*')):
  if p.suffix in ['.py','.cpp','.hpp','.txt']:shutil.copy2(p,OUT/'source_snapshot'/p.name)
 artifacts={str(p.relative_to(OUT)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact_manifest.json'}
 write(OUT/'artifact_manifest.json',dict(files=artifacts,scope='all current R05F outputs; no production modification',notes='aborted compression attempt retained and not scored; source_snapshot is evidence, not active runtime'))
 print('SEALED',len(artifacts),'artifacts;',n,'full frames;',len(check),'protected files unchanged',flush=True)
if __name__=='__main__':main()
