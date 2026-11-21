# 2026-10-29 实验接口与回退

旧 `CrackV4Create` / `CrackV4Detector::initialize` 的默认测量逻辑保持不变。Pixel V2、ResetTemporal、旧 C ABI 的结构布局保持不变。实验接口在 `src/CrackV4_experiments.h`，无需改动原有结构。

## 输入约定

参考图/当前图为内存中的 `CV_8UC1` 原始灰度图，可有合法非连续 stride。参考基准点使用**原图坐标**。如有本帧真实跟踪后的两个点，继续通过 `CrackV4Process` 的 current_points 传入；没有才传 nullptr 进入自动配准。不得用参考点冒充已跟踪当前点。

本轮用户确认的扩展侧约定：**p1 在上、p2 在下时，预期向右扩展**。局部正向为 `(p2.y-p1.y, -(p2.x-p1.x))` 归一化。方向实验仅在两侧亮度均属于材料、亮度不能判断扩展侧时保留此正向；仍需正确排序。若以后存在向左主裂纹，应交换点顺序，或单独扩展方向输入，不能让算法凭阴影猜测。

所有新测试只使用像素。旧接口的 mm 字段仅为兼容，示例 `mm_per_pixel=1.0`，不把该兼容值当毫米测量。

## 独立开关（uint32 flags）

| 位 | 名称 | 行为 |
|---:|---|---|
| 1 | CV4_DIAGNOSTICS | 数值诊断。记录匹配块、seed/tile、DP。关闭后不收集这些大数组。 |
| 2 | CV4_DEBUG_IMAGES | 调试图像，自动包含 1。仅调试，不用于生产计时。最多 256 张。 |
| 4 | CV4_DIRECTION_EXPERIMENT | 两侧都是材料时采用已确认的基准点排序约定，避免光照导致方向翻转。 |
| 8 | CV4_PHOTOMETRIC_EXPERIMENT | **仅光度统计**，不做校正、不恢复被裁剪像素。 |
| 16 | CV4_REGISTRATION_RECOVERY | 原自动配准失败后，最多 4 个背景块、每块 ±64px 的 ZNCC 恢复。至少两个一致匹配。 |
| 32 | CV4_LAYERED_AUDIT | 分层诊断及历史确认结果查询。没有统一放松 Shadow 原阈值。 |
| 64 | CV4_CURRENT_TEXTURE_GUARD | 前方 13×7 个有效样本识别近乎无纹理替换区，修改实验终端审计。无任何长度单调判断。 |
| 128 | CV4_ANCHOR_PATCH_RECOVERY | 原自动配准失败后，先匹配基准点附近两个小模板，搜索各 ±64px；二者都通过当前图验证才恢复刚体变换。 |

`CrackV4DefaultExperimentOptions` 的 flags=0。实验组合 **244 = 4+16+32+64+128**，默认 decision_policy 仍为 SHADOW。`CV4_VERIFIED_EXPERIMENTAL=2` 仍需另外显式启用。

先尝试双基准点模板，再尝试背景块。模板边长最大 161，NCC 至少 .9、8px 邻域外峰值差至少 .08，基准间距比例限制 .5～1.5，角度限制 ±8°。背景恢复 NCC 至少 .6、4px 邻域外差至少 .08、至少两个位移在 2px 内一致。全部候选失败则保留本帧错误，不借用历史变换确认尖端。当前点由用户提供时不走这两条自动失败恢复。

## 生命周期

1. 每组图像创建一次 handle。参考图和参考点只用于初始化。
2. 每个当前帧按顺序调用一次 `CrackV4Process`。每帧实测点对应参考点顺序。
3. `CrackV4GetResultV2` 获得当前 `tracking_endpoint_px`、`tip_px`、长度及有效性。完整长度仅在 `complete_length_valid` 为真时使用。
4. `CrackV4LastQualityJson` 为独立只读查询，提供 registration/path/terminal/temporal、audit_authority、当前端点及 `last_confirmed_tip.pixel_xy/detector_frame_index`。该历史点属于记录的旧帧坐标，**不是**当前帧测量。frame_index 是检测器计数，不是照片文件名/相机时间戳；错误帧处理计数见旧接口行为，业务请另存图片编号。
5. 质量查询和 LastJson/CopyPath 均应在当前 Process 后读取。历史确认遵守当前生效的 decision_policy：Shadow 保留旧正式决策；需要按审计保护当前输出时使用实验性 Verified，并评估覆盖率下降。
6. `ResetTemporal` 保留参考图和初始裂纹缓存，清除时序/历史确认。切换 V2 策略也会 reset。`GetBaseline` 保持只读缓存语义，不能代替当前帧检测。
7. 完成后 `CrackV4Destroy`。每个独立图像流使用独立实例，同一实例按流顺序调用。

## 生产与实验输出的区别

Shadow 只增加审计，不因 texture guard 或前向疑似线响应清零旧正式测量。因此 Shadow 模式仍可能输出已知遮挡断点。Verified 将审计用于当前尖端/完整长度的有效性，tracking_endpoint 仍保留；不可把它或历史点回填为不可见物理尖端。

texture guard 只识别本轮合成场景中“有纹理表面被近乎常值区域替换”的特征。它不保证识别所有遮挡、闭合、姿态变化或过曝。对真实缩短的可见裂纹，不使用旧长度否决，不钳制长度、不回填旧尖端。

## 回退

重新使用旧 `CrackV4Create`，或 CreateExtended.flags=0，恢复上一轮默认数值路径；Verified 设回 SHADOW。上一轮 DLL、源码和 SHA256 在 `baseline/`。实验版尚无人工真值，新增测量应先用 `review/index.html` 复核。
