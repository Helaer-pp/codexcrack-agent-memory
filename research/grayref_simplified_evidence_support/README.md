# 简化原型的只读交付辅助

检测与所有规则保存在相邻 `grayref_simplified_evidence_v0/`，冻结后不改。本目录只提供原始点核查、真实图重复执行核查、事后阶段损失审计、从封存PNG制作六组视频和完整复现入口。

从项目根目录运行：

```powershell
./research/grayref_simplified_evidence_support/grayref_simplified_full_delivery.ps1 -RunId NEW_UNIQUE_RUN -Workers 12
```

阶段审计先登记计划/脚本SHA，再运行主试验；只有两批推理与评分均封存后才执行阶段审计。所有人工标签仅比较，不回写推理。视频从逐帧真实图片生成，6FPS播放不是推理速度。辅助脚本不修改旧A/V1/V2、原始BMP、点、标签或已经封存的算法工件。

交付入口为运行目录下 `FINAL_FINDINGS.md`、`galleries/index.html`、`videos/index.html` 和独立的 `offline_label_overlays/index.html`。后者明确标记 OFFLINE_LABEL_OVERLAY；人工路径不进入默认图册或检测入口。

逐层审计重算原始峰、保留节点、片段和有限路径池；包含关系审计严格重放原生路径 ID、片段链和排序分数。被删除路线的离线路径覆盖不等于其尖端正确，不计入实际准确率。补充噪点反例在规则冻结后诊断，不用于调参，也不代表真实阴性假阳性率。

`grayref_simplified_delivery_seal.py --run <已完成目录>` 用于人工图像复核记录 `MANUAL_VISUAL_REVIEW.md` 写入后的最后交付检查：核对核心签名、六组视频完整解码记录与哈希、全部 HTML 本地链接及九模式逐组导航，再保存辅助源码快照、额外交付哈希和实测空间/总耗时。此最后一步需要真实人工视图复核，不由复现脚本伪造。
