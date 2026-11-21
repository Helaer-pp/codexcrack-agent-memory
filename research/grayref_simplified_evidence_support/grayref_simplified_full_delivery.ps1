# One-command reproduction including optional read-only stage audit and six videos.
param([string]$RunId,[int]$Workers=12)
$ErrorActionPreference='Stop'
if(-not $RunId -or $RunId -notmatch '^[A-Za-z0-9_-]+$'){throw 'Supply a new simple RunId.'}
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $projectRoot
$env:PYTHONPYCACHEPREFIX=Join-Path $projectRoot 'output/pycache'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONPATH=Join-Path $projectRoot 'research'
$env:MPLCONFIGDIR=Join-Path $projectRoot 'output/mplcache'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$pythonExe='D:/ProgramData/anaconda3/python.exe'
$runPath=Join-Path $projectRoot ('output/experiments/'+$RunId)
if(-not (Test-Path -LiteralPath (Join-Path $runPath 'stage_diagnostics/plan.json'))){
    & $pythonExe research/grayref_simplified_evidence_support/grayref_simplified_evidence_stage_audit.py --run $runPath --declare-only
    if($LASTEXITCODE -ne 0){throw 'Diagnostic declaration failed'}
}
if(-not (Test-Path -LiteralPath (Join-Path $runPath 'containment_diagnostics/plan.json'))){
    & $pythonExe research/grayref_simplified_evidence_support/grayref_simplified_containment_audit.py --run $runPath --declare-only
    if($LASTEXITCODE -ne 0){throw 'Containment declaration failed'}
}
& $pythonExe -m grayref_simplified_evidence_v0.run_all --run-id $RunId --workers $Workers
if($LASTEXITCODE -ne 0){throw 'Core run failed; preserve output for diagnosis'}
& $pythonExe research/grayref_simplified_evidence_support/grayref_simplified_noise_controls.py --run $runPath
if($LASTEXITCODE -ne 0){throw 'Supplementary noise controls failed'}
if(-not (Test-Path -LiteralPath (Join-Path $runPath 'point_source_independent_verification.json'))){
    & $pythonExe research/grayref_simplified_evidence_support/grayref_simplified_point_source_verify.py --run $runPath
    if($LASTEXITCODE -ne 0){throw 'P-source verification failed'}
}
& $pythonExe research/grayref_simplified_evidence_support/grayref_simplified_evidence_stage_audit.py --run $runPath
if($LASTEXITCODE -ne 0){throw 'Read-only stage audit failed'}
& $pythonExe research/grayref_simplified_evidence_support/grayref_simplified_containment_audit.py --run $runPath
if($LASTEXITCODE -ne 0){throw 'Containment audit failed'}
if(-not (Test-Path -LiteralPath (Join-Path $runPath 'real_repeat_determinism.json'))){
    & $pythonExe research/grayref_simplified_evidence_support/grayref_simplified_determinism_check.py --run $runPath
    if($LASTEXITCODE -ne 0){throw 'Real repeat determinism failed'}
}
& $pythonExe research/grayref_simplified_evidence_support/grayref_simplified_evidence_videos.py --run $runPath
if($LASTEXITCODE -ne 0){throw 'Video creation failed'}
& $pythonExe research/grayref_simplified_evidence_support/grayref_simplified_offline_overlays.py --run $runPath
if($LASTEXITCODE -ne 0){throw 'Offline label overlays failed'}
& $pythonExe research/grayref_simplified_evidence_support/grayref_simplified_mechanism_summary.py --run $runPath
if($LASTEXITCODE -ne 0){throw 'Mechanism summary failed'}
