"""Additional no-GT per-frame identity and pruning panel; raw visual layers remain immutable."""
import argparse,collections,json,concurrent.futures as cf
from .common import *
from .pipeline import resultdir

def one(args):
    run,row=args;folder=run/'galleries/frames'/row['group']/row['frame_id'];target=folder/'audit.js'
    from .presentation import clean_card
    r=readgz(resultdir(run,'FULL',row['group'])/(row['frame_id']+'.json.gz'))['result']
    presentation=clean_card(folder,row,r)
    if target.exists():return dict(group=row['group'],frame_id=row['frame_id'],sha=sha(target),presentation=presentation,preferred=r['preferred_uncertain_tip'] is not None)
    r=readgz(resultdir(run,'FULL',row['group'])/(row['frame_id']+'.json.gz'))['result'];d=readgz(resultdir(run,'FULL',row['group'])/(row['frame_id']+'_lineage.json.gz'))
    record=dict(group=row['group'],frame_id=row['frame_id'],selected_track_id=r['selected_track_id'],main_track_id=r['main_track_id'],track_transitions=r['track_transitions'],lineage_summary={k:d[k] for k in ['roots_total','roots_explored','route_states','unvisited_states','candidate_count','budget_exhausted']},pruned_reason_counts=dict(collections.Counter(x['reason'] for x in d['pruned'])),observed_continuation_prefix_count=len(d['deduplicated']),omitted_candidates=[dict(id=p['id'],endpoint=p['endpoint'],reason=p['reason']) for p in d['omitted_candidates']],full_predecessor_and_pruned_records=f'../raw_inference/FULL/{row["group"]}/{row["frame_id"]}_lineage.json.gz',gt_used=False)
    write(target,'window.receiveAudit('+json.dumps(clean(record),ensure_ascii=False,separators=(',',':'))+');')
    return dict(group=row['group'],frame_id=row['frame_id'],sha=sha(target),presentation=presentation,preferred=r['preferred_uncertain_tip'] is not None)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--split',choices=['DEV','ALL'],required=True);ap.add_argument('--workers',type=int,default=4);a=ap.parse_args();run=Path(a.run).resolve()
    if a.split=='ALL':check_freeze(run)
    rs=inventory(run,None if a.split=='ALL' else a.split)
    with cf.ProcessPoolExecutor(a.workers) as pool:records=list(pool.map(one,[(run,r) for r in rs]))
    from .render import VIEWER
    entries=[get(run/'galleries/frames'/r['group']/r['frame_id']/'done.json') for r in rs]
    for entry,record in zip(entries,records):entry['preferred']=record['preferred']
    name='reviewed_index.html' if a.split=='ALL' else 'DEV_reviewed_index.html';write(run/'galleries'/name,VIEWER.replace('__ENTRIES__',json.dumps(entries)))
    put(run/'galleries'/f'{a.split}_identity_audit_seal.json',dict(frames=len(records),records=records,index_sha=sha(run/'galleries'/name)))
    print('VIEWER IDENTITY / PRUNING AUDIT',a.split,len(records),flush=True)

if __name__=='__main__':main()
