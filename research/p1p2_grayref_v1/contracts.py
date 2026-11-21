from native import *
from python_replay import load,execute,argv
import cv2
def main():
 m=load();n=Native();folder=OUT/'tests/contracts';folder.mkdir(parents=True,exist_ok=True);reference=np.full((128,192),185,np.uint8);pp=[[30.,35.],[30.,90.]];checks=[]
 cases=[('blank_provided',reference,pp),('reversed_points',reference,list(reversed(pp))),('degenerate_points',reference,[pp[0],pp[0]]),('nonfinite_points',reference,[[float('nan'),35],pp[1]]),('image_size_mismatch',reference[:-1],pp),('point_outside_image',reference,[[190,35],[190,90]])]
 for name,cur,cp in cases:
  sub=folder/name;sub.mkdir(exist_ok=True);rpath=sub/'ref.bmp';cpath=sub/'cur.bmp';cv2.imwrite(str(rpath),reference);cv2.imwrite(str(cpath),cur);row={f'p{k}_{kind}_{axis}':p[i] for kind,pts in [('ref',pp),('cur',cp)] for k,p in enumerate(pts,1) for i,axis in enumerate(['x','y'])};metric=execute(m,argv(row,rpath,cpath,sub),sub);h=n.create(reference,pp);t=n.process(h,cur,cp);n.close(h);write(sub/'cpp_result.json',t)
  bothok=metric['status']=='OK' and t['status']=='OK';bothfail=metric['status']!='OK' and t['status']!='OK';pass_=bothok and all(x['tip'] is None for x in t['traces']) if name=='blank_provided' else bothfail;checks.append(dict(test=name,passed=bool(pass_),python_status=metric['status'],cpp_status=t['status'],python_error=metric['error'],cpp_error=t['error']))
 save(OUT/'tests/contract_matrix.csv',checks);assert all(x['passed'] for x in checks);print(checks,flush=True)
if __name__=='__main__':main()
