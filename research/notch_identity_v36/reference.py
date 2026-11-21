"""Whole-mouth signed-ridge search and reference-supported terminal rollback."""
import numpy as np
import cv2
from research.notch_identity_v35.reference import Support as Prior
from research.notch_identity_v31.detector import px

class Support(Prior):
    def mouth_seeds(self,starts,front):
        if self.ridge is None:return []
        x,y=np.array(starts).T;h,width=self.ridge.shape
        pad=px(self.s,.025);length=px(self.s,.043)
        left=max(0,int(x.min()));right=min(width-length-1,front+px(self.s,.10))
        top=max(1,int(y.min())-pad);bottom=min(h-2,int(y.max())+pad)
        if left>right or top>=bottom:return []
        ys=np.arange(top,bottom+1);xs=np.arange(left,right+length+1)
        # Compensate local illumination using the two flanks, then integrate both
        # signs across a vertical strip. Paths are traced rightwards in this frame.
        delta=self.aligned.astype(np.float32)-self.gray
        r=px(self.s,.014)
        def slab(d):return delta[np.clip(ys+d,0,h-1)[:,None],xs]
        center=(slab(-r)+slab(r))*.5
        pos=np.zeros_like(center);neg=pos.copy()
        for off in range(-r,r+1):
            val=slab(off)-center
            pos+=np.maximum(val-self.noise*.5,0)
            neg+=np.maximum(-val-self.noise*.5,0)
        ridge=self.ridge[ys[:,None],xs]
        floor=max(2.5*self.noise,.020*self.contrast)
        good=(neg<.5*pos)&(ridge>=floor)&(pos-neg>=floor)
        strength=np.where(good,np.clip(ridge/floor,0,5),0.)
        # Directional windows from every row and column, including starts without
        # an original grayscale seed. Non-maximum suppression keeps distinct roots.
        score=np.zeros((len(ys),right-left+1))
        for slope in (-.60,-.30,0.,.30,.60):
            value=np.zeros_like(score);count=np.zeros_like(score)
            for j in range(length):
                jrow=np.clip(np.arange(len(ys))+round(slope*j),0,len(ys)-1)
                section=strength[jrow,j:j+score.shape[1]]
                value+=section;count+=section>0
            score=np.maximum(score,np.where(count>=.70*length,value/length,0))
        score*=good[:,:score.shape[1]]
        # The difference can reveal the first new segment downstream of a pre-existing
        # crack. Require a physical grayscale connection to the dark notch body.
        patch_left=max(0,left-px(self.s,.06))
        patch=self.gray[top:bottom+1,patch_left:right+1]
        material=np.percentile(patch,85)
        ink=patch < material-max(3.5*self.noise,.07*self.contrast)
        _,labels=cv2.connectedComponents(ink.astype(np.uint8),connectivity=8)
        core=patch[:,:max(1,left-patch_left+1)] < material-.45*self.contrast
        counts=np.bincount(labels[:,:core.shape[1]][core],minlength=2)
        counts[0]=0
        if counts.max()<max(2,px(self.s,.02)):return []
        connected=labels==counts.argmax()
        score*=connected[:,left-patch_left:]
        seeds=[]
        while len(seeds)<12 and score.max()>0:
            i,j=np.unravel_index(score.argmax(),score.shape)
            seeds.append((int(xs[j]),int(ys[i])))
            dx=px(self.s,.030);dy=px(self.s,.016)
            score[max(0,i-dy):i+dy+1,max(0,j-dx):j+dx+1]=0
        return seeds

    def accept_lip(self,x,y,event):
        if super().accept_lip(x,y,event):return True
        a,b,c=map(int,event[:3])
        if a>self.front+px(self.s,.035) or a-x[0]>px(self.s,.045):return False
        ids=(x>=max(x[0],a-px(self.s,.018)))&(x<=c)
        if ids.sum()<px(self.s,.025):return False
        _,data=self.evidence(np.column_stack((x[ids],y[ids])))
        if data is None:return False
        gap=(x[ids]>=a)&(x[ids]<b);recovered=x[ids]>=b
        return bool(gap.any() and recovered.any() and data['good'][gap].mean()>=.7
                    and data['good'][recovered].mean()>=.8 and data['dup'].mean()<.15
                    and data['neg'].sum()<.5*data['pos'].sum())

    def review(self,points):
        rev=super().review(points)
        if self.patch!='rollback' or rev['source']=='NONE':return rev
        pts=np.asarray(points,int)
        matched=rev['decision'] in ('TRIM_MATCHED_SHAPE','TRIM_DUPLICATE')
        if not matched and (rev['cut'] is not None or not rev.get('body_net')):return rev
        end=int(rev['cut']) if matched else int(pts[-1,0])
        lo=max(pts[0,0],end-px(self.s,.15));margin=px(self.s,.024)
        xx=np.arange(max(pts[0,0],lo-margin),min(pts[-1,0],end+margin)+1)
        if len(xx)<2*margin+1:return rev
        yy=np.interp(xx,pts[:,0],pts[:,1])
        _,d=self.evidence(np.column_stack((xx,np.rint(yy).astype(int))))
        if d is None:return rev
        net=d['net'];floor=max(2*self.noise,.012*self.contrast)
        weak=net<=floor
        length=px(self.s,.020);end_id=int(np.searchsorted(xx,end))
        rev['low_run']=0;rev['break_x']=None
        low=np.flatnonzero(np.diff(np.r_[False,weak,False])).reshape(-1,2)
        for a,b in reversed(low):
            if not lo<=xx[a]<end:continue
            rev['low_run']=max(rev['low_run'],int(min(b,end_id+1)-a))
            if a<margin or b-a<length:continue
            if d['good'][a-margin:a].mean()<.50:continue
            # Without a matched scratch only suppress an unsupported continuation.
            if not matched and (b>=len(xx) or d['good'][b:].mean()>.32):continue
            rev['break_x']=int(xx[a]);break
        if matched:
            # Test the transition from the previous trunk to the orientation of
            # the matched suffix; isolated zigzags inside the suffix are ignored.
            for k in range(min(end_id-1,len(xx)-margin-1),margin-1,-1):
                if xx[k]<lo:break
                before=np.arctan2(yy[k]-yy[k-margin],margin)
                after=np.arctan2(yy[k+margin]-yy[k],margin)
                if abs(after-before)<=np.deg2rad(18) or d['good'][k-margin:k].mean()<.55:continue
                if np.median(net[k:k+margin])>np.median(net[k-margin:k])*.8:continue
                if rev['break_x'] is None or xx[k]<rev['break_x']:rev['break_x']=int(xx[k])
                break
        if rev['break_x'] is not None:
            rev.update(prior_cut=rev['cut'],prior_decision=rev['decision'],cut=rev['break_x'],
                       decision='STRIP_STATIC_BRANCH' if matched else 'TRIM_INTERRUPTED_DELTA')
        return rev
