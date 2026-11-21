from common import *
from evaluate import SENTINELS
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
def main():
 lookup={(r['variant'],r['dataset_id'],int(r['frame_id'])):r for r in rows(OUT/'failure_first_divergence.csv')};out=[]
 for g,f in SENTINELS:
  fig,axs=plt.subplots(2,2,figsize=(14,7),constrained_layout=True)
  for i,tag in enumerate(['E1_BEAM','E0_BEAM']):
   t=read(OUT/'traces'/f'{tag}_{g}_{f}.json');fail=lookup[tag,g,f];sid=int(fail['scan_id']) if fail.get('scan_id') else max(0,len(t['scans'])-1)
   if (g,f)==('group_h',78):
    audit=next(r for r in read(OUT/'tests/group_h78_short_fragment_audit.json') if r['variant']==tag and r['columns']==2)
    supporting=next((s for s in audit['actual_sampling_strip_hits'] if s['candidates_near3']),None)
    if supporting:sid=supporting['scan_id']
   if not t['scans']:continue
   s=t['scans'][sid];raw=np.array(s.get('profile',[]));response=np.array(s.get('response',[]));x=np.arange(len(raw))-(len(raw)-1)/2
   axs[i,0].plot(x,raw,color='#555');axs[i,0].set_ylabel('Original grayscale');axs[i,0].set_title(f'{tag}: {g}/{f}, scan {sid}, step {s["step_index"]}')
   axs[i,1].plot(x,response,color='#2075aa');axs[i,1].axhline(3,color='#aa3300',ls='--',label='weak minimum3');axs[i,1].axhline(8,color='#559900',ls=':',label='strong8')
   for c in s.get('candidates',[]):axs[i,1].scatter(c['normal_offset'],c['strength'],marker='x',c='red')
   axs[i,1].set_title(fail['stage']);axs[i,1].legend()
   for ax in axs[i]:ax.set_xlabel('Normal offset in original pixels');ax.grid(alpha=.2)
   out.append(dict(dataset_id=g,frame_id=f,variant=tag,scan_id=sid,step=s['step_index'],reason=fail['stage'],trace=f'traces/{tag}_{g}_{f}.json'))
  fig.savefig(OUT/'galleries/images'/f'profile_{g}_{f}.png',dpi=140);plt.close(fig)
 save(OUT/'experiments/profile_plot_index.csv',out)
if __name__=='__main__':main()
