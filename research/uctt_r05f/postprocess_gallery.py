from common import *
p=OUT/'galleries/index.html';s=p.read_text(encoding='utf8');marker='<p id="final-acceptance">'
extra=marker+'最终：指定R02/R05D研究基线S0 PASS；S1 FAIL；S2–S6 BLOCKED，生产未改。历史发布件与研究构建本来就是不同版本，不能混用精度指标。<a href="../baseline_scope.md">基线身份说明</a><a href="images/group_h78_response_segment_failure.jpg">开发组H78原生弱片段失效图</a><a href="images/final_status.jpg">最终状态卡</a></p>'
if marker not in s:s=s.replace('<label>组',extra+'<label>组',1)
p.write_text(s,encoding='utf8');print('Gallery links complete')
