"""Enforced three-group orchestration; evaluations only in separate sealed subprocesses."""
import argparse,concurrent.futures,collections,json,os,platform,re,shutil,subprocess,sys,time,traceback
import numpy as np
import cv2,psutil
from .common import *
from .geometry import CONFIG,MODES,detect,fusion,frozen
from .lineage import routes

def init():cv2.setNumThreads(1)

def inputs(run,data):
    files={};point_checks=[]
    for r in data:
        for key,hkey in [('current','image_sha'),('reference','ref_sha'),('point_source','point_source_sha')]:files[r[key]]=r[hkey]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        checks=list(pool.map(lambda kv:(kv[0],Path(kv[0]).is_file() and sha(kv[0])==kv[1]),files.items()))
    assert all(ok for _,ok in checks),'Missing/changed original input'
    for group in GROUPS:
        sub=[r for r in data if r['group']==group];mapping={}
        for line in Path(sub[0]['point_source']).read_bytes().decode('gb18030',errors='replace').splitlines():
            nums=re.findall(r'[-+]?\d+(?:\.\d+)?',line)
            if len(nums)==5 and line.lower().lstrip().startswith('num'):
                k=int(nums[0]);v=list(map(float,nums[1:]));assert k not in mapping;mapping[k]=[v[:2],v[2:]]
        for r in sub:
            assert mapping[int(r['tracking_num'])]==json.loads(r['current_points']) and mapping[0]==json.loads(r['reference_points'])
            point_checks.append(dict(group=group,frame_id=r['frame_id'],current_exact=True,reference_exact=True,point_sha=r['point_source_sha']))
    protected=get(OLD/'g0_identity.json')['protected'];protected+= [dict(path=k,sha256=h) for k,h in get(OLD/'source_hashes.json')['files'].items()]
    for p in protected:assert sha(ROOT/p['path'])==p['sha256']
    csvwrite(run/'input_manifest.csv',data);csvwrite(run/'point_source_verification.csv',point_checks)
    put(run/'g0_identity.json',dict(utc=utc(),frames=len(data),unique_original_files=len(files),excluded_frames=0,all_input_files=files,protected=protected,old_completion_sha=sha(OLD/'completion_seal.json')))

def process(job):
    run,row=job;run=Path(run);d=directory(run,row);d.mkdir(parents=True,exist_ok=True);tick=time.perf_counter()
    if (d/'inference_manifest.json').exists():
        for k,h in get(d/'inference_manifest.json')['files'].items():assert sha(d/k)==h
        return dict(group=row['group'],frame_id=row['frame_id'],resumed=True)
    a,old,cache=cached(row);cache_ms=(time.perf_counter()-tick)*1000;P=json.loads(row['current_points']);t=time.perf_counter()
    result,graphs,masks,branches,control,timing=detect(evidence=a,P_cur=P,config=CONFIG);total_ms=(time.perf_counter()-t)*1000
    expected=next(r for r in old['results'] if r['mode']=='C_FUSION_RAW');assert native_result(result[0])==expected,'A native trace changed'
    with np.load(ROOT/cache['path']/'candidate_graphs.npz') as q:
        for k,v in graphs[MODES[0]].items():assert np.array_equal(v,q['C_FUSION_RAW__'+k]),k
    E,_=fusion(a);g=a['roi'];stats=[];lineage={};audit_ms=0.;arr={name:m for name,m in zip(MODES,masks)};arr['corridor_branches']=branches;arr['global_offset']=np.array([g['xa'],g['ya']],np.int32)
    stable_A={(int(x),int(y)):i for i,(x,y,*_) in enumerate(graphs[MODES[0]]['nodes'])}
    allcoords=set(stable_A);maps=[]
    for name in MODES:
        graph=graphs[name];mapping={(int(x),int(y)):i for i,(x,y,*_) in enumerate(graph['nodes'])};maps.append(mapping);allcoords.update(mapping)
        for key,v in graph.items():arr[name+'__'+key]=v
    node_lineage=[]
    for x,y in sorted(allcoords):node_lineage.append([x+g['xa'],y+g['ya'],* [v.get((x,y),-1) for v in maps],*[int(m[y,x]) for m in masks]])
    arr['node_lineage']=np.asarray(node_lineage,np.int32).reshape(-1,8)
    for mode,mask,pred in zip(MODES,masks,result):
        graph=graphs[mode];segs=collections.defaultdict(list)
        for k,x,y in graph['segments']:segs[int(k)].append([int(x)-g['xa'],int(y)-g['ya']])
        t=time.perf_counter();route,edges,counts=routes([segs[k] for k in range(len(segs))],E,g,a['notch']);audit_ms+=(time.perf_counter()-t)*1000
        assert np.array_equal(edges,graph['edges']) and all(counts[k]==pred['counts'][k] for k in counts)
        lineage[mode]=route;reasons=collections.Counter(r['reason'] for r in route);width=mask.sum(0);allow=width[width>0];n=pred['counts'];chosen=pred['paths'][0] if pred['paths'] else None
        retained={(int(x),int(y)) for x,y,*_ in graph['nodes']};Aset=set(stable_A)
        stats.append(dict(group=row['group'],frame_id=row['frame_id'],mode=mode,safe_width=g['xr']-g['xleft'],safe_height=g['lower']-g['upper']-3,safe_area=int(masks[0].sum()),search_pixels=int(mask.sum()),area_ratio=float(mask.sum()/masks[0].sum()),width_p50=float(np.percentile(allow,50)) if len(allow) else 0,width_p95=float(np.percentile(allow,95)) if len(allow) else 0,width_max=int(width.max()),active_columns=int((width>0).sum()),max_reach_x=int(np.flatnonzero(width)[-1]+g['xa']) if width.any() else None,branches=1 if mode!=MODES[2] else int(sum(b.any() for b in branches)),raw_peaks=n['raw_peak_count'],nodes=n['retained_count'],candidate_per_1000px=1000*n['retained_count']/max(1,mask.sum()),capacity_dropped=n['capacity_dropped'],graph_edges=n['graph_edges'],incoming_truncated=n['incoming_truncated'],paths=len(pred['paths']),eligible_routes=n['eligible_routes'],containment_deleted=reasons['FRAGMENT_CONTAINMENT'],path_budget_not_visited=reasons['NOT_VISITED_PATH_BUDGET'],A_nodes_inside=sum(bool(mask[y,x]) for x,y in Aset),A_nodes_retained=len(Aset&retained),A_nodes_geometry_excluded=sum(not mask[y,x] for x,y in Aset),A_nodes_inside_but_reselected=sum(mask[y,x] and (x,y) not in retained for x,y in Aset),newly_retained_nodes=len(retained-Aset),material_fraction=float(a['material'][mask].mean()) if mask.any() else 0,valley_supported_fraction=float((a['valley'][0][mask]>=a['threshold']).mean()) if mask.any() else 0,reference_fraction=float((a['diff']['ref_quality_map'][mask]>0).mean()) if mask.any() else 0,warp_fraction=float(a['diff']['valid_warp_mask'][mask].mean()) if mask.any() else 0,expansions=control['expansions'] if mode==MODES[2] else 0,contractions=control['contractions'] if mode==MODES[2] else 0,stop_candidates=len(chosen['stop_candidates']) if chosen else 0,eligible_stops=sum(s['eligible'] for s in chosen['stop_candidates']) if chosen else 0,observed=sum(t[2] for t in chosen['selected_trace']) if chosen else 0,inferred=sum(not t[2] for t in chosen['selected_trace']) if chosen else 0,**{k:v for k,v in pred['geometry_boundary'].items() if k!='tip_validation_window'}))
    stats=[{k:v.item() if isinstance(v,np.generic) else v for k,v in s.items()} for s in stats]
    rec=dict(identity=row,roi=g,cache=cache,reference_status=a['reference_status'],noise=a['noise'],threshold=a['threshold'],notch=a['notch'],results=result,geometry=control,stats=stats,timing=timing,cache_load_verify_ms=cache_ms,geometry_control_ms=max(0,total_ms-sum(t['inference_ms'] for t in timing)),lineage_audit_ms=audit_ms,peak_rss=psutil.Process().memory_info().peak_wset if hasattr(psutil.Process().memory_info(),'peak_wset') else psutil.Process().memory_info().rss,A_parity=True,GT_accessed=False,config_sha=sha(run/'config_frozen.yaml'))
    putgz(d/'result.json.gz',rec);putgz(d/'route_lineage.json.gz',lineage);save_npz(d/'evidence_arrays.npz',**arr)
    put(d/'roi_metadata.json',dict(identity=row,roi=g,evidence_cache=cache,array_contract='Full-resolution immutable numeric cache referenced by SHA; no PNG substitutions',mask_columns=['x_global','y_global','A_node_index','B_node_index','C_node_index','A_inside','B_inside','C_inside'],reference_context_unchanged=True,tip_context_unchanged=True,origin_status=control['origin_status'],surface_grid=[100,55],diff_range=[-40,40],coordinate_convention='0-based original x/y, y down; masks use safe evidence crop offsets'))
    put(d/'inference_manifest.json',dict(files={p.name:sha(p) for p in d.iterdir() if p.is_file()},A_parity=True))
    return dict(group=row['group'],frame_id=row['frame_id'],seconds=time.perf_counter()-tick)

def role(run,data,workers,phase):
    check_sources(run);t=time.perf_counter();completed=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers,initializer=init) as pool:
        for i,r in enumerate(pool.map(process,[(str(run),r) for r in data]),1):
            completed.append(r)
            with open(run/'progress.jsonl','a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=utc(),phase=phase,**r))+'\n')
            if i%25==0 or i==len(data):print(f'{phase} {i}/{len(data)} {time.perf_counter()-t:.1f}s',flush=True)
    files={}
    for row in data:
        d=directory(run,row)
        for name in ['result.json.gz','evidence_arrays.npz','route_lineage.json.gz','roi_metadata.json','inference_manifest.json']:files[str((d/name).relative_to(run)).replace('\\','/')]=sha(d/name)
    target=run/f'frozen_{phase}.json'
    if target.exists():assert get(target)['files']==files
    else:put(target,dict(utc=utc(),frames=len(data),files=files,GT_read=False))
    if not(run/f'evaluation_complete_{phase}.json').exists():subprocess.run([sys.executable,'-m','grayref_roi_geometry_ablation.evaluate','--run',str(run),'--phase',phase],check=True,cwd=ROOT)

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--group-manifest');p.add_argument('--mode',choices=['ALL']+MODES,default='ALL');p.add_argument('--workers',type=int,default=12);p.add_argument('--resume',action='store_true');p.add_argument('--dry-run',action='store_true');p.add_argument('--render',action='store_true');p.add_argument('--phase',choices=['all','group_a','regression'],default='all');args=p.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]+',args.run_id):raise ValueError('Simple unique run ID required')
    data=manifest(args.group_manifest);run=ROOT/'output/experiments'/args.run_id
    if args.dry_run:print(json.dumps(dict(groups=GROUPS,frames=len(data),modes=MODES if args.mode=='ALL' else [args.mode],output=str(run),no_images_or_GT_opened=True)));return
    if args.mode!='ALL':raise ValueError('Primary causal run requires ALL modes; --mode selects descriptive dry-run only')
    if run.exists() and (run/'source_hashes.json').exists() and not args.resume:raise ValueError('Existing run requires --resume')
    run.mkdir(parents=True,exist_ok=True)
    if not(run/'source_hashes.json').exists():
        if args.phase=='regression':raise ValueError('GROUP_A must run first')
        from .tests import run_tests
        assert get(SOURCE/'config_frozen.yaml')==CONFIG
        inputs(run,data);run_tests(run)
        for name in ['config_frozen.yaml','experiment_plan.json','roi_geometry_spec.md','algorithm_diff_audit.md','README.md']:write_bytes(run/name,(SOURCE/name).read_bytes())
        hashes=source_hashes();put(run/'source_hashes.json',dict(utc=utc(),files=hashes))
        for name in hashes:write_bytes(run/'source_snapshot'/name,(ROOT/name).read_bytes())
        put(run/'environment.json',dict(utc=utc(),python=sys.version,platform=platform.platform(),numpy=np.__version__,opencv=cv2.__version__,logical_cpus=os.cpu_count(),memory_bytes=psutil.virtual_memory().total,free_disk=shutil.disk_usage(ROOT).free,workers=args.workers,git='NOT_A_GIT_REPOSITORY'))
    check_sources(run)
    if args.phase in ['all','group_a']:role(run,[r for r in data if r['group']=='group_a'],args.workers,'group_a')
    if args.phase in ['all','regression']:
        assert (run/'evaluation_complete_group_a.json').exists();role(run,[r for r in data if r['group']!='group_a'],args.workers,'exposed')
    if args.render:
        for module in ['render','verify_integrity','report']:
            subprocess.run([sys.executable,'-m','grayref_roi_geometry_ablation.'+module,'--run',str(run),'--workers',str(args.workers)],check=True,cwd=ROOT)

if __name__=='__main__':main()
