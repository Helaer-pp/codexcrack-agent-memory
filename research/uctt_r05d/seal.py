import shutil,zipfile,re
from PIL import Image
from common import *
def main():
 frozen=read(OUT/'frozen_manifest.json');changed=[p for p,h in frozen['protected'].items() if sha(ROOT/p)!=h];assert not changed,changed
 old=read(R05/'pre_evaluation_lock.json')
 assert all(sha(Path(p) if Path(p).is_absolute() else ROOT/p)==h for p,h in old['inputs'].items())
 assert all(sha(Path(p) if Path(p).is_absolute() else ROOT/p)==h for p,h in old['production'].items())
 eq=rows(OUT/'a0_d0_equivalence.csv');assert len(eq)==2647 and all(r['non_timing_exact']=='True' for r in eq)
 points=rows(OUT/'tip_reachability_per_frame.csv');assert len(points)==120
 assert max(float(r['coordinate_roundtrip_px']) for r in points)<1e-7
 assert all(float(r['internal_tip_to_returned_px'])==0 for r in points if r.get('internal_tip_to_returned_px'))
 assert read(OUT/'video_qa.json')['full_decode']=='PASS'
 page=(OUT/'R05D_G0_G5_Failure_Gallery.html').read_text(encoding='utf8')
 links=re.findall(r'(?:src|href)="([^"]+)"',page)
 assert all((OUT/p.split('#')[0]).is_file() for p in links)
 for p in (OUT/'images').glob('*.jpg'):
  with Image.open(p) as im:im.verify()
 with zipfile.ZipFile(OUT/'R05D_visual_evidence.zip') as z:
  assert z.testzip() is None
  assert all(p.split('#')[0] in z.namelist() for p in links)
 compiler=next((BUILD/'CMakeFiles').glob('*/CMakeCXXCompiler.cmake'));shutil.copy2(compiler,OUT/'compiler_identity.cmake')
 content=compiler.read_text();match=re.search(r'set\(CMAKE_CXX_COMPILER "([^"]+)"\)',content);compiler_path=Path(match.group(1)) if match else None
 builds={p.name:sha(p) for p in (BUILD/'Release').glob('*.dll')}
 write(OUT/'build_identity_final.json',dict(dll_hashes=builds,compiler_path=str(compiler_path),compiler_sha256=sha(compiler_path) if compiler_path and compiler_path.is_file() else None,cmake_compiler_record_sha256=sha(compiler)))
 for p in (ROOT/'output/cache').glob('r05d*.log'):shutil.copy2(p,OUT/'logs'/p.name)
 sources=list((ROOT/'research/uctt_r05d').glob('*'))+[ROOT/'AGENTS.md',ROOT/'README.md',ROOT/'docs/CURRENT_STATE.md',POLICY_PATH]
 with zipfile.ZipFile(OUT/'research_source_and_binaries.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sources:
   if p.is_file():z.write(p,p.relative_to(ROOT).as_posix())
  for p in GEN.glob('*'):
   if p.is_file():z.write(p,'generated_final/'+p.name)
  for p in (BUILD/'Release').glob('*.dll'):z.write(p,'binaries/'+p.name)
  z.write(ROOT/'output/build/src/cpp/a/Release/CrackV4.dll','binaries/A0_FROZEN.dll')
 write(OUT/'final_integrity.json',dict(status='PASS',production_and_policy_files_unchanged=len(frozen['protected']),prior_locked_inputs_unchanged=len(old['inputs']),human_labels_unchanged=True,group_x_images_or_labels_read=False,validation_used_for_tuning=False,training=False,exact_equivalence_frames=len(eq),selected_frames=len(points),all_html_links_and_zip_images_exist=True,source_snapshot=sha(OUT/'research_source_and_binaries.zip'),old_production_kept=True,stage_manifest_hashes={p.name:sha(p) for p in OUT.glob('*lock.json')}))
 write(OUT/'final_artifact_manifest.json',dict(status='SEALED',files={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='final_artifact_manifest.json'}))
 print('SEALED; production and human labels unchanged; all gallery links/ZIP images validated')
if __name__=='__main__':main()
