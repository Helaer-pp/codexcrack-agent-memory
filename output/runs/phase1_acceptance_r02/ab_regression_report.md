# 同源码 A/B 回归报告

AB-before 与 AB-after 来自同一份当前源码树：before 仅逆向 R01 的 `validCurrentPoints/current_anchor_invalid` 输入隔离补丁；after 为当前 R01 源码。Git 不可用，源码树和 DLL hash 见 `ab_build_manifest.json`。历史 2026-11-06 发布 DLL 未用于本 A/B。

- A/B-valid：988 帧，状态/尖端/长度/路径联合差异 0；逐字段差异均为 0。
- A/B-invalid：18 个 NaN/越界/退化案例；before 全部返回错误，after 全部返回成功并继续到端点分支。

| 构建 | 有效返回 | 状态一致 | 尖端一致 | 长度一致 | 路径一致 |
|---|---:|---:|---:|---:|---:|
| AB-before/after | 988 | 988 | 988 | 988 | 988 |

无效输入的差异是预期接口修复，不代表视觉精度提升；after 的确认状态仍按当前图像证据返回。有效输入行为未出现非预期回归。
