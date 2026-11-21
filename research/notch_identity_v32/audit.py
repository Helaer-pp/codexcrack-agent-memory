"""Post-seal comparisons. Read-only access to the three completed prediction sweeps."""
import json
from collections import Counter
from itertools import zip_longest

import numpy as np
from .batch import BASE, OUT, GROUPS, ALGS, read, sha, sources
from research.notch_identity_v31.report import aggregate, yes, val
from research.v3_labelme_comparison.compare import write_csv
from research.v3_labelme_comparison.infer import read_csv

MODES = ('full', 'raw_only')


def signature(model):
    return tuple(model[k] for k in ('status','root','tip','points'))


def selected(model):
    diag = model['diagnostics']
    idx = diag.get('selected')
    return diag['candidates'][idx].get('trace', {}) if idx is not None else {}


def audit():
    lock = read(OUT/'freeze.json')
    assert lock['sources'] == sources()
    for name,key in [('group_a.jsonl','group_a'), ('group_a_scores.csv','dev_scores'), ('probes.csv','probes'), ('public_check.json','public_test')]:
        assert sha(OUT/name) == lock[key]
    scores = [r for g in GROUPS for r in read_csv(OUT/(g+'_scores.csv'))]
    rows = {(r['group'],int(r['frame']),r['stage'],r['mode']):r for r in scores}
    metrics = [dict(stage=s,group=g,mode=m,**aggregate([r for r in scores if (r['stage'],r['group'],r['mode'])==(s,g,m)]))
               for s in ALGS for g in GROUPS for m in MODES]
    write_csv(OUT/'ablation_metrics.csv',metrics)
    diagnostics, changes, failures, uncertain, timings = [], [], [], [], []
    parity=0
    disagreements,branches=[],[]
    for g,n in GROUPS.items():
        times,exclusive,paired_delta = [], [], []
        ref_counts, winning = Counter(), Counter()
        differences = Counter()
        for folder in (BASE,OUT):
            seal = read(folder/(g+'_seal.json'))
            assert sha(folder/(g+'.jsonl')) == seal['predictions']
        with (OUT/(g+'.jsonl')).open() as cur, (BASE/(g+'.jsonl')).open() as old:
            for i,(a,b) in enumerate(zip_longest(cur,old),1):
                rec,prior = json.loads(a),json.loads(b)
                assert i == rec['frame'] == prior['frame'] and rec['source_sha'] == prior['source_sha']
                models=rec['models']
                end=models['v3_2']
                full=end['full']
                times.append(end['seconds'])
                exclusive.append(full['diagnostics'].get('reference_seconds',0))
                if full['tip']!=end['raw_only']['tip']:differences['tip']+=1
                if signature(full)!=signature(end['raw_only']):
                    differences['output']+=1
                    disagreements.append(dict(group=g,frame=i,full_tip=full['tip'],raw_tip=end['raw_only']['tip'],
                        full_root=full['root'],raw_root=end['raw_only']['root'],full_points=len(full['points']),
                        raw_points=len(end['raw_only']['points']),labeled=(g,i,'v3_2','full') in rows,
                        reference=selected(full).get('reference',{}),image=f'frames/{g}/{i}.jpg'))
                if full['tip'] is None:differences['invalid']+=1
                for c in full['diagnostics']['candidates']:
                    ref=c.get('trace',{}).get('reference',{}).get('status','NO_REVIEW')
                    ref_counts[ref]+=1
                winning[selected(full).get('reference',{}).get('status','NO_REVIEW')]+=1
                if len(models)==1:continue
                paired_delta.append(models['reference']['seconds']-models['distal']['seconds'])
                for s in ('r02','s3t','v3_1'):
                    for mode in MODES:
                        assert signature(models[s][mode])==signature(prior['models'][s][mode]), (g,i,s,mode)
                        parity+=1
                for mode in MODES:
                    endrow=rows[g,i,'v3_2',mode]
                    for stage,entry in models.items():
                        m=entry[mode]
                        if mode=='full' and (g,i) in {('three_point_bend',215),('group_c',69),('group_c',335)}:
                            for j,candidate in enumerate(m['diagnostics']['candidates']):
                                audit_data=candidate.get('trace',{})
                                branches.append(dict(group=g,frame=i,stage=stage,idx=j,selected=m['diagnostics'].get('selected')==j,
                                    start=candidate['start'],tip=candidate['tip'],status=candidate['status'],
                                    geometry=audit_data.get('geometry'),cut=audit_data.get('geometry_cut'),events=audit_data.get('events'),
                                    ref=audit_data.get('reference'),gate=audit_data.get('gate')))
                        trace=selected(m)
                        ref=trace.get('reference',{})
                        diagnostics.append(dict(group=g,frame=i,stage=stage,mode=mode,root=m['root'],tip=m['tip'],
                            gt=endrow['gt'],status=m['status'],geometry=trace.get('geometry'),geometry_cut=trace.get('geometry_cut'),
                            rebound_cut=trace.get('rebound_cut'),events=trace.get('events'),ref_status=ref.get('status'),ncc=ref.get('ncc'),
                            shift=ref.get('shift'),ref_cut=ref.get('cut'),before_tip=ref.get('before_tip'),
                            gate=trace.get('gate'),stop=trace.get('stop'),first_loss=trace.get('first_loss'),n_reconnect=trace.get('reconnections'),
                            rejected_taper=trace.get('taper_rejections',0),body=trace.get('body'),tail=trace.get('tail'),front=trace.get('front')))
                    if endrow['state']!='VISIBLE':
                        uncertain.append(endrow)
                        continue
                    if not yes(endrow,'joint'):
                        failures.append({**endrow,**{k:v for k,v in diagnostics[-1].items() if k not in endrow},
                            **{s+'_error':rows[g,i,s,mode]['error_px'] for s in ALGS[:-1]},
                            'overlay':f'labels/{g}/{i}.png'})
                    for s in ('s3t','v3_1'):
                        baseline=rows[g,i,s,mode]
                        flags=[field+'_lost' for field in ('hit10','joint') if yes(baseline,field) and not yes(endrow,field)]
                        err=val(endrow['error_px']); olderr=val(baseline['error_px'])
                        if olderr is not None and (err is None or err>olderr+1e-9):flags.append('error_up')
                        for field in ('coverage','precision'):
                            if float(endrow[field])<float(baseline[field])-1e-9:flags.append(field+'_down')
                        if flags:
                            changes.append(dict(group=g,frame=i,mode=mode,baseline=s,changes=','.join(flags),
                                old_tip=models[s][mode]['tip'],tip=end[mode]['tip'],old_error=olderr,error=err,
                                old_coverage=baseline['coverage'],coverage=endrow['coverage'],old_precision=baseline['precision'],precision=endrow['precision']))
        assert len(times)==n
        timings.append(dict(group=g,n=n,mean_ms=1000*np.mean(times),fps=1/np.mean(times),p95_ms=1000*np.percentile(times,95),
            worst_ms=1000*max(times),worst_frame=1+int(np.argmax(times)),review_ms=1000*np.mean(exclusive),
            active_review_frames=sum(t>0 for t in exclusive),paired_delta_ms=1000*np.mean(paired_delta),
            full_raw_tip_changes=differences['tip'],full_raw_output_changes=differences['output'],invalid=differences['invalid'],
            candidates=dict(ref_counts),selected=dict(winning)))
    assert parity==360
    write_csv(OUT/'stage_diagnostics.csv',diagnostics)
    write_csv(OUT/'focus_candidates.csv',branches)
    write_csv(OUT/'mode_disagreements.csv',disagreements)
    write_csv(OUT/'failures.csv',failures)
    write_csv(OUT/'regressions.csv',changes)
    write_csv(OUT/'uncertain.csv',uncertain)
    write_csv(OUT/'timing.csv',timings)
    return rows, metrics, diagnostics, changes, failures, timings, parity
