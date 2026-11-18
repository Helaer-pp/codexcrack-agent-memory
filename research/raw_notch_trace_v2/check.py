import cv2
import numpy as np
from detector import prepare,predict


def test(line=True, detached=False):
    image=np.full((140,300),175,np.uint8)
    cv2.fillPoly(image,[np.array([[0,56],[64,67],[69,70],[64,73],[0,85]])],18)
    if line:
        start=(88,70) if detached else (65,70)
        cv2.line(image,start,(137,78),95,1)
    prep=prepare(image,[67,70],150)
    assert prep is not None
    out=predict(prep,np.zeros_like(prep[3]))
    print(line,detached,out['root'],out['status'],out['tip'])
    if line and not detached:assert out['tip'] and np.linalg.norm(np.array(out['tip'])-[137,78])<=3
    else:assert out['tip'] is None


if __name__=='__main__':
    test();test(False);test(True,True)

