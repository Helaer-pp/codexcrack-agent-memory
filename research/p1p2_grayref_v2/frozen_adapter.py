"""Exact immutable V1 main, read-only capture; skip plotting AFTER six CSV traces.
Only the image-reader seam supplies the same decoded uint8 inputs (Unicode-safe).
Gate0 compares this compute-only adapter to an untouched CLI invocation.
"""
from v2common import *
import numpy as np,cv2,types,ast,contextlib,time
class RenderSkipped(BaseException):pass
def decode(path):
 a=cv2.imdecode(np.frombuffer(Path(path).read_bytes(),np.uint8),0)
 if a is None:raise ValueError('Image decode failed: '+str(path))
 return a
def load():
 assert sha(FROZEN)==SHA;m=types.ModuleType('original_v1');m.__file__=str(FROZEN)
 source=FROZEN.read_text(encoding='utf8');exec(compile(source,str(FROZEN),'exec'),m.__dict__)
 tree=ast.parse(source);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 line=next(n.lineno for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Tuple) and any(isinstance(e,ast.Name) and e.id=='fig' for e in t.elts) for t in n.targets))
 return m,line
def compute(R,C,rp,cp,folder):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=False);m,line=load();captured={};previous=sys.argv
 m.imread_gray=lambda p:R if p=='reference.bmp' else C
 sys.argv=[str(FROZEN),'--reference','reference.bmp','--current','current.bmp','--output-dir',str(folder)]
 # parse_args resolves relative image names against the immutable script directory.
 m.imread_gray=lambda p:R if Path(p).name=='reference.bmp' else C
 for prefix,points in [('ref',rp),('cur',cp)]:
  for i,p in enumerate(points,1):sys.argv += [f'--p{i}-{prefix}',f'{p[0]},{p[1]}']
 def observe(frame,event,arg):
  if frame.f_code is m.main.__code__ and event=='line' and frame.f_lineno==line:
   captured.update(frame.f_locals);raise RenderSkipped()
  return observe
 start=time.perf_counter()
 try:
  with (folder/'stdout.txt').open('w',encoding='utf8') as out,(folder/'stderr.txt').open('w',encoding='utf8') as err,contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
   sys.settrace(observe)
   try:m.main()
   except RenderSkipped:pass
   finally:sys.settrace(None)
 finally:sys.argv=previous
 assert 'traces' in captured
 result=dict(roi={k:int(captured[k]) for k in ['xleft','xr','upper','lower','xa','ya','xb','yb']},arrays={k:captured[k] for k in ['reference_aligned','csm','rsm','valley','newdark','flank_low','valid_material','score']},traces=captured['traces'],runtime_ms=(time.perf_counter()-start)*1000)
 write(folder/'identity.json',dict(source_sha256=SHA,adapter='exact main; decode seam; skip rendering after all six trace/summary CSVs',reference_points=rp,current_points=cp,roi=result['roi'],runtime_ms=result['runtime_ms'],gt_accessed_at_inference=False))
 return result
