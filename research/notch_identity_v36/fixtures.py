"""Known truth for the three targeted patches, independent of experiment images."""
import numpy as np
from .reference import Support
from .competition import filter_static
from .batch import OUT,save

def main():
    rng=np.random.default_rng(3641)
    bg=np.full((220,480),160,np.uint8)
    bg[:,:205]=np.clip(160+rng.normal(0,15,(220,205)),0,255)
    def ctx(a,b):
        s=Support(a,b.astype('float32'),np.s_[:,:],(0,0),(93,110),260.,1.5,138.,'v3_5')
        s.front=230;s.patch='rollback'
        return s
    bg[87:130,196:227]=40
    bg[97,225:244]=80
    a=bg.copy();a[97,243:275]=85
    roots=[(225,86),(226,130)]
    seeds=ctx(a,bg).mouth_seeds(roots,230)
    assert any(x>=238 and abs(y-97)<=1 for x,y in seeds),seeds
    assert not ctx(a,a).mouth_seeds(roots,230)
    detached=a.copy();detached[97,227:243]=160
    assert not ctx(detached,bg).mouth_seeds(roots,230)
    trials=[({'static_branch':True},None),({'positive_branch':True},None)]
    assert filter_static([0,1],trials)==[1] and filter_static([0],trials)==[0]
    xs=np.arange(230,381);ys=110-np.rint(np.clip(xs-345,0,14)*.45).astype(int)
    path=np.column_stack((xs,ys));a=bg.copy();b=bg.copy()
    for x,y in path:
        if not 340<=x<347:a[y,x]=75
        if x>=359:b[y+6,x]=75
    review=ctx(a,b).review(path)
    assert review.get('prior_cut') and 336<=review['cut']<=347,review
    save(OUT/'fixtures.json',dict(mouth=seeds,static_control=True,veto=True,rollback=review))
if __name__=='__main__':main()
