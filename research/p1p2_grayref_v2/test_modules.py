"""Synthetic semantics, determinism and numeric contracts, never real accuracy."""
from v2common import *
from algorithm import *
import traceback
def image_fixture():
 y,x=np.mgrid[:288,:640];return (195+(x*13+y*7)%17).astype(np.uint8)
def line(im,y,x0,x1,value):im[y-1:y+2,x0:x1]=value
def main():
 assert read(OUT/'gate0_complete.json')['passed'];records=[];rp=[[80.,40.],[80.,240.]];fixtures=[]
 base=image_fixture();cur=base.copy();line(cur,159,86,350,140);fixtures.append(('new_continuous',base,cur,rp,rp))
 fixtures.append(('same_image_visible',cur.copy(),cur,rp,rp))
 ref=base.copy();line(ref,100,86,350,130);c=cur.copy();line(c,100,86,350,130);fixtures.append(('existing_scratch_and_new_crack',ref,c,rp,rp))
 c=cur.copy();line(c,90,86,89,20);fixtures.append(('strong_spot_vs_continuous_69px',base,c,rp,rp))
 c=cur.copy();c[158:161,170:178]=base[158:161,170:178];fixtures.append(('eight_column_gap',base,c,rp,rp))
 for length in [1,2,3]:
  c=base.copy();line(c,159,86,86+length,170);fixtures.append((f'weak_fragment_{length}',base,c,rp,rp))
 c=base.copy();line(c,159,86,350,140);fixtures.append(('synthetic_scratch_only_negative',c.copy(),c,rp,rp))
 flat=np.full_like(base,200);fixtures.append(('all_zero_evidence',flat,flat,rp,rp))
 c=base.copy();line(c,110,86,350,140);line(c,170,86,350,140);fixtures.append(('competing_lines_tie',base,c,rp,rp))
 c=base.copy();line(c,159,86,640,140);fixtures.append(('right_boundary',base,c,rp,rp))
 shift=cur.copy();shift[:140]=np.roll(cur[:140],3,axis=1);shift[140:]=np.roll(cur[140:],-2,axis=1);fixtures.append(('different_upper_lower_motion',base,shift,rp,[[83.,41.],[78.,238.]]))
 fixtures.append(('invalid_points',base,cur,rp,[[80.,240.],[80.,40.]]))
 fixtures.append(('nan_point',base,cur,rp,[[float('nan'),40.],[80.,240.]]))
 def normal(v):
  if isinstance(v,dict):return {k:normal(x) for k,x in v.items() if not k.endswith('_ms')}
  if isinstance(v,list):return [normal(x) for x in v]
  return v
 for name,R,C,r,c in fixtures:
  result,a=detect(R,C,r,c);other,_=detect(R,C,r,c);assert normal(result)==normal(other),name
  if name in ['invalid_points','nan_point']:assert result['status']=='INPUT_ERROR'
  else:
   assert result['status']=='OK';assert len(result['results'])==5
   if name in ['same_image_visible','synthetic_scratch_only_negative','all_zero_evidence']:assert all(q['code']==0 for q in result['reference_quality'])
   if name=='all_zero_evidence':assert all(v['tip'] is None for v in result['results'])
   if name.startswith('weak_fragment_'):assert all(v['output_state']!='PROVISIONAL_OBSERVED' for v in result['results'])
   c1=next(v for v in result['results'] if v['mode']=='V2_COMBINED');t=next(v for v in result['results'] if v['mode']=='V2_TERMINAL');assert c1['seeds']==t['seeds'] and c1['paths']==t['paths'],'Terminal contaminated upstream modules'
   for v in result['results']:
    for p in v['paths']:
     for row in p['trace']:assert row[5]<=row[1]<row[6] and row[3]>=0
   if name=='strong_spot_vs_continuous_69px':
    seeds=c1['seeds'];assert any(abs(s['y']-90)<=1 for s in seeds) and any(abs(s['y']-159)<=1 for s in seeds)
  packed(OUT/'synthetic'/f'{name}.json.gz',result);records.extend(dict(fixture=name,mode=v['mode'],state=v['output_state'],tip=v['tip'],contract_pass=True,synthetic_negative=name=='synthetic_scratch_only_negative',negative_provisional_output=name=='synthetic_scratch_only_negative' and v['tip'] is not None) for v in result['results'])
 for n in range(-10000,10001):assert divround(n,1024)==(math.floor(n/1024+.5) if n>=0 else -math.floor(-n/1024+.5))
 for eps in [-1e-10,0,1e-10]:assert quant(19+eps)==19000000
 assert predict([[i,100] for i in range(12)],12,0)==102400
 assert predict([[i,100+i] for i in range(12)],12,0)==111*1024+divround(1024,5)
 save(OUT/'synthetic_contracts.csv',records);write(OUT/'gate1_complete.json',dict(passed=True,fixtures=len(fixtures),mode_cases=len(records),numeric_boundary_checks=20004,accuracy_claim=False,synthetic_negative_false_outputs=sum(r['negative_provisional_output'] for r in records)));print('GATE1 PASS',len(fixtures),flush=True)
if __name__=='__main__':main()
