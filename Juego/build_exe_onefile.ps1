$ErrorActionPreference = "Stop"

$gameDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $gameDir
Set-Location $gameDir

Write-Host "==> Carpeta de juego: $gameDir"

# Asegura que PyInstaller esté disponible.
python -m pip show pyinstaller *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "==> Instalando PyInstaller..."
    python -m pip install pyinstaller
}

$buildDir = Join-Path $gameDir "build"
$specDir = $gameDir

Write-Host "==> Limpiando build anterior..."
if (Test-Path $buildDir) { Remove-Item $buildDir -Recurse -Force }
if (Test-Path (Join-Path $gameDir "juego_cuestionario.exe")) {
    Remove-Item (Join-Path $gameDir "juego_cuestionario.exe") -Force
}
# Limpia dist heredado de builds anteriores.
if (Test-Path (Join-Path $gameDir "dist")) {
    Remove-Item (Join-Path $gameDir "dist") -Recurse -Force
}

Write-Host "==> Generando ejecutable onefile..."
$addDataArgs = @()

# Prioriza datos locales de la carpeta de entrega.
$localDataDir = Join-Path $gameDir "Data"
if (Test-Path $localDataDir) {
    $addDataArgs += @("--add-data", "$localDataDir;Data")
}

$localPreguntas = Join-Path $gameDir "Preguntas.csv"
if (Test-Path $localPreguntas) {
    $addDataArgs += @("--add-data", "$localPreguntas;.")
}

$localMaterias = Join-Path $gameDir "listado_materias.csv"
if (Test-Path $localMaterias) {
    $addDataArgs += @("--add-data", "$localMaterias;.")
}

# Fallback opcional para entorno personal si no hay datos locales.
if ($addDataArgs.Count -eq 0) {
    $legacyDataDir = Join-Path $projectRoot "Data"
    if (Test-Path $legacyDataDir) {
        Write-Host "==> No hay datos locales, usando fallback: $legacyDataDir"
        $addDataArgs += @("--add-data", "$legacyDataDir;Data")
    }
}

python -m PyInstaller `
  --onefile `
  --name "juego_cuestionario" `
  --workpath "$buildDir" `
  --distpath "$gameDir" `
  --specpath "$specDir" `
  @addDataArgs `
  "$gameDir\juego_cuestionario.py"

if ($LASTEXITCODE -ne 0) {
    throw "Fallo al generar el ejecutable."
}

Write-Host ""
Write-Host "Listo. Ejecutable generado en:"
Write-Host "  $gameDir\juego_cuestionario.exe"
Write-Host ""
Write-Host "Puedes compartir directamente ese .exe."
