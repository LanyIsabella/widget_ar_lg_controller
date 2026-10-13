$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}
Push-Location $projectRoot
try {
    & $python -m pip install -e ".[desktop,build]"
    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependências de build." }
    & $python -m PyInstaller --noconfirm --clean packaging\lg_ac_controller.spec
    if ($LASTEXITCODE -ne 0) { throw "Falha no empacotamento PyInstaller." }
}
finally {
    Pop-Location
}

Write-Host "Executável criado em dist\LGAcController.exe"
