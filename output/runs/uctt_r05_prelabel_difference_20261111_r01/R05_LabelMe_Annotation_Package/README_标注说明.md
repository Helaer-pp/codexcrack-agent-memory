# R05 原图待标注包

共 7 组 × 20 张 = 140 张原图。图像逐字节复制，未缩放、未绘制预测点；同名 JSON 的 shapes 和 flags 均为空。请只在 images/<组名>/ 中标注并保存同名 JSON。

## 开始标注

1. 在 LabelMe 中打开 images 下某一个组目录。本包使用实际安装的 LabelMe 5.2.1 校验。若通过命令行启动，可运行 `labelme images/ct2 --config labelme_config.yaml`（在包目录执行）。
2. 关闭“Keep Previous Annotation/保留上一张标注”和自动保存，避免把上张标签带入当前图；不要改变原图分辨率。配置文件已设置这两项为 false。
3. 切换对应工具：Create LineStrip 创建折线，Create Point 创建点，Create Polygon 创建不确定区域。使用下面的精确英文标签名。
4. 放大查看实际可辨认的裂纹，Ctrl+S 保存同名 JSON。可先做 ct2 frame 8、group_h frame 5/78、group_c frame 69 等历史冲突帧；文件名和清单有精确映射。
5. 完成后交回整个包或 images 下已修改的 JSON + annotation_meta.csv，不需要重新发送原图。未完成的 JSON 可以保持空白。

## 标签与语义

| 标签 | 工具 | 标注内容 |
|---|---|---|
| crack_path | LineStrip 折线 | 肉眼可辨认的目标裂纹中心线。允许多条分段；不要跨不可见间隙凭空连线。 |
| crack_tip | Point 点 | 当前帧实际可见的主裂纹最远尖端。物理上可能存在但不可见的位置不要标。 |
| interference | LineStrip 或 Polygon | 主要划痕、夹杂和非目标裂纹状纹理。 |
| uncertain_region | Polygon 多边形 | 无法区分裂纹/划痕或无法确定末端的区域；不确定时优先标这个。 |
| branch_path | LineStrip，可选 | 清晰可区分的分支。多个末端有歧义时不要随意选择最长者。 |
| no_visible_crack | 图像级 Flag | 只有人工确认当前图没有能可靠辨认的目标裂纹时才勾选。与 crack_tip / crack_path 互斥。 |

未标注 ≠ 无可见裂纹。空 shapes 不能当负样本。若不能确定，绘制 uncertain_region，并在 annotation_meta.csv 填 visibility=uncertain、tip_confidence=low；明确可见可填 visible。仅粗标即可，无需宣称单像素精确。分支主尖端歧义及备注填入该 CSV，不要强行猜点。

## 文件、分组与选帧

- selection_manifest.csv：140 张原图路径、源 SHA256、原分辨率、P1/P2、选择理由、split。frame_id 为从 1 开始的内部顺序；frame_order 为从 0 开始的采集顺序；它们不是原始文件名中的数字，也不是物理时间。
- 每组 S0–S3 各 4 张：四个时间分位内兼顾开口代理分位；S4 为 4 张困难候选。时间阶段不代表已确认的萌生/增长/闭合阶段。开口指标是 P1/P2 距离，不是裂纹长度。
- 每组 15 development + 5 holdout。保留集按选中帧的连续时间块分配，尽量加大边界间隔。全部序列此前已曝光，因此这里只是预先锁定的内部保留集，不是独立测试集。排除组X仅历史诊断、三点弯曲仅曝光验证，两者均不得调参。
- reserve_frame_candidates.csv：未占主配额的历史冲突相邻帧线索，例如开发组H 77/79。opening_analysis_pairs.csv 仅供离线差分分析，不是在线参考选择。
- references/ 是固定参考原图副本，仅供查看；不要在其中标注。若参考图也被选入主配额，请只标 images/ 中那份。
- previews_readonly/index.html 为可点击原图的缩略导航，不能替代全分辨率原图标注。缩略图不含算法预测。
- CT3 的逐帧点使用历史冻结 CSV 的显式图片名映射，未找到独立原始点文件；此限制不影响原图标注，但限制点来源独立审计。

## 自检与交回

安装 Python + Pillow 后在包目录运行 `python annotation_qc.py`，生成 annotation_progress.csv 并检查标签、坐标、哈希与互斥关系。首次空包验证使用 `python annotation_qc.py --initial`；已有人工标签时不要加 --initial。

QC 不会补写任何标签。建议先完成 5–10 张再复核标签语义，若有第二位复核者可记录分歧。未来尖端误差/路径支持率必须在人工标签归还且通过 QC 后计算，目前准确率为 N/A。
