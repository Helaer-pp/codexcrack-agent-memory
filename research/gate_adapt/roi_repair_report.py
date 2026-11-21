import argparse
import six_roi_report as r
from six_roi_replay import ROOT

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--run',default='roi_repair_20261108_final8')
    a=p.parse_args()
    r.OUT=ROOT/'output/runs'/a.run
    r.main()
