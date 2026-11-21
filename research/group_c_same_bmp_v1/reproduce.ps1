param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference = 'Stop'
$projectDir = (Get-Item -LiteralPath $PSScriptRoot).Parent
while (-not (Test-Path -LiteralPath (Join-Path $projectDir.FullName 'config/project.json'))) {
    $projectDir = $projectDir.Parent
    if ($null -eq $projectDir) { throw 'Cannot locate active CodexCrack project' }
}
Set-Location -LiteralPath $projectDir.FullName
$auditConfig = Get-Content -LiteralPath 'config/project.json' -Raw | ConvertFrom-Json
$auditPython = $auditConfig.python_executable
$env:PYTHONPYCACHEPREFIX = Join-Path $projectDir.FullName 'output/pycache'
$env:PYTHONIOENCODING = 'utf-8'
$env:GROUP_C_AUDIT_OUTPUT = $Output
function Invoke-AuditStep([string]$File, [string]$Mode = '') {
    $auditScript = Join-Path $PSScriptRoot $File
    if ($Mode) { & $auditPython $auditScript $Mode } else { & $auditPython $auditScript }
    if ($LASTEXITCODE -ne 0) { throw "Audit stage failed: $File $Mode" }
}
Invoke-AuditStep 'run.py' 'primary'
Invoke-AuditStep 'run.py' 'controlled'
Invoke-AuditStep 'run.py' 'sensitivity'
Invoke-AuditStep 'run.py' 'sentinels'
Invoke-AuditStep 'analyze.py'
Invoke-AuditStep 'controls_audit.py'
Invoke-AuditStep 'visualize.py'
Invoke-AuditStep 'report.py'
Invoke-AuditStep 'seal.py'
