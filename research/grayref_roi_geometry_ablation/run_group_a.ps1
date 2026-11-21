param([Parameter(Mandatory=$true)][string]$RunId,[int]$Workers=12,[switch]$Resume)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $projectRoot
$env:PYTHONPYCACHEPREFIX=Join-Path $projectRoot 'output/pycache'
$env:PYTHONPATH=Join-Path $projectRoot 'research'
$env:PYTHONIOENCODING='utf-8'
$env:MPLCONFIGDIR=Join-Path $projectRoot 'output/mplcache'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$pythonExe=(Get-Content -LiteralPath 'config/project.json' -Raw | ConvertFrom-Json).python_executable
$runArgs=@('-m','grayref_roi_geometry_ablation.run','--run-id',$RunId,'--workers',"$Workers",'--phase','group_a')
if($Resume){$runArgs+='--resume'}
& $pythonExe @runArgs
if($LASTEXITCODE -ne 0){throw 'GROUP_A experiment failed; preserve evidence and inspect error'}
