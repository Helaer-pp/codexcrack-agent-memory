"""Check downstream selector support, score and geometric constraints on fixed directional paths."""
import numpy as np
from research.notch_identity_v55.terminal import link_evidence

def main():
    s=100.
    early=np.column_stack((np.arange(35),np.full(35,5)))
    late=np.column_stack((np.arange(47),np.full(47,5)))
    score=np.full((48,24),.7,np.float32)
    fine=np.zeros_like(score,bool)
    score[35:38,5]=-.9
    fine[38:44,5]=True
    assert link_evidence(early,late,score,fine,s,23.,20.)['ok']
    cross=late.copy();cross[:,1]+=5
    assert 'SAME_BRANCH' in link_evidence(early,cross,score,fine,s,23.,20.)['reason']
    assert 'RATIO' in link_evidence(early,late,score,fine,s,23.,14.)['reason']
    score[35:43,5]=-1.3;fine[:]=False
    reject=link_evidence(early,late,score,fine,s,23.,20.)
    assert not reject['ok'] and 'GAP' in reject['reason'] and reject['deepest_gap']==8
    print('Accepted supported continuation; rejected parallel branch, low score and unsupported gap.')

if __name__=='__main__':
    main()
