$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "找不到虚拟环境 Python: $pythonExe"
}

Set-Location $projectRoot

Write-Host "Starting API server at http://127.0.0.1:8000"
& $pythonExe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
