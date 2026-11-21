param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$projectDir=Get-Item -LiteralPath $PSScriptRoot
while (-not (Test-Path -LiteralPath (Join-Path $projectDir.FullName 'config/project.json'))) {
 $projectDir=$projectDir.Parent
 if ($null -eq $projectDir) { throw 'Cannot find active CodexCrack root' }
}
Set-Location -LiteralPath $projectDir.FullName
$target=[IO.Path]::GetFullPath($Output)
$allowed=[IO.Path]::GetFullPath((Join-Path $projectDir.FullName 'output'))+[IO.Path]::DirectorySeparatorChar
if (-not $target.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $target)) { throw 'Use a new output directory under the active project output/' }
New-Item -ItemType Directory -Path (Join-Path $target 'logs') | Out-Null
$python=(Get-Content -LiteralPath 'config/project.json' -Raw | ConvertFrom-Json).python_executable
$env:PYTHONPYCACHEPREFIX=Join-Path $projectDir.FullName 'output/pycache'
$env:PYTHONIOENCODING='utf-8'
$env:GRAYREF_V2_OUTPUT=$target
function Run-Step([string]$File,[string[]]$Arguments=@()) {
 $name=([IO.Path]::GetFileNameWithoutExtension($File))+'_'+($Arguments -join '_')
 & $python (Join-Path $PSScriptRoot $File) @Arguments *> (Join-Path $target ('logs/'+$name+'.log'))
 if ($LASTEXITCODE -ne 0) { throw "Stage failed: $name; see output logs" }
}
Run-Step 'preflight.py'
Run-Step 'test_modules.py'
Run-Step 'replay.py' @('freeze')
Run-Step 'replay.py' @('development')
Run-Step 'evaluate_v2.py'
Run-Step 'sentinels.py'
Run-Step 'replay.py' @('validation')
Run-Step 'evaluate_v2.py' @('--validation')
& (Join-Path $PSScriptRoot 'build.ps1') -Output (Join-Path $target 'cpp_build') *> (Join-Path $target 'logs/build.log')
Run-Step 'parity.py'
Run-Step 'numeric_kernel_audit.py'
Run-Step 'failure_audit.py'
Run-Step 'aggregate.py'
Run-Step 'media_v2.py'
Run-Step 'reference_gallery.py'
Run-Step 'report_v2.py'
Run-Step 'seal.py'
