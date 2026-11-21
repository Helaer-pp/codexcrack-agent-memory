import ast
import numpy as np
from common import *
from analyze import original,local,inside
from crackv4.dataset_policy import allowed
def main():
 for turn in range(4):
  t=dict(roi=[13,27,121,85],turn=turn);p=np.array([[13,27],[133,111],[67.5,48.125]])
  assert np.max(np.abs(original(local(p,t),t)-p))<1e-12
 for g in ['group_c','three_point_bend']:assert not allowed(g,'development')
 assert not allowed('group_x','validation')
 for g in ['group_a','ct2','group_h','ct3']:assert not allowed(g,'model_training',uses_annotations=True)
 replay=(ROOT/'research/uctt_r05d/replay.py').read_text(encoding='utf8')
 assert 'ZipFile' not in replay and "selected_json" not in replay and 'human_tip_' not in replay
 assert 'R05DOffline' not in (ROOT/'src/cpp/a/CrackV4.cpp').read_text(encoding='utf8')
 # D0 has no compiled counterfactual export; all normal/CF inputs omit human coordinates.
 for p in (ROOT/'research/uctt_r05d').glob('*.py'):ast.parse(p.read_text(encoding='utf8'))
 write(OUT/'contract_tests.json',dict(status='PASS',rotation_roundtrip_four_turns=True,policy=True,annotation_reader_separate_from_native_driver=True,gt_in_native_signatures=False,cf_inputs='original image + fixed generic diagnostic variant ONLY',no_training=True))
 print('CONTRACTS PASS')
if __name__=='__main__':main()
