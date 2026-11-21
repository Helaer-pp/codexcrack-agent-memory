"""Declared release gates; a failing candidate stays in the experimental results."""
STAGES=('S1','S2','S3','S4')
P6=('P6_isolated','P6_deformed_scratch')
MIN_BLOCK_FPS=8.
PROTECTED={'group_a':(113,299,366),'three_point_bend':(215,248,381),'group_c':(38,54)}

def eligible(stage, rows, baseline, previous, synth, prev_synth, fps):
    reasons=[]
    for key, original in baseline.items():
        row=rows[key]
        if (original['joint']=='True' or previous[key]['joint']=='True') and row['joint']!='True':
            reasons.append(f'{key}: lost Joint')
        if row['severe']=='True':reasons.append(f'{key}: severe')
        if key[0]=='group_a' and key[2] in PROTECTED['group_a'] and float(row['error_px'] or 'inf')>float(original['error_px'])+1e-6:
            reasons.append(f'{key}: thin tip error increased')
    if synth['fp'] or any(synth[k]!=36 for k in ('active_fork','weak_material_bridge','mouth_glare_arc_only','P4_open')):
        reasons.append('synthetic safety/control')
    if fps<MIN_BLOCK_FPS:reasons.append('slowest TPB block below 8 FPS')
    if stage=='S4' and any(a<=b for k in P6 for a,b in zip(synth[k],prev_synth[k])):
        reasons.append('P6 did not improve at every zoom')
    return reasons

def choose(reasons):
    # Test the most complete safe candidate; absolute programme targets are reported separately.
    return next((s for s in reversed(STAGES) if not reasons[s]), None)
