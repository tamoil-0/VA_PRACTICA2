$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$python = "python"
$ports = @(8501, 8502, 8503, 8504)
$port = $null

foreach ($candidate in $ports) {
    $connection = Get-NetTCPConnection -LocalPort $candidate -ErrorAction SilentlyContinue
    if (-not $connection) {
        $port = $candidate
        break
    }
}

if (-not $port) {
    $port = 8505
}

Write-Host ""
Write-Host "Iniciando aplicacion de Visualizacion de Datos..." -ForegroundColor Cyan
Write-Host "Carpeta: $PSScriptRoot"
Write-Host "URL: http://localhost:$port"
Write-Host ""

Start-Process "http://localhost:$port"
& $python -m streamlit run app.py --server.port $port --server.headless false
