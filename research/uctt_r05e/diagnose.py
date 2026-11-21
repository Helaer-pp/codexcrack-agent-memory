"""Separated stateless native control, followed by offline label neighborhoods."""
from common import *
from compare import local,original
import ctypes as C,os,numpy as np,zipfile
def main():
 assert read(OUT/'B1_dev_complete.json')['status']=='PASS'
 directory=os.add_dll_directory(str(ROOT/'third_party/opencv440/bin'));lib=C.CDLL(str(BUILD/'Release/EVIDENCE_DP_PROBE.dll'))
 lib.R05ECurrentProbe.argtypes=[C.c_void_p,C.c_void_p,C.c_int,C.c_int];lib.R05ECurrentProbe.restype=C.c_char_p
 lib.R05EProbeGain.argtypes=[C.POINTER(C.c_int)]*3;lib.R05EProbeGain.restype=C.c_void_p
 controls=[];snapshots={}
 # Native phase: all inputs are saved pixel evidence, no human coordinates.
 for r in filter_rows(rows(OUT/'selected_frames.csv'),'development'):
  g,f=r['dataset_id'],int(r['frame_id']);require(g,'development');name=f'{g}__{f:06d}';t=read(OUT/'traces'/f'B1_{name}.json')
  with np.load(OUT/'maps'/f'{name}.npz') as m:
   if 'currentEvidence' not in m:continue
   score=np.ascontiguousarray(m['currentEvidence']);im=np.ascontiguousarray(m['current']);control=json.loads(lib.R05ECurrentProbe(score.ctypes.data,im.ctypes.data,*score.shape))
   expected={(tuple(c['xy']),c['gain']) for c in t['evidence']['candidates'] if 'current' in c['source_channel']}
   actual={(tuple(c['xy']),c['gain']) for c in control['peaks']}
   assert expected==actual,(name,'CURRENT_RECURRENCE_CONTROL_MISMATCH')
   h,w,stride=[C.c_int() for _ in range(3)];p=lib.R05EProbeGain(C.byref(h),C.byref(w),C.byref(stride));raw=C.string_at(p,h.value*stride.value);gain=np.ndarray((h.value,w.value),np.float32,buffer=raw,strides=(stride.value,4)).copy()
   np.savez_compressed(OUT/'maps'/f'{name}__current_dp.npz',gain=gain)
   controls.append(dict(dataset_id=g,frame_id=f,status='PASS',current_peaks=len(expected),trace_peaks=len(actual),scope='Exact original distalLine recurrence on frozen currentEvidence, no GT',map_sha=sha(OUT/'maps'/f'{name}.npz')))
 save(OUT/'current_dp_control.csv',controls)
 # Offline comparison phase. Every control snapshot above is already frozen.
 metrics=[];old={(r['dataset_id'],int(r['frame_id'])):r for r in rows(OUT/'evaluation_B1_dev.csv')}
 with zipfile.ZipFile(R05/'human_annotations_six_groups_snapshot.zip') as z:
  for r in filter_rows(rows(OUT/'selected_frames.csv'),'development'):
   g,f=r['dataset_id'],int(r['frame_id']);require(g,'comparison',uses_annotations=True);name=f'{g}__{f:06d}';file=OUT/'maps'/f'{name}__current_dp.npz'
   if not file.exists():continue
   label=json.loads(z.read(r['selected_json']));tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip']
   if len(tips)!=1:continue
   t=read(OUT/'traces'/f'B1_{name}.json');q=local(tips,t)[0]
   with np.load(file) as m:gain=m['gain']
   with np.load(OUT/'maps'/f'{name}.npz') as m:score=m['currentEvidence']
   h,w=score.shape;yy,xx=np.ogrid[:h,:w];near=(xx-q[0])**2+(yy-q[1])**2<=100
   support=score>=3;qualified=(gain>=12)&support;ymax=np.zeros(score.shape,bool);forward=np.zeros(score.shape,bool)
   ymax[5:h-5,4:w-10]=(gain[5:h-5,4:w-10]>=gain[4:h-6,4:w-10])&(gain[5:h-5,4:w-10]>=gain[6:h-4,4:w-10])
   forward[5:h-5,4:w-10]=gain[5:h-5,4:w-10]>np.maximum.reduce([gain[4:h-6,5:w-9],gain[5:h-5,5:w-9],gain[6:h-4,5:w-9]])
   row=dict(dataset_id=g,frame_id=f,current_support_pixels10=int(np.sum(support&near)),support_and_gain12_pixels10=int(np.sum(qualified&near)),plus_ymax_pixels10=int(np.sum(qualified&ymax&near)),plus_forward_stop_pixels10=int(np.sum(qualified&ymax&forward&near)),max_current_score10=float(score[near].max()) if np.any(near) else None,max_current_gain10=float(gain[near].max()) if np.any(near) else None,first_failure_stage=old[g,f]['first_failure_stage'],reference_unavailability_not_veto=True,denominator='VISIBLE development selections with computed maps; 10px original pixel neighborhoods')
   row['first_current_peak_filter_loss']='no_current_support' if row['current_support_pixels10']==0 else 'gain_below12_at_supported_pixels' if row['support_and_gain12_pixels10']==0 else 'not_y_local_maximum' if row['plus_ymax_pixels10']==0 else 'not_forward_stopping_maximum' if row['plus_forward_stop_pixels10']==0 else 'has_current_peak'
   metrics.append(row)
 save(OUT/'current_peak_filter_diagnosis.csv',metrics)
 write(OUT/'current_dp_probe_manifest.json',dict(control_cases=len(controls),comparison_cases=len(metrics),dll_sha=sha(BUILD/'Release/EVIDENCE_DP_PROBE.dll'),source_sha=sha(ROOT/'research/uctt_r05e/probe.cpp'),offline_only=True,no_new_runtime_rules=True))
 print('CURRENT DP CONTROL',len(controls),'PASS; offline diagnosed',len(metrics),flush=True)
if __name__=='__main__':main()
