"""Read-only audit of user labels; preserve an immutable JSON snapshot first."""
from pathlib import Path
from datetime import datetime
import csv,json,hashlib,collections,math,zipfile,html
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0,str(ROOT/'src/python'))
from crackv4.dataset_policy import filter_rows
PACKAGE=ROOT/'output/runs/uctt_r05_prelabel_difference_20261111_r01/R05_LabelMe_Annotation_Package'
OUT=ROOT/'output/runs'/('r05_annotation_audit_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
ALLOWED={'crack_path':{'linestrip'},'crack_tip':{'point'},'uncertain_region':{'polygon'},'interference':{'linestrip','polygon'},'branch_path':{'linestrip'}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def csvsave(p,rs):
 if not rs:return
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rs for k in r)));w.writeheader();w.writerows(rs)
def distance_to_polyline(point,path):
 p=np.array(point,float);a=np.array(path[:-1],float);b=np.array(path[1:],float);v=b-a;t=np.clip(((p-a)*v).sum(1)/np.maximum((v*v).sum(1),1e-12),0,1)
 return float(np.linalg.norm(p-(a+t[:,None]*v),axis=1).min())
def render(image,data,key,out):
 # Render an ROI enclosing human shapes plus context; source pixels left intact.
 pts=[p for s in data.get('shapes',[]) for p in s.get('points',[]) if len(p)==2 and all(isinstance(x,(int,float)) and math.isfinite(x) for x in p)]
 w,h=image.size
 if pts:
  arr=np.array(pts);lo=arr.min(0);hi=arr.max(0);pad=max(55,min(180,(hi-lo).max()*.12));box=(max(0,int(lo[0]-pad)),max(0,int(lo[1]-pad)),min(w,int(hi[0]+pad)),min(h,int(hi[1]+pad)))
 else:box=(0,0,w,h)
 if box[2]<=box[0] or box[3]<=box[1]:box=(0,0,w,h)
 crop=image.crop(box).convert('RGB');scale=min(2.,1100/crop.width,550/crop.height);size=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)));base=crop.resize(size)
 overlay=base.copy();draw=ImageDraw.Draw(overlay);colors={'crack_path':'#00ee77','crack_tip':'#ff3333','uncertain_region':'#ffcc00','interference':'#00bbff','branch_path':'#cc66ff'}
 for s in data.get('shapes',[]):
  ps=[((p[0]-box[0])*scale,(p[1]-box[1])*scale) for p in s.get('points',[])];color=colors.get(s.get('label'),'#ff00ff');typ=s.get('shape_type')
  if typ=='point' and ps:
   x,y=ps[0];draw.ellipse((x-5,y-5,x+5,y+5),outline=color,width=2);draw.line((x-8,y,x+8,y),fill=color,width=1);draw.line((x,y-8,x,y+8),fill=color,width=1)
  elif typ=='circle' and len(ps)==2:
   x,y=ps[0];r=math.dist(*ps);draw.ellipse((x-r,y-r,x+r,y+r),outline=color,width=2)
  elif len(ps)>1:draw.line(ps+([ps[0]] if typ=='polygon' else []),fill=color,width=2)
 font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);panel=Image.new('RGB',(max(800,size[0]),size[1]*2+94),'#18222b');d=ImageDraw.Draw(panel);d.text((12,7),key+' | human annotation audit | original ROI '+str(box),fill='white',font=font);panel.paste(base,(0,33));panel.paste(overlay,(0,size[1]+60));d.text((12,size[1]+36),'Green: path | Red: tip | Yellow: uncertainty (human labels, not algorithm predictions)',fill='white',font=font);panel.save(out,quality=92)
 return box
def main():
 OUT.mkdir(exist_ok=False);(OUT/'overlays').mkdir();manifest=filter_rows(list(csv.DictReader((PACKAGE/'selection_manifest.csv').open(encoding='utf-8-sig'))),'annotation_qc',uses_annotations=True);results=[];issues=[];sourcehashes={};snapshots={};geometries=[]
 with zipfile.ZipFile(OUT/'human_annotations_snapshot.zip','w',zipfile.ZIP_DEFLATED) as z:
  for r in manifest:
   j=PACKAGE/r['selected_json']
   if j.exists():data=j.read_bytes();snapshots[r['selected_json']]=data;sourcehashes[r['selected_json']]=hashlib.sha256(data).hexdigest();z.writestr(r['selected_json'],data)
  for name in ['selection_manifest.csv','annotation_meta.csv','annotation_schema.json']:
   if (PACKAGE/name).exists():z.write(PACKAGE/name,name)
 for r in manifest:
  g,f=r['dataset_id'],r['frame_id'];key=f'{g}__frame_{int(f):06d}';p=PACKAGE/r['selected_image'];jp=r['selected_json'];local=[]
  def flag(level,code,note):local.append(dict(dataset_id=g,frame_id=int(f),split=r['split'],severity=level,code=code,note=note,json_path=str(PACKAGE/jp),preview='overlays/'+key+'.jpg'))
  image=None;data={};counts=collections.Counter();tips=[];paths=[];uncertain=[]
  if not p.exists():flag('ERROR','MISSING_IMAGE','Original image file missing')
  else:
   if sha(p)!=r['source_sha256']:flag('ERROR','SOURCE_HASH_CHANGED','Original image bytes changed')
   try:image=Image.open(p);image.load();w,h=image.size
   except Exception as e:flag('ERROR','IMAGE_DECODE',str(e))
  if jp not in snapshots:flag('ERROR','MISSING_JSON','No saved JSON; do not infer no-visible-crack')
  else:
   try:data=json.loads(snapshots[jp].decode('utf8'))
   except Exception as e:flag('ERROR','JSON_PARSE',str(e))
  if data and image:
   if (data.get('imageWidth'),data.get('imageHeight'))!=(w,h):flag('ERROR','DIMENSION_MISMATCH','JSON dimensions differ from original')
   if ((PACKAGE/jp).parent/data.get('imagePath','')).resolve()!=p.resolve():flag('ERROR','IMAGE_PATH_MISMATCH',str(data.get('imagePath')))
   shapes=data.get('shapes',[]);flags=data.get('flags',{})
   if not isinstance(shapes,list):flag('ERROR','SHAPES_NOT_LIST','Invalid shapes');shapes=[]
   for index,s in enumerate(shapes):
    label=s.get('label');typ=s.get('shape_type');counts[label]+=1;points=s.get('points',[])
    if label not in ALLOWED or typ not in ALLOWED.get(label,set()):flag('ERROR','UNSUPPORTED_LABEL_OR_TYPE',f'shape {index+1}: {label}/{typ}; expected {sorted(ALLOWED.get(label,set()))}')
    minimum={'point':1,'linestrip':2,'polygon':3,'circle':2}.get(typ,1)
    if len(points)<minimum or (typ=='point' and len(points)!=1):flag('ERROR','POINT_COUNT',f'shape {index+1}: {len(points)} points')
    valid=all(len(pt)==2 and all(isinstance(v,(int,float)) and math.isfinite(v) for v in pt) and 0<=pt[0]<w and 0<=pt[1]<h for pt in points)
    if not valid:flag('ERROR','OUT_OF_BOUNDS_OR_NONFINITE',f'shape {index+1}')
    if not valid:continue
    if label=='crack_tip' and typ=='point' and len(points)==1:tips.append(points[0])
    if label=='crack_path' and typ=='linestrip' and len(points)>=2:
     paths.append(points);length=float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum())
     if length<1:flag('REVIEW','DEGENERATE_PATH',f'shape {index+1}: length {length:.3f}px')
    if label=='uncertain_region':uncertain.append(points)
   negative=flags.get('no_visible_crack',False)
   if not isinstance(negative,bool):flag('ERROR','FLAG_NOT_BOOL','no_visible_crack must be boolean')
   if negative and any(counts[k] for k in ['crack_tip','crack_path','branch_path']):flag('ERROR','NEGATIVE_WITH_VISIBLE_LABEL','no_visible_crack conflicts with visible crack')
   if len(tips)>1:flag('REVIEW','MULTIPLE_MAIN_TIPS',f'{len(tips)} crack_tip and {len(paths)} crack_path; main-tip identity/grouping must be clarified')
   if len(tips)==1 and not paths:flag('REVIEW','TIP_WITHOUT_PATH','Visible point has no crack_path')
   if paths and not tips and not uncertain:flag('REVIEW','PATH_WITHOUT_TIP_OR_UNCERTAINTY','Path without a visible tip or uncertainty explanation')
   if not shapes and not negative:flag('ERROR','UNANNOTATED','Empty annotation is not a negative sample')
   for ti,tip in enumerate(tips):
    if paths:
     line_distance=min(distance_to_polyline(tip,line) for line in paths);end_distance=min(math.dist(tip,p) for line in paths for p in [line[0],line[-1]])
     geometries.append(dict(dataset_id=g,frame_id=int(f),tip_index=ti+1,tip_x=tip[0],tip_y=tip[1],nearest_path_distance_px=line_distance,nearest_path_endpoint_distance_px=end_distance))
     if end_distance>10:flag('REVIEW','TIP_FAR_FROM_PATH_ENDPOINT',f'tip {ti+1}: nearest path endpoint {end_distance:.2f}px; nearest line {line_distance:.2f}px. 10px is review tolerance, not a crack truth rule')
   status='NO_VISIBLE_CRACK' if negative else 'MULTIPLE_MAIN_TIPS' if len(tips)>1 else 'VISIBLE_PATH_AND_TIP' if len(tips)==1 and paths else 'UNCERTAIN' if uncertain else 'PARTIAL'
  else:status='MISSING_OR_INVALID'
  if image:
   render(image,data,key,OUT/'overlays'/(key+'.jpg'));image.close()
  issues.extend(local);results.append(dict(dataset_id=g,frame_id=int(f),split=r['split'],status=status,crack_path_count=counts['crack_path'],crack_tip_count=counts['crack_tip'],uncertain_count=counts['uncertain_region'],errors=sum(i['severity']=='ERROR' for i in local),reviews=sum(i['severity']=='REVIEW' for i in local),json_sha256=sourcehashes.get(jp,''),selected_json=jp,preview='overlays/'+key+'.jpg'))
  if len(results)%20==0:print('audited',len(results),flush=True)
 csvsave(OUT/'frame_audit.csv',results);csvsave(OUT/'issues.csv',issues);csvsave(OUT/'tip_path_geometry.csv',geometries);write(OUT/'annotation_input_hashes.json',sourcehashes)
 # Detect concurrent user edits, without overwriting their files.
 changed=[j for j,h in sourcehashes.items() if not (PACKAGE/j).exists() or sha(PACKAGE/j)!=h]
 summary=dict(output=str(OUT),expected=len(manifest),excluded_groups=['group_x'],saved_json=len(snapshots),status_counts=dict(collections.Counter(r['status'] for r in results)),issue_counts=dict(collections.Counter(i['code'] for i in issues)),error_frames=sum(r['errors']>0 for r in results),review_frames=sum(r['reviews']>0 for r in results),geometry_clean_visible=sum(r['status']=='VISIBLE_PATH_AND_TIP' and not r['errors'] and not r['reviews'] for r in results),concurrent_edits=changed,annotation_files_modified=False)
 write(OUT/'summary.json',summary)
 cards=[]
 for r in sorted(results,key=lambda r:(-(r['errors']+r['reviews']),r['dataset_id'],r['frame_id'])):
  text='; '.join(i['code']+': '+i['note'] for i in issues if i['dataset_id']==r['dataset_id'] and i['frame_id']==r['frame_id'])
  cards.append(f'<section><h2>{r["dataset_id"]} / {r["frame_id"]} — {r["status"]}</h2><p>{html.escape(text)}</p><a href="{r["preview"]}"><img loading="lazy" src="{r["preview"]}"></a></section>')
 (OUT/'annotation_review.html').write_text('<!doctype html><meta charset="utf-8"><title>人工标注检查</title><style>body{font:16px system-ui;margin:24px;background:#eef2f4}section{padding:16px;background:white;margin-bottom:24px}img{max-width:1100px;width:100%}</style><h1>人工标注检查：原图局部 / 人工标注叠加</h1><p>仅检查标注，未修改任何人工JSON。错误/待复核帧排在前面。绿色路径、红色尖端、黄色不确定区域；图像为导航裁剪，原始坐标和像素文件不变。</p>'+''.join(cards),encoding='utf8')
 print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
