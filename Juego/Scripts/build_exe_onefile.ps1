param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$scriptsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$gameDir = Split-Path -Parent $scriptsDir
$projectRoot = Split-Path -Parent $gameDir
$distDir = Join-Path $gameDir "Distribucion"
if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir -Force | Out-Null
}
Set-Location $gameDir

Write-Host "==> Carpeta de juego: $gameDir"
Write-Host "==> Distribución: $distDir"
Write-Host "==> Raíz del proyecto: $projectRoot"

# Asegura que PyInstaller esté disponible.
$pyiOk = $false
try {
    python -m PyInstaller --version | Out-Null
    if ($LASTEXITCODE -eq 0) { $pyiOk = $true }
} catch { $pyiOk = $false }
if (-not $pyiOk) {
    Write-Host "==> Instalando PyInstaller..."
    python -m pip install pyinstaller
}

$buildDir = Join-Path $gameDir "build"
$specDir = $gameDir
$exeName = "juego_grafico"
$exePath = Join-Path $distDir "$exeName.exe"

if ($Force) {
    Write-Host "==> Reconstrucción forzada: limpiando caché de PyInstaller..."
    if (Test-Path $buildDir) { Remove-Item $buildDir -Recurse -Force }
}

if (Test-Path $exePath) {
    Remove-Item $exePath -Force
}
if (Test-Path (Join-Path $gameDir "dist")) {
    Remove-Item (Join-Path $gameDir "dist") -Recurse -Force
}

Write-Host "==> Generando ejecutable onefile (pygame)..."
$addDataArgs = @()

# Datos del banco y estado local (estructura canónica Data/Banco + Data/Juego).
$dataDir = Join-Path $projectRoot "Data"
if (Test-Path $dataDir) {
    $addDataArgs += @("--add-data", "$dataDir;Data")
} else {
    $localDataDir = Join-Path $gameDir "Data"
    if (Test-Path $localDataDir) {
        $addDataArgs += @("--add-data", "$localDataDir;Data")
    }
}

# Changelog del jugador (pantalla Info); opcional si existe.
$changelogJuego = Join-Path $projectRoot "Docs\CHANGELOG_JUEGO.md"
if (Test-Path $changelogJuego) {
    $addDataArgs += @("--add-data", "$changelogJuego;Docs")
}

if ($addDataArgs.Count -eq 0) {
    Write-Warning "No se encontró carpeta Data/. El .exe necesitará Data/ junto al ejecutable."
}

python -m PyInstaller `
  --onefile `
  --windowed `
  --name $exeName `
  --collect-all pygame `
  --hidden-import Comun `
  --hidden-import Comun.utils_plantillas_core `
  --hidden-import Grafico `
  --workpath "$buildDir" `
  --distpath "$distDir" `
  --specpath "$specDir" `
  --noconfirm `
  @addDataArgs `
  "$gameDir\juego_grafico.py"

if ($LASTEXITCODE -ne 0) {
    throw "Fallo al generar el ejecutable."
}

Write-Host "==> Limpiando artefactos temporales (.spec, dist/)..."
$specFile = Join-Path $gameDir "$exeName.spec"
if (Test-Path $specFile) { Remove-Item $specFile -Force }
if (Test-Path (Join-Path $gameDir "dist")) {
    Remove-Item (Join-Path $gameDir "dist") -Recurse -Force
}

Write-Host ""
Write-Host "Listo. Ejecutable generado en:"
Write-Host "  $exePath"
Write-Host "  (Juego/build/ se borra en la limpieza final para ahorrar espacio; --conservar-cache-exe para conservarla)"
Write-Host ""
Write-Host "Distribución recomendada:"
Write-Host "  - Copia $exeName.exe"
Write-Host "  - Si no empaquetaste Data/, añade la carpeta Data/ del repo junto al .exe"
Write-Host "  - Al jugar se creará Data/Juego/ (informes, rankings, preferencias) junto al .exe"
