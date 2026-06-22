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
python utilidades_tfg.py                 # memoria + .exe → limpieza final
python utilidades_tfg.py --sin-exe       # memoria sin .exe (más rápido)
python utilidades_tfg.py --solo-limpieza --solo-entrega   # borrar también los .docx regenerables
```

Salida Word: `Docs/Entrega/Memoria_TFG_markdown.docx` y `Memoria_TFG_latex.docx` (secciones numeradas, pie de página). Estructura de páginas:

1. **Página 1 — portada:** título, alumno/tutor, resumen y notas administrativas (fuera del índice).
2. **Página 2 — índice** (solo tabla de contenidos).
3. **Página 3 en adelante — memoria:** introducción y resto del trabajo.

Todo el borrador Markdown está en `Entrega/Memoria_TFG.md` (portada al inicio, antes de la introducción). Pandoc genera el índice y un script (`ajustar_word_memoria.py`) reordena portada → índice → cuerpo. Tras exportar, la limpieza final borra plantilla Pandoc, `__pycache__`, runtime del juego y restos de PyInstaller.

Al abrir el Word, Word debería pedir actualizar los campos; si no, pulsa **F9** (o clic derecho en el índice → *Actualizar campos*). El índice es un campo con enlaces a cada sección (no texto fijo).

El PDF de entrega lo exportas desde Word tras editar (fuera del repositorio).
