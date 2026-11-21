"""Export and independently verify both measurements in original-image pixels for every frame."""
import csv,json,math
from . import batch as b
from research.v3_labelme_comparison.infer import read_csv

def measure(m,scene):
    path=m['points'];arc=m['path_length_px'];proj=m['projected_length_px']
    root=m['root'];tip=m['tip']
    if not tip:
        assert not path and arc is None and proj is None
    else:
        assert tip==path[-1] and root==path[0]
        expected=math.fsum(math.dist(a,c) for a,c in zip(path,path[1:]))
        assert math.isclose(arc,expected,abs_tol=1e-8)
        a,c=scene['points_geometry']
        dx,dy=c[0]-a[0],c[1]-a[1];s=math.hypot(dx,dy)
        if scene['points_observed'] and s>0:
            x=tip[0]-(a[0]+c[0])/2;y=tip[1]-(a[1]+c[1])/2
            expected=(x*dy-y*dx)/s*(-1 if dy<0 else 1)
            assert math.isclose(proj,expected,abs_tol=1e-8)
        else:assert proj is None
    d=m.get('diagnostics',{}).get('dual',{})
    selected=next((a for a in d.get('branches',[]) if d.get('pick')=='BRANCH_'+str(a['id'])),{})
    bridge=selected.get('bridge',{})
    return dict(inferred_bridge_columns=(bridge.get('columns',0) if bridge.get('accepted') else 0) if tip else None, status=m['status'],root_x=root[0] if root else None,root_y=root[1] if root else None,
                tip_x=tip[0] if tip else None,tip_y=tip[1] if tip else None,path_length_px=arc,projected_length_px=proj)

def main():
    dest=b.OUT/'crack_lengths.csv';rows=[]
    for g,n in b.GROUPS.items():
        src=b.OUT/(g+'.jsonl')
        assert b.sha(src)==b.read(b.OUT/(g+'_seal.json'))['predictions']
        labels={(int(r['frame']),r['mode']):r for r in read_csv(b.OUT/(g+'_scores.csv')) if r['stage']=='v5_8'}
        with src.open() as stream:
            for i,line in enumerate(stream,1):
                rec=json.loads(line);assert (rec['group'],rec['frame'])==(g,i)
                meta=b.read(b.OLD/'evidence'/g/str(i)/'metadata.json')
                assert meta['input']['image_sha']==rec['source_sha']
                scene=meta['evidence']['scene'];row=dict(group=g,frame=i,image=meta['input']['current'],label_state=labels.get((i,'full'),{}).get('state','UNLABELED'),source_sha256=rec['source_sha'])
                for mode in ('full','raw_only'):
                    checked=measure(rec['models']['v5_8'][mode],scene)
                    row.update({mode+'_'+k:v for k,v in checked.items()})
                    score=labels.get((i,mode),{})
                    row[mode+'_tip_error_px']=score.get('error_px')
                    row[mode+'_joint']=score.get('joint') if score.get('state')=='VISIBLE' else None
                rows.append(row)
            assert i==n
    with dest.open('w',encoding='utf-8-sig',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print('Verified and exported measurements for',len(rows),'frames in two independent modes.')
if __name__=='__main__':main()
