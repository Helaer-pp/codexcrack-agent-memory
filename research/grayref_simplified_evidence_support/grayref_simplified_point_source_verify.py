"""Read original tracking numbers/P coordinates independently of inference; no labels."""
import argparse,re,json
from pathlib import Path
from grayref_simplified_evidence_v0.common import *

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();run=Path(a.run);manifest=safe_manifest(run/'input_manifest.csv');results=[]
    for group in GROUPS:
        data=[r for r in manifest if r['group']==group];source=Path(data[0]['point_source']);mapping={};names={}
        if data[0]['point_kind']=='original_tracking_txt':
            for line in source.read_bytes().decode('gb18030',errors='replace').splitlines():
                nums=re.findall(r'[-+]?\d+(?:\.\d+)?',line)
                if len(nums)==5 and line.lower().lstrip().startswith('num'):
                    k=int(nums[0]);v=list(map(float,nums[1:]));assert k not in mapping;mapping[k]=[v[:2],v[2:]]
            provenance='ORIGINAL_TRACKING_TXT_NUM_RECORD'
        else:
            assert group=='ct3' and source.suffix.lower()=='.csv'
            for r in rows(source):
                k=int(r['坐标num']);mapping[k]=[[float(r['P1x']),float(r['P1y'])],[float(r['P2x']),float(r['P2y'])]];names[k]=r['图片名']
            provenance='AUDITED_HISTORICAL_COORDINATE_CSV_ONLY_ORIGINAL_TXT_UNAVAILABLE'
        for r in data:
            k=int(r['tracking_num']);cp=json.loads(r['current_points']);rp=json.loads(r['reference_points'])
            assert cp==mapping[k] and rp==mapping[0]
            assert sha(source)==r['point_source_sha']
            if names:assert Path(r['current']).name==names[k] and Path(r['reference']).name==names[0]
            results.append(dict(group=group,frame_id=r['frame_id'],tracking_num=k,reference_tracking_num=0,current_P_exact=True,reference_P_exact=True,source=str(source),source_sha=sha(source),provenance=provenance,coordinate_unit='ORIGINAL_PIXELS_XY',reference_selected_by_label=False))
    csvwrite(run/'point_source_independent_verification.csv',results)
    put(run/'point_source_independent_verification.json',dict(utc=utc(),script_sha=sha(__file__),frames=len(results),current_and_reference_exact=len(results),failures=0,ct3_original_txt_available=False,no_GT_access=True))
    print(f'Independent original P verification: {len(results)}/2647 exact')

if __name__=='__main__':main()
