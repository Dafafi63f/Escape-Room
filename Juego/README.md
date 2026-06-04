# Juego — consola MATCAD

Todo lo necesario para **jugar** en terminal (y, opcionalmente, empaquetar un `.exe`).

| Elemento | Descripción |
|----------|-------------|
| [`juego_cuestionario.py`](juego_cuestionario.py) | Lanzador: menú principal y arranque de modos |
| [`Consola/`](Consola/README.md) | Paquete Python con la lógica del juego (`from Consola...`) |
| [`Informes/`](Informes/README.md) | Informes `.txt` de partidas (local, gitignored) |
| [`Tests/`](Tests/README.md) | Pruebas unitarias |
| [`build_exe_onefile.ps1`](build_exe_onefile.ps1) | Genera `juego_cuestionario.exe` con PyInstaller |

## Jugar

Desde la raíz del TFG:

```bash
python Juego/juego_cuestionario.py
```

Requisito: Python 3.10+, solo biblioteca estándar. Datos en [`../Data/README.md`](../Data/README.md).

Modos en el menú: **libre** (implementado), **historia** (examen balanceado), **feedback** (en desarrollo).

## Ejecutable (opcional)

### Requisitos

| Requisito | Notas |
|-----------|--------|
| Windows | El build usa PowerShell |
| Python 3.10+ | Comando `python` en el PATH |
| pip | Instala PyInstaller si falta |
| PyInstaller | Lo instala el script: `pip install pyinstaller` |
| `../Data/` | Se empaqueta entero si no hay `Juego/Data/` ni CSV sueltos en `Juego/` |

### Comando

```powershell
cd Juego
.\build_exe_onefile.ps1
```

Genera `juego_cuestionario.exe` en esta carpeta. Incluye `Data/` del proyecto (preguntas, materias, plantillas, histórico CSV). Los informes se escriben en `Informes/` **junto al `.exe`** al ejecutarlo.

### Artefactos de build

Tras un build correcto, `build_exe_onefile.ps1` **borra** `build/`, `juego_cuestionario.spec` y `dist/` si existen. Solo queda `juego_cuestionario.exe` en `Juego/`.

| Elemento | En git |
|----------|--------|
| `juego_cuestionario.exe` | Ignorado (`*.exe`) |
| `build/`, `*.spec` | Ignorados por si quedan restos |

## Limpieza de cachés Python

Desde la raíz del TFG:

```bash
python borrar_pycache.py
```
