from common import *
from candidates import propose
from decision import select,validated_decision
from reference import MaterialCache
import unittest

class Contracts(unittest.TestCase):
    def test_native_identity(self):guard()
    def test_unprunable_A_double(self):
        im=np.full((256,256),210,np.uint8);cv2.line(im,(30,128),(210,128),150,2)
        path=np.column_stack([np.arange(30.,211.),np.full(181,128.)]);tip=[210.00000000000003,128.00000000000003]
        pool,_,_=propose(im,path,tip,True,2)
        self.assertEqual(np.asarray(pool[0]['xy'],np.float64).tobytes(),np.asarray(tip,np.float64).tobytes())
        self.assertLessEqual(len(pool),12)
    def test_no_tip_does_not_become_zero_tip(self):
        pool,_,_=propose(np.full((50,50),210,np.uint8),[],None,False)
        x,_=select(pool,[],None,False)
        self.assertFalse(x['valid']);self.assertIsNone(x['tip'])
    def test_no_reference_not_a_veto(self):
        x,_=select([],[],[19.25,16.75],True)
        self.assertEqual(x['tip'],[19.25,16.75]);self.assertEqual(x['decision'],'A_UNCHANGED')
    def test_degenerate_anchors(self):
        with self.assertRaises(ValueError):anchors([[1,1],[1,1]])
    def test_projection(self):
        o,u,d=anchors([[10,0],[10,20]])
        self.assertEqual(float((np.array([40,12])-o)@u),30.)
    def test_saturated_unknown(self):
        im=np.full((256,256),255,np.uint8);c=MaterialCache(im,[[40,70],[40,180]])
        self.assertEqual(len(c.features),0)
        r=c.match(im,np.array([[1.,0,0],[0,1.,0]]),[[50,120],[150,120]])
        self.assertFalse(r['local_supported'])
    def test_crossing_is_not_stop(self):
        pool=[dict(candidate_id=0,A_original_bitwise=False,s=24.,xy=[24,0],origin='SUSTAINED_SUPPORT_CHANGE')]
        ev=[dict(arc_s=float(i),O=True,Vcur=20.,Vref=15. if 30<i<45 else 0.,DeltaV=5. if 30<i<45 else 20.,Q=20.) for i in range(0,100,4)]
        _,a=select(pool,ev,[100,0],True)
        self.assertFalse(a[0]['H_STOP_pattern']);self.assertTrue(a[0]['H_CONTINUE_supported'])

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
    save(RUN/'01_protocol_and_freeze/contract_tests.json',dict(tests=result.testsRun,passed=result.wasSuccessful(),failures=len(result.failures),errors=len(result.errors)))
    sys.exit(0 if result.wasSuccessful() else 1)
