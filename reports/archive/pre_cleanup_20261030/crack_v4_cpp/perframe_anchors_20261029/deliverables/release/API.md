# 像素API与兼容性

## 输入与实例生命周期

Create输入参考灰度图、参考两点；Process输入当前灰度图、同顺序的当前对应两点。GRAY8/CV_8UC1，非连续行可用stride；图像缓冲区调用期间有效。
未传当前点(`NULL`)时使用原自动平移配准；此模式要求当前与参考图尺寸相同。提供点时支持图像平移、旋转及不同画布尺寸，仍使用刚体几何。点间距变化不用于倍率缩放，不能当成通用变焦补偿。
一个句柄对应一条有序序列；每相机/试件独立实例。内部互斥不代替时序约束，Process→GetResultV2/LastJson/CopyPath需要调用侧保持顺序，避免其他线程插入处理。
Destroy后句柄失效；旧C++类不能复制。更换参考图需重新初始化。

## 旧API

原函数按名称保留，原头文件结构未增加字段。x64布局Config24、Result88、Point16、Image24字节。
`struct_size`必须准确。Process遇到无效result结构在运算前返回-1；其他处理错误返回-1并清零结果有效位。
GetBaseline返回不可变参考结果；**不会修改当前LastJson、历史、previous或运动状态**。因此中途GetBaseline后LastJson仍表示最近Process帧，而非基线。要读取基线的旧结果请用GetBaseline的输出结构。
旧C API `mm_per_pixel`/`length_mm`保留用于兼容，没有优化其标定逻辑。本次全部评估为像素；新V2结构无mm字段。
LastJson返回内部UTF-8指针，需立即复制，后续调用不能长期持有/跨线程读取该指针；CopyPath只读取最近处理的路径。
没有候选时，所有确认位为0、尖端为(0,0)。有路径但未确认尖端时，tracking endpoint仍可显示；完整长度不是有效测量。
按ordinal动态导入、32位构建以及不同编译器C++对象ABI未验证；建议使用配套C头与名称导出，OpenCV对象不跨DLL边界。

## V2新增接口

使用`CrackV4_v2.h`。Result/Options必须设置`struct_size=sizeof(...)`且`api_version=2`。

| 函数 | 语义 |
| --- | --- |
| CrackV4DefaultOptionsV2 | 默认SHADOW与terminal_validation=1 |
| CrackV4SetOptionsV2 | 设置策略/审计开关；改变选项自动ResetTemporal；无效参数不改变状态 |
| CrackV4GetResultV2 | 只读最近处理帧；不推进时序；无效版本/结构返回-1 |
| CrackV4ResetTemporal | 清历史/previous/帧计数，运动变换归一，最近结果回参考缓存；参考和几何/采样缓存保留 |

ResultV2为376字节，OptionsV2为16字节（本次x64布局）。参考缓存初始frame_index=0；有效输入开始处理并成功配准后递增。配准异常不会递增，不是原文件编号；文件编号应由调用侧保存。

## 输出字段

所有坐标均为当前**完整原图**坐标：左上角(0,0)，x向右，y向下。坐标小数来自拟合/插值与0.01px取整，不代表0.01px精度。

| 字段 | 单位/有效条件 |
| --- | --- |
| has_candidate | 本帧有可见候选路径，不能单独说明是裂纹 |
| tracking_endpoint_px | 候选路径末点；仅has_candidate=1时解释，未确认时也保留 |
| tip_px | 按当前策略确认的尖端；tip_confirmed=0时为(0,0)，不要推导长度 |
| root_px | 根部连接位置；root_confirmed=0时为(0,0) |
| observed_length_px | 检出的平滑中心线弧长；不含推断的根部桥接；has_candidate=1时解释 |
| root_bridge_length_px | 既有局部连接接受的短桥接长度；root无效为0；上限保留12px |
| root_to_tip_length_px | 完整路径弧长，包含合法短桥接；complete_length_valid=0时为0 |
| complete_length_valid | 所选策略尖端与根部都有效；不应拿候选弧长代替完整长度 |
| terminal_verified | 新终端启发式检查通过；不是物理真值保证，与旧策略tip_confirmed可不同 |
| legacy_tip_confirmed | 该帧沿当前跟踪路径按旧时序/证据规则判断 |
| shadow_tip_confirmed | 该帧沿当前路径按新终端/端点时序规则判断 |
| path_quality_valid | 支持率/断点/弯折满足实验阈值 |
| path/tail_support_fraction | 原路径采样点分数≥2.5的比例；尾部取最后16个采样点 |
| longest_gap_samples | 连续低于阈值的最长采样点数，约1px步长；不是标定后的物理断裂长度 |
| path_width_median_px | seed宽度+延伸每8px横截面宽度的中位数，截面单侧最多8px；诊断估计，非精确开口测量 |
| tail_width_median_px | 最后tile中的8个截面支持宽度中位数；不能当作精确裂纹开口 |
| endpoint_temporal_hits | 仅合格历史端点可贡献的证据次数，最多5；允许旧端点位于当前增长路径上 |
| terminal_reason / divergence_reason | 边界、信号不足、前向疑似延续、配准不确定或时序未确认等可审计原因 |
| detector_ms / api_ms | 单帧核心/内部API时间，不含图像读取、路径JSON导出与显示 |

路径数组用旧CopyPath接口或LastJson获取。LastJson还保留旧measurement完整诊断，未确认时可能有`estimated_root_to_tip_length_px`；它是候选估计，不是有效完整长度。显示/保存正式值应看有效位。

## 参考状态

- `CV4_DECLARED_CLEAN=0`：调用者明确指定Clean；不表示算法证明无裂纹。
- `CV4_REFERENCE_CRACK=1`：原参考完整裂纹策略接受了参考路径。
- `CV4_REFERENCE_UNCERTAIN=2`：Auto没有接受完整参考裂纹；仍保留旧差分fallback，参考图并未被确认干净。

显式Cracked模式不能初始化完整参考裂纹时返回错误。当前参考检测仍沿用原完整裂纹策略，新实验终端策略不会偷偷改变初始化；若需要从边界或不完整参考裂纹初始化，尚未增加这一能力。

## 策略与预算

`CV4_LEGACY=0`和`CV4_SHADOW=1`均保留正式旧输出；SHADOW是默认。terminal_validation独立控制是否生成新审计，设0可关闭开销；旧状态修复不会关闭。
`CV4_VERIFIED_EXPERIMENTAL=2`要求审计开启，会以新证据决定正式尖端，并影响previous更新；只验证了接口和生成场景，未完成真实序列人工验收，默认关闭。
更换策略会重置时序。新旁路审计的全序列统计不能当成启用Verified反馈后的序列效果。
终端审计复用最后tile；前向3条小角度射线，每条16个样本，总48个，不启动新DP。横截面与路径统计由现有路径/tiles数量约束；这是工作量上限，不是操作系统调度下的硬实时保证。
终端盲区包括遮挡/闭合后的不可见延续、弱信号、同形划痕和不可靠配准。具体失败见报告。
# 2026-10-29 measured per-frame anchors extension

This isolated revision preserves the existing C layouts and default `CrackV4Create`
behavior. Use `CrackV4CreateExtended` to opt in. The final four-group candidate uses
`flags=3572` (`244+256+1024+2048`), `refine_anchor_motion=1`, Shadow policy 1 and
`terminal_validation=1`. This does not silently enable Verified policy 2.

New independent bits: `256=CV4_DIRECTION_POSITIVE`,
`512=CV4_DIRECTION_NEGATIVE` (mutually exclusive),
`1024=CV4_GUARDED_REGISTRATION`, `2048=CV4_REJECT_ERASED_TERMINAL`.
Auto direction uses neither256 nor512. The positive normal of ordered P1→P2 is
`(dy,-dx)` in image coordinates; upper P1/lower P2 therefore points right.
The selected normal rotates with the reference/current rigid motion.

Provide reference points once at creation and the two corresponding tracked
current points for every `CrackV4Process`. Both pairs must be original-image,
uncropped/unscaled coordinates with stable point identities. A null current pair
requests automatic registration; it is never silently replaced with the reference
pair. Keep one handle for the complete acquisition stream; initialize/reset only
when starting a new reference or deliberately clearing history.

`CrackV4LastGeometryJson` is a new read-only extension. It reports
`REGISTRATION_VALID/AMBIGUOUS/FAILED`, `current_anchor_valid`, current-pair supply,
automatic-success verification and bounded-recovery flags. VALID means the
selected procedure passed its tests; it is not a proof of physical accuracy.
The existing LastQualityJson and Pixel V2 keep current candidate endpoint,
tip/root/length validity and historical confirmed coordinates separate.

Bit2048 only retracts formal tip/complete-length confirmation when existing local
sampling finds nearly constant replacement texture ahead of the visible path.
The visible centerline and current tracking endpoint remain available; arbitrary
occlusion and clipping are not guaranteed detectable. It adds no monotonic prior.

Use `tip_confirmed`, `root_confirmed`, and `complete_length_valid` independently.
Tip-only results do not imply a complete root-to-tip length. Keep missing values
unavailable; do not compute a substitute length from the anchor midpoint or reuse
the previous frame. Millimeter fields remain ABI-compatible but this release's
evaluation and exports are pixel-only. See `example_experiments.cpp` and the five
reports for integration, limitations and measured timing.

