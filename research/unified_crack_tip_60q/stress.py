"""Additional synthetic risk probes. Failures are retained, never hidden by threshold tuning."""
import argparse
from .common import *
from .tests import scene,P
from .engine import Engine

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();run=Path(a.run).resolve();cv2.setNumThreads(1);cases=[]
    points=scene(None)
    for x in range(65,250,5):cv2.circle(points,(x,115),1,0,-1)
    cases.append(('isolated_dark_point_chain',points,points.copy(),None,'NULL_NEGATIVE'))
    scratch=scene(None)
    for x in range(65,250,16):cv2.line(scratch,(x,115),(x+11,115),20,1)
    cases.append(('static_fragmented_near_origin_scratch',scratch,scratch.copy(),None,'NULL_NEGATIVE'))
    detached=scene(None);cv2.line(detached,(65,115),(240,115),20,1)
    cases.append(('static_detached_dark_stroke_near_origin',detached,detached.copy(),None,'NULL_NEGATIVE'))
    ring=scene(None);cv2.circle(ring,(85,110),13,0,2);cases.append(('near_origin_marker_ring',ring,ring.copy(),None,'NULL_NEGATIVE'))
    rng=np.random.default_rng(6013);texture=cv2.GaussianBlur(rng.integers(130,230,(220,420),dtype=np.uint8),(0,0),1.5)
    cv2.line(texture,(55,110),(200,110),40,1);cases.append(('strong_raw_trusted_zero_reference',texture,texture.copy(),texture.copy(),'TIP_200_110'))
    rows_out=[]
    for name,current,fixed,previous,expected in cases:
        r,d=Engine().process(current,P,fixed,P,previous,P if previous is not None else None)
        passed=r['tip'] is None if expected=='NULL_NEGATIVE' else r['tip'] is not None and np.linalg.norm(np.asarray(r['tip'])-[200,110])<=3
        folder=run/'synthetic_risk_probes_extended'/name;folder.mkdir(parents=True,exist_ok=True)
        Image=None
        from PIL import Image
        Image.fromarray(current).save(folder/'current.png');putgz(folder/'result.json.gz',r)
        rows_out.append(dict(case=name,expected=expected,status=r['status'],tip=r['tip'],passed=bool(passed),fixed_fraction=r['reference_info']['fixed']['valid_fraction'],prev_fraction=r['reference_info']['prev']['valid_fraction']))
    csvwrite(run/'reports/synthetic_risk_probes_extended.csv',rows_out);put(run/'reports/synthetic_risk_probes_extended.json',rows_out)
    print(json.dumps(clean(rows_out)),flush=True)

if __name__=='__main__':main()
