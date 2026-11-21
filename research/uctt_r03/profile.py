"""Generate timer-only source copy; replay serially after behavioral experiment."""
import sys,json,ctypes as C,difflib,shutil,time
from prepare import ROOT,OUT,BUILD,sha,write
from pilot import api,inventory,LIMITS,lib,create,run,normalized
PBUILD=ROOT/'output/build/uctt_r03_profile'
SRC=ROOT/'output/build/uctt_r03_profile_source'
def generate():
 SRC.mkdir(parents=True,exist_ok=True)
 for p in (ROOT/'src/cpp/a').glob('*.inc'):shutil.copy2(p,SRC/p.name)
 edits={
 'CrackV4.cpp':[
 ('std::array<double, 16> profile_ms','std::array<double, 24> profile_ms'),
 ('bool Detector::estimateTipMotion(const cv::Mat &im) {','bool Detector::estimateTipMotion(const cv::Mat &im) {\n    PROFILE_SCOPE(16);'),
 ('    profile_ms.fill(0.);\n#endif','    profile_ms.fill(0.);\n#endif\n    PROFILE_SCOPE(20);')],
 'roi_tip.inc':[
 ('cv::Point drift,cv::Mat1b &knownCrack,const cv::Mat &mask) {','cv::Point drift,cv::Mat1b &knownCrack,const cv::Mat &mask) {\n    PROFILE_SCOPE(18);'),
 ('Path distalLine(const cv::Mat1f &score,const cv::Mat1f &intensity,bool absolute) {','Path distalLine(const cv::Mat1f &score,const cv::Mat1f &intensity,bool absolute) {\n    PROFILE_SCOPE(19);'),
 ('void Detector::measureTip(Result &r,const cv::Mat &im,P center,P roiDirection,bool isReference) {','void Detector::measureTip(Result &r,const cv::Mat &im,P center,P roiDirection,bool isReference) {\n    PROFILE_SCOPE(17);')]
 }
 diff=[]
 for name,replaces in edits.items():
  old=(ROOT/'src/cpp/a'/name).read_text(encoding='utf8');new=old
  for a,b in replaces:
   assert new.count(a)==1,(name,a);new=new.replace(a,b)
  (SRC/name).write_text(new,encoding='utf8')
  diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='production/'+name,tofile='timer_copy/'+name))
 (OUT/'profile_instrumentation.diff').write_text(''.join(diff),encoding='utf8')
 (SRC/'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.20)
project(R03Profile LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
get_filename_component(ROOT "../../.." ABSOLUTE BASE_DIR "${CMAKE_CURRENT_SOURCE_DIR}")
add_library(R03Profile SHARED CrackV4.cpp)
target_compile_definitions(R03Profile PRIVATE CRACK_V4_EXPORTS CRACK_V4_PROFILE NOMINMAX)
target_compile_options(R03Profile PRIVATE /O2 /fp:precise /utf-8)
target_include_directories(R03Profile PRIVATE "${ROOT}/src/cpp/a/include" "${ROOT}/src/cpp/a/internal" "${ROOT}/third_party/opencv440/include")
target_link_libraries(R03Profile PRIVATE "${ROOT}/third_party/opencv440/lib/opencv_world440.lib")
''',encoding='utf8')
 print(SRC)
def replay():
 l=lib(PBUILD/'Release/R03Profile.dll');l.CrackV4ProfileMilliseconds.restype=C.POINTER(C.c_double)
 expected={};sides={}
 with (OUT/'snapshots.jsonl').open(encoding='utf8') as f:
  for line in f:
   r=json.loads(line)
   if r['variant_id']=='measured':expected[r['dataset_id'],r['frame_id']]=r['raw'];sides[r['dataset_id'],r['frame_id']]=r['stateonly']
 rows=[]
 for g,(mode,seq) in inventory().items():
  seq=seq[:LIMITS[g]];d=create(l,api.read(seq[0][0]),seq[0][1],mode)
  try:
   for i,(p,cp,h) in enumerate(seq):
    im=api.read(p);rr,rc,ms,raw,dbg=run(d,im,cp,i==0)
    if i==0:continue # Cached query is NOT a processing measurement.
    vals=list(l.CrackV4ProfileMilliseconds()[:24]);s=sides[g,i+1]
    row=dict(dataset_id=g,frame_id=i+1,image_w=im.shape[1],image_h=im.shape[0],raw_status=raw['status'],state_after=s['state_after'],tip_source=s['source'],api_wall_ms=ms,reported_api_ms=rr.api_ms,raw_equivalent=normalized(raw)==normalized(expected[g,i+1]),main_total_ms=vals[20],tip_total_ms=vals[17],local_reference_ms=vals[18],terminal_path_ms=vals[19],tip_motion_ms=vals[16],main_motion_ms=vals[0],seed_inclusive_ms=vals[1],response_inclusive_ms=vals[2],follow_inclusive_ms=vals[3],terminal_inclusive_ms=vals[4],root_inclusive_ms=vals[5],tip_response_prepost_residual_ms=vals[17]-vals[18]-vals[19],outer_residual_ms=ms-vals[20]-vals[17])
    # Only these disjoint categories can be added to account for full API time.
    row['main_other_ms']=vals[20]-vals[0]-vals[16]
    rows.append(row)
    if(i+1)%40==0:print(g,i+1,flush=True)
  finally:d.close()
  api.csvout(OUT/'performance_scopes.csv',rows)
 write('profile_identity.json',dict(dll=sha(PBUILD/'Release/R03Profile.dll'),source={p.name:sha(p) for p in SRC.glob('*') if p.is_file()},frames=len(rows),raw_mismatches=sum(not r['raw_equivalent'] for r in rows)))
if __name__=='__main__':generate() if '--generate' in sys.argv else replay()
