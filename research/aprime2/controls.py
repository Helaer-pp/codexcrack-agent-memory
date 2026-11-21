from common import *
from dev import material
from reference import MaterialCache,ReferenceCache

def execute():
    rr=[];details=[]
    conditions=['shift_0.5','shift_1','shift_3','shift_5','photo','affine','repeated','occlusion','compression','saturated','existing_line']
    for bg in range(3):
        for rep in range(4):
            rng=np.random.default_rng(991105+100*bg+rep);n=512;ref=np.clip(np.rint(material(n,bg,rng)),0,255).astype(np.uint8)
            rp=np.array([[95,150],[95,350]],float);path=np.column_stack([np.arange(130.,300.),np.full(170,250.)])
            for cond in conditions:
                r=ref.copy();M=np.array([[1.,0.,2.25],[0.,1.,-1.25]])
                if cond=='repeated':
                    yy,xx=np.mgrid[:n,:n];r=np.clip(200+12*np.sin(xx*2*np.pi/8)*np.cos(yy*2*np.pi/8),0,255).astype(np.uint8)
                if cond=='saturated':r[:]=255
                if cond=='existing_line':cv2.line(r,(130,250),(300,250),160,2)
                if cond=='affine':M=np.array([[1.01,.008,-1.],[.004,.99,1.]])
                cur=cv2.warpAffine(r,M,(n,n),borderValue=205)
                if cond=='photo':cur=np.clip(.9*cur.astype(float)+17,0,255).astype(np.uint8)
                if cond=='occlusion':cur[220:285,260:330]=250
                if cond=='compression':cur=cv2.imdecode(cv2.imencode('.jpg',cur,[cv2.IMWRITE_JPEG_QUALITY,60])[1],0)
                guess=M.copy();error=float(cond.split('_')[-1]) if cond.startswith('shift_') else 0.
                guess[:,2]-=[error,0.];cp=apply(M,path)
                for method,cache in [('legacy',ReferenceCache(r,rp)),('fraction',MaterialCache(r,rp,False)),('balanced',MaterialCache(r,rp))]:
                    reg=cache.match(cur,guess,cp);photo=cache.photo(cur,reg)
                    # Audit actual transform over candidate's independent square, not just fitted patch points.
                    target=path[-1]+np.array([[-16,-16],[-16,16],[16,-16],[16,16]])
                    e=np.linalg.norm(apply(reg['M'],target)-apply(M,target),axis=1)
                    row=dict(background=bg,rep=rep,condition=cond,method=method,features=len(cache.features),
                        geometry=reg['local_supported'],joint=reg['local_supported'] and photo['state']=='PHOTO_SUPPORTED',
                        max_GT_geometry_error=float(max(e)),false_accept=reg['local_supported'] and max(e)>1.,
                        holdout_p90=reg['holdout_p90_px'],reason=reg['reason'],photo_reason=photo['reason'],ms=reg['cost_ms']+photo['cost_ms'])
                    rr.append(row);details.append(dict(**row,reg=reg,photo=photo))
    csvout(RUN/'04_reference_validity/known_GT_controls.csv',rr)
    with (RUN/'04_reference_validity/known_GT_controls.jsonl').open('w',encoding='utf8') as f:
        for z in details:dump_line(f,z)
    summary=[]
    for method in ['legacy','fraction','balanced']:
        q=[x for x in rr if x['method']==method];accepted=[x['max_GT_geometry_error'] for x in q if x['geometry']]
        summary.append(dict(method=method,n=len(q),geometry=sum(x['geometry'] for x in q),joint=sum(x['joint'] for x in q),
            false_accept=sum(x['false_accept'] for x in q),accepted_error=api.stats(accepted)))
    save(RUN/'04_reference_validity/known_GT_summary.json',summary);print(summary,flush=True)

if __name__=='__main__':execute()
