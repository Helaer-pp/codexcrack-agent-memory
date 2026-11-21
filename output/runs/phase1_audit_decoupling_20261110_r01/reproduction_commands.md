# 复现命令

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1 check
D:/ProgramData/anaconda3/python.exe -B tests/check_invalid_current_anchor.py
$env:CRACK_STRICT_RUN='phase1_strict_anchor_20261110_r01'; D:/ProgramData/anaconda3/python.exe -B tests/strict_anchor_invariance.py
```

项目检查会复现冒烟、冻结 A 回放、研究合同、端点终止、现有锚点不变性和无效当前点回归。严格矩阵输出在 `output/runs/phase1_strict_anchor_20261110_r01/`。
