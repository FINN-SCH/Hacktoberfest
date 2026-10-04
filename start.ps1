$ErrorActionPreference = 'Stop'
$repoRoot = $PSScriptRoot
$pythonExe = Join-Path $repoRoot 'backend/.venv/Scripts/python.exe'
$frontendDir = Join-Path $repoRoot 'frontend'
$indexFile = Join-Path $frontendDir 'dist/index.html'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Missing backend/.venv. Follow SETUP_GUIDE.md Windows setup.' }
if (-not (Test-Path -LiteralPath (Join-Path $frontendDir 'node_modules'))) { throw 'Missing frontend/node_modules. Run npm.cmd ci in frontend.' }
$null = Get-Command node -ErrorAction Stop
$null = Get-Command npm.cmd -ErrorAction Stop
$nodeVersion = (& node --version).TrimStart('v').Split('.')
if ([int]$nodeVersion[0] -lt 22 -or ([int]$nodeVersion[0] -eq 22 -and [int]$nodeVersion[1] -lt 11)) {
    throw 'Node.js 22.11+ is required.'
}
& $pythonExe -c 'import sys; assert sys.version_info >= (3,10)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.10+ is required.' }
if (-not $env:npm_config_prefix -and (Test-Path -LiteralPath 'C:/Program Files/nodejs/npm.cmd')) {
    $env:npm_config_prefix = 'C:/Program Files/nodejs'
}
$needsBuild = -not (Test-Path -LiteralPath $indexFile)
foreach ($asset in @('silero_vad_v5.onnx', 'vad.worklet.bundle.min.js')) {
    if (-not (Test-Path -LiteralPath (Join-Path $frontendDir "dist/vad/$asset"))) { $needsBuild = $true }
}
foreach ($extension in @('wasm', 'mjs')) {
    if (-not (Get-ChildItem -Path (Join-Path $frontendDir "dist/vad/ort-wasm*.$extension") -File -ErrorAction SilentlyContinue)) { $needsBuild = $true }
}
if (-not $needsBuild) {
    $builtAt = (Get-Item -LiteralPath $indexFile).LastWriteTimeUtc
    $inputs = @()
    foreach ($directory in @('src', 'public', 'scripts')) {
        $inputs += Get-ChildItem -LiteralPath (Join-Path $frontendDir $directory) -File -Recurse
    }
    foreach ($file in @('package.json', 'package-lock.json', 'index.html', 'vite.config.ts', 'tsconfig.json')) {
        $inputs += Get-Item -LiteralPath (Join-Path $frontendDir $file)
    }
    $needsBuild = [bool]($inputs | Where-Object { $_.LastWriteTimeUtc -gt $builtAt } | Select-Object -First 1)
}
if ($needsBuild) {
    Write-Host 'Building frontend (missing or stale dist)...'
    Push-Location $frontendDir
    try {
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed. Resolve the error before starting the app.' }
    } finally { Pop-Location }
} else { Write-Host 'Frontend build is current.' }
Push-Location (Join-Path $repoRoot 'backend')
try {
    @'
from app.config import Settings
s = Settings()
print(f"Tutor URL: http://{s.host}:{s.port} (Ctrl+C to stop)")
'@ | & $pythonExe -
    if ($LASTEXITCODE -ne 0) { throw 'Invalid backend settings. Check backend/.env without sharing its values.' }
    & $pythonExe -m app.main
    $launchExit = $LASTEXITCODE
} finally { Pop-Location }
exit $launchExit
