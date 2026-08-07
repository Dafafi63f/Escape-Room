# Juego — cuestionario MATCAD

Interfaz gráfica del juego (pygame) sobre el dominio compartido en [`Comun/`](Comun/README.md). **Versión actual:** `v1.1.0` (juego educativo / proyecto personal; la entrega TFG fue la `v1.0.0`, ver [`Docs/RELEASE_1.0.md`](../Docs/RELEASE_1.0.md)).

**Requisitos para jugar:** [`COMO_JUGAR.md`](COMO_JUGAR.md).
**Solo el juego (zip):** [descarga desde Releases](https://github.com/Dafafi63f/Escape-Room/releases/download/juego/MATCAD_juego_portable.zip).

## Estructura

| Elemento | Descripción |
|----------|-------------|
| [`juego_grafico.py`](juego_grafico.py) | Lanzador pygame (libre, historia, resistencia, escape room, feedback) |
| [`LEEME.txt`](LEEME.txt) | Instrucciones breves |
| [`COMO_JUGAR.md`](COMO_JUGAR.md) | Guía completa para usuarios |
| [`requirements.txt`](requirements.txt) | Dependencias para jugar (pygame-ce) |
| [`Comun/`](Comun/README.md) | Dominio compartido (`from Comun...`) |
| [`Grafico/`](Grafico/README.md) | Interfaz pygame |

Datos: [`../Data/README.md`](../Data/README.md). Tests: [`../Tests/README.md`](../Tests/README.md).

## Ejecutar

```bash
pip install -r Juego/requirements.txt   # desde la raíz del repo
python Juego/juego_grafico.py
```

## Modos

| Modo | Descripción |
|------|-------------|
| **Libre** | Partida configurable, filtros, informes al cerrar |
| **Historia** | Examen balanceado según tu práctica local; carrusel de presets |
| **Resistencia** | Partida continua, eventos, objetos |
| **Escape room** | Salas y puertas, tienda, botín, inventario |
| **Feedback** | Formulario en pantalla (icono 📣) |

Detalle: [`Grafico/README.md`](Grafico/README.md) y [`Comun/README.md`](Comun/README.md).

## Configuración del creador

```bash
cd Juego
python -m Comun.feedback
```

Genera `Data/Privado/creador_privado.json` (no versionado).
