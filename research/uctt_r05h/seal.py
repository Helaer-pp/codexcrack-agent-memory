"""Verify the completed delivery and seal its artifact manifest."""
from common import *
import datetime,shutil
def main():
 lock=read(OUT/'freeze.json');assert all(sha(ROOT/p)==s for p,s in lock['files'].items());assert all(sha(ROOT/p)==s for p,s in lock['protected'].items())
 complete=read(OUT/'replay_complete.json');assert complete['frames']==2647 and complete['calls']==7342
 videos=read(OUT/'videos/verified_videos.json');assert len(videos)==6 and sum(r['unique_source_frames'] for r in videos)==2647
 for v in videos:assert v['full_decode_pass'] and sha(OUT/v['path'])==v['sha256'] and v['encoded_frames']==32+v['unique_source_frames']
 renders=rows(OUT/'galleries/render_manifest.csv');assert len(renders)==2647 and len({(r['dataset_id'],r['frame_id']) for r in renders})==2647;assert all((OUT/r['path']).is_file() for r in renders)
 assert read(OUT/'previous_round_integrity.json')['unchanged'];assert (OUT/'development_report.md').is_file();assert read(OUT/'evaluation_complete.json')['selected']==120
 for p in (ROOT/'research/uctt_r05h').glob('*'):
  if p.is_file():
   target=OUT/'source_snapshot'/p.name
   if target.exists():assert sha(target)==sha(p),(p,'snapshot drift')
   else:shutil.copy2(p,target)
 state=dict(status='COMPLETE_RESEARCH_DELIVERY_ACCURACY_AND_SAFETY_FAIL',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frames=2647,native_calls=7342,videos=6,local_images=2647,validation='source/DLL/rules frozen before1082-frame FULL replay; no retuning',production_unchanged=True,annotations_comparison_only=True,group_x_opened=0,known_limitations='false confirmations/history writes; premature STOP; low valid reference rate; weak terminal miss; limited translation navigation; see report')
 write(OUT/'final_status.json',state)
 files={str(p.relative_to(OUT)).replace('\\','/'):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact_manifest.json'}
 write(OUT/'artifact_manifest.json',dict(files=files,count=len(files),sealed=True));print('SEALED',len(files),'artifacts; 6 videos; 2647 images',flush=True)
if __name__=='__main__':main()
