"""Independent raw-current-image start points, transcribed before any R05G GT scoring.
Not training data; never imported by the automatic replay runner.
"""
from common import *
import numpy as np,math

def main():
 # Each tuple was visually read from the corresponding raw-only origin sheet.
 # Coordinates are u/L, v/L, tangent angle relative to P1/P2 right normal.
 tables={
 'group_a':[(.32,.025,0),(.32,.022,0),(.34,.025,-.15),(.34,.025,-.15),(.34,.028,-.15),(.34,.028,-.15),(.34,.028,-.15),(.34,.028,-.15),(.34,.025,-.15),(.34,.025,-.15),(.34,.025,-.15),(.34,.025,-.15),(.34,.025,-.15),(.34,.025,-.15),(.34,.025,-.15),(.34,.025,-.15),(.34,.025,-.15),(.34,.025,-.15),(.34,.025,-.15),(.34,.025,-.15)],
 'ct2':[(.25,-.024,-.1),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,0),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,-.1),(.25,-.016,-.1)],
 'group_h':[(.19,0,0),(.19,0,0),(.19,0,0),(.19,-.004,0),(.19,-.004,0),(.19,-.004,0),(.19,0,0),(.19,-.004,0),(.19,-.004,0),(.19,-.004,0),(.19,-.004,0),(.19,-.002,0),(.19,0,0),(.19,-.004,0),(.19,-.004,0),(.19,-.004,0),(.19,-.004,0),(.19,-.004,0),(.19,-.004,0),(.19,-.004,0)],
 'ct3':[(.40,0,0),(.45,-.04,-.45),(.45,-.04,-.45),(.45,-.04,-.45),(.45,-.04,-.45),(.45,-.04,-.45),(.45,-.04,-.45),(.45,-.04,-.45),(.48,-.06,-.45),(.48,-.06,-.45),(.48,-.06,-.45),(.48,-.06,-.45),(.48,-.06,-.45),(.48,-.06,-.45),(.48,-.06,-.45),(.48,-.06,-.45),(.50,-.07,-.45),(.50,-.07,-.45),(.50,-.07,-.45),(.50,-.07,-.45)]}
 uncertain={('group_a',1),('group_a',67),('group_h',1),('group_h',5),('group_h',41),('group_h',115),('group_h',252),('ct2',271),('ct3',1)}
 result=[];indices={g:0 for g in DEV}
 for r in rows(OUT/'seeds/origin_mapping.csv'):
  g=r['dataset_id'];f=int(r['frame_id']);require(g,'development');u,v,theta=tables[g][indices[g]];indices[g]+=1
  origin=np.array(json.loads(r['origin']));forward=np.array(json.loads(r['forward']));normal=np.array(json.loads(r['normal']));L=float(r['spacing']);p=origin+L*(u*forward+v*normal);t=math.cos(theta)*forward+math.sin(theta)*normal
  result.append(dict(dataset_id=g,frame_id=f,seed=[*p.tolist(),*t.tolist()],origin_uv=[u,v],relative_angle=theta,quality='NOTCH_PRIOR_UNCERTAIN' if (g,f) in uncertain else 'RAW_CURRENT_VISUAL_START',operator='agent_visual_raw_current',source_sha256=r['source_sha256'],sheet_sha256=sha(OUT/'seeds'/f'{g}_raw_origin_sheet.jpg'),manual_intervention='one point + one tangent per current frame; no further correction',labelme_read=False,future_frame_used=False,scope='DIAGNOSTIC_SEEDED_ONLY',display_xy=[(u+.1)/1.2*579,(v+.22)/.44*219]))
 write(OUT/'seeds/diagnostic_seeds.json',result)
 write(OUT/'seeds/provenance_lock.json',dict(seed_sha256=sha(OUT/'seeds/diagnostic_seeds.json'),frames=80,manual_points=80,manual_tangents=80,full_paths=0,tip_points=0,labelme_reads=0,source='current raw origin sheets; visual approximate starts, not certified correct starts',uncertain_starts=len(uncertain),perturbation_predeclared='normal +/-2 original px; angle +/-5 degrees; all80, one factor at a time, no best-of selection'))
 print('Seed provenance locked',len(result))
if __name__=='__main__':main()
