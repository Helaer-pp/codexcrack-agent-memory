"""Check tracked working files and reachable Git objects against the public handoff budget."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
def git(*args):
    return subprocess.check_output(['git', *args], cwd=root)

paths = git('ls-files', '-z').decode().split('\0')
working = sum((root/p).stat().st_size for p in paths if p and (root/p).is_file())
objects = git('rev-list', '--objects', '--all').splitlines()
ids = {line.split(b' ',1)[0] for line in objects}
if ids:
    sizes = subprocess.check_output(['git','cat-file','--batch-check=%(objectsize)'], input=b'\n'.join(ids)+b'\n', cwd=root)
    history = sum(map(int,sizes.splitlines()))
else:
    history = 0
print(f'Tracked files: {working:,} bytes. Reachable Git objects (uncompressed): {history:,} bytes.')
if max(working,history) >= 100_000_000:
    raise SystemExit('Repository exceeds its size budget.')

