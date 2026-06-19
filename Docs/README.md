# Documentación y entrega del TFG

Todo lo relacionado con la memoria, el seguimiento del proyecto y los artefactos de entrega.

## En la raíz de `Docs/`

| Fichero | Contenido |
|---------|-----------|
| [`CHANGELOG_PROYECTO.md`](CHANGELOG_PROYECTO.md) | Estado del TFG, feedback del tutor, historial técnico |
| [`CHANGELOG_JUEGO.md`](CHANGELOG_JUEGO.md) | Novedades visibles para quien juega (hub Info del juego gráfico) |
| [`CHECKLIST.md`](CHECKLIST.md) | Pendientes e ideas futuras |
| [`generar_figuras_memoria.py`](generar_figuras_memoria.py) | Regenera PNG en `Figuras/` |

## Subcarpetas (solo estas dos)

| Carpeta | Contenido |
|---------|-----------|
| [`Entrega/`](Entrega/) | Borrador Markdown, LaTeX y Word (`Memoria_TFG.*`) |
| [`Figuras/`](Figuras/) | Imágenes insertadas en la memoria |

## Comandos (desde la raíz del repo)

```bash
python Docs/generar_figuras_memoria.py   # opcional, figuras
python utilidades_tfg.py                 # limpieza + Word (o --solo-limpieza / --solo-memoria)
```

Salida Word: `Docs/Entrega/Memoria_TFG_markdown.docx` y `Memoria_TFG_latex.docx`.

El PDF de entrega lo exportas desde Word tras editar (fuera del repositorio).
