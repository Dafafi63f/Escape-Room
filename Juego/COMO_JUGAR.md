# Cómo jugar — requisitos y formas de ejecución

Guía para **usuarios finales** (no para desarrollo del TFG). El mantenimiento del banco está en [`Files/README.md`](../Files/README.md).

## Resumen rápido

| Forma | Necesitas | Comando / acción |
|-------|-----------|------------------|
| **Repositorio o zip portable** | Python 3.10+ y pygame | `pip install -r Juego/requirements.txt` → `python Juego/juego_grafico.py` |
| **Ejecutable Windows** | Poder lanzar `.exe` | `Juego/Distribucion/juego_grafico.exe` (+ carpeta `Data/` si no va embebida) |
| **PC muy restringido** | — | Sin Python ni `.exe` permitidos → **no hay opción soportada** |

## Requisitos de software

### Opción Python (recomendada para el zip `Juego/Distribucion/MATCAD_juego_portable.zip`)

| Requisito | Detalle |
|-----------|---------|
| **Python** | 3.10 o superior (3.12+ recomendado). [python.org/downloads](https://www.python.org/downloads/) |
| **pip** | Suele venir con Python. Comprueba con `python -m pip --version` |
| **pygame-ce** | `pip install -r Juego/requirements.txt` |
| **Sistema** | Windows 10/11; también Linux/macOS con los mismos comandos |
| **Red** | Solo la primera vez (descarga de pygame). Después el juego es **offline** |

El zip portable incluye `Data/` y `Juego/` (código, [`requirements.txt`](requirements.txt), [`LEEME.txt`](LEEME.txt), esta guía, y `Distribucion/` con [`Jugar.bat`](Distribucion/Jugar.bat)). **No incluye** el intérprete Python, el `.exe`, ni la carpeta `Scripts/` (empaquetado o diagnóstico).

### Opción ejecutable (`juego_grafico.exe`)

| Requisito | Detalle |
|-----------|---------|
| **Windows** | 64 bits, 10/11 |
| **Permisos** | Ejecutar aplicaciones descargadas (SmartScreen puede avisar) |
| **Datos** | Carpeta `Data/` al lado del `.exe` si PyInstaller no la embebió |

No hace falta instalar Python ni pip. El `.exe` está en `Juego/Distribucion/`.

## Scripts de ayuda (Windows, solo repositorio completo)

En el **repositorio clonado** (no en el zip portable):

```powershell
# Diagnóstico (no modifica nada)
powershell -ExecutionPolicy Bypass -File Juego\Scripts\comprobar_entorno.ps1

# Instalar Python (winget, si está disponible) + dependencias
powershell -ExecutionPolicy Bypass -File Juego\Scripts\instalar_entorno.ps1
```

Atajo: doble clic en [`Distribucion/Jugar.bat`](Distribucion/Jugar.bat) (sube a la raíz de `Juego/` y lanza `juego_grafico.py`).

## Pasos detallados — zip portable

1. Descomprime `Juego/Distribucion/MATCAD_juego_portable.zip` (o la copia que te hayan entregado).
2. Lee [`LEEME.txt`](LEEME.txt) en la carpeta `Juego/`.
3. Instala Python si no lo tienes (instalador oficial desde python.org).
4. En la carpeta del paquete (donde está `Data/`):
   ```bash
   pip install -r Juego/requirements.txt
   python Juego/juego_grafico.py
   ```
   O doble clic en `Juego/Distribucion/Jugar.bat`.

## Pasos detallados — repositorio clonado

```bash
git clone https://github.com/Dafafi63f/Escape-Room.git
cd Escape-Room
pip install -r Juego/requirements.txt
python Juego/juego_grafico.py
```

Para **desarrollo** (tests, memoria, mantenimiento): `pip install -r requirements.txt` en la raíz del repo (incluye `-r Juego/requirements.txt` más pandas, matplotlib, PyInstaller, etc.).

## Limitaciones en PCs corporativos o del centro

| Bloqueo | Efecto |
|---------|--------|
| Sin Python instalado | La opción zip **no funciona** hasta instalar Python (puede requerir admin) |
| `pip` bloqueado o sin internet | No se puede instalar pygame |
| `.exe` no firmados bloqueados | `juego_grafico.exe` **no arranca** |
| PowerShell / scripts bloqueados | Usa el instalador de Python manual y `Jugar.bat` |

En esos casos hace falta que informática permita Python usuario, un `.exe` firmado, o una excepción de política. El proyecto **no puede** saltarse AppLocker o políticas de grupo de forma automática.

### ¿Se puede instalar Python “solo con comandos”?

**A veces**, en Windows 10/11 con [winget](https://learn.microsoft.com/es-es/windows/package-manager/winget/):

```powershell
winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
```

`Juego/Scripts/instalar_entorno.ps1` hace eso si no detecta Python. Limitaciones:

- Puede pedir **elevación (UAC)** o estar deshabilitado en el centro.
- Tras instalar, a veces hace falta **abrir una terminal nueva** para que el PATH se actualice.
- No sustituye a un instalador manual si winget no está disponible.

No hay forma fiable de instalar Python en **cualquier** PC aleatorio sin permisos de usuario o administrador.

## Generar el zip portable (desarrollador)

```bash
python Docs/utilidades_tfg.py --solo-zip
```

Crea `Juego/Distribucion/MATCAD_juego_portable.zip` con `Data/` y `Juego/` (sin `.exe`, `.ps1`, `Scripts/`, `build/`, `dist/`; incluye `requirements.txt`, `LEEME.txt`, `COMO_JUGAR.md`, y `Distribucion/Jugar.bat`).

## Más información

- [`README.md`](README.md) — modos de juego y `.exe`
- [`Data/README.md`](../Data/README.md) — archivos de datos necesarios
- [`README.md`](../README.md) — visión general del TFG
