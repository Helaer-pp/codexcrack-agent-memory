"""Synthetic QC fixtures stay outside the user's annotation package."""
from PIL import Image
from common import *
from annotation_qc import validate
def main():
 folder=OUT/'synthetic_annotation_qc';folder.mkdir(exist_ok=False);manifest=[]
 for i in range(20):
  p=folder/f'synthetic_{i}.png';j=p.with_suffix('.json');Image.new('L',(32,24),i*10).save(p)
  write(j,dict(version='5.2.1',flags={},shapes=[],imagePath=p.name,imageData=None,imageHeight=24,imageWidth=32))
  manifest.append(dict(dataset_id='SYNTHETIC_QC_ONLY',frame_id=i+1,split='development' if i<15 else 'holdout',selected_image=p.name,selected_json=j.name,source_sha256=sha(p),image_width=32,image_height=24))
 save(folder/'selection_manifest.csv',manifest);assert all(r['annotation_status']=='UNANNOTATED' for r in validate(folder,True))
 j=folder/'synthetic_0.json';d=json.loads(j.read_text());d['flags']={'no_visible_crack':True};write(j,d);assert validate(folder)[0]['annotation_status']=='NO_VISIBLE_CRACK'
 d['flags']={};d['shapes']=[dict(label='uncertain_region',shape_type='polygon',points=[[1,1],[9,1],[9,9]],flags={},group_id=None)];write(j,d);assert validate(folder)[0]['annotation_status']=='UNCERTAIN'
 d['shapes']=[dict(label='crack_tip',shape_type='point',points=[[9,9]],flags={},group_id=None)];d['flags']={'no_visible_crack':True};write(j,d)
 try:validate(folder)
 except AssertionError:pass
 else:raise AssertionError('negative/tip conflict accepted')
 d['flags']={};d['shapes'][0]['points']=[[99,9]];write(j,d)
 try:validate(folder)
 except AssertionError:pass
 else:raise AssertionError('out-of-image tip accepted')
 (folder/'README.txt').write_text('SYNTHETIC SOFTWARE TEST FIXTURES ONLY. Not user images or human ground truth.',encoding='utf8')
 write(OUT/'annotation_import_tests.json',dict(T07='PASS',unannotated_vs_negative_vs_uncertain='DISTINCT',negative_tip_conflict='REJECTED',out_of_image_coordinate='REJECTED',human_package_modified=False))
 print('ANNOTATION IMPORT TESTS PASS')
if __name__=='__main__':main()
