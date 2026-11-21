# 接手规则

从 [当前状态](docs/CURRENT_STATE.md)、[V6.3 开发报告](evidence/v6_3/REPORT.md)、[报告索引](reports/INDEX.md) 和 [工作区项目约定](docs/LOCAL_PROJECT_RULES.md) 开始。研究版本 V6.3 S2，日常默认 V5.15 S2。

- 数据分组在 config/dataset_usage_policy.json。group_a、ct2、group_h、ct3 可用于开发，group_c、three_point_bend 仅用于冻结后验证，group_x 排除。人工标注仅供对照。
- 后续集成使用 GrayDetectionV2 类和同前缀导出，发布一个 hpp、一个 lib、一个 dll。保持已发布的序号与布局。
- 原图、人工标注、视频和第三方二进制保存在本地。公开仓库限制为 100,000,000 字节，发布前使用 tools/check_size.py 核验。
