"""Folder IO/point-tracking contracts; does not use human labels or tune detection."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('paired_editor',ROOT/'paired_p1p2_roi_easy_edit.py')
app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)

class FolderContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=ROOT/'output/tests';base.mkdir(parents=True,exist_ok=True)
        cls.fixture=Path(tempfile.mkdtemp(prefix='paired_folder_contract_',dir=base))
        folder=cls.fixture/'中文图像';folder.mkdir()
        rng=np.random.default_rng(524)
        image=np.clip(rng.normal(210,10,(360,600)),0,255).astype('uint8')
        image[162:166,90:160]=60
        app.cv2.imencode('.png',image)[1].tofile(cls.fixture/'参考.png')
        for name,dx,dy,end in [('1.png',0,0,160),('2.png',2,1,300),('10.png',4,2,330)]:
            current=image.copy();current[162:166,106:end]=60
            current=app.cv2.warpAffine(current,np.float32([[1,0,dx],[0,1,dy]]),(600,360),borderMode=app.cv2.BORDER_REFLECT_101)
            app.cv2.imencode('.png',current)[1].tofile(folder/name)
        (folder/'3.bmp').write_bytes(b'bad image for failure continuation check')
        (folder/'说明.txt').write_text('not an image',encoding='utf-8')
        cls.out=app.main(['--reference',str(cls.fixture/'参考.png'),'--image-folder',str(folder),
                         '--p1-ref','100,90','--p2-ref','100,240','--right-edge','570','--point-search','3',
                         '--output-dir',str(cls.fixture/'runs'),'--no-open'])

    def test_natural_order_and_exclusion_before_image_read(self):
        self.assertEqual([p.name for p in sorted(map(Path,['10.bmp','2.bmp','1.bmp']),key=app.natural_key)],['1.bmp','2.bmp','10.bmp'])
        with self.assertRaises(PermissionError):app.list_images(ROOT/'output/not_present/排除组X')

    def test_textureless_template_rejected(self):
        im=np.full((120,120),200,np.uint8)
        with self.assertRaisesRegex(ValueError,'constant template'):
            app.track_reference_point(im,im,(60,60),8,3,.8)

    def test_sequential_tracking_corruption_and_original_trace_parity(self):
        fixture=self.fixture;out=self.out
        summary=pd.read_csv(out/'batch_summary.csv')
        self.assertEqual(summary.filename.tolist(),['1.png','2.png','3.bmp','10.png'])
        self.assertEqual(summary.status.tolist(),['NO_TIP','NO_TIP','ERROR','NO_TIP'])
        self.assertEqual(summary.loc[1,['p1_x','p1_y']].tolist(),[102.,91.])
        self.assertEqual(summary.loc[3,['p1_x','p1_y']].tolist(),[104.,92.])
        self.assertTrue(str(summary.loc[3,'tracking_source']).endswith('2.png'))
        self.assertEqual(json.loads((out/'run_status.json').read_text())['errors'],1)
        for record in summary.to_dict('records'):
            self.assertTrue((out/record['detail']).is_file())
            if isinstance(record['image'],str):self.assertTrue((out/record['image']).is_file())
        # Reference-only matching cannot follow the final +4 displacement with a +/-3 search.
        ref=app.imread_gray(fixture/'参考.png');cur=app.imread_gray(fixture/'中文图像/10.png')
        with self.assertRaises(ValueError):app.track_reference_point(ref,cur,(100,90),29,3,.8)

    def test_original_trace_parity(self):
        golden=ROOT/'output/tests/paired_folder_20261113_r01/golden'
        if not golden.is_dir():self.skipTest('Pre-edit captured golden traces are not present')
        self.assertEqual(len(list(golden.glob('trace_*.csv'))),6)
        for before in golden.glob('trace_*.csv'):
            pd.testing.assert_frame_equal(pd.read_csv(before),pd.read_csv(self.out/'frames/000002'/before.name),check_exact=True)
        before=pd.read_csv(golden/'summary_results.csv')
        after=pd.read_csv(self.out/'frames/000002/summary_results.csv')
        pd.testing.assert_frame_equal(before.drop(columns='stop_reason'),after.drop(columns='stop_reason'),check_exact=True)
        self.assertEqual(after.loc[after['mode']=='current','stop_reason'].tolist(),['roi_right_boundary']*3)

if __name__=='__main__':unittest.main()
