# 候选召回与预算

|组|全帧|可见/不确定|原A observed|原A ≤5px|current10|raw10|retained10|预算误删10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|group_a (DEVELOPMENT)|551|19/1|4|2|19|19|18|1|
|ct2 (DEVELOPMENT)|468|20/0|14|0|18|15|8|7|
|group_h (DEVELOPMENT)|410|18/2|16|0|18|14|10|4|
|ct3 (DEVELOPMENT)|136|19/1|18|9|19|19|19|0|
|group_c (VALIDATION_ONLY)|562|20/0|18|6|19|19|16|3|
|three_point_bend (VALIDATION_ONLY)|520|15/5|3|0|15|10|6|4|

固定容差3/5/10完整数字见group_summary.csv。raw为当前与legacy峰并集，retained仅代表节点坐标；合并从属节点虽映射retained_id，不把从属坐标当成保留。桶间/桶内选择不读取GT。原始峰预算耗尽时记录budget_exhausted，旁路始终无确认输出。全帧候选计数P50/P95/P99/max/sum在group_summary.json，容量删除每帧计数与逐原始候选理由已导出。

## 对候选未生成的直接定位

76个有图像地图的选帧，用同一个原生distalLine递推重算currentEvidence；current-source峰坐标/增益与B1快照集合完全一致，之后才离线查询GT邻域。74个VISIBLE有图可查，2个G0没有证据地图。

|组/帧|当前达标像素10|同时gain≥12|再通过纵向极值|再通过向前停止极值|首先丢失条件|
|---|---:|---:|---:|---:|---|
|ct2/196|61|61|20|0|not_forward_stopping_maximum|
|ct2/338|57|55|18|0|not_forward_stopping_maximum|
|ct2/431|59|59|20|0|not_forward_stopping_maximum|
|group_h/41|6|0|0|0|gain_below12_at_supported_pixels|
|group_h/78|10|0|0|0|gain_below12_at_supported_pixels|
|group_h/115|4|0|0|0|gain_below12_at_supported_pixels|
|group_h/304|49|49|20|0|not_forward_stopping_maximum|

这定位的是固定提取器中的实际过滤步骤，不是物理裂纹终止真相；未据此下降阈值或更换容差。控制表current_dp_control.csv、查询表current_peak_filter_diagnosis.csv、实际gain图maps/*__current_dp.npz可复核。

## 预算误删归因

全部误删的近端raw_id、合并代表、桶内保留节点、分数及裁剪原因见budget_loss_lineage.csv。B1/B2原始候选集合逐帧精确对照；只发生压缩变化，因此不能用“原本没有候选”解释这些退化。

- group_a/398 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 1749 → retained 62；原A hit5=False, hit10=False。
- ct2/1 (dev): ["BUCKET_CAPACITY"]；近端raw 4；全帧raw 149 → retained 48；原A hit5=False, hit10=False。
- ct2/43 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 137 → retained 47；原A hit5=False, hit10=False。
- ct2/76 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 130 → retained 45；原A hit5=False, hit10=False。
- ct2/131 (dev): ["BUCKET_CAPACITY"]；近端raw 2；全帧raw 118 → retained 46；原A hit5=False, hit10=False。
- ct2/157 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 133 → retained 50；原A hit5=False, hit10=False。
- ct2/251 (dev): ["BUCKET_CAPACITY"]；近端raw 2；全帧raw 120 → retained 47；原A hit5=False, hit10=False。
- ct2/271 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 155 → retained 47；原A hit5=False, hit10=False。
- group_h/141 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 73 → retained 46；原A hit5=False, hit10=False。
- group_h/216 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 70 → retained 45；原A hit5=False, hit10=False。
- group_h/252 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 92 → retained 47；原A hit5=False, hit10=False。
- group_h/401 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 81 → retained 50；原A hit5=False, hit10=False。
- group_c/221 (val): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 122 → retained 31；原A hit5=False, hit10=True。
- group_c/456 (val): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 132 → retained 32；原A hit5=False, hit10=False。
- group_c/528 (val): ["BUCKET_CAPACITY"]；近端raw 3；全帧raw 127 → retained 31；原A hit5=False, hit10=False。
- three_point_bend/1 (val): ["BUCKET_CAPACITY"]；近端raw 3；全帧raw 130 → retained 28；原A hit5=False, hit10=False。
- three_point_bend/178 (val): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 123 → retained 27；原A hit5=False, hit10=False。
- three_point_bend/306 (val): ["BUCKET_CAPACITY"]；近端raw 2；全帧raw 117 → retained 26；原A hit5=False, hit10=False。
- three_point_bend/407 (val): ["MERGE_REPRESENTATIVE_OUTSIDE10"]；近端raw 1；全帧raw 134 → retained 30；原A hit5=False, hit10=False。
