"""Assess and render the repaired seven-group replay."""
import argparse
import six_roi_outputs as o
from six_roi_replay import api, ROOT

GROUPS=('group_a','group_c','ct2','group_h','group_x','ct3','three_point_bend')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--run',default='roi_repair_20261108_final')
    args=p.parse_args()
    o.OUT=ROOT/'output/runs'/args.run
    for group in GROUPS:
        records=api.load(o.OUT/group/'records.jsonl')
        print(o.assess(group,records),flush=True)
        o.render(group,records)
