"""Reproduce into a NEW ASCII output directory. Default DEVELOPMENT only; no overwrite."""
from pathlib import Path
import argparse,sys,os,subprocess,zipfile,hashlib,json,shutil

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--package',type=Path);p.add_argument('--include-validation',action='store_true',help='Explicitly replay already-exposed validation after native parity, never tune');p.add_argument('--plan',action='store_true',help='Validate destinations and print steps without writing or inference');a=p.parse_args()
 import common
 root=common.ROOT;out=a.output.resolve();assert out.is_relative_to((root/'output').resolve());assert out.as_posix().isascii(),'Frozen OpenCV file I/O needs ASCII path';assert not out.exists(),'Never overwrite a completed/partial run; choose a new output directory'
 packages=list(root.glob('P1P2_GrayRef_V1_Frozen*.zip'));package=a.package.resolve() if a.package else packages[0] if len(packages)==1 else None;assert package and package.is_file(),'Specify --package';assert common.sha(common.FROZEN)==common.EXPECTED_SHA
 steps=['Verify package/hash; metadata-only DEVELOPMENT manifest','Compile separate C++17/v142 DLL','Original six-mode regression and contracts','All1565 DEVELOPMENT original Python main, then C++ full trace parity','Offline76 VISIBLE/4 UNCERTAIN scoring;12 CLI timing samples','Four full videos and80 detailed cards']+(['Lock rules; all1082 validation frames;35 VISIBLE/5 UNCERTAIN offline scoring','Two validation videos; combined reports and index'] if a.include_validation else ['Stop without validation images or labels'])
 print(json.dumps(dict(output=str(out),package=str(package),validation=a.include_validation,steps=steps),ensure_ascii=False,indent=2),flush=True)
 if a.plan:return
 out.mkdir(parents=True);common.OUT=out;common.BUILD=out/'build';os.environ['PYTHONPYCACHEPREFIX']=str(out/'pycache')
 with zipfile.ZipFile(package) as z:
  for entry in z.infolist():
   dest=(out/'input_package'/entry.filename).resolve();assert dest.is_relative_to((out/'input_package').resolve());dest.parent.mkdir(parents=True,exist_ok=True)
   if not entry.is_dir():dest.write_bytes(z.read(entry))
 pack=out/'input_package';assert common.sha(pack/'paired_p1p2_roi_V1_FROZEN.py')==common.EXPECTED_SHA
 import preflight
 prior=sys.argv;sys.argv=[__file__,'--frozen-root',str(pack),'--output',str(out)]
 try:preflight.main()
 finally:sys.argv=prior
 with (out/'build.log').open('w',encoding='utf8') as log:
  for cmd in [['D:/CMake/bin/cmake.exe','-S',str(root/'research/p1p2_grayref_v1'),'-B',str(common.BUILD),'-G','Visual Studio 17 2022','-A','x64','-T','v142'],['D:/CMake/bin/cmake.exe','--build',str(common.BUILD),'--config','Release']]:subprocess.run(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT,check=True)
 import python_replay,cpp_replay,contracts,parity_gate,evaluate,benchmark_cli,media,frame_comparisons
 python_replay.regression();gold=common.rows(pack/'baseline/expected_summary_results.csv');actual=common.rows(out/'regression/summary_results.csv');assert gold==actual,'Do not rewrite golden values'
 checks=common.read(out/'regression/regression_checks.json');checks.update(six_golden_complete=True,six_full_summary_rows_equal=True)
 for check,row in zip(checks['checks'],gold):check.update(expected=[int(row['tip_x']),int(row['tip_y'])],passed=True,expected_source='original_package_expected_summary_results.csv')
 common.write(out/'regression/regression_checks.json',checks)
 common.write(out/'package_identity.json',dict(zip_path=str(package),zip_sha256=common.sha(package),source_exact=True,full_six_row_regression_equal=True,files={str(x.relative_to(pack)):common.sha(x) for x in pack.rglob('*') if x.is_file()}))
 contracts.main();cpp_replay.regression()
 for g in common.DEV:python_replay.replay(g)
 for g in common.DEV:cpp_replay.replay(g)
 parity_gate.main();evaluate.main(common.DEV);benchmark_cli.main()
 for g in common.DEV:media.group(g);frame_comparisons.main(g)
 if a.include_validation:
  import validation,report
  validation.prepare()
  for g in common.VAL:validation.run(g)
  evaluate.main(common.VAL)
  for g in common.VAL:media.group(g);frame_comparisons.main(g)
  media.index();report.main()
 print('REPRODUCTION COMPLETE; original sealed output untouched',flush=True)
if __name__=='__main__':main()
