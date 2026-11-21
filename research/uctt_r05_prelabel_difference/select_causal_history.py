"""Causal metadata cache. No labels, group identity, filenames or future data in scoring."""
from collections import deque
import math
RULES=dict(history_capacity=64,candidate_budget=4,roi_max_width=1280,roi_output_max_width=640,
           transition_half_fraction=.025,ecc_iterations=40,minimum_texture_std=4.,minimum_holdout_ncc=.5,
           maximum_holdout_p95=45.,minimum_side_coverage=.7,activation_threshold=25,component_min_pixels=12,
           global_rules_revision=1)
def state(r):
 try:
  p=[[float(r[f'p{k}_x']),float(r[f'p{k}_y'])] for k in [1,2]]
  if r.get('p1p2_valid') not in (True,'True'):return None
  d=math.dist(*p);theta=math.atan2(p[1][1]-p[0][1],p[1][0]-p[0][0])
  return dict(points=p,D=d,theta=theta,M=[(p[0][i]+p[1][i])/2 for i in range(2)])
 except (ValueError,KeyError):return None
def score(current,past):
 a,b=state(current),state(past)
 if a is None or b is None:return None
 angle=abs(math.atan2(math.sin(a['theta']-b['theta']),math.cos(a['theta']-b['theta'])))
 return abs(a['D']-b['D'])/max(a['D']*.01,1)+angle/.03
class CausalHistory:
 def __init__(self,capacity=64):self.cache=deque(maxlen=capacity);self.last=-1
 def candidates(self,current,budget=4):
  t=int(current['frame_order']);assert t>self.last and all(int(r['frame_order'])<t for r in self.cache)
  if state(current) is None:return [],'no_valid_p1p2'
  rr=[(score(current,h),int(h['frame_order']),h) for h in self.cache if score(current,h) is not None]
  return [r[2] for r in sorted(rr,key=lambda z:(z[0],-z[1]))[:budget]],'no_prior_candidate' if not rr else ''
 def add(self,current):
  t=int(current['frame_order']);assert t>self.last;self.last=t;self.cache.append(dict(current))
