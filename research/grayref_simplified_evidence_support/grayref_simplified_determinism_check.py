"""Repeat four predeclared development BMP inputs with frozen image-only code; no GT."""
import argparse,json,time,hashlib
from pathlib import Path
import cv2,numpy as np
from grayref_simplified_evidence_v0.common import *
from grayref_simplified_evidence_v0.algorithm import detect,CONFIG
from grayref_simplified_evidence_v0.run_all import check_sources

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();run=Path(a.run);check_sources(run);cv2.setNumThreads(1);data=safe_manifest(run/'input_manifest.csv');records=[]
    for g in sorted(DEV):
        group=[r for r in data if r['group']==g];r=group[len(group)//2];C=imread(r['current']);R=imread(r['reference']);rp=json.loads(r['reference_points']);cp=json.loads(r['current_points']);tick=time.perf_counter()
        aa,ra,ga=detect(current_uint8=C,reference_uint8=R,P_ref=rp,P_cur=cp,config=CONFIG)
        ab,rb,gb=detect(current_uint8=C,reference_uint8=R,P_ref=rp,P_cur=cp,config=CONFIG)
        assert ra==rb and aa['roi']==ab['roi'] and aa['reference_windows']==ab['reference_windows']
        arrays=0
        for key in aa['diff']:assert np.array_equal(aa['diff'][key],ab['diff'][key],equal_nan=True);arrays+=1
        for key in ['gray','valley']:
            for x,y in zip(aa[key],ab[key]):assert np.array_equal(x,y,equal_nan=True);arrays+=1
        for mode in ga:
            for key in ga[mode]:assert np.array_equal(ga[mode][key],gb[mode][key],equal_nan=True);arrays+=1
        target=frame_dir(run,r)/'result.json.gz';frozen_match=None
        if target.exists():frozen_match=readgz(target)['results']==ra;assert frozen_match
        records.append(dict(group=g,frame_id=r['frame_id'],all_arrays_exact=arrays,all_nine_mode_paths_tips_and_states_exact=True,roi_exact=True,reference_quality_exact=True,existing_frozen_result_exact=frozen_match,GT_access=False,seconds=time.perf_counter()-tick))
        print(json.dumps(records[-1]),flush=True)
    put(run/'real_repeat_determinism.json',dict(script_sha=sha(__file__),frozen_source_sha=sha(run/'source_hashes.json'),selection='middle manifest row of each DEVELOPMENT group; same preflight selection, no label lookup',records=records,passed=True))

if __name__=='__main__':main()
