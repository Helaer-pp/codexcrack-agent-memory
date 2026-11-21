# 独立证据通道

当前3×3 σ0.8模糊暗谷=min(y−4,y+4)−current；当前flank≥75方可支持，完全不读取参考有效性。当前证据仅暗线。referenceEvidence为配准参考暗谷，referenceChange为registered−current，referenceQuality为实际accepted tile全11×11处理足迹有效；否则浮点NaN，非负证据。保留原legacyScore、eroded/refMin/refMax/novel/knownCrack及legacyReason地图。局部参考64tile、9个24模板、corr阈值.62、至少2票及2px一致票全部保持；完整小块位置、delta、corr、票和拒绝原因在选帧trace tiles中。votes<2时agree默认0是未执行，一律解释为UNKNOWN，不能当测得不一致0票。

reasonMask位1边界未计算、2当前flank不足、4参考未知、8旧eroded门、16旧参考纹理门、32已知裂纹mask、64当前响应恢复。quality=0只表示UNKNOWN而非否定裂纹。图册统一当前证据色标0..30、变化−20..20，NaN紫色；原始float图保存在maps。
