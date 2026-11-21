from pathlib import Path
import os,sys,json,csv,hashlib,time,collections,subprocess
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
os.environ['CRACK_AP2_RUN']=os.environ.get('CRACK_AP3_RUN','aprime3_20261105_r01')
sys.path.insert(0,str(ROOT/'research/aprime2'))
from common import (np,cv2,api,sha,scalar,write,save,rows,csvout,jl,read,native,guard,utc,anchors,apply,rigid,sample,put,dump_line)
SOURCE=ROOT/'research/aprime3';RUN=ROOT/'output/runs'/os.environ['CRACK_AP2_RUN']
if RUN.parent!=ROOT/'output/runs':raise ValueError('Unsafe run ID')
if (RUN/'manifest_sha256.csv').exists():raise RuntimeError('This run is sealed. Set CRACK_AP3_RUN to a fresh run ID; do not overwrite sealed evidence.')
OLD=ROOT/'output/runs/aprime2_20261105_r01'
for d in ['00_audit','00_protocol','01_diagnosis','02_source','03_exposed_regression','04_NEW_DEV','05_NEW_TEST','06_native_performance','07_media','08_reports']:(RUN/d).mkdir(parents=True,exist_ok=True)
cv2.setNumThreads(1)
