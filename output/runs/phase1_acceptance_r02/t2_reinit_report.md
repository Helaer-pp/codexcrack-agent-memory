# T2-A 初始点重新初始化验收报告

运行：`phase1_acceptance_r02_t2a_20261110_r01`；候选 DLL：`55a0e7a79162da79e691ede9ff58229e59a56fdd1e0b1e3f609dc51128860402`。每个变体独立创建检测器，使用同一当前点轨迹；不存在状态复用。

| 组别 | 帧窗 | 变体 | 控制确认 | 最坏 P95 px | 最坏 max px | 最低 Cpair/C0 | 状态差异 | 判定 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| group_a | 252 | 16/16 | 1 | 0.0 | 0.0 | 1.0 | 0 | BLOCKED / INSUFFICIENT_OBSERVED_SUPPORT |
| group_c | 80 | 16/16 | 50 | 0.0 | 6.082762530298219 | 1.0 | 82 | FAIL / SUPPORTED |
| ct2 | 120 | 16/16 | 110 | 190.91883092036784 | 257.6373420139247 | 0.9636363636363636 | 215 | FAIL / SUPPORTED |
| group_h | 120 | 16/16 | 114 | 1194.0616527304219 | 1400.8301110413067 | 0.5087719298245614 | 187 | FAIL / SUPPORTED |
| group_x | 120 | 16/16 | 120 | 296.00168918436935 | 298.7189314389029 | 1.0 | 0 | FAIL / SUPPORTED |
| three_point_bend | 160 | 16/16 | 160 | 0.0 | 0.0 | 1.0 | 500 | FAIL / SUPPORTED |
| ct3 | 136 | 16/16 | 124 | 0.0 | 0.0 | 1.0 | 0 | PASS / SUPPORTED |

## 解释

- `C0/Cv/Cpair` 和 paired distance 只在共同视觉确认且坐标有效时计数；共同未确认不产生 0 px 样本。
- GROUP_A 控制窗口只有 1 个确认帧，因此判定 `BLOCKED/INSUFFICIENT_OBSERVED_SUPPORT`，不能宣称稳定通过。
- CT2、开发组H、验证组C和三点弯出现状态或坐标差异；差异首帧见 `first_divergence.csv`，不是通过减少确认率制造的零误差。
- 当前生产接口没有独立 `predicted/fallback` 枚举，也没有公开端点变换矩阵；R02 逐帧记录为 `not_confirmed`/`null`，详细阻塞见 `diagnostic_coverage.md`。

结论：T2-A 不是总体 PASS。部分组在当前窗口表现稳定，但整体行为验收仍为 PARTIAL/FAIL，需把初始化敏感性作为后续 Phase 1 工作项；本轮不修改生产算法。
