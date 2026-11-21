param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$projectDir=(Get-Item -LiteralPath $PSScriptRoot)
while (-not (Test-Path -LiteralPath (Join-Path $projectDir.FullName 'config/project.json'))) {
 $projectDir=$projectDir.Parent
 if ($null -eq $projectDir) { throw 'Project root unavailable' }
}
Set-Location -LiteralPath $projectDir.FullName
$buildPath=[IO.Path]::GetFullPath($Output)
$allowed=[IO.Path]::GetFullPath((Join-Path $projectDir.FullName 'output'))+[IO.Path]::DirectorySeparatorChar
if (-not $buildPath.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)) { throw 'Build must be inside project output' }
$cmake=(Get-Content -LiteralPath 'config/project.json' -Raw | ConvertFrom-Json).cmake_executable
& $cmake -S $PSScriptRoot -B $buildPath -G 'Visual Studio 17 2022' -A x64 -T v142
if ($LASTEXITCODE -ne 0) { throw 'CMake configure failed' }
& $cmake --build $buildPath --config Release
if ($LASTEXITCODE -ne 0) { throw 'CMake build failed' }
