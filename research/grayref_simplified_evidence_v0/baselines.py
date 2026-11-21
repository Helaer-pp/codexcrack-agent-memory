"""Read-only mapping/replay of actual immutable baseline traces. No GT."""
from .common import OLD,readgz,sha

def load_baselines(row,artifact_files):
    rel=f"frames/{row['group']}/{row['frame_id']}/result.json.gz";path=OLD/rel
    # Original artifact keys are slash-normalized.
    expected=artifact_files.get(rel) or artifact_files.get(rel.replace('/','\\'))
    if expected is None or sha(path)!=expected['sha256']:raise ValueError('Frozen baseline identity mismatch '+rel)
    old=readgz(path)
    for field in ['image_sha','ref_sha','reference_points','current_points']:
        incoming=row[field]
        import json
        if field.endswith('points'):incoming=json.loads(incoming)
        if old['input'][field]!=incoming:raise ValueError('Baseline input mapping mismatch '+field)
    results=[old['baseline']]+[x for x in old['results'] if x['mode'] in ['V2_NUMERIC_CONTROL','V2_COMBINED']]
    adapted=[]
    for r in results:
        trace=[[p[0],p[1],int(p[2])] for p in r['trace']]
        paths=[]
        if trace:
            paths=[dict(id=r.get('chosen_path_id',0),selected_trace=trace,observed_trace=trace,bridges=[],candidate_tip=r['candidate_tip'],last_observed_pixel=r['candidate_tip'],stop_candidates=[],components={})]
        adapted.append(dict(mode=r['mode'],output_state=r['output_state'],tip=r['tip'],candidate_tip=r['candidate_tip'],last_observed_pixel=r['candidate_tip'],tip_status=r['output_state'],paths=paths,chosen_path_id=r.get('chosen_path_id'),source_result=str(path),source_sha256=expected['sha256'],replay_kind='EXACT_IMMUTABLE_RESULT_AND_TRACE_REPLAY_NOT_NEW_DETECTOR_RUN',gt_accessed=False))
    return adapted,old['roi']
