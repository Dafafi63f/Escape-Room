# Cómo jugar — requisitos y formas de ejecución

Guía para **usuarios finales** (no para desarrollo del TFG). El mantenimiento del banco está en [`Files/README.md`](../Files/README.md).

## Resumen rápido

| Forma | Necesitas | Comando / acción |
|-------|-----------|------------------|
| **Zip completo o mínimo** | Python 3.10+ y pygame | `pip install -r Juego/requirements.txt` → doble clic en `Jugar.bat` o `python Juego/juego_grafico.py` |
| **Repositorio clonado** | Igual | `pip install -r Juego/requirements.txt` → `python Juego/juego_grafico.py` |

Hay dos paquetes distintos (puedes tener ambos instalados en carpetas separadas):

| Zip | Contenido |
|-----|-----------|
| `MATCAD_juego_portable.zip` | Juego **completo** (`Data/` + `Juego/`) |
| `MATCAD_juego_minimal.zip` | Juego **mínimo** (CSV + motor reducido) |

## Requisitos de software

| Requisito | Detalle |
|-----------|---------|
| **Python** | 3.10 o superior (3.12+ recomendado). [python.org/downloads](https://www.python.org/downloads/) |
| **pip** | Suele venir con Python. Comprueba con `python -m pip --version` |
| **pygame-ce** | `pip install -r Juego/requirements.txt` |
| **Sistema** | Windows 10/11; también Linux/macOS con los mismos comandos |
| **Red** | Solo la primera vez (descarga de pygame). Después el juego es **offline** |

Los zips **no incluyen** Python ni scripts de empaquetado. Sí incluyen [`Jugar.bat`](Distribucion/Jugar.bat) para arrancar con doble clic en Windows.

## Arrancar en Windows (recomendado)

1. Descomprime el zip en una carpeta propia.
2. Instala Python si no lo tienes (marca «Add python.exe to PATH»).
3. Abre CMD o PowerShell en la carpeta del paquete y ejecuta **una sola vez**:
   ```bash
   pip install -r Juego/requirements.txt
   ```
4. Arranca el juego:
   - **Doble clic** en `Juego/Distribucion/Jugar.bat` (zip completo), o en `Jugar.bat` (zip mínimo).
   - O desde terminal: `python Juego/juego_grafico.py`

## Pasos detallados — zip completo

1. Descomprime `Juego/Distribucion/MATCAD_juego_portable.zip`.
2. Debes ver `Data/` y `Juego/` en la misma carpeta.
3. Lee [`LEEME.txt`](LEEME.txt).
4. Instala dependencias y arranca (ver arriba).

## Pasos detallados — zip mínimo

1. Descomprime `MATCAD_juego_minimal.zip` → carpeta `MATCAD_minimal/`.
2. Instala dependencias: `pip install -r Juego/requirements.txt`.
3. Doble clic en `Jugar.bat` o `python Juego/juego_grafico.py`.

## Repositorio clonado

```bash
git clone https://github.com/Dafafi63f/Escape-Room.git
cd Escape-Room
pip install -r Juego/requirements.txt
python Juego/juego_grafico.py
```

Para **desarrollo** (tests, memoria, mantenimiento): `pip install -r requirements.txt` en la raíz del repo.

## Scripts de ayuda (Windows, solo repositorio)

```powershell
# Diagnóstico (no modifica nada)
powershell -ExecutionPolicy Bypass -File Juego\Scripts\comprobar_entorno.ps1

# Instalar Python (winget, si está disponible) + dependencias
powershell -ExecutionPolicy Bypass -File Juego\Scripts\instalar_entorno.ps1
```

## Limitaciones en PCs corporativos

| Bloqueo | Efecto |
|---------|--------|
| Sin Python instalado | Hay que instalar Python (puede requerir permisos) |
| `pip` bloqueado o sin internet | No se puede instalar pygame |
| PowerShell / scripts bloqueados | Usa el instalador manual de Python y `Jugar.bat` |

En esos casos hace falta que informática permita Python en modo usuario o una excepción de política.

### ¿Se puede instalar Python “solo con comandos”?

**A veces**, en Windows 10/11 con [winget](https://learn.microsoft.com/es-es/windows/package-manager/winget/):

```powershell
winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
```

`Juego/Scripts/instalar_entorno.ps1` intenta eso si no detecta Python.

## Generar los zips (desarrollador)

```bash
python Docs/utilidades_tfg.py --solo-zip          # zips completo + mínimo
python Juego/Scripts/crear_zip_minimal.py         # zip mínimo
```

## Más información

- [`README.md`](README.md) — estructura del juego
- [`Data/README.md`](../Data/README.md) — archivos de datos
- [`Data/Plantillas/README.md`](../Data/Plantillas/README.md) — plantilla CSV para datos propios
