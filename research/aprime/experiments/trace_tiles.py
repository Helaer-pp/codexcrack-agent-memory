from common_ap import *
guard();cv2.setNumThreads(1);lib=api.base_library();lib.CrackV4LastDebugJson.argtypes=[api.C.c_void_p];lib.CrackV4LastDebugJson.restype=api.C.c_char_p
mm=rows(O/'00_protocol/inputs_manifest.csv');checks=[];tiles=[]
for g,keys in [('ct2',{6,18,84}),('group_x',{51,473})]:
 rr=[r for r in mm if r['dataset_alias']==g];pr,pj,pp=native(ROOT/f'data/frozen_a_replay/{g}_A');ref=read(rr[0]['input_image']);engine=api.Baseline(ref,json.loads(rr[0]['points']),mode=rr[0]['mode'],flags=3573)
 for i,r in enumerate(rr):
  a=engine.run(ref if i==0 else read(r['input_image']),json.loads(r['points']),is_reference=i==0);same=api.normalized(a['native'])==api.normalized(pj[i])and np.array_equal(np.asarray(a['formal']['raw_path']).reshape(-1,2),pp[i])
  assert same,(g,i,'DIAGNOSTICS_CHANGED_A');checks.append(dict(group=g,frame_id=i,diagnostic_flags=3573,formal_flags=3572,same_native_state_and_float64_path=True))
  if i in keys:
   debug=json.loads(lib.CrackV4LastDebugJson(engine.handle));save(O/f'01_audit/traces/{g}_{i:04d}.json',debug)
   for j,t in enumerate(debug['tiles']):tiles.append(dict(group=g,frame_id=i,tile_id=j,origin=t['origin'],direction=t['direction'],dp_points=len(t['dp']),dp_last=t['dp'][-1]if t['dp']else None,threshold=t['threshold'],noise_tail=t['noise_tail'],invalid_fraction=t['invalid_fraction'],formal_stop=a['native']['stop_reason'],formal_confirmed=a['formal']['confirmed_tip'],legacy_tip=a['native']['terminal_audit']['legacy_tip'],shadow_tip=a['native']['terminal_audit']['shadow_tip'],temporal_hits=a['native'].get('temporal_hits'),endpoint_hits=a['native']['terminal_audit']['endpoint_hits']))
   print('TRACE',g,i,len(debug['tiles']),flush=True)
 engine.close();csvout(O/'01_audit/diagnostic_trace_equivalence.csv',checks);csvout(O/'01_audit/native_tile_and_confirmation_audit.csv',tiles)
guard();save(O/'01_audit/diagnostic_trace_complete.json',dict(compared_frames=len(checks),differences=0))
