"""Offline artifact joins, verification and review images. Never invokes detection."""
import json
from collections import Counter
from itertools import zip_longest
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .batch import OUT,GROUPS,ALGS,ROOT,BASE,SELECT,read,sha,sources
from research.v3_labelme_comparison.infer import read_csv,current
from research.v3_labelme_comparison.compare import draw,PACKAGE,write_csv,evaluate,crop,panel
from research.notch_identity_v31.report import aggregate,NAMES
from research.notch_identity_v32.audit import signature,selected

MODES=('full','raw_only')
def fmt(v):
    return '—' if v is None or v=='' else f'{float(v):.2f}'
def regtext(reg):
    return f"{reg.get('status','—')}，平移 {reg.get('shift') or '—'}，NCC {fmt(reg.get('ncc'))}，峰差 {fmt(reg.get('margin'))}"

def audit():
    lock=read(OUT/'freeze.json')
    assert lock['sources']==sources()
    for p,k in [('group_a.jsonl','group_a'),('group_a_scores.csv','dev_scores'),('probes.csv','probes'),('paired_probes.csv','paired_probes'),('reference_tests.json','reference_tests')]:
        assert sha(OUT/p)==lock[k]
    assert read(OUT/'delivery_check.json')['cards']==1633
    rows={(g,int(r['frame']),r['stage'],r['mode']):r for g in GROUPS for r in read_csv(OUT/(g+'_scores.csv'))}
    stats=[dict(group=g,stage=s,mode=m,**aggregate([r for (group,i,stage,mode),r in rows.items() if (group,stage,mode)==(g,s,m)])) for g in GROUPS for s in ALGS for m in MODES]
    write_csv(OUT/'ablation_metrics.csv',stats)
    records={};times=[];evidence=[];parity=0
    for g,n in GROUPS.items():
        for folder in (OUT,BASE):
            assert sha(folder/(g+'.jsonl'))==read(folder/(g+'_seal.json'))['predictions']
        elapsed=[];revs=Counter();coarse=Counter();waived=0;diff=0;eligible=0
        with (OUT/(g+'.jsonl')).open() as new,(BASE/(g+'.jsonl')).open() as old:
            for a,b in zip_longest(new,old):
                rec,prior=json.loads(a),json.loads(b);i=rec['frame']
                assert rec['source_sha']==prior['source_sha'] and i==prior['frame']
                models=rec['models'];end=models['v3_4']['full']
                elapsed.append(models['v3_4']['seconds']);diff+=end['tip']!=models['v3_4']['raw_only']['tip']
                coarse[(end['diagnostics'].get('coarse') or {}).get('status','NO_ROOT')]+=1
                for c in end['diagnostics']['candidates']:
                    t=c.get('trace',{});ref=t.get('reference',{})
                    if c['status']=='VALID':assert 'decision' in ref
                    if ref:
                        eligible+=1;revs[ref['decision']]+=1;revs['SOURCE_'+ref.get('source','NONE')]+=1;waived+=bool(t.get('waived'))
                assert signature(models['v3_4']['raw_only'])==signature(prior['models']['v3_3']['raw_only'])
                if len(models)==1:continue
                records[g,i]=rec
                for s in ('r02','s3t','v3_1','v3_2','v3_3'):
                    for mode in MODES:
                        assert signature(models[s][mode])==signature(prior['models'][s][mode])
                        parity+=1
                for mode in MODES:
                    m=models['v3_4'][mode];t=selected(m);ref=t.get('reference',{});cr=m['diagnostics'].get('coarse') or {}
                    evidence.append(dict(group=g,frame=i,mode=mode,root=m['root'],tip=m['tip'],gate=t.get('gate'),stop=t.get('stop'),
                        geometry=t.get('geometry'),geometry_cut=t.get('geometry_cut'),rebound=t.get('rebound_cut'),waived=t.get('waived'),
                        coarse=cr,local=ref,increment_rank=t.get('increment_rank')))
        assert len(elapsed)==n
        times.append(dict(group=g,frames=n,mean_ms=1000*np.mean(elapsed),fps=1/np.mean(elapsed),
            p95_ms=1000*np.percentile(elapsed,95),worst_ms=1000*max(elapsed),worst_frame=int(np.argmax(elapsed))+1,
            coarse=dict(coarse),review=dict(revs),reviewed_candidates=eligible,waiver_candidates=waived,full_raw_tip_changed=diff))
    assert parity==600 and len(records)==60
    write_csv(OUT/'timing.csv',times);write_csv(OUT/'reference_audit.csv',evidence)
    return rows,stats,records,times

def failure_image(rec,mode,row,label_item,folder,summary):
    g=rec['group'];i=rec['frame'];model=rec['models']['v3_4'][mode]
    assert rec['source_sha']==label_item['sha256']
    raw=current(label_item['source_image'],rec['source_sha'])
    lab=read(PACKAGE/label_item['selected_json'])
    assert raw.shape==(lab['imageHeight'],lab['imageWidth'])
    paths=[np.asarray(s['points']) for s in lab['shapes'] if s['label']=='crack_path']
    gt,=[np.asarray(s['points'][0]) for s in lab['shapes'] if s['label']=='crack_tip']
    metric=evaluate(model,paths,gt)
    assert all(np.isclose(float(row[k]),metric[k]) for k in ('error_px','coverage','precision'))
    base=draw(raw,dict(group=g,frame=i,hint=model['root'] or paths[0][0],full=model),paths,gt,[],dict(state='VISIBLE',**metric))
    # The legacy zoom is centered on the annotation and can clip large errors.
    # Use one shared window containing both endpoints for all three detail panes.
    focus=crop(raw,[gt[None,:],np.asarray(model['tip'])[None,:]],35)
    manual=[(p,(255,204,25),False,False) for p in paths]
    predicted=[(model['points'],(65,225,90),False,True)]
    gm=[(gt,(255,204,25),True)];pm=[(model['tip'],(50,65,255),False)]
    base[345:]=25
    for j,(lines,marks) in enumerate([( [],[]),(manual,gm),(manual+predicted,gm+pm)]):
        panel(base,raw,focus,(480*j+8,349),(464,220),lines,marks)
    cv2.rectangle(base,(966,54),(1439,96),(25,25,25),-1)
    cv2.putText(base,'V3.4 '+mode+' : green path / red tip',(970,82),cv2.FONT_HERSHEY_SIMPLEX,.6,(238,238,238),1,cv2.LINE_AA)
    im=Image.new('RGB',(1440,720),'#f3f5f4');im.paste(Image.fromarray(cv2.cvtColor(base,cv2.COLOR_BGR2RGB)),(0,0))
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22);d=ImageDraw.Draw(im)
    lines=[f"{NAMES[g]}第 {i} 帧 · {mode}　人工尖端 ({gt[0]:.2f}, {gt[1]:.2f})　预测 {model['tip']}　覆盖 {float(row['coverage']):.1%}　精度 {float(row['precision']):.1%}"]
    line=''
    for char in summary:
        if d.textlength(line+char,font=font)>1370:lines.append(line);line=''
        line+=char
    lines.append(line)
    for k,line in enumerate(lines):d.text((18,591+33*k),line,font=font,fill='#172d3c')
    assert len(lines)<=4
    rel=f'failure_frames/{folder}/{mode}/{g}/{i:04d}.png'
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
    with Image.open(p) as test:test.load();assert test.size==im.size
    return rel
