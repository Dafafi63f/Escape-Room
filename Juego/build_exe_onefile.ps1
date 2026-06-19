$ErrorActionPreference = "Stop"

$gameDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $gameDir
Set-Location $gameDir

Write-Host "==> Carpeta de juego: $gameDir"
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

Write-Host "==> Limpiando build anterior..."
if (Test-Path $buildDir) { Remove-Item $buildDir -Recurse -Force }
if (Test-Path (Join-Path $gameDir "$exeName.exe")) {
    Remove-Item (Join-Path $gameDir "$exeName.exe") -Force
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

$filesDir = Join-Path $projectRoot "Files"
if (-not (Test-Path (Join-Path $filesDir "utils_plantillas_core.py"))) {
    throw "No se encontró Files/utils_plantillas_core.py (requerido por Comun/datos.py)."
}

python -m PyInstaller `
  --onefile `
  --windowed `
  --name $exeName `
  --collect-all pygame `
  --paths "$filesDir" `
  --hidden-import Comun `
  --hidden-import Grafico `
  --hidden-import utils_plantillas_core `
  --workpath "$buildDir" `
  --distpath "$gameDir" `
  --specpath "$specDir" `
  @addDataArgs `
  "$gameDir\juego_grafico.py"

if ($LASTEXITCODE -ne 0) {
    throw "Fallo al generar el ejecutable."
}

Write-Host "==> Limpiando artefactos de build (build/, .spec)..."
if (Test-Path $buildDir) { Remove-Item $buildDir -Recurse -Force }
$specFile = Join-Path $gameDir "$exeName.spec"
if (Test-Path $specFile) { Remove-Item $specFile -Force }
if (Test-Path (Join-Path $gameDir "dist")) {
    Remove-Item (Join-Path $gameDir "dist") -Recurse -Force
}

Write-Host ""
Write-Host "Listo. Ejecutable generado en:"
Write-Host "  $gameDir\$exeName.exe"
Write-Host ""
Write-Host "Distribución recomendada:"
Write-Host "  - Copia $exeName.exe"
Write-Host "  - Si no empaquetaste Data/, añade la carpeta Data/ del repo junto al .exe"
Write-Host "  - Al jugar se creará Data/Juego/ (informes, rankings, preferencias) junto al .exe"
