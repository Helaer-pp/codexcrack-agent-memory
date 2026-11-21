"""Image-independent check of the C++ Gaussian arithmetic contract."""
from v2common import *
import math
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.ndimage._filters import _gaussian_kernel1d

def main():
    sigma=.7
    kernel=_gaussian_kernel1d(sigma,0,3)
    expected=['0x1.eaf0abfddfc57p-15','0x1.3b3170a27df78p-7','0x1.a4a892b55c7f0p-3','0x1.23c2d39adde1dp-1','0x1.a4a892b55c7f0p-3','0x1.3b3170a27df78p-7','0x1.eaf0abfddfc57p-15']
    assert [x.hex() for x in kernel]==expected
    old=[math.exp(-.5*i*i/(sigma*sigma)) for i in range(-3,4)]
    total=sum(old);old=[x/total for x in old]
    rng=np.random.default_rng(20261112)
    a=rng.integers(0,256,size=(64,128)).astype(np.float32)
    # Reflect padding is independent of the detector and real specimen data.
    pad=np.pad(a,((0,0),(3,3)),mode='symmetric')
    actual=gaussian_filter1d(a,sigma,axis=1)
    records=[]
    for name,k,order in [('old',old,range(1,4)),('locked_kernel_outer_first',kernel,range(3,0,-1))]:
        calculated=np.empty_like(a)
        for y in range(a.shape[0]):
            for x in range(a.shape[1]):
                acc=float(a[y,x])*float(k[3])
                for j in order:acc+=(float(pad[y,x+3-j])+float(pad[y,x+3+j]))*float(k[3-j])
                calculated[y,x]=acc
        records.append(dict(variant=name,equal=bool(np.array_equal(actual,calculated)),different_pixels=int(np.count_nonzero(actual!=calculated)),max_abs=float(np.abs(actual-calculated).max())))
    assert records[-1]['equal']
    write(OUT/'numeric_kernel_audit.json',dict(sigma=sigma,kernel_hex=expected,old_kernel_hex=[x.hex() for x in old],synthetic_seed=20261112,synthetic_shape=list(a.shape),records=records,real_images_used=False,parameters_changed=False,array_tolerance=1e-5))
    print('KERNEL ARITHMETIC AUDIT',records,flush=True)

if __name__=='__main__':main()
