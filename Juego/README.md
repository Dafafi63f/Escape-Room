# Juego — cuestionario MATCAD

Interfaz gráfica del juego (pygame) sobre el dominio compartido en [`Comun/`](Comun/README.md).

**Requisitos para jugar** (Python, pip, `.exe`, zip, PCs del centro): [`COMO_JUGAR.md`](COMO_JUGAR.md).

## Estructura

| Elemento | Descripción |
|----------|-------------|
| [`juego_grafico.py`](juego_grafico.py) | Lanzador pygame (libre, historia, resistencia, escape room, feedback) |
| [`LEEME.txt`](LEEME.txt) | Instrucciones breves (zip portable) |
| [`COMO_JUGAR.md`](COMO_JUGAR.md) | Guía completa para usuarios |
| [`requirements.txt`](requirements.txt) | Dependencias para jugar (pygame-ce) |
| [`Comun/`](Comun/README.md) | Dominio compartido (`from Comun...`) |
| [`Grafico/`](Grafico/README.md) | Interfaz pygame (ratón; teclado para texto) |
| [`Distribucion/`](Distribucion/) | Artefactos: zip, `.exe`, `Jugar.bat` |
| [`Scripts/`](Scripts/) | Build y diagnóstico (PowerShell; no va en el zip portable) |

| En `Distribucion/` | Descripción |
|--------------------|-------------|
| [`Jugar.bat`](Distribucion/Jugar.bat) | Atajo Windows (doble clic) |
| [`MATCAD_juego_portable.zip`](Distribucion/MATCAD_juego_portable.zip) | Paquete portable (`python Docs/utilidades_tfg.py --solo-zip`) |
| [`juego_grafico.exe`](Distribucion/juego_grafico.exe) | Ejecutable Windows (opcional) |

| En `Scripts/` | Descripción |
|---------------|-------------|
| [`build_exe_onefile.ps1`](Scripts/build_exe_onefile.ps1) | PyInstaller → `Distribucion/juego_grafico.exe` |
| [`comprobar_entorno.ps1`](Scripts/comprobar_entorno.ps1) | Diagnóstico (Python, pip, pygame, datos) |
| [`instalar_entorno.ps1`](Scripts/instalar_entorno.ps1) | Intenta instalar Python (winget) + dependencias |

Datos: [`../Data/README.md`](../Data/README.md). Tests: [`../Tests/README.md`](../Tests/README.md).

## Ejecutar

```bash
pip install -r Juego/requirements.txt   # desde la raíz del repo
python Juego/juego_grafico.py
```

En Windows: doble clic en [`Distribucion/Jugar.bat`](Distribucion/Jugar.bat) o:

```powershell
powershell -ExecutionPolicy Bypass -File Juego\Scripts\comprobar_entorno.ps1
powershell -ExecutionPolicy Bypass -File Juego\Scripts\instalar_entorno.ps1
```

## Modos

| Modo | Descripción |
|------|-------------|
| **Libre** | Partida configurable, filtros, informes al cerrar |
| **Historia** | Examen balanceado según histórico; carrusel de 5 presets |
| **Resistencia** | Partida continua, eventos, objetos, ranking local |
| **Escape room** | Salas y puertas, tienda, botín, inventario; partida distinta cada vez |
| **Feedback** | Formulario en pantalla (icono 📣) |

Detalle: [`Grafico/README.md`](Grafico/README.md) y [`Comun/README.md`](Comun/README.md).

## Configuración del creador

```bash
cd Juego
python -m Comun.feedback
```

Genera `Data/Banco/creador_privado.json` (no versionado).

## Ejecutable Windows (sin Python)

```powershell
pip install -r requirements.txt   # raíz del repo (desarrollo + PyInstaller)
.\Juego\Scripts\build_exe_onefile.ps1
```

Genera `Juego/Distribucion/juego_grafico.exe`. Si no empaquetas `Data/`, copia la carpeta `Data/` del repo junto al `.exe`. El estado del jugador se escribe en `Data/Juego/` al lado del ejecutable.

En PCs con `.exe` bloqueados, usa la vía Python. Ver [`COMO_JUGAR.md`](COMO_JUGAR.md).
