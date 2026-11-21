"""Offline budget causality comparison, after image-only probe completed."""
from compare import *

def main():
 dest=OUT/'stateless_budget_x8';assert read(dest/'complete.json')['frames']==80
 baseline={(r['dataset_id'],int(r['frame_id'])):r for r in rows(OUT/'experiments/B0_candidate_reachability.csv')};rr=[]
 with zipfile.ZipFile(R05/'human_annotations_six_groups_snapshot.zip') as z:
  for s in filter_rows(rows(OUT/'selected_frames.csv'),'development'):
   g=s['dataset_id'];f=int(s['frame_id']);require(g,'comparison',uses_annotations=True);t=read(dest/f'{g}_{f}.json');b=baseline[g,f]
   label=json.loads(z.read(s['selected_json']));tips=[v['points'][0] for v in label['shapes'] if v['label']=='crack_tip'];visible=len(tips)==1;gt=np.array(tips[0]) if visible else None
   allp=np.array([c['xy'] for c in t['candidates']]).reshape(-1,2);dedup=np.array([c['xy'] for c in t['candidates'] if c['id']==c['canonical_id']]).reshape(-1,2)
   r=dict(dataset_id=g,frame_id=f,kind='stateless_probe_NOT_online',visibility='VISIBLE' if visible else 'UNCERTAIN',B0_raw10=b['raw_hit10'],B0_dedup10=b['dedup_hit10'],B0_incomplete=b['search_incomplete'],probe_incomplete=t['search_incomplete'],probe_candidates=len(allp),probe_dedup=len(dedup),probe_segments=len(t['segments']),probe_api_ms=t['api_ms'],raw_nearest_px=float(np.linalg.norm(allp-gt,axis=1).min()) if visible and len(allp) else None,dedup_nearest_px=float(np.linalg.norm(dedup-gt,axis=1).min()) if visible and len(dedup) else None)
   for tol in [3,5,10]:
    for key in ['raw','dedup']:r[f'{key}_hit{tol}']=r[f'{key}_nearest_px']<=tol if r[f'{key}_nearest_px'] is not None else False if visible else None
   rr.append(r)
 save(dest/'offline_reachability.csv',rr)
 print('x8 raw/dedup10',sum(bool(r['raw_hit10']) for r in rr),sum(bool(r['dedup_hit10']) for r in rr),'incomplete',sum(bool(r['probe_incomplete']) for r in rr))
 print('restored solely by higher cap',[(r['dataset_id'],r['frame_id']) for r in rr if r['raw_hit10'] and r['B0_raw10']!='True'])
if __name__=='__main__':main()
