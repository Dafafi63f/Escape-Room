@echo off
cd /d "%~dp0"
python -m pip install -r Juego\requirements.txt
if errorlevel 1 (
  echo Fallo al instalar dependencias. Comprueba que Python este en el PATH.
  pause
  exit /b 1
)
python Juego\juego_grafico.py
if errorlevel 1 pause
