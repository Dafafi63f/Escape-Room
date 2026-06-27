@echo off
setlocal
cd /d "%~dp0\.."

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 juego_grafico.py
    goto :fin
)

where python >nul 2>&1
if %errorlevel%==0 (
    python juego_grafico.py
    goto :fin
)

echo.
echo No se encontro Python en el PATH.
echo.
echo 1. Instala Python 3.10+ desde https://www.python.org/downloads/
echo    (marca "Add python.exe to PATH").
echo 2. En la carpeta del paquete (un nivel arriba de Juego\):
echo      pip install -r Juego\requirements.txt
echo 3. Vuelve a ejecutar Juego\Distribucion\Jugar.bat
echo.
echo O lee Juego\LEEME.txt
echo.

:fin
if errorlevel 1 pause
