from common3 import *
import shutil
# Uses the already-built read-only observer, not a substituted production library.
env=os.environ.copy();env['CRACK_AP2_RUN']=RUN.name
subprocess.run([sys.executable,'-B',str(ROOT/'research/aprime2/timing.py')],cwd=ROOT,env=env,check=True)
for src,dst in [(RUN/'03_A_candidate_audit/Gate0_final_native.csv',RUN/'03_exposed_regression/A_Aprime3_3035_equalities.csv'),
                (RUN/'03_A_candidate_audit/Gate0_final_native.json',RUN/'03_exposed_regression/Gate0.json'),
                (RUN/'07_native_timing/all_frames.csv',RUN/'06_native_performance/latency_per_frame.csv'),
                (RUN/'07_native_timing/summary.json',RUN/'06_native_performance/latency_summary_by_group.json')]:shutil.copyfile(src,dst)
save(RUN/'06_native_performance/15hz_gate.json',dict(full_native_Aprime3='NOT_TESTED',scope='A plus unchanged native tile observer; candidate/reference/decision not native',
    isolated_from_media_and_DEV=True,production_changed=False))
print('AP3 NATIVE GATE0 DONE',flush=True)
