"""Count actual stored MT registration decisions at native frame, window and side resolution."""
import json
from collections import Counter
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b
from .run import frozen


def main():
    frozen()
    path=b.OUT/'group_h.jsonl'
    assert b.sha(path)==b.read(b.OUT/'group_h_seal.json')['predictions']
    summary=Counter();frame_rows=[];rows=[]
    for rec in map(json.loads,path.open(encoding='utf8')):
        windows=rec['mappings']['original']['S2']['windows']
        byframe=Counter()
        for w in windows:
            for side in ('up','down','single'):
                reason=w[side+'_status']
                if reason is None:continue
                peak=w[side+'_ncc']
                if side=='single':
                    adopted='single' in (w['up_mode'],w['down_mode'])
                    shift=(w['up'] if w['up_mode']=='single' else w['down']) if adopted else None
                else:
                    adopted=w[side+'_mode']=='side'
                    shift=w[side] if adopted else None
                assert adopted==(reason=='OK')
                flags=dict(attempt=1,insufficient=reason=='INSUFFICIENT_CONTEXT',low_texture=reason=='LOW_TEXTURE',
                           ncc=peak is not None,ambiguous=reason=='AMBIGUOUS',low_ncc=reason=='LOW_NCC',
                           adopted=adopted,nonzero=bool(shift and max(map(abs,shift))))
                assert flags['insufficient']+flags['low_texture']+flags['ncc']==1
                byframe.update(flags)
                for key,value in flags.items():summary[side,key]+=value
                rows.append(dict(frame=rec['frame'],x0=w['x0'],x1=w['x1'],side=side,reason=reason,
                                 ncc=peak,adopted=adopted,shift=shift,white_fraction=w['white_fraction']))
        frame_rows.append(dict(frame=rec['frame'],windows=len(windows),mapped=byframe['adopted']>0,**byframe))
    assert len(frame_rows)==410
    write_csv(b.OUT/'group_h_ncc_windows.csv',rows)
    write_csv(b.OUT/'group_h_ncc_frames.csv',frame_rows)
    write_csv(b.OUT/'group_h_ncc_summary.csv',[dict(side=side,**{key:summary[side,key] for key in flags}) for side in ('up','down','single')])

if __name__=='__main__':main()
