param(
 [ValidateSet('check','research')][string]$Command='check',
 [string]$Script='',
 [string]$RunId=''
)
$ErrorActionPreference='Stop'
$projectRoot=$PSScriptRoot
$cfg=Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'config/project.json') | ConvertFrom-Json
$env:PYTHONUTF8='1';$env:PYTHONDONTWRITEBYTECODE='1'
$taskTemp=Join-Path $projectRoot 'output/cache/tmp'
New-Item -ItemType Directory -Force -Path $taskTemp | Out-Null
$env:TEMP=$taskTemp;$env:TMP=$taskTemp
Push-Location -LiteralPath $projectRoot
try {
 if ($Command -eq 'check') {
  & $cfg.python_executable -B (Join-Path $projectRoot 'tests/check_project.py')
 } else {
  if ($RunId -notmatch '^[A-Za-z0-9_-]+$') {throw 'Provide a safe unique -RunId'}
  $allowed=@('setup_round','replay_ap','real_reference_audit','trace_tiles','engineering_dev')
  if ($Script -notin $allowed) {throw ('Allowed scripts: '+($allowed -join ', '))}
  $env:CRACK_RUN_ID=$RunId
  & $cfg.python_executable -B (Join-Path $projectRoot "research/aprime/experiments/$Script.py")
 }
 if ($LASTEXITCODE -ne 0) {throw 'Project command failed'}
} finally {Pop-Location}
