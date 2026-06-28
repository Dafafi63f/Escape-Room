# Juego — cuestionario MATCAD

Interfaz gráfica del juego (pygame) sobre el dominio compartido en [`Comun/`](Comun/README.md).

**Requisitos para jugar** (Python, pip, zips, PCs del centro): [`COMO_JUGAR.md`](COMO_JUGAR.md).

## Estructura

| Elemento | Descripción |
|----------|-------------|
| [`juego_grafico.py`](juego_grafico.py) | Lanzador pygame (libre, historia, resistencia, escape room, feedback) |
| [`LEEME.txt`](LEEME.txt) | Instrucciones breves (zip portable) |
| [`COMO_JUGAR.md`](COMO_JUGAR.md) | Guía completa para usuarios |
| [`requirements.txt`](requirements.txt) | Dependencias para jugar (pygame-ce) |
| [`Comun/`](Comun/README.md) | Dominio compartido (`from Comun...`) |
| [`Grafico/`](Grafico/README.md) | Interfaz pygame (ratón; teclado para texto) |
| [`Distribucion/`](Distribucion/) | Zips y `Jugar.bat` |
| [`Scripts/`](Scripts/) | Diagnóstico e instalación (PowerShell; no va en el zip portable) |

| En `Distribucion/` | Descripción |
|--------------------|-------------|
| [`Jugar.bat`](Distribucion/Jugar.bat) | Atajo Windows: lanza `python juego_grafico.py` |
| [`MATCAD_juego_portable.zip`](Distribucion/MATCAD_juego_portable.zip) | Paquete completo (`python Docs/utilidades_tfg.py --solo-zip`) |
| [`MATCAD_juego_minimal.zip`](Distribucion/MATCAD_juego_minimal.zip) | Paquete mínimo (`python Docs/utilidades_tfg.py --solo-zip`) |

| En `Scripts/` | Descripción |
|---------------|-------------|
| [`comprobar_entorno.ps1`](Scripts/comprobar_entorno.ps1) | Diagnóstico (Python, pip, pygame, datos) |
| [`instalar_entorno.ps1`](Scripts/instalar_entorno.ps1) | Intenta instalar Python (winget) + dependencias |
| [`crear_zip_minimal.py`](Scripts/crear_zip_minimal.py) | Genera el zip del juego mínimo |

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
| **Historia** | Examen balanceado según histórico; carrusel de presets |
| **Resistencia** | Partida continua, eventos, objetos |
| **Escape room** | Salas y puertas, tienda, botín, inventario |
| **Feedback** | Formulario en pantalla (icono 📣) |

Detalle: [`Grafico/README.md`](Grafico/README.md) y [`Comun/README.md`](Comun/README.md).

## Configuración del creador

```bash
cd Juego
python -m Comun.feedback
```

Genera `Data/Banco/creador_privado.json` (no versionado).
