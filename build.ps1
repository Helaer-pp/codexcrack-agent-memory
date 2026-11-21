param([string]$Configuration='Release')
$ErrorActionPreference='Stop'
$projectRoot=$PSScriptRoot
$taskTemp=Join-Path $projectRoot 'output/cache/tmp'
New-Item -ItemType Directory -Force -Path $taskTemp | Out-Null
$env:TEMP=$taskTemp;$env:TMP=$taskTemp
$cfg=Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'config/project.json') | ConvertFrom-Json
$buildPath=[IO.Path]::GetFullPath((Join-Path $projectRoot 'output/build'))
if (-not $buildPath.StartsWith(([IO.Path]::GetFullPath($projectRoot)+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase)) {throw 'Build path outside project'}
& $cfg.cmake_executable -S $projectRoot -B $buildPath -G 'Visual Studio 17 2022' -A x64 -T v142
if ($LASTEXITCODE -ne 0) {throw 'CMake configuration failed'}
& $cfg.cmake_executable --build $buildPath --config $Configuration --target GrayDetectionV2 CrackV4Example CrackReadOnlyBench -- /m:1 /nodeReuse:false
if ($LASTEXITCODE -ne 0) {throw 'C++ build failed'}
