"""Independent, post-freeze controls for the low-texture unipolar admission rule."""
import cv2
import numpy as np
from research.notch_identity_v62 import domain as old_domain,terminal as old_terminal
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b,domain,terminal
from .run import frozen


def main():
    frozen(); cv2.setNumThreads(1)
    yy,xx=np.indices((160,310));center=80
    shape=(xx<=70)&(abs(yy-center)<=8+.28*(70-xx))
    coords=np.zeros((2,2));rows=[]
    for fixture_gray in (0,22):
        for length in range(8,23):
            span=(xx>70)&(xx<=70+length)
            for mode in ('unipolar','displaced_line','unchanged'):
                reference=np.where(shape,float(fixture_gray),255.)
                current=reference.copy()
                if mode!='unchanged':
                    current-=span*125*np.exp(-.5*((yy-center)/.85)**2)
                if mode=='displaced_line':
                    reference-=span*125*np.exp(-.5*((yy-center-3)/.85)**2)
                raw=current.astype('uint8');ref=reference.astype('uint8')
                hint=np.array([70,center])
                prep=terminal.prepare(raw,hint,b.SCALE,'S2',ref,hint)
                mapped=domain.ReferenceMap(raw,ref,coords,coords,[0,0,310,160],prep,'S2')
                m=terminal.predict(prep,None,mapped)
                d=m['diagnostics']['dual']
                picked=next((a for a in d['branches'] if d['pick']==f"BRANCH_{a['id']}"),{})
                before=old_terminal.prepare(raw,hint,b.SCALE,'S2',ref,hint)
                old_map=old_domain.ReferenceMap(raw,ref,coords,coords,[0,0,310,160],before,'S2')
                baseline=old_terminal.predict(before,None,old_map)
                rows.append(dict(fixture_gray=fixture_gray,mode=mode,length=length,old_tip=baseline['tip'],tip=m['tip'],stop=d['stop'],
                                 registration=(d.get('registration') or {}).get('status'),
                                 clean_run=max((br.get('curve',{}).get('clean_run',0) for br in d['branches']),default=0),
                                 selected_by_exception=bool(picked.get('curve',{}).get('clean_primer_admitted'))))
    write_csv(b.OUT/'primer_controls.csv',rows)

if __name__=='__main__':main()
