"""Verify native-sized differences and frame mappings independently of the renderer."""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from .batch import ROOT,OUT,OLD,GROUPS,read,save
from research.v3_labelme_comparison.infer import read_csv
from .difference_views import DEST

def main():
    rows=read_csv(DEST/'coordinates.csv')
    assert len(rows)==sum(GROUPS.values())
    lengths=read_csv(OUT/'crack_lengths.csv')
    assert len(rows)==len(lengths)
    for row,measured in zip(rows,lengths):
        assert (row['group'],row['frame'])==(measured['group'],measured['frame'])
        for key in ('path_length_px','projected_length_px'):
            assert row[key]==measured['full_'+key],(row['group'],row['frame'],key)
    checks=[];root_audit={}
    from research.notch_identity_v31.detector import px
    for g,n in GROUPS.items():
        rr=[r for r in rows if r['group']==g]
        assert [int(r['frame']) for r in rr]==list(range(1,n+1))
        total=0;trials=0;violations=[]
        with (OUT/(g+'.jsonl')).open() as stream:
            for line in stream:
                rec=json.loads(line);m=rec['models']['v5_8']['full'];d=m['diagnostics']['dual']
                if 'front' not in d:continue
                meta=read(OLD/'evidence'/g/str(rec['frame'])/'metadata.json')
                left=d['front'];right=left+d['seed_band']-1
                candidates=[k['start'] for k in m['diagnostics']['candidates']]+[k['seed'] for k in d.get('trials',[])]
                if m['root'] and m['tip']:candidates.append(m['root']);total+=1
                trials+=len(candidates)
                for x,y in candidates:
                    if not left<=x<=right:violations.append(dict(frame=rec['frame'],x=x,left=left,right=right))
        assert not violations,(g,violations[:4])
        root_audit[g]=dict(valid=total,checks=trials,outside=violations)
        for r in (rr[0],rr[n//3],rr[n//2],rr[-1]):
            folder=OLD/'evidence'/g/r['frame']
            off=read(folder/'metadata.json')['evidence']['scene']['bounds'][:2]
            x=int(r['diff_x'])-off[0];y=int(r['diff_y'])-off[1]
            dx,dy=json.loads(r['shift'])
            actual=np.asarray(Image.open(DEST/r['difference']).convert('RGB'))
            h,w=actual.shape[:2]
            assert (h,w)==(int(r['diff_height']),int(r['diff_width']))
            with np.load(folder/'arrays.npz') as z:
                from research.v3_labelme_comparison.infer import current
                cur=z['raw'];meta=read(folder/'metadata.json');info=meta['input']
                l,t,right,bottom=meta['evidence']['scene']['bounds']
                native=current(info['reference'],info['ref_sha'])[t:bottom,l:right].astype('float32')
                with (OUT/(g+'.jsonl')).open() as series:
                    d=next(json.loads(line) for j,line in enumerate(series,1) if j==int(r['frame']))['models']['v5_8']['full']['diagnostics']['dual']
                mapping=d.get('material_map')
                if mapping:
                    sy,sx=np.indices(native.shape,dtype='float32')
                    offsets=np.asarray(mapping['offsets'])
                    xxmap=(sx+np.interp(sy,mapping['rows'],offsets[:,0]).astype('float32')).astype('float32')
                    yymap=(sy+np.interp(sy,mapping['rows'],offsets[:,1]).astype('float32')).astype('float32')
                    ref=cv2.remap(native,xxmap,yymap,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
                else:ref=np.full(native.shape,np.nan,'float32')
                yy,xx=np.indices((h,w));yy+=y;xx+=x
                valid=(xx>=0)&(xx<cur.shape[1])&(yy>=0)&(yy<cur.shape[0])&(xx+dx>=0)&(xx+dx<ref.shape[1])&(yy+dy>=0)&(yy+dy<ref.shape[0])
                if r['status']=='OUTSIDE':valid[:]=False
                diff=np.full((h,w),np.nan,np.float32)
                diff[valid]=0 if r['status']=='SAME' else ref[yy[valid]+dy,xx[valid]+dx].astype(float)-cur[yy[valid],xx[valid]]
                valid=np.isfinite(diff)
                mid=np.array([244,244,240]);red=np.array([182,32,27]);blue=np.array([27,83,168])
                t=np.clip(np.nan_to_num(diff),-32,32)[:,:,None]/32
                rgb=mid+np.maximum(0,t)*(red-mid)+np.maximum(0,-t)*(blue-mid)
                rgb[~valid]=90
                assert np.abs(np.rint(rgb)-actual).max()<=1
                assert int(valid.sum())==int(r['valid_pixels'])
                checks.append(dict(group=g,frame=int(r['frame']),pixels=w*h,valid=int(valid.sum())))
        stream=cv2.VideoCapture(str(DEST/(g+'.mp4')))
        assert int(stream.get(cv2.CAP_PROP_FRAME_COUNT))==n and stream.get(cv2.CAP_PROP_FRAME_WIDTH)==2000
        stream.release()
    assert (DEST/'index.html').is_file()
    save(OUT/'delivery_check.json',dict(frames=len(rows),individual_differences=len(rows),video_frames=GROUPS,sampled_difference_checks=checks,front_band=root_audit))
    print('Verified',len(rows),'comparison/difference pairs;',sum(r['pixels'] for r in checks),'independently checked pixels.')

if __name__=='__main__':main()
