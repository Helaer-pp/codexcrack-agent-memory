# 开发组H MT · V6.1 冻结回放

开发组H 410/410 帧由参考中心缺口回退完成准备并进入配准和路径搜索，410 帧的材料窗均缺少通过 NCC 的局部匹配，实际均使用粗对齐的零局部位移。342 帧发布尖端，68 帧无输出。上轮有效输出为 0/410。20 张人工标注中有 18 张可见、2 张不确定。Hit@5 为 7/18，Hit@10 为 9/18，Joint 为 9/18。

[410 帧参考、原图、裂纹路径与差分视频](../../output/experiments/v61_center_gate_r01/difference_views/group_h.mp4) · [人工标注计分](../../output/experiments/v61_center_gate_r01/group_h_scores.csv) · [全序列尖端与长度](../../output/experiments/v61_center_gate_r01/group_h_lengths.csv)

开发组A与开发组H为开发回放，三点弯、验证组C只做冻结后验证。按任务书直接应用给定常数。第 1 帧固定参考，每帧独立；图像来源与逐帧基准点经过校验。人工标签只用于预测封存后的计分。验证组C两套点位复用同一批图像。Joint 要求原像素尖端误差 ≤10 px，且路径精确率、覆盖率均 ≥80%；未输出尖端计漏检。

| 组 | 帧 | 进入配准／DP | 参考中心回退 | 有 NCC 支持 | 全窗零回退 | 有尖端 |
| --- | --- | --- | --- | --- | --- | --- |
| 开发组H MT | 410 | 410 | 410 | 0 | 410 | 342 |

第 216、221 帧分别提前 116.75、117.37 px。两帧各只有一个可回溯候选，在重选端点前已停于原图 x=2754 附近。第 78、115 帧进入既有暗线路由后无法确认；强制联合分支，第 78 帧仍因路径太短被拒，第 115 帧误差反而达 140.29 px。

## 失败标注帧

| 帧 | 误差 px | 横向偏差 px | 路由 | 回溯分支数 | 直接失效表现 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| 41 | 80.80 | -80.80 | JOINT | 1 | 全部回溯分支未命中，输出提前终止 | [图与得分曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0041.jpg) |
| 78 | — | — | PREEXISTING_CHECK | 1 | 未发布尖端，NO_CONFIRMED_PREEXISTING | [图与得分曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0078.jpg) |
| 115 | — | — | PREEXISTING_CHECK | 1 | 未发布尖端，NO_CONFIRMED_PREEXISTING | [图与得分曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0115.jpg) |
| 141 | 48.79 | -48.65 | JOINT | 1 | 全部回溯分支未命中，输出提前终止 | [图与得分曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0141.jpg) |
| 216 | 116.75 | -116.74 | JOINT | 1 | 全部回溯分支未命中，输出提前终止 | [图与得分曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0216.jpg) |
| 221 | 117.37 | -117.33 | JOINT | 1 | 全部回溯分支未命中，输出提前终止 | [图与得分曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0221.jpg) |
| 252 | 37.68 | -37.68 | JOINT | 1 | 全部回溯分支未命中，输出提前终止 | [图与得分曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0252.jpg) |
| 340 | 40.28 | -40.26 | JOINT | 1 | 全部回溯分支未命中，输出提前终止 | [图与得分曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0340.jpg) |
| 377 | 11.46 | -11.19 | JOINT | 1 | 全部回溯分支未命中，输出提前终止 | [图与得分曲线](../../output/experiments/v61_center_gate_r01/audit_views/group_h_original_0377.jpg) |

## 基准点与适用条件

左移包含重裁与重新定位，每组 20 个抽检帧，含重复共 26 个配对。开发组H 26 次左移后均无可用缺口体，无法计算尖端漂移。20 个独立测试帧的参考窗口右界均缩至 x=2603（不含），原参考顶点 x=2643 已在窗外。三点弯第 120 帧最大漂移 48.21 px。验证组C亮区实际只能移动 −17 至 −14 px，第 95 帧漂移 22.80 px。

名义点位下的中心缺口定位成功率不能外推到实际左移 150 px 的输入。[实际左移、定位状态与端点明细](../../output/experiments/v61_center_gate_r01/group_h_stress.csv) · [参考窗右界与候选坐标](../../output/experiments/v61_center_gate_r01/group_h_left_apex.csv)
