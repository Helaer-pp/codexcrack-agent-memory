from common import *
import zipfile, difflib

guard()
ident = guard()
save(RUN/'01_protocol_and_freeze/baseline_identity.json', ident)
save(RUN/'01_protocol_and_freeze/pre_DEV_protocol.json', dict(
    utc=utc(), role='EXPOSED_DEV_RESEARCH_SHADOW', production='KEEP_FROZEN_A',
    flags=3572, policy=1, terminal=1, refine=True, threads=4, K=12,
    activation_pairs_min=12, backgrounds_min=3, correct_radius_px=8,
    strong_false_tail_error_px=32, catastrophic_px=160, rejection_loss=32, loss_cap=64,
    selection_gate='Activation + candidate recall + independently validated disputed intervals',
    test_status='NOT_STARTED', real_GT=None, monotonic_prior=False,
    output_directory=str(RUN), no_runtime_group_or_GT=True))
records=[]
for zpath in [ROOT/'output/aprime_20261105/run01/A_prime_source_results_reports.zip',
              ROOT/'archive/packages/C2_results_source_reports.zip',
              ROOT/'archive/packages/CrackV4_C_截图数据_轻量版.zip']:
    rec=dict(path=str(zpath.relative_to(ROOT)), exists=zpath.exists())
    if zpath.exists():
        rec.update(sha256=sha(zpath), bytes=zpath.stat().st_size)
        with zipfile.ZipFile(zpath) as z:
            listing=z.namelist(); rec['members']=len(listing)
            selected=[n for n in listing if n.endswith(('.md','.py')) and any(k in n.lower() for k in
                      ['candidate_union','path_ownership','endpoint_decision','summary','executive','failure'])]
            rec['read_members']=selected
            for j,n in enumerate(selected):
                dest=RUN/'01_protocol_and_freeze/history_readonly'/zpath.stem/f'{j:03d}_{Path(n).name}'
                write(dest,z.read(n).decode('utf-8-sig',errors='replace'))
    records.append(rec)
save(RUN/'01_protocol_and_freeze/material_inventory.json',records)
frozen=ROOT/'baseline/frozen_a/src/CrackV4.cpp'
original=frozen.read_text(encoding='utf8'); clone=original
def replace(a,b):
    global clone
    assert clone.count(a)==1, (a[:70],clone.count(a))
    clone=clone.replace(a,b)
replace('class Detector {', '''// Independent bounded observer. No writes to A state, DP or thresholds.
struct AP2Stop { double x,y,dx,dy,gain,support,median,threshold,invalid; int path_size,dp_size; };
class Detector {''')
replace('    Config cfg;\n    double brightness_minus', '''    Config cfg;
    std::array<AP2Stop,256> ap2_stops{};
    int ap2_count=0;
    bool ap2_overflow=false;
    double brightness_minus''')
replace('    if(debug()) { debug_tiles.clear(); debug_images.clear(); starts_count=0; }',
'''    ap2_count=0; ap2_overflow=false;
    if(debug()) { debug_tiles.clear(); debug_images.clear(); starts_count=0; }''')
replace('        if (supported.size() < 3 || gain < 4) {', '''        // Reuse the existing tile/path samples. Fixed 256 records, O(tile count).
        if (ap2_count < int(ap2_stops.size())) {
            P cp=current(o), cd=rotation*d;
            double med=0; if (!ss.empty()) { auto tmp=ss; auto mid=tmp.begin()+tmp.size()/2;
                std::nth_element(tmp.begin(),mid,tmp.end()); med=*mid; }
            ap2_stops[ap2_count++]={cp.x,cp.y,cd.x,cd.y,gain,
                ss.empty()?0.:double(supported.size())/ss.size(),med,t.threshold,
                1.-cv::mean(t.valid)[0]/255.,int(path.size()),int(ridgep.size())};
        } else ap2_overflow=true;
        if (supported.size() < 3 || gain < 4) {''')
clone+='''
// Research-only export; production ABI/source unchanged. Flat rows, 11 doubles.
extern "C" __declspec(dllexport) int AP2CopyStops(CrackV4Handle h, double* out, int capacity) {
    if(!h) return -1;
    auto &d=*static_cast<Detector*>(h); std::lock_guard<std::mutex> lock(d.mutex);
    if(!out) return d.ap2_count;
    int n=std::min(capacity,d.ap2_count);
    for(int i=0;i<n;++i) { auto &v=d.ap2_stops[i]; double *p=out+11*i;
        p[0]=v.x;p[1]=v.y;p[2]=v.dx;p[3]=v.dy;p[4]=v.gain;p[5]=v.support;
        p[6]=v.median;p[7]=v.threshold;p[8]=v.invalid;p[9]=v.path_size;p[10]=v.dp_size; }
    return d.ap2_overflow?-n-1:n;
}
'''
write(SOURCE/'src/native_shadow/CrackV4_ap2.cpp',clone)
write(RUN/'01_protocol_and_freeze/native_instrumentation.diff',''.join(difflib.unified_diff(
      original.splitlines(True),clone.splitlines(True),fromfile='frozen_A',tofile='shadow_A')))
save(RUN/'01_protocol_and_freeze/initial_source_hashes.json',{
    str(p.relative_to(ROOT)):sha(p) for p in SOURCE.rglob('*') if p.is_file()})
print('BOOTSTRAP',RUN,flush=True)
