# 开发组完整结果

GROUP_A551+三点弯520全部保留；标注34张VISIBLE，6张UNKNOWN，仅离线比较，无训练/GT参数搜索。新算法未依据验证组C像素/P/GT修改规则；但冻结前误运行通用旧A检查，读取了验证组C原图/P点，严格输入隔离不通过。详见PROTOCOL_DEVIATION.md，不能宣称本轮完全未接触验证组C输入。

| group | frames | visible | valid | null | hit3 | hit5 | hit10 | hit20 | coverage | over100 | over500 | mean_error | median_error | p95_error | max_error | oracle_hit10 | preferred_uncertain_hit10 | passes_frozen_thresholds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| group_a | 551 | 19 | 0 | 19 | 0 | 0 | 0 | 0 | 0.0 | 0 | 0 | None | None | None | None | 7 | 0 | False |
| three_point_bend | 520 | 15 | 11 | 4 | 1 | 1 | 3 | 8 | 0.7333333333333333 | 2 | 0 | 36.68662250226558 | 12.496366253842499 | 117.23453906657002 | 130.72400202672185 | 14 | 0 | False |


最早可观测丢失（不是因果结论；BUDGET_INCOMPLETE为审计优先状态，不表示已经排除更早灰度/片段损失，S1–S5覆盖另列）：

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
  }
}
```

合成工程检查成功不等于真实跨试件准确率通过。保留所有预算耗尽与错误端点，不调小分母、不按组修参数、不把preferred/Oracle补入正式输出。候选词典序搜索仍可能失去不同前驱的路径身份，结构门可能保留纹理、丢失细线；需结合逐帧血缘和配对消融进一步定位。
