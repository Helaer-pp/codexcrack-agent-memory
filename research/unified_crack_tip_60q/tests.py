"""Synthetic contracts; never load experiment images or annotation files."""
import copy,inspect,json,unittest
import cv2,numpy as np
from .engine import Engine,select_official
from .features import raw_valleys,opening_projection,prepare
from .config import CONFIG

P=np.array([[55.,65.],[55.,155.]])
def scene(end=200,width=1,branch=False,gap=None):
    a=np.full((220,420),180,np.uint8)
    if end:
        cv2.line(a,(55,110),(end,110),45,width)
        if branch:cv2.line(a,(100,110),(end+45,135),45,width)
        if gap:a[105:116,gap[0]:gap[1]]=180
    return a

class Contracts(unittest.TestCase):
    def test_raw_one_two_pixels(self):
        for w in [1,2]:
            a=scene(width=w);v=raw_valleys(a,CONFIG)
            self.assertGreater(v[0][110,100],100);self.assertTrue(v[-1][108:113,90:180].any())
    def test_current_tip_and_retreat(self):
        e=Engine();fixed=scene(None)
        for end in [180,300,140]:
            r,_=e.process(scene(end),P,fixed,P)
            self.assertEqual(r['status'],'VALID',str(r['candidates'])[:1000]);self.assertLess(np.linalg.norm(np.array(r['tip'])-[end,110]),4)
            if end==300:self.assertTrue(any(x['passed'] for x in r['rechecks']))
        r,_=e.process(scene(None),P,fixed,P);self.assertIsNone(r['tip']);self.assertTrue(any(t['state']=='LOST' for t in r['tracks']))
        r,_=e.process(scene(145),P,fixed,P);self.assertEqual(r['status'],'VALID');self.assertTrue(any(t['transition']=='REACQUIRING' for t in r['track_transitions']))
    def test_branch_rightmost(self):
        r,_=Engine().process(scene(branch=True),P,scene(None),P)
        self.assertEqual(r['status'],'VALID');self.assertGreaterEqual(r['tip'][0],242)
    def test_noise_not_tip(self):
        a=scene();a[110,350]=0
        r,_=Engine().process(a,P,scene(None),P);self.assertEqual(r['status'],'VALID');self.assertLess(r['tip'][0],205)
    def test_swap_and_determinism(self):
        a=Engine().process(scene(),P,scene(None),P)[0];b=Engine().process(scene(),P[::-1],scene(None),P[::-1])[0]
        self.assertEqual(a,b);self.assertEqual(a,Engine().process(scene(),P,scene(None),P)[0])
    def test_missing_prev_weak_fixed(self):
        r,_=Engine().process(scene(),P,scene(),P)
        self.assertEqual(r['status'],'VALID');self.assertEqual(r['channels']['prev'],'UNAVAILABLE')
    def test_independent_reference_masks(self):
        rng=np.random.default_rng(6013);a=rng.integers(130,210,(220,420),dtype=np.uint8)
        q=prepare(a,P,np.full_like(a,180),P,a.copy(),P,config=CONFIG)
        self.assertFalse(q['fixed']['valid'].any());self.assertTrue(q['prev']['valid'].any())
        self.assertTrue(np.all(q['prev']['signed'][q['prev']['valid']]==0))
        q=prepare(a,P,a.copy(),P,None,None,config=CONFIG)
        self.assertTrue(q['fixed']['valid'].any());self.assertFalse(q['prev']['valid'].any());self.assertTrue(np.isnan(q['prev']['signed']).all())
    def test_long_lost_reinitialization(self):
        e=Engine();e.process(scene(),P,scene(None),P)
        for _ in range(CONFIG['track_lost_ttl']+2):
            r,_=e.process(scene(None),P,scene(None),P);self.assertIsNone(r['tip'])
        self.assertEqual(e.state['tracks'],[])
        r,_=e.process(scene(300),P,scene(None),P);self.assertEqual(r['status'],'VALID')
    def test_very_dark_disconnected_scratch(self):
        a=scene();cv2.line(a,(310,140),(380,140),0,1)
        r,_=Engine().process(a,P,scene(None),P);self.assertEqual(r['status'],'VALID');self.assertLess(r['tip'][0],205)
    def test_degraded_points_and_size(self):
        r,_=Engine().process(scene(),None,scene(None),P);self.assertIn('P1P2_DEGRADED',r['flags'])
        r,_=Engine().process(np.zeros((4,4),np.uint8),P,scene(None),P);self.assertEqual(r['status'],'PROCESSING_ERROR');self.assertIsNone(r['tip'])
    def test_budget(self):
        c=copy.deepcopy(CONFIG);c['max_roi_pixels']=10
        r,_=Engine(c).process(scene(),P,scene(None),P);self.assertIsNone(r['tip']);self.assertEqual(r['status'],'BUDGET_EXHAUSTED')
    def test_gap_observed_end(self):
        for gap in [(130,133),(130,165)]:
            r,_=Engine().process(scene(gap=gap),P,scene(None),P)
            self.assertTrue(r['tip'] is None or scene(gap=gap)[r['tip'][1],r['tip'][0]]==45)
            for p in r['candidates']:self.assertEqual(p['tip_observation'],'CURRENT_OBSERVED')
    def test_tie_is_uncertain(self):
        ps=[dict(id=i,verified=True,endpoint=[200,100+i*20],evidence=dict(origin_support=.8,raw_depth=30)) for i in range(2)]
        self.assertEqual(select_official(ps),(None,'IDENTITY_UNCERTAIN'))
    def test_opening_fixed_axis(self):
        q=P.copy();q[1]+=[20,3]
        self.assertEqual(opening_projection(q,P,(220,420)),3)
    def test_no_metadata_interface(self):
        self.assertEqual(list(inspect.signature(Engine.process).parameters),['self','current','current_points','fixed','fixed_points','previous','previous_points'])
        with self.assertRaises(TypeError):Engine().process(scene(),P,scene(None),P,gt=[100,110])
        with self.assertRaises(ValueError):Engine({**CONFIG,'specimen':'x'})

if __name__=='__main__':unittest.main(verbosity=2)
