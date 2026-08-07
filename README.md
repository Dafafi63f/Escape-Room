# MATCAD — Escape Room (proyecto personal)

Juego educativo de cuestionarios MatCAD en **pygame** (modos libre, historia, resistencia, escape room y feedback).

**Versión actual:** `v1.1.0` — juego educativo · proyecto personal  
**Origen académico:** la entrega TFG v1.0.0 queda fuera de este repositorio (archivo local del autor).

- **Descargar solo el juego:** [MATCAD_juego_portable.zip](https://github.com/Dafafi63f/Escape-Room/releases/download/juego/MATCAD_juego_portable.zip) (sin tests ni docs de desarrollo)
- **Cómo jugar:** [`Juego/COMO_JUGAR.md`](Juego/COMO_JUGAR.md) · lanzador [`Juego/juego_grafico.py`](Juego/juego_grafico.py)
- **Repositorio:** https://github.com/Dafafi63f/Escape-Room.git

```bash
pip install -r Juego/requirements.txt
python Juego/juego_grafico.py
```

No incluyas tokens, contraseñas ni claves privadas en archivos versionados.

## Documentación

| Tema | Dónde |
|------|-------|
| Banco y datos | [`Data/README.md`](Data/README.md) |
| Juego y modos | [`Juego/README.md`](Juego/README.md) |
| Dominio / UI | [`Juego/Comun/README.md`](Juego/Comun/README.md) · [`Juego/Grafico/README.md`](Juego/Grafico/README.md) |
| Mantenimiento del banco | [`Files/README.md`](Files/README.md) |
| Docs / utilidades | [`Docs/README.md`](Docs/README.md) · [`Docs/utilidades.py`](Docs/utilidades.py) |
| Tests | [`Tests/README.md`](Tests/README.md) |
| Novedades del jugador | [`Docs/CHANGELOG_JUEGO.md`](Docs/CHANGELOG_JUEGO.md) |

## Estructura

| Carpeta | Rol |
|---------|-----|
| `Juego/` | Código del juego (lanzador, `Comun/`, `Grafico/`) |
| `Data/` | Preguntas, listado, plantillas |
| `Files/` | Scripts de mantenimiento (no hace falta para jugar) |
| `Docs/` | Changelogs, checklist y [`utilidades.py`](Docs/utilidades.py) |
| `Tests/` | Pruebas unitarias y CI |

## Comandos útiles

```bash
python -m unittest discover -s Tests -t .
python Files/health_check.py --solo-datos
python Docs/utilidades.py
```
