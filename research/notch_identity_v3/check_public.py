"""Run the public V3 regression matrix in a fresh temporary output directory."""
import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from . import probes

def check(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    original=probes.RUN
    expected=original/'probes.csv'
    def rows(p):
        with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    try:
        with TemporaryDirectory(dir=root) as tmp:
            probes.RUN=Path(tmp)
            probes.run(['s1','s2','s3','s3t'])
            actual=rows(probes.RUN/'probes.csv')
            assert len(actual)==420 and actual==rows(expected)
    finally:
        probes.RUN=original
    return len(actual)

if __name__=='__main__':
    print('Public synthetic rows verified:',check(Path('output/tests/public_v3')))

