"""Test dataset isolation and original-coordinate coverage, without real labels."""
import numpy as np
from validate_annotations import *
from crackv4.dataset_policy import allowed

def main():
 for g in policy()['groups']:
  for purpose in ['model_training','parameter_fitting','automatic_threshold_search','development']:
   assert not allowed(g,purpose,uses_annotations=True)
 for g in ['group_c','three_point_bend']:
  assert not allowed(g,'development') and allowed(g,'validation') and allowed(g,'comparison',uses_annotations=True)
 for purpose in ['development','validation','comparison','annotation_qc','model_training']:
  assert not allowed('group_x',purpose) and not allowed('group_x',purpose,uses_annotations=True)
 data=[dict(dataset_id=g) for g in policy()['groups']];assert len(active_rows(data))==6
 # Outside-ROI GT must remain in total arc length, never disappear from denominator.
 shapes=[dict(label='crack_path',points=[[-10,5],[20,5]],shape_type='linestrip')];points,weights=sample_paths(shapes)
 assert abs(weights.sum()-30)<1e-12;mask=np.ones((10,10),bool);roi=np.array([0,0,10,10]);scale=np.array([1.,1.]);fraction_inside=fraction(weights,sample_mask(points,mask,roi,scale));assert abs(fraction_inside-1/3)<.02
 assert fraction(weights,sample_mask(points,np.zeros_like(mask),roi,scale))==0
 # Tolerances are measured in ORIGINAL pixels even after ROI downsampling.
 shapes=[dict(label='crack_path',points=[[0,5],[9,5]],shape_type='linestrip')];distance=tube_distance(shapes,(5,5),roi,np.array([.5,.5]));assert abs(distance[2,2]-.5)<1e-12 and abs(distance[1,2]-2.5)<1e-12
 # Collinear segment insertion cannot alter analytic tolerance bands.
 subdivided=[dict(label='crack_path',points=[[0,5],[4,5],[9,5]],shape_type='linestrip')];assert np.array_equal(distance,tube_distance(subdivided,(5,5),roi,np.array([.5,.5])))
 assert classify(dict(shapes=[],flags={}))=='INCOMPLETE_OR_AMBIGUOUS'
 assert classify(dict(shapes=[],flags={'no_visible_crack':True}))=='NO_VISIBLE_CRACK'
 assert classify(dict(shapes=[dict(label='uncertain_region')],flags={}))=='UNCERTAIN'
 write(OUT/'validation_contract_tests.json',dict(status='PASS',training_with_annotations='REJECTED_ALL_GROUPS',validation_group_development='REJECTED',group_x_all_new_uses='REJECTED',original_pixel_tolerance='PASS',outside_roi_denominator='PASS',missing_not_negative='PASS',comparison_only=True))
 print('VALIDATION CONTRACTS PASS')
if __name__=='__main__':main()
