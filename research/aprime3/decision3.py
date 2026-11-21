from common3 import *
from decision import validated_decision
from local_reference import inside

def decide(ref,cur,path,pool,queries,ev,tip,valid,width):
    # Multiscale proposals share the same current-response morphology semantics.
    adapted=[dict(c,origin='SUSTAINED_SUPPORT_CHANGE' if c['origin']=='MULTISCALE_SUPPORT_CHANGE' else c['origin']) for c in pool]
    legacy,audit,perturb=validated_decision(ref,cur,path,adapted,queries,ev,tip,valid,width)
    result=dict(valid=bool(valid),tip=tip if valid else None,decision='A_FALLBACK_NOT_VERIFIED',reason='NO_INDEPENDENT_STOP_SUPPORT',hypothesis='H_UNRESOLVED')
    for a in audit:
        relevant=[e for e in ev if e['arc_s']>a['s']+6]
        darkened=sum(e.get('interval_state')=='UNKNOWN_REFERENCE_DARKENING' for e in relevant)/max(1,len(relevant))
        static=sum(e.get('interval_state')=='SUPPORTED_STATIC' for e in relevant)/max(1,len(relevant))
        a['darkening_ambiguity_fraction']=darkened;a['trusted_static_fraction']=static
        a['hypothesis']='H_CONTINUE' if a['new_reappears'] else 'H_UNRESOLVED' if darkened>.15 else 'H_STOP' if a['H_STOP_pattern'] else 'H_UNRESOLVED'
    if legacy['decision']=='RESEARCH_RELOCATED':
        chosen=next((a for a in audit if a.get('selected')),None)
        if chosen and chosen['darkening_ambiguity_fraction']>.15:
            result.update(reason='REFERENCE_DARKENING_IS_NOT_PHYSICAL_OWNERSHIP',hypothesis='H_UNRESOLVED')
        else:result=dict(legacy,hypothesis='H_STOP')
    elif legacy['decision'] in ['AMBIGUOUS','RESEARCH_UNCONFIRMED']:
        result.update(reason=legacy['reason'])
    return result,audit,perturb,legacy

class EndpointHistory:
    def __init__(self):self.ends=[]
    def update(self,M,pool,queries,official_tip,official_valid):
        records=[]
        def validated_reference_point(point):
            footprint=np.asarray(point)+np.array([[-3,-3],[-3,3],[3,-3],[3,3]])
            for q in queries:
                if q['reg']['local_supported'] and q['photo']['state']=='PHOTO_SUPPORTED' and inside(q['reg']['polygon'],footprint):
                    return apply(cv2.invertAffineTransform(np.asarray(q['reg']['M'],float)),[point])[0]
            return None
        for c in pool:
            refp=validated_reference_point(c['xy']);covered=refp is not None
            distance=min([np.linalg.norm(refp-x) for x in self.ends]+[float('inf')]) if covered else float('inf')
            records.append(dict(candidate_id=c['candidate_id'],past_endpoint_distance=float(distance) if np.isfinite(distance) else None,
                status='SUPPORTED_LOCAL_PROXIMITY_ONLY' if covered and distance<=max(3.,c.get('local_W',2.) or 2.) else 'UNKNOWN',
                reason='NOT_OWNERSHIP_NOT_MONOTONIC_PRIOR'))
        if official_valid:
            rp=validated_reference_point(official_tip)
            if rp is not None:self.ends.append(rp);self.ends=self.ends[-5:]
        return records
