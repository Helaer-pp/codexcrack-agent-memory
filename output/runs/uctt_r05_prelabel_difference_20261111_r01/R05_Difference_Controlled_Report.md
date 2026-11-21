# R05-PRE：原图标注准备与参考差分受控验证

## 用户可直接使用的文件

- [140张原图目录](R05_LabelMe_Annotation_Package/images/)、[原图缩略导航](R05_LabelMe_Annotation_Package/previews_readonly/index.html)、[完整标注包](R05_LabelMe_Annotation_Package.zip)、[中文标注说明](R05_LabelMe_Annotation_Package/README_标注说明.md)。
- 实际 LabelMe 5.2.1 / Qt MainWindow 加载140个空JSON通过：[记录](labelme_open_validation.csv)、[CT2实际加载截图](labelme_open_ct2.png)。未保存或自动写入任何标签。
- [同帧固定/历史差分图册](R05_Reference_Difference_Comparison.html)、[因果与缺失合同测试](contract_tests.json)。例如验证组C frame38 可配对；GROUP_A frame241 双侧有效面积不足，拒绝并保留证据，不是假零残差。

## 数据与选帧

实际7组3171张原图全部可解码、组内SHA唯一：GROUP_A551、验证组C562、CT2 468、开发组H410、排除组X524、三点弯曲520、CT3 136。前六组原始点文件num逐帧与manifest一致；CT3仅有冻结CSV显式图片名/坐标映射，独立原始跟踪文件NOT_AVAILABLE。图像不隐式缩放后套用原坐标；frame_id是1基顺序，frame_order是0基顺序，不是文件名数字或物理时间。[盘点](data_quality_report.md)、[冻结源](frozen_manifest.json)。

每组20张：S0–S3时间四分位各4张，兼顾P1/P2距离分位；S4四张历史冲突/开口变化/低纹理代理。实际物理阶段全部待人工确认，不用预测长度或检测成功选“真裂纹”。CT2 frame8、开发组H5/78、验证组C69/38、排除组X1、GROUP_A241等进入主包；开发组H77/79等相邻帧保留在reserve清单。每组15 development+5内部holdout；后者不代表新独立试件。排除组X历史诊断、三点弯曲验证仍禁止调参。原图字节复制，140个JSON均为空，无自动尖端、路径或无裂纹标签。

## 受控方法与边界

全组同一套锁定规则（global_rules.json），不使用组名/文件名/帧号调阈值。历史缓存最近64条过去元数据、候选预算4，按相对开口差和旋转差排序，以图像拟合质量辅助排序，双侧独立验证门筛选；候选必须h<t。固定参考是同序列首帧，仅t>0使用。未来图像与未来P1/P2扰动不改变此前选择、warp和mask；合成可控平移和CT3真实前缀均已重放。缓存32/128敏感性仅比较候选元数据，不冒称完整图像质量敏感性实验。

当前ROI由当前P1/P2和图幅确定、最大原图宽1280，统一缩至最大宽640；同目标的所有分支共享ROI、分辨率、阈值25灰度级。上下材料分别由各自P点初始化平移，再在几何外侧条带进行图像Euclidean ECC拟合；邻近但未参与拟合的条带验证相关性和残差。几何条带只是“稳定材料候选”，未经人工确认确实无裂纹/划痕变化，因而所有残差都只是代理。没有强行用P1/P2合成一个整体刚体。

中央过渡带排除，不把两个侧向warp无证据拼成裂纹连续图。饱和/边界像素排除；E1/E2统计只取两臂共同有效mask。任一分支失败则该目标公平配对不计分，缺失值为CSV空字段/JSON null，不计0。四臂消融再取E1/E2/C0/C1共同交集。变化少不等于裂纹识别好，历史参考可能已有裂纹，差分不能单独给尖端。中央裂纹证据被排除的风险明确保留，GT回来后须量化路径覆盖损失。

主指标使用未做亮度归一化的差分。另保存稳定拟合区中位偏置（限±20）的归一化诊断图与NPZ，不用它调阈值。每案例NPZ保存current、各warp、带符号/归一化差分、各有效mask、公共mask、候选区、原图ROI与坐标比例；JPG图中紫色是无效区域。未实现逆向往返配准、重型非刚性模型或全局配准C2；本轮C0/C1已覆盖必须的开口匹配消融。

## 实测代理结果

| 组 | 目标帧/其中标注帧 | E1双侧通过 | E2可用 | 公平配对 | E1/E2 稳定区残差p95的中位数（灰度级） | 平均共同面积 |
|---|---:|---:|---:|---:|---|---:|
| group_a | 27/20 | 0 | 0 | 0 | N/A / N/A | N/A |
| group_x | 26/20 | 0 | 0 | 0 | N/A / N/A | N/A |
| ct2 | 26/20 | 22 | 25 | 22 | 6.00 / 6.50 | 0.75 |
| ct3 | 27/20 | 1 | 3 | 0 | N/A / N/A | N/A |
| group_h | 26/20 | 0 | 0 | 0 | N/A / N/A | N/A |
| three_point_bend | 27/20 | 26 | 26 | 26 | 6.00 / 5.00 | 0.91 |
| group_c | 26/20 | 25 | 25 | 25 | 12.00 / 7.00 | 0.78 |

残差单位为0–255灰度级；有效面积是统一缩放ROI像素比例。分母包括序列首帧（无先验参考）；第一帧不可与自身构成在线历史。额外回放是每组预先固定的frame_order 0–7连续窗口。全部主表配对帧一致，无失败帧补零。

| 组 | 四臂交集分母 | C0最近帧 | C1仅开口排序 | E2开口+配准门 |
|---|---:|---:|---:|---:|
| group_a | 0 | N/A | N/A | N/A |
| group_x | 0 | N/A | N/A | N/A |
| ct2 | 22 | 7.00 | 6.00 | 6.50 |
| ct3 | 0 | N/A | N/A | N/A |
| group_h | 0 | N/A | N/A | N/A |
| three_point_bend | 26 | 6.00 | 5.00 | 5.00 |
| group_c | 25 | 7.00 | 7.00 | 7.00 |

上述消融只比较同一四臂交集上的稳定区域残差，未证明相似开口本身比“最近过去帧”提供更好的真实裂纹证据。通过分母很小或为零的组不能外推收益。E1排除原因计数：{'no_prior_candidate': 7, 'insufficient_valid_area|insufficient_valid_area': 51, 'poor_registration': 5, 'insufficient_valid_area|ecc_nonconvergence': 25, 'poor_registration|poor_registration': 3, 'poor_registration|ecc_nonconvergence': 15, 'ecc_nonconvergence': 5, 'no_common_valid_pair': 1}。

## 问题判断与下一步

开口代理能生成因果候选，但相似间距不保证两侧图像都配准成功。历史图可能降低部分纹理残差，也可能无可用公共区域；不存在跨七组“历史必然优于固定”的结论。GROUP_A241显示当前裂纹可供人查看，但可用纹理/面积门失败，不能硬压门槛宣称通过。验证组C38展示同ROI实际配对，其较小残差仍非尖端GT。

闭合/再张开、已有裂纹未增长、真正新生扩展等物理分类均缺同步/人工证据，暂为UNKNOWN；不把frame序号或D变化命名为这些状态。真实划痕错位、可见末端、分叉身份需要用户在140张原图中标注。下一步优先补人工可见路径/干扰证据并核验稳定区域和有效覆盖，再决定修正配准或历史选择；本轮没有证据可跳到候选归属/尖端终止优化。没有变更D2、动态ROI或生产ABI。

## 性能与可迁移边界

本机Python/OpenCV单线程 sidecar，185个目标，历史检索+候选配准CPU累计段每目标中位数 377.17ms / P95 975.11ms；图像读取（含LRU命中）中位数 102.45ms / P95 844.47ms。差分统计计时另列difference_ms；渲染、压缩不包含在CPU配准段。不是完整DLL端到端吞吐，更不是目标i7验收。

可迁移模块为bounded history元数据缓存、ROI采样、双侧图像Euclidean拟合、质量mask、差分/诊断；C++17/OpenCV CPU理论上均有对应实现，但目前先测可靠性，不能承诺≤50ms。若证据支持，下一轮再做原生精简和预算拆分。无深度网络、DIC/稠密光流、第二全图路径搜索。

## 验收

- LABELME_PACKAGE_READY = PASS：140原图/140空JSON，真实LabelMe加载及ZIP CRC通过。
- CAUSAL_REFERENCE_SELECTION = PASS：740条选择记录检查h<t，未来扰动测试通过。
- 公平性/缺失QA = PASS：185个真实目标保存同ROI、公共交集、排除原因与真实差分；首帧/失败无假零统计。
- FIXED_VS_HISTORY_FEASIBILITY = INCONCLUSIVE：有代理对照，但覆盖不足、稳定区域未人工核验，不能推广到真实尖端。
- REAL_TIP_ACCURACY = AWAITING_MANUAL_ANNOTATION：无尖端预测评分，缺失不作负样本。
- PRODUCTION_ALGORITHM_UPDATED = NO：587个受保护文件哈希不变。
- R05_FORMAL_DEVELOPMENT_READY = NO：等待真实标注和公共区域路径覆盖验证。
- G7 = NOT_YET_TESTED_FOR_PRODUCTION。

人工标注导入脚本已实现3/5/10原图像素容差带、干扰激活、公共区域覆盖、分层输出；没有观察到的尖端预测时误差仍为N/A。holdout必须显式传入锁定规则SHA才可评价。当前真实执行输出为AWAITING_MANUAL_ANNOTATION。合成导入测试明确与用户包隔离，覆盖空白/无可见裂纹/不确定三态、标签互斥和越界拒绝；不是真实标签。
