# 实测开发/验证报告

工程完整性：2647/2647 帧；默认 C_FUSION_RAW。算法验收：NO_GO；生产批准：NO。所有结果为暂定身份。

[六组逐帧图册](../galleries/index.html) · [完整性](../run_integrity.json) · [统一规则](../model_protocol.md) · [逐帧指标](../offline_evaluation.csv)

| group | mode | visible | hit3 | hit5 | hit10 | joint | output_coverage | over100 | over500 | raw_over100 | raw_over500 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEVELOPMENT | A_VALLEY_ONLY_RAW | 76 | 1 | 1 | 2 | 2 | 4 | 2 | 1 | 4 | 2 |
| DEVELOPMENT | B_DIFF_ONLY_RAW | 76 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| DEVELOPMENT | C_FUSION_RAW | 76 | 1 | 1 | 2 | 2 | 3 | 1 | 1 | 3 | 2 |
| DEVELOPMENT | A_VALLEY_ONLY_MEDIAN3 | 76 | 1 | 1 | 1 | 1 | 3 | 2 | 1 | 2 | 1 |
| DEVELOPMENT | B_DIFF_ONLY_MEDIAN3 | 76 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| DEVELOPMENT | C_FUSION_MEDIAN3 | 76 | 1 | 1 | 1 | 1 | 3 | 2 | 1 | 2 | 1 |
| DEVELOPMENT | A_VALLEY_ONLY_GAUSSIAN_LIGHT | 76 | 1 | 1 | 2 | 2 | 7 | 5 | 3 | 5 | 3 |
| DEVELOPMENT | B_DIFF_ONLY_GAUSSIAN_LIGHT | 76 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 |
| DEVELOPMENT | C_FUSION_GAUSSIAN_LIGHT | 76 | 1 | 1 | 2 | 2 | 6 | 4 | 3 | 5 | 3 |
| DEVELOPMENT | V1_LOCKED | 76 | 6 | 8 | 12 | 11 | 50 | 31 | 18 | 31 | 18 |
| DEVELOPMENT | V2_NUMERIC_CONTROL | 76 | 6 | 8 | 12 | 11 | 43 | 24 | 17 | 31 | 18 |
| DEVELOPMENT | V2_COMBINED | 76 | 2 | 2 | 4 | 4 | 37 | 26 | 19 | 57 | 37 |
| EXPOSED_REGRESSION | A_VALLEY_ONLY_RAW | 35 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EXPOSED_REGRESSION | B_DIFF_ONLY_RAW | 35 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EXPOSED_REGRESSION | C_FUSION_RAW | 35 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EXPOSED_REGRESSION | A_VALLEY_ONLY_MEDIAN3 | 35 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EXPOSED_REGRESSION | B_DIFF_ONLY_MEDIAN3 | 35 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EXPOSED_REGRESSION | C_FUSION_MEDIAN3 | 35 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EXPOSED_REGRESSION | A_VALLEY_ONLY_GAUSSIAN_LIGHT | 35 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EXPOSED_REGRESSION | B_DIFF_ONLY_GAUSSIAN_LIGHT | 35 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EXPOSED_REGRESSION | C_FUSION_GAUSSIAN_LIGHT | 35 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EXPOSED_REGRESSION | V1_LOCKED | 35 | 0 | 2 | 5 | 5 | 20 | 4 | 0 | 4 | 0 |
| EXPOSED_REGRESSION | V2_NUMERIC_CONTROL | 35 | 0 | 2 | 5 | 5 | 14 | 0 | 0 | 4 | 0 |
| EXPOSED_REGRESSION | V2_COMBINED | 35 | 2 | 2 | 4 | 3 | 6 | 0 | 0 | 1 | 0 |

完整可见分母76/35，未知9张单列；未标注帧不认作阴性。当前/参考/点全部重新哈希。开发推理封存后独立评分，再使用同一冻结源码执行曝光验证。旧基线为2647帧原始完整trace/result校验回放，未重新运行旧C++；其原生预测及本轮独立评分复现。

## 逐组默认与基线

| group | mode | visible | hit3 | hit5 | hit10 | joint | output_coverage | over100 | over500 | raw_over100 | raw_over500 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | C_FUSION_RAW | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| group_a | V1_LOCKED | 19 | 0 | 0 | 0 | 0 | 13 | 13 | 1 | 13 | 1 |
| group_a | V2_COMBINED | 19 | 0 | 0 | 0 | 0 | 6 | 6 | 0 | 19 | 0 |
| ct2 | C_FUSION_RAW | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ct2 | V1_LOCKED | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ct2 | V2_COMBINED | 20 | 0 | 0 | 0 | 0 | 20 | 20 | 19 | 20 | 19 |
| ct3 | C_FUSION_RAW | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ct3 | V1_LOCKED | 19 | 6 | 8 | 12 | 11 | 19 | 0 | 0 | 0 | 0 |
| ct3 | V2_COMBINED | 19 | 2 | 2 | 4 | 4 | 11 | 0 | 0 | 0 | 0 |
| group_h | C_FUSION_RAW | 18 | 1 | 1 | 2 | 2 | 3 | 1 | 1 | 3 | 2 |
| group_h | V1_LOCKED | 18 | 0 | 0 | 0 | 0 | 18 | 18 | 17 | 18 | 17 |
| group_h | V2_COMBINED | 18 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 18 | 18 |
| three_point_bend | C_FUSION_RAW | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| three_point_bend | V1_LOCKED | 15 | 0 | 2 | 5 | 5 | 14 | 0 | 0 | 0 | 0 |
| three_point_bend | V2_COMBINED | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| group_c | C_FUSION_RAW | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| group_c | V1_LOCKED | 20 | 0 | 0 | 0 | 0 | 6 | 4 | 0 | 4 | 0 |
| group_c | V2_COMBINED | 20 | 2 | 2 | 4 | 3 | 6 | 0 | 0 | 0 | 0 |

## 同一原型内部对照与架构比较

| role | comparison | hit_gained | hit_lost | joint_gained | joint_lost | new_over100 | new_over500 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEVELOPMENT | C_FUSION_RAW versus A_VALLEY_ONLY_RAW | 0 | 0 | 0 | 0 | 0 | 0 |
| DEVELOPMENT | C_FUSION_RAW versus B_DIFF_ONLY_RAW | 2 | 0 | 2 | 0 | 1 | 1 |
| DEVELOPMENT | C_FUSION_RAW versus C_FUSION_MEDIAN3 | 1 | 0 | 1 | 0 | 0 | 0 |
| DEVELOPMENT | C_FUSION_RAW versus C_FUSION_GAUSSIAN_LIGHT | 0 | 0 | 0 | 0 | 0 | 0 |
| DEVELOPMENT | C_FUSION_RAW versus V1_LOCKED | 2 | 12 | 2 | 11 | 0 | 0 |
| DEVELOPMENT | C_FUSION_RAW versus V2_NUMERIC_CONTROL | 2 | 12 | 2 | 11 | 0 | 0 |
| DEVELOPMENT | C_FUSION_RAW versus V2_COMBINED | 2 | 4 | 2 | 4 | 1 | 1 |
| EXPOSED_REGRESSION | C_FUSION_RAW versus A_VALLEY_ONLY_RAW | 0 | 0 | 0 | 0 | 0 | 0 |
| EXPOSED_REGRESSION | C_FUSION_RAW versus B_DIFF_ONLY_RAW | 0 | 0 | 0 | 0 | 0 | 0 |
| EXPOSED_REGRESSION | C_FUSION_RAW versus C_FUSION_MEDIAN3 | 0 | 0 | 0 | 0 | 0 | 0 |
| EXPOSED_REGRESSION | C_FUSION_RAW versus C_FUSION_GAUSSIAN_LIGHT | 0 | 0 | 0 | 0 | 0 | 0 |
| EXPOSED_REGRESSION | C_FUSION_RAW versus V1_LOCKED | 0 | 5 | 0 | 5 | 0 | 0 |
| EXPOSED_REGRESSION | C_FUSION_RAW versus V2_NUMERIC_CONTROL | 0 | 5 | 0 | 5 | 0 | 0 |
| EXPOSED_REGRESSION | C_FUSION_RAW versus V2_COMBINED | 0 | 4 | 0 | 3 | 0 | 0 |

A/B/C与滤波对照使用同一连接/停止器；与V1/V2的端到端差异不能解释为某个单模块的因果效应。新增候选不等于新增正确主裂纹。拒绝率、原始候选严重错误与全量状态均保留，不能把减少输出当精度提升。

## 环境与成本

{
  "utc": "2026-11-13T03:28:01.588730+00:00",
  "python": "3.12.7 | packaged by Anaconda, Inc. | (main, Oct  4 2024, 13:17:27) [MSC v.1929 64 bit (AMD64)]",
  "platform": "Windows-11-10.0.26200-SP0",
  "processor": "AMD64 Family 25 Model 97 Stepping 2, AuthenticAMD",
  "cpus": 32,
  "numpy": "1.26.4",
  "scipy": "1.17.1",
  "opencv": "4.12.0",
  "matplotlib": "3.10.9",
  "pillow": "10.4.0",
  "memory": 67768807424,
  "disk_free": 128867921920,
  "workers": 12
}

每帧九模式推理时间（含证据计算，不含绘图/I/O）P50/P95：[9606.63179999392, 20240.26572000002] ms。该研究Python成本不代表生产性能。
