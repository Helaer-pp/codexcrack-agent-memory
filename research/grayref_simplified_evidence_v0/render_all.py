"""Offline renderer. Predictions and full-resolution arrays are the sole sources; no GT."""
import io,json,math,html
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw,ImageFont
from .algorithm import CONFIG,MODES,FILTERS
from .common import put,get,readgz,write_bytes,frame_dir,sha
plt.rcParams.update({'font.size':8,'axes.titlesize':9,'figure.dpi':90,'savefig.dpi':90,'axes.unicode_minus':False})

def savefig(fig,path):
    if not Path(path).exists():
        b=io.BytesIO();fig.savefig(b,format='png',facecolor='white',metadata={'Software':'GrayRef simplified evidence v0'});write_bytes(path,b.getvalue())
    plt.close(fig)
def png_array(path,array):
    if Path(path).exists():return
    b=io.BytesIO();Image.fromarray(array).save(b,format='PNG');write_bytes(path,b.getvalue())
def surface_grid(raw,g,c=CONFIG):
    sy=max(1,math.ceil(raw.shape[0]/c['surface_rows']));sx=max(1,math.ceil(raw.shape[1]/c['surface_cols']))
    ys=np.arange(0,raw.shape[0],sy);xs=np.arange(0,raw.shape[1],sx)
    X,Y=np.meshgrid(xs+g['xa'],ys+g['ya'])
    return X,Y,raw[np.ix_(ys,xs)],sx,sy
def surface(fig,slot,raw,g,title):
    X,Y,Z,sx,sy=surface_grid(raw,g);ax=fig.add_subplot(slot,projection='3d')
    ax.plot_surface(X,Y,Z,cmap='gray',vmin=0,vmax=255,rcount=Z.shape[0],ccount=Z.shape[1],linewidth=0,antialiased=False)
    ax.set(xlabel='Original x [px]',ylabel='Original y [px]',zlabel='Gray level',zlim=(0,255),title=title)
    ax.view_init(elev=35,azim=-65);ax.set_ylim(g['yb'],g['ya']);ax.set_box_aspect((2,1,.6))
    return sx,sy
def heat(ax,A,g,title,cmap='gray',vmin=0,vmax=255):
    im=ax.imshow(A,cmap=cmap,vmin=vmin,vmax=vmax,extent=[g['xa'],g['xb'],g['yb'],g['ya']],aspect='auto',interpolation='nearest')
    ax.set(title=title,xlabel='Original x [px]',ylabel='Original y [px]');return im

def render_frame(directory):
    d=Path(directory);r=readgz(d/'result.json.gz');g=r['roi'];ident=r['identity'];title=f"{ident['group']} / {ident['frame_id']}"
    with np.load(d/'roi_gray.npz') as z:gray={k:z[k] for k in z.files}
    with np.load(d/'roi_difference.npz') as z:diff={k:z[k] for k in z.files}
    raw=gray['raw'];sx=sy=1
    if not (d/'gray_surface_raw.png').exists():
        fig=plt.figure(figsize=(10,5));sx,sy=surface(fig,111,raw,g,title+' | RAW actual gray');savefig(fig,d/'gray_surface_raw.png')
    else:_,_,_,sx,sy=surface_grid(raw,g)
    if not(d/'gray_surface_filtered.png').exists():
        fig=plt.figure(figsize=(14,5));surface(fig,121,gray['median3'],g,title+' | FILTERED MEDIAN3');surface(fig,122,gray['gaussian_light'],g,title+' | FILTERED GAUSSIAN sigma=0.6');savefig(fig,d/'gray_surface_filtered.png')
    png_array(d/'gray_full_resolution.png',raw)
    for name in ['valley_raw','valley_median3','valley_gaussian_light']:
        # PNG fixed 0..80 display, NPZ unmodified full float responses.
        png_array(d/(name+'_full_resolution.png'),np.uint8(np.clip(gray[name]/80,0,1)*255))
    if not(d/'gray_2d_and_profiles.png').exists():
        fig=plt.figure(figsize=(12,9));gs=fig.add_gridspec(4,2)
        a=fig.add_subplot(gs[0,:]);heat(a,raw,g,title+' | RAW current ROI')
        a=fig.add_subplot(gs[1,:]);im=heat(a,gray['valley_raw'],g,'Current valley response (not raw gray Z)','magma',0,80);fig.colorbar(im,ax=a,label='Gray-level valley depth')
        profiles=[]
        for k,f in enumerate([.1,.3,.5,.7,.9]):
            x=min(raw.shape[1]-1,round(f*(raw.shape[1]-1)));y=np.arange(raw.shape[0])+g['ya']
            profiles.append((x,y))
        ax=fig.add_subplot(gs[2:,:])
        for x,y in profiles:
            v=raw[:,x].astype(float);peaks=(v<=np.roll(v,1))&(v<np.roll(v,-1))&(gray['valley_raw'][:,x]>=r['threshold'])
            ax.plot(y,v,lw=.65,label=f"x={x+g['xa']} px");ax.scatter(y[peaks],v[peaks],s=4)
        ax.set(xlabel='Original y [px]; full-resolution profiles, markers=automatic valleys',ylabel='Gray level',ylim=(0,255));ax.legend(ncol=5);fig.tight_layout();savefig(fig,d/'gray_2d_and_profiles.png')
    cmap=plt.get_cmap('RdBu_r').copy();cmap.set_bad('#44bb44');K=CONFIG['display_diff']
    if not(d/'roi_difference_signed.png').exists():
        fig,ax=plt.subplots(figsize=(12,5));im=heat(ax,diff['signed_raw'],g,title+' | '+r['reference_status']+'\nRAW P-warp: + current darker / - current brighter; green=invalid',cmap,-K,K);fig.colorbar(im,ax=ax,label='Reference - current [gray level]');fig.tight_layout();savefig(fig,d/'roi_difference_signed.png')
    if not(d/'roi_difference_panel.png').exists():
        fig,axes=plt.subplots(3,3,figsize=(15,9));panels=[('aligned_reference','P-only aligned reference','gray',0,255),('CURRENT','Current RAW','gray',0,255),('signed_raw','P-only signed raw',cmap,-K,K),('positive','Positive raw','magma',0,K),('absolute','Absolute raw','magma',0,K),('ref_quality_map','Local texture confidence proxy','viridis',0,1),('valid_warp_mask','Valid P warp (white=valid)','gray',0,1),('signed_corrected','Local + illumination corrected',cmap,-K,K),('valid_material_mask','Material measurable (white)','gray',0,1)]
        for ax,(key,label,cm,lo,hi) in zip(axes.flat,panels):
            im=heat(ax,raw if key=='CURRENT' else diff[key],g,label,cm,lo,hi);fig.colorbar(im,ax=ax,shrink=.7)
        fig.suptitle(title+' | '+r['reference_status']+' | physical registration NOT certified');fig.tight_layout();savefig(fig,d/'roi_difference_panel.png')
    # Unaligned reference ROI is separately identified, never mistaken for P-aligned evidence.
    png_array(d/'reference_unaligned_roi.png',gray['reference_unaligned'])
    for result in r['results']:
        name='overlay_path_tip.png' if result['mode']=='C_FUSION_RAW' else 'overlay_'+result['mode']+'.png'
        if (d/name).exists():continue
        im=Image.fromarray(raw).convert('RGB');draw=ImageDraw.Draw(im)
        for idx,p in reversed(list(enumerate(result['paths']))):
            t=p['selected_trace'];color=(0,255,80) if idx==0 else (80,155,255)
            for a,b in zip(t,t[1:]):
                xy=[a[0]-g['xa'],a[1]-g['ya'],b[0]-g['xa'],b[1]-g['ya']]
                draw.line(xy,fill=color if a[2] and b[2] else (255,165,0),width=2 if idx==0 else 1)
        if result['candidate_tip']:
            x,y=result['candidate_tip'];x-=g['xa'];y-=g['ya'];draw.ellipse([x-5,y-5,x+5,y+5],outline=(255,0,255),width=2)
        canvas=Image.new('RGB',(max(1100,im.width),im.height+70),'#111923');canvas.paste(im,(0,70));txt=ImageDraw.Draw(canvas)
        txt.text((8,6),title+'  '+result['mode']+'  '+result['output_state'],fill='white')
        txt.text((8,24),'GREEN observed chosen | BLUE other candidates | ORANGE inferred gap | MAGENTA candidate tip (may be uncertain)',fill='white')
        txt.text((8,42),f"Original coordinates: x={g['xa']}..{g['xb']}, y={g['ya']}..{g['yb']} px. GT-FREE; provisional identity.",fill='white')
        b=io.BytesIO();canvas.save(b,format='PNG');write_bytes(d/name,b.getvalue())
    put(d/'render_metadata.json',dict(z='actual current gray level',z_range=[0,255],surface_stride_x=sx,surface_stride_y=sy,sampling='regular original-pixel grid; display only',risk='1px lines may lie between 3D samples; use full-resolution PNG/NPZ and full y profiles',elev=35,azim=-65,cmap='gray',difference_range=[-K,K],difference_cmap='RdBu_r; green invalid',profile_fractions=[.1,.3,.5,.7,.9],roi=g))
    modes=json.dumps({m:('overlay_path_tip.png' if m=='C_FUSION_RAW' else 'overlay_'+m+'.png') for m in MODES})
    content=f'''<!doctype html><meta charset="utf-8"><title>{title}</title><style>body{{font:16px sans-serif;background:#10202c;color:#eee;margin:24px}}a{{color:#7ed6ff}}img{{max-width:100%;background:white;margin:8px 0}}select{{font-size:18px}}details{{margin:10px}}</style>
<a href="../index.html">Group</a> | <a href="../../index.html">All groups</a><h1>{title} — GT-FREE evidence</h1>
<p>{r['reference_status']} · no physical registration/main-crack certification · x/y original px</p>
<select id="mode">{''.join('<option '+('selected ' if m=='C_FUSION_RAW' else '')+'>'+m+'</option>' for m in MODES)}</select><img id="overlay" src="overlay_path_tip.png">
<h2>Raw gray surface</h2><img loading="lazy" src="gray_surface_raw.png"><p>Regular grid is display-only. Fine lines may disappear between samples.</p>
<h2>Filtered comparison</h2><img loading="lazy" src="gray_surface_filtered.png"><h2>Full-resolution y profiles</h2><img loading="lazy" src="gray_2d_and_profiles.png">
<h2>Signed difference (+ darker current; - brighter current)</h2><img loading="lazy" src="roi_difference_signed.png"><img loading="lazy" src="roi_difference_panel.png">
<details><summary>Full-resolution / numeric / provenance</summary>{''.join('<p><a href="'+f+'">'+f+'</a></p>' for f in ['gray_full_resolution.png','valley_raw_full_resolution.png','valley_median3_full_resolution.png','valley_gaussian_light_full_resolution.png','reference_unaligned_roi.png','roi_gray.npz','roi_difference.npz','candidate_graphs.npz','result.json.gz','roi_difference_metadata.json','render_metadata.json','frame_manifest.json'])}</details>
<script>const files={modes};document.getElementById('mode').onchange=e=>document.getElementById('overlay').src=files[e.target.value];</script>'''
    write_bytes(d/'index.html',content.encode('utf-8'))
    return d
