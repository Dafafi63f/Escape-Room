# Documentación del juego

Seguimiento del proyecto personal.
La memoria, figuras y presentación del TFG no forman parte de este repositorio.

## Contenido

| Fichero | Contenido |
|---------|-----------|
| [`CHANGELOG_JUEGO.md`](CHANGELOG_JUEGO.md) | Novedades visibles (hub Info del juego gráfico) |
| [`CHANGELOG_PROYECTO.md`](CHANGELOG_PROYECTO.md) | Historial técnico del proyecto |
| [`CHECKLIST.md`](CHECKLIST.md) | Pendientes e ideas futuras |
| [`RELEASE_1.0.md`](RELEASE_1.0.md) | Alcance de la entrega TFG v1.0.0 (histórico) |
| [`utilidades.py`](utilidades.py) | Limpia temporales/runtime y regenera `MATCAD_juego_portable.zip` en la raíz |
| [`../Juego/COMO_JUGAR.md`](../Juego/COMO_JUGAR.md) | Cómo instalar y jugar |

## Utilidades del repo

```bash
python Docs/utilidades.py                 # limpieza + MATCAD_juego_portable.zip (raíz)
python Docs/utilidades.py --solo-limpieza
python Docs/utilidades.py --solo-zip
python Files/mantenimiento.py temporales  # solo limpieza
```
