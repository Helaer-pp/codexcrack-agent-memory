# 基线身份与历史发布边界

本轮S0的A0为 `output/build/src/cpp/a/Release/CrackV4.dll`，SHA256 55a0e7a79162da79e691ede9ff58229e59a56fdd1e0b1e3f609dc51128860402；这是R02 environment.md明确列出的候选基线，R05D/R05E继续使用。当前源码克隆与其1565帧完整非计时结果完全一致。

`output/releases/A_Win64_OpenCV440/bin/CrackV4.dll` SHA256 1c74283c53eb99479190df47daea2c4d061f7ba90bb81acd7a847b9aa3b8e21f，是R01 inventory.md明确保留的2026-11-06历史发布件。R01 dependency_audit.md:25明确说它与当前源码不是同一构建；R02 ab_regression_report.md:3明确历史发布DLL未用于该A/B。config/project.json仍指向此发布包，意味着发布包与研究候选不能混称，而非本轮应把它们的不同当成克隆失败。

本轮附加全序列量化：formal完全相同1162/1565；403帧不同，其中confirmed_tip不同104帧，tip字段不同277帧，完整长度确认不同13帧。geometry全帧有三个诊断字段不同。完整摘要0/1565一致。`release_equivalence.json`中的FAIL只指对“两个文件版本相同”的附加假设检验，不是S0指定55a0源码克隆的失败，也不是R05F引入的回归。

初始交流中曾将追加差异解读为整体S0失败；查回上述历史版本说明后已纠正。保留原始数值，不隐藏差异，不将版本边界变成虚构的本轮bug。S0范围和最终准入判定以本文件和acceptance_matrix.csv为准。
