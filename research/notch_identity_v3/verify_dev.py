"""Replay representative development frames into an isolated directory before freezing."""
import csv
import json
from pathlib import Path
from . import run


def verify():
    stages=['s1','s2','s3','s3t']
    root=run.RUN
    replay=root/'dev_replay'
    samples={'group_a':{1,165,551},'three_point_bend':{1,215,520}}
    with (run.OLD/'manifests/input_inventory.csv').open(encoding='utf-8-sig') as f:
        rows=[r for r in csv.DictReader(f) if r['group'] in samples and int(r['frame_id']) in samples[r['group']]]
    expected={}
    for s in stages:
        for g in samples:
            (replay/s/'frames'/g).mkdir(parents=True,exist_ok=True)
        with (root/s/'dev.jsonl').open() as f:
            for r in map(json.loads,f):
                if r['frame'] in samples[r['group']]:
                    expected[s,r['group'],r['frame']]=r
    run.RUN=replay
    comparisons=0
    for row in rows:
        for s,new in run.process((row,stages)).items():
            old=expected[s,new['group'],new['frame']]
            assert old['card_sha']==new['card_sha']
            for mode in ('raw_only','full'):
                for key in ('status','points','root','tip'):
                    assert old[mode][key]==new[mode][key]
                comparisons+=1
    run.save(root/'development_replay.json',dict(frames=len(rows),stage_mode_checks=comparisons,card_checks=comparisons//2))


if __name__=='__main__':
    verify()

