"""Startup-inclusive frozen CLI timing on deterministic first/middle/last DEVELOPMENT frames."""
from common import *
from python_replay import stage,argv
import subprocess,time
def main():
 measurements=[];manifest=rows(OUT/'inputs/manifest.csv')
 for g in DEV:
  require(g,'development');seq=[r for r in manifest if r['group']==g];folder=OUT/'tests/cli_timing'/g;folder.mkdir(parents=True,exist_ok=True);ref=folder/'reference.bmp';cur=folder/'current.bmp';stage(seq[0]['reference'],ref)
  for i in [0,len(seq)//2,len(seq)-1]:
   row=seq[i];f=int(row['frame_id']);stage(row['current'],cur);sub=folder/str(f);sub.mkdir(exist_ok=True);cmd=[sys.executable,*argv(row,ref,cur,sub)];tick=time.perf_counter();r=subprocess.run(cmd,capture_output=True,text=True,errors='replace');wall=(time.perf_counter()-tick)*1000;(sub/'cli_stdout.txt').write_text(r.stdout,encoding='utf8');(sub/'cli_stderr.txt').write_text(r.stderr,encoding='utf8');assert r.returncode==0
   equal=rows(sub/'summary_results.csv')==rows(OUT/'py_runs'/g/str(f)/'summary_results.csv');assert equal;measurements.append(dict(group=g,frame_id=f,full_cli_wall_ms=wall,source_reported_io_export_render_ms=read(sub/'metadata.json')['runtime_seconds_total_including_io_and_render']*1000,six_summary_rows_equal=equal,source_sha256=sha(FROZEN),selection='first/middle/last by sequence order, no GT selection',concurrency='validation workers may be active; not isolated deployment benchmark'));print('CLI',g,f,round(wall,2),flush=True)
 save(OUT/'tables/full_cli_timing_samples.csv',measurements)
if __name__=='__main__':main()
