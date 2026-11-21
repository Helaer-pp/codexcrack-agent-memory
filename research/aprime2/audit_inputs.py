from common import *
from concurrent.futures import ThreadPoolExecutor
mm=rows(ROOT/'data/inputs/six_groups_manifest.csv')
def check(m):
    actual=sha(m['input_image'])
    assert actual==m['input_sha256'],m['input_image']
    return dict(group=m['dataset_alias'],frame_id=int(m['frame_id']),path=m['input_image'],sha256=actual,verified=True)
with ThreadPoolExecutor(max_workers=2) as ex:rr=list(ex.map(check,mm))
csvout(RUN/'01_protocol_and_freeze/input_hashes_verified.csv',rr)
save(RUN/'01_protocol_and_freeze/input_audit.json',dict(images=len(rr),hashes_match=True,utc=utc()))
print('INPUT HASHES',len(rr),flush=True)
