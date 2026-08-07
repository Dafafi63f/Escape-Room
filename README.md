# MATCAD — Escape Room (proyecto personal)

Juego educativo de cuestionarios MatCAD en **pygame** (modos libre, historia, resistencia, escape room y feedback).

**Versión actual:** `v1.1.0` — juego educativo · proyecto personal  
**Origen académico:** la entrega TFG v1.0.0 queda archivada en la carpeta hermana `Treball Final de Grau`.

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
| Tests | [`Tests/README.md`](Tests/README.md) |
| Novedades del jugador | [`Docs/CHANGELOG_JUEGO.md`](Docs/CHANGELOG_JUEGO.md) |
| Empaquetado zip | [`Docs/utilidades_distribucion.py`](Docs/utilidades_distribucion.py) |

## Estructura

| Carpeta | Rol |
|---------|-----|
| `Juego/` | Código del juego y zips en `Distribucion/` |
| `Data/` | Preguntas, listado, plantillas, histórico |
| `Files/` | Scripts de mantenimiento (no hace falta para jugar) |
| `Docs/` | Changelog del juego y utilidades de distribución |
| `Tests/` | Pruebas unitarias y CI |

## Comandos útiles

```bash
python -m unittest discover -s Tests -t .
python Files/health_check.py --solo-datos
python Docs/utilidades_distribucion.py --solo-zip --forzar-zip
```
