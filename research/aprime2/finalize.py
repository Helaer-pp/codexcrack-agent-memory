from common import *
import shutil,subprocess,zipfile,html,difflib
from concurrent.futures import ThreadPoolExecutor
from local_reference import inside

def execute():
    guard();assert (RUN/'03_A_candidate_audit/Gate0_final_native.json').exists()
    assert not (RUN/'06_TEST').exists(),'No independent TEST authorized by gates'
    media=RUN/'08_media';verification=[]
    def verify_png(p):
        a=cv2.imdecode(np.fromfile(str(p),np.uint8),cv2.IMREAD_UNCHANGED)
        assert a is not None and a.shape[:2]==(900,1600),str(p)
        return dict(path=p.relative_to(RUN).as_posix(),kind='PNG',decoded=True,frames=1)
    pngs=sorted(media.rglob('*.png'))
    with ThreadPoolExecutor(max_workers=2) as ex:verification.extend(ex.map(verify_png,pngs))
    ff=ROOT/'third_party/ffmpeg/ffmpeg.exe';probe=ROOT/'third_party/ffmpeg/ffprobe.exe'
    expected={g['id']:g['frames'] for g in json.loads((ROOT/'config/datasets.json').read_text(encoding='utf8'))['groups']}
    for p in sorted((media/'videos').glob('*.mp4')):
        raw=subprocess.check_output([str(probe),'-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,r_frame_rate','-of','json',str(p)])
        s=json.loads(raw)['streams'][0];n=int(s['nb_frames']);want=540 if p.name.startswith('DEV') else next(v for g,v in expected.items() if p.name.startswith(g+'_'))
        assert n==want and s['width']==1600 and s['height']==900 and s['r_frame_rate']=='15/1'
        result=subprocess.run([str(ff),'-v','error','-i',str(p),'-f','null','-'],capture_output=True)
        assert result.returncode==0 and not result.stderr,result.stderr.decode(errors='replace')
        verification.append(dict(path=p.relative_to(RUN).as_posix(),kind='MP4',decoded=True,frames=n))
        print('VERIFIED VIDEO',p.name,n,flush=True)
    csvout(media/'verification.csv',verification)
    save(media/'verification_summary.json',dict(pngs=len(pngs),videos=sum(x['kind']=='MP4' for x in verification),all_decoded=True))
    mm=rows(ROOT/'data/inputs/six_groups_manifest.csv');lookup={(m['dataset_alias'],int(m['frame_id'])):m for m in mm}
    flat=[];cands=[];preserved=0;valid_a=0;max_candidates=0
    for z in jl(RUN/'04_reference_validity/real_predictions.jsonl'):
        a=z['A']['formal'];tip=a['tip'];m=lookup[z['group'],z['frame_id']];pp=z['points']
        max_candidates=max(max_candidates,len(z['pool']));assert len(z['pool'])<=12
        if a['confirmed_tip']:
            valid_a+=1;c=next(c for c in z['pool'] if c['A_original_bitwise'])
            assert np.asarray(c['xy'],dtype='<f8').tobytes()==np.asarray(tip,dtype='<f8').tobytes()
            preserved+=1
        flat.append(dict(run_id=RUN.name,group=z['group'],frame_id=z['frame_id'],image_number=z['frame_id']+1,filename=m['filename'],
            input_image=m['input_image'],image_sha256=m['input_sha256'],reference_sha256=lookup[z['group'],0]['input_sha256'],
            A_path_sha256=hashlib.sha256(np.asarray(a['raw_path'],dtype='<f8').tobytes()).hexdigest(),P1_x=pp[0][0],P1_y=pp[0][1],P2_x=pp[1][0],P2_y=pp[1][1],
            A_valid=a['confirmed_tip'],A_tip_x=tip[0] if tip else None,A_tip_y=tip[1] if tip else None,A_old_arc_px=a['length_px'],
            Aprime2_valid=a['confirmed_tip'],Aprime2_tip_x=tip[0] if tip else None,Aprime2_tip_y=tip[1] if tip else None,
            Aprime2_decision='A_UNCHANGED',Aprime2_reason='GLOBAL_REFERENCE_GATE_NOT_PASSED',tip_authority='FROZEN_A_FALLBACK_NOT_NEW_CONFIRMATION',
            horizontal_length_px=z['horizontal_length_px'],candidate_count=len(z['pool']),A_stop_reason=z['A']['native']['stop_reason'],
            phase='PHASE_UNKNOWN',reference_path_coverage=z['states']['coverage'],full_native_ms='NOT_TESTED',physical_GT=None))
        for c in z['pool']:
            geometry=False;photo=False
            audit=np.asarray(c['xy'])+np.array([[-16,-16],[-16,16],[16,-16],[16,16]])
            for q in z['queries']:
                covered=q['reg']['local_supported'] and inside(q['reg']['polygon'],audit)
                geometry|=covered;photo|=covered and q['photo']['state']=='PHOTO_SUPPORTED'
            comp=next((t for t in z['comparison'] if t['candidate_id']==c['candidate_id']),{})
            cands.append(dict(group=z['group'],frame_id=z['frame_id'],**c,
                reference_geometry_state='SUPPORTED' if geometry else 'UNKNOWN',reference_photo_state='SUPPORTED' if photo else 'UNKNOWN',
                disputed_coverage=comp.get('disputed_coverage'),NEW_interval_lengths=None,STATIC_RISK_interval_lengths=None,
                increment_state='UNKNOWN' if not photo else 'SEE_PATH_EVIDENCE_NOT_WHOLE_INTERVAL_PROOF',
                selected=bool(c['A_original_bitwise']),rejected_reason=None if c['A_original_bitwise'] else 'GLOBAL_GATE_B_NOT_PASSED',processing_cost_ms=None))
    csvout(RUN/'09_reports/real_frame_results.csv',flat);csvout(RUN/'03_A_candidate_audit/candidate_complete_audit.csv',cands)
    save(RUN/'03_A_candidate_audit/A_original_retention.json',dict(valid_A=valid_a,bitwise_preserved=preserved,rate=1.,K_max=max_candidates))
    # Saved code has project-relative layout; it is evidence, not an import dependency.
    sources=[*SOURCE.rglob('*.py'),*SOURCE.rglob('*.cpp'),*SOURCE.rglob('*.md'),
             * (ROOT/'src/python/crackv4').glob('*.py'),* (ROOT/'research/aprime/experiments').glob('*.py'),
             * (ROOT/'baseline/frozen_a/src').glob('*'),ROOT/'CMakeLists.txt',ROOT/'build.ps1',ROOT/'config/project.json',
             ROOT/'config/datasets.json',ROOT/'requirements.txt',ROOT/'AGENTS.md',ROOT/'README.md',ROOT/'docs/CURRENT_STATE.md',ROOT/'CrackV4_Aprime2_MultiStop_ValidatedReference_Agent_Prompt.md']
    sourcehash={}
    for p in sources:
        if not p.is_file():continue
        rel=p.relative_to(ROOT);dest=RUN/'02_source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);sourcehash[rel.as_posix()]=sha(p)
    for name in ['CrackV4AP2Shadow.dll','AP2DualBench.exe']:
        p=ROOT/'output/build/Release'/name;dest=RUN/'02_source/native_research_bin'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    save(RUN/'01_protocol_and_freeze/final_source_snapshot.json',dict(utc=utc(),role='POST_DEV_RESEARCH_SNAPSHOT_NOT_PRE_TEST_LOCK',hashes=sourcehash))
    baseline=(ROOT/'baseline/frozen_a/src/CrackV4.cpp').read_text(encoding='utf8');shadow=(SOURCE/'src/native_shadow/CrackV4_ap2.cpp').read_text(encoding='utf8')
    write(RUN/'01_protocol_and_freeze/final_native_diff.patch',''.join(difflib.unified_diff(baseline.splitlines(True),shadow.splitlines(True),fromfile='frozen_A',tofile='AP2_shadow')))
    # HTML entry point and per-group lazy image galleries, all local relative links.
    style='body{background:#0a1721;color:#e2eaf0;font:16px system-ui;margin:30px}a{color:#6ed5ed}video{width:min(100%,1100px)}img{max-width:100%}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:20px}figure{margin:0}p{line-height:1.65}'
    links=[]
    for g in expected:
        rowsg=[m for m in mm if m['dataset_alias']==g]
        gallery=''.join(f'<figure><a href="../08_media/per_frame/{g}/{int(m["frame_id"]):04d}.png"><img loading="lazy" src="../08_media/per_frame/{g}/{int(m["frame_id"]):04d}.png"></a><figcaption>num={m["frame_id"]} / 第{int(m["frame_id"])+1}张 / {html.escape(m["filename"])}</figcaption></figure>' for m in rowsg)
        write(RUN/f'09_reports/gallery_{g}.html',f'<!doctype html><meta charset="utf-8"><style>{style}</style><h1>{g} 逐帧原图/路径/候选对照</h1><p><a href="../index.html">返回</a>；无物理GT，橙色是候选，A输出未修改。</p><div class="grid">{gallery}</div>')
        links.append(f'<h2>{g} · {expected[g]}帧</h2><p><a href="09_reports/gallery_{g}.html">全部逐帧对照图</a> · <a href="08_media/videos/{g}_A_AP2_diagnostic.mp4">MP4文件</a></p><video controls preload="none" src="08_media/videos/{g}_A_AP2_diagnostic.mp4"></video>')
    for v in [2,3]:links.append(f'<h2>DEV v{v} · 540帧（已曝光）</h2><video controls preload="none" src="08_media/videos/DEV_v{v}_{"prefilter_" if v==3 else ""}diagnostic.mp4"></video>')
    keys=''.join(f'<figure><a href="{p.relative_to(RUN).as_posix()}"><img loading="lazy" src="{p.relative_to(RUN).as_posix()}"></a><figcaption>{html.escape(p.stem)}</figcaption></figure>' for p in sorted((media/'key_cases').glob('*.png')))
    write(RUN/'index.html',f'''<!doctype html><html lang="zh"><meta charset="utf-8"><title>A′2 研究交付</title><style>{style}</style>
<h1>A′2 开发结果：KEEP_A</h1><p>冻结 A 全部3035帧保持一致。DEV正确尖端359→365；参考未泛化，未启动独立TEST，未发布生产DLL。视频15 FPS只是播放速度，完整原生A′2实时性未测试。</p>
<p><a href="00_executive_summary.md">摘要</a> · <a href="09_reports/development_report.md">开发报告</a> · <a href="09_reports/real_frame_results.csv">真实3035帧结果CSV</a> · <a href="05_DEV/full_v3/failure_stages.csv">DEV失败逐帧CSV</a> · <a href="reproduce.md">复现</a></p>
<p>黄圈=A原端点；橙圈=研究候选；绿圈=DEV研究改动；紫十字=程序GT；青多边形=局部参考有效域。真实资料无物理GT，排除组X退役历史、三点弯曝光验证，均不调参。</p>
{''.join(links)}<h2>关键失败与配对证据</h2><div class="grid">{keys}</div></html>''')
    # Verify HTML links point to real artifacts before hashing.
    import re
    for page in [RUN/'index.html',*(RUN/'09_reports').glob('gallery_*.html')]:
        for target in re.findall(r'(?:href|src)="([^"]+)"',page.read_text(encoding='utf8')):
            assert (page.parent/target).resolve().exists(),(page,target)
    hashes=[dict(path=p.relative_to(RUN).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(RUN.rglob('*')) if p.is_file() and p.name not in ['manifest_sha256.csv','A_prime2_source_results.zip','finalize.log']]
    csvout(RUN/'manifest_sha256.csv',hashes)
    package=RUN/'A_prime2_source_results.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as zz:
        zz.writestr('PACKAGE_README.txt','This is a SOURCE/NUMERIC/REPORT subset, not the full media delivery.\nMP4, PNG, synthetic input images and HTML galleries remain in the local run folder.\nOpen the local run index.html for verified videos and images.\nmanifest_sha256.csv describes the FULL local run, not only this ZIP.\nProduction is frozen A; native_research_bin contains observer tooling only.\n')
        for p in sorted(RUN.rglob('*')):
            if not p.is_file() or p==package:continue
            rel=p.relative_to(RUN)
            if rel.parts[0]=='08_media' or 'inputs' in rel.parts or p.suffix in ['.log','.html']:continue
            zz.write(p,rel.as_posix())
    with zipfile.ZipFile(package) as zz:assert zz.testzip() is None
    guard();print('FINALIZED',len(pngs),'PNGs',sum(x['kind']=='MP4' for x in verification),'videos',len(flat),'real rows',flush=True)

if __name__=='__main__':execute()
