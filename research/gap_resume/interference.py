"""Counterfactuals on CT3 frame 109 only. The inserted lines have known ownership."""
import argparse
import cv2
from replay import ROOT, api, csv, np, Path, json, run_extra

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-id',required=True)
    args=parser.parse_args()
    if Path(args.run_id).name!=args.run_id:raise ValueError(args.run_id)
    out=ROOT/'output/runs'/args.run_id
    with (ROOT/'output/runs/ct3_white_frozenA_20261106_r01/逐帧裂纹结果.csv').open(encoding='utf-8-sig') as stream:
        rows=list(csv.DictReader(stream))[:109]
    data=Path(r'D:/datasets\1-引伸计\1-裂纹\2.裂纹扩展\白色喷漆')
    api.BASE=ROOT/'output/build/Release/CrackV4GapResume.dll'
    api.EXPECTED_BASE=api.sha(api.BASE)
    ref=api.read(data/rows[0]['图片名'])
    def anchors(row):
        return [[float(row[f'P{j}x']),float(row[f'P{j}y'])] for j in (1,2)]
    def prefix(reference):
        det=api.Baseline(reference,anchors(rows[0]),mode='auto')
        for i,r in enumerate(rows[:-1]):
            im=reference if i==0 else api.read(data/r['图片名'])
            det.run(im,anchors(r),i==0)
        return det
    actual=api.read(data/rows[-1]['图片名']);pp=anchors(rows[-1])
    det=prefix(ref)
    measured=det.run(actual,pp)
    matrix=np.asarray(measured['native']['transform_reference_to_current'])
    det.close()
    cases=make_cases(ref,actual,matrix)
    result=[]
    for name,reference,current in cases:
        det=prefix(reference)
        z=det.run(current,pp);extra=run_extra(det,current,108)
        result.append(dict(case=name,A_stop=z['native']['stop_reason'],A_tip=z['formal']['tip'],
                           extra=extra['reason'],extra_tip=extra['tip_px'],
                           spans=[[s[0],s[-1]] for s in extra['segments']]))
        det.close()
    api.save(out/'interference.json',result)
    print(json.dumps(result,indent=2))

def make_cases(ref,actual,matrix):
    ref_now=cv2.warpAffine(ref,matrix,ref.shape[::-1],borderMode=cv2.BORDER_REPLICATE)
    def restore_distal(im):
        im=im.copy()
        im[490:620,493:694]=ref_now[490:620,493:694]
        return im
    def mark(im,offset=0,in_reference=False):
        pts=np.array([[497,584+offset],[527,573+offset],[557,558+offset],[584,550+offset],[615,537+offset]],dtype=float)
        if in_reference:
            inv=cv2.invertAffineTransform(matrix)
            pts=pts@inv[:,:2].T+inv[:,2]
        im=im.copy()
        cv2.polylines(im,[np.int32(np.round(pts))],False,40,2,cv2.LINE_AA)
        return im
    cleaned=restore_distal(actual)
    mid_gap=actual.copy()
    mid_gap[520:595,544:561]=ref_now[520:595,544:561]
    return [
        ('real_control', ref, actual),
        ('remove_distal',ref,cleaned),
        ('static_scratch_both',mark(ref,in_reference=True),mark(cleaned)),
        ('competing_parallel',ref,mark(actual,8)),
        ('interrupted_visible_path',ref,mid_gap),
        ('new_collinear_scratch_only',ref,mark(cleaned)),
    ]
if __name__=='__main__':main()
