"""Standalone CPU Python V2 CLI: no label/GT/group input accepted."""
from v2common import *
from frozen_adapter import decode
from algorithm import detect
import argparse
def point(s):
 p=list(map(float,s.split(',')))
 if len(p)!=2:raise argparse.ArgumentTypeError('Expected x,y')
 return p
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',required=True,type=Path);p.add_argument('--current',required=True,type=Path);p.add_argument('--p1-ref',required=True,type=point);p.add_argument('--p2-ref',required=True,type=point);p.add_argument('--p1-cur',required=True,type=point);p.add_argument('--p2-cur',required=True,type=point);p.add_argument('--output',required=True,type=Path);a=p.parse_args();dest=a.output.resolve();assert dest.is_relative_to(ROOT/'output') and not dest.exists(),'Use a fresh directory inside project output';dest.mkdir(parents=True)
 r,arrays=detect(decode(a.reference),decode(a.current),[a.p1_ref,a.p2_ref],[a.p1_cur,a.p2_cur]);write(dest/'result.json',r);write(dest/'input_identity.json',dict(reference=str(a.reference.resolve()),current=str(a.current.resolve()),reference_sha=sha(a.reference),current_sha=sha(a.current),algorithm_sha=sha(Path(__file__).parent/'algorithm.py'),gt_accessed_at_inference=False));print([(x['mode'],x['output_state'],x['tip']) for x in r['results']])
if __name__=='__main__':main()
