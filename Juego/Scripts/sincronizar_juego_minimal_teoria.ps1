# Copia Juego/ del repo TFG a la instalacion descomprimida de Teoria.
# Uso (PowerShell):
#   .\Juego\Scripts\sincronizar_juego_minimal_teoria.ps1

$ErrorActionPreference = "Stop"
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$destino = Join-Path $env:USERPROFILE "Documents\UAB\Running\ModSim-SDiN (25-26) ▶️\Sistemes Distribuits i el Nuvol ❌\Teoria\MATCAD_juego_minimal"
$origen = Join-Path $repo "Juego"

if (-not (Test-Path $origen)) {
    Write-Error "No se encuentra $origen"
}
if (-not (Test-Path $destino)) {
    Write-Error "No se encuentra $destino"
}

$backup = Join-Path $destino ("Juego_backup_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
if (Test-Path (Join-Path $destino "Juego")) {
    Rename-Item (Join-Path $destino "Juego") $backup
}
Copy-Item $origen $destino -Recurse
Get-ChildItem (Join-Path $destino "Juego") -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "OK: Juego sincronizado en"
Write-Host "  $destino"
Write-Host "Copia anterior (si existia): $backup"
Write-Host "Cierra el juego y vuelve a ejecutar Jugar.bat"
