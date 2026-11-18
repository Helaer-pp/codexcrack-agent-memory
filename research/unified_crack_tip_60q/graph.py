"""Bounded segment graph, with all tested pair outcomes retained."""
import math
import numpy as np
from scipy.spatial import cKDTree
from numba import njit

@njit(cache=True)
def line_support(points,pairs,valley,xa,ya,threshold):
    out=np.zeros(len(pairs),np.float32)
    for i in range(len(pairs)):
        a=points[pairs[i,0]];b=points[pairs[i,1]];d=math.hypot(a[0]-b[0],a[1]-b[1]);n=max(1,int(math.ceil(d))-1);hit=0
        for j in range(n):
            t=(j+1)/(n+1);x=int(round(a[0]*(1-t)+b[0]*t))-xa;y=int(round(a[1]*(1-t)+b[1]*t))-ya
            if 0<=x<valley.shape[1] and 0<=y<valley.shape[0] and valley[y,x]>=.5*threshold:hit+=1
        out[i]=hit/n
    return out

def build_graph(e,c):
    f=e['features'];n=len(f);xy=e['xy'];ptr=e['ptr'];base=(f[:,0]>=2)&e['component_structure'][e['component_ids']]&~np.asarray(e['cyclic'],bool)
    endpoints=f[:,11:15].reshape(-1,2).astype(np.float64)
    small=(f[:,0]>=2)&~base&~np.asarray(e['cyclic'],bool)
    eligible=base.copy()
    if base.any() and small.any():
        tree=cKDTree(endpoints[np.repeat(base,2)])
        distance,_=tree.query(endpoints[np.repeat(small,2)],k=1)
        eligible[small]=(distance.reshape(-1,2).min(1)<=c['short_gap']+1)
    ids=np.flatnonzero(np.repeat(eligible,2));pts=endpoints[ids]
    gap=int(np.clip(round(e['scene']['scale']*c['gap_scale']),c['gap_min'],c['gap_max']))
    pairs=cKDTree(pts).query_pairs(gap+1,output_type='ndarray') if len(pts) else np.empty((0,2),np.int64)
    topology_rejected=0
    if len(pairs):
        pairs=ids[pairs];pairs=pairs[pairs[:,0]//2!=pairs[:,1]//2]
        same=e['component_ids'][pairs[:,0]//2]==e['component_ids'][pairs[:,1]//2]
        distance=np.linalg.norm(endpoints[pairs[:,0]]-endpoints[pairs[:,1]],axis=1)
        redundant=same&(distance>1.5);topology_rejected=int(redundant.sum());pairs=pairs[~redundant]
        pairs=pairs[np.lexsort((pairs[:,1],pairs[:,0]))]
    budget=len(pairs)>c['max_graph_pairs'];potential=len(pairs);pairs=pairs[:c['max_graph_pairs']]
    tangent=np.zeros((2*n,2),float)
    for k in np.flatnonzero(eligible):
        p=xy[ptr[k]:ptr[k+1]].astype(float)
        for side,v in [(0,p[0]-p[min(4,len(p)-1)]),(1,p[-1]-p[max(0,len(p)-5)])]:
            tangent[2*k+side]=v/max(1e-6,np.linalg.norm(v))
    if not len(pairs):return np.empty((0,8),np.float32),eligible,dict(potential_pairs=potential,accepted=0,rejected=0,budget_exhausted=budget,gap_bound=gap)
    delta=endpoints[pairs[:,1]]-endpoints[pairs[:,0]];dist=np.linalg.norm(delta,axis=1);unit=delta/np.maximum(dist[:,None],1e-6)
    ca=(tangent[pairs[:,0]]*unit).sum(1);cb=-(tangent[pairs[:,1]]*unit).sum(1)
    junction=dist<=1.5;jcos=-(tangent[pairs[:,0]]*tangent[pairs[:,1]]).sum(1)
    angle_ok=np.where(junction,jcos>=math.cos(math.radians(c['max_turn_degrees'])),(ca>=.5)&(cb>=.5))
    support=np.zeros(len(pairs),np.float32);long=(dist>c['short_gap']+1)&angle_ok
    if long.any():support[long]=line_support(endpoints,pairs[long],e['valley'],e['scene']['bounds'][0],e['scene']['bounds'][1],e['threshold'])
    strong=(f[pairs[:,0]//2,2]>=c['strong_factor']*e['threshold'])&(f[pairs[:,1]//2,2]>=c['strong_factor']*e['threshold'])
    long_ok=(ca>=math.cos(math.radians(c['long_gap_turn'])))&(cb>=math.cos(math.radians(c['long_gap_turn'])))&strong&(support>=.2)
    code=np.zeros(len(pairs),np.int32);code[~angle_ok]=1;code[long&~long_ok]=2
    valid=np.flatnonzero(code==0)
    if len(valid)>c['max_edges']:code[valid[c['max_edges']:]]=3;budget=True
    # code0 allowed,1 direction,2 long-gap lacks current support,3 budget not examined.
    edges=np.column_stack([pairs,dist,np.maximum(0,dist-1),ca,cb,support,code]).astype(np.float32)
    return edges,eligible,dict(potential_pairs=potential,accepted=int((code==0).sum()),rejected=int((code!=0).sum()),same_component_shortcuts_not_proposed=topology_rejected,budget_exhausted=budget,gap_bound=gap,
                            outcome_codes={'0':'GEOMETRIC_CONNECTION','1':'DIRECTION_INCONSISTENT','2':'LONG_GAP_UNSUPPORTED','3':'EDGE_BUDGET'})
