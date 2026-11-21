"""Offline original-coordinate comparison; no native imports or feedback."""
from common import *
import numpy as np,zipfile,collections
from scipy.spatial import cKDTree

def dense_path(shapes):
 pp=[]
 for s in shapes:
  if s['label']!='crack_path':continue
  p=np.array(s['points'],float)
  for a,b in zip(p[:-1],p[1:]):
   k=max(1,int(np.ceil(np.linalg.norm(b-a))));pp.extend(a+(b-a)*np.arange(k)[:,None]/k)
  if len(p):pp.append(p[-1])
 return np.array(pp,float).reshape(-1,2)

def evaluate(tag='B0'):
 assert read(OUT/(tag+'_complete.json'))['frames']==1565
 baseline={(r['dataset_id'],r['frame_id']):r['formal'] for r in map(json.loads,(OUT/'A0_frames.jsonl').read_text().splitlines())}
 records=[]
 with zipfile.ZipFile(R05/'human_annotations_six_groups_snapshot.zip') as z:
  for s in filter_rows(rows(OUT/'selected_frames.csv'),'development'):
   g=s['dataset_id'];f=int(s['frame_id']);require(g,'comparison',uses_annotations=True)
   label=json.loads(z.read(s['selected_json']));tips=[v['points'][0] for v in label['shapes'] if v['label']=='crack_tip'];visible=len(tips)==1;gt=np.array(tips[0]) if visible else None
   t=read(OUT/'traces'/f'{tag}_{g}_{f}.json');cand=t['candidates'];raw=np.array([v['xy'] for v in cand]).reshape(-1,2);dedup=np.array([v['xy'] for v in cand if v['id']==v['canonical_id']]).reshape(-1,2)
   a=baseline[g,f];err=float(np.linalg.norm(np.array(a['tip'])-gt)) if visible and a['confirmed_tip'] else None
   rec=dict(dataset_id=g,frame_id=f,variant=tag,role='DEVELOPMENT',split=s['split'],visibility='VISIBLE' if visible else 'UNCERTAIN',raw_count=t['raw_candidates'],stored_count=len(cand),dedup_count=len(dedup),search_incomplete=t['search_incomplete'],A0_observed=a['confirmed_tip'],A0_error_px=err,new_observed=False,new_predicted=False,new_fallback=True,new_error_px=None,reason=t['reason'])
   for key,p in [('raw',raw),('dedup',dedup),('budget',dedup)]:
    dist=float(np.linalg.norm(p-gt,axis=1).min()) if visible and len(p) else None
    rec[key+'_nearest_px']=dist
    for tol in [3,5,10]:rec[f'{key}_hit{tol}']=dist<=tol if dist is not None else False if visible else None
   path=dense_path(label['shapes']);ridge=np.array([p for seg in t['segments'] for p in seg['points']]).reshape(-1,2)
   distances=cKDTree(ridge).query(path)[0] if len(ridge) and len(path) else np.full(len(path),np.inf)
   rec['path_sample_count']=len(path)
   for tol in [3,5,10]:rec[f'path_centerline_band_coverage{tol}']=float(np.mean(distances<=tol)) if len(path) else None
   # Budget clipping prevents claims of pre-budget RAW exhaustive recall.
   rec['raw_complete']=t['raw_candidates']==len(cand) and t['raw_segments']==len(t['segments'])
   records.append(rec)
 save(OUT/'experiments'/f'{tag}_candidate_reachability.csv',records)
 summary=[]
 for g in DEV+['ALL']:
  for split in ['all','development','holdout']:
   subset=[r for r in records if (g=='ALL' or r['dataset_id']==g) and (split=='all' or r['split']==split)];vv=[r for r in subset if r['visibility']=='VISIBLE'];aa=[r['A0_error_px'] for r in vv if r['A0_error_px'] is not None]
   out=dict(dataset_id=g,split=split,variant=tag,role='DEVELOPMENT',selected=len(subset),visible=len(vv),uncertain=len(subset)-len(vv),A0_observed=len(aa),new_observed=0,new_missing=len(vv),A0_over100=sum(e>100 for e in aa),A0_over500=sum(e>500 for e in aa),A0_error_p50=float(np.median(aa)) if aa else None,A0_error_p95=float(np.percentile(aa,95)) if aa else None,A0_error_max=max(aa) if aa else None,new_accuracy='N/A shadow evidence only')
   for tol in [3,5,10]:
    out[f'A0_hit{tol}']=sum(e<=tol for e in aa)
    for kind in ['raw','dedup','budget']:out[f'{kind}_hit{tol}']=sum(bool(r[f'{kind}_hit{tol}']) for r in vv)
   summary.append(out)
 save(OUT/'experiments'/f'{tag}_comparison_by_group.csv',summary)
 print([r for r in summary if r['dataset_id']=='ALL' and r['split']=='all'])
 print('SENTINELS',[r for r in records if (r['dataset_id'],r['frame_id']) in [('ct2',395),('group_h',78),('group_a',504),('ct3',65)]])
 return records,summary
if __name__=='__main__':evaluate()
