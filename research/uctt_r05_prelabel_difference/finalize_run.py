"""Repeat representative real computations and seal research source/artifact identities."""
import shutil,platform,importlib.metadata as metadata
from common import *
from select_causal_history import CausalHistory,RULES,score
from register_two_sides import context,register

def main():
 cv2.setNumThreads(1);cv2.setRNGSeed(20261111);inv=rows(OUT/'input_inventory.csv');selections=rows(OUT/'history_reference_selection.csv');checks=[]
 for g,frame in [('group_a',241),('group_c',38),('ct2',8),('three_point_bend',20),('ct3',20)]:
  stream=[r for r in inv if r['dataset_id']==g];current=stream[frame-1];history=CausalHistory(RULES['history_capacity'])
  for r in stream[:frame-1]:history.add(r)
  cc,_=history.candidates(current,RULES['candidate_budget']);ctx=context(read_image(current['source_image']),current);valid=[];computed={}
  for p in cc:
   result=register(read_image(p['source_image']),p,ctx);computed[int(p['frame_order'])]=result
   if result['valid']:valid.append((score(current,p)+.2*(1-float(np.mean([s['fit_ecc'] for s in result['sides']]))),-int(p['frame_order']),p,result))
  best=min(valid,key=lambda a:(a[0],a[1])) if valid else None;selected=int(best[2]['frame_order']) if best else None
  old=next(r for r in selections if r['dataset_id']==g and int(r['target_frame'])==frame and r['reference_type']=='E2_MATCHED_HISTORY');assert selected==(int(old['selected_order']) if old['selected_order'] else None)
  fixed=register(read_image(stream[0]['source_image']),stream[0],ctx)
  with np.load(OUT/'diagnostics'/f'{g}__frame_{frame:06d}.npz') as d:
   assert np.array_equal(fixed['warp'],d['E1_FIXED_REF_warp']) and np.array_equal(fixed['mask'],d['E1_FIXED_REF_valid_mask'])
   if best:assert np.array_equal(best[3]['warp'],d['E2_MATCHED_HISTORY_warp']) and np.array_equal(best[3]['mask'],d['E2_MATCHED_HISTORY_valid_mask'])
  checks.append(dict(dataset_id=g,frame_id=frame,selected_h=selected,reference_selection_identical=True,warp_and_mask_bit_identical=True))
 write(OUT/'real_repeatability.json',checks)
 write(OUT/'test_matrix.json',dict(T01='PASS future metadata + pixel perturbation synthetic and CT3; all 740 real log rows h<t or null',T02='PASS original bytes/dimensions, all3171 anchors in bounds with P1 above P2',T03='PASS140 empty JSON and exact source bytes',T04='PASS185 sameROI/commonmask/threshold; paired displays share commonmask',T05='PASS missing geometry and blank texture synthetic failures, real failures excluded',T06='PASS3171 source decode/hash +140 real Qt loads',T07='PASS isolated synthetic import states and conflicts',T08='PASS shared group-independent runtime scoring and registration functions',T09='PARTIAL physical scenarios await human annotations; synthetic translation only; historical conflict frames included',T10='PASS deterministic selection + five real representative exact reference/warp/mask replays; timing excluded'))
 source=Path(__file__).parent;snapshot=OUT/'source_snapshot';snapshot.mkdir(exist_ok=False)
 for p in source.iterdir():
  if p.is_file():shutil.copyfile(p,snapshot/p.name)
 versions={name:metadata.version(name) for name in ['numpy','opencv-python','Pillow','scipy','PyQt5','qtpy','imgviz']}
 write(OUT/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),libraries=versions,labelme='5.2.1 isolated output/toolchains',git_commit='NOT_AVAILABLE: workspace is not a Git repository',random_seed=20261111,opencv_threads=1))
 artifacts={}
 for p in sorted(OUT.iterdir()):
  if p.is_file() and p.name!='final_artifact_manifest.json':artifacts[p.name]=dict(sha256=sha(p),bytes=p.stat().st_size)
 write(OUT/'final_artifact_manifest.json',dict(source=tree(source),source_snapshot=tree(snapshot),artifacts=artifacts,annotation_directory='editable human working copy; immutable initial delivery is ZIP',production='UNCHANGED',conclusion='AWAITING_MANUAL_ANNOTATION'))
 print('FINALIZED: five real replays exact; source and delivery hashes saved',flush=True)
if __name__=='__main__':main()
