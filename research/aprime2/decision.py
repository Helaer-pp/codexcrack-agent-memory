"""Transparent short/continue competition. Research output never changes native A."""
from common import *
PARAM=dict(min_disputed_px=24.,coverage=.9,static_fraction=.85,min_pre_samples=3,
           pre_new_fraction=.8,reference_line_snr=6.,reference_noise_floor=1.,
           min_margin=.12,stability_perturbation_px=.5)

def select(pool,evidence,A_tip,A_valid,allow=False):
    audit=[]
    result=dict(valid=bool(A_valid),tip=A_tip if A_valid else None,decision='A_UNCHANGED',
                reason='NO_TRUSTED_DISPUTED_INTERVAL',ownership='UNKNOWN',selected_origin='A_ORIGINAL' if A_valid else 'A_NO_TIP')
    if not pool or len(evidence)<3:return result,audit
    # Canonical ordering means caller candidate-order cannot break a tie.
    candidates=sorted([c for c in pool if not c['A_original_bitwise']],key=lambda c:(c['s'],c['xy'][0],c['xy'][1]))
    end=max(e['arc_s'] for e in evidence)
    for c in candidates:
        s=c['s'];pre=[e for e in evidence if s-24<=e['arc_s']<s-4];post=[e for e in evidence if s+6<e['arc_s']<end-4]
        good=[e for e in post if e['O']];before=[e for e in pre if e['O']]
        coverage=sum(e['O'] for e in post)/max(1,len(post))
        noise=[max(1.,abs(e['Vcur']/e['Q'])) if abs(e['Q'])>1e-9 else 1. for e in good]
        static=[e['Vref']>PARAM['reference_line_snr']*n and e['Vcur']>4*n for e,n in zip(good,noise)]
        new_after=[e['Vcur']>4*n and e['Vref']<3*n and e['DeltaV']>4*n for e,n in zip(good,noise)]
        new_before=[e['DeltaV']>4 and e['Vref']<max(3.,.2*e['Vcur']) for e in before]
        stat=float(np.mean(static)) if static else 0.
        prefrac=float(np.mean(new_before)) if new_before else 0.
        # A static crossing followed by new signal explicitly supports CONTINUE.
        reappears=any(all(new_after[k:k+3]) for k in range(max(0,len(new_after)-2)))
        enough=end-s>=PARAM['min_disputed_px'] and len(before)>=PARAM['min_pre_samples'] and coverage>=PARAM['coverage']
        support=bool(enough and stat>=PARAM['static_fraction'] and prefrac>=PARAM['pre_new_fraction'] and not reappears)
        audit.append(dict(candidate_id=c['candidate_id'],s=s,pre_observed=len(before),post_observed=len(good),
            disputed_coverage=coverage,static_fraction=stat,new_before=prefrac,new_reappears=reappears,
            H_STOP_pattern=support,H_CONTINUE_supported=reappears,
            pattern_reason='CONTINUE_NEW_AFTER_STATIC' if reappears else 'STATIC_TAIL_WITH_NEW_PREFIX' if support else 'INSUFFICIENT_OR_CONFLICTING_EVIDENCE',
            selected=False))
    supported=[r for r in audit if r['H_STOP_pattern']]
    # This pattern alone has a known confound: a preexisting crack can darken.
    # Require a separately supplied stability validation, never merely pass reg.
    if supported:
        result.update(decision='RESEARCH_UNCONFIRMED',reason='STOP_PATTERN_REQUIRES_PERTURBATION_AND_MORPHOLOGY_VALIDATION',ownership='UNKNOWN')
    if allow:
        raise ValueError('Endpoint relocation not enabled until independent stability/morphology gates pass')
    return result,audit

def validated_decision(ref,cur,path,pool,queries,evidence,A_tip,A_valid,width):
    """Research-only relocation after current morphology + whole-interval stability.

    No first-transition priority: multiple stable stop identities are ambiguous.
    Reference-existing darkening remains a physical confound, so no production claim.
    """
    from local_reference import path_evidence
    base,audit=select(pool,evidence,A_tip,A_valid)
    possible={r['candidate_id'] for r in audit if r['H_STOP_pattern']}
    possible={c['candidate_id'] for c in pool if c['candidate_id'] in possible and
              c['origin']=='SUSTAINED_SUPPORT_CHANGE' and c.get('pre_support',0)-c.get('post_support',0)>2.5}
    if not possible:return base,audit,[]
    perturb=[];stable=set(possible)
    residual=max([q['reg']['holdout_p90_px'] or 0. for q in queries if q['reg']['local_supported']]+[.25])
    delta=max(.25,min(1.,residual))
    for dx,dy,gain in [(delta,0,1),(-delta,0,1),(0,delta,1),(0,-delta,1),(0,0,.98),(0,0,1.02)]:
        sets=[]
        for q in queries:
            reg=q['reg'].copy();reg['M']=np.asarray(reg['M'],float).copy();reg['M'][:,2]+=[dx,dy]
            ph=q['photo'].copy();ph['a']*=gain
            ev,_=path_evidence(ref,cur,path,reg,ph,width);sets.append(ev)
        merged=[]
        for i in range(len(sets[0])):
            valid=[e[i] for e in sets if e[i]['O']]
            x=(valid[0] if valid else sets[0][i]).copy()
            if valid and max(t['DeltaV'] for t in valid)-min(t['DeltaV'] for t in valid)>3:
                x['O']=False
            merged.append(x)
        _,aa=select(pool,merged,A_tip,A_valid)
        passed={r['candidate_id'] for r in aa if r['H_STOP_pattern']}
        stable&=passed
        perturb.append(dict(dx=dx,dy=dy,photo_gain_multiplier=gain,stable_candidates=sorted(passed)))
    if len(stable)==1:
        chosen=next(c for c in pool if c['candidate_id'] in stable)
        base=dict(valid=True,tip=chosen['xy'],decision='RESEARCH_RELOCATED',
            reason='CURRENT_SUPPORT_CHANGE_AND_OBSERVABLE_STATIC_DISPUTE_STABLE',
            ownership='SUPPORTED_RESEARCH_HYPOTHESIS_NOT_PHYSICAL_GT',selected_origin=chosen['origin'])
        for r in audit:r['selected']=r['candidate_id']==chosen['candidate_id']
    elif not stable:
        base.update(decision='RESEARCH_UNCONFIRMED',reason='EVIDENCE_UNSTABLE_UNDER_GEOMETRY_PHOTOMETRY_PERTURBATION')
    else:
        base.update(decision='AMBIGUOUS',reason='MULTIPLE_STABLE_STOP_IDENTITIES')
    return base,audit,perturb
