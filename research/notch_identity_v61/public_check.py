"""Replay selected native frames through the user's EXE and compare sealed outputs."""
import json
import os
from pathlib import Path
import subprocess
import sys
from PIL import Image
from research.v3_labelme_comparison.compare import write_csv
from tools.check_crack_tip_run import check
from . import batch as b
from .run import frozen
from .inputs import metadata

def main():
    frozen()
    stage=b.read(b.OUT/'selection.json')['stage']
    flags=[] if b.read(b.OUT/'selection.json')['release'] else ['--candidate']
    exe=b.ROOT/'output/releases/CrackTipRunner/CrackTipRunner.exe'
    run_dir=b.ROOT/'output/verification/v61_public_runner';run_dir.mkdir(parents=True,exist_ok=True)
    version=subprocess.check_output([str(exe),*flags,'--version'],text=True,encoding='utf8').strip()
    assert version=='V6.1 '+stage,version
    from run_crack_tip import SETTINGS
    rows=[]
    for g,i,placement in [('group_h',78,'original'),('group_h',397,'original'),('group_a',112,'original'),('group_a',299,'original'),('three_point_bend',144,'original'),('three_point_bend',215,'original'),('group_c',7,'original'),('group_c',7,'bright'),('group_c',38,'bright')]:
        assert b.read(b.ROOT/'config/dataset_usage_policy.json')['groups'][g] in ('VALIDATION_ONLY','DEVELOPMENT')
        meta=metadata(g,i)
        name=f'{g}_{placement}_{i}'
        target=run_dir/name;cfg=run_dir/(name+'.json')
        template=dict(SETTINGS,reference_image=meta['input']['reference'],image_input=meta['input']['current'],
            output_dir=str(target),reference_points=meta['fixed_points'],current_points=meta['current_points'],
            point_mode='fixed',first_frame=1,last_frame=1,roi=None,feature_scale_px=None,
            bright_profile='auto' if placement=='bright' else None,save_comparisons=True,save_differences=True,
            save_video=True,ffmpeg=str(b.ROOT/'third_party/ffmpeg/ffmpeg.exe'))
        cfg.write_text(json.dumps(template,ensure_ascii=False,indent=2),encoding='utf8')
        before=set(target.glob('*/run.json'))
        proc=subprocess.run([str(exe),*flags,'--config',str(cfg)],cwd=b.ROOT,check=True)
        new,=set(target.glob('*/run.json'))-before
        folder=new.parent
        check(folder,b.OUT/(g+'.jsonl'),placement,i)
        exact=None
        if g=='group_a' and i==112:
            with Image.open(folder/'differences/000001.png') as a,Image.open(b.OUT/'difference_views/differences/group_a/0112.png') as c:
                exact=a.size==c.size and a.tobytes()==c.tobytes()
            assert exact
        rows.append(dict(group=g,frame=i,placement=placement,version=version,matched=True,
                         identical_unlabeled_diff=exact,folder=str(folder)))
    write_csv(run_dir/'checks.csv',rows)

if __name__=='__main__':main()
