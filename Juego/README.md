# Juego — cuestionario MATCAD

Interfaz gráfica del juego (pygame) sobre el dominio compartido en [`Comun/`](Comun/README.md).

| Lanzador | Interfaz | Requisitos |
|----------|----------|------------|
| [`juego_grafico.py`](juego_grafico.py) | Pygame (libre, historia, resistencia, feedback) | `pip install -r requirements.txt` |

| Elemento | Descripción |
|----------|-------------|
| [`juego_grafico.py`](juego_grafico.py) | Lanzador pygame |
| [`Comun/`](Comun/README.md) | Dominio compartido (`from Comun...`) |
| [`Grafico/`](Grafico/README.md) | Interfaz pygame (ratón; teclado para texto) |
| [`Data/Banco/`](../Data/README.md) | Banco de preguntas y catálogos |
| [`Data/Juego/`](../Data/README.md) | Estado local del jugador (informes, rankings, preferencias) |
| [`Tests/`](../Tests/README.md) | Pruebas unitarias |

## Ejecutar

```bash
pip install -r requirements.txt
python Juego/juego_grafico.py
```

Datos en [`../Data/README.md`](../Data/README.md).

## Modos

| Modo | Descripción |
|------|-------------|
| **Libre** | Partida configurable, filtros, informes al cerrar |
| **Historia** | Examen balanceado según histórico; carrusel de 5 presets (repaso, simulacro, examen por materia, etc.) |
| **Resistencia** | Partida infinita, eventos, objetos, ranking local |
| **Feedback** | Formulario en pantalla (icono 📣); ver [`Grafico/pantalla_feedback.py`](Grafico/pantalla_feedback.py) |

Detalle de bancos, puntuación y arquitectura: [`Grafico/README.md`](Grafico/README.md) y [`Comun/README.md`](Comun/README.md).

## Configuración del creador

Plantilla local para SMTP y datos privados: [`Comun/config_creador.py`](Comun/config_creador.py).

```bash
cd Juego
python -m Comun.config_creador
```

Genera `Data/Banco/creador_privado.json` (no versionado). Rellena tus datos reales en el fichero generado si necesitas SMTP.

## Ejecutable Windows (opcional)

Empaquetado con PyInstaller (incluye pygame, `Files/utils_plantillas_core.py` y el banco `Data/` del repositorio):

```powershell
pip install -r requirements.txt
.\Juego\build_exe_onefile.ps1
```

Genera `Juego/juego_grafico.exe` (ventana sin consola). Si no empaquetas `Data/`, copia la carpeta `Data/` del repo junto al `.exe`. El estado del jugador (informes, rankings, preferencias) se escribe en `Data/Juego/` al lado del ejecutable.
