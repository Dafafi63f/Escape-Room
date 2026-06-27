# Comprueba si el PC puede ejecutar el juego con Python (no modifica el sistema).
# Uso: powershell -ExecutionPolicy Bypass -File Juego\scripts\comprobar_entorno.ps1

$ErrorActionPreference = "Continue"
$scriptsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$gameDir = Split-Path -Parent $scriptsDir
$proyecto = Split-Path -Parent $gameDir
Set-Location $proyecto

function Test-Cmd($nombre) {
    $c = Get-Command $nombre -ErrorAction SilentlyContinue
    return [bool]$c
}

Write-Host "=== Comprobacion de entorno - MATCAD ===" -ForegroundColor Cyan
Write-Host "Carpeta del proyecto: $proyecto`n"

$pythonOk = $false
$pythonExe = $null

foreach ($candidato in @("py", "python", "python3")) {
    if (-not (Test-Cmd $candidato)) { continue }
    try {
        $ver = & $candidato -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if (-not $ver) { $ver = & $candidato -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null }
        if ($ver) {
            $parts = $ver.Trim() -split "\."
            $mayor = [int]$parts[0]
            $menor = [int]$parts[1]
            if ($mayor -gt 3 -or ($mayor -eq 3 -and $menor -ge 10)) {
                $pythonOk = $true
                $pythonExe = $candidato
                Write-Host "OK: Python $ver ($candidato)" -ForegroundColor Green
            } else {
                Write-Host "AVISO: Python $ver demasiado antiguo (se requiere 3.10+)" -ForegroundColor Yellow
            }
            break
        }
    } catch {}
}

if (-not $pythonOk) {
    Write-Host "FALTA: Python 3.10+ no encontrado en PATH" -ForegroundColor Red
    Write-Host "    Instala desde https://www.python.org/downloads/ o ejecuta:" -ForegroundColor Gray
    Write-Host "    powershell -ExecutionPolicy Bypass -File Juego\scripts\instalar_entorno.ps1`n" -ForegroundColor Gray
}

$pipOk = $false
if ($pythonOk) {
    foreach ($pip in @("pip", "pip3")) {
        if (Test-Cmd $pip) { $pipOk = $true; Write-Host "OK: $pip disponible" -ForegroundColor Green; break }
    }
    if (-not $pipOk) {
        $pipTest = & $pythonExe -3 -m pip --version 2>$null
        if ($pipTest) {
            $pipOk = $true
            Write-Host "OK: pip via $pythonExe -m pip" -ForegroundColor Green
        } else {
            Write-Host "FALTA: pip no encontrado" -ForegroundColor Red
        }
    }
}

$pygameOk = $false
if ($pythonOk) {
    $pygameTest = & $pythonExe -3 -c "import pygame; print(pygame.version.ver)" 2>$null
    if (-not $pygameTest) {
        $pygameTest = & $pythonExe -c "import pygame; print(pygame.version.ver)" 2>$null
    }
    if ($pygameTest) {
        $pygameOk = $true
        Write-Host "OK: pygame instalado ($pygameTest)" -ForegroundColor Green
    } else {
        Write-Host "AVISO: pygame no instalado. Ejecuta:" -ForegroundColor Yellow
        Write-Host "    pip install -r Juego/requirements.txt" -ForegroundColor Gray
    }
}

$dataOk = (Test-Path "Data\Banco\Preguntas.csv") -and (Test-Path "Data\Banco\listado_materias.csv")
if ($dataOk) {
    Write-Host "OK: Data\Banco\ presente" -ForegroundColor Green
} else {
    Write-Host "FALTA: archivos en Data\Banco\" -ForegroundColor Red
}

$exeOk = Test-Path "Juego\Distribucion\juego_grafico.exe"
if ($exeOk) {
    Write-Host "OK: Juego\Distribucion\juego_grafico.exe (alternativa sin Python)" -ForegroundColor Green
} else {
    Write-Host "INFO: sin juego_grafico.exe (normal en zip portable)" -ForegroundColor DarkGray
}

Write-Host "`n--- Politica de ejecucion ---" -ForegroundColor Cyan
Write-Host "Si Python o los .exe estan bloqueados por el centro, ninguna opcion"
Write-Host "funcionara sin intervencion del administrador."

if ($pythonOk -and $pygameOk -and $dataOk) {
    Write-Host "`nListo para: python Juego\juego_grafico.py" -ForegroundColor Green
    exit 0
}
if ($exeOk -and $dataOk) {
    Write-Host "`nListo para: Juego\Distribucion\juego_grafico.exe" -ForegroundColor Green
    exit 0
}
Write-Host "`nEntorno incompleto. Ver Juego\LEEME.txt o Juego\COMO_JUGAR.md" -ForegroundColor Yellow
exit 1
