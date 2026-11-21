from common import *

def engine(ref, pp, mode='auto', shadow=False, flags=3572):
    if not shadow:
        return api.Baseline(ref, pp, mode=mode, flags=flags)
    old=(api.BASE,api.EXPECTED_BASE,api._base)
    try:
        api.BASE=ROOT/'output/build/Release/CrackV4AP2Shadow.dll'
        api.EXPECTED_BASE=sha(api.BASE);api._base=None
        obj=api.Baseline(ref,pp,mode=mode,flags=flags)
        obj.lib.AP2CopyStops.argtypes=[api.C.c_void_p,api.C.POINTER(api.C.c_double),api.C.c_int]
        obj.lib.AP2CopyStops.restype=api.C.c_int
        return obj
    finally:
        api.BASE,api.EXPECTED_BASE,api._base=old

def stops(obj):
    n=obj.lib.AP2CopyStops(obj.handle,None,0)
    a=np.empty((n,11),np.float64)
    rc=obj.lib.AP2CopyStops(obj.handle,a.ctypes.data_as(api.C.POINTER(api.C.c_double)),n)
    return a,rc<0

if __name__=='__main__':
    guard();mm=rows(ROOT/'data/inputs/six_groups_manifest.csv');eq=[]
    fn=RUN/'03_A_candidate_audit/native_tile_observer.jsonl'
    with fn.open('w',encoding='utf8') as out:
        for g in dict.fromkeys(x['dataset_alias'] for x in mm):
            rr=[x for x in mm if x['dataset_alias']==g]
            cr,cj,cp=native(ROOT/f'data/frozen_a_replay/{g}_A')
            ref=read(rr[0]['input_image']);rp=json.loads(rr[0]['points'])
            a=engine(ref,rp,rr[0]['mode']);b=engine(ref,rp,rr[0]['mode'],True)
            for i,m in enumerate(rr):
                im=ref if i==0 else read(m['input_image']);pp=json.loads(m['points'])
                x=a.run(im,pp,i==0);y=b.run(im,pp,i==0);z,over=stops(b)
                exact=api.normalized(x['native'])==api.normalized(y['native'])==api.normalized(cj[i])
                xp=np.asarray(x['formal']['raw_path'],dtype='<f8').reshape(-1,2)
                yp=np.asarray(y['formal']['raw_path'],dtype='<f8').reshape(-1,2)
                exact=exact and xp.tobytes()==yp.tobytes()==cp[i].astype('<f8').tobytes()
                assert exact,(g,i,'GATE0_MISMATCH')
                row=dict(group=g,frame_id=i,exact_state_tip_arc_float64_path=exact,
                         A_process_ms=x['formal']['process_ms'],shadow_process_ms=y['formal']['process_ms'],
                         tile_records=len(z),overflow=over)
                eq.append(row);dump_line(out,dict(**row,tiles=z,A=y,observer_encoding='INVALID_FRACTION_0_1'))
                if i%100==0:print('GATE0',g,i,flush=True)
            a.close();b.close()
            csvout(RUN/'03_A_candidate_audit/Gate0_per_frame.csv',eq)
    guard();save(RUN/'03_A_candidate_audit/Gate0.json',dict(pass_gate0=True,frames=len(eq),differences=0,utc=utc()))
    print('GATE0 PASSED',len(eq),flush=True)
