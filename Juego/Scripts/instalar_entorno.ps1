# Intenta preparar Python + pygame para jugar. Puede pedir permisos de administrador.
# Uso: powershell -ExecutionPolicy Bypass -File Juego\scripts\instalar_entorno.ps1
#      powershell -ExecutionPolicy Bypass -File Juego\scripts\instalar_entorno.ps1 -SoloComprobar

param(
    [switch]$SoloComprobar,
    [switch]$OmitirPython
)

$ErrorActionPreference = "Stop"
$scriptsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$gameDir = Split-Path -Parent $scriptsDir
$proyecto = Split-Path -Parent $gameDir
Set-Location $proyecto

function Invoke-Comprobar {
    & "$scriptsDir\comprobar_entorno.ps1"
    exit $LASTEXITCODE
}

if ($SoloComprobar) {
    Invoke-Comprobar
}

Write-Host "=== Instalacion de entorno — MATCAD ===" -ForegroundColor Cyan

$pythonCmd = $null
foreach ($candidato in @("py", "python", "python3")) {
    if (-not (Get-Command $candidato -ErrorAction SilentlyContinue)) { continue }
    try {
        $null = & $candidato -3 -c "import sys; assert sys.version_info >= (3, 10)" 2>$null
        if ($LASTEXITCODE -eq 0) { $pythonCmd = "$candidato -3"; break }
        $null = & $candidato -c "import sys; assert sys.version_info >= (3, 10)" 2>$null
        if ($LASTEXITCODE -eq 0) { $pythonCmd = $candidato; break }
    } catch {}
}

if (-not $pythonCmd -and -not $OmitirPython) {
    Write-Host "Python 3.10+ no detectado." -ForegroundColor Yellow
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "Intentando instalar Python con winget (puede pedir confirmacion UAC)..." -ForegroundColor Cyan
        winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
        if ($LASTEXITCODE -ne 0) {
            Write-Host "winget no pudo instalar Python. Instalalo manualmente:" -ForegroundColor Red
            Write-Host "  https://www.python.org/downloads/" -ForegroundColor Gray
            Write-Host "  Marca 'Add python.exe to PATH' y vuelve a ejecutar este script."
            exit 1
        }
        Write-Host "Cierra y abre una nueva terminal, luego ejecuta de nuevo este script." -ForegroundColor Yellow
        exit 0
    }
    Write-Host "winget no disponible. Descarga Python manualmente:" -ForegroundColor Red
    Write-Host "  https://www.python.org/downloads/windows/" -ForegroundColor Gray
    Start-Process "https://www.python.org/downloads/"
    exit 1
}

if (-not $pythonCmd) {
    Write-Host "Python no disponible (usa -OmitirPython solo si ya lo instalaste en otra ventana)." -ForegroundColor Red
    exit 1
}

Write-Host "Usando: $pythonCmd" -ForegroundColor Green

$req = Join-Path $gameDir "requirements.txt"
if (-not (Test-Path $req)) {
    Write-Host "No se encuentra Juego/requirements.txt" -ForegroundColor Red
    exit 1
}

Write-Host "Instalando dependencias del juego (Juego/requirements.txt)..." -ForegroundColor Cyan
& $pythonCmd -m pip install --upgrade pip
& $pythonCmd -m pip install -r $req
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error en pip install." -ForegroundColor Red
    exit 1
}

Write-Host "`nInstalacion completada. Arranque:" -ForegroundColor Green
Write-Host "  $pythonCmd Juego\juego_grafico.py"
Write-Host "  o doble clic en Juego\Distribucion\Jugar.bat`n"
Invoke-Comprobar
