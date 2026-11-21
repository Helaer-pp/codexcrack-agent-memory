# 诊断覆盖范围

| 字段/证据 | 状态 | 说明 |
|---|---|---|
| 输入文件 SHA-256 | AVAILABLE | `t2_reinit_results.csv` 对每帧记录文件字节 hash |
| 参考帧 SHA-256 | AVAILABLE | 同上，按组固定 |
| DLL/source/config hash | AVAILABLE/PARTIAL | DLL 和 config 可核验；无 Git commit，用源码树 hash |
| 初始/当前 P1/P2 | AVAILABLE | 分列记录；当前轨迹来自 manifest |
| tip ROI 原图坐标 | AVAILABLE | 只读 debug JSON `tip_roi_xywh` |
| registration state/quality | AVAILABLE | geometry/quality JSON |
| endpoint rotation/translation | NOT_AVAILABLE | 生产只读 API 未公开 `tip_rotation/tip_translation`；未修改数值路径补字段 |
| tip source observed/predicted/fallback | PARTIAL | 现有 ABI 只有 `tip_confirmed`；R02 用 `observed` 或 `not_confirmed`，未把未确认帧冒充预测/回退 |
| terminal status/failure | AVAILABLE | native status/terminal/error 字段 |
| 模块级耗时 | PARTIAL | `CRACK_V4_PROFILE` 独立诊断构建记录 scope；生产 DLL 不带 profile，未把未归因时间摊入模块 |
| 真实人工尖端 GT | MISSING | 不能判断物理尖端正确性 |
| T2-B-real 外部轨迹 | MISSING | 未发现多初始点对应的真实追踪轨迹 |
| 宿主级集成 | NOT_RUN | 只有 SDK example/ABI 冒烟 |
