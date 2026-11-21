"""Five shared C-search evidence panels per frame; no label access."""
import argparse,concurrent.futures,io,math,time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from .common import *
from .geometry import MODES
plt.rcParams.update({'font.size':8,'figure.dpi':85,'savefig.dpi':85})
PNGS=['roi_overlay_abc.png','gray_surface_search.png','gray_2d_profiles.png','roi_difference_signed.png','roi_difference_panel.png']

def save(fig,path):
    if not path.exists():
        b=io.BytesIO();fig.savefig(b,format='png',facecolor='white',metadata={'Software':'Frozen ROI geometry r01'});write_bytes(path,b.getvalue())
    plt.close(fig)

def heat(ax,values,g,title,cmap='gray',lo=0,hi=255):
    im=ax.imshow(values,cmap=cmap,vmin=lo,vmax=hi,extent=[g['xa'],g['xb'],g['yb'],g['ya']],aspect='auto',interpolation='nearest');ax.set(title=title,xlabel='Original x [px]',ylabel='Original y [px]');return im

def edges(mask):
    import cv2
    return mask&~cv2.erode(mask.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)

def job(args):
    run,row=args;d=directory(run,row)
    if (d/'visual_manifest.json').exists():
        for k,h in get(d/'visual_manifest.json')['files'].items():assert sha(d/k)==h
        return dict(group=row['group'],frame_id=row['frame_id'],resumed=True)
    t=time.perf_counter();r=readgz(d/'result.json.gz');g=r['roi'];a,_,_=cached(row,False);raw=a['gray'][0];diff=a['diff'];title=row['group']+' / '+row['frame_id'];cp=json.loads(row['current_points'])
    with np.load(d/'evidence_arrays.npz') as q:ms=[q[n] for n in MODES];branches=q['corridor_branches']
    mask=ms[2];coords=[g['xa'],g['xb'],g['yb'],g['ya']];colors=['cyan','gold','magenta']
    fig=plt.figure(figsize=(15,9));grid=fig.add_gridspec(3,3);ax=fig.add_subplot(grid[:,0]);C=imread(row['current']);ax.imshow(C,cmap='gray',vmin=0,vmax=255);ax.scatter(*np.asarray(cp).T,c=['red','blue'],s=20);ax.plot(*np.asarray(cp).T,color='orange');ax.set_title(title+' | P1 red / P2 blue\nFull current image; GT-free')
    for i,(m,pred) in enumerate(zip(ms,r['results'])):
        ey,ex=np.where(edges(m));take=max(1,len(ex)//6000);ax.scatter(ex[::take]+g['xa'],ey[::take]+g['ya'],s=.2,c=colors[i])
        bx=fig.add_subplot(grid[i,1:]);heat(bx,raw,g,MODES[i]+' | '+pred['output_state'])
        display=np.zeros((*m.shape,4));display[edges(m)]=matplotlib.colors.to_rgba(colors[i]);bx.imshow(display,extent=coords,aspect='auto',interpolation='nearest')
        for j,path in enumerate(pred['paths']):
            pts=np.asarray(path['selected_trace']);bx.plot(pts[:,0],pts[:,1],color='lime' if j==0 else 'deepskyblue',lw=.7,alpha=1 if j==0 else .4)
            gap=pts[:,2]==0
            if gap.any():bx.scatter(pts[gap,0],pts[gap,1],c='orange',s=3)
        if pred['candidate_tip']:bx.scatter(*pred['candidate_tip'],c='red',s=12,marker='x')
    fig.suptitle('Only search geometry changes | A cyan / B yellow / C magenta | green observed, orange inferred | tip may be withheld');fig.tight_layout();save(fig,d/PNGS[0])
    sy=max(1,math.ceil(raw.shape[0]/55));sx=max(1,math.ceil(raw.shape[1]/100));ys=np.arange(0,raw.shape[0],sy);xs=np.arange(0,raw.shape[1],sx);X,Y=np.meshgrid(xs+g['xa'],ys+g['ya']);Z=raw[np.ix_(ys,xs)].astype(float);Z[~mask[np.ix_(ys,xs)]]=np.nan
    fig=plt.figure(figsize=(10,5));ax=fig.add_subplot(111,projection='3d');ax.plot_surface(X,Y,Z,cmap='gray',vmin=0,vmax=255,rcount=len(ys),ccount=len(xs),linewidth=0,antialiased=False);ax.set(xlabel='Original x [px]',ylabel='Original y [px]',zlabel='Actual gray',zlim=(0,255),title=title+' | C search only; outside mask omitted');ax.view_init(35,-65);ax.set_ylim(g['yb'],g['ya']);ax.set_box_aspect((2,1,.6));save(fig,d/PNGS[1])
    fig,ax=plt.subplots(3,1,figsize=(13,8));heat(ax[0],np.ma.masked_where(~mask,raw),g,title+' | RAW C mask (full numeric cache retained)');im=heat(ax[1],np.ma.masked_where(~mask,a['valley'][0]),g,'Frozen raw valley depth; C mask','magma',0,80);fig.colorbar(im,ax=ax[1],label='gray-level depth')
    for f in [.1,.3,.5,.7,.9]:
        x=round((raw.shape[1]-1)*f);ax[2].plot(np.arange(raw.shape[0])+g['ya'],raw[:,x],lw=.6,label=f'x={x+g["xa"]}');inside=mask[:,x];ax[2].scatter(np.flatnonzero(inside)+g['ya'],raw[inside,x],s=1)
    ax[2].set(xlabel='Original y [px]',ylabel='Raw gray 0..255',ylim=(0,255),title='Full-resolution vertical profiles at predeclared x fractions; points = C search');ax[2].legend(ncol=5);fig.tight_layout();save(fig,d/PNGS[2])
    cmap=plt.get_cmap('RdBu_r').copy();cmap.set_bad('#55aa55');fig,ax=plt.subplots(figsize=(13,5));im=heat(ax,np.ma.masked_where(~mask|~diff['valid_warp_mask'],diff['signed_raw']),g,title+' | '+r['reference_status']+'\nR aligned - current; + darker / - brighter; green = outside C or invalid','RdBu_r',-40,40);im.set_cmap(cmap);fig.colorbar(im,ax=ax,label='Reference-current [gray level]');fig.tight_layout();save(fig,d/PNGS[3])
    fig,axes=plt.subplots(2,3,figsize=(14,7));panels=[(diff['aligned_reference'],'P-aligned reference','gray',0,255),(raw,'Current RAW','gray',0,255),(diff['signed_raw'],'Signed raw (C masked)','RdBu_r',-40,40),(diff['positive'],'Positive raw','magma',0,40),(diff['ref_quality_map'],'Texture proxy; BOTH sides required','viridis',0,1),(diff['valid_warp_mask'],'Warp valid; C mask contour','gray',0,1)]
    for ax,(v,ttl,cm,lo,hi) in zip(axes.ravel(),panels):
        arr=np.ma.masked_where(~mask,v) if ttl!='Warp valid; C mask contour' else v;im=heat(ax,arr,g,ttl,cm,lo,hi);fig.colorbar(im,ax=ax,shrink=.8)
    fig.suptitle(title+' | '+r['reference_status']+' | Same frozen full-safe registration / no physical certification');fig.tight_layout();save(fig,d/PNGS[4])
    put(d/'render_metadata.json',dict(surface_stride_x=sx,surface_stride_y=sy,regular_display_only=True,full_resolution_preserved=True,masked_nonsearch_pixels=True,gray_z_range=[0,255],signed_range=[-40,40],render_ms=(time.perf_counter()-t)*1000))
    body='<meta charset="utf-8"><style>body{font:16px sans-serif;background:#142330;color:white}img{max-width:100%}a{color:cyan}</style><a href="../../../galleries/'+row['group']+'.html">Group index</a><h1>'+title+' | GT-FREE ROI-only experiment</h1>'
    for name in PNGS:body+='<h2>'+name+'</h2><img loading="lazy" src="'+name+'">'
    body+='<p><a href="evidence_arrays.npz">Masks, branch lanes, nodes, edges and lineage</a> | <a href="roi_metadata.json">Source numeric-cache SHA and coordinates</a></p>'
    write_bytes(d/'index.html',body.encode());put(d/'visual_manifest.json',dict(files={n:sha(d/n) for n in PNGS+['index.html','render_metadata.json']},GT_free=True));return dict(group=row['group'],frame_id=row['frame_id'],seconds=time.perf_counter()-t)

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--workers',type=int,default=12);a=p.parse_args();run=Path(a.run);check_sources(run);assert (run/'evaluation_complete_exposed.json').exists();data=manifest(run/'input_manifest.csv')
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:
        for i,r in enumerate(pool.map(job,[(str(run),row) for row in data]),1):
            if i%50==0 or i==len(data):print('RENDER '+str(i)+'/1633',flush=True)

if __name__=='__main__':main()
