from common import ROOT
for filename,old,new in [('AGENTS.md','- Latest work is R05E research','- Previous work is R05E research'),('README.md','最新诊断见 [R05E问题结论]','上一轮诊断见 [R05E问题结论]')]:
 p=ROOT/filename;s=p.read_text(encoding='utf8');assert s.count(old)==1;p.write_text(s.replace(old,new,1),encoding='utf8')
print('Historical R05E entries labeled as previous round')
