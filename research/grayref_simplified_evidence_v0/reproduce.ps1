param([string]$RunId='grayref_simplified_evidence_v0_20261113_r01',[int]$Workers=5)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $projectRoot
$env:PYTHONPYCACHEPREFIX=Join-Path $projectRoot 'output/pycache'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONPATH=Join-Path $projectRoot 'research'
$env:MPLCONFIGDIR=Join-Path $projectRoot 'output/mplcache'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
& 'D:/ProgramData/anaconda3/python.exe' -m grayref_simplified_evidence_v0.run_all --run-id $RunId --workers $Workers
if($LASTEXITCODE -ne 0){throw 'Run failed; inspect preserved artifacts and logs.'}
