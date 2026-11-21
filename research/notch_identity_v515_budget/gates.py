"""Predeclared eligibility, evaluated once on sealed stages."""
STAGES=("S1","S2","S3")
P6=("P6_isolated","P6_deformed_scratch")
LATENCY_TARGET=4.5
LATENCY_FLOOR=4.0

def select(synthetic,real,speed,anchors):
    eligible=dict(S1=True)
    for stage,base in (("S2","S1"),("S3","S2")):
        counts=synthetic[stage]
        safe=counts["fp"]==0 and counts["bridge"]==36 and counts["glare"]==36
        # Every visible hit and joint from the preceding stage must be preserved.
        retained=all(not old or new for k,old in real[base].items() for new in [real[stage][k]])
        same_anchors=all(anchors[stage][k]<=anchors[base][k]+0.05 for k in anchors[base])
        eligible[stage]=eligible[base] and safe and retained and same_anchors and min(speed[stage])>=LATENCY_TARGET
        if stage=="S3":
            eligible[stage] &= all(min(counts[k])>0 and len(set(counts[k]))==1 for k in P6)
    return next(s for s in reversed(STAGES) if eligible[s]),eligible
