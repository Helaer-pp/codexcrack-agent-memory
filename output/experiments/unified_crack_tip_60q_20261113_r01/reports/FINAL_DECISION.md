# 最终验收：PRODUCTION_NO_GO

本轮已完成独立主链、DEV两组全量11模式、锁定验证组C单轮FULL、分离的GT评价和1633帧诊断/三组视频。研究实现不替换旧A。必须同时阅读[协议偏差](PROTOCOL_DEVIATION.md)：严格冻结前验证组C数据隔离未完全遵守，不能将完成实验等同规范全部验收通过。

| group | frames | visible | valid | null | hit3 | hit5 | hit10 | hit20 | coverage | over100 | over500 | mean_error | median_error | p95_error | max_error | oracle_hit10 | preferred_uncertain_hit10 | passes_frozen_thresholds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| group_a | 551 | 19 | 0 | 19 | 0 | 0 | 0 | 0 | 0.0 | 0 | 0 | None | None | None | None | 7 | 0 | False |
| three_point_bend | 520 | 15 | 11 | 4 | 1 | 1 | 3 | 8 | 0.7333333333333333 | 2 | 0 | 36.68662250226558 | 12.496366253842499 | 117.23453906657002 | 130.72400202672185 | 14 | 0 | False |
| group_c | 562 | 20 | 20 | 0 | 1 | 3 | 12 | 19 | 1.0 | 0 | 0 | 9.520212062433203 | 8.733486430907812 | 16.492070640888716 | 22.00093199995825 | 17 | 0 | False |

正式分母固定19/15/20。阈值：GROUP_A hit10≥14/valid≥16/>100=0；三点弯11/12/0；验证组C14/16/≤1。分组准确率门整体=False。另有冻结前通用旧A检查读取验证组C原图/P点的隔离偏差（DATA_ISOLATION_AUDIT=FAIL_WITH_DISCLOSED_DEVIATION），以及高密度边枚举尚无OS硬内存保障的工程局限，不能批准生产。null保留分母，Oracle和preferred不并入正式命中，未标注帧不是负例、真实FPR=N/A。

## RESEARCH_RESULT

原始细线保真、两路独立引用、动态工作掩膜、多轨迹与大跳跃证据复查已连通，15项基本合成合同通过，但追加5项风险探针有1项静态独立暗线误输出；真实序列指标和条件消融在DEVELOPMENT_REPORT/ABLATION_REPORT中完整披露。工程通过项不能证明裂纹身份。验证组C是已曝光固定回归，不是新盲测。新算法源码和参数在验证组C新算法运行前冻结；旧A通用检查的预冻结读图偏差单独披露。标注不训练，r01没有GT参数搜索。

最早可观测失败阶段（非物理因果）：

```json
{
  "group_a": {
    "BUDGET_INCOMPLETE": 19
  },
  "three_point_bend": {
    "S4_IDENTITY_VERIFICATION": 1,
    "S6_ENDPOINT_OR_SELECTION": 4,
    "S3_CONNECTION_CANDIDATE": 7,
    "BUDGET_INCOMPLETE": 3
  },
  "group_c": {
    "S6_ENDPOINT_OR_SELECTION": 7,
    "OFFICIAL_HIT10": 10,
    "S3_CONNECTION_CANDIDATE": 3
  }
}
```

## 后续建议

1. 优先解决已有合成反例：在缺口根部不确定时，附近静态独立暗线仍输出VALID(240,115)。保持RAW/参考输入，单独研究物理起源关联及身份不确定性的传播，不能以参考零差分否决所有旧裂纹。此安全反例在任何指标改善前都须明确保留。
2. 针对候选预算与纹理图的传播范围做受控实验：固定RAW、参考和身份规则，比较有界流式边提案/候选终点保留，证明减少的是冗余而不是正确尾端；不能仅持续加预算或缩ROI。
3. 依据配对消融和候选Oracle，区分候选不可达、身份拒绝、端点竞争；逐帧核对反例再改变单模块。覆盖率本身不证明路径正确，部分GT路径不能认证gap物理连接。
4. 建立独立缺口/材料纹理配准真实性检查和划痕阴性集，验证物理身份与局部参考有效性。当前局部NCC通过不等于真实变形场。下一轮若开发，使用新实验版本；不能利用本次验证组C成绩回调同一冻结版本。

## 完整性与复现

全部1633帧保留；DEV11781+LOCKED562=12343条完整模式预测（不把中断尝试、合成、无标签smoke或固定审计重放计入完整预测数）。保护历史176105文件，变动0。仅Python，C++未实现。源代码hash、运行环境、清单和原始TXT配对见manifests；实际命令见源码README。原四模块和参数未变；中途增加经133例全原生一致性核对的批量执行副本，来源hash分别保留，见执行副本注册。验证组C全部使用冻结批量副本；开发耗时按旧/新执行版本分列。调度中断的未完成文件隔离，完整历史结果未覆盖。

图册：[全帧交互平台](../galleries/index.html)；视频：[GROUP_A](../videos/group_a.mp4)、[三点弯](../videos/three_point_bend.mp4)、[验证组C](../videos/group_c.mp4)。独立GT：[开发](../offline_evaluation/overlays/DEV_index.html)、[验证组C](../offline_evaluation/overlays/LOCKED_index.html)。
