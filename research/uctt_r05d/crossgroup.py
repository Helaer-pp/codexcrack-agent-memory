"""Six cross-group collages from existing, frozen per-frame evidence images."""
import zipfile,re
from PIL import Image
from common import *
def main():
 pairs=[(('ct2',395),('ct3',65)),(('group_h',78),('ct3',65)),(('group_a',504),('ct3',65)),(('ct2',8),('group_h',96)),(('group_c',528),('ct2',395)),(('three_point_bend',503),('group_a',67))]
 links=[]
 for i,pair in enumerate(pairs,1):
  canvas=Image.new('RGB',(1600,2000))
  for j,(g,f) in enumerate(pair):
   require(g,'comparison');canvas.paste(Image.open(OUT/'images'/f'{g}__{f:06d}.jpg'),(0,j*1000))
  name=f'crossgroup_{i:02d}.jpg';canvas.save(OUT/'images'/name,quality=92);links.append(f'<a href="images/{name}">{pair[0][0]}/{pair[0][1]} ↔ {pair[1][0]}/{pair[1][1]}</a>')
 page=OUT/'R05D_G0_G5_Failure_Gallery.html';content=page.read_text(encoding='utf8');content=re.sub(r'<p>六组关键对照拼图：.*?</p>','',content);start=content.index('<section ');content=content[:start]+'<p>六组关键对照拼图：'+' · '.join(links)+'</p>'+content[start:];page.write_text(content,encoding='utf8')
 # Explain unevaluated states without changing the frozen stage classifier.
 per=rows(OUT/'tip_reachability_per_frame.csv')
 for r in per:
  if r['annotation_state']=='VISIBLE' and r['first_failure_stage']=='INDETERMINATE':
   t=read(OUT/'traces'/f"{r['dataset_id']}__{int(r['frame_id']):06d}.json")
   if t['terminal_cause']=='declared_clean_reference_skip':r['missing_internal_state']='Reference declared clean: measureTip returns before score/DP; cached GetBaseline is not current-frame inference. No endpoint evidence exists to query.'
 save(OUT/'tip_reachability_per_frame.csv',per)
 audited={(r['dataset_id'],r['frame_id']):json.loads(r['peak_rejection_counts']) for r in rows(OUT/'terminal_audit_trace.csv')}
 candidates=rows(OUT/'candidate_trace.csv')
 for c in candidates:
  if c['stage']=='not_visited_after_rank_stop' and 'competing_disjoint_paths' in audited[c['dataset_id'],c['frame_id']]:c['stage']='not_visited_after_ambiguity_return'
 save(OUT/'candidate_trace.csv',candidates)
 report=OUT/'root_cause_report.md';body=report.read_text(encoding='utf8');note='## 原始trace默认值说明'
 if note not in body:body+='\n'+note+'\n\n原生Peak默认stage字符串为not_visited_after_rank_stop，表示尚未访问；如果前一个候选因竞争路径直接return，实际也未发生排名门。原始JSON保持不改，candidate_trace.csv保留raw_trace_stage并将该情形明确写为not_visited_after_ambiguity_return。未执行的hits/tail/shared导出为null，不能把默认0理解为测得0支持。局部参考votes<2时agree尚未执行，local_reference_vote_trace.csv中为null。\n'
 report.write_text(body,encoding='utf8')
 files=[p for p in OUT.rglob('*') if p.is_file() and (p.parent.name in ['images','source_evidence','traces'] or p.parent==OUT and p.suffix in ['.md','.html','.csv','.jpg'])]
 with zipfile.ZipFile(OUT/'R05D_visual_evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,p.relative_to(OUT).as_posix())
 qa=read(OUT/'visual_qa.json');qa.update(crossgroup_montages=6,images=246,zip_entries=len(files));write(OUT/'visual_qa.json',qa)
 print('CROSS-GROUP MONTAGES AND COMPLETE ZIP READY')
if __name__=='__main__':main()
