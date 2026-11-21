"""Supplementary frozen-rule noise-chain controls. No fitting, no real labels."""
import argparse
from pathlib import Path
import cv2,numpy as np
from grayref_simplified_evidence_v0.common import put,save_npz,sha
from grayref_simplified_evidence_v0.algorithm import CONFIG,detect

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args();run=Path(args.run);out=run/'supplementary_controls';out.mkdir(parents=True,exist_ok=True);cv2.setNumThreads(1);records=[]
    for width in [1,2]:
        reference=np.full((256,512),180,np.uint8);current=reference.copy()
        for x in range(100,301,10):current[120,x:x+width]=80
        p=[[40.,50.],[40.,200.]];a,results,graphs=detect(current_uint8=current,reference_uint8=reference,P_ref=p,P_cur=p,config=CONFIG)
        result=next(r for r in results if r['mode']=='C_FUSION_RAW');put(out/f'noise_chain_width{width}_result.json',result);save_npz(out/f'noise_chain_width{width}.npz',current=current,reference=reference)
        records.append(dict(pixel_width=width,spacing_px=10,output_state=result['output_state'],public_tip=result['tip'],candidate_paths=len(result['paths']),observed=sum(p[2] for p in result['paths'][0]['selected_trace']) if result['paths'] else 0,inferred=sum(not p[2] for p in result['paths'][0]['selected_trace']) if result['paths'] else 0,physical_identity=result['physical_main_crack_identity'],known_non_crack_synthetic=True,actual_real_FPR='N/A'))
    put(out/'noise_chain_controls.json',dict(script_sha=sha(__file__),phase='POST_FREEZE_DIAGNOSTIC_NO_TUNING',config=CONFIG,controls=records,real_GT_access=False,algorithm_changed=False));print(records)

if __name__=='__main__':main()
