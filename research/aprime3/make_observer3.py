"""Reproducible observer-only instrumentation; no branch or score is changed."""
from common3 import *
p=ROOT/'research/aprime2/src/native_shadow/CrackV4_ap2.cpp';s=p.read_text(encoding='utf8')
def replace(a,b):
 global s
 assert s.count(a)==1,(a[:60],s.count(a));s=s.replace(a,b)
replace('    int ap2_count=0;','    std::array<double,9> ap3_seed{};\n    int ap2_count=0;')
replace('    ap2_count=0; ap2_overflow=false;','    ap2_count=0; ap2_overflow=false; ap3_seed.fill(0.);')
replace('    int minimum = std::max(6, rnd(.025 * spacing));\n    if ((int)supported.size() < minimum || gain < minimum * 1.5)\n        return false;',
'''    int minimum = std::max(6, rnd(.025 * spacing));
    ap3_seed[0]=1; ap3_seed[1]=double(supported.size()); ap3_seed[2]=minimum;
    ap3_seed[3]=gain; ap3_seed[4]=double(ridgep.size());
    if ((int)supported.size() < minimum || gain < minimum * 1.5)
        return false;''')
replace('    if (lastidx - first < minimum)\n        return false;','    ap3_seed[0]=2; ap3_seed[5]=lastidx-first;\n    if (lastidx - first < minimum)\n        return false;')
replace('    if (double(good) / (startup_end - first) < .6 || maxstart < 6)\n        return false;',
'''    ap3_seed[0]=3; ap3_seed[6]=double(good)/(startup_end-first); ap3_seed[7]=maxstart; ap3_seed[8]=cfg.score;
    if (double(good) / (startup_end - first) < .6 || maxstart < 6)
        return false;
    ap3_seed[0]=4;''')
s+='''
extern "C" __declspec(dllexport) int AP3CopySeed(CrackV4Handle h,double* out,int capacity) {
 if(!h || !out || capacity<9) return -1;
 auto &d=*static_cast<Detector*>(h); std::lock_guard<std::mutex> lock(d.mutex);
 std::copy(d.ap3_seed.begin(),d.ap3_seed.end(),out); return 9;
}
'''
write(SOURCE/'src/CrackV4_ap3_observer.cpp',s)
save(RUN/'00_audit/observer_instrumentation.json',dict(parent_sha256=sha(p),child_sha256=sha(SOURCE/'src/CrackV4_ap3_observer.cpp'),purpose='SEED_GATE_OBSERVATION_ONLY',fields=['stage','support_count','minimum','gain','ridge_size','contiguous_span','startup_fraction','startup_peak','score_threshold']))
